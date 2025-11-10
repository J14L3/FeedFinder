/**
 * Tests for Login component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Login from '../Login'
import * as authService from '../authService'

// Mock authService
vi.mock('../authService', () => ({
  login: vi.fn(),
  verifySession: vi.fn()
}))

describe('Login Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const renderLogin = () => {
    return render(
      <BrowserRouter>
        <Login />
      </BrowserRouter>
    )
  }

  it('should render login form', () => {
    renderLogin()

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument()
  })

  it('should handle form submission', async () => {
    authService.login.mockResolvedValue({
      success: true,
      data: { message: 'Login successful', user: { id: 1, username: 'testuser' } }
    })

    renderLogin()

    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /login/i })

    fireEvent.change(usernameInput, { target: { value: 'testuser' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(authService.login).toHaveBeenCalledWith('testuser', 'password123')
    })
  })

  it('should display error message on login failure', async () => {
    authService.login.mockResolvedValue({
      success: false,
      data: { message: 'Invalid credentials' }
    })

    renderLogin()

    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /login/i })

    fireEvent.change(usernameInput, { target: { value: 'testuser' } })
    fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
    })
  })

  it('should validate required fields', async () => {
    renderLogin()

    const submitButton = screen.getByRole('button', { name: /login/i })
    fireEvent.click(submitButton)

    // Form validation should prevent submission
    await waitFor(() => {
      expect(authService.login).not.toHaveBeenCalled()
    })
  })
})

