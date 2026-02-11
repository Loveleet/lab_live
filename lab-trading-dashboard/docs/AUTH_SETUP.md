# Auth Setup (Cookie-Based Login)

## Database

1. Ensure the **users** table exists (you already created it).
2. Run the **sessions** table migration:

```bash
psql -U <user> -d <database> -f server/sql/sessions.sql
```

Or run manually:

```sql
CREATE TABLE IF NOT EXISTS sessions (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  expires_at  TIMESTAMPTZ NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_exp  ON sessions(expires_at);
```

## Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/login` | POST | No | `{ email, password }` → sets session cookie |
| `/auth/logout` | POST | No | Clears session cookie |
| `/auth/me` | GET | Yes | Returns current user |
| `/api/*` | * | Yes | Protected (except `/api/health`, `/api/server-info`, `/api/tunnel-url`) |

## Login

Use the user you inserted in `users` (e.g. `test@example.com` / `YourPassword123!`).

## Production (GitHub Pages)

- Set `NODE_ENV=production` so cookies use `secure: true` and `sameSite: "none"`.
- Ensure CORS `allowedOrigins` includes your frontend origin.
