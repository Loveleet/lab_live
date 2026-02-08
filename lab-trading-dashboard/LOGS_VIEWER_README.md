# 🔍 Interactive Log Viewer for Trading Bot

## Overview
A comprehensive interactive log viewer for trading bot signal processing logs with customizable grid and list views, advanced filtering, and real-time statistics.

## 🚀 Features

### 📦 Grid View
- **Card-based Layout**: Each log displayed as an interactive card
- **Customizable Fields**: Choose which fields to display
- **Field Positioning**: Adjust field positions (top-left, top-right, center, bottom-left, bottom-right)
- **Expandable JSON**: Click to expand and view detailed JSON data
- **Color-coded Actions**: BUY/SELL signals with distinct colors
- **Trend Indicators**: Visual trend indicators with color coding

### 📄 List View
- **Table Format**: Classic table layout with sortable columns
- **Customizable Columns**: Show/hide columns as needed
- **JSON Detail Modal**: Full-screen JSON viewer on row click
- **Responsive Design**: Works on all screen sizes

### ⚙️ Adjust View Panel
- **View Mode Toggle**: Switch between Grid and List views
- **Field Selection**: Choose which fields to display
- **Field Reordering**: Drag and drop to reorder columns (List view)
- **Position Control**: Adjust field positions within grid cards
- **Settings Persistence**: All settings saved to localStorage

### 📊 Report Summary
- **Total Logs Count**: Real-time count of filtered logs
- **Buy/Sell Statistics**: Separate counts for BUY and SELL signals
- **Average RSI**: Calculated average RSI across filtered data
- **Unique Symbols**: Count of unique trading symbols
- **Machine Statistics**: Count of active machines
- **Date Range**: Earliest and latest log timestamps

### 🔍 Advanced Filtering
- **Symbol Filter**: Search by trading symbol (e.g., BTCUSDT)
- **Signal Type**: Filter by signal type
- **Machine Filter**: Filter by specific machine ID
- **Date Range**: Filter by log timestamp
- **RSI Range**: Filter by RSI values (min/max)
- **Action Filter**: Filter by BUY/SELL actions
- **Real-time Updates**: Filters apply instantly to both view and summary

## 🛠️ Backend API

### Endpoints

#### GET `/api/SignalProcessingLogs`
Fetches paginated signal processing logs with filtering support.

**Query Parameters:**
- `page` (number): Page number (default: 1)
- `limit` (number): Items per page (default: 50)
- `symbol` (string): Filter by symbol (partial match)
- `signalType` (string): Filter by signal type
- `machineId` (string): Filter by machine ID
- `fromDate` (string): Filter from date (ISO format)
- `toDate` (string): Filter to date (ISO format)
- `minRsi` (number): Minimum RSI value
- `maxRsi` (number): Maximum RSI value
- `action` (string): Filter by action (BUY/SELL)

**Response:**
```json
{
  "logs": [
    {
      "Id": 1,
      "Symbol": "BTCUSDT",
      "Interval": "1h",
      "SignalType": "BUY",
      "Trend": "UP",
      "RSI": 65.5,
      "MACD": 0.0023,
      "LogTime": "2024-01-15T10:30:00Z",
      "MachineId": "MACHINE_001",
      "json_data": { /* detailed signal data */ },
      "Status": "ACTIVE",
      "Action": "BUY",
      "Price": 45000.50,
      "Volume": 100.5
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 1250,
    "totalPages": 25,
    "hasNext": true,
    "hasPrev": false
  }
}
```

#### GET `/api/SignalProcessingLogs/summary`
Fetches summary statistics for filtered logs.

**Query Parameters:** Same as logs endpoint

**Response:**
```json
{
  "summary": {
    "totalLogs": 1250,
    "buyCount": 650,
    "sellCount": 600,
    "avgRSI": "58.75",
    "uniqueSymbols": 15,
    "uniqueMachines": 5,
    "earliestLog": "2024-01-01T00:00:00Z",
    "latestLog": "2024-01-15T23:59:59Z"
  }
}
```

## 🎨 UI Components

### LogsViewer
Main component that orchestrates the entire log viewing experience.

### LogCard (Grid View)
Individual card component for grid view with:
- Customizable field positioning
- Expandable JSON section
- Action buttons for interaction
- Color-coded indicators

### LogTable (List View)
Table component for list view with:
- Sortable columns
- Customizable column visibility
- Row click handlers
- Responsive design

### JsonModal
Full-screen modal for viewing detailed JSON data with:
- Syntax highlighting
- Scrollable content
- Close functionality

## 🔧 Configuration

### Field Configuration
```javascript
const availableFields = {
  symbol: { label: 'Symbol', icon: TrendingUp, color: 'text-blue-500' },
  interval: { label: 'Interval', icon: Clock, color: 'text-green-500' },
  signalType: { label: 'Signal Type', icon: Zap, color: 'text-purple-500' },
  trend: { label: 'Trend', icon: TrendingUp, color: 'text-orange-500' },
  rsi: { label: 'RSI', icon: Activity, color: 'text-red-500' },
  macd: { label: 'MACD', icon: BarChart3, color: 'text-indigo-500' },
  action: { label: 'Action', icon: Zap, color: 'text-yellow-500' },
  price: { label: 'Price', icon: TrendingUp, color: 'text-emerald-500' },
  volume: { label: 'Volume', icon: BarChart3, color: 'text-cyan-500' },
  machineId: { label: 'Machine ID', icon: Activity, color: 'text-gray-500' },
  logTime: { label: 'Log Time', icon: Clock, color: 'text-gray-600' },
  status: { label: 'Status', icon: Activity, color: 'text-gray-700' }
};
```

### Position Options
- `top-left`: Top left corner
- `top-right`: Top right corner
- `center`: Center of card
- `bottom-left`: Bottom left corner
- `bottom-right`: Bottom right corner

## 🚀 Usage

### Navigation
1. Click on "Reports & Logs" in the sidebar
2. The LogsViewer will load with default settings
3. Use the "Adjust View" panel to customize the display
4. Apply filters to narrow down the data
5. Switch between Grid and List views as needed

### Customization
1. Click "Adjust View" to open settings panel
2. Toggle fields on/off to show/hide them
3. For Grid view: Adjust field positions using dropdowns
4. For List view: Fields will appear as columns
5. Settings are automatically saved to localStorage

### Filtering
1. Use the filter panel at the top
2. Enter values in any filter field
3. Filters apply instantly to both view and summary
4. Clear filters by emptying the fields

## 📱 Responsive Design
- **Desktop**: Full feature set with optimal layout
- **Tablet**: Adjusted spacing and touch-friendly controls
- **Mobile**: Stacked layout with simplified controls

## 🔒 Security
- CORS properly configured for production domains
- Input validation on all filter parameters
- SQL injection protection through parameterized queries
- Error handling with user-friendly messages

## 🛠️ Development

### Prerequisites
- Node.js 16+
- React 18+
- SQL Server database with SignalProcessingLogs table

### Database Schema
```sql
CREATE TABLE SignalProcessingLogs (
  Id INT IDENTITY(1,1) PRIMARY KEY,
  Symbol NVARCHAR(20) NOT NULL,
  Interval NVARCHAR(10) NOT NULL,
  SignalType NVARCHAR(50) NOT NULL,
  Trend NVARCHAR(10),
  RSI DECIMAL(5,2),
  MACD DECIMAL(10,6),
  LogTime DATETIME2 NOT NULL,
  MachineId NVARCHAR(50) NOT NULL,
  json_data NVARCHAR(MAX),
  Status NVARCHAR(20),
  Action NVARCHAR(10),
  Price DECIMAL(18,8),
  Volume DECIMAL(18,8)
);
```

### Installation
1. Clone the repository
2. Install dependencies: `npm install`
3. Configure database connection in `server/server_shadow.js`
4. Start the backend: `npm start` (in server directory)
5. Start the frontend: `npm run dev`

## 🎯 Future Enhancements
- [ ] Export functionality (CSV, Excel)
- [ ] Advanced analytics and charts
- [ ] Real-time updates via WebSocket
- [ ] User preferences and themes
- [ ] Bulk operations on logs
- [ ] Advanced search with regex support
- [ ] Log comparison tools
- [ ] Performance optimization for large datasets

## 📞 Support
For issues or questions, please refer to the main project documentation or create an issue in the repository. 