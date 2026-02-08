import React, { useState } from 'react';
import ChartGrid from './ChartGrid';

// Example 1: Basic Usage
export const BasicChartGrid = () => {
  const [showGrid, setShowGrid] = useState(false);
  
  return (
    <div className="p-4">
      <button 
        onClick={() => setShowGrid(true)}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        Show Basic Chart Grid
      </button>
      
      {showGrid && (
        <ChartGrid
          symbols={['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT']}
          gridCols={2}
          height={500}
          interval="15m"
          onClose={() => setShowGrid(false)}
        />
      )}
    </div>
  );
};

// Example 2: Advanced Usage with Custom Configuration
export const AdvancedChartGrid = () => {
  const [showGrid, setShowGrid] = useState(false);
  
  return (
    <div className="p-4">
      <button 
        onClick={() => setShowGrid(true)}
        className="bg-green-500 text-white px-4 py-2 rounded"
      >
        Show Advanced Chart Grid
      </button>
      
      {showGrid && (
        <ChartGrid
          symbols={['SOLUSDT', 'AVAXUSDT', 'DOTUSDT', 'LINKUSDT', 'UNIUSDT', 'AAVEUSDT']}
          gridCols={3}
          height={600}
          interval="1h"
          theme="dark"
          showVolume={true}
          showRSI={true}
          showMACD={true}
          onClose={() => setShowGrid(false)}
        />
      )}
    </div>
  );
};

// Example 3: Dynamic Symbols from Trade Data
export const DynamicChartGrid = ({ tradeData }) => {
  const [showGrid, setShowGrid] = useState(false);
  
  // Extract unique symbols from trade data
  const getUniqueSymbols = () => {
    if (!tradeData || !Array.isArray(tradeData)) return ['BTCUSDT', 'ETHUSDT'];
    
    const symbols = [...new Set(
      tradeData
        .filter(trade => trade.Pair)
        .map(trade => trade.Pair.replace(/<[^>]+>/g, '').toUpperCase())
    )];
    
    return symbols.slice(0, 6); // Limit to 6 symbols
  };
  
  return (
    <div className="p-4">
      <button 
        onClick={() => setShowGrid(true)}
        className="bg-purple-500 text-white px-4 py-2 rounded"
      >
        Show Dynamic Chart Grid ({getUniqueSymbols().length} symbols)
      </button>
      
      {showGrid && (
        <ChartGrid
          symbols={getUniqueSymbols()}
          gridCols={2}
          height={550}
          interval="5m"
          theme="dark"
          showVolume={false}
          showRSI={true}
          showMACD={true}
          onClose={() => setShowGrid(false)}
        />
      )}
    </div>
  );
};

// Example 4: Integration with TableView (for your existing app)
export const TableViewChartGrid = ({ filteredData }) => {
  const [showGrid, setShowGrid] = useState(false);
  
  // Extract symbols from filtered table data
  const getSymbolsFromTableData = () => {
    if (!filteredData || !Array.isArray(filteredData)) return ['BTCUSDT', 'ETHUSDT'];
    
    const symbols = [...new Set(
      filteredData
        .filter(row => row.Pair)
        .map(row => {
          // Clean HTML from Pair field
          const cleanPair = row.Pair.replace(/<[^>]+>/g, '').trim();
          return cleanPair.toUpperCase();
        })
        .filter(symbol => symbol && symbol.includes('USDT'))
    )];
    
    return symbols.slice(0, 8); // Limit to 8 symbols
  };
  
  const symbols = getSymbolsFromTableData();
  
  if (symbols.length === 0) {
    return (
      <div className="p-4 text-gray-500">
        No valid symbols found in table data
      </div>
    );
  }
  
  return (
    <div className="p-4">
      <div className="flex items-center gap-4 mb-4">
        <button 
          onClick={() => setShowGrid(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
        >
          📊 View Charts ({symbols.length} symbols)
        </button>
        <span className="text-sm text-gray-600">
          Symbols: {symbols.join(', ')}
        </span>
      </div>
      
      {showGrid && (
        <ChartGrid
          symbols={symbols}
          gridCols={symbols.length <= 4 ? 2 : 3}
          height={600}
          interval="15m"
          theme="dark"
          showVolume={true}
          showRSI={true}
          showMACD={true}
          onClose={() => setShowGrid(false)}
        />
      )}
    </div>
  );
};

// Example 5: Mini Chart Grid for Dashboard
export const MiniChartGrid = () => {
  const [showGrid, setShowGrid] = useState(false);
  
  return (
    <div className="p-4">
      <button 
        onClick={() => setShowGrid(true)}
        className="bg-orange-500 text-white px-4 py-2 rounded"
      >
        📈 Mini Charts
      </button>
      
      {showGrid && (
        <ChartGrid
          symbols={['BTCUSDT', 'ETHUSDT']}
          gridCols={2}
          height={400}
          interval="5m"
          theme="dark"
          showVolume={false}
          showRSI={true}
          showMACD={false}
          onClose={() => setShowGrid(false)}
        />
      )}
    </div>
  );
};

export default {
  BasicChartGrid,
  AdvancedChartGrid,
  DynamicChartGrid,
  TableViewChartGrid,
  MiniChartGrid
}; 