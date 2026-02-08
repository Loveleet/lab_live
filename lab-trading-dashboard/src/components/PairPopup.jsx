import React from 'react';

const PairPopup = ({ open, onClose, title, timestamps, onTimestampClick }) => {
  if (!open) return null;
  return (
    <div className="fixed top-0 left-0 w-full bg-white shadow-lg z-50 p-4 flex flex-col items-center">
      <div className="flex justify-between w-full max-w-2xl mb-2">
        <span className="font-bold text-lg">{title}</span>
        <button onClick={onClose} className="text-red-500 font-bold">Close</button>
      </div>
      <div className="flex flex-row gap-4 flex-wrap">
        {timestamps.map(ts => (
          <button
            key={ts.value}
            className="px-3 py-1 bg-blue-100 rounded hover:bg-blue-300"
            onClick={() => onTimestampClick(ts)}
          >
            {ts.label}
          </button>
        ))}
      </div>
    </div>
  );
};

export default PairPopup; 