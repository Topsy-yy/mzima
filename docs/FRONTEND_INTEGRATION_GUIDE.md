# Mzima Frontend Integration Guide

## Overview

This document describes how the React/TypeScript frontend integrates with the Mzima Backend API. The frontend is a **Vite + React 18 + TypeScript** application located at the project root.

---

## Quick Start

### Prerequisites

| Tool | Version |
|------|---------|
| Node.js | ≥ 18 |
| npm | ≥ 9 |

### 1. Install Dependencies

```bash
cd /home/taz/desktop/ai/mzima
npm ci
```

### 2. Configure API Base URL

The frontend assumes the backend runs at the same origin (served via reverse proxy in production) or at `http://localhost:8000` in development.

**Development proxy** (configured in `vite.config.ts`):
```typescript
server: {
  proxy: {
    '/api': 'http://localhost:8000',
  },
}
```

### 3. Start Development Server

```bash
npm run dev
```

Opens at `http://localhost:5173` with API requests proxied to `http://localhost:8000`.

### 4. Build for Production

```bash
npm run build
# Output in ./dist/
```

---

## Project Structure

```
src/
├── main.tsx              # React entry point
├── App.tsx               # Root component, routing, auth context
├── api.ts                # Typed API client (fetch wrapper)
├── styles.css            # Global styles
├── components/           # UI components (not shown in current tree)
├── pages/                # Page components (not shown in current tree)
├── hooks/                # Custom React hooks (not shown)
└── types/                # Shared TypeScript types (inline in api.ts)
```

---

## API Client (`src/api.ts`)

### Core Function

```typescript
async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string
): Promise<T>
```

- **Base path**: Relative (`/api/v1/...`) — relies on Vite proxy in dev, same-origin in prod
- **Auth**: Attaches `Authorization: Bearer <token>` header when `token` provided
- **Error handling**: Throws `Error` with backend's `detail` message on non-2xx
- **Content-Type**: Auto-set to `application/json` or `application/x-www-form-urlencoded` for login

### Authentication

```typescript
// Login → returns access_token string
const token = await login(username, password);

// Store token (e.g., in React context + localStorage)
// Include in subsequent requests:
const user = await getCurrentUser(token);
```

### Endpoints

| Function | HTTP | Backend Endpoint | Auth | Returns |
|----------|------|------------------|------|---------|
| `login(username, password)` | POST | `/api/v1/auth/login` | No | `{ access_token }` |
| `getCurrentUser(token)` | GET | `/api/v1/auth/me` | Yes | `ApiUser` |
| `getAppointmentQueue(token)` | GET | `/api/v1/appointments/clinic/review-queue` | Yes | `AppointmentRequest[]` |
| `createAppointmentRequest(patientId, specialty)` | POST | `/api/v1/appointments/appointment-requests` | No* | `AppointmentRequest` |
| `decideAppointmentRequest(id, decision, reason, token)` | POST | `/api/v1/appointments/appointment-requests/{id}/decision` | Yes | `ClinicianDecision` |
| `getWalkInQueue(token)` | GET | `/api/v1/queue` | Yes | `QueueVisit[]` |
| `checkInVisit(payload, token)` | POST | `/api/v1/visits` | Yes | `Visit` |
| `callVisit(visitId, overrideReason, token)` | POST | `/api/v1/queue/{id}/call` | Yes | `Visit` |
| `completeVisitTriage(visitId, category, destination, token)` | POST | `/api/v1/visits/{id}/triage` | Yes | `Visit` |

> * `createAppointmentRequest` currently lacks auth in `api.ts` — verify backend requirement.

---

## Type Definitions

All types defined inline in `api.ts`:

```typescript
type ApiRole = 'clerk' | 'nurse' | 'shift_lead' | 'admin';

interface ApiUser {
  id: string;
  username: string;
  role: ApiRole;
}

interface AppointmentRequest {
  id: string;
  patient_identifier: string;
  requested_specialty: string;
  status: string;
  created_at: string;
}

interface QueueVisit {
  visit_id: string;
  token_number: string;
  arrival_time: string;
  minutes_waiting: number;
  is_fast_track: boolean;
  is_wait_capped: boolean;
  calculated_score: number;
  red_flags: Record<string, boolean>;
}

interface Visit {
  id: string;
  token_number: string;
  arrival_time: string;
  age_band: string;
  visit_type: string;
  is_fast_track: boolean;
  red_flags: Record<string, boolean>;
  status: string;
  triage_start_time: string | null;
  triage_end_time: string | null;
  triage_category: string | null;
  destination: string | null;
}

interface ClinicianDecision {
  id: string;
  request_id: string;
  clinician_id: string;
  decision: string;
  reason: string | null;
  created_at: string;
}
```

---

## Authentication Flow

### 1. Login Page

```tsx
const handleLogin = async (username: string, password: string) => {
  try {
    const token = await login(username, password);
    // Store in context + localStorage
    authContext.login(token);
    navigate('/dashboard');
  } catch (err) {
    setError(err.message);
  }
};
```

### 2. Auth Context (Pattern)

```tsx
// context/AuthContext.tsx
interface AuthContextType {
  token: string | null;
  user: ApiUser | null;
  login: (token: string) => void;
  logout: () => void;
}

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(() => localStorage.getItem('token'));
  const [user, setUser] = useState<ApiUser | null>(null);

  const login = async (newToken: string) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
    const u = await getCurrentUser(newToken);
    setUser(u);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ token, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
```

### 3. Protected Routes

```tsx
const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" />;
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" />;
  }
  return children;
};
```

---

## Data Flow Patterns

### 1. Queue Dashboard (Real-time Feel)

```tsx
// Poll every 10s for queue updates
const { data: queue } = useQuery({
  queryKey: ['queue'],
  queryFn: () => getWalkInQueue(token),
  refetchInterval: 10_000,
});
```

### 2. Optimistic Updates

```tsx
const callVisitMutation = useMutation({
  mutationFn: (visitId) => callVisit(visitId, '', token),
  onMutate: async (visitId) => {
    await queryClient.cancelQueries(['queue']);
    const previous = queryClient.getQueryData(['queue']);
    queryClient.setQueryData(['queue'], (old) =>
      old.map((v) => v.visit_id === visitId ? { ...v, status: 'CALLED' } : v)
    );
    return { previous };
  },
  onError: (err, _, context) => {
    queryClient.setQueryData(['queue'], context.previous);
  },
});
```

### 3. Form Handling (React Hook Form + Zod)

```tsx
const schema = z.object({
  age_band: z.enum(['under_5', '5_12', '13_17', '18_64', '65_plus']),
  visit_type: z.enum(['new', 'review', 'refill']),
  red_flags: z.record(z.boolean()),
});

const form = useForm<z.infer<typeof schema>>({ resolver: zodResolver(schema) });

const onSubmit = async (data) => {
  const visit = await checkInVisit(data, token);
  queryClient.invalidateQueries(['queue']);
};
```

---

## Role-Based UI

| Role | Permissions | UI Access |
|------|-------------|-----------|
| `clerk` | Check-in walk-ins, create appointments | `/checkin`, `/appointments/new` |
| `nurse` | Call patients, complete triage, review appointments | `/queue`, `/triage`, `/appointments/review` |
| `shift_lead` | All nurse + priority override | `/queue`, `/override` |
| `admin` | All + user management (if implemented) | `/admin` |

```tsx
const rolePermissions = {
  clerk: ['checkin', 'appointments:create'],
  nurse: ['queue:view', 'queue:call', 'triage:complete', 'appointments:review'],
  shift_lead: ['queue:view', 'queue:call', 'triage:complete', 'queue:override', 'appointments:review'],
  admin: ['*'],
};
```

---

## Error Handling

### Global Error Boundary

```tsx
// Catch render errors
<ErrorBoundary fallback={<ErrorPage />}>
  <App />
</ErrorBoundary>
```

### API Error Handling

```tsx
try {
  await callVisit(id, reason, token);
  toast.success('Patient called');
} catch (err) {
  if (err.message.includes('403')) {
    toast.error('Insufficient permissions');
  } else if (err.message.includes('401')) {
    authContext.logout();
    navigate('/login');
  } else {
    toast.error(err.message);
  }
}
```

---

## Development Tips

### 1. Type Safety

- Backend Pydantic models → frontend TypeScript types should stay in sync
- Consider generating types from OpenAPI: `openapi-typescript`

### 2. Environment Variables

```bash
# .env.local (not committed)
VITE_API_BASE_URL=http://localhost:8000
```

```typescript
// api.ts
const BASE = import.meta.env.VITE_API_BASE_URL || '';
```

### 3. Mocking in Tests

```typescript
// __mocks__/api.ts
export const login = vi.fn();
export const getWalkInQueue = vi.fn();
// ...
```

### 4. Debugging Network

- DevTools → Network tab → filter "api"
- React Query DevTools for cache inspection

---

## Production Deployment

### Build

```bash
npm run build
# Creates ./dist/ with hashed assets
```

### Serve via Nginx (Example)

```nginx
server {
  listen 80;
  server_name mzima.example.com;

  root /var/www/mzima/dist;
  index index.html;

  # Frontend SPA routing
  location / {
    try_files $uri $uri/ /index.html;
  }

  # Proxy API to backend
  location /api/ {
    proxy_pass http://localhost:8000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

### Docker (Multi-stage)

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Runtime stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

---

## API Reference Summary

| Feature | Endpoint | Method | Auth | Role |
|---------|----------|--------|------|------|
| **Auth** | | | | |
| Login | `/api/v1/auth/login` | POST | No | Public |
| Current User | `/api/v1/auth/me` | GET | Yes | Any |
| **Walk-in Queue** | | | | |
| List Queue | `/api/v1/queue` | GET | Yes | Clerk+ |
| Check-in | `/api/v1/visits` | POST | Yes | Clerk+ |
| Call Next | `/api/v1/queue/call-next` | POST | Yes | Nurse+ |
| Call Specific | `/api/v1/queue/{id}/call` | POST | Yes | Nurse+ |
| Complete Triage | `/api/v1/visits/{id}/triage` | POST | Yes | Nurse+ |
| Override Priority | `/api/v1/queue/override` | POST | Yes | Shift Lead+ |
| **Appointments** | | | | |
| Create Request | `/api/v1/appointments/appointment-requests` | POST | Yes* | Clerk+ |
| Review Queue | `/api/v1/appointments/clinic/review-queue` | GET | Yes | Nurse+ |
| Decide Request | `/api/v1/appointments/appointment-requests/{id}/decision` | POST | Yes | Nurse+ |

---

## Related Documents

- [Backend Technical Guide](./BACKEND_TECHNICAL_GUIDE.md) — Server setup, architecture, security
- [API Specification (OpenAPI)](http://localhost:8000/api/v1/openapi.json) — Auto-generated from FastAPI

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| CORS errors in dev | Ensure `vite.config.ts` proxy configured, backend CORS allows `localhost:5173` |
| 401 on every request | Token expired → re-login; check `SECRET_KEY` matches backend |
| 403 Forbidden | User role insufficient for endpoint; check `RoleEnum` in backend |
| Types out of sync | Regenerate from OpenAPI or manually update `api.ts` |
| Proxy not working | Restart Vite dev server after config change |