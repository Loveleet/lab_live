/**
 * Auth helper for login. Replace the implementation below with a database/API check later.
 * e.g. POST /api/auth/login with { password } and check response.
 */

import React from "react";
import { API_BASE_URL } from "./config";

export const AuthContext = React.createContext(null);

/** Use anywhere inside AuthContext.Provider to show a logout button */
export function LogoutButton({ className = "", ...rest }) {
  const auth = React.useContext(AuthContext);
  if (!auth) return null;
  return (
    <button
      type="button"
      onClick={auth.logout}
      title="Log out"
      className={
        className ||
        "px-2 py-1 rounded bg-red-600 hover:bg-red-700 text-white text-sm font-semibold transition-colors"
      }
      {...rest}
    >
      Logout
    </button>
  );
}

// Demo password until database/API is connected
const DEMO_PASSWORD = "demo123";

/**
 * Validate password. For now checks against DEMO_PASSWORD.
 * TODO: Replace with API call, e.g.:
 *   const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
 *     method: 'POST',
 *     headers: { 'Content-Type': 'application/json' },
 *     body: JSON.stringify({ password }),
 *   });
 *   const data = await res.json();
 *   return data?.ok === true;
 */
export async function validatePassword(password) {
  const p = (password || "").trim();
  if (!p) return false;
  // Demo: check against constant
  if (p === DEMO_PASSWORD) return true;
  // TODO: Uncomment and use when backend is ready:
  // try {
  //   const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
  //     method: "POST",
  //     headers: { "Content-Type": "application/json" },
  //     body: JSON.stringify({ password: p }),
  //   });
  //   if (!res.ok) return false;
  //   const data = await res.json();
  //   return data?.success === true || data?.ok === true;
  // } catch {
  //   return false;
  // }
  return false;
}

export const AUTH_STORAGE_KEY = "lab_trading_auth";

// Session: 1 hour; show "stay logged in" popup 10 minutes before expiry
export const SESSION_DURATION_MS = 60 * 60 * 1000;
export const SESSION_WARNING_BEFORE_MS = 10 * 60 * 1000;

function getStored() {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(AUTH_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed.at === "number" ? parsed : null;
  } catch {
    return null;
  }
}

export function getSession() {
  return getStored();
}

export function setSession() {
  try {
    window.localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({ at: Date.now() }));
  } catch (_) {}
}

export function clearSession() {
  try {
    window.localStorage.removeItem(AUTH_STORAGE_KEY);
  } catch (_) {}
}

export function isSessionExpired() {
  const s = getStored();
  if (!s) return true;
  return Date.now() - s.at >= SESSION_DURATION_MS;
}

/** True when within the last 10 minutes of the 1-hour session (time to show "stay logged in") */
export function isSessionWarningTime() {
  const s = getStored();
  if (!s) return false;
  const elapsed = Date.now() - s.at;
  return elapsed >= SESSION_DURATION_MS - SESSION_WARNING_BEFORE_MS && elapsed < SESSION_DURATION_MS;
}

export function isAuthenticated() {
  const s = getStored();
  if (!s) return false;
  return Date.now() - s.at < SESSION_DURATION_MS;
}

export function setAuthenticated(value) {
  if (value) {
    setSession();
  } else {
    clearSession();
  }
}
