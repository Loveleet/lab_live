import React, { useState } from 'react';
import CustomChart, { isValidBinanceSpotSymbol } from './CustomChart';

const CustomChartGrid = ({ trades = [], layout: initialLayout = 3, interval: initialInterval = '15m', theme: initialTheme = 'dark' }) => {
  const [layout, setLayout] = useState(initialLayout);
  const [interval, setInterval] = useState(initialInterval);
  const [theme, setTheme] = useState(initialTheme);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [fontSize, setFontSize] = useState(14); // Default font size
  const [chartSizes, setChartSizes] = useState({}); // { idx: { width, height } }
  const [gridColWidth, setGridColWidth] = useState(400); // Default grid column width

  // Only show trades with valid Binance spot symbols
  const filteredTrades = trades.filter(trade => isValidBinanceSpotSymbol(trade.Pair.replace(/<[^>]+>/g, '').replace(/[^A-Z0-9]/gi, '').toUpperCase()));
  const pagedTrades = filteredTrades.slice(page * pageSize, (page + 1) * pageSize);
  const totalPages = Math.ceil(filteredTrades.length / pageSize);

  return (
    <div style={{ background: theme === 'dark' ? '#111' : '#fff', minHeight: '100vh', padding: 24 }}>
      <div style={{ marginBottom: 16, color: theme === 'dark' ? '#fff' : '#222' }}>
        <label>Interval:
          <select value={interval} onChange={e => setInterval(e.target.value)} style={{ marginLeft: 8 }}>
            {['1m','3m','5m','15m','30m','1h','4h','1d'].map(opt => <option key={opt} value={opt}>{opt}</option>)}
          </select>
        </label>
        <label style={{ marginLeft: 16 }}>Layout:
          <select value={layout} onChange={e => setLayout(Number(e.target.value))} style={{ marginLeft: 8 }}>
            {[1,2,3,4,5,6].map(opt => <option key={opt} value={opt}>{opt} per row</option>)}
          </select>
        </label>
        <label style={{ marginLeft: 16 }}>Theme:
          <select value={theme} onChange={e => setTheme(e.target.value)} style={{ marginLeft: 8 }}>
            {['dark','light'].map(opt => <option key={opt} value={opt}>{opt}</option>)}
          </select>
        </label>
        <label style={{ marginLeft: 16 }}>Page Size:
          <select value={pageSize} onChange={e => { setPageSize(Number(e.target.value)); setPage(0); }} style={{ marginLeft: 8 }}>
            {[5,10,20,50,100].map(opt => <option key={opt} value={opt}>{opt}</option>)}
          </select>
        </label>
        <label style={{ marginLeft: 16 }}>Font Size:
          <select value={fontSize} onChange={e => setFontSize(Number(e.target.value))} style={{ marginLeft: 8 }}>
            {[12, 14, 16, 18, 20].map(opt => <option key={opt} value={opt}>{opt}px</option>)}
          </select>
        </label>
        <label style={{ marginLeft: 16 }}>Grid Width:
          <input type="range" min={200} max={800} value={gridColWidth} onChange={e => setGridColWidth(Number(e.target.value))} style={{ marginLeft: 8, verticalAlign: 'middle' }} />
          <span style={{ marginLeft: 8 }}>{gridColWidth}px</span>
        </label>
        <span style={{ marginLeft: 16 }}>Page {page+1} / {totalPages}</span>
        <button disabled={page===0} onClick={()=>setPage(p=>Math.max(0,p-1))} style={{ marginLeft: 8 }}>Prev</button>
        <button disabled={page>=totalPages-1} onClick={()=>setPage(p=>Math.min(totalPages-1,p+1))} style={{ marginLeft: 8 }}>Next</button>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${layout}, ${gridColWidth}px)`, gap: 24 }}>
        {pagedTrades.map((trade, idx) => {
          const cleanSymbol = trade.Pair.replace(/<[^>]+>/g, '').replace(/[^A-Z0-9]/gi, '').toUpperCase();
          const isValid = isValidBinanceSpotSymbol(cleanSymbol);
          const size = chartSizes[idx] || { width: gridColWidth, height: 300 };
          // Drag logic for this chart
          const dragRef = React.useRef();
          const [dragging, setDragging] = React.useState(false);
          const [dragStart, setDragStart] = React.useState({ x: 0, y: 0, width: size.width, height: size.height });
          const onDragStart = (e) => {
            setDragging(true);
            setDragStart({ x: e.clientX, y: e.clientY, width: size.width, height: size.height });
          };
          const onDrag = (e) => {
            if (!dragging) return;
            const dx = e.clientX - dragStart.x;
            const dy = e.clientY - dragStart.y;
            setChartSizes(sizes => ({ ...sizes, [idx]: { width: Math.max(200, dragStart.width + dx), height: Math.max(150, dragStart.height + dy) } }));
          };
          const onDragEnd = () => setDragging(false);
          React.useEffect(() => {
            if (dragging) {
              window.addEventListener('mousemove', onDrag);
              window.addEventListener('mouseup', onDragEnd);
            } else {
              window.removeEventListener('mousemove', onDrag);
              window.removeEventListener('mouseup', onDragEnd);
            }
            return () => {
              window.removeEventListener('mousemove', onDrag);
              window.removeEventListener('mouseup', onDragEnd);
            };
          }, [dragging]);
          // Range slider for chart height (styled like ecommerce price filter)
          const onHeightChange = (e) => setChartSizes(sizes => ({ ...sizes, [idx]: { ...size, height: Number(e.target.value) } }));
          return (
            <div key={idx} style={{ background: theme === 'dark' ? '#181818' : '#f9f9f9', borderRadius: 8, padding: 8 }}>
              <div style={{ color: theme === 'dark' ? '#fff' : '#222', fontWeight: 'bold', marginBottom: 4 }}>{trade.Pair}</div>
              {isValid ? (
                <>
                  {/* Height range adjuster above chart */}
                  <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
                    <label style={{ color: theme === 'dark' ? '#fff' : '#222', fontSize: 13, marginRight: 8 }}>Chart Height:</label>
                    <input
                      type="range"
                      min={150}
                      max={800}
                      value={size.height}
                      onChange={onHeightChange}
                      style={{ flex: 1, accentColor: '#6366f1', marginRight: 8 }}
                      title="Adjust chart height"
                    />
                    <span style={{ color: theme === 'dark' ? '#fff' : '#222', fontSize: 13, minWidth: 40, textAlign: 'right' }}>{size.height}px</span>
                  </div>
                  <div style={{ position: 'relative', width: size.width, height: size.height }}>
                    <CustomChart symbol={cleanSymbol} trade={trade} interval={interval} theme={theme} width={gridColWidth} height={size.height} />
                    {/* Drag handle for width/height (optional, can keep for fine-tuning) */}
                    <div
                      ref={dragRef}
                      onMouseDown={onDragStart}
                      style={{
                        position: 'absolute',
                        right: 8,
                        bottom: 8,
                        width: 32,
                        height: 32,
                        background: dragging ? '#444' : '#222',
                        cursor: 'nwse-resize',
                        borderRadius: 6,
                        border: '2px solid #888',
                        color: '#fff',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        zIndex: 2,
                        boxShadow: dragging ? '0 0 8px #888' : 'none',
                        fontSize: 22,
                        fontWeight: 'bold',
                        userSelect: 'none',
                      }}
                      title="Drag to resize chart"
                    >
                      <span style={{fontFamily: 'monospace', letterSpacing: 1}}>⋮⋮<br/>⋮⋮</span>
                    </div>
                  </div>
                </>
              ) : (
                <div style={{ width: 400, height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#f00', background: '#222', borderRadius: 8 }}>
                  Invalid or unsupported symbol
                </div>
              )}
              <div style={{ color: theme === 'dark' ? '#fff' : '#222', fontSize: fontSize, marginTop: 8 }}>
                PL: <b>{trade.PL ?? 'N/A'}</b><br/>
                Buy: <b>{trade.Buy_Price ?? 'N/A'}</b> | Sell: <b>{trade.Sell_Price ?? 'N/A'}</b><br/>
                Stop: <b>{trade.Stop_Price ?? 'N/A'}</b> | Save: <b>{trade.Save_Price ?? 'N/A'}</b><br/>
                Unique ID: <b>{trade.Unique_id ?? trade.Unique_ID ?? 'N/A'}</b><br/>
                Type: <b>{trade.Action ?? trade.Type ?? 'N/A'}</b><br/>
                Candle Date: <b>{trade.Candel_time ?? trade.Candle_time ?? 'N/A'}</b><br/>
                Operator Time: <b>{trade.Operator_Trade_time ?? 'N/A'}</b><br/>
                Closing Time: <b>{trade.Operator_Close_time ?? 'N/A'}</b>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CustomChartGrid; 