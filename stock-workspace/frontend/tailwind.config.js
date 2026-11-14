export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: { extend: { keyframes: { pop: { from: { opacity: 0, transform: "translateY(8px)" }, to: { opacity: 1, transform: "none" } } },
                     animation: { pop: "pop .25s ease-out" } } },
};
