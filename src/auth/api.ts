// Auth-specific helpers used by AuthContext and the login screen.
// Wraps the shared ../api module but exposes a typed error surface so the UI
// can distinguish invalid credentials, rate limiting, and transport failures
// without leaking backend detail.
import { login as apiLogin, getCurrentUser as apiGetCurrentUser, type ApiUser } from '../api';

export type AuthFailureKind = 'credentials' | 'rateLimited' | 'network' | 'server';

export class AuthFailure extends Error {
  kind: AuthFailureKind;
  retryAfter?: number;
  constructor(kind: AuthFailureKind, message: string, retryAfter?: number) {
    super(message);
    this.kind = kind;
    this.retryAfter = retryAfter;
  }
}

export async function loginRequest(username: string, password: string): Promise<string> {
  try {
    return await apiLogin(username, password);
  } catch (error) {
    const status = (error as { status?: number }).status;
    const retryAfter = (error as { retryAfter?: number }).retryAfter;
    if (status === 401) {
      throw new AuthFailure('credentials', 'Those details don\'t match. Check your username and password.');
    }
    if (status === 429) {
      throw new AuthFailure('rateLimited', 'Too many attempts. Wait a few minutes and try again.', retryAfter);
    }
    if (status && status >= 500) {
      throw new AuthFailure('server', 'We can\'t reach the server right now. Please try again.');
    }
    // Network errors have no status.
    if (!status) {
      throw new AuthFailure('network', 'We can\'t reach the server right now. Please try again.');
    }
    throw new AuthFailure('server', 'We can\'t reach the server right now. Please try again.');
  }
}

export { apiGetCurrentUser as fetchCurrentUser };

export type { ApiUser };