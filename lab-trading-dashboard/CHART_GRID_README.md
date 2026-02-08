# 📊 ChartGrid Component

A React component that displays multiple full TradingView charts in a responsive grid layout using iframes.

## ✨ Features

- **Full TradingView Charts**: Each chart is a complete TradingView advanced chart with all features
- **Responsive Grid Layout**: Configurable 1-4 column layouts
- **Multiple Chart Sources**: Switch between TradingView and Binance charts
- **Customizable Height**: Adjust chart height with a slider (400-800px)
- **Symbol Management**: Easy to add/remove trading symbols
- **Clean UI**: Modern design with shadows, rounded corners, and proper spacing

## 🚀 Usage

### Basic Usage

```jsx
import ChartGrid from './components/ChartGrid';

function App() {
  return (
    <ChartGrid 
      symbols={['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT']}
      gridCols={2}
      height={500}
      chartType="tradingview"
    />
  );
}
```

### Advanced Usage with State Management

```jsx
import React, { useState } from 'react';
import ChartGrid from './components/ChartGrid';

function App() {
  const [showCharts, setShowCharts] = useState(false);
  const [symbols, setSymbols] = useState(['BTCUSDT', 'ETHUSDT']);

  return (
    <div>
      <button onClick={() => setShowCharts(!showCharts)}>
        {showCharts ? 'Hide Charts' : 'Show Charts'}
      </button>
      
      {showCharts && (
        <ChartGrid 
          symbols={symbols}
          gridCols={3}
          height={600}
          chartType="tradingview"
          className="my-8"
        />
      )}
    </div>
  );
}
```

## 📋 Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `symbols` | `string[]` | `['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'DOTUSDT']` | Array of trading symbols |
| `gridCols` | `number` | `2` | Number of columns in the grid (1-4) |
| `height` | `number` | `600` | Height of each chart in pixels |
| `chartType` | `'tradingview' \| 'binance'` | `'tradingview'` | Chart source platform |
| `className` | `string` | `''` | Additional CSS classes |

## 🎛️ Controls

The component includes built-in controls for:

- **Layout**: Switch between 1, 2, 3, or 4 columns
- **Chart Type**: Toggle between TradingView and Binance charts
- **Height**: Slider to adjust chart height (400-800px)
- **Chart Count**: Shows the number of active charts

## 🔗 Chart URLs

### TradingView
- Format: `https://www.tradingview.com/chart/?symbol=BINANCE:{SYMBOL}.P`
- Example: `https://www.tradingview.com/chart/?symbol=BINANCE:BTCUSDT.P`

### Binance
- Format: `https://www.binance.com/en/futures/{SYMBOL}`
- Example: `https://www.binance.com/en/futures/BTCUSDT`

## 📱 Responsive Design

The grid automatically adjusts to screen size:
- Mobile: Single column layout
- Tablet: 2-column layout
- Desktop: Configurable 1-4 column layout

## 🎨 Styling

The component uses Tailwind CSS classes and includes:
- Clean white background with shadows
- Rounded corners and proper spacing
- Hover effects on interactive elements
- Responsive design patterns

## 🔧 Customization

### Custom Styling
```jsx
<ChartGrid 
  symbols={symbols}
  className="bg-gray-100 p-4 rounded-xl"
/>
```

### Custom Symbols
```jsx
const customSymbols = [
  'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT',
  'DOTUSDT', 'LINKUSDT', 'LTCUSDT', 'BCHUSDT'
];

<ChartGrid symbols={customSymbols} />
```

## 📦 Installation

1. Copy `ChartGrid.jsx` to your components folder
2. Import and use as shown in the examples above
3. Ensure you have Tailwind CSS for styling

## 🚨 Important Notes

- **Cross-Origin**: Charts are loaded via iframes from external domains
- **Performance**: Multiple charts may impact page load time
- **Browser Support**: Requires modern browsers with iframe support
- **Network**: Requires internet connection to load TradingView/Binance

## 🎯 Example Files

- `ChartGrid.jsx` - Main component
- `ChartGridExample.jsx` - Standalone example with symbol management
- This README - Documentation

## 🔄 Updates

The component is designed to be easily extensible. Future features could include:
- Custom chart intervals
- Theme switching (dark/light)
- Chart synchronization
- Export functionality
- More chart sources (Coinbase, Kraken, etc.) 