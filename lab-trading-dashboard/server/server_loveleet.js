const fs = require("fs");
const path = require("path");

// ✅ Load secrets from one file (never in Git). Tries: SECRETS_FILE env, then ./secrets.env, ../secrets.env, /etc/lab-trading-dashboard.secrets.env
(function loadSecretsEnv() {
  const tryPaths = [
    process.env.SECRETS_FILE,
    path.join(__dirname, "secrets.env"),
    path.join(__dirname, "..", "secrets.env"),
    "/etc/lab-trading-dashboard.secrets.env",
  ].filter(Boolean);
  for (const p of tryPaths) {
    try {
      if (fs.existsSync(p)) {
        const content = fs.readFileSync(p, "utf8");
        content.split("\n").forEach((line) => {
          const trimmed = line.replace(/#.*$/, "").trim();
          if (!trimmed) return;
          const match = trimmed.match(/^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$/);
          if (match && process.env[match[1]] === undefined) {
            process.env[match[1]] = match[2].replace(/^["']|["']$/g, "").trim();
          }
        });
        console.log("[secrets] Loaded from", p);
        return;
      }
    } catch (e) {
      // skip invalid path
    }
  }
})();

const http = require("http");
const express = require("express");
const cors = require("cors");
const cookieParser = require("cookie-parser");
const { Pool } = require("pg");
const axios = require('axios');

const app = express();
let currentLogPath = "D:/Projects/blockchainProject/pythonProject/Binance/Loveleet_Anish_Bot/LAB-New-Logic/hedge_logs";
const PORT = process.env.PORT || 10000;
const ENABLE_SELF_PING = String(process.env.ENABLE_SELF_PING || '').toLowerCase() === 'true';
const VERBOSE_LOG = String(process.env.VERBOSE_LOG || '').toLowerCase() === 'true';

// ✅ Allowed Frontend Origins (local dev, cloud server, GitHub Pages)
const extraOrigins = (process.env.ALLOWED_ORIGINS || "")
  .split(",")
  .map((o) => o.trim())
  .filter(Boolean);
const allowedOrigins = [
  "http://localhost:5173",
  "http://localhost:5174",
  "http://localhost:10000",
  "http://150.241.244.130:10000",
  "https://loveleet.github.io",
  ...extraOrigins, // e.g. ALLOWED_ORIGINS=https://api.yourdomain.com for GitHub Pages
];

// ✅ Proper CORS Handling
app.use(cors({
  origin: function (origin, callback) {
    try {
      if (!origin) {
        console.log("[CORS] Request with no origin (same-origin or server-to-server) — allowing");
        return callback(null, true);
      }
      if (allowedOrigins.includes(origin)) {
        console.log("[CORS] ✅ Allowed origin:", origin);
        return callback(null, true);
      }
      console.error("❌ CORS blocked origin:", origin);
      console.error("❌ Allowed origins:", allowedOrigins.join(", "));
      return callback(new Error("CORS not allowed for this origin"));
    } catch (e) {
      console.error("❌ CORS origin parse error:", e.message);
      return callback(new Error("CORS origin parse error"));
    }
  },
  credentials: true,
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
}));

app.use(express.json());
app.use(cookieParser());

app.use("/logs", (req, res, next) => {
  express.static(currentLogPath)(req, res, next);
});

// ✅ Database Configuration — use Render DATABASE_URL so cloud shows same data as Render, or DB_* vars
function buildDbConfig() {
  const databaseUrl = process.env.DATABASE_URL;
  if (databaseUrl) {
    try {
      const url = new URL(databaseUrl);
      const db = (url.pathname || '/labdb2').replace(/^\//, '') || 'labdb2';
      return {
        host: url.hostname,
        port: parseInt(url.port || '5432', 10),
        user: url.username || 'postgres',
        password: url.password || '',
        database: db,
        connectionTimeoutMillis: 10000,
        idleTimeoutMillis: 30000,
        max: 10,
      };
    } catch (e) {
      console.error("Invalid DATABASE_URL:", e.message);
    }
  }
  // Default to cloud database (150.241.244.130) for local development
  // Set DB_HOST=localhost to use local PostgreSQL instead
  const dbHost = process.env.DB_HOST || '150.241.244.130';
  const isLocalHost = dbHost === 'localhost' || dbHost === '127.0.0.1';
  const isCloudHost = dbHost === '150.241.244.130';
  
  // On macOS localhost, PostgreSQL often has no "postgres" role — use current user if DB_USER not set
  // For cloud DB, default to "lab" user
  let defaultUser = 'postgres';
  if (isLocalHost && process.env.USER) {
    defaultUser = process.env.USER;
  } else if (isCloudHost) {
    defaultUser = 'lab';
  }
  
  // Real trading data is in "olab" (same as Final_olab_database.py). Use DB_NAME=labdb2 for demo/seed data.
  const defaultDb = isCloudHost ? 'olab' : 'labdb2';
  return {
    host: dbHost,
    port: parseInt(process.env.DB_PORT || '5432', 10),
    user: process.env.DB_USER || defaultUser,
    password: process.env.DB_PASSWORD || (isCloudHost ? 'IndiaNepal1-' : ''),
    database: process.env.DB_NAME || defaultDb,
    connectionTimeoutMillis: 10000,
    idleTimeoutMillis: 30000,
    max: 10,
  };
}
const dbConfig = buildDbConfig();
console.log("[SERVER] Allowed CORS origins:", allowedOrigins.join(", "));
if (process.env.DATABASE_URL) {
  console.log("[DB] Using DATABASE_URL (e.g. Render) — cloud will show same data as Render");
} else {
  const hostType = dbConfig.host === '150.241.244.130' ? 'CLOUD' : (dbConfig.host === 'localhost' ? 'LOCAL' : 'REMOTE');
  console.log(`[DB] Using ${hostType} database — host: ${dbConfig.host}, database: ${dbConfig.database}, user: ${dbConfig.user}`);
}
if (dbConfig.database !== 'olab' && dbConfig.host === '150.241.244.130') {
  console.warn("[DB] ⚠️ Cloud server should use database=olab for real data. Current:", dbConfig.database);
}

// ✅ Retry PostgreSQL Connection Until Successful (try non-SSL first when using localhost, like Render)
function getConnectionConfigs() {
  const isLocal = !dbConfig.host || dbConfig.host === 'localhost' || dbConfig.host === '127.0.0.1';
  const isCloud = dbConfig.host === '150.241.244.130';
  
  if (isLocal) {
    return [
      { ...dbConfig, ssl: false },
      { ...dbConfig, ssl: { rejectUnauthorized: false } },
      { ...dbConfig, ssl: { rejectUnauthorized: false, sslmode: 'require' } },
    ];
  }
  
  // Cloud DB (150.241.244.130) - try non-SSL first (same as Python code)
  if (isCloud) {
    return [
      { ...dbConfig, ssl: false },
      { ...dbConfig, ssl: { rejectUnauthorized: false } },
    ];
  }
  
  // Other remote hosts - try SSL first
  return [
    { ...dbConfig, ssl: { rejectUnauthorized: false } },
    { ...dbConfig, ssl: { rejectUnauthorized: false, sslmode: 'require' } },
    { ...dbConfig, ssl: false },
  ];
}

const MAX_DB_RETRY_ROUNDS = 2; // then resolve with null so API doesn't hang

async function connectWithRetry(round = 0) {
  const configs = getConnectionConfigs();

  for (let i = 0; i < configs.length; i++) {
    const config = configs[i];
    try {
      console.log(`🔧 Attempt ${i + 1}: PostgreSQL connection to:`, `${config.host}:${config.port}/${config.database} (user: ${config.user})`);
      
      const pool = new Pool(config);
      await pool.query('SELECT NOW()');
      console.log(`✅ Connected to PostgreSQL successfully with config ${i + 1}`);
      const countResult = await pool.query('SELECT count(*) as c FROM alltraderecords').catch(() => ({ rows: [{ c: 0 }] }));
      const tradeCount = parseInt(countResult.rows[0]?.c || 0, 10);
      console.log(`[DB] alltraderecords has ${tradeCount} rows — dashboard will show ${tradeCount} trades`);
      return pool;
    } catch (err) {
      console.error(`❌ PostgreSQL Connection Failed (attempt ${i + 1}):`, err.message);
      
      if (i === configs.length - 1) {
        if (round < MAX_DB_RETRY_ROUNDS - 1) {
          console.error("   All configs failed. Retrying in 5 seconds...");
          await new Promise((resolve) => setTimeout(resolve, 5000));
          return connectWithRetry(round + 1);
        }
        console.error("   Giving up after " + MAX_DB_RETRY_ROUNDS + " rounds. API will run without DB (trades/debug will return empty). Set DATABASE_URL or DB_* to fix.");
        return null;
      }
      console.log(`   Trying next configuration...`);
    }
  }
  return null;
}

let poolPromise = connectWithRetry();

// ✅ lab_settings: store action_password for confirming sensitive actions (Auto-Pilot, Execute, End Trade, etc.)
// Set in DB: INSERT INTO lab_settings (key, value) VALUES ('action_password', 'your_secret') ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();
const LAB_SETTINGS_TABLE = "lab_settings";
const ACTION_PASSWORD_KEY = "action_password";

async function ensureLabSettingsTable(pool) {
  if (!pool) return;
  try {
    await pool.query(`
      CREATE TABLE IF NOT EXISTS ${LAB_SETTINGS_TABLE} (
        key TEXT PRIMARY KEY,
        value TEXT,
        updated_at TIMESTAMPTZ DEFAULT NOW()
      );
    `);
  } catch (e) {
    console.error("[lab_settings] Failed to create table:", e.message);
  }
}

/** Returns the stored action password from DB, or null if not set. */
async function getActionPasswordFromDb(pool) {
  if (!pool) return null;
  try {
    await ensureLabSettingsTable(pool);
    const r = await pool.query(
      `SELECT value FROM ${LAB_SETTINGS_TABLE} WHERE key = $1`,
      [ACTION_PASSWORD_KEY]
    );
    const v = r.rows[0]?.value;
    return typeof v === "string" ? v.trim() : null;
  } catch (e) {
    console.error("[lab_settings] getActionPassword error:", e.message);
    return null;
  }
}

/** Returns true if submitted password is valid for actions.
 * Accepts (1) the logged-in user's password (users table + crypt), or (2) action_password from lab_settings.
 * userIdOptional: current user id from req.user.id; if provided, we check users.password_hash = crypt(submitted, password_hash) first. */
async function validateActionPassword(pool, submitted, userIdOptional) {
  if (typeof submitted !== "string" || !submitted.trim()) return false;
  const pw = submitted.trim();

  // 1) If we know the logged-in user, accept their login password (same as /auth/login)
  if (pool && userIdOptional) {
    try {
      const r = await pool.query(
        `SELECT 1 FROM users WHERE id = $1 AND is_active = TRUE AND password_hash = crypt($2, password_hash)`,
        [userIdOptional, pw]
      );
      if (r.rows && r.rows.length > 0) return true;
    } catch (e) {
      console.error("[lab_settings] validateActionPassword user check:", e.message);
    }
  }

  // 2) Otherwise fall back to action_password in lab_settings
  const stored = await getActionPasswordFromDb(pool);
  if (stored != null && stored !== "" && pw === stored) return true;
  return false;
}

// ✅ alert_rule_books: store named rule books (rules + groups + masterBlinkColor) on the server
const ALERT_RULE_BOOKS_TABLE = "alert_rule_books";

async function ensureAlertRuleBooksTable(pool) {
  if (!pool) return;
  try {
    await pool.query(`
      CREATE TABLE IF NOT EXISTS ${ALERT_RULE_BOOKS_TABLE} (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        payload JSONB NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
      );
    `);
  } catch (e) {
    console.error("[alert_rule_books] Failed to create table:", e.message);
  }
}

// ✅ ui_settings: per user + theme profile (Anish, Loveleet, or custom)
const UI_SETTINGS_TABLE = "ui_settings";
const THEME_PROFILES_TABLE = "theme_profiles";

async function ensureThemeProfilesTable(pool) {
  if (!pool) return;
  try {
    await pool.query(`
      CREATE TABLE IF NOT EXISTS ${THEME_PROFILES_TABLE} (
        id SERIAL PRIMARY KEY,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE (user_id, name)
      );
    `);
    await pool.query(`CREATE INDEX IF NOT EXISTS idx_theme_profiles_user ON ${THEME_PROFILES_TABLE}(user_id);`);
  } catch (e) {
    console.error("[theme_profiles] Failed to create table:", e.message);
  }
}

/** Ensure default theme profiles "Anish" and "Loveleet" exist for user. */
async function ensureDefaultThemeProfiles(pool, userId) {
  if (!pool || !userId) return [];
  const uid = String(userId);
  for (const name of ["Anish", "Loveleet"]) {
    try {
      await pool.query(
        `INSERT INTO ${THEME_PROFILES_TABLE} (user_id, name) VALUES ($1, $2) ON CONFLICT (user_id, name) DO NOTHING`,
        [uid, name]
      );
    } catch (e) {
      console.warn("[theme_profiles] ensure default:", e.message);
    }
  }
  const r = await pool.query(`SELECT id, name FROM ${THEME_PROFILES_TABLE} WHERE user_id = $1 ORDER BY id`, [uid]);
  return r.rows || [];
}

async function ensureUiSettingsTable(pool) {
  if (!pool) return;
  try {
    await ensureThemeProfilesTable(pool);
    await pool.query(`
      CREATE TABLE IF NOT EXISTS ${UI_SETTINGS_TABLE} (
        id SERIAL PRIMARY KEY,
        user_id TEXT,
        key TEXT NOT NULL,
        value JSONB NOT NULL,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
      );
    `);
    await pool.query(`
      DO $$ BEGIN
        IF NOT EXISTS (
          SELECT 1 FROM information_schema.columns
          WHERE table_schema = 'public' AND table_name = '${UI_SETTINGS_TABLE}' AND column_name = 'theme_profile_id'
        ) THEN
          ALTER TABLE ${UI_SETTINGS_TABLE} ADD COLUMN theme_profile_id INT NULL;
        END IF;
      END $$;
    `);
    await pool.query(`DROP INDEX IF EXISTS ui_settings_user_key_idx;`);
    await pool.query(`
      DO $$
      BEGIN
        IF NOT EXISTS (
          SELECT 1 FROM pg_indexes
          WHERE schemaname = 'public' AND indexname = 'ui_settings_user_theme_key_idx'
        ) THEN
          CREATE UNIQUE INDEX ui_settings_user_theme_key_idx
          ON ${UI_SETTINGS_TABLE} (user_id, theme_profile_id, key);
        END IF;
      END$$;
    `);
  } catch (e) {
    console.error("[ui_settings] Failed to create/alter table:", e.message);
  }
}

// ✅ Health Check (for monitoring)
app.get("/api/health", (req, res) => {
  res.send("✅ Backend is working!");
});

// ✅ Auth: login only from DB (users table + crypt); no hardcoded credentials.
const AUTH_SESSION_COOKIE = "lab_session";
const SESSION_DURATION_DAYS = 7;

app.post("/auth/login", async (req, res) => {
  const email = (req.body?.email || "").trim().toLowerCase();
  const password = req.body?.password ?? "";
  if (!email || !password) {
    return res.status(400).json({ error: "email and password required" });
  }
  try {
    const pool = await poolPromise;
    if (!pool) return res.status(503).json({ error: "Database not connected" });
    // Validate with same logic as your SQL: is_active, locked_until, crypt(password, password_hash)
    const userResult = await pool.query(
      `SELECT id, email FROM users
       WHERE email = $1 AND is_active = TRUE
         AND (locked_until IS NULL OR locked_until <= NOW())
         AND password_hash = crypt($2, password_hash)`,
      [email, password]
    );
    if (!userResult.rows?.length) {
      return res.status(401).json({ error: "Invalid credentials" });
    }
    const user = userResult.rows[0];
    const expiresAt = new Date(Date.now() + SESSION_DURATION_DAYS * 24 * 60 * 60 * 1000);
    const sessionResult = await pool.query(
      `INSERT INTO sessions (user_id, expires_at) VALUES ($1, $2) RETURNING id`,
      [user.id, expiresAt]
    );
    const sessionId = sessionResult.rows[0]?.id;
    if (!sessionId) return res.status(500).json({ error: "Failed to create session" });
    const isProduction = process.env.NODE_ENV === "production";
    res.cookie(AUTH_SESSION_COOKIE, sessionId, {
      httpOnly: true,
      secure: isProduction,
      sameSite: isProduction ? "none" : "lax",
      maxAge: SESSION_DURATION_DAYS * 24 * 60 * 60 * 1000,
      path: "/",
    });
    res.json({ ok: true, user: { id: user.id, email: user.email } });
  } catch (e) {
    console.error("[auth] login error:", e.message);
    res.status(500).json({ error: e.code === "42P01" ? "Auth tables missing (run server/sql/sessions.sql)" : "Login failed" });
  }
});

app.get("/auth/me", async (req, res) => {
  const sessionId = req.cookies?.[AUTH_SESSION_COOKIE];
  if (!sessionId) return res.status(401).json({ error: "Not logged in" });
  try {
    const pool = await poolPromise;
    if (!pool) return res.status(503).json({ error: "Database not connected" });
    const result = await pool.query(
      `SELECT s.id AS session_id, s.expires_at, u.id AS user_id, u.email
       FROM sessions s
       JOIN users u ON u.id = s.user_id
       WHERE s.id = $1`,
      [sessionId]
    );
    if (!result.rows?.length || new Date(result.rows[0].expires_at) < new Date()) {
      res.clearCookie(AUTH_SESSION_COOKIE, { path: "/" });
      return res.status(401).json({ error: "Session expired" });
    }
    const row = result.rows[0];
    res.json({ ok: true, user: { id: row.user_id, email: row.email } });
  } catch (e) {
    console.error("[auth] me error:", e.message);
    res.status(500).json({ error: "Session check failed" });
  }
});

app.post("/auth/logout", async (req, res) => {
  const sessionId = req.cookies?.[AUTH_SESSION_COOKIE];
  if (sessionId) {
    try {
      const pool = await poolPromise;
      if (pool) await pool.query("DELETE FROM sessions WHERE id = $1", [sessionId]);
    } catch (e) { /* ignore */ }
  }
  res.clearCookie(AUTH_SESSION_COOKIE, { path: "/" });
  res.json({ ok: true });
});

// Extend session (e.g. when user clicks "Stay logged in" after 1 hour)
app.post("/auth/extend-session", async (req, res) => {
  const sessionId = req.cookies?.[AUTH_SESSION_COOKIE];
  if (!sessionId) return res.status(401).json({ error: "Not logged in" });
  try {
    const pool = await poolPromise;
    if (!pool) return res.status(503).json({ error: "Database not connected" });
    const result = await pool.query(
      `SELECT s.id FROM sessions s JOIN users u ON u.id = s.user_id WHERE s.id = $1 AND s.expires_at > NOW()`,
      [sessionId]
    );
    if (!result.rows?.length) return res.status(401).json({ error: "Session expired" });
    const newExpiresAt = new Date(Date.now() + SESSION_DURATION_DAYS * 24 * 60 * 60 * 1000);
    await pool.query("UPDATE sessions SET expires_at = $1 WHERE id = $2", [newExpiresAt, sessionId]);
    res.json({ ok: true });
  } catch (e) {
    console.error("[auth] extend-session error:", e.message);
    res.status(500).json({ error: "Failed to extend session" });
  }
});

// ✅ Auth middleware: protect /api/* routes (except those defined before this point, e.g. /api/health)
async function requireAuth(req, res, next) {
  const sessionId = req.cookies?.[AUTH_SESSION_COOKIE];
  if (!sessionId) {
    return res.status(401).json({ error: "Not logged in" });
  }
  try {
    const pool = await poolPromise;
    if (!pool) return res.status(503).json({ error: "Database not connected" });
    const result = await pool.query(
      `SELECT s.id AS session_id, s.expires_at, u.id AS user_id, u.email
       FROM sessions s
       JOIN users u ON u.id = s.user_id
       WHERE s.id = $1`,
      [sessionId]
    );
    if (!result.rows?.length || new Date(result.rows[0].expires_at) < new Date()) {
      res.clearCookie(AUTH_SESSION_COOKIE, { path: "/" });
      return res.status(401).json({ error: "Session expired" });
    }
    const row = result.rows[0];
    req.user = { id: row.user_id, email: row.email };
    return next();
  } catch (e) {
    console.error("[auth] middleware error:", e.message);
    return res.status(500).json({ error: "Auth check failed" });
  }
}

// Optional: allow these endpoints without auth so Information/Binance Data panels load when session cookie isn't sent (e.g. cross-origin)
const ALLOW_PUBLIC_READ_SIGNALS = String(process.env.ALLOW_PUBLIC_READ_SIGNALS || "").toLowerCase() === "true";
if (ALLOW_PUBLIC_READ_SIGNALS) {
  console.log("[SERVER] ALLOW_PUBLIC_READ_SIGNALS=true — pairstatus, active-loss, open-position, calculate-signals are public");
}

function optionalAuth(req, res, next) {
  const url = (req.originalUrl || req.url || "").split("?")[0];
  if (ALLOW_PUBLIC_READ_SIGNALS && /\/api\/(pairstatus|active-loss|open-position|calculate-signals)$/.test(url)) {
    return next();
  }
  return requireAuth(req, res, next);
}

app.use("/api", optionalAuth);

// ✅ Protected: set log path (requires auth)
app.post("/api/set-log-path", (req, res) => {
  const { path } = req.body;
  if (fs.existsSync(path)) {
    currentLogPath = path;
    console.log("✅ Log path updated to:", currentLogPath);
    res.json({ success: true, message: "Log path updated." });
  } else {
    res.status(400).json({ success: false, message: "Invalid path" });
  }
});

// ✅ Server config check (no secrets) — verify cloud has CORS + olab; call from browser or: curl http://your-cloud-ip:10000/api/server-info
app.get("/api/server-info", (req, res) => {
  const requestOrigin = req.headers.origin || "(no origin header)";
  const isAllowed = !requestOrigin || requestOrigin === "(no origin header)" || allowedOrigins.includes(requestOrigin);
  res.json({
    ok: true,
    allowedOrigins,
    database: dbConfig.database,
    dbHost: dbConfig.host,
    hasGitHubPagesOrigin: allowedOrigins.includes("https://loveleet.github.io"),
    requestOrigin,
    requestOriginAllowed: isAllowed,
    message: allowedOrigins.includes("https://loveleet.github.io") && dbConfig.database === "olab"
      ? "Cloud server config OK for GitHub Pages (CORS + olab)"
      : "Update server.js on cloud: need correct CORS origins and DB=olab",
  });
});

// ✅ Alert Rule Books (server-side rule scripts)
app.get("/api/alert-rule-books", async (req, res) => {
  try {
    const pool = await poolPromise;
    if (!pool) return res.json({ ruleBooks: [] });
    await ensureAlertRuleBooksTable(pool);
    const result = await pool.query(
      `SELECT id, name, created_at, updated_at FROM ${ALERT_RULE_BOOKS_TABLE} ORDER BY updated_at DESC, id DESC`
    );
    res.json({ ruleBooks: result.rows || [] });
  } catch (e) {
    console.error("[alert_rule_books] list error:", e);
    res.status(500).json({ error: e.message || "Failed to fetch rule books" });
  }
});

app.get("/api/alert-rule-books/:id", async (req, res) => {
  const id = parseInt(req.params.id, 10);
  if (!Number.isFinite(id)) {
    return res.status(400).json({ error: "Invalid rule book id" });
  }
  try {
    const pool = await poolPromise;
    if (!pool) return res.status(500).json({ error: "Database not connected" });
    await ensureAlertRuleBooksTable(pool);
    const result = await pool.query(
      `SELECT id, name, payload, created_at, updated_at FROM ${ALERT_RULE_BOOKS_TABLE} WHERE id = $1 LIMIT 1`,
      [id]
    );
    if (!result.rows.length) {
      return res.status(404).json({ error: "Rule book not found" });
    }
    const row = result.rows[0];
    res.json({
      id: row.id,
      name: row.name,
      createdAt: row.created_at,
      updatedAt: row.updated_at,
      payload: row.payload || {},
    });
  } catch (e) {
    console.error("[alert_rule_books] get error:", e);
    res.status(500).json({ error: e.message || "Failed to fetch rule book" });
  }
});

app.post("/api/alert-rule-books", async (req, res) => {
  const body = req.body || {};
  const id = body.id != null ? parseInt(body.id, 10) : null;
  const name = (body.name || "").trim();
  const payload = body.payload || {};

  if (!name) {
    return res.status(400).json({ error: "name is required" });
  }
  if (typeof payload !== "object") {
    return res.status(400).json({ error: "payload must be an object" });
  }

  try {
    const pool = await poolPromise;
    if (!pool) return res.status(500).json({ error: "Database not connected" });
    await ensureAlertRuleBooksTable(pool);

    if (id && Number.isFinite(id)) {
      const result = await pool.query(
        `UPDATE ${ALERT_RULE_BOOKS_TABLE}
         SET name = $1, payload = $2, updated_at = NOW()
         WHERE id = $3
         RETURNING id, name, created_at, updated_at`,
        [name, payload, id]
      );
      if (!result.rows.length) {
        return res.status(404).json({ error: "Rule book not found for update" });
      }
      return res.json({ ok: true, ruleBook: result.rows[0] });
    }

    const result = await pool.query(
      `INSERT INTO ${ALERT_RULE_BOOKS_TABLE} (name, payload)
       VALUES ($1, $2)
       RETURNING id, name, created_at, updated_at`,
      [name, payload]
    );
    return res.json({ ok: true, ruleBook: result.rows[0] });
  } catch (e) {
    console.error("[alert_rule_books] upsert error:", e);
    res.status(500).json({ error: e.message || "Failed to save rule book" });
  }
});

// Theme profiles and UI settings are now stored in localStorage only (no server endpoints).

// ✅ Auto-Pilot state (in-memory by unique_id; replace with DB write/read if needed)
const autopilotStore = new Map();
app.get("/api/autopilot", (req, res) => {
  const unique_id = (req.query.unique_id || "").trim();
  if (!unique_id) return res.status(400).json({ error: "unique_id required" });
  const entry = autopilotStore.get(unique_id);
  res.json({ enabled: !!(entry && entry.enabled) });
});
app.post("/api/autopilot", async (req, res) => {
  const { unique_id, password, enabled } = req.body || {};
  if (!(unique_id && typeof unique_id === "string")) return res.status(400).json({ error: "unique_id required" });
  const pool = await poolPromise;
  const userId = req.user && req.user.id;
  const valid = await validateActionPassword(pool, password, userId);
  if (!valid) {
    return res.status(403).json({ error: "Invalid password. Use your login password or set action_password in lab_settings." });
  }
  autopilotStore.set(unique_id.trim(), { enabled: !!enabled, updatedAt: new Date().toISOString() });
  res.json({ ok: true, enabled: !!enabled });
});

// ✅ Action routes: validate password (logged-in user's password or lab_settings action_password)
function requireActionPassword(req, res, next) {
  (async () => {
    const password = (req.body && req.body.password) || "";
    const pool = await poolPromise;
    const userId = req.user && req.user.id;
    const valid = await validateActionPassword(pool, password, userId);
    if (!valid) {
      return res.status(403).json({ error: "Invalid password. Use your login password or set action_password in lab_settings." });
    }
    next();
  })().catch(next);
}

app.post("/api/execute", requireActionPassword, (req, res) => {
  // TODO: proxy to Python/trading API when available
  res.status(501).json({ error: "Password accepted. Execute is not yet connected to the trading system." });
});
app.post("/api/end-trade", requireActionPassword, (req, res) => {
  res.status(501).json({ error: "Password accepted. End-trade is not yet connected to the trading system." });
});
app.post("/api/hedge", requireActionPassword, (req, res) => {
  res.status(501).json({ error: "Password accepted. Hedge is not yet connected to the trading system." });
});
app.post("/api/stop-price", requireActionPassword, (req, res) => {
  res.status(501).json({ error: "Password accepted. Stop-price is not yet connected to the trading system." });
});
app.post("/api/add-investment", requireActionPassword, (req, res) => {
  res.status(501).json({ error: "Password accepted. Add-investment is not yet connected to the trading system." });
});
app.post("/api/clear", requireActionPassword, (req, res) => {
  res.status(501).json({ error: "Password accepted. Clear is not yet connected to the trading system." });
});

// ✅ Debug: table row counts (no secrets)
app.get("/api/debug", async (req, res) => {
  try {
    const pool = await poolPromise;
    if (!pool) return res.json({ ok: false, error: "Database not connected" });
    const tables = ["alltraderecords", "machines", "pairstatus", "signalprocessinglogs", "bot_event_log"];
    const counts = {};
    const sampleData = {};
    for (const table of tables) {
      try {
        const r = await pool.query(`SELECT count(*) as c FROM ${table}`);
        counts[table] = parseInt(r.rows[0]?.c ?? 0, 10);
        // Get sample row if table has data
        if (counts[table] > 0) {
          try {
            const sample = await pool.query(`SELECT * FROM ${table} LIMIT 1`);
            if (sample.rows.length > 0) {
              sampleData[table] = {
                columns: Object.keys(sample.rows[0]),
                hasData: true
              };
            }
          } catch (e) {
            sampleData[table] = { error: e.message };
          }
        } else {
          sampleData[table] = { hasData: false };
        }
      } catch (e) {
        counts[table] = e.code === "42P01" ? "missing" : e.message;
        sampleData[table] = { error: e.code === "42P01" ? "table missing" : e.message };
      }
    }
    const tradesEmpty = counts.alltraderecords === 0 || counts.alltraderecords === "missing";
    res.json({ 
      ok: true, 
      counts, 
      sampleData,
      dbConfig: {
        host: dbConfig.host,
        port: dbConfig.port,
        database: dbConfig.database,
        user: dbConfig.user,
        usingDATABASE_URL: !!process.env.DATABASE_URL
      },
      hint: tradesEmpty ? "alltraderecords is empty or missing — copy DB or add data to see trades" : null 
    });
  } catch (e) {
    res.json({ ok: false, error: e.message, stack: e.stack });
  }
});

// ✅ Test DB: Get sample rows from key tables
app.get("/api/test-db", async (req, res) => {
  try {
    const pool = await poolPromise;
    if (!pool) {
      return res.json({ ok: false, error: "Database pool not available" });
    }
    
    // Test connection
    const connectionTest = await pool.query('SELECT NOW() as current_time, version() as pg_version');
    
    // Get sample from alltraderecords
    let tradesSample = [];
    try {
      const tradesResult = await pool.query('SELECT * FROM alltraderecords LIMIT 3');
      tradesSample = tradesResult.rows;
    } catch (e) {
      tradesSample = [{ error: e.message, code: e.code }];
    }
    
    // Get sample from signalprocessinglogs
    let signalsSample = [];
    try {
      const signalsResult = await pool.query('SELECT * FROM signalprocessinglogs ORDER BY created_at DESC LIMIT 3');
      signalsSample = signalsResult.rows;
    } catch (e) {
      signalsSample = [{ error: e.message, code: e.code }];
    }
    
    res.json({
      ok: true,
      connection: {
        connected: true,
        currentTime: connectionTest.rows[0].current_time,
        pgVersion: connectionTest.rows[0].pg_version.split(' ')[0] + ' ' + connectionTest.rows[0].pg_version.split(' ')[1]
      },
      samples: {
        alltraderecords: tradesSample,
        signalprocessinglogs: signalsSample
      },
      message: tradesSample.length > 0 && !tradesSample[0].error 
        ? `✅ Database is returning data — found ${tradesSample.length} sample trade(s)`
        : "⚠️ Database connection works but alltraderecords table is empty or missing"
    });
  } catch (e) {
    res.json({ ok: false, error: e.message, code: e.code, stack: e.stack });
  }
});

// ✅ API: Fetch All Trades
// ✅ API: Fetch SuperTrend Signals (returns empty if table missing so dashboard doesn't 500)
app.get("/api/supertrend", async (req, res) => {
  try {
    const pool = await poolPromise;
    if (!pool) return res.json({ supertrend: [] });
    const result = await pool.query(
      'SELECT source, trend, timestamp FROM supertrend ORDER BY timestamp DESC LIMIT 10;'
    );
    res.json({ supertrend: result.rows || [] });
  } catch (error) {
    if (isMissingTable(error)) {
      console.log("[SuperTrend] Table supertrend missing — returning empty");
      return res.json({ supertrend: [] });
    }
    console.error("❌ [SuperTrend] Error:", error.message);
    res.status(500).json({ error: error.message || "Failed to fetch SuperTrend data" });
  }
});
// Helper: true if error is "table does not exist"
function isMissingTable(err) {
  return err && (err.code === "42P01" || (err.message && err.message.includes("does not exist")));
}

app.get("/api/trades", async (req, res) => {
  try {
    const pool = await poolPromise;
    if (!pool) {
      console.log("[Trades] ❌ No pool — returning empty");
      return res.json({ trades: [], _meta: { count: 0, table: "alltraderecords", error: "pool not available" } });
    }
    
    // Test connection first
    try {
      await pool.query('SELECT 1');
    } catch (connErr) {
      console.error("[Trades] ❌ Connection test failed:", connErr.message);
      return res.json({ trades: [], _meta: { count: 0, table: "alltraderecords", error: "connection failed", details: connErr.message } });
    }
    
    const result = await pool.query("SELECT * FROM alltraderecords ORDER BY created_at DESC NULLS LAST, unique_id DESC;");
    const count = result.rows.length;
    
    console.log(`[Trades] ✅ Fetched ${count} rows from alltraderecords`);
    if (count > 0) {
      console.log(`[Trades] Sample columns: ${Object.keys(result.rows[0]).join(', ')}`);
      console.log(`[Trades] First trade pair: ${result.rows[0].pair || 'N/A'}, created_at: ${result.rows[0].created_at || 'N/A'}`);
    } else {
      console.log("[Trades] ⚠️ Table is empty — dashboard will show no trade rows until data is added or DB is copied.");
    }
    
    res.json({ trades: result.rows, _meta: { count, table: "alltraderecords", timestamp: new Date().toISOString() } });
  } catch (error) {
    if (isMissingTable(error)) {
      console.log("[Trades] ⚠️ Table alltraderecords missing — returning empty");
      return res.json({ trades: [], _meta: { count: 0, table: "alltraderecords", error: "table missing", code: error.code } });
    }
    console.error("❌ [Trades] Error:", error.message);
    console.error("❌ [Trades] Error code:", error.code);
    console.error("❌ [Trades] Error stack:", error.stack);
    res.status(500).json({ error: error.message || "Failed to fetch trades", code: error.code });
  }
});

// ✅ API: Fetch single trade by unique_id (for Live Trade view polling)
app.get("/api/trade", async (req, res) => {
  const unique_id = (req.query.unique_id || "").trim();
  if (!unique_id) return res.status(400).json({ error: "unique_id query required" });
  try {
    const pool = await poolPromise;
    if (!pool) return res.status(500).json({ error: "Database not connected" });
    const result = await pool.query(
      "SELECT * FROM alltraderecords WHERE unique_id = $1 OR \"Unique_ID\" = $1 LIMIT 1",
      [unique_id]
    );
    const trade = result.rows[0] || null;
    res.json({ trade });
  } catch (error) {
    if (isMissingTable(error)) return res.json({ trade: null });
    console.error("❌ [Trade] Error:", error.message);
    res.status(500).json({ error: error.message || "Failed to fetch trade" });
  }
});

// ✅ API: Fetch Machines
app.get("/api/machines", async (req, res) => {
  try {
    const pool = await poolPromise;
    if (!pool) return res.json({ machines: [] });
    const result = await pool.query("SELECT machineid, active FROM machines;");
    res.json({ machines: result.rows });
  } catch (error) {
    if (isMissingTable(error)) return res.json({ machines: [] });
    console.error("❌ Query Error (/api/machines):", error.message);
    res.status(500).json({ error: error.message || "Failed to fetch machines" });
  }
});

// ✅ API: Fetch EMA Trend Data from pairstatus
app.get("/api/pairstatus", async (req, res) => {
  try {
    const pool = await poolPromise;
    if (!pool) return res.json({});
    const result = await pool.query(`
      SELECT overall_ema_trend_1m, overall_ema_trend_percentage_1m,
             overall_ema_trend_5m, overall_ema_trend_percentage_5m,
             overall_ema_trend_15m, overall_ema_trend_percentage_15m
      FROM pairstatus
      LIMIT 1;
    `);
    res.json(result.rows[0] || {});
  } catch (error) {
    if (isMissingTable(error)) return res.json({});
    console.error("❌ Query Error (/api/pairstatus):", error.message);
    res.status(500).json({ error: error.message || "Failed to fetch pairstatus" });
  }
});

// ✅ API: Fetch Active Loss/Condition flags (e.g., BUY/SELL booleans)
// Expected table: active_loss with columns like buy, sell (bool/int/text) where id=1
const defaultActiveLoss = { id: 1, buy: false, sell: false, buy_condition: false, sell_condition: false, buyflag: false, sellflag: false };
app.get("/api/active-loss", async (req, res) => {
  try {
    const pool = await poolPromise;
    if (!pool) {
      return res.json(defaultActiveLoss);
    }
    const result = await pool.query(`
      SELECT *
      FROM active_loss
      WHERE id = 1
      LIMIT 1;
    `);
    const row = result.rows?.[0] || defaultActiveLoss;
    res.json(row);
  } catch (error) {
    if (error.code === "42P01" || (error.message && error.message.includes("does not exist"))) {
      return res.json(defaultActiveLoss);
    }
    console.error("❌ Query Error (/api/active-loss):", error.message);
    res.status(500).json({ error: error.message || "Failed to fetch active loss flags" });
  }
});

// ✅ Binance Proxy Endpoint (always use local/cloud server, no Render)
const LOCAL_PROXY = `http://localhost:${process.env.PORT || 10000}/api/klines`;

app.get('/api/klines', async (req, res) => {
  try {
    const { symbol, interval, limit } = req.query;
    const url = `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=${limit || 200}`;
    const { data } = await axios.get(url);
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.toString() });
  }
});

// ✅ Proxy to Python CalculateSignals API (run python/api_signals.py on cloud, e.g. port 5001)
const PYTHON_SIGNALS_URL = process.env.PYTHON_SIGNALS_URL || "http://localhost:5001";
if (!process.env.PYTHON_SIGNALS_URL) {
  console.warn("[SERVER] PYTHON_SIGNALS_URL not set — using default http://localhost:5001. Set it in /etc/lab-trading-dashboard.secrets.env on the cloud for Information/Binance Data sections.");
} else {
  console.log("[SERVER] PYTHON_SIGNALS_URL =", PYTHON_SIGNALS_URL);
}

// Proxy to Python getOpenPosition(symbol) for live exchange data
app.get("/api/open-position", async (req, res) => {
  try {
    const symbol = (req.query.symbol || "").trim().toUpperCase();
    if (!symbol) return res.status(400).json({ ok: false, message: "symbol query param required" });
    const resp = await fetch(`${PYTHON_SIGNALS_URL}/api/open-position?symbol=${encodeURIComponent(symbol)}`, {
      method: "GET",
      signal: AbortSignal.timeout(15000),
    });
    const data = await resp.json().catch(() => ({}));
    res.status(resp.status || 200).json(data);
  } catch (err) {
    console.error("[open-position] Proxy error:", err.message);
    res.status(502).json({ ok: false, message: err.message || "Python signals service unavailable" });
  }
});

// Proxy to Python sync-open-positions (getAllOpenPosition → exchange_trade sync)
app.get("/api/sync-open-positions", async (req, res) => {
  try {
    console.log("[sync-open-positions] Calling Python API:", PYTHON_SIGNALS_URL + "/api/sync-open-positions");
    const SYNC_POSITIONS_TIMEOUT_MS = Number(process.env.SYNC_POSITIONS_TIMEOUT_MS) || 180000; // 3 min
    const resp = await fetch(`${PYTHON_SIGNALS_URL}/api/sync-open-positions`, {
      method: "GET",
      signal: AbortSignal.timeout(SYNC_POSITIONS_TIMEOUT_MS),
    });
    const data = await resp.json().catch(() => ({}));
    const positionsCount = data.positions_count ?? "?";
    const inserted = data.inserted_count ?? 0;
    const alreadyExisted = data.already_existed_count ?? "?";
    console.log("[sync-open-positions] positions from getAllOpenPosition =", positionsCount);
    console.log("[sync-open-positions] already existed in exchange_trade (skipped) =", alreadyExisted);
    console.log("[sync-open-positions] insert success count =", inserted);
    res.status(resp.status || 200).json(data);
  } catch (err) {
    console.error("[sync-open-positions] Proxy error:", err.message);
    res.status(502).json({ ok: false, message: err.message || "Python signals service unavailable" });
  }
});

// Health check for Python signals (so you can open https://api.clubinfotech.com/api/calculate-signals/health in browser)
app.get("/api/calculate-signals/health", async (req, res) => {
  try {
    const resp = await fetch(`${PYTHON_SIGNALS_URL}/api/calculate-signals/health`, { signal: AbortSignal.timeout(5000) });
    const data = await resp.json().catch(() => ({}));
    res.status(resp.status || 200).json(data);
  } catch (err) {
    res.status(502).json({ ok: false, message: err.message || "Python signals service unreachable" });
  }
});

// Proxy to Python /api/calculate-signals for the signals grid
app.post("/api/calculate-signals", async (req, res) => {
  try {
    console.log("[calculate-signals] Request body:", JSON.stringify(req.body));
    const resp = await fetch(`${PYTHON_SIGNALS_URL}/api/calculate-signals`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req.body),
      signal: AbortSignal.timeout(Number(process.env.CALCULATE_SIGNALS_TIMEOUT_MS) || 300000), // 5 min default
    });
    const data = await resp.json().catch(() => ({}));
    console.log("[calculate-signals] Python API response:", JSON.stringify(data, null, 2));
    res.status(resp.status || 200).json(data);
  } catch (err) {
    console.error("[calculate-signals] Proxy error:", err.message);
    res.status(502).json({ ok: false, message: err.message || "Python signals service unavailable" });
  }
});

// ✅ API: Fetch Signal Processing Logs with Pagination and Filtering
app.get("/api/SignalProcessingLogs", async (req, res) => {
  try {
    console.log("🔍 [SignalProcessingLogs] Request received:", req.query);
    const pool = await poolPromise;
    if (!pool) throw new Error("Database not connected");
    
    // Parse query parameters
    const page = parseInt(req.query.page) || 1;
    const limit = req.query.limit === 'all' ? 'all' : (parseInt(req.query.limit) || 50);
    const offset = (page - 1) * (limit === 'all' ? 0 : limit);
    
    // Build WHERE clause for filters
    let whereConditions = [];
    let params = [];
    let paramIndex = 1;
    
    // Symbol filter
    if (req.query.symbol) {
      whereConditions.push(`symbol LIKE $${paramIndex}`);
      params.push(`%${req.query.symbol}%`);
      paramIndex++;
    }
    // Signal type filter
    if (req.query.signalType) {
      whereConditions.push(`signal_type LIKE $${paramIndex}`);
      params.push(`%${req.query.signalType}%`);
      paramIndex++;
    }
    // Machine filter
    if (req.query.machineId) {
      whereConditions.push(`machine_id = $${paramIndex}`);
      params.push(req.query.machineId);
      paramIndex++;
    }
    // Date range filter
    if (req.query.fromDate) {
      whereConditions.push(`candle_time >= $${paramIndex}`);
      params.push(req.query.fromDate);
      paramIndex++;
    }
    if (req.query.toDate) {
      whereConditions.push(`candle_time <= $${paramIndex}`);
      params.push(req.query.toDate);
      paramIndex++;
    }
    // RSI range filter (from json_data, so not filterable in SQL directly)
    const whereClause = whereConditions.length > 0 ? `WHERE ${whereConditions.join(' AND ')}` : '';

    // --- Sorting logic ---
    const allowedSortKeys = [
      'candle_time', 'symbol', 'interval', 'signal_type', 'signal_source', 'candle_pattern', 'price',
      'squeeze_status', 'active_squeeze', 'processing_time_ms', 'machine_id', 'timestamp', 'created_at', 'unique_id'
    ];
    let sortKey = req.query.sortKey;
    let sortDirection = req.query.sortDirection && req.query.sortDirection.toUpperCase() === 'ASC' ? 'ASC' : 'DESC';
    if (!allowedSortKeys.includes(sortKey)) {
      sortKey = 'candle_time';
    }
    const orderByClause = `ORDER BY ${sortKey} ${sortDirection}`;
    
    // Build the query
    const countQuery = `SELECT COUNT(*) as total FROM signalprocessinglogs ${whereClause}`;
    const dataQuery = `
      SELECT 
        id,
        candle_time,
        symbol,
        interval,
        signal_type,
        signal_source,
        candle_pattern,
        price,
        squeeze_status,
        active_squeeze,
        processing_time_ms,
        machine_id,
        timestamp,
        json_data,
        created_at,
        unique_id
      FROM signalprocessinglogs 
      ${whereClause}
      ${orderByClause}
      ${limit === 'all' ? '' : `LIMIT ${limit} OFFSET ${offset}`}
    `;
    
    // Execute queries
    console.log("🔍 [SignalProcessingLogs] Count query:", countQuery);
    console.log("🔍 [SignalProcessingLogs] Data query:", dataQuery);
    console.log("🔍 [SignalProcessingLogs] Parameters:", params);
    
    const [countResult, dataResult] = await Promise.all([
      pool.query(countQuery, params),
      pool.query(dataQuery, params)
    ]);
    
    const total = parseInt(countResult.rows[0].total);
    const logs = dataResult.rows;
    
    console.log("🔍 [SignalProcessingLogs] Total records:", total);
    console.log("🔍 [SignalProcessingLogs] Fetched logs:", logs.length);
    
    // Parse JSON data for each log and extract extra fields
    const processedLogs = logs.map(log => {
      let extra = {};
      if (log.json_data) {
        try {
          const json = JSON.parse(log.json_data);
          extra = {
            rsi: json.rsi,
            macd: json.macd,
            trend: json.trend,
            action: json.action,
            status: json.status,
            // add more as needed
          };
        } catch (e) {}
      }
      return { ...log, ...extra };
    });
    
    console.log("🔍 [SignalProcessingLogs] Sending response with", processedLogs.length, "logs");
    res.json({
      logs: processedLogs,
      pagination: {
        page,
        limit,
        total,
        totalPages: limit === 'all' ? 1 : Math.ceil(total / limit),
        hasNext: limit === 'all' ? false : page < Math.ceil(total / limit),
        hasPrev: limit === 'all' ? false : page > 1
      }
    });
    
  } catch (error) {
    console.error("❌ [SignalProcessingLogs] Error:", error);
    console.error("❌ [SignalProcessingLogs] Error stack:", error.stack);
    res.status(500).json({ error: error.message || "Failed to fetch signal processing logs" });
  }
});

// ✅ API: Fetch Bot Event Logs with Pagination and Filtering
app.get("/api/bot-event-logs", async (req, res) => {
  try {
    const pool = await poolPromise;
    if (!pool) throw new Error("Database not connected");
    
    // Parse query parameters
    const page = parseInt(req.query.page) || 1;
    const limit = req.query.limit === 'all' ? 'all' : (parseInt(req.query.limit) || 50);
    const offset = (page - 1) * (limit === 'all' ? 0 : limit);
    
    // Build WHERE clause for filters
    let whereConditions = [];
    let params = [];
    let paramIndex = 1;
    
    // UID filter (exact match)
    if (req.query.uid) {
      whereConditions.push(`uid = $${paramIndex}`);
      params.push(req.query.uid);
      paramIndex++;
    }
    
    // Source filter
    if (req.query.source) {
      whereConditions.push(`source LIKE $${paramIndex}`);
      params.push(`%${req.query.source}%`);
      paramIndex++;
    }
    
    // Machine filter
    if (req.query.machineId) {
      whereConditions.push(`machine_id = $${paramIndex}`);
      params.push(req.query.machineId);
      paramIndex++;
    }
    
    // Date range filter
    if (req.query.fromDate) {
      whereConditions.push(`timestamp >= $${paramIndex}`);
      params.push(req.query.fromDate);
      paramIndex++;
    }
    if (req.query.toDate) {
      whereConditions.push(`timestamp <= $${paramIndex}`);
      params.push(req.query.toDate);
      paramIndex++;
    }
    
    const whereClause = whereConditions.length > 0 ? `WHERE ${whereConditions.join(' AND ')}` : '';
    
    // --- Sorting logic ---
    const allowedSortKeys = [
      'id', 'uid', 'source', 'pl_after_comm', 'plain_message', 'timestamp', 'machine_id'
    ];
    let sortKey = req.query.sortKey;
    let sortDirection = req.query.sortDirection && req.query.sortDirection.toUpperCase() === 'ASC' ? 'ASC' : 'DESC';
    if (!allowedSortKeys.includes(sortKey)) {
      sortKey = 'timestamp';
    }
    const orderByClause = `ORDER BY ${sortKey} ${sortDirection}`;
    
    // Build the query
    const countQuery = `SELECT COUNT(*) as total FROM bot_event_log ${whereClause}`;
    const dataQuery = `
      SELECT 
        id,
        uid,
        source,
        pl_after_comm,
        plain_message,
        json_message,
        timestamp,
        machine_id
      FROM bot_event_log 
      ${whereClause}
      ${orderByClause}
      ${limit === 'all' ? '' : `LIMIT ${limit} OFFSET ${offset}`}
    `;
    
    // Execute queries
    const [countResult, dataResult] = await Promise.all([
      pool.query(countQuery, params),
      pool.query(dataQuery, params)
    ]);
    
    const total = parseInt(countResult.rows[0].total);
    const logs = dataResult.rows;
    
    // Parse JSON message for each log if needed
    const processedLogs = logs.map(log => {
      let parsedJson = null;
      if (log.json_message) {
        try {
          parsedJson = JSON.parse(log.json_message);
        } catch (e) {
          // Keep as string if parsing fails
        }
      }
      return { 
        ...log, 
        parsed_json_message: parsedJson 
      };
    });
    
    res.json({
      logs: processedLogs,
      pagination: {
        page,
        limit,
        total,
        totalPages: limit === 'all' ? 1 : Math.ceil(total / (limit === 'all' ? total : limit)),
        hasNext: limit === 'all' ? false : page < Math.ceil(total / (limit === 'all' ? total : limit)),
        hasPrev: limit === 'all' ? false : page > 1
      }
    });
    
  } catch (error) {
    console.error("\u274c Query Error (/api/bot-event-logs):", error.message);
    res.status(500).json({ error: error.message || "Failed to fetch bot event logs" });
  }
});

// ✅ API: Get Log Summary Statistics
app.get("/api/SignalProcessingLogs/summary", async (req, res) => {
  try {
    const pool = await poolPromise;
    if (!pool) throw new Error("Database not connected");
    
    // Build WHERE clause for filters (same as above)
    let whereConditions = [];
    let params = [];
    let paramIndex = 1;
    if (req.query.symbol) {
      whereConditions.push(`symbol LIKE $${paramIndex}`);
      params.push(`%${req.query.symbol}%`);
      paramIndex++;
    }
    if (req.query.signalType) {
      whereConditions.push(`signal_type LIKE $${paramIndex}`);
      params.push(`%${req.query.signalType}%`);
      paramIndex++;
    }
    if (req.query.machineId) {
      whereConditions.push(`machine_id = $${paramIndex}`);
      params.push(req.query.machineId);
      paramIndex++;
    }
    if (req.query.fromDate) {
      whereConditions.push(`candle_time >= $${paramIndex}`);
      params.push(req.query.fromDate);
      paramIndex++;
    }
    if (req.query.toDate) {
      whereConditions.push(`candle_time <= $${paramIndex}`);
      params.push(req.query.toDate);
      paramIndex++;
    }
    const whereClause = whereConditions.length > 0 ? `WHERE ${whereConditions.join(' AND ')}` : '';
    
    // Get all logs for summary (for small/medium datasets; for large, optimize with SQL aggregation)
    const summaryQuery = `
      SELECT 
        signal_type,
        json_data
      FROM signalprocessinglogs 
      ${whereClause}
    `;
    const result = await pool.query(summaryQuery, params);
    const logs = result.rows;
    let totalLogs = logs.length;
    let buyCount = 0;
    let sellCount = 0;
    let rsiSum = 0;
    let rsiCount = 0;
    let earliestLog = null;
    let latestLog = null;
    let uniqueSymbols = new Set();
    let uniqueMachines = new Set();
    logs.forEach(log => {
      if (log.signal_type === 'BUY') buyCount++;
      if (log.signal_type === 'SELL') sellCount++;
      if (log.json_data) {
        try {
          const json = JSON.parse(log.json_data);
          if (json.rsi !== undefined && json.rsi !== null) {
            rsiSum += Number(json.rsi);
            rsiCount++;
          }
        } catch (e) {}
      }
    });
    const avgRSI = rsiCount > 0 ? (rsiSum / rsiCount).toFixed(2) : null;
    res.json({
      summary: {
        totalLogs,
        buyCount,
        sellCount,
        avgRSI,
        uniqueSymbols: uniqueSymbols.size,
        uniqueMachines: uniqueMachines.size,
        earliestLog,
        latestLog
      }
    });
  } catch (error) {
    console.error("❌ Query Error (/api/SignalProcessingLogs/summary):", error.message);
    res.status(500).json({ error: error.message || "Failed to fetch summary" });
  }
});

// ✅ API: Get Bot Event Log Summary Statistics
app.get("/api/bot-event-logs/summary", async (req, res) => {
  try {
    const pool = await poolPromise;
    if (!pool) throw new Error("Database not connected");
    
    // Build WHERE clause for filters (same as above)
    let whereConditions = [];
    let params = [];
    let paramIndex = 1;
    
    if (req.query.uid) {
      whereConditions.push(`uid = $${paramIndex}`);
      params.push(req.query.uid);
      paramIndex++;
    }
    if (req.query.source) {
      whereConditions.push(`source LIKE $${paramIndex}`);
      params.push(`%${req.query.source}%`);
      paramIndex++;
    }
    if (req.query.machineId) {
      whereConditions.push(`machine_id = $${paramIndex}`);
      params.push(req.query.machineId);
      paramIndex++;
    }
    if (req.query.fromDate) {
      whereConditions.push(`timestamp >= $${paramIndex}`);
      params.push(req.query.fromDate);
      paramIndex++;
    }
    if (req.query.toDate) {
      whereConditions.push(`timestamp <= $${paramIndex}`);
      params.push(req.query.toDate);
      paramIndex++;
    }
    
    const whereClause = whereConditions.length > 0 ? `WHERE ${whereConditions.join(' AND ')}` : '';
    
    // Get summary statistics
    const summaryQuery = `
      SELECT 
        COUNT(*) as totalLogs,
        COUNT(DISTINCT machine_id) as uniqueMachines,
        COUNT(DISTINCT source) as uniqueSources,
        SUM(CASE WHEN pl_after_comm > 0 THEN 1 ELSE 0 END) as positivePLCount,
        SUM(CASE WHEN pl_after_comm < 0 THEN 1 ELSE 0 END) as negativePLCount,
        SUM(CASE WHEN pl_after_comm = 0 THEN 1 ELSE 0 END) as zeroPLCount,
        AVG(pl_after_comm) as avgPL,
        MIN(timestamp) as earliestLog,
        MAX(timestamp) as latestLog
      FROM bot_event_log 
      ${whereClause}
    `;
    
    const result = await pool.query(summaryQuery, params);
    const summary = result.rows[0];
    
    res.json({
      summary: {
        totalLogs: summary.totalLogs,
        uniqueMachines: summary.uniqueMachines,
        uniqueSources: summary.uniqueSources,
        positivePLCount: summary.positivePLCount,
        negativePLCount: summary.negativePLCount,
        zeroPLCount: summary.zeroPLCount,
        avgPL: summary.avgPL ? parseFloat(summary.avgPL).toFixed(2) : 0,
        earliestLog: summary.earliestLog,
        latestLog: summary.latestLog
      }
    });
  } catch (error) {
    console.error("❌ Query Error (/api/bot-event-logs/summary):", error.message);
    res.status(500).json({ error: error.message || "Failed to fetch bot event log summary" });
  }
});

// ✅ API: Fetch Trades with Pair Filter
app.get("/api/trades/filtered", async (req, res) => {
  try {
    const pool = await poolPromise;
    if (!pool) throw new Error("Database not connected");
    
    const { pair, limit = 1000 } = req.query;
    let query = "SELECT * FROM alltraderecords";
    let params = [];
    let paramIndex = 1;
    
    if (pair) {
      query += ` WHERE pair = $${paramIndex}`;
      params.push(pair);
      paramIndex++;
    }
    
    query += " ORDER BY created_at DESC";
    
    if (limit && limit !== 'all') {
      query += ` LIMIT ${parseInt(limit)}`;
    }
    
    const result = await pool.query(query, params);
    console.log(`[Server] Fetched ${result.rows.length} trades for pair: ${pair || 'all'}`);
    
    res.json({ trades: result.rows });
  } catch (error) {
    console.error("❌ Query Error (/api/trades/filtered):", error.message);
    res.status(500).json({ error: error.message || "Failed to fetch filtered trades" });
  }
});

// ✅ API: Fetch SignalProcessingLogs with Unique_id only (paginated)
app.get("/api/SignalProcessingLogsWithUniqueId", async (req, res) => {
  try {
    const pool = await poolPromise;
    if (!pool) throw new Error("Database not connected");

    let { symbols, page = 1, limit = 100, sortKey, sortDirection = 'ASC' } = req.query;
    page = parseInt(page);
    limit = parseInt(limit);
    if (!symbols) return res.status(400).json({ error: "Missing symbols param" });
    const symbolList = symbols.split(",").map(s => s.trim()).filter(Boolean);
    if (!symbolList.length) return res.status(400).json({ error: "No symbols provided" });

    // Define allowed sort keys to prevent SQL injection
    const allowedSortKeys = [
      'candle_time', 'symbol', 'interval', 'signal_type', 'signal_source', 
      'candle_pattern', 'price', 'squeeze_status', 'active_squeeze', 
      'machine_id', 'timestamp', 'processing_time_ms', 'created_at', 'unique_id'
    ];

    // Build WHERE clause for symbols and Unique_id (PostgreSQL trims whitespace)
    const symbolPlaceholders = symbolList.map((_, i) => `$${i + 1}`).join(",");
    const whereClause = `symbol IN (${symbolPlaceholders}) AND unique_id IS NOT NULL AND TRIM(unique_id) <> ''`;

    // Build ORDER BY clause
    let orderByClause = 'ORDER BY created_at DESC';
    if (sortKey && allowedSortKeys.includes(sortKey)) {
      orderByClause = `ORDER BY ${sortKey} ${sortDirection === 'ASC' ? 'ASC' : 'DESC'}`;
    }

    // Get total count for pagination (primary query)
    const countQuery = `SELECT COUNT(*) as total FROM signalprocessinglogs WHERE ${whereClause}`;
    const countResult = await pool.query(countQuery, symbolList);
    let total = parseInt(countResult.rows[0]?.total) || 0;
    let totalPages = Math.ceil(total / limit);
    const offset = (page - 1) * limit;

    // Fetch paginated logs (primary query)
    const logsQuery = `SELECT * FROM signalprocessinglogs WHERE ${whereClause} ${orderByClause} LIMIT $${symbolList.length + 1} OFFSET $${symbolList.length + 2}`;
    const logsParams = [...symbolList, limit, offset];
    const logsResult = await pool.query(logsQuery, logsParams);

    let filteredLogs = logsResult.rows.filter(
      log => typeof log.unique_id === 'string' && log.unique_id.replace(/\s|\u00A0/g, '').length > 0
    );

    // If no results, run fallback query (BUY/SELL signal_type)
    let usedFallback = false;
    if (filteredLogs.length === 0) {
      usedFallback = true;
      // Fallback count
      const fallbackCountQuery = `SELECT COUNT(*) as total FROM signalprocessinglogs WHERE symbol IN (${symbolPlaceholders}) AND (signal_type = 'BUY' OR signal_type = 'SELL')`;
      const fallbackCountResult = await pool.query(fallbackCountQuery, symbolList);
      total = parseInt(fallbackCountResult.rows[0]?.total) || 0;
      totalPages = Math.ceil(total / limit);
      // Fallback logs
      const fallbackQuery = `SELECT * FROM signalprocessinglogs WHERE symbol IN (${symbolPlaceholders}) AND (signal_type = 'BUY' OR signal_type = 'SELL') ${orderByClause} LIMIT $${symbolList.length + 1} OFFSET $${symbolList.length + 2}`;
      const fallbackParams = [...symbolList, limit, offset];
      const fallbackResult = await pool.query(fallbackQuery, fallbackParams);
      filteredLogs = fallbackResult.rows;
    }

    res.json({
      logs: filteredLogs,
      pagination: {
        total,
        totalPages,
        page,
        limit,
        usedFallback
      }
    });
  } catch (error) {
    console.error("❌ Query Error (/api/SignalProcessingLogsWithUniqueId):", error);
    res.status(500).json({ error: error.message || "Failed to fetch logs with Unique_id" });
  }
});

// ✅ API: Fetch SignalProcessingLogs by a list of UIDs
app.get("/api/SignalProcessingLogsByUIDs", async (req, res) => {
  try {
    const pool = await poolPromise;
    if (!pool) throw new Error("Database not connected");
    let { uids } = req.query;
    if (!uids) return res.status(400).json({ error: "Missing uids param" });
    const uidList = uids.split(",").map(u => u.trim()).filter(Boolean);
    if (!uidList.length) return res.status(400).json({ error: "No UIDs provided" });

    const uidPlaceholders = uidList.map((_, i) => `$${i + 1}`).join(",");
    const query = `SELECT * FROM signalprocessinglogs WHERE unique_id IN (${uidPlaceholders})`;
    const result = await pool.query(query, uidList);

    res.json({ logs: result.rows });
  } catch (error) {
    console.error("❌ Query Error (/api/SignalProcessingLogsByUIDs):", error);
    res.status(500).json({ error: error.message || "Failed to fetch logs by UIDs" });
  }
});

// ✅ Serve frontend (dashboard) from dist when present
const distPath = path.join(__dirname, "..", "dist");
if (fs.existsSync(distPath)) {
  app.use(express.static(distPath));
  app.get("*", (req, res, next) => {
    if (req.path.startsWith("/api")) return next();
    res.sendFile(path.join(distPath, "index.html"), (err) => err && next());
  });
}

// ✅ Start Express Server
app.listen(PORT, () => {
  console.log(`🚀 Server running at http://localhost:${PORT}`);
  console.log(`[SERVER] Check config: GET http://localhost:${PORT}/api/server-info (must show hasGitHubPagesOrigin: true, database: olab)`);
  console.log(`[SERVER] Python signals proxy: ${PYTHON_SIGNALS_URL} (Information/Binance Data depend on api_signals.py)`);
});

// Self-ping this server (cloud local) to keep warm — gated by env
if (ENABLE_SELF_PING) {
  const pingUrl = `http://127.0.0.1:${PORT}/api/health`;
  setInterval(() => {
    http.get(pingUrl, (res) => {
      if (VERBOSE_LOG) console.log(`📡 Self-ping status: ${res.statusCode}`);
    }).on("error", (err) => {
      console.error("❌ Self-ping failed:", err.message);
    });
  }, 14 * 60 * 1000); // 14 minutes
}