import React from 'react';
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';

const ControlBar = () => {
  return (
    <AppBar position="static" color="default" elevation={1}>
      <Toolbar>
        <Typography variant="h6" color="inherit" component="div">
          Pairs Grid Control Bar (Placeholder)
        </Typography>
      </Toolbar>
    </AppBar>
  );
};

export default ControlBar; 