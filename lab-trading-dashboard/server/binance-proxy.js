const express = require('express');
const axios = require('axios');
const app = express();

app.get('/api/klines', async (req, res) => {
  try {
    const { symbol, interval, limit } = req.query;
    const url = `https://api.binance.com/api/v3/klines?symbol=${symbol}&interval=${interval}&limit=${limit || 200}`;
    const { data } = await axios.get(url);
    res.json(data);
  } catch (err) {
    res.status(500).json({ error: err.toString() });
  }
});

app.listen(4000, () => console.log('Binance proxy running on http://localhost:4000')); 