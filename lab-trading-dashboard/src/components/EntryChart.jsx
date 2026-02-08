import React, { useEffect, useRef } from "react";
import {
  createChart,
  CrosshairMode
} from "lightweight-charts";

const EntryChart = ({ candleData, entryTime, entryPrice }) => {
  const chartContainerRef = useRef();

  useEffect(() => {
    const chart = createChart(chartContainerRef.current, {
      width: 600,
      height: 400,
      layout: {
        background: { color: "#111" },
        textColor: "#d1d4dc"
      },
      grid: {
        vertLines: { color: "#444" },
        horzLines: { color: "#444" }
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
      timeScale: {
        borderColor: "#71649C"
      },
      priceScale: {
        borderColor: "#71649C"
      }
    });

    const candleSeries = chart.addCandlestickSeries();

    candleSeries.setData(candleData);

    // Draw entry marker
    if (entryTime && entryPrice) {
      candleSeries.setMarkers([
        {
          time: entryTime,
          position: 'belowBar',
          color: entryPrice > candleData[0].close ? 'green' : 'red',
          shape: 'arrowUp',
          text: 'Entry'
        }
      ]);
    }

    return () => chart.remove();
  }, [candleData, entryTime, entryPrice]);

  return <div ref={chartContainerRef} />;
};

export default EntryChart;