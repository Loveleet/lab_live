import React, { useState } from "react";
import { validatePassword, setAuthenticated } from "../auth";

export default function LoginPage({ onLogin }) {
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const ok = await validatePassword(password);
      if (ok) {
        setAuthenticated(true);
        onLogin();
      } else {
        setError("Invalid password");
      }
    } catch (err) {
      setError(err?.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f0f0f] p-4">
      <div className="w-full max-w-sm rounded-2xl border border-gray-700 bg-[#181a20] shadow-xl p-8">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-white">LAB Trading</h1>
          <p className="text-gray-400 text-sm mt-1">Sign in to continue</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="login-password" className="block text-sm font-medium text-gray-300 mb-1">
              Password
            </label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setError(""); }}
              placeholder="Enter password"
              autoFocus
              disabled={loading}
              className="w-full px-4 py-3 rounded-lg border border-gray-600 bg-[#222] text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent disabled:opacity-60"
            />
          </div>
          {error && (
            <p className="text-sm text-red-400">{error}</p>
          )}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-lg bg-teal-600 hover:bg-teal-700 disabled:bg-teal-800 disabled:cursor-not-allowed text-white font-semibold transition-colors"
          >
            {loading ? "Checking…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}
