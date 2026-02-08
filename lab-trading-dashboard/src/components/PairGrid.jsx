import React, { useState } from 'react';

// Example badge icons (replace with real icons as needed)
const BADGE_ICONS = {
  running: '🏃',
  hedgeRunning: '🤺',
  closedProfit: '🏅',
  hedgeHold: '⏳',
};

const PairGrid = ({
  pairs,
  sortOptions,
  onSortChange,
  sortOrder,
  onSortOrderToggle,
  searchValue,
  onSearchChange,
  onSelectPair,
  selectedPair,
  getBadgeInfo,
  getTileColor,
}) => {
  return (
    <div className="w-full">
      {/* Sort/Search Bar */}
      <div className="flex flex-wrap items-center gap-4 mb-4">
        <select
          value={sortOptions.selected}
          onChange={e => onSortChange(e.target.value)}
          className="px-3 py-2 border rounded"
        >
          {sortOptions.options.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <button
          onClick={onSortOrderToggle}
          className="px-2 py-1 border rounded"
        >
          {sortOrder === 'asc' ? '⬆️ Asc' : '⬇️ Desc'}
        </button>
        <input
          type="text"
          value={searchValue}
          onChange={e => onSearchChange(e.target.value)}
          placeholder="Search pair..."
          className="px-3 py-2 border rounded flex-1"
        />
      </div>
      {/* Grid of unique pairs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {pairs.map(pair => {
          const badges = getBadgeInfo(pair);
          const tileColor = getTileColor(pair);
          const isSelected = selectedPair && selectedPair.symbol === pair.symbol;
          return (
            <div
              key={pair.symbol}
              className={`rounded-lg shadow p-4 cursor-pointer transition-all duration-200 ${isSelected ? 'scale-105 z-10 border-2 border-blue-500' : 'hover:scale-105'} `}
              style={{ background: tileColor, opacity: isSelected ? 1 : 0.95 }}
              onClick={() => onSelectPair(pair)}
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="font-bold text-lg">{pair.symbol}</span>
                {badges.map(b => (
                  <span key={b.type} title={b.label} className="inline-block text-xl align-middle">{BADGE_ICONS[b.type]}</span>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-1 text-xs">
                <div>Sell: <b>{pair.sellCount}</b></div>
                <div>Buy: <b>{pair.buyCount}</b></div>
                <div>Running: <b>{pair.runningCount}</b></div>
                <div>Profit Closed: <b>{pair.profitClosedCount}</b></div>
                <div>Hedge Running: <b>{pair.hedgeRunningCount}</b></div>
                <div>Hedge Hold: <b>{pair.hedgeHoldCount}</b></div>
                <div>Hedge Closed: <b>{pair.hedgeClosedCount}</b></div>
                <div>Total Trades: <b>{pair.totalTrades}</b></div>
                <div>Total Sell: <b>{pair.totalSell}</b></div>
                <div>Total Buy: <b>{pair.totalBuy}</b></div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PairGrid; 