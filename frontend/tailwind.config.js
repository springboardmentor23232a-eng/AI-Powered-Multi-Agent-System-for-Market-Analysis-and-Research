/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: { extend: { colors: { brand: { 50: "#eef4ff", 100: "#dbe7ff", 500: "#2f5fe0", 600: "#244bbd", 700: "#1d3b95" } } } },
  plugins: [],
};
