// Verifies keys/mackeys.lua against the REAL compositor: each ⌘ shortcut handler is called through
// `hyprctl eval`, and a scratch Brave (own profile, own window) reports the exact chord it receives.
// Needs a running Hyprland session. Usage: node test/verify-mackeys.mjs
import { launch, checker } from "./cdp.mjs";
import { spawn, execFileSync } from "node:child_process";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const LUA = join(HERE, "..", "keys", "mackeys.lua");
const PORT = 9336;
const c = checker("mackeys.lua");
const hypr = (...a) => execFileSync("hyprctl", a, { encoding: "utf8" });
const lua = (code) => hypr("eval", code);
const focus = (addr) => hypr("dispatch", `hl.dsp.focus({ window = "address:${addr}" })`);
const tag = (addr, t) => hypr("dispatch", `hl.dsp.window.tag({ tag = "${t}", window = "address:${addr}" })`);

const dir = mkdtempSync(join(tmpdir(), "mackeys-"));
const page = join(dir, "keytest.html");
writeFileSync(page, `<!doctype html><meta charset=utf-8><title>mackeys test</title><textarea id=t rows=4 cols=40>hello world</textarea>
<script>window.log=[];addEventListener('keydown',e=>{if(['Control','Shift','Alt','Meta'].includes(e.key))return;
log.push((e.metaKey?'Meta+':'')+(e.ctrlKey?'Ctrl+':'')+(e.altKey?'Alt+':'')+(e.shiftKey?'Shift+':'')+e.key)});
document.getElementById('t').focus();</script>`);

// Use the installed bindings when they are loaded, otherwise load the module just for this test.
const installed = /table/.test(lua(`print(type(o.mac_shortcuts))`)) || hypr("binds", "-j").includes("Select all (⌘A)");
if (!installed) lua(`dofile("${LUA}")`);

const brave = spawn("/opt/brave-bin/brave", [`--user-data-dir=${join(dir, "profile")}`, `--remote-debugging-port=${PORT}`,
  "--no-first-run", "--no-default-browser-check", "--ozone-platform=wayland", "--new-window", "file://" + page], { stdio: "ignore", detached: true });
process.env.CDP_ATTACH = String(PORT);
let b; let takeovers = false;
const winAddr = () => JSON.parse(hypr("clients", "-j")).find(w => w.title.startsWith("mackeys test"))?.address;
try {
  b = await launch();
  await b.sleep(800);
  const addr = winAddr();
  c.ok(!!addr, "scratch Brave window exists", addr);
  focus(addr); await b.sleep(300);
  c.ok(JSON.parse(hypr("activewindow", "-j")).address === addr, "scratch window is focused");
  const log = async () => JSON.parse(await b.eval(`JSON.stringify(window.log.splice(0))`));
  // Brave handles some chords itself (Ctrl+B moves focus to its sidebar), so put focus back in the page first.
  const refocus = async () => {
    for (let i = 0; i < 3 && !(await b.eval(`document.hasFocus()`)); i++) {
      await b.send("Page.bringToFront"); const r = await b.eval(`(()=>{const r=document.getElementById('t').getBoundingClientRect();return [r.x+20,r.y+20]})()`);
      await b.click(r[0], r[1]); await b.sleep(250);
    }
    await b.eval(`document.getElementById('t').focus()`);
  };
  const call = async (desc) => { await refocus(); await log(); lua(`o.mac_shortcuts[${JSON.stringify(desc)}]()`); await b.sleep(350); return log(); };
  await b.eval(`document.getElementById('t').focus()`); await log();

  console.log("bindings");
  const binds = JSON.parse(hypr("binds", "-j"));
  const mine = binds.filter(x => (x.description || "").includes("⌘"));
  c.ok(mine.length === 13, "13 ⌘ shortcuts are bound", String(mine.length));
  const chord = x => x.modmask + ":" + x.key.toUpperCase();
  const seen = new Map(); const dup = [];
  for (const x of binds) { if (x.key === "" || x.mouse) continue; const k = chord(x); if (seen.has(k) && (x.description || "").includes("⌘")) dup.push(`${x.description} vs ${seen.get(k)}`); seen.set(k, x.description); }
  c.ok(dup.length === 0, "no ⌘ shortcut shares its keys with another binding (Omarchy's own keep working)", dup.join(" | "));

  console.log("each shortcut sends the right chord to the app");
  const simple = [["Select all (⌘A)", "Ctrl+a"], ["Undo (⌘Z)", "Ctrl+z"], ["Redo (⇧⌘Z)", "Ctrl+Shift+Z"], ["Bold (⌘B)", "Ctrl+b"],
    ["Italic (⌘I)", "Ctrl+i"], ["Underline (⌘U)", "Ctrl+u"], ["Back (⌘[)", "Alt+ArrowLeft"], ["Forward (⌘])", "Alt+ArrowRight"],
    ["Reopen closed tab (⇧⌘T)", "Ctrl+Shift+T"]];
  for (const [d, want] of simple) {
    const got = await call(d);
    c.ok(got.length === 1 && got[0] === want, `${d} → ${want}`, JSON.stringify(got) + " page focused: " + await b.eval(`document.hasFocus()`));
  }
  for (const d of ["Reload (⌘R)", "Hard reload (⇧⌘R)"]) {
    await b.eval(`window.__m = 1`); await call(d).catch(() => {}); await b.sleep(1200);
    const type = await b.eval(`window.__m === undefined && performance.getEntriesByType('navigation')[0].type`);
    c.ok(type === "reload", `${d} reloads the page`, JSON.stringify(type));
  }

  console.log("terminals are left alone");
  tag(addr, "+terminal"); await b.sleep(200);
  c.ok(JSON.parse(hypr("activewindow", "-j")).tags.some(t => t.replace(/\*$/, "") === "terminal"), "window is tagged as a terminal for the test");
  await b.eval(`document.getElementById('t').focus()`); await log();
  for (const d of ["Select all (⌘A)", "Undo (⌘Z)"]) { const got = await call(d); c.ok(got.length === 0, `${d} sends nothing in a terminal`, JSON.stringify(got)); }
  tag(addr, "-terminal"); await b.sleep(200);
  const back = await call("Select all (⌘A)"); c.ok(back.length === 1 && back[0] === "Ctrl+a", "and works again once it is no longer a terminal", JSON.stringify(back));

  console.log("optional takeovers: Super+W/T/F/S/L/G/P (off by default)");
  const floating = () => JSON.parse(hypr("clients", "-j")).find(w => w.address === addr)?.floating;
  const fullscreen = () => JSON.parse(hypr("clients", "-j")).find(w => w.address === addr)?.fullscreen;
  c.ok(!JSON.parse(hypr("binds", "-j")).some(x => x.modmask === 64 && x.key.toUpperCase() === "T" && (x.description || "").includes("⌘")), "nothing is taken over until you ask for it");
  lua(`o.mac_extras("W T F S L G P")`); await b.sleep(400); takeovers = true;
  const bnd = JSON.parse(hypr("binds", "-j"));
  const MACD = ["Close tab or window (⌘W)", "New tab (⌘T)", "Find (⌘F)", "Save (⌘S)", "Address bar (⌘L)", "Find next (⌘G)", "Print (⌘P)"];
  const HOMED = ["Close window (Omarchy, any app)", "Toggle window floating/tiling (Omarchy, any app)", "Full screen (Omarchy, any app)", "Toggle scratchpad (Omarchy, any app)",
    "Toggle workspace layout (Omarchy, any app)", "Toggle window grouping (Omarchy, any app)", "Pseudo window (Omarchy, any app)"];
  c.ok(MACD.every(d => bnd.filter(x => x.description === d).length === 1), "each of the 7 Mac keys is bound exactly once");
  c.ok(HOMED.every(d => bnd.filter(x => x.description === d).length === 1), "each displaced Omarchy action is bound exactly once, at its new chord");
  const supers = bnd.filter(x => x.modmask === 64 && "WTFSLGP".includes(x.key.toUpperCase()) && x.key.length === 1);
  c.ok(supers.length === 7 && supers.every(x => x.description.includes("⌘")), "Super+W/T/F/S/L/G/P now carry only the Mac meaning", supers.map(x => x.key + ":" + x.description).join(" | "));
  const ch = new Map(); const dups = [];
  for (const x of bnd) { if (x.key === "" || x.mouse) continue; const k = x.modmask + ":" + x.key.toUpperCase(); if (ch.has(k) && (MACD.includes(x.description) || HOMED.includes(x.description))) dups.push(x.description + " vs " + ch.get(k)); ch.set(k, x.description); }
  c.ok(dups.length === 0, "no chord is shared with another binding", dups.join(" | "));
  const f = await call("Find (⌘F)"); c.ok(f.length === 1 && f[0] === "Ctrl+f", "Find (⌘F) → Ctrl+f in an app", JSON.stringify(f));
  const tabs0 = (await (await fetch(`http://127.0.0.1:${PORT}/json`)).json()).filter(t => t.type === "page").length;
  await call("New tab (⌘T)"); await b.sleep(900);
  const tabs1 = (await (await fetch(`http://127.0.0.1:${PORT}/json`)).json()).filter(t => t.type === "page").length;
  c.ok(tabs1 > tabs0, "New tab (⌘T) → Brave opens a new tab in an app", `${tabs0} → ${tabs1}`);
  focus(addr); await b.sleep(300);
  const fl0 = floating(); lua(`o.mac_shortcuts["Toggle window floating/tiling (Omarchy, any app)"]()`); await b.sleep(400);
  c.ok(floating() !== fl0, "the displaced Omarchy action still works in an app (float toggle)", `${fl0} → ${floating()}`);
  lua(`o.mac_shortcuts["Toggle window floating/tiling (Omarchy, any app)"]()`); await b.sleep(400);
  tag(addr, "+terminal"); await b.sleep(200);
  const fl1 = floating(); await call("New tab (⌘T)").catch(() => {}); await b.sleep(400);
  c.ok(floating() !== fl1, "in a terminal, Super+T keeps its Omarchy meaning (float toggle)", `${fl1} → ${floating()}`);
  lua(`o.mac_shortcuts["New tab (⌘T)"]()`); await b.sleep(400);
  const fs0 = fullscreen(); lua(`o.mac_shortcuts["Find (⌘F)"]()`); await b.sleep(500);
  c.ok(fullscreen() !== fs0, "in a terminal, Super+F keeps its Omarchy meaning (full screen)", `${fs0} → ${fullscreen()}`);
  lua(`o.mac_shortcuts["Find (⌘F)"]()`); await b.sleep(500);
  tag(addr, "-terminal"); await b.sleep(200);
  hypr("reload"); await b.sleep(1200); takeovers = false;
  const restored = JSON.parse(hypr("binds", "-j"));
  c.ok(restored.filter(x => (x.description || "").includes("⌘")).length === 13 && restored.some(x => x.modmask === 64 && x.key.toUpperCase() === "T" && x.description === "Toggle window floating/tiling"),
    "a reload puts everything back (13 Mac shortcuts, Super+T is Omarchy's float toggle again)");

  console.log("window-opening shortcuts");
  const before = (await (await fetch(`http://127.0.0.1:${PORT}/json`)).json()).filter(t => t.type === "page").length;
  const d1 = await call("Bookmark page (⌘D)"); c.ok(d1.length === 1 && d1[0] === "Ctrl+d", "Bookmark page (⌘D) → Ctrl+d", JSON.stringify(d1));
  await b.eval(`document.getElementById('t').focus()`);
  focus(addr); await b.sleep(300);
  await call("New window (⌘N)");   // Ctrl+N is a reserved browser accelerator: the page never sees it, so count windows
  await b.sleep(1500);
  const after = (await (await fetch(`http://127.0.0.1:${PORT}/json`)).json()).filter(t => t.type === "page").length;
  c.ok(after > before, "New window (⌘N) → Brave opens a new window", `${before} → ${after} pages`);
} catch (e) { console.log("HARNESS ERROR", e.message); c.ok(false, "harness ran to completion", e.message); }
finally {
  try { b?.close(); } catch {}
  try { process.kill(-brave.pid, "SIGTERM"); } catch {}
  await new Promise(r => setTimeout(r, 800));
  rmSync(dir, { recursive: true, force: true });
  if (takeovers || !installed) hypr("reload");
}
const fails = c.done(); process.exit(fails ? 1 : 0);
