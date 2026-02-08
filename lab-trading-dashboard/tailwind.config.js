module.exports = {
  darkMode: 'class',
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        sidebarGradientStart: "#1E3A8A",
        sidebarGradientEnd: "#1E40AF",
        sidebarHover: "#374151",
        activeLink: "#F59E0B",
      },
      backgroundImage: {
        sidebarGradient: "linear-gradient(to bottom, #1E3A8A, #1E40AF)",
      },
    },
  },
  plugins: [],
};