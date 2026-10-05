// Minimal Chrome DevTools Protocol driver (no dependencies; Node 22+ has WebSocket built in).
import { spawn } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

// CDP_ATTACH=<port> attaches to an already-running browser (e.g. a real GPU Brave window) instead of
// spawning headless Chromium; the browser is left running afterwards.
export async function launch({ width = 1280, height = 1000, port = 9333 } = {}) {
  const attach = process.env.CDP_ATTACH ? +process.env.CDP_ATTACH : 0;
  if (attach) port = attach;
  const dir = attach ? "" : mkdtempSync(join(tmpdir(), "cdp-"));
  const proc = attach ? { kill() {} } : spawn("chromium", ["--headless=new", "--disable-gpu", "--no-sandbox", `--remote-debugging-port=${port}`,
    `--user-data-dir=${dir}`, `--window-size=${width},${height}`, "about:blank"], { stdio: "ignore" });
  let tabs;
  for (let i = 0; i < 50; i++) {
    try { tabs = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); if (tabs.length) break; } catch {}
    await new Promise(r => setTimeout(r, 200));
  }
  const page = tabs.find(t => t.type === "page" && (!attach || t.url.includes("8787"))) || tabs.find(t => t.type === "page");
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  await new Promise(r => (ws.onopen = r));
  let id = 0; const pending = new Map(); const errors = [];
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (globalThis.__cdpHook) globalThis.__cdpHook(m);
    if (m.id && pending.has(m.id)) { const { res, rej } = pending.get(m.id); pending.delete(m.id); m.error ? rej(new Error(m.error.message)) : res(m.result); }
    else if (m.method === "Runtime.exceptionThrown") errors.push("exception: " + (m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text));
    else if (m.method === "Runtime.consoleAPICalled" && m.params.type === "error") errors.push("console.error: " + m.params.args.map(a => a.value ?? a.description).join(" "));
    else if (m.method === "Log.entryAdded" && m.params.entry.level === "error") errors.push("log: " + m.params.entry.text + " " + (m.params.entry.url || ""));
  };
  const send = (method, params = {}) => new Promise((res, rej) => { const i = ++id; pending.set(i, { res, rej }); ws.send(JSON.stringify({ id: i, method, params })); });
  await send("Page.enable"); await send("Runtime.enable"); await send("Log.enable");
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const api = {
    errors, send, sleep,
    async goto(url) { await send("Page.navigate", { url }); await sleep(900); },
    async eval(expr) {
      const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true });
      if (r.exceptionDetails) throw new Error("eval failed: " + (r.exceptionDetails.exception?.description || r.exceptionDetails.text) + "\n  in: " + expr.slice(0, 120));
      return r.result.value;
    },
    async shot(path, { clip } = {}) { const r = await send("Page.captureScreenshot", { format: "png", ...(clip ? { clip: { ...clip, scale: 1 } } : {}) }); writeFileSync(path, Buffer.from(r.data, "base64")); },
    async resetViewport() { await send("Emulation.clearDeviceMetricsOverride"); await sleep(500); },
    async viewport(w, h, mobile = false) { await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile }); await sleep(500); },
    async scheme(s) { await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-color-scheme", value: s }] }); await sleep(200); },
    async move(x, y) { await send("Input.dispatchMouseEvent", { type: "mouseMoved", x, y }); await sleep(120); },
    async click(x, y) { await send("Input.dispatchMouseEvent", { type: "mouseMoved", x, y }); await send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount: 1 }); await send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount: 1 }); await sleep(250); },
    async dblclick(x, y) { for (const c of [1, 2]) { await send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount: c }); await send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount: c }); } await sleep(300); },
    async drag(x1, y1, x2, y2, steps = 8) {
      await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: x1, y: y1 });
      await send("Input.dispatchMouseEvent", { type: "mousePressed", x: x1, y: y1, button: "left", clickCount: 1 });
      for (let i = 1; i <= steps; i++) { await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: x1 + (x2 - x1) * i / steps, y: y1 + (y2 - y1) * i / steps, button: "left", buttons: 1 }); await sleep(16); }
      await send("Input.dispatchMouseEvent", { type: "mouseReleased", x: x2, y: y2, button: "left", clickCount: 1 }); await sleep(900);
    },
    async wheel(x, y, dy) { await send("Input.dispatchMouseEvent", { type: "mouseWheel", x, y, deltaX: 0, deltaY: dy }); await sleep(450); },
    async key(code, key, type = "both") {
      const base = { code, key, windowsVirtualKeyCode: key.length === 1 ? key.toUpperCase().charCodeAt(0) : 0 };
      if (type !== "up") await send("Input.dispatchKeyEvent", { type: "rawKeyDown", ...base });
      if (type !== "down") await send("Input.dispatchKeyEvent", { type: "keyUp", ...base });
      await sleep(80);
    },
    // centre of an element's visible top face, in viewport coordinates
    async center(sel) { await api.eval(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(e)e.scrollIntoView({block:'center'})})()`); await sleep(120); return api.eval(`(()=>{const e=document.querySelector(${JSON.stringify(sel)});if(!e)return null;const r=e.getBoundingClientRect();return {x:r.x+r.width/2,y:r.y+r.height/2,w:r.width,h:r.height}})()`); },
    close() { try { ws.close(); } catch {} proc.kill(); },
  };
  return api;
}

export function checker(name) {
  let pass = 0, fail = 0;
  return {
    ok(cond, msg, detail = "") { cond ? pass++ : fail++; console.log(`${cond ? "  PASS" : "  FAIL"}  ${msg}${!cond && detail ? "  → " + detail : ""}`); },
    done() { console.log(`\n${name}: ${pass} passed, ${fail} failed`); return fail; },
  };
}
