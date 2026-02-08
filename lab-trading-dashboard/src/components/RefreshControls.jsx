import React from 'react';

function parseDurationToSeconds(input) {
  if (!input && input !== 0) return null;
  if (typeof input === 'number' && !Number.isNaN(input)) return Math.max(0, Math.floor(input));
  const str = String(input).trim().toLowerCase();
  if (!str) return null;
  // Support HH:MM:SS or MM:SS or SS
  if (/^\d{1,2}(:\d{1,2}){0,2}$/.test(str)) {
    const parts = str.split(':').map(p => parseInt(p, 10) || 0);
    if (parts.length === 3) {
      const [h, m, s] = parts;
      return h * 3600 + m * 60 + s;
    }
    if (parts.length === 2) {
      const [m, s] = parts;
      return m * 60 + s;
    }
    return parts[0];
  }
  // Support expressions like "1h 30m", "90s", "2m", "1h"
  let total = 0;
  const regex = /(\d+)(h|m|s)/g;
  let match;
  while ((match = regex.exec(str)) !== null) {
    const value = parseInt(match[1], 10);
    const unit = match[2];
    if (unit === 'h') total += value * 3600;
    if (unit === 'm') total += value * 60;
    if (unit === 's') total += value;
  }
  if (total > 0) return total;
  // Fallback: plain number seconds
  const n = parseInt(str, 10);
  return Number.isNaN(n) ? null : Math.max(0, n);
}

function formatSmartDuration(seconds) {
  if (seconds == null || Number.isNaN(seconds)) return '--';
  const s = Math.max(0, Math.floor(seconds));
  if (s < 60) return `${s}s`;
  if (s < 3600) {
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}m ${sec}s`;
  }
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return `${h}h ${m}m ${sec}s`;
}

export default function RefreshControls({
  onRefresh,
  storageKey = 'default',
  initialIntervalSec = 20,
  initialAutoOn = false,
  style,
  className,
}) {
  const [autoOn, setAutoOn] = React.useState(() => {
    try {
      const saved = localStorage.getItem(`refresh_${storageKey}_autoOn`);
      return saved ? JSON.parse(saved) === true : initialAutoOn;
    } catch {
      return initialAutoOn;
    }
  });
  const [intervalSec, setIntervalSec] = React.useState(() => {
    try {
      const saved = localStorage.getItem(`refresh_${storageKey}_intervalSec`);
      const parsed = saved ? parseInt(saved, 10) : initialIntervalSec;
      return Number.isNaN(parsed) ? initialIntervalSec : parsed;
    } catch {
      return initialIntervalSec;
    }
  });
  const [lastRefreshTs, setLastRefreshTs] = React.useState(() => Date.now());
  const [tick, setTick] = React.useState(0);
  const [isRefreshing, setIsRefreshing] = React.useState(false);

  React.useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  React.useEffect(() => {
    try { localStorage.setItem(`refresh_${storageKey}_autoOn`, JSON.stringify(autoOn)); } catch {}
  }, [autoOn, storageKey]);

  React.useEffect(() => {
    try { localStorage.setItem(`refresh_${storageKey}_intervalSec`, String(intervalSec)); } catch {}
  }, [intervalSec, storageKey]);

  React.useEffect(() => {
    if (!autoOn) return;
    const now = Date.now();
    const nextAt = lastRefreshTs + intervalSec * 1000;
    if (now >= nextAt) {
      triggerRefresh();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tick, autoOn, intervalSec]);

  const triggerRefresh = async () => {
    if (isRefreshing) return; // Prevent multiple simultaneous refreshes
    
    setIsRefreshing(true);
    setLastRefreshTs(Date.now()); // Update timestamp immediately for visual feedback
    
    try {
      await Promise.resolve(onRefresh && onRefresh());
    } catch (e) {
      // swallow
    } finally {
      setIsRefreshing(false);
    }
  };

  const remainingSec = React.useMemo(() => {
    if (!autoOn) return null;
    const nextAt = lastRefreshTs + intervalSec * 1000;
    return Math.max(0, Math.ceil((nextAt - Date.now()) / 1000));
  }, [autoOn, intervalSec, lastRefreshTs, tick]);

  const elapsedSec = React.useMemo(() => {
    if (autoOn) return null;
    return Math.max(0, Math.floor((Date.now() - lastRefreshTs) / 1000));
  }, [autoOn, lastRefreshTs, tick]);

  const onClickSettings = () => {
    const input = prompt('Set auto refresh interval (e.g., 45, 90s, 2m, 1h 5m, or HH:MM:SS):', String(intervalSec));
    if (input == null) return;
    const seconds = parseDurationToSeconds(input);
    if (seconds == null || seconds <= 0) {
      alert('Please enter a valid time greater than 0.');
      return;
    }
    setIntervalSec(seconds);
  };

  const containerStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    ...style,
  };
  const btnStyle = {
    padding: '6px 10px',
    borderRadius: 8,
    border: '1px solid #d1d5db',
    background: '#f3f4f6',
    fontWeight: 700,
    cursor: 'pointer',
  };

  return (
    <div className={className} style={containerStyle}>
      <button
        onClick={triggerRefresh}
        disabled={isRefreshing}
        title={isRefreshing ? 'Refreshing...' : (autoOn ? 'Click to refresh now' : 'Click to refresh')}
        style={{
          ...btnStyle,
          background: isRefreshing ? '#fbbf24' : '#e5e7eb',
          borderColor: isRefreshing ? '#f59e0b' : '#cbd5e1',
          opacity: isRefreshing ? 0.8 : 1,
          cursor: isRefreshing ? 'not-allowed' : 'pointer',
        }}
      >
        {isRefreshing ? '⟳' : '⟲'} {autoOn ? formatSmartDuration(remainingSec) : formatSmartDuration(elapsedSec)}
      </button>
      <button
        onClick={() => setAutoOn(v => !v)}
        title="Auto Refresh"
        style={{
          ...btnStyle,
          background: autoOn ? 'linear-gradient(90deg, #22c55e 60%, #16a34a 100%)' : '#e5e7eb',
          color: autoOn ? '#fff' : '#111827',
          border: 'none',
        }}
      >
        {autoOn ? 'Auto: ON' : 'Auto: OFF'}
      </button>
      <button
        onClick={onClickSettings}
        title={`Set interval (current: ${formatSmartDuration(intervalSec)})`}
        style={{
          ...btnStyle,
          padding: '6px 8px',
          borderRadius: 999,
        }}
      >
        ⚙️
      </button>
    </div>
  );
}

