import React, { useEffect, useMemo, useState, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import moment from "moment";
import Sidebar from "./Sidebar";
import { API_BASE_URL } from "../config";

const toKey = (trade) => {
  const symbol = (trade?.pair || trade?.symbol || trade?.PAIR || "").toString().trim().toUpperCase();
  const candleRaw = trade?.candel_time || trade?.candle_time || trade?.Candle_time || "";
  const candleIso = candleRaw ? moment.utc(candleRaw).toISOString() : "";
  // Bucket candle to 4-hour windows so that close times within 4h are matched
  const bucketed = candleRaw
    ? moment
        .utc(candleRaw)
        .startOf("hour")
        .subtract(moment.utc(candleRaw).hour() % 4, "hours")
        .toISOString()
    : candleIso;
  return `${symbol}__${bucketed}`;
};

const parseNumber = (value) => {
  const n = parseFloat(value);
  return Number.isFinite(n) ? n : null;
};

const getActionPrice = (trade) => {
  const action = (trade?.action || "").toUpperCase();
  if (action === "BUY") {
    return parseNumber(trade?.buy_price ?? trade?.Buy_Price ?? trade?.buyPrice);
  }
  if (action === "SELL") {
    return parseNumber(trade?.sell_price ?? trade?.Sell_Price ?? trade?.sellPrice);
  }
  return parseNumber(trade?.close_price ?? trade?.Close_Price ?? trade?.price);
};

const getClosePrice = (trade) => parseNumber(trade?.close_price ?? trade?.Close_Price ?? trade?.price);
const getInterval = (trade) => (trade?.interval ?? trade?.Interval ?? "").toString();
const toBinanceInterval = (val) => {
  const raw = (val || "").toString().trim();
  if (!raw) return "15m";
  if (raw === "60") return "1h";
  if (raw === "240") return "4h";
  if (raw === "D" || raw === "1d" || raw === "1D") return "1d";
  if (/^(\\d+)[mhd]$/i.test(raw)) return raw.toLowerCase();
  return `${raw}m`;
};
const buildBinanceUrl = (symbol, interval) => {
  const cleanSymbol = (symbol || "").replace("/", "").toUpperCase();
  if (!cleanSymbol) return null;
  const intervalParam = interval ? `?interval=${toBinanceInterval(interval)}` : "";
  return `https://www.binance.com/en/futures/${cleanSymbol}${intervalParam}`;
};

const getFetcherTime = (trade) => trade?.fetcher_trade_time || trade?.fetcher_time || trade?.Fetcher_time;
const getCloseTime = (trade) =>
  trade?.operator_close_time ||
  trade?.close_time ||
  trade?.Operator_close_time ||
  trade?.["Operator_🕒❌"] ||
  trade?.operatorCloseTime;

const minutesDiff = (a, b) => {
  const ma = moment(a);
  const mb = moment(b);
  if (!ma.isValid() || !mb.isValid()) return null;
  return Math.abs(ma.diff(mb, "minutes", true));
};

const percentDiff = (base, compare) => {
  if (base === null || compare === null) return null;
  const denom = Math.max(Math.abs(base), Math.abs(compare), 1e-9);
  return Math.abs((compare - base) / denom) * 100;
};

const statusFromCloseTime = (trade) => {
  const typeVal = (trade?.type || trade?.Type || "").toString().toLowerCase();
  if (typeVal.includes("back_close")) return "closed";
  const closeAt = getCloseTime(trade);
  return closeAt ? "closed" : "running";
};

const severityTint = (pct) => {
  if (pct === null || pct === undefined) return "";
  if (pct >= 25) return "bg-red-800 text-white";
  if (pct >= 20) return "bg-red-600 text-white";
  if (pct >= 15) return "bg-red-500 text-white";
  if (pct >= 10) return "bg-orange-400 text-white";
  return "";
};

const Card = ({ title, value, subtitle, tint }) => (
  <div className={`p-4 rounded-lg border shadow-sm ${tint || "bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-700"}`}>
    <div className="text-sm font-semibold text-gray-600 dark:text-gray-300">{title}</div>
    <div className="text-3xl font-bold mt-1 text-gray-900 dark:text-white">{value}</div>
    {subtitle && <div className="text-xs mt-1 text-gray-500 dark:text-gray-400">{subtitle}</div>}
  </div>
);

const Badge = ({ children, tone }) => (
  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold ${tone || "bg-gray-200 text-gray-800"}`}>
    {children}
  </span>
);

const TradeComparePage = () => {
  // Local dark mode toggle (mirrors main app behavior)
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem("theme");
    if (saved) return saved === "dark";
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  });
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [darkMode]);

  const [trades, setTrades] = useState([]);
  const [machines, setMachines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [fromDate, setFromDate] = useState(() => localStorage.getItem("tc_fromDate") || "");
  const [toDate, setToDate] = useState(() => localStorage.getItem("tc_toDate") || "");
  const [backendMachines, setBackendMachines] = useState(() => {
    try {
      const saved = localStorage.getItem("tc_backendMachines");
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [liveMachines, setLiveMachines] = useState(() => {
    try {
      const saved = localStorage.getItem("tc_liveMachines");
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [showIssuesOnly, setShowIssuesOnly] = useState(() => localStorage.getItem("tc_showIssuesOnly") === "true");
  const [quickFilters, setQuickFilters] = useState(() => {
    try {
      const saved = localStorage.getItem("tc_quickFilters");
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [sortConfig, setSortConfig] = useState(() => {
    try {
      const saved = localStorage.getItem("tc_sortConfig");
      return saved ? JSON.parse(saved) : { key: "candle", direction: "asc" };
    } catch {
      return { key: "candle", direction: "asc" };
    }
  });
  const [selectedRow, setSelectedRow] = useState(null);
  const [expandedRow, setExpandedRow] = useState(null);
  const [rowDetails, setRowDetails] = useState({});
  const [rowLoading, setRowLoading] = useState({});
  const [detailSort, setDetailSort] = useState({ key: "ts", direction: "asc" });
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [copiedSymbol, setCopiedSymbol] = useState(null);
  const [copiedUid, setCopiedUid] = useState(null);
  const [fontScale, setFontScale] = useState(() => {
    const saved = localStorage.getItem("tc_font_scale");
    const val = saved ? parseFloat(saved) : 1;
    return Number.isFinite(val) ? val : 1;
  });
  const [compareRow, setCompareRow] = useState(null);

  // Map dashboard column keys to trade fields (best-effort)
  const valueForColumn = useCallback((col, trade) => {
    if (!trade) return "";
    const key = (col || "").toLowerCase();
    const direct = trade[col] ?? trade[col?.toLowerCase()] ?? trade[col?.toUpperCase()];
    if (direct !== undefined) return direct;
    if (key.includes("m.id") || key === "m_id" || key === "m.id") return trade.machineid ?? trade.machine_id ?? "";
    if (key.includes("unique")) return trade.unique_id ?? "";
    if (key.includes("candle")) return trade.candel_time ?? trade.candle_time ?? "";
    if (key.includes("fetcher")) return trade.fetcher_trade_time ?? trade.fetcher_time ?? "";
    if (key.includes("operator") && key.includes("close")) return trade.operator_close_time ?? "";
    if (key.includes("operator")) return trade.operator_trade_time ?? trade.operator_time ?? "";
    if (key === "pair" || key === "symbol") return trade.pair ?? trade.symbol ?? "";
    if (key.includes("interval")) return trade.interval ?? "";
    if (key.includes("action")) return trade.action ?? "";
    if (key.includes("type")) return trade.type ?? "";
    if (key.includes("pl after comm") || key === "pl" || key.includes("pl_after_comm")) return trade.pl_after_comm ?? trade.Pl_after_comm ?? "";
    if (key.includes("investment")) return trade.investment ?? "";
    if (key.includes("stop")) return trade.stop_price ?? "";
    if (key.includes("save")) return trade.save_price ?? "";
    if (key.includes("buy price")) return trade.buy_price ?? "";
    if (key.includes("sell price")) return trade.sell_price ?? "";
    if (key.includes("close price")) return trade.close_price ?? "";
    return "";
  }, []);
  const [activeRegularLabels] = useState(() => {
    try {
      const saved = localStorage.getItem("liveTradeView_regular_labels");
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [activeJsonLabels] = useState(() => {
    try {
      const saved = localStorage.getItem("liveTradeView_json_labels");
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const navigate = useNavigate();

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [tradesRes, machinesRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/trades`),
        fetch(`${API_BASE_URL}/api/machines`)
      ]);
      const tradesJson = tradesRes.ok ? await tradesRes.json() : { trades: [] };
      const machinesJson = machinesRes.ok ? await machinesRes.json() : { machines: [] };
      const tradesArr = Array.isArray(tradesJson.trades) ? tradesJson.trades : [];
      const machineArr = Array.isArray(machinesJson.machines) ? machinesJson.machines : [];
      setTrades(tradesArr);
      setMachines(machineArr);

      // Initialize selections: backend defaults to machineid "9" if present; live to all others
      const ids = [
        ...new Set([
          ...machineArr.map((m) => m.machineid?.toString()),
          ...tradesArr.map((t) => t.machineid?.toString())
        ].filter(Boolean))
      ];
      const hasNine = ids.includes("9");
      const backendDefault = hasNine ? ["9"] : ids.slice(0, 1);
      setBackendMachines((prev) => prev.length ? prev : backendDefault);
      setLiveMachines((prev) => prev.length ? prev : ids.filter((id) => !backendDefault.includes(id)));
    } catch (e) {
      console.error(e);
      setError("Failed to load trades/machines");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Persist filters/settings
  useEffect(() => {
    if (fromDate) localStorage.setItem("tc_fromDate", fromDate);
    else localStorage.removeItem("tc_fromDate");
  }, [fromDate]);

  useEffect(() => {
    if (toDate) localStorage.setItem("tc_toDate", toDate);
    else localStorage.removeItem("tc_toDate");
  }, [toDate]);

  useEffect(() => {
    localStorage.setItem("tc_backendMachines", JSON.stringify(backendMachines));
  }, [backendMachines]);

  useEffect(() => {
    localStorage.setItem("tc_liveMachines", JSON.stringify(liveMachines));
  }, [liveMachines]);

  useEffect(() => {
    localStorage.setItem("tc_showIssuesOnly", showIssuesOnly ? "true" : "false");
  }, [showIssuesOnly]);

  useEffect(() => {
    localStorage.setItem("tc_quickFilters", JSON.stringify(quickFilters));
  }, [quickFilters]);

  useEffect(() => {
    localStorage.setItem("tc_sortConfig", JSON.stringify(sortConfig));
  }, [sortConfig]);

  const fetchRowDetail = useCallback(
    async (row) => {
      const uid = row.liveTrade?.unique_id || row.liveTrade?.uid || row.liveTrade?.Unique_ID;
      if (!uid) {
        setRowDetails((prev) => ({ ...prev, [row.key]: { error: "No UID on live trade" } }));
        return;
      }
      if (rowDetails[row.key]?.loaded) return; // already loaded
      setRowLoading((prev) => ({ ...prev, [row.key]: true }));
      try {
        const res = await fetch(`${API_BASE_URL}/api/bot-event-logs?uid=${encodeURIComponent(uid)}&limit=500`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        const logs = Array.isArray(data.logs) ? data.logs : [];
        const parsed = logs.map((log) => {
          let json = {};
          try {
            json =
              typeof log.json_message === "string"
                ? JSON.parse(log.json_message)
                : log.json_message || {};
          } catch {
            json = {};
          }
          const pl = parseNumber(json["Pl After Comm"] ?? json["pl_after_comm"]);
          const ts = log.timestamp || log.created_at || log.time || log.Timestamp || log.time_stamp;
          return { ts, pl, raw: log, json };
        });
        // Sort ascending by timestamp
        parsed.sort((a, b) => {
          const ma = moment(a.ts);
          const mb = moment(b.ts);
          if (!ma.isValid() || !mb.isValid()) return 0;
          return ma.valueOf() - mb.valueOf();
        });

        // Compute post-$20 peak and drawdown
        let crossed = false;
        let peak = null;
        let peakAt = null;
        let issue = null;
        let recovered = null;
        let everPositive = null;
        parsed.forEach((entry) => {
          if (entry.pl === null) return;
          if (everPositive === null) everPositive = false;
          if (entry.pl > 0) everPositive = true;
          if (!crossed && entry.pl > 20) {
            crossed = true;
            peak = entry.pl;
            peakAt = entry.ts;
            return;
          }
          if (!crossed) return;

          if (entry.pl > peak) {
            peak = entry.pl;
            peakAt = entry.ts;
            issue = null; // clear any prior drop
            recovered = { peak, at: peakAt };
            return;
          }

          const dropPct = peak ? ((peak - entry.pl) / peak) * 100 : 0;
          if (!issue && dropPct > 20) {
            issue = { dropPct, peak, at: entry.ts, value: entry.pl };
            recovered = null;
          }
        });

        setRowDetails((prev) => ({
          ...prev,
          [row.key]: { logs: parsed, issue, recovered, loaded: true, everPositive }
        }));
      } catch (e) {
        setRowDetails((prev) => ({ ...prev, [row.key]: { error: e.message || "Failed to load logs" } }));
      } finally {
        setRowLoading((prev) => ({ ...prev, [row.key]: false }));
      }
    },
    [rowDetails]
  );

  const machineOptions = useMemo(() => {
    const ids = [
      ...new Set([
        ...machines.map((m) => m.machineid?.toString()),
        ...trades.map((t) => t.machineid?.toString())
      ].filter(Boolean))
    ];
    return ids;
  }, [machines, trades]);

  const filteredTrades = useMemo(() => {
    const from = fromDate ? moment.utc(fromDate).startOf("day") : null;
    const to = toDate ? moment.utc(toDate).endOf("day") : null;
    return trades.filter((t) => {
      const candle = t?.candel_time || t?.candle_time;
      if (!candle) return false;
      const mCandle = moment.utc(candle);
      if (from && mCandle.isBefore(from)) return false;
      if (to && mCandle.isAfter(to)) return false;
      return true;
    });
  }, [trades, fromDate, toDate]);

  const backendTrades = useMemo(() => {
    const backendSet = new Set(backendMachines.map(String));
    return filteredTrades.filter((t) => backendSet.has((t.machineid || t.machine_id || "").toString()));
  }, [filteredTrades, backendMachines]);

  const liveTrades = useMemo(() => {
    const liveSet = new Set(liveMachines.map(String));
    return filteredTrades.filter((t) => liveSet.has((t.machineid || t.machine_id || "").toString()));
  }, [filteredTrades, liveMachines]);

  const backendBySymbol = useMemo(() => {
    const map = new Map();
    backendTrades.forEach((t) => {
      const sym = (t.pair || t.symbol || t.PAIR || "").toString().trim().toUpperCase();
      if (!map.has(sym)) map.set(sym, []);
      map.get(sym).push(t);
    });
    map.forEach((list) => list.sort((a, b) => moment.utc(a.candel_time || a.candle_time).valueOf() - moment.utc(b.candel_time || b.candle_time).valueOf()));
    return map;
  }, [backendTrades]);

  const liveBySymbol = useMemo(() => {
    const map = new Map();
    liveTrades.forEach((t) => {
      const sym = (t.pair || t.symbol || t.PAIR || "").toString().trim().toUpperCase();
      if (!map.has(sym)) map.set(sym, []);
      map.get(sym).push(t);
    });
    map.forEach((list) => list.sort((a, b) => moment.utc(a.candel_time || a.candle_time).valueOf() - moment.utc(b.candel_time || b.candle_time).valueOf()));
    return map;
  }, [liveTrades]);

  const comparisons = useMemo(() => {
    const rows = [];
    const usedLive = new Set();

    backendBySymbol.forEach((backendList, sym) => {
      const liveList = liveBySymbol.get(sym) || [];
      backendList.forEach((backendTrade) => {
        let matchLive = null;
        let bestDiff = Infinity;
        liveList.forEach((liveTrade) => {
          if (usedLive.has(liveTrade)) return;
          const diffHours = Math.abs(
            moment.utc(backendTrade?.candel_time || backendTrade?.candle_time).diff(
              moment.utc(liveTrade?.candel_time || liveTrade?.candle_time),
              "hours",
              true
            )
          );
          if (diffHours <= 4 && diffHours < bestDiff) {
            bestDiff = diffHours;
            matchLive = liveTrade;
          }
        });

        if (matchLive) {
          usedLive.add(matchLive);
        }

        const backendTradeRef = backendTrade || null;
        const liveTradeRef = matchLive || null;

        const fetcherDiff = minutesDiff(getFetcherTime(backendTradeRef), getFetcherTime(liveTradeRef));
        const candleDiffHours =
          backendTradeRef && liveTradeRef
            ? Math.abs(
                moment.utc(backendTradeRef?.candel_time || backendTradeRef?.candle_time).diff(
                  moment.utc(liveTradeRef?.candel_time || liveTradeRef?.candle_time),
                  "hours",
                  true
                )
              )
            : null;
        const actionPriceBackend = getActionPrice(backendTradeRef);
        const actionPriceLive = getActionPrice(liveTradeRef);
        const priceDeltaPct = percentDiff(actionPriceBackend, actionPriceLive);
        const investmentDeltaPct = percentDiff(parseNumber(backendTradeRef?.investment), parseNumber(liveTradeRef?.investment));

        const backendStatus = statusFromCloseTime(backendTradeRef);
        const liveStatus = statusFromCloseTime(liveTradeRef);
        const backendClosePrice = getClosePrice(backendTradeRef);
        const liveClosePrice = getClosePrice(liveTradeRef);
        const closeTimeDiff =
          backendStatus === "closed" && liveStatus === "closed"
            ? minutesDiff(getCloseTime(backendTradeRef), getCloseTime(liveTradeRef))
            : null;
        const closePriceDelta =
          backendStatus === "closed" &&
          liveStatus === "closed" &&
          backendClosePrice !== null &&
          liveClosePrice !== null
            ? (() => {
                const denom = (Math.abs(liveClosePrice) + Math.abs(backendClosePrice)) / 2 || 1e-9;
                return Math.abs(liveClosePrice - backendClosePrice) / denom * 100;
              })()
            : null;

        const issues = [];
        if (candleDiffHours !== null && candleDiffHours > 4) {
          issues.push(`Candle gap ${candleDiffHours.toFixed(1)}h`);
        }
        if (fetcherDiff !== null && fetcherDiff > 5) {
          issues.push(`Late fetch (${fetcherDiff.toFixed(1)}m)`);
        }
        if (priceDeltaPct !== null && priceDeltaPct > 15) {
          issues.push(`Price gap ${priceDeltaPct.toFixed(1)}%`);
        }
        if (backendStatus === "closed" && liveStatus === "running") {
          issues.push("Backend closed, live running");
        }
        if (backendStatus === "running" && liveStatus === "closed") {
          issues.push("Backend running, live closed");
        }
        const livePl = parseNumber(liveTradeRef?.pl_after_comm);
        const backendPl = parseNumber(backendTradeRef?.pl_after_comm);
        if (closeTimeDiff !== null && closeTimeDiff > 16 && livePl !== null && backendPl !== null && livePl < backendPl) {
          issues.push(`Close time gap ${closeTimeDiff.toFixed(1)}m and live earned less`);
        }
        if (closePriceDelta !== null && closePriceDelta > 15 && livePl !== null && backendPl !== null && livePl < backendPl) {
          issues.push(`Close price gap ${closePriceDelta.toFixed(1)}% with worse P/L`);
        }
        if (investmentDeltaPct !== null && investmentDeltaPct > 0) {
          issues.push(`Investment gap ${investmentDeltaPct.toFixed(1)}%`);
        }

        rows.push({
          key: `${sym}__${backendTradeRef?.candel_time || backendTradeRef?.candle_time || "na"}__${liveTradeRef?.candel_time || liveTradeRef?.candle_time || "na"}`,
          backendList: backendTradeRef ? [backendTradeRef] : [],
          liveList: liveTradeRef ? [liveTradeRef] : [],
          backendTrade: backendTradeRef,
          liveTrade: liveTradeRef,
          fetcherDiff,
          priceDeltaPct,
          closeTimeDiff,
          closePriceDelta,
          investmentDeltaPct,
          backendStatus,
          liveStatus,
          issues
        });
      });
    });

    liveBySymbol.forEach((liveList, sym) => {
      liveList.forEach((liveTrade) => {
        if (usedLive.has(liveTrade)) return;
        rows.push({
          key: `${sym}__liveonly__${liveTrade?.candel_time || liveTrade?.candle_time || "na"}`,
          backendList: [],
          liveList: [liveTrade],
          backendTrade: null,
          liveTrade,
          fetcherDiff: null,
          priceDeltaPct: null,
          closeTimeDiff: null,
          closePriceDelta: null,
          investmentDeltaPct: null,
          backendStatus: "missing",
          liveStatus: statusFromCloseTime(liveTrade),
          issues: ["Extra in live"]
        });
      });
    });

    return rows;
  }, [backendBySymbol, liveBySymbol]);

  const [labelOrder, setLabelOrder] = useState(() => {
    try {
      const saved = localStorage.getItem("liveTradeView_unified_labels_order");
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  // Auto-fetch detail for each comparison so drop warnings can surface without expanding
  useEffect(() => {
    comparisons.forEach((row) => {
      if (!row.liveTrade) return;
      if (rowDetails[row.key]?.loaded || rowLoading[row.key]) return;
      fetchRowDetail(row);
    });
  }, [comparisons, fetchRowDetail]); // omit rowDetails/rowLoading to avoid re-run on every set

  const filteredComparisons = useMemo(() => {
    const base = showIssuesOnly ? comparisons.filter((row) => row.issues && row.issues.length) : comparisons;
    if (!quickFilters || quickFilters.length === 0) return base;
    const matches = (r, key) => {
      switch (key) {
        case "backendMissing":
          return r.liveList.length === 0;
        case "liveExtra":
          return r.backendList.length === 0;
        case "lateFetch":
          return Number.isFinite(r.fetcherDiff) && r.fetcherDiff > 5;
        case "priceGap":
          return Number.isFinite(r.priceDeltaPct) && r.priceDeltaPct > 15;
        case "closureMismatch":
          return (
            (r.backendStatus === "closed" && r.liveStatus === "running") ||
            (r.backendStatus === "running" && r.liveStatus === "closed")
          );
        case "closureGap":
          return (
            Number.isFinite(r.closeTimeDiff) &&
            r.closeTimeDiff > 16 &&
            Number.isFinite(r.closePriceDelta) &&
            r.closePriceDelta > 15
          );
        case "plDrop":
          return !!rowDetails[r.key]?.issue;
        case "neverProfit":
          return rowDetails[r.key]?.everPositive === false;
        case "totalBackend":
          return r.backendList.length > 0;
        case "totalLive":
          return r.liveList.length > 0;
        default:
          return false;
      }
    };
    return base.filter((r) => quickFilters.some((key) => matches(r, key)));
  }, [comparisons, showIssuesOnly, quickFilters, rowDetails]);

  const dropIssueCount = useMemo(
    () => comparisons.filter((row) => rowDetails[row.key]?.issue).length,
    [comparisons, rowDetails]
  );
  const neverProfitCount = useMemo(
    () => filteredComparisons.filter((row) => rowDetails[row.key]?.everPositive === false).length,
    [filteredComparisons, rowDetails]
  );
  const scannedCount = useMemo(
    () =>
      filteredComparisons.filter(
        (row) => rowDetails[row.key]?.loaded || rowDetails[row.key]?.error
      ).length,
    [filteredComparisons, rowDetails]
  );

  const sortedComparisons = useMemo(() => {
    const { key, direction } = sortConfig;
    const dir = direction === "asc" ? 1 : -1;
    const getVal = (row) => {
      switch (key) {
        case "symbol":
          return row.backendTrade?.pair || row.liveTrade?.pair || "";
        case "candle":
          return row.backendTrade?.candel_time || row.liveTrade?.candel_time || "";
        case "fetcher":
          return Number.isFinite(row.fetcherDiff) ? row.fetcherDiff : Infinity;
        case "price":
          return Number.isFinite(row.priceDeltaPct) ? row.priceDeltaPct : Infinity;
        case "investment":
          return Number.isFinite(row.investmentDeltaPct) ? row.investmentDeltaPct : Infinity;
        case "close":
          if (Number.isFinite(row.closeTimeDiff)) return row.closeTimeDiff;
          if (Number.isFinite(row.closePriceDelta)) return row.closePriceDelta;
          return Infinity;
        case "backend":
          return (row.backendList.map((t) => t.machineid).join(",") || "").toLowerCase();
        case "live":
          return (row.liveList.map((t) => t.machineid).join(",") || "").toLowerCase();
        case "action": {
          const ba = (row.backendTrade?.action || "").toLowerCase();
          const la = (row.liveTrade?.action || "").toLowerCase();
          return `${ba}-${la}`;
        }
        case "status":
          return `${row.backendStatus}-${row.liveStatus}`;
        case "drawdown": {
          const dd = rowDetails[row.key]?.issue?.dropPct;
          return Number.isFinite(dd) ? dd : Infinity;
        }
        case "issues":
          return row.issues ? row.issues.length : 0;
        default:
          return 0;
      }
    };
    return [...filteredComparisons].sort((a, b) => {
      const av = getVal(a);
      const bv = getVal(b);
      if (av < bv) return -1 * dir;
      if (av > bv) return 1 * dir;
      return 0;
    });
  }, [filteredComparisons, sortConfig, rowDetails]);

  const setSort = (key) => {
    setSortConfig((prev) => {
      if (prev.key === key) {
        return { key, direction: prev.direction === "asc" ? "desc" : "asc" };
      }
      return { key, direction: "asc" };
    });
  };

  const summary = useMemo(() => {
    const backendMissing = comparisons.filter((r) => r.liveList.length === 0).length;
    const liveExtra = comparisons.filter((r) => r.backendList.length === 0).length;
    const lateFetch = comparisons.filter((r) => r.fetcherDiff !== null && r.fetcherDiff > 5).length;
    const priceGap = comparisons.filter((r) => r.priceDeltaPct !== null && r.priceDeltaPct > 15).length;
    const closureMismatch = comparisons.filter(
      (r) =>
        (r.backendStatus === "closed" && r.liveStatus === "running") ||
        (r.backendStatus === "running" && r.liveStatus === "closed")
    ).length;
    const closureGap = comparisons.filter(
      (r) =>
        r.closeTimeDiff !== null &&
        r.closeTimeDiff > 16 &&
        r.closePriceDelta !== null &&
        r.closePriceDelta > 15
    ).length;
    const totalBackend = backendTrades.length;
    const totalLive = liveTrades.length;
    return { backendMissing, liveExtra, lateFetch, priceGap, closureMismatch, closureGap, totalBackend, totalLive };
  }, [comparisons, backendTrades, liveTrades]);

  // Totals of PL differences (live vs backend) for closed trades within the current filter scope
  const closeDeltaTotals = useMemo(() => {
    let profit = 0;
    let loss = 0;
    filteredComparisons.forEach((row) => {
      const livePl = parseNumber(row.liveTrade?.pl_after_comm);
      const backendPl = parseNumber(row.backendTrade?.pl_after_comm);
      const bothClosed = row.backendStatus === "closed" && row.liveStatus === "closed";
      if (!bothClosed || livePl === null || backendPl === null) return;
      const diff = livePl - backendPl;
      if (diff > 0) profit += diff;
      if (diff < 0) loss += Math.abs(diff);
    });
    return {
      profit,
      loss,
      net: profit - loss
    };
  }, [filteredComparisons]);

  const renderIssues = (issues) => {
    if (!issues || !issues.length) return <Badge tone="bg-green-100 text-green-800">OK</Badge>;
    return (
      <div className="flex flex-wrap gap-1">
        {issues.map((i, idx) => (
          <Badge key={idx} tone="bg-red-100 text-red-800">
            {i}
          </Badge>
        ))}
      </div>
    );
  };

  if (loading) {
    return <div className="p-6 text-center">Loading trades…</div>;
  }
  if (error) {
    return <div className="p-6 text-center text-red-600">{error}</div>;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#f5f6fa] dark:bg-black text-gray-900 dark:text-gray-100">
      <Sidebar isOpen={isSidebarOpen} toggleSidebar={() => setIsSidebarOpen((o) => !o)} />
      <div className={`flex-1 transition-all duration-300 ${isSidebarOpen ? "ml-64" : "ml-20"} h-full overflow-hidden`}>
        <div className="p-6 h-full flex flex-col space-y-6 overflow-hidden">
      <div className="space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div>
            <h1 className="text-2xl font-bold">Trade Compare</h1>
            <p className="text-sm text-gray-600 dark:text-gray-300">Backend (Assigned) vs Live by symbol + candle time</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <div className="px-4 py-2 rounded-lg bg-green-100 text-green-800 dark:bg-green-900/60 dark:text-green-100 border border-green-200 dark:border-green-700">
              <div className="text-xs uppercase tracking-wide">Total Profit Δ</div>
              <div className="text-xl font-bold">${closeDeltaTotals.profit.toFixed(2)}</div>
            </div>
            <div className="px-4 py-2 rounded-lg bg-red-100 text-red-800 dark:bg-red-900/60 dark:text-red-100 border border-red-200 dark:border-red-700">
              <div className="text-xs uppercase tracking-wide">Total Loss Δ</div>
              <div className="text-xl font-bold">${closeDeltaTotals.loss.toFixed(2)}</div>
            </div>
            <div className="px-4 py-2 rounded-lg bg-blue-100 text-blue-900 dark:bg-blue-900/60 dark:text-blue-100 border border-blue-200 dark:border-blue-700">
              <div className="text-xs uppercase tracking-wide">Net PL Δ</div>
              <div className="text-xl font-bold">${closeDeltaTotals.net.toFixed(2)}</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link
              to="/"
              className="px-3 py-2 rounded bg-gray-200 dark:bg-gray-800 text-black dark:text-white border border-gray-300 dark:border-gray-700 hover:bg-gray-300 dark:hover:bg-gray-700"
              title="Back to main dashboard"
            >
              ← Home
            </Link>
            <div className="flex items-center gap-1 text-sm">
              <button
                className="px-2 py-1 rounded bg-gray-200 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 hover:bg-gray-300 dark:hover:bg-gray-700"
                onClick={() => {
                  setFontScale((v) => {
                    const next = Math.max(0.6, v - 0.1);
                    localStorage.setItem("tc_font_scale", String(next));
                    return next;
                  });
                }}
                title="Decrease font size"
              >
                −
              </button>
              <span className="px-2">Font {fontScale.toFixed(1)}x</span>
              <button
                className="px-2 py-1 rounded bg-gray-200 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 hover:bg-gray-300 dark:hover:bg-gray-700"
                onClick={() => {
                  setFontScale((v) => {
                    const next = Math.min(2.0, v + 0.1);
                    localStorage.setItem("tc_font_scale", String(next));
                    return next;
                  });
                }}
                title="Increase font size"
              >
                +
              </button>
            </div>
            <button
              onClick={() => setDarkMode((d) => !d)}
              className="px-3 py-2 rounded bg-gray-200 dark:bg-gray-800 text-black dark:text-white border border-gray-300 dark:border-gray-700"
              title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
            >
              {darkMode ? "🌞 Light" : "🌙 Dark"}
            </button>
            <button
              onClick={fetchData}
              className="px-3 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
            >
              Refresh
            </button>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={showIssuesOnly}
                onChange={(e) => setShowIssuesOnly(e.target.checked)}
              />
              Show only issues
            </label>
          </div>
        </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-2 text-sm">
        <div className="col-span-1 md:col-span-2">
          <div className="border rounded bg-white dark:bg-gray-900 p-2 flex flex-col gap-2 text-xs">
            <div className="flex flex-wrap items-end gap-2">
              <label className="flex flex-col gap-1">
                <span className="font-semibold">From</span>
                <input
                  type="datetime-local"
                  value={fromDate ? moment.utc(fromDate).format("YYYY-MM-DDTHH:mm") : ""}
                  onChange={(e) => setFromDate(e.target.value ? moment.utc(e.target.value).toISOString() : "")}
                  className="h-8 border rounded px-2 bg-white text-black dark:bg-gray-800 dark:text-white dark:border-gray-700"
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="font-semibold">To</span>
                <input
                  type="datetime-local"
                  value={toDate ? moment.utc(toDate).format("YYYY-MM-DDTHH:mm") : ""}
                  onChange={(e) => setToDate(e.target.value ? moment.utc(e.target.value).toISOString() : "")}
                  className="h-8 border rounded px-2 bg-white text-black dark:bg-gray-800 dark:text-white dark:border-gray-700"
                />
              </label>
            </div>
            <div className="flex flex-wrap gap-2">
              <div className="flex-1 min-w-[180px]">
                <div className="font-semibold mb-1">Backend (Assigned)</div>
                <div className="flex flex-wrap gap-1 max-h-14 overflow-auto pr-1">
                  {machineOptions.map((id) => (
                    <label key={`b-${id}`} className="flex items-center gap-1 border px-2 py-1 rounded">
                      <input
                        type="checkbox"
                        checked={backendMachines.includes(id)}
                        onChange={(e) => {
                          setBackendMachines((prev) =>
                            e.target.checked ? [...prev, id] : prev.filter((x) => x !== id)
                          );
                        }}
                      />
                      {id}
                    </label>
                  ))}
                </div>
              </div>
              <div className="flex-1 min-w-[180px]">
                <div className="font-semibold mb-1">Live machines</div>
                <div className="flex flex-wrap gap-1 max-h-14 overflow-auto pr-1">
                  {machineOptions.map((id) => (
                    <label key={`l-${id}`} className="flex items-center gap-1 border px-2 py-1 rounded">
                      <input
                        type="checkbox"
                        checked={liveMachines.includes(id)}
                        onChange={(e) => {
                          setLiveMachines((prev) =>
                            e.target.checked ? [...prev, id] : prev.filter((x) => x !== id)
                          );
                        }}
                      />
                      {id}
                    </label>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
        <div className="col-span-1 md:col-span-2">
          <div className="grid grid-rows-2 grid-flow-col auto-cols-[200px] gap-2 overflow-x-auto pb-1">
            {[
              { key: "backendMissing", title: "Backend missing in live", value: summary.backendMissing },
              { key: "liveExtra", title: "Live extra vs backend", value: summary.liveExtra },
              { key: "totalBackend", title: "Total backend trades", value: summary.totalBackend },
              { key: "totalLive", title: "Total live trades", value: summary.totalLive },
              { key: "lateFetch", title: "Late fetch (>5m)", value: summary.lateFetch },
              { key: "priceGap", title: "Price gap (>15%)", value: summary.priceGap },
              { key: "closureMismatch", title: "Closure mismatch", value: summary.closureMismatch },
              { key: "closureGap", title: "Closure gap (time/price)", value: summary.closureGap },
              { key: "plDrop", title: "PL drop after $20 (>15%)", value: dropIssueCount },
              {
                key: "neverProfit",
                title: "Never in profit (scanned)",
                value: neverProfitCount,
                subtitle: `${scannedCount}/${filteredComparisons.length} scanned`
              }
            ].map((item, idx) => {
              const palette = [
                "bg-gradient-to-br from-cyan-500/80 via-sky-400/80 to-blue-500/80 text-white",
                "bg-gradient-to-br from-emerald-500/80 via-green-400/80 to-lime-500/80 text-white",
                "bg-gradient-to-br from-amber-500/80 via-orange-400/80 to-rose-500/80 text-white",
                "bg-gradient-to-br from-purple-500/80 via-fuchsia-500/80 to-pink-500/80 text-white",
                "bg-gradient-to-br from-slate-600/80 via-slate-500/80 to-gray-500/80 text-white"
              ];
              const tint = palette[idx % palette.length];
              const isActive = quickFilters.includes(item.key);
              return (
                <button
                  key={item.key}
                  onClick={() =>
                    setQuickFilters((prev) =>
                      prev.includes(item.key) ? prev.filter((k) => k !== item.key) : [...prev, item.key]
                    )
                  }
                  className={`text-left h-full w-full transition-all rounded-lg shadow-md ${
                    isActive
                      ? "ring-2 ring-white/70 dark:ring-cyan-300 scale-[1.01]"
                      : "hover:scale-[1.01] hover:ring-1 hover:ring-white/50 dark:hover:ring-cyan-200/70"
                  }`}
                >
                  <Card
                    title={item.title}
                    value={item.value}
                    subtitle={item.subtitle}
                    tint={isActive ? tint : `${tint} opacity-90`}
                  />
                </button>
              );
            })}
            <div className="flex items-center">
              <button onClick={() => setQuickFilters([])} className="text-sm text-blue-200 underline">
                Show all
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-end mb-2">
        <div className="flex items-center gap-1 text-sm">
          <button
            className="px-2 py-1 rounded bg-gray-200 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 hover:bg-gray-300 dark:hover:bg-gray-700"
            onClick={() => {
              setFontScale((v) => {
                const next = Math.max(0.6, v - 0.1);
                localStorage.setItem("tc_font_scale", String(next));
                return next;
              });
            }}
            title="Decrease font size"
          >
            −
          </button>
          <span className="px-2">Font {fontScale.toFixed(1)}x</span>
          <button
            className="px-2 py-1 rounded bg-gray-200 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 hover:bg-gray-300 dark:hover:bg-gray-700"
            onClick={() => {
              setFontScale((v) => {
                const next = Math.min(2.0, v + 0.1);
                localStorage.setItem("tc_font_scale", String(next));
                return next;
              });
            }}
            title="Increase font size"
          >
            +
          </button>
        </div>
      </div>
      </div>
      <div className="flex-1 overflow-hidden">
      <div className="border rounded-lg h-full" style={{ fontSize: `${fontScale}rem` }}>
        <div className="overflow-auto h-full">
        <table className="min-w-[1400px]" style={{ fontSize: "inherit" }}>
          <thead className="bg-gray-100 dark:bg-gray-800">
            <tr>
                  <th className="px-3 py-2 text-left">
                    <button className="flex items-center gap-1" onClick={() => setSort("symbol")}>
                      Symbol {sortConfig.key === "symbol" ? (sortConfig.direction === "asc" ? "▲" : "▼") : ""}
                    </button>
                  </th>
                  <th className="px-3 py-2 text-left">Unique ID</th>
                  <th className="px-3 py-2 text-left">
                    <button className="flex items-center gap-1" onClick={() => setSort("candle")}>
                      Candle Time {sortConfig.key === "candle" ? (sortConfig.direction === "asc" ? "▲" : "▼") : ""}
                    </button>
                  </th>
                  <th className="px-3 py-2 text-left">
                    <button className="flex items-center gap-1" onClick={() => setSort("backend")}>
                      Backend {sortConfig.key === "backend" ? (sortConfig.direction === "asc" ? "▲" : "▼") : ""}
                    </button>
                  </th>
                  <th className="px-3 py-2 text-left">
                    <button className="flex items-center gap-1" onClick={() => setSort("live")}>
                      Live {sortConfig.key === "live" ? (sortConfig.direction === "asc" ? "▲" : "▼") : ""}
                    </button>
                  </th>
                  <th className="px-3 py-2 text-left">
                    <button className="flex items-center gap-1" onClick={() => setSort("action")}>
                      Action {sortConfig.key === "action" ? (sortConfig.direction === "asc" ? "▲" : "▼") : ""}
                    </button>
                  </th>
                  <th className="px-3 py-2 text-left">
                    <button className="flex items-center gap-1" onClick={() => setSort("fetcher")}>
                      Fetcher Δ {sortConfig.key === "fetcher" ? (sortConfig.direction === "asc" ? "▲" : "▼") : ""}
                    </button>
                  </th>
                  <th className="px-3 py-2 text-left">
                    <button className="flex items-center gap-1" onClick={() => setSort("price")}>
                      Price Δ% {sortConfig.key === "price" ? (sortConfig.direction === "asc" ? "▲" : "▼") : ""}
                    </button>
                  </th>
                  <th className="px-3 py-2 text-left">
                    <button className="flex items-center gap-1" onClick={() => setSort("investment")}>
                      Invest Δ% {sortConfig.key === "investment" ? (sortConfig.direction === "asc" ? "▲" : "▼") : ""}
                    </button>
                  </th>
                  <th className="px-3 py-2 text-left">
                    <button className="flex items-center gap-1" onClick={() => setSort("status")}>
                      Status {sortConfig.key === "status" ? (sortConfig.direction === "asc" ? "▲" : "▼") : ""}
                    </button>
                  </th>
                  <th className="px-3 py-2 text-left">
                    <button className="flex items-center gap-1" onClick={() => setSort("close")}>
                      Close Δ {sortConfig.key === "close" ? (sortConfig.direction === "asc" ? "▲" : "▼") : ""}
                    </button>
                  </th>
                  <th className="px-3 py-2 text-left">
                    <button className="flex items-center gap-1" onClick={() => setSort("drawdown")}>
                      Closing issue {sortConfig.key === "drawdown" ? (sortConfig.direction === "asc" ? "▲" : "▼") : ""}
                    </button>
                  </th>
                  <th className="px-3 py-2 text-left">
                    <button className="flex items-center gap-1" onClick={() => setSort("issues")}>
                      Issues {sortConfig.key === "issues" ? (sortConfig.direction === "asc" ? "▲" : "▼") : ""}
                    </button>
                  </th>
                  <th className="px-3 py-2 text-left">Compare</th>
                </tr>
              </thead>
              <tbody>
            {filteredComparisons.length === 0 && (
              <tr>
                  <td colSpan={13} className="px-3 py-4 text-center text-gray-500">
                      No trades in range
                    </td>
                  </tr>
                )}
            {sortedComparisons.map((row) => {
              const symbol = row.backendTrade?.pair || row.liveTrade?.pair || "N/A";
              const candle = row.backendTrade?.candel_time || row.liveTrade?.candel_time || "N/A";
              const interval = getInterval(row.backendTrade) || getInterval(row.liveTrade);
              const binanceUrl = buildBinanceUrl(symbol, interval);
              const fetcherCell = Number.isFinite(row.fetcherDiff)
                ? `${row.fetcherDiff.toFixed(1)}m`
                : "—";
              const priceCell = Number.isFinite(row.priceDeltaPct)
                ? `${row.priceDeltaPct.toFixed(1)}%`
                : "—";
              const priceClass = severityTint(row.priceDeltaPct);
              const investmentCell = Number.isFinite(row.investmentDeltaPct)
                ? `${row.investmentDeltaPct.toFixed(1)}%`
                : "—";
              const investmentClass = severityTint(row.investmentDeltaPct);
              const livePl = parseNumber(row.liveTrade?.pl_after_comm);
              const backendPl = parseNumber(row.backendTrade?.pl_after_comm);
              const liveClosePrice = getClosePrice(row.liveTrade);
              const backendClosePrice = getClosePrice(row.backendTrade);
              const plDiff = livePl !== null && backendPl !== null ? livePl - backendPl : null;
              const plDiffPct =
                livePl !== null && backendPl !== null && backendPl !== 0
                  ? ((livePl - backendPl) / Math.abs(backendPl)) * 100
                  : null;

              const bothClosed = row.backendStatus === "closed" && row.liveStatus === "closed";
              const backendCloseTime = getCloseTime(row.backendTrade);
              const liveCloseTime = getCloseTime(row.liveTrade);
              const timeLabel = (() => {
                if (bothClosed && Number.isFinite(row.closeTimeDiff)) return `${row.closeTimeDiff.toFixed(1)}m`;
                const parts = [];
                if (backendCloseTime) parts.push(`B:${backendCloseTime}`);
                if (liveCloseTime) parts.push(`L:${liveCloseTime}`);
                return parts.length ? parts.join(" | ") : "—";
              })();
              const priceLabel = (() => {
                if (bothClosed && Number.isFinite(row.closePriceDelta)) return `${row.closePriceDelta.toFixed(1)}%`;
                const parts = [];
                if (Number.isFinite(backendClosePrice)) parts.push(`B:${backendClosePrice.toFixed(2)}`);
                if (Number.isFinite(liveClosePrice)) parts.push(`L:${liveClosePrice.toFixed(2)}`);
                return parts.length ? parts.join(" / ") : "—";
              })();
              const plContent = (() => {
                const parts = [];
                if (backendPl !== null) parts.push(`B:${backendPl.toFixed(2)}`);
                if (livePl !== null) parts.push(`L:${livePl.toFixed(2)}`);
                const deltaLine =
                  plDiff !== null ? (
                    <div className="font-bold text-sm">
                      Δ ${plDiff.toFixed(2)} {plDiffPct !== null ? `(${plDiffPct.toFixed(1)}%)` : ""}
                    </div>
                  ) : null;
                if (parts.length === 0 && !deltaLine) return <div>PL: —</div>;
                return (
                  <div className="leading-tight">
                    {parts.length ? <div>{parts.join(" / ")}</div> : null}
                    {deltaLine}
                  </div>
                );
              })();

              const closeCell = (
                <div className="space-y-0.5 text-xs">
                  <div>Time: {timeLabel}</div>
                  <div>Price: {priceLabel}</div>
                  <div>{plContent}</div>
                  {!bothClosed && <div className="text-gray-500">Pending (running)</div>}
                </div>
              );

              const closeClass = (() => {
                if (!bothClosed) return "";
                if (plDiff !== null) {
                  if (plDiff > 0) return "bg-green-200 text-green-900";
                  if (plDiff < 0) return "bg-red-200 text-red-900";
                }
                return severityTint(row.closePriceDelta);
              })();
              return (
                <React.Fragment key={row.key}>
                  <tr
                    className={`border-t border-gray-200 dark:border-gray-800 cursor-pointer transition-colors ${
                      selectedRow === row.key
                        ? "bg-yellow-100 dark:bg-yellow-900"
                        : "hover:bg-gray-100 dark:hover:bg-gray-800"
                    }`}
                    onClick={() => {
                      setSelectedRow(row.key);
                      if (compareRow === row.key) setCompareRow(null);
                    }}
                    onDoubleClick={() => {
                      const next = expandedRow === row.key ? null : row.key;
                      setExpandedRow(next);
                      if (next) fetchRowDetail(row);
                    }}
                  >
                    <td className="px-3 py-2 font-semibold">
                      <div className="flex items-center gap-2">
                        {binanceUrl ? (
                          <a
                            href={binanceUrl}
                            target="_blank"
                            rel="noreferrer"
                            className="text-blue-600 dark:text-cyan-300 underline"
                            onClick={(e) => e.stopPropagation()}
                            title={`Open ${symbol} on Binance (${toBinanceInterval(interval)})`}
                          >
                            {symbol}
                          </a>
                        ) : (
                          <span>{symbol}</span>
                        )}
                        <button
                          className="text-xs px-2 py-1 rounded bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigator.clipboard.writeText(symbol || "");
                            setCopiedSymbol(symbol || "");
                            setTimeout(() => setCopiedSymbol(null), 1200);
                          }}
                          title="Copy symbol"
                        >
                          {copiedSymbol === symbol ? "✅" : "📋"}
                        </button>
                      </div>
                    </td>
                    <td className="px-3 py-2">
                      {row.liveTrade?.unique_id || row.backendTrade?.unique_id ? (
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            data-uid-link
                            className="underline text-blue-600 dark:text-blue-300"
                            onClick={(e) => {
                              e.stopPropagation();
                              const uid = row.liveTrade?.unique_id || row.backendTrade?.unique_id || "";
                              if (uid) navigate(`/live-trade-view?uid=${encodeURIComponent(uid)}`);
                            }}
                          >
                            {row.liveTrade?.unique_id || row.backendTrade?.unique_id}
                          </button>
                          <button
                            className="text-xs px-2 py-1 rounded bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600"
                            onClick={(e) => {
                              e.stopPropagation();
                              const uid = row.liveTrade?.unique_id || row.backendTrade?.unique_id || "";
                              navigator.clipboard.writeText(uid);
                              setCopiedUid(uid);
                              setTimeout(() => setCopiedUid(null), 1200);
                            }}
                            title="Copy UID"
                          >
                            {copiedUid === (row.liveTrade?.unique_id || row.backendTrade?.unique_id) ? "✅" : "📋"}
                          </button>
                        </div>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td className="px-3 py-2">{candle}</td>
                    <td className="px-3 py-2">
                      <div className="text-xs text-gray-700 dark:text-gray-200">Machines: {row.backendList.map((t) => t.machineid).join(", ") || "—"}</div>
                      <div className="text-xs">Status: {row.backendStatus}</div>
                      <div className="text-xs">Fetcher: {getFetcherTime(row.backendTrade) || "—"}</div>
                      <div className="text-xs">Price: {getActionPrice(row.backendTrade) ?? "—"}</div>
                    </td>
                    <td className="px-3 py-2">
                      <div className="text-xs text-gray-700 dark:text-gray-200">Machines: {row.liveList.map((t) => t.machineid).join(", ") || "—"}</div>
                      <div className="text-xs">Status: {row.liveStatus}</div>
                      <div className="text-xs">Fetcher: {getFetcherTime(row.liveTrade) || "—"}</div>
                      <div className="text-xs">Price: {getActionPrice(row.liveTrade) ?? "—"}</div>
                    </td>
                    <td className="px-3 py-2">
                      <div>Backend: {row.backendTrade?.action || "—"}</div>
                      <div>Live: {row.liveTrade?.action || "—"}</div>
                    </td>
                    <td className="px-3 py-2">{fetcherCell}</td>
                    <td className={`px-3 py-2 ${priceClass}`}>{priceCell}</td>
                    <td className={`px-3 py-2 ${investmentClass}`}>{investmentCell}</td>
                    <td className="px-3 py-2">
                      <div>Backend: {row.backendStatus}</div>
                      <div>Live: {row.liveStatus}</div>
                    </td>
                  <td className={`px-3 py-2 ${closeClass}`}>{closeCell}</td>
                  <td className="px-3 py-2 text-xs">
                    {rowDetails[row.key]?.loading && <span className="text-gray-500">Scanning…</span>}
                    {!rowDetails[row.key]?.loading && rowDetails[row.key]?.issue && (
                      <span className="text-red-500 font-semibold">
                        ⚠️ Dropped {(rowDetails[row.key].issue.dropPct || 0).toFixed(1)}% from peak $
                        {rowDetails[row.key].issue.peak?.toFixed(2)} at {rowDetails[row.key].issue.at}
                      </span>
                    )}
                    {!rowDetails[row.key]?.loading && !rowDetails[row.key]?.issue && rowDetails[row.key]?.recovered && (
                      <span className="text-green-500 font-semibold">
                        ✅ Recovered to ${rowDetails[row.key].recovered.peak?.toFixed(2)} at {rowDetails[row.key].recovered.at}
                      </span>
                    )}
                    {!rowDetails[row.key]?.loading && !rowDetails[row.key]?.issue && !rowDetails[row.key]?.recovered && (
                      <span className="text-green-500">OK</span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex flex-col gap-1">
                      {renderIssues(row.issues)}
                    </div>
                  </td>
                  <td className="px-3 py-2">
                    <button
                      className="px-2 py-1 rounded bg-gray-200 dark:bg-gray-800 hover:bg-gray-300 dark:hover:bg-gray-700"
                      onClick={(e) => {
                        e.stopPropagation();
                        setCompareRow((prev) => (prev === row.key ? null : row.key));
                        if (!rowDetails[row.key]) fetchRowDetail(row);
                      }}
                    >
                      {compareRow === row.key ? "Hide" : "Compare"}
                    </button>
                  </td>
                  </tr>
                  {expandedRow === row.key && (
                    <tr className="border-t border-gray-100 dark:border-gray-800">
                      <td colSpan={13} className="px-0 py-0">
                        <div className="bg-gray-50 dark:bg-gray-900 p-4">
                          <div className="max-h-[50vh] overflow-auto" style={{ fontSize: `${fontScale}rem` }}>
                            {rowLoading[row.key] && <div>Loading trade history…</div>}
                            {!rowLoading[row.key] && rowDetails[row.key]?.error && (
                              <div className="text-red-500 text-sm">{rowDetails[row.key].error}</div>
                            )}
                            {!rowLoading[row.key] && rowDetails[row.key]?.logs && (() => {
                              const logs = rowDetails[row.key].logs;
                              const isColVisible = (col) => {
                                if (col.type === "json") {
                                  if (!activeJsonLabels) return false;
                                  const active = activeJsonLabels[col.value];
                                  if (!active) return false;
                                  if (col.interval) return !!active[col.interval];
                                  return Object.values(active).some(Boolean) || active === true;
                                }
                                if (Array.isArray(activeRegularLabels) && activeRegularLabels.length) {
                                  return activeRegularLabels.includes(col.value);
                                }
                                return true;
                              };

                              const inferredOrderRaw =
                                Array.isArray(labelOrder) && labelOrder.length
                                  ? labelOrder
                                  : (logs[0]?.json ? Object.keys(logs[0].json) : []);
                              const columns = (inferredOrderRaw && inferredOrderRaw.length ? inferredOrderRaw : Object.keys(logs[0]?.json || []))
                                .map((item) => {
                                  if (typeof item === "string") {
                                    return { header: item, key: item, type: "regular", value: item };
                                  }
                                  if (item && typeof item === "object") {
                                    return {
                                      header: item.label || item.value || JSON.stringify(item),
                                      key: item.value || item.label || JSON.stringify(item),
                                      type: item.type || item.kind || "regular",
                                      value: item.value || item.label || JSON.stringify(item),
                                      interval: item.interval
                                    };
                                  }
                                  return { header: String(item), key: String(item), type: "regular", value: String(item) };
                                })
                                .filter(isColVisible);
                              return (
                                <div className="space-y-2">
                                  {rowDetails[row.key].issue && (
                                    <div className="text-sm text-red-500 font-semibold">
                                      ⚠️ Dropped {(rowDetails[row.key].issue.dropPct || 0).toFixed(1)}% from peak $
                                      {rowDetails[row.key].issue.peak?.toFixed(2)} at {rowDetails[row.key].issue.at}
                                    </div>
                                  )}
                                  <table className="min-w-full text-xs" style={{ fontSize: "inherit" }}>
                                    <thead className="bg-gray-200 dark:bg-gray-800 sticky top-0">
                                      <tr>
                                        <th className="px-2 py-1">
                                          <button
                                            className="flex items-center gap-1"
                                            onClick={() =>
                                              setDetailSort((prev) => ({
                                                key: "ts",
                                                direction: prev.key === "ts" && prev.direction === "asc" ? "desc" : "asc"
                                              }))
                                            }
                                          >
                                            Timestamp {detailSort.key === "ts" ? (detailSort.direction === "asc" ? "▲" : "▼") : ""}
                                          </button>
                                        </th>
                                        {columns.map((col, cidx) => (
                                          <th key={`${col.header}-${cidx}`} className="px-2 py-1 text-left">
                                            <button
                                              className="flex items-center gap-1"
                                              onClick={() =>
                                                setDetailSort((prev) => ({
                                                  key: col.key,
                                                  direction: prev.key === col.key && prev.direction === "asc" ? "desc" : "asc"
                                                }))
                                              }
                                            >
                                              {col.header} {detailSort.key === col.key ? (detailSort.direction === "asc" ? "▲" : "▼") : ""}
                                            </button>
                                          </th>
                                        ))}
                                      </tr>
                                    </thead>
                                    <tbody>
                                      {logs
                                        .slice()
                                        .sort((a, b) => {
                                          const dir = detailSort.direction === "asc" ? 1 : -1;
                                          const key = detailSort.key;
                                          if (key === "ts") {
                                            const ma = moment(a.ts || a.raw?.timestamp);
                                            const mb = moment(b.ts || b.raw?.timestamp);
                                            if (!ma.isValid() || !mb.isValid()) return 0;
                                            return ma.valueOf() === mb.valueOf() ? 0 : ma.valueOf() > mb.valueOf() ? dir : -dir;
                                          }
                                          const va = a.json ? a.json[key] : undefined;
                                          const vb = b.json ? b.json[key] : undefined;
                                          if (va === vb) return 0;
                                          return va > vb ? dir : -dir;
                                        })
                                        .map((log, idx) => (
                                        <tr key={idx} className="border-t border-gray-200 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors cursor-pointer">
                                          <td className="px-2 py-1 whitespace-nowrap">{log.ts || log.raw?.timestamp || "—"}</td>
                                          {columns.map((col, cidx) => {
                                            const keyName = col.key;
                                            const val =
                                              log.json && Object.prototype.hasOwnProperty.call(log.json, keyName)
                                                ? log.json[keyName]
                                                : "";
                                            const display =
                                              val === null || val === undefined
                                                ? ""
                                                : typeof val === "object"
                                                ? JSON.stringify(val)
                                                : String(val);
                                            return (
                                              <td key={`${keyName}-${cidx}`} className="px-2 py-1 whitespace-nowrap hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
                                                {display}
                                              </td>
                                            );
                                          })}
                                        </tr>
                                      ))}
                                    </tbody>
                                  </table>
                                </div>
                              );
                            })()}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                {compareRow === row.key && (
                  <tr className="border-t border-gray-100 dark:border-gray-800">
                    <td colSpan={13} className="px-4 py-3 bg-gray-50 dark:bg-gray-900">
                      {(() => {
                        const columnOrderRaw = localStorage.getItem("tableColumnOrder_global");
                        const columns = columnOrderRaw ? JSON.parse(columnOrderRaw) : null;
                        const order = Array.isArray(columns) && columns.length ? columns : Object.keys(row.liveTrade || row.backendTrade || {});
                        return (
                          <div
                            className="overflow-auto max-h-[50vh] border rounded bg-gray-900 text-white dark:bg-white dark:text-black"
                            style={{ fontSize: `${fontScale}rem` }}
                          >
                            <table className="min-w-[1200px] text-xs">
                              <thead className="sticky top-0 bg-gray-800 text-white dark:bg-gray-200 dark:text-black">
                                <tr>
                                  <th className="px-2 py-1 text-left">Side</th>
                    {order.map((col) => (
                      <th key={col} className="px-2 py-1 text-left">{col}</th>
                    ))}
                  </tr>
                </thead>
                              <tbody>
                                {[
                                  { title: "Backend", trade: row.backendTrade },
                                  { title: "Live", trade: row.liveTrade }
                                ].map(({ title, trade }) => (
                                  <tr
                                    key={title}
                                    className="border-t border-gray-700 dark:border-gray-200 bg-gray-900 text-white dark:bg-white dark:text-black hover:bg-gray-700 dark:hover:bg-gray-100 transition-colors"
                                  >
                                    <td className="px-2 py-1 font-semibold">{title}</td>
                                    {order.map((col) => (
                                      <td key={col} className="px-2 py-1 whitespace-nowrap">
                                        {valueForColumn(col, trade)}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        );
                      })()}
                    </td>
                  </tr>
                )}
              </React.Fragment>
            );
            })}
          </tbody>
        </table>
        </div>
      </div>
      </div>
    </div>
  </div>
  </div>
  );
};

export default TradeComparePage;
