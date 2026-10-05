// Omarchy Kit shell, loaded by every page: live Omarchy theme, the Ctrl+K command palette, XP / streak /
// badges for the learning path, toasts and confetti. Works without the server too (file://): the theme and
// anything needing the local helper simply stay off.
(function () {
  const K = (window.Kit = {});
  const live = location.protocol.startsWith("http");
  const file = !live;
  const es = () => (document.documentElement.lang || "en").slice(0, 2) === "es";
  const t = (o) => (o == null ? "" : typeof o === "string" ? o : (es() ? o.es : o.en) ?? o.en ?? "");
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const href = (route) => {
    if (!file) return route;
    const [path, hash] = route.split("#");
    const p = (window.KitNav?.pages || []).find((x) => x[1] === path);
    return (p ? p[0] : "index.html") + (hash ? "#" + hash : "");
  };
  const token = () => document.querySelector('meta[name="kit-token"]')?.content || window.TOKEN || null;
  K.t = t; K.esc = esc; K.href = href; K.live = live;
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} },
  };
  const today = () => new Date().toLocaleDateString("en-CA");
  const reduced = () => matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ------------------------------------------------------------- toasts
  K.toast = (title, sub, big) => {
    let box = document.querySelector(".kit-toasts");
    if (!box) { box = document.createElement("div"); box.className = "kit-toasts"; box.setAttribute("role", "status"); document.body.append(box); }
    const n = document.createElement("div"); n.className = "kit-toast";
    n.innerHTML = (big ? `<span class="big" aria-hidden="true">${esc(big)}</span>` : "") + `<div><b>${esc(title)}</b>${sub ? `<small>${esc(sub)}</small>` : ""}</div>`;
    box.append(n);
    setTimeout(() => { n.classList.add("out"); setTimeout(() => n.remove(), 350); }, 4200);
  };

  // ------------------------------------------------------------- confetti (theme colors)
  K.confetti = (power = 1) => {
    if (reduced()) return;
    const cs = getComputedStyle(document.documentElement);
    const cols = ["--acc-fill", "--acc", "--ok", "--warn", "--fg"].map((v) => cs.getPropertyValue(v).trim()).filter(Boolean);
    const c = document.createElement("canvas"), dpr = devicePixelRatio || 1;
    c.style.cssText = "position:fixed;inset:0;width:100vw;height:100vh;pointer-events:none;z-index:130";
    c.width = innerWidth * dpr; c.height = innerHeight * dpr; document.body.append(c);
    const x = c.getContext("2d"); x.scale(dpr, dpr);
    const N = Math.round(140 * power), ps = [];
    for (let i = 0; i < N; i++) {
      const side = i % 2 ? 1 : -1;
      ps.push({ x: side > 0 ? -10 : innerWidth + 10, y: innerHeight * (0.55 + Math.random() * 0.3), vx: side * (6 + Math.random() * 9), vy: -(9 + Math.random() * 11),
        r: Math.random() * Math.PI, vr: (Math.random() - 0.5) * 0.4, w: 6 + Math.random() * 6, h: 4 + Math.random() * 5, c: cols[i % cols.length] });
    }
    let f = 0;
    (function step() {
      x.clearRect(0, 0, innerWidth, innerHeight);
      for (const p of ps) {
        p.vy += 0.35; p.vx *= 0.985; p.x += p.vx; p.y += p.vy; p.r += p.vr;
        x.save(); x.translate(p.x, p.y); x.rotate(p.r); x.fillStyle = p.c; x.globalAlpha = Math.max(0, 1 - f / 170); x.fillRect(-p.w / 2, -p.h / 2, p.w, p.h); x.restore();
      }
      if (++f < 180) requestAnimationFrame(step); else c.remove();
    })();
  };

  // ------------------------------------------------------------- shared index (lessons, shortcuts, apps…)
  let indexP = null;
  K.index = () => (indexP ||= live ? fetch("/data/kit-index.json").then((r) => r.json()).catch(() => null) : Promise.resolve(window.PORTAL ? fromPortal() : null));
  function fromPortal() {
    const D = window.PORTAL;
    return { lessons: D.levels.flatMap((lv) => lv.lessons.map((l) => ({ id: l.id, en: l.en, es: l.es, level: lv.id, steps: l.steps.length }))),
      levels: D.levels.map((lv) => ({ id: lv.id, en: lv.en, es: lv.es, lessons: lv.lessons.map((l) => l.id) })), shortcuts: [], mac: [], glossary: [], apps: [], commands: [], menu: [] };
  }

  // ------------------------------------------------------------- progress, XP, streak, badges
  const RANKS = [[0, "Newcomer", "Recién llegado"], [80, "Apprentice", "Aprendiz"], [220, "Tiler", "Acomodador"],
    [420, "Power user", "Experto"], [650, "Omarchist", "Omarchista"]];
  const act = () => store.get("kit-activity", { days: [], pages: [], palette: 0, themes: 0, night: false });
  const saveAct = (a) => store.set("kit-activity", a);
  K.activity = act;
  function bump(fn) { const a = act(); fn(a); saveAct(a); K.refresh(); }
  K.logStep = () => bump((a) => { const d = today(); if (!a.days.includes(d)) a.days.push(d); a.days = a.days.slice(-400); const h = new Date().getHours(); if (h < 5) a.night = true; });

  function streak(days) {
    const set = new Set(days); let n = 0; const d = new Date();
    if (!set.has(d.toLocaleDateString("en-CA"))) d.setDate(d.getDate() - 1); // a streak survives until the day ends
    while (set.has(d.toLocaleDateString("en-CA"))) { n++; d.setDate(d.getDate() - 1); }
    return n;
  }

  K.stats = async () => {
    const ix = await K.index(); if (!ix) return null;
    const prog = store.get("kit-progress", {}), a = act();
    const steps = Object.keys(prog).filter((k) => k.startsWith("step:") && prog[k] === 1).length;
    const done = ix.lessons.filter((l) => prog[l.id] === "done");
    const totalSteps = ix.lessons.reduce((s, l) => s + l.steps, 0);
    const levelsDone = ix.levels.filter((lv) => lv.lessons.every((id) => prog[id] === "done"));
    const st = streak(a.days);
    const B = [
      ["first", "👣", { en: "First steps", es: "Primeros pasos" }, { en: "Finish any step", es: "Completa cualquier paso" }, steps > 0],
      ["lesson", "🎓", { en: "Lesson learned", es: "Lección aprendida" }, { en: "Finish a whole lesson", es: "Completa una lección" }, done.length > 0],
      ...ix.levels.map((lv, i) => ["lv-" + lv.id, ["🛟", "🪟", "🧰", "🎨", "🚀", "🧠", "🏔️"][i] || "⭐", { en: lv.en.replace(/^\d+\s*·\s*/, ""), es: lv.es.replace(/^\d+\s*·\s*/, "") },
        { en: "Complete level " + (i + 1), es: "Completa el nivel " + (i + 1) }, levelsDone.includes(lv)]),
      ["streak3", "🔥", { en: "On fire", es: "En racha" }, { en: "Learn 3 days in a row", es: "Aprende 3 días seguidos" }, st >= 3],
      ["streak7", "🌋", { en: "Unstoppable", es: "Imparable" }, { en: "Learn 7 days in a row", es: "Aprende 7 días seguidos" }, st >= 7],
      ["explorer", "🧭", { en: "Explorer", es: "Explorador" }, { en: "Visit every page of the kit", es: "Visita todas las páginas del kit" }, (window.KitNav?.pages || []).every((p) => a.pages.includes(p[1]))],
      ["palette", "⚡", { en: "Speed demon", es: "Veloz" }, { en: "Use Ctrl+K search 5 times", es: "Usa la búsqueda Ctrl+K 5 veces" }, a.palette >= 5],
      ["stylist", "🎨", { en: "Stylist", es: "Estilista" }, { en: "Switch your Omarchy theme", es: "Cambia tu tema de Omarchy" }, a.themes > 0],
      ["sysmon", "📈", { en: "Under the hood", es: "Bajo el capó" }, { en: "Open the live System page", es: "Abre la página Sistema en vivo" }, a.pages.includes("/system")],
      ["owl", "🦉", { en: "Night owl", es: "Búho nocturno" }, { en: "Finish a step after midnight", es: "Completa un paso después de medianoche" }, !!a.night],
      ["grad", "🏆", { en: "Omarchist", es: "Omarchista" }, { en: "Finish every lesson", es: "Completa todas las lecciones" }, done.length === ix.lessons.length],
    ].map(([id, em, name, how, got]) => ({ id, em, name, how, got }));
    const xp = steps * 10 + done.length * 30 + B.filter((b) => b.got).length * 25;
    const ri = RANKS.reduce((acc, r, i) => (xp >= r[0] ? i : acc), 0);
    const next = RANKS[ri + 1];
    return { xp, steps, totalSteps, lessons: done.length, totalLessons: ix.lessons.length, streak: st, badges: B,
      rank: { n: ri + 1, en: RANKS[ri][1], es: RANKS[ri][2], from: RANKS[ri][0], to: next ? next[0] : null, nextEn: next?.[1], nextEs: next?.[2] },
      pct: totalSteps ? Math.round((100 * steps) / totalSteps) : 0 };
  };

  // Recompute, update the nav chip, and announce badges earned since last time.
  let refreshing = null;
  K.refresh = () => (refreshing ||= (async () => {
    await null;
    const s = await K.stats(); refreshing = null; if (!s) return;
    const chip = document.getElementById("kitXp");
    if (chip) {
      chip.hidden = false;
      chip.title = t({ en: `${s.rank.en}: ${s.xp} XP`, es: `${s.rank.es}: ${s.xp} XP` }) + (s.streak ? t({ en: ` · ${s.streak}-day streak`, es: ` · racha de ${s.streak} días` }) : "");
      chip.innerHTML = `<span class="lv">Lv ${s.rank.n}</span><span class="xp">${s.xp} XP</span>${s.streak ? `<span>🔥${s.streak}</span>` : ""}`;
    }
    const seen = store.get("kit-badges", null), got = s.badges.filter((b) => b.got).map((b) => b.id);
    if (seen) {
      const fresh = s.badges.filter((b) => b.got && !seen.includes(b.id));
      fresh.forEach((b, i) => setTimeout(() => { K.toast(t({ en: "Badge unlocked: ", es: "Insignia desbloqueada: " }) + t(b.name), t(b.how), b.em); }, 600 + i * 900));
      if (fresh.length) setTimeout(() => K.confetti(0.6), 600);
    }
    store.set("kit-badges", got);
    document.dispatchEvent(new CustomEvent("kit:stats", { detail: s }));
  })());

  // Hook the portal's progress store so every finished step counts towards the streak.
  function hookProgress() {
    const P = window.Portal?.progress; if (!P || P.__kit) return;
    const set = P.set.bind(P), reset = P.reset.bind(P);
    P.set = (id, v) => { set(id, v); if (v === 1 || v === "done") K.logStep(); else K.refresh(); };
    P.reset = () => { reset(); K.refresh(); };
    P.__kit = true;
  }

  // ------------------------------------------------------------- live Omarchy theme
  let themeVer = null;
  async function watchTheme() {
    if (!live || document.hidden) return;
    try {
      const r = await (await fetch("/api/theme", { cache: "no-store" })).json();
      if (themeVer && r.version !== themeVer) {
        const l = document.querySelector('link[href^="theme.css"],link[href^="/theme.css"]');
        if (l) { const n = l.cloneNode(); n.href = "/theme.css?v=" + Date.now(); n.onload = () => l.remove(); l.after(n); }
        const changedName = themeVer.split("|")[0] !== r.version.split("|")[0];
        if (changedName) { bump((a) => (a.themes += 1)); K.toast(t({ en: "Theme: ", es: "Tema: " }) + r.name.replace(/(^|-)([a-z])/g, (m, a, b) => (a ? " " : "") + b.toUpperCase()), t({ en: "The kit follows your Omarchy theme.", es: "El kit sigue tu tema de Omarchy." }), "🎨"); }
        document.dispatchEvent(new CustomEvent("kit:theme", { detail: r }));
      }
      themeVer = r.version; K.themes = r.themes; K.themeName = r.name;
    } catch (e) {}
  }
  K.setTheme = async (id) => {
    const tk = token(); if (!tk) return false;
    try { return (await fetch("/api/theme", { method: "POST", headers: { "X-Token": tk, "Content-Type": "application/json" }, body: JSON.stringify({ id }) })).ok; } catch (e) { return false; }
  };
  K.menu = async (route) => {
    const tk = token(); if (!tk) return false;
    try { return (await fetch("/api/menu", { method: "POST", headers: { "X-Token": tk, "Content-Type": "application/json" }, body: JSON.stringify({ route }) })).ok; } catch (e) { return false; }
  };

  // ------------------------------------------------------------- command palette
  const ICON = {
    page: "M5 3h9l5 5v13H5zM14 3v5h5", lesson: "M2 9l10-5 10 5-10 5zM6 11v5c3 2.5 9 2.5 12 0v-5", key: "M3 6h18v12H3zM7 10h.01M11 10h.01M15 10h.01M7 14h10",
    mac: "M12 8c-2-1.2-6-.8-6 4 0 4 2.5 8 4 8 1 0 1.3-.6 2-.6s1 .6 2 .6c1.4 0 3-2.5 3.6-4.5-2.6-1.1-2.7-4.8-.2-6.1C16.2 7.6 13.6 7.4 12 8zM15 4c-1.5 0-3 1.2-3 3 1.6 0 3-1.3 3-3z",
    app: "M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z", cmd: "M4 6l5 6-5 6M12 18h8", menu: "M4 6h16M4 12h16M4 18h10",
    word: "M4 4h11a3 3 0 0 1 3 3v13H7a3 3 0 0 1-3-3zM4 17a3 3 0 0 1 3-3h11", theme: "M12 3a9 9 0 1 0 0 18c1 0 1.5-.8 1.5-1.5 0-1-.8-1.2-.8-2.2 0-.8.7-1.3 1.5-1.3H17a4 4 0 0 0 4-4c0-5-4-9-9-9zM7.5 11h.01M10 7h.01M15 7h.01",
    act: "M13 2 4 14h7l-1 8 9-12h-7z",
  };
  const ic = (n) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${ICON[n]}"/></svg>`;
  const kbd = (k) => k.map((x) => `<kbd>${esc({ SUPER: "Super", SHIFT: "Shift", CTRL: "Ctrl", ALT: "Alt", RETURN: "Return", SPACE: "Space", ESCAPE: "Esc", COMMA: ",", PERIOD: ".", SLASH: "/", MINUS: "−", EQUAL: "=", LEFT: "←", RIGHT: "→", UP: "↑", DOWN: "↓" }[String(x).toUpperCase()] || (String(x).length === 1 ? String(x).toUpperCase() : x))}</kbd>`).join("");
  const norm = (s) => String(s || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");

  async function items() {
    const ix = (await K.index()) || {};
    const L = [];
    const G = { pages: { en: "Pages", es: "Páginas" }, actions: { en: "Actions", es: "Acciones" }, lessons: { en: "Lessons", es: "Lecciones" },
      keys: { en: "Shortcuts", es: "Atajos" }, mac: { en: "From macOS", es: "Desde macOS" }, apps: { en: "Apps", es: "Apps" }, themes: { en: "Themes", es: "Temas" },
      menu: { en: "Omarchy menu", es: "Menú de Omarchy" }, gloss: { en: "Glossary", es: "Glosario" }, cmds: { en: "Commands", es: "Comandos" } };
    (window.KitNav?.pages || []).forEach((p) => L.push({ g: "pages", i: "page", title: es() ? p[3] : p[2], hay: p[2] + " " + p[3], go: p[1] }));
    L.push({ g: "actions", i: "act", title: t({ en: "Switch language: English ⇄ Español", es: "Cambiar idioma: Español ⇄ English" }), hay: "language idioma english espanol", run: () => document.getElementById("bLang")?.click() });
    if (token()) {
      L.push({ g: "actions", i: "menu", title: t({ en: "Open the Omarchy menu", es: "Abrir el menú de Omarchy" }), hay: "omarchy menu super space", run: () => K.menu("root") });
      L.push({ g: "actions", i: "theme", title: t({ en: "Next background image", es: "Siguiente fondo de pantalla" }), hay: "wallpaper background fondo next siguiente", run: () => K.menu("style.background") });
    }
    (ix.lessons || []).forEach((l) => L.push({ g: "lessons", i: "lesson", title: t(l), hay: l.en + " " + l.es, go: "/learn#" + l.id }));
    (K.themes || []).forEach((th) => L.push({ g: "themes", i: "theme", title: th.name + (th.id === K.themeName ? " ✓" : ""), hay: "theme tema " + th.name + " " + th.mode,
      right: `<span class="kp-sw">${[th.bg, th.fg, th.acc].map((c) => `<i style="background:${esc(c)}"></i>`).join("")}</span>`,
      run: async () => { if (!(await K.setTheme(th.id))) K.toast(t({ en: "Couldn't switch theme", es: "No se pudo cambiar el tema" }), t({ en: "Open the kit with Super+Shift+H.", es: "Abre el kit con Super+Shift+H." }), "⚠️"); } }));
    (ix.shortcuts || []).forEach((k) => L.push({ g: "keys", i: "key", title: t(k), hay: k.en + " " + k.es + " " + k.k.join(" "), right: kbd(k.k), go: "/keyboard" }));
    (ix.mac || []).forEach((m) => L.push({ g: "mac", i: "mac", title: t(m), sub: t(m.group), hay: m.en + " " + m.es + " " + m.mk + " mac", right: m.mk ? `<span>${esc(m.mk)}</span>` : "", go: "/mac" }));
    (ix.apps || []).forEach((a) => L.push({ g: "apps", i: "app", title: a.name, sub: t(a), hay: a.name + " " + a.en + " " + a.es, go: "/apps" }));
    (ix.menu || []).forEach((m) => L.push({ g: "menu", i: "menu", title: m.label, hay: m.label + " " + m.id + " menu", right: token() ? `<span>${t({ en: "Show me ↗", es: "Muéstrame ↗" })}</span>` : "",
      run: token() ? () => K.menu(m.id) : null, go: "/reference#menu" }));
    (ix.glossary || []).forEach((g) => L.push({ g: "gloss", i: "word", title: t(g), sub: es() ? g.des : g.den, hay: g.en + " " + g.es + " " + g.den, go: "/reference#gloss" }));
    (ix.commands || []).forEach((c) => L.push({ g: "cmds", i: "cmd", title: c.cmd, sub: c.summary, hay: c.cmd.replace(/-/g, " ") + " " + c.summary,
      right: `<span>${t({ en: "copy", es: "copiar" })}</span>`, copy: c.cmd }));
    L.forEach((x) => { x.n = norm(x.hay + " " + x.title); x.gl = t(G[x.g]); });
    return L;
  }
  const ORDER = ["pages", "actions", "lessons", "themes", "keys", "mac", "apps", "menu", "gloss", "cmds"];
  function search(L, q) {
    const words = norm(q).split(/\s+/).filter(Boolean);
    if (!words.length) return L.filter((x) => x.g === "pages" || x.g === "actions" || x.g === "lessons").slice(0, 30);
    const scored = [];
    for (const x of L) {
      let s = 0, ok = true;
      for (const w of words) {
        const i = x.n.indexOf(w);
        if (i < 0) { ok = false; break; }
        s += i === 0 ? 6 : /\s|-/.test(x.n[i - 1]) ? 4 : 1;
        if (norm(x.title).includes(w)) s += 3;
      }
      if (ok) scored.push([s - ORDER.indexOf(x.g) * 0.3, x]);
    }
    scored.sort((a, b) => b[0] - a[0]);
    const per = {}; // keep each group short so one big group can't drown the rest
    return scored.map((s) => s[1]).filter((x) => (per[x.g] = (per[x.g] || 0) + 1) <= 8).slice(0, 50)
      .sort((a, b) => ORDER.indexOf(a.g) - ORDER.indexOf(b.g));
  }

  let open = null;
  K.palette = async () => {
    if (open) return;
    bump((a) => (a.palette += 1));
    const back = document.createElement("div"); back.className = "kp-back";
    back.innerHTML = `<div class="kp" role="dialog" aria-modal="true" aria-label="${esc(t({ en: "Search Omarchy Kit", es: "Buscar en Omarchy Kit" }))}">
      <input type="text" role="combobox" aria-expanded="true" aria-controls="kpList" autocomplete="off" spellcheck="false" placeholder="${esc(t({ en: "Search pages, lessons, shortcuts, apps, themes, commands…", es: "Busca páginas, lecciones, atajos, apps, temas, comandos…" }))}">
      <div class="kp-list" id="kpList" role="listbox"></div>
      <div class="kp-foot"><span><kbd>↑</kbd><kbd>↓</kbd> ${t({ en: "move", es: "mover" })}</span><span><kbd>Return</kbd> ${t({ en: "open", es: "abrir" })}</span><span><kbd>Esc</kbd> ${t({ en: "close", es: "cerrar" })}</span><span style="margin-left:auto">${t({ en: "Tip: type “theme” to restyle your whole desktop", es: "Tip: escribe “tema” para cambiar el estilo de todo tu escritorio" })}</span></div></div>`;
    document.body.append(back);
    const inp = back.querySelector("input"), list = back.querySelector(".kp-list");
    const prevFocus = document.activeElement;
    open = back; inp.focus();
    const L = await items();
    let res = [], sel = 0;
    const draw = () => {
      res = search(L, inp.value); sel = Math.min(sel, Math.max(0, res.length - 1));
      if (!res.length) { list.innerHTML = `<div class="kp-empty">${t({ en: "Nothing found. Try a Mac word like “Spotlight” or “Finder”.", es: "Nada encontrado. Prueba una palabra de Mac como “Spotlight” o “Finder”." })}</div>`; return; }
      let g = null;
      list.innerHTML = res.map((x, i) => (x.g !== g ? `<div class="kp-group">${esc((g = x.g, x.gl))}</div>` : "") +
        `<div class="kp-item" role="option" id="kp${i}" data-i="${i}" aria-selected="${i === sel}"><span class="ic">${ic(x.i)}</span><div style="min-width:0"><div class="t">${esc(x.title)}</div>${x.sub ? `<div class="s">${esc(x.sub)}</div>` : ""}</div><span class="r">${x.right || ""}</span></div>`).join("");
      inp.setAttribute("aria-activedescendant", "kp" + sel);
      list.querySelector('[aria-selected="true"]')?.scrollIntoView({ block: "nearest" });
    };
    const close = () => { back.remove(); open = null; prevFocus?.focus?.(); };
    const choose = async (x) => {
      if (!x) return;
      if (x.copy) { try { await navigator.clipboard.writeText(x.copy); K.toast(t({ en: "Copied", es: "Copiado" }), x.copy, "📋"); } catch (e) {} close(); return; }
      close();
      if (x.run) { await x.run(); return; }
      if (x.go) {
        const url = href(x.go), [path, hash] = url.split("#");
        if (location.pathname === path || location.pathname.endsWith("/" + path)) { location.hash = hash || ""; if (!hash) scrollTo({ top: 0, behavior: "smooth" }); }
        else location.href = url;
      }
    };
    inp.addEventListener("input", () => { sel = 0; draw(); });
    inp.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") { sel = Math.min(sel + 1, res.length - 1); draw(); e.preventDefault(); }
      else if (e.key === "ArrowUp") { sel = Math.max(sel - 1, 0); draw(); e.preventDefault(); }
      else if (e.key === "Enter") { choose(res[sel]); e.preventDefault(); }
      else if (e.key === "Escape") { close(); e.preventDefault(); }
      else if (e.key === "Tab") e.preventDefault();
    });
    list.addEventListener("mousemove", (e) => { const it = e.target.closest(".kp-item"); if (it && +it.dataset.i !== sel) { sel = +it.dataset.i; list.querySelectorAll(".kp-item").forEach((n) => n.setAttribute("aria-selected", +n.dataset.i === sel)); } });
    list.addEventListener("click", (e) => { const it = e.target.closest(".kp-item"); if (it) choose(res[+it.dataset.i]); });
    back.addEventListener("mousedown", (e) => { if (e.target === back) close(); });
    draw();
  };
  document.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && !e.altKey && e.key.toLowerCase() === "k") { e.preventDefault(); open ? open.querySelector("input").focus() : K.palette(); }
  }, true);
  document.addEventListener("click", (e) => { if (e.target.closest("[data-kit-palette]")) K.palette(); });

  // ------------------------------------------------------------- boot
  function boot() {
    const route = (KitNav?.pages || []).find((p) => (file ? location.pathname.endsWith("/" + p[0]) : (location.pathname.replace(/\/$/, "") || "/") === p[1] || location.pathname === "/" + p[0]));
    if (route) { const a = act(); if (!a.pages.includes(route[1])) { a.pages.push(route[1]); saveAct(a); } }
    hookProgress(); K.refresh();
    if (live) { watchTheme(); setInterval(watchTheme, 2500); document.addEventListener("visibilitychange", watchTheme); }
  }
  document.addEventListener("kit:nav", () => K.refresh());
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
