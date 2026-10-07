import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        tg: {
          bg: "var(--tg-theme-bg-color, #0f172a)",
          text: "var(--tg-theme-text-color, #f8fafc)",
          hint: "var(--tg-theme-hint-color, #94a3b8)",
          link: "var(--tg-theme-link-color, #38bdf8)",
          button: "var(--tg-theme-button-color, #2563eb)",
          buttonText: "var(--tg-theme-button-text-color, #ffffff)",
          secondaryBg: "var(--tg-theme-secondary-bg-color, #1e293b)",
        },
        sat: {
          navy: "#0a192f",
          blue: "#2563eb",
          cyan: "#06b6d4",
          gold: "#f59e0b",
          green: "#10b981",
          card: "#1e293b",
          border: "#334155",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
