import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        forest: {
          900: "#0e2219",
          800: "#143026",
          700: "#1b3a2f",
          600: "#27503f",
          500: "#356350",
          400: "#5a8873",
        },
        ivory: {
          50: "#faf7ef",
          100: "#f5f0e3",
          200: "#ebe3cf",
        },
        stone: {
          warm: "#8a8374",
          deep: "#4a463d",
        },
        accent: {
          clay: "#b4703e",
          gold: "#c79a4b",
        },
      },
      fontFamily: {
        serif: ["var(--font-serif)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        soft: "0 6px 30px -12px rgba(14, 34, 25, 0.25)",
      },
    },
  },
  plugins: [],
};

export default config;
