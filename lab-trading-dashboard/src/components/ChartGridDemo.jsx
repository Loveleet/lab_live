import React, { useState } from 'react';
import ChartGrid from './ChartGrid';

const ChartGridDemo = () => {
  const [showChartGrid, setShowChartGrid] = useState(false);
  const [gridConfig, setGridConfig] = useState({
    symbols: ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT'],
    gridCols: 2,
    height: 600,
    interval: '15m',
    theme: 'dark',
    showVolume: true,
    showRSI: true,
    showMACD: true
  });

  const [customSymbols, setCustomSymbols] = useState('BTCUSDT,ETHUSDT,BNBUSDT,ADAUSDT');

  // Predefined symbol sets
  const symbolSets = {
    'Top 4': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT'],
    'DeFi': ['UNIUSDT', 'AAVEUSDT', 'COMPUSDT', 'SUSHIUSDT'],
    'Layer 1': ['SOLUSDT', 'AVAXUSDT', 'DOTUSDT', 'LINKUSDT'],
    'Meme': ['DOGEUSDT', 'SHIBUSDT', 'PEPEUSDT', 'FLOKIUSDT'],
    'AI': ['FETUSDT', 'OCEANUSDT', 'RNDRUSDT', 'AGIXUSDT']
  };

  const handleSymbolSetChange = (setName) => {
    setGridConfig(prev => ({
      ...prev,
      symbols: symbolSets[setName]
    }));
    setCustomSymbols(symbolSets[setName].join(','));
  };

  const handleCustomSymbolsChange = (value) => {
    setCustomSymbols(value);
    const symbols = value.split(',').map(s => s.trim().toUpperCase()).filter(s => s);
    setGridConfig(prev => ({
      ...prev,
      symbols
    }));
  };

  const handleConfigChange = (key, value) => {
    setGridConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">
            📊 TradingView Chart Grid Demo
          </h1>
          <p className="text-gray-600">
            Display multiple full TradingView charts in a responsive grid layout with advanced features.
          </p>
        </div>

        {/* Configuration Panel */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">⚙️ Configuration</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Symbol Sets */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                📈 Predefined Symbol Sets
              </label>
              <select
                onChange={(e) => handleSymbolSetChange(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md"
              >
                {Object.keys(symbolSets).map(setName => (
                  <option key={setName} value={setName}>{setName}</option>
                ))}
              </select>
            </div>

            {/* Custom Symbols */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ✏️ Custom Symbols (comma-separated)
              </label>
              <input
                type="text"
                value={customSymbols}
                onChange={(e) => handleCustomSymbolsChange(e.target.value)}
                placeholder="BTCUSDT,ETHUSDT,BNBUSDT"
                className="w-full p-2 border border-gray-300 rounded-md"
              />
            </div>

            {/* Grid Columns */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                📐 Grid Columns
              </label>
              <select
                value={gridConfig.gridCols}
                onChange={(e) => handleConfigChange('gridCols', parseInt(e.target.value))}
                className="w-full p-2 border border-gray-300 rounded-md"
              >
                <option value={1}>1 Column</option>
                <option value={2}>2 Columns</option>
                <option value={3}>3 Columns</option>
                <option value={4}>4 Columns</option>
              </select>
            </div>

            {/* Interval */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                ⏱️ Time Interval
              </label>
              <select
                value={gridConfig.interval}
                onChange={(e) => handleConfigChange('interval', e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md"
              >
                <option value="1m">1 Minute</option>
                <option value="3m">3 Minutes</option>
                <option value="5m">5 Minutes</option>
                <option value="15m">15 Minutes</option>
                <option value="30m">30 Minutes</option>
                <option value="1h">1 Hour</option>
                <option value="4h">4 Hours</option>
                <option value="1d">1 Day</option>
              </select>
            </div>

            {/* Theme */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                🎨 Theme
              </label>
              <select
                value={gridConfig.theme}
                onChange={(e) => handleConfigChange('theme', e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md"
              >
                <option value="dark">Dark</option>
                <option value="light">Light</option>
              </select>
            </div>

            {/* Chart Height */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                📏 Chart Height (px)
              </label>
              <input
                type="number"
                value={gridConfig.height}
                onChange={(e) => handleConfigChange('height', parseInt(e.target.value))}
                min="400"
                max="1000"
                step="50"
                className="w-full p-2 border border-gray-300 rounded-md"
              />
            </div>
          </div>

          {/* Indicators */}
          <div className="mt-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              📊 Indicators
            </label>
            <div className="flex flex-wrap gap-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={gridConfig.showRSI}
                  onChange={(e) => handleConfigChange('showRSI', e.target.checked)}
                  className="mr-2"
                />
                RSI
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={gridConfig.showMACD}
                  onChange={(e) => handleConfigChange('showMACD', e.target.checked)}
                  className="mr-2"
                />
                MACD
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={gridConfig.showVolume}
                  onChange={(e) => handleConfigChange('showVolume', e.target.checked)}
                  className="mr-2"
                />
                Volume
              </label>
            </div>
          </div>

          {/* Launch Button */}
          <div className="mt-6">
            <button
              onClick={() => setShowChartGrid(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-semibold text-lg"
            >
              🚀 Launch Chart Grid
            </button>
          </div>
        </div>

        {/* Current Configuration Display */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h3 className="text-lg font-semibold mb-3">📋 Current Configuration</h3>
          <div className="bg-gray-50 p-4 rounded-md">
            <pre className="text-sm text-gray-700 overflow-x-auto">
              {JSON.stringify(gridConfig, null, 2)}
            </pre>
          </div>
        </div>

        {/* Features List */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold mb-3">✨ Features</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium text-gray-800 mb-2">📊 Chart Features</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Full TradingView advanced charts</li>
                <li>• RSI, MACD, Volume indicators</li>
                <li>• Drawing tools and annotations</li>
                <li>• Multiple timeframes</li>
                <li>• Dark/Light theme support</li>
              </ul>
            </div>
            <div>
              <h4 className="font-medium text-gray-800 mb-2">🎛️ Grid Features</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Responsive grid layout</li>
                <li>• Fullscreen mode</li>
                <li>• Customizable columns</li>
                <li>• Individual chart controls</li>
                <li>• Loading states</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Chart Grid Modal */}
      {showChartGrid && (
        <ChartGrid
          {...gridConfig}
          onClose={() => setShowChartGrid(false)}
        />
      )}
    </div>
  );
};

export default ChartGridDemo; 