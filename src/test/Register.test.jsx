/**
 * Tests for Register component
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Register from '../Register'
import * as authService from '../authService'

// Mock authService
vi.mock('../authService', () => ({
  register: vi.fn(),
  verifySession: vi.fn()
}))

describe('Register Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const renderRegister = () => {
    return render(
      <BrowserRouter>
        <Register />
      </BrowserRouter>
    )
  }

  it('should render registration form', () => {
    renderRegister()

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument()
  })

  it('should handle form submission', async () => {
    authService.register.mockResolvedValue({
      success: true,
      data: { message: 'Account created successfully!', user: { id: 1, username: 'newuser' } }
    })

    renderRegister()

    const usernameInput = screen.getByLabelText(/username/i)
    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    const submitButton = screen.getByRole('button', { name: /register/i })

    fireEvent.change(usernameInput, { target: { value: 'newuser' } })
    fireEvent.change(emailInput, { target: { value: 'new@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(authService.register).toHaveBeenCalled()
    })
  })

  it('should validate password match', async () => {
    renderRegister()

    const passwordInput = screen.getByLabelText(/password/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    const submitButton = screen.getByRole('button', { name: /register/i })

    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    fireEvent.change(confirmPasswordInput, { target: { value: 'different' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument()
    })
  })

  it('should display error message on registration failure', async () => {
    authService.register.mockResolvedValue({
      success: false,
      data: { message: 'Username already exists' }
    })

    renderRegister()

    const usernameInput = screen.getByLabelText(/username/i)
    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    const submitButton = screen.getByRole('button', { name: /register/i })

    fireEvent.change(usernameInput, { target: { value: 'existinguser' } })
    fireEvent.change(emailInput, { target: { value: 'existing@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/username already exists/i)).toBeInTheDocument()
    })
  })
})

