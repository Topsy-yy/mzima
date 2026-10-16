import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchCurrentUser, loginRequest } from './api';
import type { ApiUser } from '../api';

export type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated';

export interface AuthContextValue {
  user: ApiUser | null;
  token: string | null;
  status: AuthStatus;
  login: (username: string, password: string) => Promise<ApiUser>;
  loginClerk: (identifier: string, password: string) => Promise<ApiUser>;
  loginNurse: (identifier: string, password: string) => Promise<ApiUser>;
  loginShiftLead: (identifier: string, password: string) => Promise<ApiUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const CLERK_IDS = Array.from({ length: 10 }, (_, i) => `R${String(i + 1).padStart(3, '0')}`);
const NURSE_IDS = Array.from({ length: 10 }, (_, i) => `N${String(i + 1).padStart(3, '0')}`);
const LEAD_IDS = Array.from({ length: 10 }, (_, i) => `S${String(i + 1).padStart(3, '0')}`);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const navigate = useNavigate();
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<ApiUser | null>(null);
  const [status, setStatus] = useState<AuthStatus>('loading');

  useEffect(() => {
    if (!token) {
      setStatus('unauthenticated');
      return;
    }
    if (token.startsWith('clerk-demo-')) {
      const id = token.replace('clerk-demo-', '');
      setUser({ id, username: id, role: 'clerk' });
      setStatus('authenticated');
      return;
    }
    if (token.startsWith('nurse-demo-')) {
      const id = token.replace('nurse-demo-', '');
      setUser({ id, username: id, role: 'nurse' });
      setStatus('authenticated');
      return;
    }
    if (token.startsWith('lead-demo-')) {
      const id = token.replace('lead-demo-', '');
      setUser({ id, username: id, role: 'shift_lead' });
      setStatus('authenticated');
      return;
    }
    let active = true;
    (async () => {
      try {
        const current = await fetchCurrentUser(token);
        if (active) {
          setUser(current);
          setStatus('authenticated');
        }
      } catch {
        if (active) {
          setUser(null);
          setToken(null);
          setStatus('unauthenticated');
        }
      }
    })();
    return () => {
      active = false;
    };
  }, [token]);

  const login = useCallback(async (username: string, password: string) => {
    const accessToken = await loginRequest(username, password);
    const currentUser = await fetchCurrentUser(accessToken);
    setToken(accessToken);
    setUser(currentUser);
    setStatus('authenticated');
    return currentUser;
  }, []);

  function makeDemo(ids: string[], prefix: string, role: ApiUser['role']) {
    return async (identifier: string, password: string) => {
      if (!ids.includes(identifier)) {
        throw new Error(`Unknown identifier. Use ${ids[0]} to ${ids[ids.length - 1]}.`);
      }
      void password;
      const currentUser: ApiUser = { id: identifier, username: identifier, role };
      setToken(`${prefix}-${identifier}`);
      setUser(currentUser);
      setStatus('authenticated');
      return currentUser;
    };
  }

  const loginClerk = useCallback(makeDemo(CLERK_IDS, 'clerk-demo', 'clerk'), []);
  const loginNurse = useCallback(makeDemo(NURSE_IDS, 'nurse-demo', 'nurse'), []);
  const loginShiftLead = useCallback(makeDemo(LEAD_IDS, 'lead-demo', 'shift_lead'), []);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    setStatus('unauthenticated');
    navigate('/');
  }, [navigate]);

  const value = useMemo<AuthContextValue>(
    () => ({ user, token, status, login, loginClerk, loginNurse, loginShiftLead, logout }),
    [user, token, status, login, loginClerk, loginNurse, loginShiftLead, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}