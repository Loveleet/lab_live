import React, { useEffect, useMemo, useRef, useState } from "react";

const DEFAULT_SETTINGS = {
  enabled: true,
  volume: 0.7,
  mode: "tts", // 'tts' | 'audio'
  announceActions: { BUY: true, SELL: true },
  announceSignals: {}, // will be filled from availableSignals
  audioUrls: { BUY: "", SELL: "" },
  newTradeWindowHours: 4,
};

export default function SoundSettings({ isOpen, onClose, settings, onChange, availableSignals, onTestVisual }) {
  const [localSettings, setLocalSettings] = useState(settings || DEFAULT_SETTINGS);
  const containerRef = useRef(null);
  const [pos, setPos] = useState(null); // { x, y } when dragged, otherwise centered
  const dragRef = useRef({ dragging: false, offsetX: 0, offsetY: 0, width: 0, height: 0 });

  useEffect(() => {
    setLocalSettings((prev) => {
      const base = { ...DEFAULT_SETTINGS, ...(settings || {}) };
      // Initialize announceSignals keys from availableSignals if not present
      const mergedSignals = { ...(base.announceSignals || {}) };
      (availableSignals || []).forEach((s) => {
        if (mergedSignals[s] === undefined) mergedSignals[s] = true;
      });
      base.announceSignals = mergedSignals;
      return base;
    });
  }, [settings, availableSignals]);

  // Reset position when the modal opens
  useEffect(() => {
    if (isOpen) {
      setPos(null);
    }
  }, [isOpen]);

  const handleSave = () => {
    onChange(localSettings);
    onClose();
  };

  const handleTest = () => {
    const s = localSettings || DEFAULT_SETTINGS;
    if (!s.enabled) return;
    const volume = Math.max(0, Math.min(1, Number(s.volume || 0.7)));

    // Choose an action to preview: prefer BUY if enabled, else SELL, else any
    const actionPref = ["BUY", "SELL"];
    let action = actionPref.find((a) => s.announceActions?.[a] !== false) || "BUY";

    // Choose a signal to preview: first enabled from availableSignals
    const firstEnabledSignal = (availableSignals || []).find((sg) => s.announceSignals?.[sg] !== false);
    const signal = firstEnabledSignal || "signal";

    if (s.mode === "audio") {
      const url = s.audioUrls?.[action];
      if (url) {
        try {
          const audio = new Audio(url);
          audio.volume = volume;
          audio.play().catch(() => {});
          return;
        } catch {
          // fall through to TTS preview
        }
      }
    }
    try {
      const phrase = `${action === "BUY" ? "Buy" : action === "SELL" ? "Sell" : action} from ${signal}`;
      const u = new SpeechSynthesisUtterance(phrase);
      u.volume = volume;
      window.speechSynthesis.speak(u);
    } catch {}
    // Trigger visual sticker preview in parent if provided
    if (typeof onTestVisual === "function") {
      onTestVisual();
    }
  };

  const onHeaderMouseDown = (e) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    // Initialize pos immediately to current rect (removes center transform)
    setPos({ x: rect.left, y: rect.top });
    dragRef.current = {
      dragging: true,
      offsetX: e.clientX - rect.left,
      offsetY: e.clientY - rect.top,
      width: rect.width,
      height: rect.height,
    };
    window.addEventListener("mousemove", onWindowMouseMove);
    window.addEventListener("mouseup", onWindowMouseUp, { once: true });
  };

  const onWindowMouseMove = (e) => {
    if (!dragRef.current.dragging) return;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const nx = e.clientX - dragRef.current.offsetX;
    const ny = e.clientY - dragRef.current.offsetY;
    const minPad = 8;
    const maxX = Math.max(minPad, vw - dragRef.current.width - minPad);
    const maxY = Math.max(minPad, vh - dragRef.current.height - minPad);
    const clampedX = Math.min(Math.max(nx, minPad), maxX);
    const clampedY = Math.min(Math.max(ny, minPad), maxY);
    setPos({ x: clampedX, y: clampedY });
  };

  const onWindowMouseUp = () => {
    dragRef.current.dragging = false;
    window.removeEventListener("mousemove", onWindowMouseMove);
  };

  const ActionToggle = ({ action }) => (
    <label className="flex items-center gap-2 text-sm">
      <input
        type="checkbox"
        checked={!!localSettings.announceActions[action]}
        onChange={(e) =>
          setLocalSettings((s) => ({
            ...s,
            announceActions: { ...s.announceActions, [action]: e.target.checked },
          }))
        }
      />
      {action}
    </label>
  );

  const SignalToggle = ({ signal }) => (
    <label className="flex items-center gap-2 text-sm">
      <input
        type="checkbox"
        checked={!!localSettings.announceSignals[signal]}
        onChange={(e) =>
          setLocalSettings((s) => ({
            ...s,
            announceSignals: { ...s.announceSignals, [signal]: e.target.checked },
          }))
        }
      />
      {signal}
    </label>
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div
        ref={containerRef}
        className="fixed w-[92vw] max-w-2xl bg-white dark:bg-gray-900 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-800 text-gray-900 dark:text-gray-100"
        style={
          pos
            ? { left: pos.x, top: pos.y }
            : { left: '50%', top: '50%', transform: 'translate(-50%, -50%)' }
        }
      >
        <div
          className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-800 cursor-move select-none"
          onMouseDown={onHeaderMouseDown}
        >
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">Sound & New Trades</h3>
          <button className="text-sm px-2 py-1 rounded bg-gray-200 dark:bg-gray-800 text-black dark:text-white" onClick={onClose}>
            Close
          </button>
        </div>

        <div className="p-4 space-y-4">
          <div className="flex items-center gap-3">
            <label className="text-sm font-semibold text-gray-900 dark:text-gray-100">Enable sound</label>
            <input
              type="checkbox"
              checked={!!localSettings.enabled}
              onChange={(e) => setLocalSettings((s) => ({ ...s, enabled: e.target.checked }))}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div>
                <label className="text-sm font-semibold text-gray-900 dark:text-gray-100">Volume: {Math.round((localSettings.volume || 0) * 100)}%</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.01"
                  className="w-full"
                  value={localSettings.volume || 0}
                  onChange={(e) => setLocalSettings((s) => ({ ...s, volume: parseFloat(e.target.value) }))}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-900 dark:text-gray-100">Mode</label>
                <div className="flex items-center gap-3">
                  <label className="flex items-center gap-2 text-sm text-gray-900 dark:text-gray-100">
                    <input
                      type="radio"
                      name="mode"
                      value="tts"
                      checked={(localSettings.mode || "tts") === "tts"}
                      onChange={(e) => setLocalSettings((s) => ({ ...s, mode: e.target.value }))}
                    />
                    Voice (TTS)
                  </label>
                  <label className="flex items-center gap-2 text-sm text-gray-900 dark:text-gray-100">
                    <input
                      type="radio"
                      name="mode"
                      value="audio"
                      checked={localSettings.mode === "audio"}
                      onChange={(e) => setLocalSettings((s) => ({ ...s, mode: e.target.value }))}
                    />
                    Audio URLs
                  </label>
                </div>
              </div>
              {localSettings.mode === "audio" && (
                <div className="space-y-2">
                  <div className="flex flex-col gap-1">
                    <label className="text-xs font-semibold text-gray-900 dark:text-gray-100">BUY audio URL</label>
                    <input
                      className="px-2 py-1 rounded border border-gray-300 dark:border-gray-700 dark:bg-gray-800"
                      placeholder="https://example.com/buy.mp3"
                      value={localSettings.audioUrls?.BUY || ""}
                      onChange={(e) =>
                        setLocalSettings((s) => ({
                          ...s,
                          audioUrls: { ...(s.audioUrls || {}), BUY: e.target.value },
                        }))
                      }
                    />
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-xs font-semibold text-gray-900 dark:text-gray-100">SELL audio URL</label>
                    <input
                      className="px-2 py-1 rounded border border-gray-300 dark:border-gray-700 dark:bg-gray-800"
                      placeholder="https://example.com/sell.mp3"
                      value={localSettings.audioUrls?.SELL || ""}
                      onChange={(e) =>
                        setLocalSettings((s) => ({
                          ...s,
                          audioUrls: { ...(s.audioUrls || {}), SELL: e.target.value },
                        }))
                      }
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-3">
              <div className="space-y-1">
                <label className="text-sm font-semibold text-gray-900 dark:text-gray-100">Announce actions</label>
                <div className="flex items-center gap-4">
                  <ActionToggle action="BUY" />
                  <ActionToggle action="SELL" />
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-sm font-semibold text-gray-900 dark:text-gray-100">Announce signals</label>
                <div className="grid grid-cols-2 gap-2 max-h-36 overflow-auto p-2 border border-gray-200 dark:border-gray-800 rounded">
                  {(availableSignals || []).map((s) => (
                    <SignalToggle key={s} signal={s} />
                  ))}
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  "New trades" window for sticker (hours)
                </label>
                <input
                  type="number"
                  min="1"
                  max="72"
                  className="w-24 px-2 py-1 rounded border border-gray-300 dark:border-gray-700 dark:bg-gray-800"
                  value={localSettings.newTradeWindowHours || 4}
                  onChange={(e) =>
                    setLocalSettings((s) => ({
                      ...s,
                      newTradeWindowHours: Math.max(1, Math.min(72, parseInt(e.target.value || "1"))),
                    }))
                  }
                />
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 px-4 py-3 border-t border-gray-200 dark:border-gray-800">
          <button className="px-3 py-1 rounded bg-green-600 text-white" onClick={handleTest}>Test</button>
          <button className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800 text-black dark:text-white" onClick={onClose}>Cancel</button>
          <button className="px-3 py-1 rounded bg-blue-600 text-white" onClick={handleSave}>Save</button>
        </div>
      </div>
    </div>
  );
}


