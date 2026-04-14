import { createContext, useState, useEffect, type ReactNode } from 'react';
import { login as apiLogin, register as apiRegister } from '../services/api';
import type { User } from '../types';

interface AuthContextType {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (email: string, password: string) => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'));
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken) {
      setToken(storedToken);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const data = await apiLogin(email, password);
    localStorage.setItem('token', data.access_token);
    setToken(data.access_token);
    setUser({ id: 0, email });
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const register = async (email: string, password: string) => {
    const data = await apiRegister(email, password);
    localStorage.setItem('token', data.access_token);
    setToken(data.access_token);
    setUser({ id: 0, email });
  };

  return (
    <AuthContext.Provider value={{ token, user, isAuthenticated: !!token, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  );
};
