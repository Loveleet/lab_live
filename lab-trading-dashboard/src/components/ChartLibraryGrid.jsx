useEffect(() => {
  const script = document.createElement("script");
  script.src = "/charting_library/charting_library.standalone.js";
  script.onload = () => {
    initCharts(); // call your init logic
  };
  document.body.appendChild(script);
}, []);

const initCharts = () => {
  symbols.forEach((symbol, idx) => {
    const containerId = `tv_chart_${idx}`;
    if (window.TradingView) {
      new window.TradingView.widget({
        autosize: true,
        symbol: symbol,
        interval: "15",
        container_id: containerId,
        library_path: "/charting_library/",
        locale: "en",
        theme: "Dark",
        style: "1",
        timezone: "Asia/Kolkata",
        toolbar_bg: "#1e222d",
        hide_side_toolbar: false,
        allow_symbol_change: false,
        studies_overrides: {},
      });
    }
  });
};