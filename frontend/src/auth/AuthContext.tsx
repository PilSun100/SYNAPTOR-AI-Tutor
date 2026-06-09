import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import {
  clearAuthTokens,
  getCurrentUser,
  getStoredAccessToken,
  getStoredRefreshToken,
  loginUser,
  refreshSession,
  registerUser,
} from '../api/client';
import type { User } from '../types/api';
import { AuthContext } from './authContextStore';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [initializing, setInitializing] = useState(true);

  useEffect(() => {
    let mounted = true;

    async function restoreSession() {
      if (!getStoredAccessToken() && !getStoredRefreshToken()) {
        setInitializing(false);
        return;
      }

      try {
        const currentUser = await getCurrentUser();
        if (mounted) {
          setUser(currentUser);
        }
      } catch {
        try {
          const refreshed = await refreshSession();
          if (mounted) {
            setUser(refreshed.user);
          }
        } catch {
          clearAuthTokens();
          if (mounted) {
            setUser(null);
          }
        }
      } finally {
        if (mounted) {
          setInitializing(false);
        }
      }
    }

    restoreSession();

    return () => {
      mounted = false;
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const auth = await loginUser(email, password);
    setUser(auth.user);
  }, []);

  const register = useCallback(async (email: string, password: string, displayName: string) => {
    const auth = await registerUser(email, password, displayName);
    setUser(auth.user);
  }, []);

  const logout = useCallback(() => {
    clearAuthTokens();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      initializing,
      isAuthenticated: Boolean(user),
      login,
      register,
      logout,
    }),
    [initializing, login, logout, register, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
