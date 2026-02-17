/**
 * Theme profile (Anish, Loveleet, or custom): list, select active, save/load UI settings per profile on server.
 * Debug: open /api/debug-theme-settings in browser or check console for [Theme] logs.
 */

import React, { useState, useEffect, useCallback, useImperativeHandle } from "react";
import { api } from "./config";

export const ThemeProfileContext = React.createContext(null);

const DEBUG = true;
function log(...args) {
  if (DEBUG && typeof console !== "undefined") console.log("[Theme]", ...args);
}

export function ThemeProfileProvider({ children, isLoggedIn, onSettingsLoaded, themeProfileRef }) {
  const [profiles, setProfiles] = useState([]);
  const [activeProfile, setActiveProfileState] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchProfiles = useCallback(async () => {
    const url = api("/api/theme-profiles");
    const res = await fetch(url, { credentials: "include" });
    if (!res.ok) return [];
    const data = await res.json().catch(() => ({}));
    const list = data?.profiles || [];
    setProfiles(list);
    log("profiles loaded", list.length, list.map((p) => p.name));
    return list;
  }, []);

  const fetchActiveProfile = useCallback(async () => {
    const url = api("/api/active-theme-profile");
    const res = await fetch(url, { credentials: "include" });
    if (!res.ok) return null;
    const data = await res.json().catch(() => ({}));
    const active = data?.activeProfile || null;
    setActiveProfileState(active);
    log("active profile", active?.name, "id=", active?.id);
    return active;
  }, []);

  useEffect(() => {
    if (!isLoggedIn) {
      setProfiles([]);
      setActiveProfileState(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    Promise.all([fetchProfiles(), fetchActiveProfile()])
      .then(([list, active]) => {
        if (cancelled) return;
        if (!active && list.length > 0) {
          log("no active profile; defaulting to first:", list[0].name);
          setActiveProfileId(list[0].id);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, [isLoggedIn, fetchProfiles, fetchActiveProfile]);

  const setActiveProfileId = useCallback(
    async (themeProfileId) => {
      const url = api("/api/active-theme-profile");
      const res = await fetch(url, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ theme_profile_id: themeProfileId }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        log("set active profile failed", res.status, err);
        return false;
      }
      const active = themeProfileId != null ? profiles.find((p) => p.id === themeProfileId) || { id: themeProfileId, name: "?" } : null;
      setActiveProfileState(active);
      log("set active profile", active?.name, "id=", themeProfileId);
      return true;
    },
    [profiles]
  );

  const refetchSettings = useCallback(async () => {
    const themeProfileId = activeProfile?.id;
    const q = themeProfileId != null ? `?theme_profile_id=${themeProfileId}` : "";
    const url = api("/api/ui-settings") + q;
    const res = await fetch(url, { credentials: "include" });
    if (!res.ok) {
      log("refetchSettings failed", res.status);
      return { settings: [] };
    }
    const data = await res.json().catch(() => ({}));
    const settings = data?.settings || [];
    log("refetchSettings", settings.length, "keys", settings.slice(0, 10).map((s) => s.key));
    return { settings };
  }, [activeProfile?.id]);

  const saveSetting = useCallback(
    async (key, value) => {
      const themeProfileId = activeProfile?.id;
      const url = api("/api/ui-settings");
      const body = { key, value };
      if (themeProfileId != null) body.theme_profile_id = themeProfileId;
      const res = await fetch(url, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        log("saveSetting failed", key, res.status);
        return false;
      }
      log("saveSetting", key, "profile=", activeProfile?.name);
      return true;
    },
    [activeProfile]
  );

  const createProfile = useCallback(
    async (name) => {
      const url = api("/api/theme-profiles");
      const res = await fetch(url, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: (name || "").trim() }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        log("createProfile failed", err);
        return { ok: false, error: err?.error || "Failed" };
      }
      const data = await res.json().catch(() => ({}));
      const profile = data?.profile;
      if (profile) {
        setProfiles((prev) => [...prev, profile]);
        log("createProfile", profile.name, "id=", profile.id);
        return { ok: true, profile };
      }
      return { ok: false, error: "No profile returned" };
    },
    []
  );

  // When active profile is set or changes, fetch settings and notify parent so it can apply to state
  useEffect(() => {
    if (!isLoggedIn || !activeProfile?.id || typeof onSettingsLoaded !== "function") return;
    let cancelled = false;
    refetchSettings().then(({ settings }) => {
      if (!cancelled) {
        log("apply server settings to app", settings.length, "keys");
        onSettingsLoaded(settings);
      }
    });
    return () => { cancelled = true; };
  }, [isLoggedIn, activeProfile?.id, onSettingsLoaded]);

  const value = {
    profiles,
    activeProfile,
    activeThemeProfileId: activeProfile?.id ?? null,
    loading,
    setActiveProfileId,
    refetchSettings,
    saveSetting,
    createProfile,
    fetchProfiles,
    fetchActiveProfile,
  };

  useImperativeHandle(themeProfileRef, () => ({
    saveSetting,
    activeProfile,
    activeThemeProfileId: activeProfile?.id ?? null,
    refetchSettings,
  }), [saveSetting, activeProfile, refetchSettings]);

  return (
    <ThemeProfileContext.Provider value={value}>
      {children}
    </ThemeProfileContext.Provider>
  );
}

/** Dropdown to select theme profile (Anish, Loveleet, or custom). Show only when logged in. */
export function ThemeProfileSelector({ className = "", showDebug = true }) {
  const ctx = React.useContext(ThemeProfileContext);
  const [newName, setNewName] = React.useState("");
  const [creating, setCreating] = React.useState(false);

  if (!ctx) return null;
  const { profiles, activeProfile, setActiveProfileId, createProfile } = ctx;

  const runDebugCheck = React.useCallback(async () => {
    try {
      const url = api("/api/debug-theme-settings");
      const res = await fetch(url, { credentials: "include" });
      const data = await res.json().catch(() => ({}));
      log("debug-theme-settings", data);
      if (typeof console !== "undefined") console.log("[Theme] Debug result (see Network tab for /api/debug-theme-settings):", data);
    } catch (e) {
      console.warn("[Theme] Debug check failed", e);
    }
  }, []);

  const handleCreate = async () => {
    const name = newName.trim();
    if (!name) return;
    setCreating(true);
    const result = await createProfile(name);
    setCreating(false);
    setNewName("");
    if (result?.ok && result?.profile) {
      await setActiveProfileId(result.profile.id);
    }
  };

  return (
    <div className={`flex items-center gap-2 flex-wrap ${className}`}>
      <span className="text-sm font-medium text-black dark:text-gray-200">View:</span>
      <select
        value={activeProfile?.id ?? ""}
        onChange={(e) => {
          const v = e.target.value;
          setActiveProfileId(v === "" ? null : Number(v));
        }}
        className="bg-gray-200 dark:bg-gray-700 text-black dark:text-gray-200 border border-gray-400 dark:border-gray-600 rounded px-2 py-1 text-sm"
      >
        {profiles.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
          </option>
        ))}
      </select>
      <div className="flex items-center gap-1">
        <input
          type="text"
          placeholder="New profile name"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCreate()}
          className="w-28 px-2 py-1 text-sm rounded border border-gray-400 dark:border-gray-600 bg-white dark:bg-gray-800 text-black dark:text-gray-200"
        />
        <button
          type="button"
          onClick={handleCreate}
          disabled={creating || !newName.trim()}
          className="px-2 py-1 rounded bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-sm"
        >
          + New
        </button>
      </div>
      {showDebug && (
        <button
          type="button"
          onClick={runDebugCheck}
          title="Verify theme profile and settings (opens in console)"
          className="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 underline"
        >
          Check
        </button>
      )}
    </div>
  );
}
