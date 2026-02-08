import React, { useState, useEffect, useRef } from "react";

const TV_SCRIPT_ID = "tradingview-widget-script";
function loadTradingViewScript() {
  if (!document.getElementById(TV_SCRIPT_ID)) {
    const script = document.createElement("script");
    script.id = TV_SCRIPT_ID;
    script.src = "https://s3.tradingview.com/tv.js";
    script.async = true;
    document.body.appendChild(script);
  }
}

const INDICATORS = [
  { key: "RSI@tv-basicstudies", label: "RSI-9" },
  { key: "MACD@tv-basicstudies", label: "MACD" },
  { key: "Volume@tv-basicstudies", label: "Volume" },
  // Add more supported indicators here
];

const intervalMap = {
  "1m": "1",
  "3m": "3",
  "5m": "5",
  "15m": "15",
  "30m": "30",
  "1h": "60",
  "4h": "240",
  "1d": "D"
};

const getRobustSymbol = (pair) => {
  if (!pair) return "BTCUSDT";
  let symbol = pair.replace(/<[^>]+>/g, '')
    .replace(/\s+/g, '')
    .replace(/[^A-Z0-9]/gi, '')
    .replace('PERPETUALCONTRACT', '')
    .replace('PERP', '')
    .replace('Chart', '')
    .toUpperCase();
  if (symbol.startsWith('BINANCE')) symbol = symbol.slice(7);
  // Remove trailing numbers for expiry (e.g. ETHUSDT250926 -> ETHUSDT)
  symbol = symbol.replace(/\d{6,}$/,'');
  return symbol;
};

const ChartGridPage = ({ symbols: initialSymbols = [], trades: initialTrades = [] }) => {
  // Load settings from localStorage or use defaults
  const getSetting = (key, def) => {
    try {
      const val = localStorage.getItem(`chartGridSetting_${key}`);
      if (val !== null) return JSON.parse(val);
    } catch {}
    return def;
  };
  const [symbols, setSymbols] = useState(initialSymbols);
  const [trades, setTrades] = useState(initialTrades);
  const [source, setSource] = useState(getSetting('source', "tradingview"));
  const [interval, setInterval] = useState(getSetting('interval', "15m"));
  const [indicators, setIndicators] = useState(getSetting('indicators', ["RSI@tv-basicstudies", "MACD@tv-basicstudies", "Volume@tv-basicstudies"]));
  const [layout, setLayout] = useState(getSetting('layout', 3));
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(getSetting('pageSize', 50));
  const [chartSize, setChartSize] = useState(getSetting('chartSize', { width: 400, height: 400 }));
  const [fontSize, setFontSize] = useState(14); // Default font size

  // Sticky filter bar ref
  const filterBarRef = useRef();

  // Live data sync (BroadcastChannel + localStorage fallback)
  useEffect(() => {
    const channel = new BroadcastChannel("chart-grid-data");
    channel.onmessage = (e) => {
      if (e.data.symbols) {
        setSymbols(e.data.symbols);
        localStorage.setItem("chartGridSymbols", JSON.stringify(e.data.symbols));
      }
      if (e.data.trades) {
        setTrades(e.data.trades);
        localStorage.setItem("chartGridTrades", JSON.stringify(e.data.trades));
      }
    };
    // On mount, if no data, try to load from localStorage
    if ((!initialSymbols || initialSymbols.length === 0) && symbols.length === 0) {
      const storedSymbols = localStorage.getItem("chartGridSymbols");
      if (storedSymbols) setSymbols(JSON.parse(storedSymbols));
    }
    if ((!initialTrades || initialTrades.length === 0) && trades.length === 0) {
      const storedTrades = localStorage.getItem("chartGridTrades");
      if (storedTrades) setTrades(JSON.parse(storedTrades));
    }
    return () => channel.close();
    // eslint-disable-next-line
  }, []);

  // TradingView script loader
  useEffect(() => {
    if (source === "tradingview") loadTradingViewScript();
  }, [source]);

  // Render TradingView widgets after DOM update
  useEffect(() => {
    if (source !== "tradingview" || !window.TradingView) return;
    pagedTrades().forEach((trade, idx) => {
      const symbol = getRobustSymbol(trade.Pair);
      const containerId = `tv_chart_${idx}`;
      const container = document.getElementById(containerId);
      if (container) container.innerHTML = "";
      new window.TradingView.widget({
        container_id: containerId,
        autosize: true,
        symbol: `BINANCE:${symbol}PERP`,
        interval: intervalMap[interval] || "15",
        timezone: "Etc/UTC",
        theme: "dark",
        style: "8",
        locale: "en",
        studies: indicators,
        overrides: {
          "volumePaneSize": indicators.includes("Volume@tv-basicstudies") ? "medium" : "0",
          "paneProperties.topMargin": 10,
          "paneProperties.bottomMargin": 15,
          "paneProperties.rightMargin": 20,
          "scalesProperties.fontSize": 11,
        },
        studies_overrides: {
          "RSI@tv-basicstudies.length": 9,
        },
        hide_side_toolbar: false,
        allow_symbol_change: false,
        details: true,
        withdateranges: true,
        hideideas: true,
        toolbar_bg: "#222",
        height: chartSize.height,
        width: chartSize.width,
      });
    });
    // eslint-disable-next-line
  }, [source, interval, indicators, layout, page, chartSize, trades, pageSize]);

  // Paging helpers
  const pagedTrades = () => trades.slice(page * pageSize, (page + 1) * pageSize);
  const totalPages = Math.ceil(trades.length / pageSize);

  // Drag handlers for resizing
  const dragRef = useRef();
  const [dragging, setDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0, width: 400, height: 400 });

  const onDragStart = (e) => {
    setDragging(true);
    setDragStart({
      x: e.clientX,
      y: e.clientY,
      width: chartSize.width,
      height: chartSize.height,
    });
  };
  const onDrag = (e) => {
    if (!dragging) return;
    const dx = e.clientX - dragStart.x;
    const dy = e.clientY - dragStart.y;
    setChartSize({
      width: Math.max(200, dragStart.width + dx),
      height: Math.max(200, dragStart.height + dy),
    });
  };
  const onDragEnd = () => setDragging(false);
  useEffect(() => {
    if (dragging) {
      window.addEventListener("mousemove", onDrag);
      window.addEventListener("mouseup", onDragEnd);
    } else {
      window.removeEventListener("mousemove", onDrag);
      window.removeEventListener("mouseup", onDragEnd);
    }
    return () => {
      window.removeEventListener("mousemove", onDrag);
      window.removeEventListener("mouseup", onDragEnd);
    };
    // eslint-disable-next-line
  }, [dragging]);

  // Add state for copied field
  const [copied, setCopied] = useState({});
  const handleCopy = (field, value, idx) => {
    if (!value) return;
    navigator.clipboard.writeText(value.toString());
    setCopied(prev => ({ ...prev, [`${idx}_${field}`]: true }));
    setTimeout(() => setCopied(prev => ({ ...prev, [`${idx}_${field}`]: false })), 1200);
  };

  // Save settings to localStorage on change
  useEffect(() => { localStorage.setItem('chartGridSetting_source', JSON.stringify(source)); }, [source]);
  useEffect(() => { localStorage.setItem('chartGridSetting_interval', JSON.stringify(interval)); }, [interval]);
  useEffect(() => { localStorage.setItem('chartGridSetting_indicators', JSON.stringify(indicators)); }, [indicators]);
  useEffect(() => { localStorage.setItem('chartGridSetting_layout', JSON.stringify(layout)); }, [layout]);
  useEffect(() => { localStorage.setItem('chartGridSetting_pageSize', JSON.stringify(pageSize)); }, [pageSize]);
  useEffect(() => { localStorage.setItem('chartGridSetting_chartSize', JSON.stringify(chartSize)); }, [chartSize]);

  return (
    <div className="w-full h-full min-h-screen bg-black">
      <div className="w-full text-center text-white py-2 text-sm font-semibold">Total Trades: {trades.length}</div>
      {/* Sticky Filter Bar */}
      <div
        ref={filterBarRef}
        className="sticky top-0 z-40 bg-[#181818] shadow p-4 flex flex-wrap gap-4 items-center justify-between"
        style={{ borderBottom: "1px solid #222" }}
      >
        <div className="flex flex-wrap gap-4 items-center text-white">
          <label>Source:
            <select value={source} onChange={e => setSource(e.target.value)} className="ml-2 border rounded px-2 py-1 bg-[#222] text-white">
              <option value="tradingview">TradingView</option>
              <option value="binance">Binance</option>
            </select>
          </label>
          <label>Interval:
            <select value={interval} onChange={e => setInterval(e.target.value)} className="ml-2 border rounded px-2 py-1 bg-[#222] text-white">
              {Object.keys(intervalMap).map(opt => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </label>
          <label>Indicators:</label>
          {INDICATORS.map(ind => (
            <label key={ind.key} className="ml-2 flex items-center gap-1">
              <input
                type="checkbox"
                checked={indicators.includes(ind.key)}
                onChange={e => {
                  setIndicators(prev => e.target.checked ? [...prev, ind.key] : prev.filter(i => i !== ind.key));
                }}
              />
              <span className="text-white">{ind.label}</span>
            </label>
          ))}
          <label>Layout:
            <select value={layout} onChange={e => setLayout(Number(e.target.value))} className="ml-2 border rounded px-2 py-1 bg-[#222] text-white">
              {[1,2,3,4,5,6].map(opt => (
                <option key={opt} value={opt}>{opt} per row</option>
              ))}
            </select>
          </label>
          <label>Page Size:
            <select value={pageSize} onChange={e => { setPageSize(Number(e.target.value)); setPage(0); }} className="ml-2 border rounded px-2 py-1 bg-[#222] text-white">
              {[10, 20, 50, 100, 200].map(opt => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </label>
          <label>Font Size:
            <select value={fontSize} onChange={e => setFontSize(Number(e.target.value))} className="ml-2 border rounded px-2 py-1 bg-[#222] text-white">
              {[12, 14, 16, 18, 20].map(opt => (
                <option key={opt} value={opt}>{opt}px</option>
              ))}
            </select>
          </label>
        </div>
        {/* Paging */}
        <div className="flex items-center gap-2 text-white">
          <button disabled={page === 0} onClick={() => setPage(p => Math.max(0, p - 1))} className="px-2 py-1 bg-[#222] rounded text-white">Prev</button>
          <span>Page {page + 1} / {totalPages}</span>
          <button disabled={page >= totalPages - 1} onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} className="px-2 py-1 bg-[#222] rounded text-white">Next</button>
        </div>
        {/* Drag adjuster for chart size */}
        <div className="flex items-center gap-2 text-white">
          <span>Chart Size:</span>
          <div
            ref={dragRef}
            onMouseDown={onDragStart}
            style={{ width: 24, height: 24, background: dragging ? '#333' : '#222', cursor: 'nwse-resize', borderRadius: 4, display: 'inline-block', border: '1px solid #444', color: '#fff' }}
            title="Drag to resize charts"
          >
            45
          </div>
          <span>{chartSize.width}x{chartSize.height}</span>
        </div>
      </div>
      {/* Chart Grid */}
      <div
        className="grid gap-6 p-6"
        style={{ gridTemplateColumns: `repeat(${layout}, minmax(0, 1fr))`, background: '#111' }}
      >
        {pagedTrades().map((trade, idx) => {
          const symbol = getRobustSymbol(trade.Pair);
          return (
            <div key={idx} className="bg-[#181818] rounded-lg p-2 flex flex-col items-center shadow relative" style={{ minHeight: chartSize.height, minWidth: chartSize.width }}>
              <div className="font-bold mb-1 text-white">{symbol} {source === "tradingview" ? "4c8" : "7e1"} CHART</div>
              {source === "tradingview" ? (
                <div id={`tv_chart_${idx}`} style={{ width: "100%", height: chartSize.height }} />
              ) : (
                <iframe
                  title={symbol}
                  src={`https://www.binance.com/en/futures/${symbol}`}
                  style={{ width: "100%", height: chartSize.height, border: 0 }}
                  sandbox="allow-scripts allow-same-origin allow-popups"
                />
              )}
              {/* Trade Info */}
              <div className="mt-2 text-white w-full flex flex-col gap-1" style={{ fontSize: fontSize }}>
                <div>PL: <b>{trade.PL ?? 'N/A'}</b></div>
                <div>
                  <span
                    className="cursor-pointer hover:underline px-1"
                    onClick={() => handleCopy('Buy_Price', trade.Buy_Price, idx)}
                    title="Click to copy"
                  >Buy: <b>{trade.Buy_Price ?? 'N/A'}</b>{copied[`${idx}_Buy_Price`] && <span className="ml-1 text-green-400">Copied!</span>}</span>
                  <span className="mx-1">|</span>
                  <span
                    className="cursor-pointer hover:underline px-1"
                    onClick={() => handleCopy('Sell_Price', trade.Sell_Price, idx)}
                    title="Click to copy"
                  >Sell: <b>{trade.Sell_Price ?? 'N/A'}</b>{copied[`${idx}_Sell_Price`] && <span className="ml-1 text-green-400">Copied!</span>}</span>
                </div>
                <div>
                  <span
                    className="cursor-pointer hover:underline px-1"
                    onClick={() => handleCopy('Stop_Price', trade.Stop_Price, idx)}
                    title="Click to copy"
                  >Stop: <b>{trade.Stop_Price ?? 'N/A'}</b>{copied[`${idx}_Stop_Price`] && <span className="ml-1 text-green-400">Copied!</span>}</span>
                  <span className="mx-1">|</span>
                  <span
                    className="cursor-pointer hover:underline px-1"
                    onClick={() => handleCopy('Save_Price', trade.Save_Price, idx)}
                    title="Click to copy"
                  >Save: <b>{trade.Save_Price ?? 'N/A'}</b>{copied[`${idx}_Save_Price`] && <span className="ml-1 text-green-400">Copied!</span>}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ChartGridPage; 