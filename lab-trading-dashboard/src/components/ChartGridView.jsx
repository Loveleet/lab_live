// ChartGridView.jsx
import React, { useEffect, useRef } from "react";

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

const ChartGridView = ({
  symbols = [],
  trades = [],
  chartSettings = {},
  onClose,
}) => {
  const gridRef = useRef();
  const {
    layout = 2,
    height = 500,
    interval = "15",
    showRSI = true,
    showMACD = true,
    showVolume = true,
  } = chartSettings;

  // Compose studies array
  const studies = [];
  if (showRSI) studies.push("RSI@tv-basicstudies");
  if (showMACD) studies.push("MACD@tv-basicstudies");
  if (showVolume) studies.push("Volume@tv-basicstudies");

  useEffect(() => {
    loadTradingViewScript();
    const timer = setTimeout(() => {
      if (window.TradingView) {
        symbols.forEach((symbol, idx) => {
          const containerId = `tv_chart_${symbol}`;
          // Remove previous widget if any
          const container = document.getElementById(containerId);
          if (container) container.innerHTML = "";
          new window.TradingView.widget({
            container_id: containerId,
            autosize: true,
            symbol: `BINANCE:${symbol}PERP`,
            interval: interval,
            timezone: "Etc/UTC",
            theme: "dark",
            style: "8",
            locale: "en",
            studies,
            overrides: {
              "volumePaneSize": showVolume ? "medium" : "0",
              "paneProperties.topMargin": 10,
              "paneProperties.bottomMargin": 15,
              "paneProperties.rightMargin": 20,
              "scalesProperties.fontSize": 11,
              "RSI.length": 9,
            },
            hide_side_toolbar: false,
            allow_symbol_change: false,
            details: true,
            withdateranges: true,
            hideideas: true,
            toolbar_bg: "#222",
            height,
          });
        });
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [symbols, interval, showRSI, showMACD, showVolume, height]);

  // Find trade info for a symbol
  const getTradeInfo = (symbol) => {
    const trade = trades.find((t) => {
      if (!t.Pair) return false;
      const clean = typeof t.Pair === "string" ? t.Pair.replace(/<[^>]+>/g, "").toUpperCase().trim() : "";
      return clean === symbol;
    });
    return trade || {};
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60">
      <div className="bg-white rounded-lg shadow-lg p-6 max-w-7xl w-full relative overflow-y-auto" style={{ maxHeight: '90vh' }}>
        <button
          className="absolute top-2 right-2 text-gray-600 hover:text-black text-2xl font-bold"
          onClick={onClose}
          aria-label="Close"
        >
          ×
        </button>
        <h2 className="text-xl font-bold mb-4 text-center">Chart Grid View</h2>
        {/* Controls */}
        <div className="flex flex-wrap gap-4 mb-4 items-center justify-center">
          <label>Height:
            <input
              type="number"
              min={200}
              max={1200}
              value={height}
              onChange={e => chartSettings.setHeight && chartSettings.setHeight(Number(e.target.value))}
              className="ml-2 border rounded px-2 py-1 w-20"
            />
          </label>
          <label>Interval:
            <select
              value={interval}
              onChange={e => chartSettings.setInterval && chartSettings.setInterval(e.target.value)}
              className="ml-2 border rounded px-2 py-1"
            >
              {['1','3','5','15','30','60','240','D'].map(opt => (
                <option key={opt} value={opt}>{opt}</option>
              ))}
            </select>
          </label>
          <label className="flex items-center gap-1">
            <input type="checkbox" checked={showRSI} onChange={e => chartSettings.setShowRSI && chartSettings.setShowRSI(e.target.checked)} /> RSI
          </label>
          <label className="flex items-center gap-1">
            <input type="checkbox" checked={showMACD} onChange={e => chartSettings.setShowMACD && chartSettings.setShowMACD(e.target.checked)} /> MACD
          </label>
          <label className="flex items-center gap-1">
            <input type="checkbox" checked={showVolume} onChange={e => chartSettings.setShowVolume && chartSettings.setShowVolume(e.target.checked)} /> Volume
          </label>
          <label>Layout:
            <select
              value={layout}
              onChange={e => chartSettings.setLayout && chartSettings.setLayout(Number(e.target.value))}
              className="ml-2 border rounded px-2 py-1"
            >
              {[1,2,3,4].map(opt => (
                <option key={opt} value={opt}>{opt} per row</option>
              ))}
            </select>
          </label>
        </div>
        {/* Chart Grid */}
        <div
          ref={gridRef}
          className="grid gap-6"
          style={{ gridTemplateColumns: `repeat(${layout}, minmax(0, 1fr))` }}
        >
          {symbols.map((symbol) => {
            const trade = getTradeInfo(symbol);
            return (
              <div key={symbol} className="bg-gray-100 rounded-lg p-2 flex flex-col items-center shadow">
                <div className="font-bold mb-1">{symbol}</div>
                <div id={`tv_chart_${symbol}`} style={{ width: '100%', height: height }} />
                {/* Trade Info */}
                <div className="mt-2 text-xs text-gray-700 w-full">
                          <div>PL: <b>{trade.pl_after_comm ?? 'N/A'}</b></div>
        <div>Buy: <b>{trade.buy_price ?? 'N/A'}</b> | Sell: <b>{trade.sell_price ?? 'N/A'}</b></div>
        <div>Stop: <b>{trade.stop_price ?? 'N/A'}</b> | Save: <b>{trade.save_price ?? 'N/A'}</b></div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ChartGridView;