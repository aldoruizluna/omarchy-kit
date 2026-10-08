import { launch, checker } from "./cdp.mjs";
import { mkdirSync } from "node:fs";
if ((process.argv[2] || "").startsWith("-")) { console.log("usage: node test/verify-keyboard.mjs [output-folder]   (drives the running portal in a browser; see README)"); process.exit(["-h", "--help"].includes(process.argv[2]) ? 0 : 2); }
const OUT = process.argv[2] || "/tmp/kbshots"; mkdirSync(OUT, { recursive: true });
const URL = process.env.BASE ? process.env.BASE + "/keyboard" : "file://" + process.cwd().replace(/\/test$/, "") + "/keyboard.html";
const c = checker("keyboard.html"); const b = await launch({ width: 1280, height: 1000 });
try {
  await b.goto(URL); await b.sleep(600); await b.eval(`document.getElementById("stage").scrollIntoView()`); await b.sleep(200);
  await b.shot(`${OUT}/01-default.png`);
  console.log("structure");
  const n = await b.eval(`document.querySelectorAll('.key').length`);
  c.ok(n >= 70, `keys rendered (${n})`);
  c.ok(await b.eval(`!!document.querySelector('.tp-wrap')`), "trackpad rendered");
  c.ok(await b.eval(`!!document.querySelector('.lid .screen')`), "lid + screen rendered");
  c.ok(await b.eval(`getComputedStyle(document.querySelector('.board')).transformStyle==='preserve-3d'`), "board is preserve-3d");
  c.ok(await b.eval(`document.querySelectorAll('.key.has').length>10`), "Super layer lights up many keys", await b.eval(`document.querySelectorAll('.key.has').length`));
  c.ok(await b.eval(`document.documentElement.scrollWidth<=innerWidth`), "no horizontal page overflow");

  console.log("hover");
  const w = await b.center('.key[data-id="KeyW"] .f-top');
  c.ok(!!w, "W key has a hit-testable face", JSON.stringify(w));
  await b.move(w.x, w.y);
  c.ok(await b.eval(`document.querySelector('.key[data-id="KeyW"]').classList.contains('hover')`), "hover class set on W");
  c.ok(await b.eval(`document.getElementById('tip').classList.contains('on')`), "tooltip visible");
  c.ok(await b.eval(`document.getElementById('tip').innerText.includes('Close window')`), "tooltip lists Super+W = Close window", await b.eval(`document.getElementById('tip').innerText`));
  c.ok(await b.eval(`document.querySelector('.screen .hud')?.innerText.includes('Close window')`), "laptop screen HUD shows the binding");
  await b.shot(`${OUT}/02-hover-W.png`);

  console.log("layers");
  const ctl = await b.center('.key[data-id="ControlLeft"] .f-top');
  await b.click(ctl.x, ctl.y);
  c.ok(await b.eval(`layerKey()==='SUPER+CTRL'`), "clicking ⌃ switches to Super+Ctrl", await b.eval(`layerKey()`));
  c.ok(await b.eval(`document.querySelector('.key[data-id="ControlLeft"]').classList.contains('mod-on')`), "⌃ key lit");
  c.ok(await b.eval(`document.querySelector('[data-l="SUPER+CTRL"]').getAttribute('aria-pressed')==='true'`), "chip reflects layer");
  await b.shot(`${OUT}/03-super-ctrl.png`);
  await b.eval(`document.querySelector('[data-l="SUPER+SHIFT"]').click()`);
  c.ok(await b.eval(`layerKey()==='SUPER+SHIFT'&&document.querySelectorAll('.key.has').length>8`), "chip switches to Super+Shift");

  console.log("details + chord preview");
  const k = await b.center('.key[data-id="KeyK"] .f-top'); await b.click(k.x, k.y);
  c.ok(await b.eval(`selKey==='KeyK'&&document.getElementById('info').innerText.includes('Kagi')`), "click K → info lists Super+Shift+K Kagi");
  await b.eval(`document.querySelector('#info [data-chord]').dispatchEvent(new MouseEvent('mouseover',{bubbles:true}))`);
  c.ok(await b.eval(`document.querySelectorAll('.key.chord').length>=2`), "hovering a binding animates its chord on the keyboard", await b.eval(`document.querySelectorAll('.key.chord').length`));
  await b.eval(`document.body.dispatchEvent(new MouseEvent('mouseover',{bubbles:true}))`);

  console.log("3D interaction");
  const before = await b.eval(`({rx,rz,zoom})`);
  await b.drag(300, 520, 520, 430);
  const after = await b.eval(`({rx,rz,zoom})`);
  c.ok(after.rz > before.rz + 10, "drag right rotates around Z", JSON.stringify({ before, after }));
  c.ok(after.rx > before.rx + 10, "drag up tilts the board back (rx grows)", JSON.stringify({ before, after }));
  await b.shot(`${OUT}/04-rotated.png`);
  for(let i=0;i<3;i++) await b.wheel(640, 500, -300);
  c.ok(await b.eval(`zoom`) > 1.1, "wheel up zooms in", await b.eval(`zoom`));
  await b.eval(`document.getElementById("stage").scrollIntoView()`); await b.sleep(150);
  const sc = await b.eval(`(()=>{const r=document.getElementById("stage").getBoundingClientRect();return {x:r.left+30,y:Math.min(innerHeight-30,r.top+60)}})()`);
  await b.dblclick(sc.x, sc.y); await b.sleep(700);
  c.ok(await b.eval(`rx===36&&rz===0&&zoom===1`), "double-click resets the view");
  for (const v of ["top", "low", "screen"]) { await b.eval(`document.querySelector('[data-view="${v}"]').click()`); await b.sleep(700); await b.shot(`${OUT}/05-view-${v}.png`); }
  await b.eval(`document.querySelector('[data-view="tilt"]').click()`); await b.sleep(600);

  console.log("angle sweep (nothing clipped by the stage)");
  const clipped = await b.eval(`(()=>{const bad=[];for(const x of [0,20,40,60,75,86])for(const z of [-75,-45,-20,0,20,45,75]){rx=x;rz=z;zoom=1;applyTilt(true);
    const s=document.getElementById('stage').getBoundingClientRect();
    for(const el of [document.querySelector('.case'),document.querySelector('.lid')]){const r=el.getBoundingClientRect();
      if(r.left<s.left-1||r.right>s.right+1||r.top<s.top-1||r.bottom>s.bottom+1)bad.push(x+'/'+z+' '+el.className)}}
    rx=36;rz=0;applyTilt(true);return bad})()`);
  c.ok(clipped.length === 0, "laptop stays inside the stage at all 42 angles", clipped.slice(0, 6).join(", "));
  c.ok(await b.eval(`document.querySelectorAll('.rowplane').length===6&&document.querySelectorAll('.rowplane .key').length===78`), "keys live in 6 row planes (no per-key 3D boxes)");
  console.log("explode + sway");
  await b.eval(`document.getElementById('bExplode').click()`); await b.sleep(700);
  c.ok(await b.eval(`document.getElementById('board').classList.contains('exploded')`), "explode toggles");
  const zx = await b.eval(`getComputedStyle(document.querySelectorAll('.rowplane')[0]).transform`);
  const zx2 = await b.eval(`getComputedStyle(document.querySelectorAll('.rowplane')[5]).transform`);
  c.ok(zx !== zx2, "rows lift to different heights when exploded");
  await b.shot(`${OUT}/06-exploded.png`);
  await b.eval(`document.getElementById('bExplode').click()`);
  const r0 = await b.eval(`rz`); await b.eval(`document.getElementById('bSway').click()`); await b.sleep(700);
  c.ok(Math.abs(await b.eval(`rz`) - r0) > 0.5, "sway animates rotation"); await b.eval(`document.getElementById('bSway').click()`);
  await b.eval(`resetView()`); await b.sleep(700);

  console.log("physical keys + trackpad");
  await b.key("KeyK", "k", "down");
  c.ok(await b.eval(`document.querySelector('.key[data-id="KeyK"]').classList.contains('hit')`), "pressing K lights the K key");
  await b.key("KeyK", "k", "up");
  c.ok(await b.eval(`!document.querySelector('.key[data-id="KeyK"]').classList.contains('hit')`), "released key returns");
  const tp = await b.center('.tp-wrap'); await b.click(tp.x, tp.y);
  c.ok(await b.eval(`selKey==='Trackpad'&&document.getElementById('info').innerText.includes('Switch spaces')`), "trackpad click shows gestures");
  await b.shot(`${OUT}/07-trackpad.png`);

  console.log("language + search + categories");
  await b.eval(`document.getElementById('bLang').click()`);
  c.ok(await b.eval(`document.querySelector('h1').innerText.startsWith('Teclado')`), "ES toggle translates the title");
  c.ok(await b.eval(`document.getElementById('info').innerText.includes('Cambiar de espacio')`), "ES translates the trackpad panel");
  await b.eval(`document.getElementById('bLang').click()`);
  await b.eval(`(()=>{const i=document.getElementById('q');i.value='screenshot';i.dispatchEvent(new Event('input'))})()`);
  c.ok(await b.eval(`layerKey()==='SUPER+ALT'&&document.querySelector('.key[data-id="KeyP"]').classList.contains('has')`), "search 'screenshot' jumps to Super+Alt and lights P", await b.eval(`layerKey()`));
  await b.eval(`(()=>{const i=document.getElementById('q');i.value='';i.dispatchEvent(new Event('input'))})()`);
  await b.eval(`document.querySelector('[data-c="windows"]').click()`);
  c.ok(await b.eval(`hidden.has('windows')`), "category filter hides windows bindings");
  await b.eval(`document.querySelector('[data-c="windows"]').click()`);

  console.log("themes + responsive");
  await b.scheme("light"); await b.sleep(400); await b.shot(`${OUT}/08-light.png`);
  await b.scheme("dark");
  await b.viewport(400, 900, true); await b.sleep(900);
  c.ok(await b.eval(`document.documentElement.scrollWidth<=innerWidth+1`), "no horizontal overflow at 400px", await b.eval(`document.documentElement.scrollWidth+' vs '+innerWidth`));
  c.ok(await b.eval(`+document.getElementById('board').dataset.cw*zoom<=document.getElementById('stage').clientWidth+2`), "board fits the stage at 400px");
  await b.shot(`${OUT}/09-mobile.png`);
  process.env.CDP_ATTACH ? await b.resetViewport() : await b.viewport(1280, 1000);

  console.log("performance + errors");
  const ms = await b.eval(`(()=>{const t=performance.now();for(let i=0;i<60;i++){rz=Math.sin(i)*20;applyTilt(false);document.body.offsetHeight}return (performance.now()-t)/60})()`);
  c.ok(ms < 30, `drag/sway frame cost ${ms.toFixed(2)} ms (style+layout, software rendering)`);
  const nodes = await b.eval(`document.querySelectorAll('#board *').length`); console.log("  info  DOM nodes in 3D board:", nodes);
  c.ok(b.errors.length === 0, "no console errors / exceptions", b.errors.join(" | "));
} catch (e) { console.log("HARNESS ERROR", e.message); c.ok(false, "harness ran to completion", e.message); }
const fails = c.done(); b.close(); process.exit(fails ? 1 : 0);
