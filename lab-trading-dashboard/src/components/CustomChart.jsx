import React, { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import { RSI, MACD } from 'technicalindicators';
import axios from 'axios';
import { api } from '../config';

const LOCAL_PROXY = api('/api/klines');

function toUnix(ts) {
  return Math.floor(ts / 1000);
}

function cleanSymbol(symbol) {
  if (!symbol) return '';
  // Remove everything after first non-alphanumeric (e.g. _250926, -PERP, etc.)
  return symbol.replace(/[^A-Z0-9]/gi, '').replace(/(PERP|USDTFUT|USDTPERP|USDTPERF|USDTPER)/, '').replace(/\d{6,}$/,'').toUpperCase();
}

function getTradeField(trade, key) {
  // Try both camel and snake case
  return trade[key] ?? trade[key.toLowerCase()] ?? trade[key.replace('_', '').toLowerCase()] ?? 'N/A';
}

function isValidBinanceSpotSymbol(symbol) {
  // Only allow symbols that are all caps, end with USDT, and have no numbers or underscores after USDT
  return /^[A-Z]+USDT$/.test(symbol);
}

const CustomChart = ({ symbol, trade, interval = '15m', theme = 'dark', width = 400, height = 300 }) => {
  const chartRef = useRef();
  const chartContainerRef = useRef();
  const [error, setError] = useState(null);

  useEffect(() => {
    let chart, candleSeries, rsiSeries, macdSeries, buyLine, sellLine, stopLine, saveLine;
    let destroyed = false;
    async function fetchData() {
      setError(null);
      const cleanSym = cleanSymbol(symbol);
      if (!isValidBinanceSpotSymbol(cleanSym)) {
        setError('Invalid or unsupported symbol');
        return;
      }
      const intervalMap = { '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m', '1h': '1h', '4h': '4h', '1d': '1d' };
      const binanceInterval = intervalMap[interval] || '15m';
      const url = `${LOCAL_PROXY}?symbol=${cleanSym}&interval=${binanceInterval}&limit=200`;
      try {
        const { data } = await axios.get(url);
        if (destroyed) return;
        if (!data || !Array.isArray(data) || data.length === 0) {
          setError('No data for this symbol');
          console.warn('[CustomChart] No data for', cleanSym, data);
          return;
        }
        const candles = data.map(d => ({
          time: toUnix(d[0]),
          open: +d[1],
          high: +d[2],
          low: +d[3],
          close: +d[4],
          value: +d[5],
          volume: +d[5],
        }));
        const closes = candles.map(c => c.close);
        const rsi = RSI.calculate({ period: 9, values: closes });
        const macd = MACD.calculate({ values: closes, fastPeriod: 12, slowPeriod: 26, signalPeriod: 9, SimpleMAOscillator: false, SimpleMASignal: false });
        chart = createChart(chartContainerRef.current, {
          width,
          height,
          layout: { background: { color: theme === 'dark' ? '#181818' : '#fff' }, textColor: theme === 'dark' ? '#fff' : '#222' },
          grid: { vertLines: { color: '#222' }, horzLines: { color: '#222' } },
          timeScale: { timeVisible: true, secondsVisible: false },
          rightPriceScale: { visible: false },
        });
        candleSeries = chart.addCandlestickSeries();
        candleSeries.setData(candles);
        rsiSeries = chart.addLineSeries({ color: '#fbc02d', lineWidth: 2, priceScaleId: 'rsi' });
        rsiSeries.setData(rsi.map((v, i) => ({ time: candles[i + (candles.length - rsi.length)].time, value: v })));
        const macdLineSeries = chart.addLineSeries({ color: '#42a5f5', lineWidth: 2, priceScaleId: 'macd' });
        macdLineSeries.setData(macd.map((v, i) => ({ time: candles[i + (candles.length - macd.length)].time, value: v.MACD })));
        const signalLineSeries = chart.addLineSeries({ color: '#ff9800', lineWidth: 2, priceScaleId: 'macd' });
        signalLineSeries.setData(macd.map((v, i) => ({ time: candles[i + (candles.length - macd.length)].time, value: v.signal })));
        const macdHistSeries = chart.addHistogramSeries({ priceScaleId: 'macd', scaleMargins: { top: 0.7, bottom: 0 } });
        const macdHistData = macd.map((v, i, arr) => {
          const value = v.MACD - v.signal;
          let color = '#26a69a'; // default green
          if (i > 0) {
            if (value > 0 && value > (arr[i-1].MACD - arr[i-1].signal)) color = '#26a69a'; // green, rising
            else if (value > 0) color = '#b2dfdb'; // green, falling
            else if (value < 0 && value < (arr[i-1].MACD - arr[i-1].signal)) color = '#ef5350'; // red, falling
            else color = '#ffcdd2'; // red, rising
          } else {
            color = value >= 0 ? '#26a69a' : '#ef5350';
          }
          return {
            time: candles[i + (candles.length - macd.length)].time,
            value,
            color
          };
        });
        macdHistSeries.setData(macdHistData);
        if (getTradeField(trade, 'Buy_Price') !== 'N/A') buyLine = candleSeries.createPriceLine({ price: +getTradeField(trade, 'Buy_Price'), color: '#00e676', lineWidth: 2, lineStyle: 2, title: 'Buy' });
        if (getTradeField(trade, 'Sell_Price') !== 'N/A') sellLine = candleSeries.createPriceLine({ price: +getTradeField(trade, 'Sell_Price'), color: '#ff1744', lineWidth: 2, lineStyle: 2, title: 'Sell' });
        if (getTradeField(trade, 'Stop_Price') !== 'N/A') stopLine = candleSeries.createPriceLine({ price: +getTradeField(trade, 'Stop_Price'), color: '#ffd600', lineWidth: 2, lineStyle: 2, title: 'Stop' });
        if (getTradeField(trade, 'Save_Price') !== 'N/A') saveLine = candleSeries.createPriceLine({ price: +getTradeField(trade, 'Save_Price'), color: '#00b0ff', lineWidth: 2, lineStyle: 2, title: 'Save' });
      } catch (err) {
        setError('No data for this symbol (CORS or symbol error)');
        console.error('[CustomChart] Error fetching data for', cleanSym, err);
      }
    }
    fetchData();
    return () => { destroyed = true; if (chart) chart.remove(); };
  }, [symbol, trade, interval, theme, width, height]);

  return (
    <div style={{ width, height, background: theme === 'dark' ? '#181818' : '#fff', borderRadius: 8, position: 'relative' }}>
      {error ? (
        <div style={{ color: '#fff', textAlign: 'center', paddingTop: height/2 - 30, fontWeight: 'bold' }}>{error}</div>
      ) : (
        <div ref={chartContainerRef} style={{ width, height }} />
      )}
    </div>
  );
};

export default CustomChart;
export { isValidBinanceSpotSymbol }; 