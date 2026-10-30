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
  let preference = stored();
  const apply = () => {
    const theme = preference;
    const dark = theme === "dark" || (theme !== "light" && system.matches);
    document.documentElement.dataset.theme = dark ? "dark" : "light";
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", dark ? "#151515" : "#fcfbfa");
    document.dispatchEvent(new Event("themechange"));
  };
  window.YourTurnTheme = {
    preference: () => preference === "light" || preference === "dark" ? preference : "system",
    set: (value) => {
      preference = value === "light" || value === "dark" ? value : null;
      let saved = true;
      try {
        if (preference) localStorage.setItem("theme", preference);
        else localStorage.removeItem("theme");
      } catch { saved = false; }
      apply();
      return saved;
    },
  };
  apply();
  system.addEventListener("change", apply);
  addEventListener("storage", (event) => {
    if (event.key === "theme" || event.key === null) { preference = stored(); apply(); }
  });
})();
