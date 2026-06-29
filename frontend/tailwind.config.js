/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#13182B",
        inkdeep: "#0B0E1C",
        parchment: "#F6F1E7",
        parchmentdark: "#EBE2D0",
        brass: "#C9A24B",
        brassdark: "#A9803A",
        sage: "#5E8C6A",
        rust: "#A1503D",
        slate: "#3A3F4B",
      },
      fontFamily: {
        display: ["Fraunces", "serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      boxShadow: {
        seal: "0 8px 24px rgba(169, 128, 58, 0.35)",
        card: "0 2px 8px rgba(19,24,43,0.06), 0 12px 32px rgba(19,24,43,0.08)",
      },
      backgroundImage: {
        grain: "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.04'/%3E%3C/svg%3E\")",
      },
    },
  },
  plugins: [],
};
