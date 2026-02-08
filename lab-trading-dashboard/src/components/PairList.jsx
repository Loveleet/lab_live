import React from 'react';

const getRowColor = (type, shade) => {
  // type: 'buy' | 'sell', shade: 0 (main), 1-5 (lighter)
  const base = type === 'buy' ? [34,197,94] : [239,68,68]; // green/red
  const alpha = shade === 0 ? 1 : 0.5 - (shade-1)*0.1;
  return `rgba(${base[0]},${base[1]},${base[2]},${alpha})`;
};

const PairList = ({
  logs,
  activeLabels,
  activeIntervals,
  fontSizes,
  masterFontSize,
  getBadges,
  getRowTypeAndShade,
}) => {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border rounded">
        <thead>
          <tr>
            <th className="sticky left-0 bg-white z-10">Badges</th>
            {activeLabels.map(label => (
              <th key={label} className="px-2 py-1">{label}</th>
            ))}
            {activeIntervals.map(interval => (
              <th key={interval} className="px-2 py-1">{interval}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {logs.map((row, idx) => {
            const { type, shade } = getRowTypeAndShade(row, idx);
            const rowColor = getRowColor(type, shade);
            const badges = getBadges(row);
            return (
              <tr key={row.Unique_id + '-' + row.candle_time + '-' + row.candle_type} style={{ background: rowColor }}>
                <td className="sticky left-0 bg-white z-10">
                  {badges.map(b => <span key={b.type}>{b.icon}</span>)}
                </td>
                {activeLabels.map(label => (
                  <td key={label} style={{ fontSize: (fontSizes[label] || 16) * masterFontSize }}>{row[label]}</td>
                ))}
                {activeIntervals.map(interval => (
                  <td key={interval}>{row[interval]}</td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default PairList; 