// Checks the Games page's "Free games store" section in English and Spanish. The page is served from this
// checkout by a throwaway static server, not by the kit service, so it needs no running service and can test an
// uncommitted worktree. (Live data on the page needs the service; this section is static text.)
//   python3 build_cheatsheet.py && node test/verify-store-page.mjs
import { spawn } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { launch, checker } from "./cdp.mjs";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const PORT = 8790 + Math.floor(Math.random() * 150);
const BASE = `http://127.0.0.1:${PORT}`;
const srv = spawn("python3", ["-m", "http.server", String(PORT), "--bind", "127.0.0.1", "--directory", ROOT], { stdio: "ignore" });
const c = checker("store page");
let b;
try {
  for (let i = 0; i < 50; i++) { try { if ((await fetch(BASE + "/games.html")).ok) break; } catch {} await new Promise(r => setTimeout(r, 100)); }
  b = await launch({ width: 1280, height: 1000 });
  const go = async () => { await b.goto(BASE + "/games.html"); await b.sleep(900); };
  await go(); await b.eval(`localStorage.setItem('lang','en')`); await go();
  const text = (sel) => b.eval(`document.querySelector(${JSON.stringify(sel)})?.innerText || ''`);

  console.log("English");
  c.ok(await b.eval(`[...document.querySelectorAll('h2')].some(h => h.textContent === 'Free games store')`), "section heading is shown");
  const rows = await b.eval(`document.querySelectorAll('#storeCmds tr').length`);
  c.ok(rows === 9, "command table lists the 8 store commands plus its header", `rows=${rows}`);
  const en = await text("#store");
  for (const need of ["store-publisher.pem", "store refresh", "store get", "store sync", "tombstone", "never accepts a key the first time"])
    c.ok(en.includes(need), `English text mentions "${need}"`);
  const note = await b.eval(`[...document.querySelectorAll('p.small.mut')].map(p => p.innerText).find(t => t.includes('Nothing is uploaded')) || ''`);
  c.ok(note.includes("Nothing is uploaded") && note.includes("guide"), "privacy and guide-only note is shown", note.slice(0, 80));

  console.log("Your own backups (English)");
  c.ok(await b.eval(`[...document.querySelectorAll('h2')].some(h => h.textContent === 'Your own backups')`), "backups heading is shown");
  const brows = await b.eval(`document.querySelectorAll('#backupCmds tr').length`);
  c.ok(brows === 8, "backups table lists the 7 commands plus its header", `rows=${brows}`);
  const bk = await text("#backups");
  for (const need of ["store locations add", "store scan", "unidentified", "In your backups", "--which", "--link", "refused"])
    c.ok(bk.includes(need), `backups text mentions "${need}"`);
  const stays = await b.eval(`[...document.querySelectorAll('p.small.mut')].map(p => p.innerText).find(t => t.includes('Stays on this machine')) || ''`);
  c.ok(stays.includes("no way to export, share or import") && stays.includes("personal.sqlite") && stays.includes("Nothing is uploaded"), "the page says plainly that nothing is shared", stays.slice(0, 80));

  console.log("Spanish");
  await b.eval(`document.getElementById('bLang').click()`); await b.sleep(250);
  c.ok(await b.eval(`[...document.querySelectorAll('h2')].some(h => h.textContent === 'Tienda de juegos libres')`), "heading switches to Spanish");
  const es = await text("#store");
  for (const need of ["store-publisher.pem", "lápida", "ni acepta una llave nueva la primera vez"])
    c.ok(es.includes(need), `Spanish text mentions "${need}"`);
  c.ok(await b.eval(`[...document.querySelectorAll('p.small.mut')].some(p => p.innerText.includes('Nada se sube'))`), "Spanish privacy note is shown");
  c.ok(!(await text("#store")).includes("Nothing is uploaded"), "no English left in the store card after switching");
  c.ok(await b.eval(`[...document.querySelectorAll('h2')].some(h => h.textContent === 'Tus propios respaldos')`), "backups heading switches to Spanish");
  const bes = await text("#backups");
  for (const need of ["store locations add", "sin identificar", "En tus respaldos", "--which", "Se rechazan"])
    c.ok(bes.includes(need), `Spanish backups text mentions "${need}"`);
  c.ok(await b.eval(`[...document.querySelectorAll('p.small.mut')].some(p => p.innerText.includes('No sale de esta máquina') && p.innerText.includes('a propósito no hay forma de exportar'))`), "Spanish says plainly that nothing is shared");
  c.ok(!bes.includes("Register the folder") && !bes.includes("Nothing is uploaded"), "no English left in the backups card after switching");
  await b.eval(`document.getElementById('bLang').click()`);

  console.log("hygiene");
  const all = await b.eval(`document.documentElement.outerHTML`);
  // Private product names are not written into this public repo. A maintainer lists them in the environment to check the page:
  //   KIT_PRIVATE_NAMES="name1,name2" node test/verify-store-page.mjs
  const privateNames = (process.env.KIT_PRIVATE_NAMES || "").split(",").map((n) => n.trim().toLowerCase()).filter(Boolean);
  c.ok(privateNames.every((n) => !all.toLowerCase().includes(n)), `the page names none of the ${privateNames.length} private names given in KIT_PRIVATE_NAMES`);
  c.ok(!b.errors.some(e => e.startsWith("exception:")), "no script exceptions", b.errors.filter(e => e.startsWith("exception:")).join(" | "));
  await b.viewport(400, 900, true); await go();
  c.ok(await b.eval(`document.documentElement.scrollWidth <= innerWidth + 1`), "no horizontal overflow at phone width", await b.eval(`document.documentElement.scrollWidth`));
} catch (e) { console.log("HARNESS ERROR", e.message); c.ok(false, "harness ran to completion", e.message); }
const f = c.done(); b?.close(); srv.kill(); process.exit(f ? 1 : 0);
