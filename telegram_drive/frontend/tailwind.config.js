/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Keep existing utility names while applying the FLOW accent palette.
        blue: {
          50: "#eefbf6",
          100: "#d8f5e9",
          200: "#b1ead5",
          300: "#7dd9b8",
          400: "#45bd95",
          500: "#109870",
          600: "#0d7d5d",
          700: "#0b654c",
          800: "#0c503f",
          900: "#0b4235",
          950: "#05251e",
        },
      },
    },
  },
  plugins: [],
};
