"use strict";

// Loaded without defer so the theme is set before first paint.
(() => {
  const system = matchMedia("(prefers-color-scheme: dark)");
  const stored = () => {
    try {
      return localStorage.getItem("theme");
    } catch {
      return null;
    }
  };
  const apply = () => {
    const theme = stored();
    const dark = theme === "dark" || (theme !== "light" && system.matches);
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", dark ? "#05060a" : "#eef1f8");
    document.dispatchEvent(new Event("themechange"));
  };
  apply();
  system.addEventListener("change", apply);
  addEventListener("storage", (event) => event.key === "theme" && apply());
})();
