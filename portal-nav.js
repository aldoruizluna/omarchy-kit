// Shared navigation for every Omarchy Kit page. Renders into <div id="top"></div> and follows the page's
// language (it watches <html lang>, which every page sets when its EN/ES toggle is used). kit.js fills the
// search button and XP chip it leaves on the right.
(function () {
  var PAGES = [
    ["index.html", "/", "Start", "Inicio", "home"],
    ["learn.html", "/learn", "Learn", "Aprender", "learn"],
    ["mac.html", "/mac", "From macOS", "Desde macOS", "mac"],
    ["macbook.html", "/macbook", "Your MacBook", "Tu MacBook", "laptop"],
    ["system.html", "/system", "System", "Sistema", "pulse"],
    ["games.html", "/games", "Games", "Juegos", "pad"],
    ["keyboard.html", "/keyboard", "Keyboard", "Teclado", "keys"],
    ["trackpad.html", "/trackpad", "Trackpad", "Trackpad", "touch"],
    ["reference.html", "/reference", "Reference", "Referencia", "book"],
    ["cheatsheet.html", "/cheatsheet", "Cheat sheet", "Guía rápida", "bolt"],
    ["apps.html", "/apps", "Apps", "Apps", "grid"],
    ["setup.html", "/setup", "Setup log", "Bitácora", "check"]
  ];
  // 24×24 stroke icons (drawn for this kit)
  var P = {
    home: "M3 11 12 4l9 7M5 10v10h5v-6h4v6h5V10",
    learn: "M2 9l10-5 10 5-10 5zM6 11v5c3 2.5 9 2.5 12 0v-5M22 9v6",
    mac: "M15 4c-1.5 0-3 1.2-3 3 1.6 0 3-1.3 3-3zM12 8c-2-1.2-6-.8-6 4 0 4 2.5 8 4 8 1 0 1.3-.6 2-.6s1 .6 2 .6c1.4 0 3-2.5 3.6-4.5-2.6-1.1-2.7-4.8-.2-6.1C16.2 7.6 13.6 7.4 12 8z",
    laptop: "M5 6h14v9H5zM2 19h20l-2-4H4z",
    pulse: "M2 12h4l3-7 4 14 3-7h6",
    keys: "M3 6h18v12H3zM7 10h.01M11 10h.01M15 10h.01M7 14h10",
    touch: "M4 5h16v14H4zM4 15h16M12 15v4",
    pad: "M7 8h10a5 5 0 0 1 4.6 7l-1 2.3a2.5 2.5 0 0 1-4.2.5L15 16H9l-1.4 1.8a2.5 2.5 0 0 1-4.2-.5l-1-2.3A5 5 0 0 1 7 8zM8 11v3M6.5 12.5h3M15.5 12h.01M17.5 13.5h.01",
    book: "M4 4h11a3 3 0 0 1 3 3v13H7a3 3 0 0 1-3-3zM4 17a3 3 0 0 1 3-3h11",
    bolt: "M13 2 4 14h7l-1 8 9-12h-7z",
    grid: "M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z",
    check: "M9 4h6v3H9zM6 6H5v15h14V6h-1M8.5 14l2.5 2.5 4.5-5"
  };
  function icon(n) { return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="' + P[n] + '"/></svg>'; }
  window.KitNav = { pages: PAGES, icon: icon };
  function render() {
    var el = document.getElementById("top"); if (!el) return;
    var file = location.protocol === "file:", es = (document.documentElement.lang || "en").slice(0, 2) === "es";
    var here = location.pathname.replace(/\/$/, "") || "/";
    el.className = "kit-bar";
    var nav = PAGES.map(function (p) {
      var href = file ? p[0] : p[1];
      var on = file ? location.pathname.endsWith("/" + p[0]) || (p[0] === "index.html" && /\/$/.test(location.pathname))
                    : (here === p[1] || here === "/" + p[0] || (p[1] === "/" && here === "/index.html"));
      return '<a href="' + href + '"' + (on ? ' aria-current="page"' : "") + ">" + icon(p[4]) + (es ? p[3] : p[2]) + "</a>";
    }).join("");
    var tools = '<div class="kit-tools">' +
      '<button class="kit-search" type="button" data-kit-palette title="' + (es ? "Buscar en todo" : "Search everything") + '">' +
      '<svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>' +
      '<span class="lbl">' + (es ? "Buscar" : "Search") + '</span><kbd>Ctrl K</kbd></button>' +
      '<a class="kit-xp" id="kitXp" href="' + (file ? "index.html" : "/") + '#progress" hidden></a></div>';
    // tools sit in the page header next to the language button, so the nav gets the full width
    var lang = document.getElementById("bLang"), old = document.querySelector(".kit-tools");
    if (old) old.remove();
    el.innerHTML = '<nav class="kit-nav" aria-label="Omarchy Kit">' + nav + '</nav>' + (lang ? "" : tools);
    var anchor = lang; // the header's own child that holds the language button
    while (anchor && anchor.parentElement && anchor.parentElement.tagName !== "HEADER") anchor = anchor.parentElement;
    if (lang) (anchor && anchor.parentElement ? anchor : lang).insertAdjacentHTML("beforebegin", tools);
    document.dispatchEvent(new CustomEvent("kit:nav"));
  }
  var css = document.createElement("style");
  css.textContent = ".kit-nav{display:flex;flex-wrap:wrap;gap:4px 14px;margin:10px 0 0;font-weight:600;font-size:.93rem}" +
    ".kit-nav a{color:var(--acc);text-decoration:none;padding:2px 0;border-bottom:2px solid transparent}" +
    ".kit-nav a:hover{border-bottom-color:color-mix(in srgb,var(--acc) 40%,transparent)}" +
    ".kit-nav a[aria-current=page]{color:var(--fg);border-bottom-color:var(--acc)}";
  document.head.prepend(css);
  new MutationObserver(render).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", render); else render();
})();
