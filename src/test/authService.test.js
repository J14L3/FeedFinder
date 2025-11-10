/**
 * Tests for authentication service
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  fetchCSRFToken,
  getCSRFToken,
  authenticatedFetch,
  refreshToken,
  verifySession,
  logout,
  login,
  register
} from '../authService'

// Mock fetch globally
global.fetch = vi.fn()

describe('AuthService', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset module state
    vi.resetModules()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('fetchCSRFToken', () => {
    it('should fetch and store CSRF token', async () => {
      const mockToken = 'test-csrf-token'
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ csrf_token: mockToken })
      })

      const token = await fetchCSRFToken()

      expect(token).toBe(mockToken)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/csrf-token'),
        expect.objectContaining({
          method: 'GET',
          credentials: 'include'
        })
      )
    })

    it('should return null on error', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Network error'))

      const token = await fetchCSRFToken()

      expect(token).toBeNull()
    })

    it('should return null when response is not ok', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false
      })

      const token = await fetchCSRFToken()

      expect(token).toBeNull()
    })
  })

  describe('getCSRFToken', () => {
    it('should fetch token if not available', async () => {
      const mockToken = 'test-csrf-token'
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ csrf_token: mockToken })
      })

      const token = await getCSRFToken()

      expect(token).toBe(mockToken)
      expect(global.fetch).toHaveBeenCalled()
    })
  })

  describe('login', () => {
    it('should login successfully', async () => {
      const mockResponse = {
        success: true,
        message: 'Welcome!',
        user: { id: 1, username: 'testuser' }
      }

      // Mock CSRF token fetch
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ csrf_token: 'csrf-token' })
      })

      // Mock login response
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      })

      const result = await login('testuser', 'password123')

      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockResponse)
      expect(global.fetch).toHaveBeenCalledTimes(2) // CSRF + login
    })

    it('should handle login failure', async () => {
      // Mock CSRF token fetch
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ csrf_token: 'csrf-token' })
      })

      // Mock login failure
      global.fetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ success: false, message: 'Invalid credentials' })
      })

      const result = await login('testuser', 'wrongpassword')

      expect(result.success).toBe(false)
    })

    it('should handle network errors', async () => {
      global.fetch.mockRejectedValueOnce(new Error('Network error'))

      const result = await login('testuser', 'password123')

      expect(result.success).toBe(false)
      expect(result.data.message).toContain('error')
    })
  })

  describe('register', () => {
    it('should register successfully', async () => {
      const userData = {
        username: 'newuser',
        email: 'new@example.com',
        password: 'password123',
        confirm_password: 'password123'
      }

      const mockResponse = {
        success: true,
        message: 'Account created successfully!',
        user: { id: 1, username: 'newuser' }
      }

      // Mock CSRF token fetch
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ csrf_token: 'csrf-token' })
      })

      // Mock register response
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      })

      const result = await register(userData)

      expect(result.success).toBe(true)
      expect(result.data).toEqual(mockResponse)
    })
  })

  describe('logout', () => {
    it('should logout successfully', async () => {
      // Mock CSRF token fetch
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ csrf_token: 'csrf-token' })
      })

      // Mock logout response
      global.fetch.mockResolvedValueOnce({
        ok: true
      })

      const result = await logout()

      expect(result).toBe(true)
    })
  })

  describe('verifySession', () => {
    it('should verify session successfully', async () => {
      const mockUser = { id: 1, username: 'testuser', role: 'normie' }

      // Mock CSRF token fetch
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ csrf_token: 'csrf-token' })
      })

      // Mock authenticatedFetch (which verifySession uses)
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, user: mockUser })
      })

      const user = await verifySession()

      expect(user).toEqual(mockUser)
    })

    it('should return null on verification failure', async () => {
      // Mock CSRF token fetch
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ csrf_token: 'csrf-token' })
      })

      // Mock failed verification
      global.fetch.mockResolvedValueOnce({
        ok: false
      })

      const user = await verifySession()

      expect(user).toBeNull()
    })
  })

  describe('refreshToken', () => {
    it('should refresh token successfully', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: true
      })

      const result = await refreshToken()

      expect(result).toBe(true)
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/refresh'),
        expect.objectContaining({
          method: 'POST',
          credentials: 'include'
        })
      )
    })

    it('should return false on refresh failure', async () => {
      global.fetch.mockResolvedValueOnce({
        ok: false
      })

      const result = await refreshToken()

      expect(result).toBe(false)
    })
  })
})

