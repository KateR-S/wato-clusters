import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { LoginForm } from '../../src/components/Auth/LoginForm';
import { RegisterForm } from '../../src/components/Auth/RegisterForm';
import { AuthContext } from '../../src/contexts/AuthContext';

const mockLogin = vi.fn();
const mockRegister = vi.fn();

const mockAuthContext = {
  token: null,
  user: null,
  isAuthenticated: false,
  login: mockLogin,
  logout: vi.fn(),
  register: mockRegister,
};

const renderWithAuth = (component: React.ReactNode) =>
  render(
    <AuthContext.Provider value={mockAuthContext}>
      <MemoryRouter>{component}</MemoryRouter>
    </AuthContext.Provider>
  );

describe('LoginForm', () => {
  beforeEach(() => {
    mockLogin.mockReset();
  });

  it('renders email and password fields', () => {
    renderWithAuth(<LoginForm />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
  });

  it('submits with correct values', async () => {
    mockLogin.mockResolvedValue(undefined);
    renderWithAuth(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'test@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'password123' } });
    fireEvent.submit(screen.getByRole('button', { name: /sign in/i }));
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123');
    });
  });

  it('shows error on failed login', async () => {
    mockLogin.mockRejectedValue(new Error('Unauthorized'));
    renderWithAuth(<LoginForm />);
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'bad@example.com' } });
    fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'wrong' } });
    fireEvent.submit(screen.getByRole('button', { name: /sign in/i }));
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });
});

describe('RegisterForm', () => {
  beforeEach(() => {
    mockRegister.mockReset();
  });

  it('renders all fields', () => {
    renderWithAuth(<RegisterForm />);
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getAllByLabelText(/password/i)).toHaveLength(2);
  });

  it('shows error when passwords do not match', async () => {
    renderWithAuth(<RegisterForm />);
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'new@example.com' } });
    const [passField, confirmField] = screen.getAllByLabelText(/password/i);
    fireEvent.change(passField, { target: { value: 'password123' } });
    fireEvent.change(confirmField, { target: { value: 'different' } });
    fireEvent.submit(screen.getByRole('button', { name: /register/i }));
    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });
  });

  it('does not call register when passwords do not match', async () => {
    renderWithAuth(<RegisterForm />);
    fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'new@example.com' } });
    const [passField, confirmField] = screen.getAllByLabelText(/password/i);
    fireEvent.change(passField, { target: { value: 'password123' } });
    fireEvent.change(confirmField, { target: { value: 'different' } });
    fireEvent.submit(screen.getByRole('button', { name: /register/i }));
    expect(mockRegister).not.toHaveBeenCalled();
  });
});
