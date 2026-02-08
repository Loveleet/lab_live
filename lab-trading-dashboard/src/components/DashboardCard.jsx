import React, { useRef, useState } from "react";

const DashboardCard = ({ title, value, isSelected, onClick, sticker, onStickerClick }) =>  {
  // Tag state for each card, loaded from localStorage by title
  const [tag, setTag] = React.useState(() => localStorage.getItem(`boxTag-${title}`) || "");
  const [showTagEditor, setShowTagEditor] = useState(false);
  const [tagName, setTagName] = useState("");
  const [tagColor, setTagColor] = useState("#FFF9C4");
  const [tagSize, setTagSize] = useState(1.0);
  const tagButtonRef = useRef(null);

  const colorChoices = [
    { name: "Yellow", value: "#FFF9C4" },
    { name: "Orange", value: "#FFE0B2" },
    { name: "Green", value: "#C8E6C9" },
    { name: "Blue", value: "#BBDEFB" },
    { name: "Pink", value: "#F8BBD0" },
  ];
  const sizeChoices = [
    { name: "Small", value: 1.0 },
    { name: "Large", value: 1.2 },
    { name: "Largest", value: 1.4 },
  ];

  // Tag add/update (visual popup)
  const handleTagClick = (e) => {
    e.stopPropagation();
    setTagName("");
    setTagColor("#FFF9C4");
    setTagSize(1.0);
    setShowTagEditor(true);
  };
  // Tag remove
  const handleTagRemove = (e) => {
    e.stopPropagation();
    setTag("");
    localStorage.removeItem(`boxTag-${title}`);
  };
  // Tag save
  const handleTagSave = (e) => {
    e.stopPropagation();
    const tagData = JSON.stringify({ text: tagName, color: tagColor, scale: tagSize });
    setTag(tagData);
    localStorage.setItem(`boxTag-${title}`, tagData);
    setShowTagEditor(false);
  };
  // Tag cancel
  const handleTagCancel = (e) => {
    e.stopPropagation();
    setShowTagEditor(false);
  };

  // Use title attribute for tooltips on number spans
  const formatValue = (val) => {
    let numberIndex = 0;
    return val.split(/([+-]?[\d.]+)/g).map((part, index) => {
      if (!isNaN(part) && part.trim() !== "") {
        const num = parseFloat(part);
        const colorClass = num < 0 ? "text-red-400" : "text-green-300";
        numberIndex++;
        // Tooltip mapping for number spans (running, closed, total)
        // Handlers for single tooltip reuse
        return (
          <span
            key={index}
            className={`relative px-[3px] font-semibold text-[46px] ${colorClass}`}
            onMouseEnter={(e) => {
              const tooltipMap = ["Running", "Closed", "Total"];
              let tooltip = window.dashboardTooltip;

              if (!tooltip) {
                tooltip = document.createElement("div");
                tooltip.id = "dashboardTooltip";
                tooltip.style.cssText = `
                  position: fixed;
                  background: #222;
                  color: #fff;
                  padding: 6px 12px;
                  border-radius: 5px;
                  font-size: 18px;
                  font-weight: 600;
                  box-shadow: 0 2px 10px rgba(0,0,0,0.3);
                  z-index: 9999;
                  pointer-events: none;
                  opacity: 0;
                  transition: opacity 0.1s ease;
                `;
                document.body.appendChild(tooltip);
                window.dashboardTooltip = tooltip;
              }

              tooltip.innerText = tooltipMap[numberIndex - 1] || "";
              tooltip.style.left = `${e.clientX + 10}px`;
              tooltip.style.top = `${e.clientY + 10}px`;
              tooltip.style.opacity = "0";
              requestAnimationFrame(() => {
                tooltip.style.display = "block";
                requestAnimationFrame(() => {
                  tooltip.style.opacity = "1";
                });
              });
            }}
            onMouseMove={(e) => {
              if (window.dashboardTooltip) {
                window.dashboardTooltip.style.left = `${e.clientX + 10}px`;
                window.dashboardTooltip.style.top = `${e.clientY + 10}px`;
              }
            }}
            onMouseLeave={() => {
              if (window.dashboardTooltip) {
                window.dashboardTooltip.style.display = "none";
              }
            }}
          >
            {part}
          </span>
        );
      } else {
        return (
          <span key={index} className="text-white text-sm px-[1px] opacity-80">
            {part}
          </span>
        );
      }
    });
  };

  // Wrap card UI in relative div with overlays for tag and add button
  return (
    <div className="relative group">
      {/* Selected badge */}
      {isSelected && (
        <div className="absolute top-2 right-2 bg-yellow-400 text-yellow-900 text-xs font-bold px-3 py-1 rounded-full shadow-lg z-20 border border-yellow-600 animate-pulse">
          Selected
        </div>
      )}
      {/* Tag display and remove button with dynamic color and font size */}
      {tag && (() => {
        const parsed = JSON.parse(tag);
        return (
          <div
            className="absolute top-2 left-2 flex items-center gap-1 px-3 py-1.5 rounded-full z-10 shadow-lg border border-gray-300 dark:border-gray-700"
            style={{
              backgroundColor: parsed.color || "yellow",
              fontSize: `calc(1.1rem * var(--app-font-scale) * ${parsed.scale || 1})`,
            }}
          >
            <span className="font-bold mr-1">🏷️</span>{parsed.text}
            <button onClick={handleTagRemove} className="ml-1 text-red-700 font-bold hover:text-red-900">×</button>
          </div>
        );
      })()}
      {/* Add tag button (always shown) */}
      <button
        ref={tagButtonRef}
        onClick={handleTagClick}
        className="absolute top-2 left-2 bg-gray-200 text-black text-xs w-5 h-5 rounded-full z-10 shadow hover:bg-gray-300 border border-gray-400 flex items-center justify-center"
        style={{ transform: "translate(-110%, -110%)" }}
        title="Add tag"
      >
        +
      </button>
      {/* Tag editor popup */}
      {showTagEditor && (
        <div className="absolute top-8 left-2 z-30 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg shadow-lg p-4 w-64 animate-fade-in" style={{ minWidth: 220 }}>
          <div className="mb-2">
            <label className="block text-xs font-semibold mb-1">Tag Name</label>
            <input
              className="w-full px-2 py-1 rounded border border-gray-300 dark:bg-gray-800 dark:text-white"
              value={tagName}
              onChange={e => setTagName(e.target.value)}
              placeholder="Enter tag name"
              autoFocus
            />
          </div>
          <div className="mb-2">
            <label className="block text-xs font-semibold mb-1">Color</label>
            <div className="flex gap-2">
              {colorChoices.map(c => (
                <button
                  key={c.value}
                  className={`w-7 h-7 rounded-full border-2 ${tagColor === c.value ? 'border-black dark:border-white scale-110' : 'border-gray-300'} transition-all`}
                  style={{ backgroundColor: c.value }}
                  onClick={e => { e.stopPropagation(); setTagColor(c.value); }}
                  title={c.name}
                />
              ))}
            </div>
          </div>
          <div className="mb-2">
            <label className="block text-xs font-semibold mb-1">Size</label>
            <div className="flex gap-2">
              {sizeChoices.map(s => (
                <button
                  key={s.value}
                  className={`px-2 py-1 rounded border-2 ${tagSize === s.value ? 'border-blue-500 bg-blue-100 dark:bg-blue-900' : 'border-gray-300'} transition-all text-xs font-semibold`}
                  onClick={e => { e.stopPropagation(); setTagSize(s.value); }}
                  title={s.name}
                >
                  {s.name}
                </button>
              ))}
            </div>
          </div>
          <div className="flex justify-end gap-2 mt-3">
            <button className="px-3 py-1 rounded bg-gray-200 hover:bg-gray-300 text-black text-xs font-semibold" onClick={handleTagCancel}>Cancel</button>
            <button className="px-3 py-1 rounded bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold" onClick={handleTagSave} disabled={!tagName.trim()}>Save</button>
          </div>
        </div>
      )}
      {/* Card UI */}
      <div
        className={`cursor-pointer p-8 rounded-2xl border-2 border-transparent transition-all duration-300 transform bg-gradient-to-br from-blue-800/90 to-indigo-900/90 dark:from-blue-900/80 dark:to-gray-900/90 group-hover:scale-105 group-hover:shadow-2xl group-hover:border-yellow-400/70 group-focus-within:scale-105 group-focus-within:shadow-2xl group-focus-within:border-yellow-400/90 group-active:scale-100 group-active:shadow-lg group-active:border-yellow-500/90
      ${isSelected ? "ring-4 ring-yellow-400 border-yellow-600 scale-105 shadow-2xl bg-yellow-100/80 dark:bg-yellow-900/30" : "hover:ring-2 hover:ring-yellow-400/60"}
      `}
        onClick={onClick}
        tabIndex={0}
        title={title.replace(/_/g, " ")}
      >
        {/* Optional sticker overlay (e.g., new trades) */}
        {sticker && (
          <button
            className="absolute -top-2 -right-2 z-20 bg-pink-600 text-white text-[10px] md:text-xs font-bold px-2 py-1 rounded-full shadow-lg border border-pink-300 hover:bg-pink-700 animate-pulse ring-2 ring-pink-300"
            onClick={(e) => {
              e.stopPropagation();
              if (onStickerClick) onStickerClick();
            }}
            title="View newly added trades"
          >
            {sticker}
          </button>
        )}
        {/* Title with tooltip */}
        <h2 className="text-lg font-semibold text-center text-sky-300 mb-2 truncate" title={title.replace(/_/g, " ")}>{title.replace(/_/g, " ")}</h2>
        {/* Properly formatted value using JSX with tooltips */}
        <div className="text-2xl font-bold text-center leading-snug whitespace-nowrap overflow-x-auto">
          {typeof value === "string"
            ? (
              <span className="text-[22px] leading-snug inline-block min-w-full pointer-events-none">
                <div className="flex flex-wrap justify-end gap-[3px] pointer-events-auto" style={{ pointerEvents: "auto" }}>
                  {formatValue(value)}
                </div>
              </span>
            )
            : value}
        </div>
      </div>
    </div>
  );
};

export default DashboardCard;