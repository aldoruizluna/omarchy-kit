// Omarchy Kit portal runtime: language, key rendering, saved progress, and the local helper's API.
// Pages set window.PORTAL (built data) and call Portal.start(renderFn).
(function () {
  const P = (window.Portal = {});
  P.data = window.PORTAL || {};
  P.token = window.TOKEN || null;
  P.live = location.protocol.startsWith("http"); // served by omarchy-kit.service (file:// has no API)
  P.lang = (navigator.language || "en").slice(0, 2) === "es" ? "es" : "en";
  try { P.lang = localStorage.getItem("lang") || P.lang; } catch (e) {}
  P.t = (o) => (o == null ? "" : typeof o === "string" ? o : o[P.lang] ?? o.en ?? "");
  P.esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  // ---- keys: {mods:[..], key:".."} | "Super+Shift+H" | ["Super","H"] -> <kbd> chips
  const NAME = { SUPER: "Super", SHIFT: "Shift", CTRL: "Ctrl", ALT: "Alt", RETURN: "Return", ESCAPE: "Esc", SPACE: "Space",
    BACKSPACE: "Backspace", TAB: "Tab", COMMA: ",", PERIOD: ".", SLASH: "/", MINUS: "−", EQUAL: "=", LEFT: "←", RIGHT: "→", UP: "↑", DOWN: "↓",
    BRACKETLEFT: "[", BRACKETRIGHT: "]", DELETE: "Delete", PRINT: "Print" };
  P.keyName = (k) => NAME[String(k).toUpperCase()] || (String(k).length === 1 ? String(k).toUpperCase() : k);
  P.kbd = (combo) => {
    if (!combo) return "";
    let parts = Array.isArray(combo) ? combo : typeof combo === "string" ? combo.split("+").map((s) => s.trim()) : [...(combo.mods || []), combo.key];
    return parts.map((p) => `<kbd>${P.esc(P.keyName(p))}</kbd>`).join('<span class="plus">+</span>');
  };
  // binding lookup by Omarchy's own description (resolved at build time into PORTAL.keys)
  P.bind = (desc) => (P.data.keys || {})[desc] || null;
  P.bindHTML = (desc) => { const b = P.bind(desc); return b ? P.kbd(b) : `<span class="badge warn">${P.lang === "es" ? "sin atajo" : "not bound"}</span>`; };

  // ---- saved progress (per browser; this portal is per-user anyway)
  const KEY = "kit-progress";
  P.progress = {
    all() { try { return JSON.parse(localStorage.getItem(KEY) || "{}"); } catch (e) { return {}; } },
    get(id) { return this.all()[id]; },
    set(id, v) { const a = this.all(); a[id] = v; try { localStorage.setItem(KEY, JSON.stringify(a)); } catch (e) {} },
    reset() { try { localStorage.removeItem(KEY); } catch (e) {} },
  };

  // ---- local helper API
  P.api = {
    async state() { if (!P.live) return null; try { const r = await fetch("/api/state", { cache: "no-store" }); return r.ok ? r.json() : null; } catch (e) { return null; } },
    async hw() { if (!P.live) return null; try { const r = await fetch("/api/hw", { cache: "no-store" }); return r.ok ? r.json() : null; } catch (e) { return null; } },
    async menu(route) {
      if (!P.live || !P.token) return false;
      try { const r = await fetch("/api/menu", { method: "POST", headers: { "X-Token": P.token, "Content-Type": "application/json" }, body: JSON.stringify({ route }) }); return r.ok; }
      catch (e) { return false; }
    },
  };

  // ---- page plumbing
  const renderers = [];
  P.start = (fn) => { renderers.push(fn); P.render(); };
  P.render = () => {
    document.documentElement.lang = P.lang;
    document.querySelectorAll("[data-en]").forEach((e) => (e.innerHTML = e.dataset[P.lang] ?? e.dataset.en));
    const b = document.getElementById("bLang"); if (b) b.textContent = P.lang === "en" ? "EN → ES" : "ES → EN";
    renderers.forEach((f) => f());
  };
  document.addEventListener("click", async (e) => {
    const lb = e.target.closest("#bLang");
    if (lb) { P.lang = P.lang === "en" ? "es" : "en"; try { localStorage.setItem("lang", P.lang); } catch (x) {} P.render(); return; }
    const c = e.target.closest("[data-copy]");
    if (c) { try { await navigator.clipboard.writeText(c.dataset.copy); const t = c.textContent; c.textContent = "✓"; setTimeout(() => (c.textContent = t), 1100); } catch (x) {} return; }
    const m = e.target.closest("[data-menu]");
    if (m) {
      const ok = await P.api.menu(m.dataset.menu);
      if (!ok) alertInline(m, P.lang === "es" ? "Abre esta página desde Omarchy Kit (Super+Shift+H) para usar este botón." : "Open this page through Omarchy Kit (Super+Shift+H) to use this button.");
    }
  });
  function alertInline(el, msg) { let n = el.nextElementSibling; if (!n || !n.classList.contains("inline-msg")) { n = document.createElement("span"); n.className = "inline-msg small warn"; n.style.marginLeft = "8px"; el.after(n); } n.textContent = msg; }
  P.copyBtn = (text) => `<button class="copy" data-copy="${P.esc(text)}">${P.lang === "es" ? "Copiar" : "Copy"}</button>`;
  P.menuBtn = (route) => `<button class="copy" data-menu="${P.esc(route)}" title="${P.lang === "es" ? "Abre el menú real de Omarchy aquí" : "Opens the real Omarchy menu here"}">${P.lang === "es" ? "Muéstrame ↗" : "Show me ↗"}</button>`;
})();
