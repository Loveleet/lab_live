
import React, { useEffect, useState } from "react";

function formatSinceTime(timestamp, now) {
  const ts = new Date(timestamp).getTime();
  let diff = Math.floor((now - ts) / 1000); // in seconds
  if (diff < 0) diff = 0;
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) {
    const m = Math.floor(diff / 60);
    const s = diff % 60;
    return `${m}m ${s}s ago`;
  }
  if (diff < 86400) {
    const h = Math.floor(diff / 3600);
    const m = Math.floor((diff % 3600) / 60);
    const s = diff % 60;
    return `${h}h ${m}m ${s}s ago`;
  }
  const d = Math.floor(diff / 86400);
  const h = Math.floor((diff % 86400) / 3600);
  const m = Math.floor((diff % 3600) / 60);
  const s = diff % 60;
  return `${d}d ${h}h ${m}m ${s}s ago`;
}

function SuperTrendPanel({ data = [] }) {
  // Live clock for updating time ago
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, []);

  // Detect dark mode from document
  const [dark, setDark] = useState(() => document.documentElement.classList.contains('dark'));
  useEffect(() => {
    const observer = new MutationObserver(() => {
      setDark(document.documentElement.classList.contains('dark'));
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  return (
    <div className="flex flex-row items-center gap-3 ml-4">
      {data.length === 0 && (
        <span className="text-gray-400 text-xs">No SuperTrend signals</span>
      )}
      {data.map((row, i) => {
        const ts = new Date(row.timestamp).getTime();
        const diff = Math.floor((now - ts) / 1000);
        const offer = diff < 2700; // 15 min
        // Theme-aware text color
        const textColor = dark ? "text-white" : "text-black";
        // Trend color
        const trendColor = row.trend && row.trend.toUpperCase() === "BUY" ? "text-green-500" : row.trend && row.trend.toUpperCase() === "SELL" ? "text-red-500" : "";
        // Border and bg: transparent, no white/gray
        return (
          <span
            key={i}
            className={`px-2 py-1 rounded border ${offer ? "border-yellow-400 animate-pulse" : "border-gray-500"} flex flex-row items-center gap-1 bg-transparent`}
            style={{ background: "none" }}
          >
            <span className={`font-mono text-blue-400 ${textColor}`}>{row.source}</span>
            <span className={`font-bold ${trendColor}`}>{row.trend}</span>
            <span className={offer ? "text-orange-400 font-bold" : textColor}>
              {formatSinceTime(row.timestamp, now)}
              {/* OFFER! badge removed as requested */}
            </span>
          </span>
        );
      })}
    </div>
  );
}

export default SuperTrendPanel;
