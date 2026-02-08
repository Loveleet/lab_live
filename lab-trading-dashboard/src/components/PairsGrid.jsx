import React from 'react';
import Button from '@mui/material/Button';

const PairsGrid = ({ onSelectPair }) => {
  return (
    <div style={{ padding: 32, textAlign: 'center' }}>
      <h2>Pairs Grid (Placeholder)</h2>
      <Button variant="contained" color="primary" onClick={() => onSelectPair('BTCUSDT')}>
        Simulate Select BTCUSDT
      </Button>
    </div>
  );
};

export default PairsGrid; 