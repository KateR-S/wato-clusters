import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { type ReactNode, createElement } from 'react';
import { AuthProvider } from '../../src/contexts/AuthContext';
import { useAuth } from '../../src/hooks/useAuth';

vi.mock('../../src/services/api', () => ({
  login: vi.fn().mockResolvedValue({ access_token: 'test-token', token_type: 'bearer' }),
  register: vi.fn().mockResolvedValue({ access_token: 'reg-token', token_type: 'bearer' }),
}));

const wrapper = ({ children }: { children: ReactNode }) =>
  createElement(AuthProvider, null, children);

describe('useAuth', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('starts unauthenticated', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.token).toBeNull();
  });

  it('stores token in localStorage after login', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    await act(async () => {
      await result.current.login('test@example.com', 'password');
    });
    expect(localStorage.getItem('token')).toBe('test-token');
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('clears token from localStorage after logout', async () => {
    const { result } = renderHook(() => useAuth(), { wrapper });
    await act(async () => {
      await result.current.login('test@example.com', 'password');
    });
    expect(result.current.isAuthenticated).toBe(true);
    act(() => {
      result.current.logout();
    });
    expect(localStorage.getItem('token')).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });
});
