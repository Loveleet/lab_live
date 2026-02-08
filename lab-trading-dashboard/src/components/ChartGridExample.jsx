import React, { useState } from 'react';
import ChartGrid from './ChartGrid';

const ChartGridExample = () => {
  const [symbols, setSymbols] = useState(['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT']);
  const [newSymbol, setNewSymbol] = useState('');

  const addSymbol = () => {
    if (newSymbol && !symbols.includes(newSymbol.toUpperCase())) {
      setSymbols([...symbols, newSymbol.toUpperCase()]);
      setNewSymbol('');
    }
  };

  const removeSymbol = (symbolToRemove) => {
    setSymbols(symbols.filter(s => s !== symbolToRemove));
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-8">📊 TradingView Chart Grid Example</h1>
        
        {/* Symbol Management */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-xl font-semibold mb-4">Symbol Management</h2>
          <div className="flex flex-wrap items-center gap-4 mb-4">
            <input
              type="text"
              value={newSymbol}
              onChange={(e) => setNewSymbol(e.target.value)}
              placeholder="Enter symbol (e.g., BTCUSDT)"
              className="px-3 py-2 border rounded-md"
              onKeyPress={(e) => e.key === 'Enter' && addSymbol()}
            />
            <button
              onClick={addSymbol}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
            >
              Add Symbol
            </button>
          </div>
          
          <div className="flex flex-wrap gap-2">
            {symbols.map(symbol => (
              <div key={symbol} className="flex items-center gap-2 bg-gray-100 px-3 py-1 rounded-md">
                <span className="font-medium">{symbol}</span>
                <button
                  onClick={() => removeSymbol(symbol)}
                  className="text-red-600 hover:text-red-800 text-sm"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* ChartGrid Component */}
        <ChartGrid 
          symbols={symbols}
          gridCols={2}
          height={500}
          chartType="tradingview"
          className="bg-white rounded-lg shadow-lg"
        />
      </div>
    </div>
  );
};

export default ChartGridExample; 