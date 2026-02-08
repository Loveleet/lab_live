import React, { useState } from 'react';

const ChartGrid = ({ 
  symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT'],
  gridCols = 2,
  height = 600,
  chartType = 'tradingview', // 'tradingview' or 'binance'
  className = ''
}) => {
  const [layout, setLayout] = useState(gridCols);
  const [chartHeight, setChartHeight] = useState(height);
  const [selectedChartType, setSelectedChartType] = useState(chartType);

  // Generate chart URLs based on type
  const getChartUrl = (symbol) => {
    const cleanSymbol = symbol.replace('USDT', '');
    
    if (selectedChartType === 'binance') {
      return `https://www.binance.com/en/futures/${symbol}`;
    } else {
      // TradingView full chart
      return `https://www.tradingview.com/chart/?symbol=BINANCE:${symbol}.P`;
    }
  };

  // Layout options
  const layoutOptions = [1, 2, 3, 4];

  return (
    <div className={`chart-grid-container ${className}`}>
      {/* Controls */}
      <div className="chart-controls mb-4 p-4 bg-gray-100 rounded-lg">
        <div className="flex flex-wrap items-center gap-4">
          {/* Layout Selector */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Layout:</label>
            <select 
              value={layout} 
              onChange={(e) => setLayout(Number(e.target.value))}
              className="px-3 py-1 border rounded text-sm"
            >
              {layoutOptions.map(cols => (
                <option key={cols} value={cols}>
                  {cols} Column{cols > 1 ? 's' : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Chart Type Selector */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Chart Type:</label>
            <select 
              value={selectedChartType} 
              onChange={(e) => setSelectedChartType(e.target.value)}
              className="px-3 py-1 border rounded text-sm"
            >
              <option value="tradingview">TradingView</option>
              <option value="binance">Binance</option>
            </select>
          </div>

          {/* Height Slider */}
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">Height: {chartHeight}px</label>
            <input 
              type="range" 
              min="400" 
              max="800" 
              step="50"
              value={chartHeight} 
              onChange={(e) => setChartHeight(Number(e.target.value))}
              className="w-24"
            />
          </div>

          {/* Chart Count */}
          <div className="text-sm text-gray-600">
            {symbols.length} Chart{symbols.length > 1 ? 's' : ''}
          </div>
        </div>
      </div>

      {/* Chart Grid */}
      <div 
        className="chart-grid"
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${layout}, 1fr)`,
          gap: '16px',
          padding: '16px'
        }}
      >
        {symbols.map((symbol, index) => (
          <div 
            key={symbol} 
            className="chart-item bg-white rounded-lg shadow-lg overflow-hidden border border-gray-200"
          >
            {/* Chart Header */}
            <div className="chart-header bg-gray-50 px-4 py-2 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-gray-800">{symbol}</h3>
                <a 
                  href={getChartUrl(symbol)} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  🔗 Open Full Chart
                </a>
              </div>
            </div>

            {/* Chart Iframe */}
            <div className="chart-iframe-container">
              <iframe
                src={getChartUrl(symbol)}
                title={`${symbol} Chart`}
                style={{
                  width: '100%',
                  height: `${chartHeight}px`,
                  border: 'none'
                }}
                allowFullScreen
                loading="lazy"
              />
            </div>
          </div>
        ))}
      </div>

      {/* Responsive Note */}
      <div className="mt-4 p-3 bg-blue-50 rounded-lg">
        <p className="text-sm text-blue-800">
          💡 <strong>Tip:</strong> Charts are responsive and will adjust to your screen size. 
          Use the layout controls above to change the grid arrangement.
        </p>
      </div>
    </div>
  );
};

export default ChartGrid;