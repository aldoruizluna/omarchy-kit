// End-to-end checks for the learning portal, against the live service (http://127.0.0.1:8787).
// Never clicks "Show me" (that would open the real Omarchy menu on the user's screen).
import { launch, checker } from "./cdp.mjs";
import { mkdirSync } from "node:fs";
const OUT = process.argv[2] || "/tmp/portalshots"; mkdirSync(OUT, { recursive: true });
const BASE = process.env.BASE || "http://127.0.0.1:8787";
const c = checker("portal"); const b = await launch({ width: 1280, height: 1000 });
const go = async (p) => { await b.goto(BASE + p); await b.sleep(700); };
try {
  console.log("every page: loads, shared nav, no errors");
  for (const p of ["/", "/learn", "/mac", "/macbook", "/system", "/games", "/reference", "/cheatsheet", "/keyboard", "/trackpad", "/apps", "/setup"]) {
    const before = b.errors.length; await go(p);
    const n = await b.eval(`document.querySelectorAll('#top a').length`);
    const cur = await b.eval(`document.querySelector('#top a[aria-current=page]')?.getAttribute('href')`);
    const themed = await b.eval(`getComputedStyle(document.documentElement).getPropertyValue('--acc-fill').trim()!=='' && !!document.querySelector('.kit-search')`);
    c.ok(n === 12 && cur === p && themed && b.errors.length === before, `${p}: 12 nav links, '${p}' marked current, Omarchy theme + search button, no errors`, `links=${n} current=${cur} themed=${themed} errors=${b.errors.slice(before).join(" | ")}`);
  }
  console.log("Ctrl+K palette, XP, System page");
  await go("/keyboard");
  await b.send("Input.dispatchKeyEvent", { type: "rawKeyDown", key: "k", code: "KeyK", modifiers: 2, windowsVirtualKeyCode: 75 }); await b.sleep(600);
  c.ok(await b.eval(`!!document.querySelector('.kp input') && document.activeElement===document.querySelector('.kp input')`), "Ctrl+K opens the palette with the search box focused");
  await b.eval(`(()=>{const i=document.querySelector('.kp input');i.value='spotlight';i.dispatchEvent(new Event('input'))})()`); await b.sleep(200);
  c.ok(await b.eval(`[...document.querySelectorAll('.kp-item .t')].some(x=>/Spotlight/.test(x.textContent))`), "palette finds the Spotlight lesson and Mac translation");
  await b.eval(`(()=>{const i=document.querySelector('.kp input');i.value='screenshot';i.dispatchEvent(new Event('input'))})()`); await b.sleep(200);
  c.ok(await b.eval(`document.querySelectorAll('.kp-item kbd').length>0`), "palette shows shortcut keys");
  await b.eval(`(()=>{const i=document.querySelector('.kp input');i.value='nord';i.dispatchEvent(new Event('input'))})()`); await b.sleep(200);
  c.ok(await b.eval(`[...document.querySelectorAll('.kp-group')].some(g=>/Themes/.test(g.textContent))`), "palette lists Omarchy themes (never applied by this test)");
  await b.send("Input.dispatchKeyEvent", { type: "rawKeyDown", key: "Escape", code: "Escape", windowsVirtualKeyCode: 27 }); await b.sleep(200);
  c.ok(await b.eval(`!document.querySelector('.kp-back')`), "Esc closes the palette");
  c.ok(await b.eval(`/Lv \\d/.test(document.getElementById('kitXp').textContent)`), "XP chip shows the level");
  await go("/system"); await b.sleep(2500);
  c.ok(await b.eval(`document.querySelectorAll('.chart svg path').length>=6`), "System page draws its graphs", await b.eval(`document.querySelectorAll('.chart svg path').length`));
  c.ok(await b.eval(`/°C/.test(document.getElementById('heroT').textContent) && document.querySelectorAll('.fact').length===10`), "System page hero temperature + 10 facts");
  c.ok(await b.eval(`document.querySelectorAll('#topTbl tr').length>1`), "busiest-apps table filled");
  await go("/games"); await b.sleep(2500);
  c.ok(await b.eval(`document.querySelectorAll('#sys .card').length===20`), "Games page lists the 20 planned systems", await b.eval(`document.querySelectorAll('#sys .card').length`));
  c.ok(await b.eval(`/budget/.test(document.getElementById('lib').innerText) && document.querySelectorAll('#bios tr').length>3`), "Games page shows the budget and BIOS checklist");
  console.log("language");
  await go("/mac"); await b.eval(`localStorage.setItem('lang','en')`); await go("/mac");
  await b.eval(`document.getElementById('bLang').click()`); await b.sleep(200);
  c.ok(await b.eval(`document.querySelector('h1').textContent.includes('Viniendo') && [...document.querySelectorAll('#top a')].some(a=>a.textContent==='Aprender')`), "ES toggle translates page and nav");
  await b.eval(`document.getElementById('bLang').click()`);

  console.log("start page");
  await b.eval(`localStorage.removeItem('kit-progress')`); await go("/"); await b.sleep(1200);
  c.ok(await b.eval(`document.querySelectorAll('#nowList dt').length>=5`), "live 'your machine' panel filled", await b.eval(`document.getElementById('nowList').innerText.slice(0,120)`));
  c.ok(await b.eval(`document.querySelectorAll('#levels .level').length===5`), "5 levels in the learning path");
  c.ok(await b.eval(`document.getElementById('ctaBtn').textContent.includes('first lesson')`), "fresh visitor is invited to the first lesson");
  await b.shot(`${OUT}/01-start.png`);

  console.log("learn: verification engine (synthetic desktop states)");
  await go("/learn#super"); await b.sleep(600);
  c.ok(await b.eval(`document.querySelectorAll('#side a').length===Portal.data.levels.reduce((n,l)=>n+l.lessons.length,0)`), "every lesson is listed", await b.eval(`document.querySelectorAll('#side a').length+' of '+Portal.data.levels.reduce((n,l)=>n+l.lessons.length,0)`));
  c.ok(await b.eval(`document.getElementById('liveNote').innerText.includes('Live mode')`), "live mode active when served by the helper");
  const unit = await b.eval(`(()=>{
    const base={ws:1,special:"",active:{addr:"a",floating:false,fullscreen:0,grouped:0},clients:[{addr:"a",class:"org.omarchy.terminal",ws:1}],theme:"Tokyo Night",volume:"0.5",shot:0};
    const s=(p)=>Object.assign(JSON.parse(JSON.stringify(base)),p);
    const r={};
    r.newWindow=CHECKS.newWindow(s({clients:[...base.clients,{addr:"b",class:"foot",ws:1}]}),base,{cls:"terminal|foot"});
    r.newWindowNo=!CHECKS.newWindow(s({clients:[...base.clients,{addr:"b",class:"brave",ws:1}]}),base,{cls:"terminal|foot"});
    r.close=CHECKS.closeWindow(s({clients:[]}),base);
    r.ws=CHECKS.wsIs(s({ws:2}),base,{ws:2});
    r.moved=CHECKS.moved(s({clients:[{addr:"a",class:"x",ws:3}]}),base);
    r.float=CHECKS.floating(s({active:{...base.active,floating:true}}),base,{v:true});
    r.full=CHECKS.fullscreen(s({active:{...base.active,fullscreen:1}}),base,{v:true});
    r.special=CHECKS.special(s({special:"special:scratchpad"}),base,{v:true});
    r.toSpecial=CHECKS.toSpecial(s({clients:[{addr:"a",class:"x",ws:-98}]}),base);
    r.theme=CHECKS.themeChanged(s({theme:"Nord"}),base);
    r.shot=CHECKS.newShot(s({shot:123}),base);
    return r})()`);
  for (const [k, v] of Object.entries(unit)) c.ok(v === true, `check '${k}' behaves correctly`);

  console.log("learn: complete a real lesson (accents)");
  await go("/learn#accents"); await b.sleep(700);
  c.ok(await b.eval(`!!document.getElementById('box')`), "accents lesson shows a typing box");
  await b.eval(`(()=>{const x=document.getElementById('box');x.value='¿Año? ¡Sí!';x.dispatchEvent(new Event('input'))})()`); await b.sleep(400);
  c.ok(await b.eval(`document.getElementById('party').classList.contains('on')`), "typing ¿Año? ¡Sí! completes the lesson");
  c.ok(await b.eval(`JSON.parse(localStorage.getItem('kit-progress')).accents==='done'`), "progress saved");
  await b.shot(`${OUT}/02-learn-done.png`);
  await go("/"); await b.sleep(500);
  c.ok(await b.eval(`document.getElementById('levels').innerText.includes('1/'+Portal.data.levels[2].lessons.length)`), "Start page shows level progress (1 done in Everyday tasks)", await b.eval(`document.getElementById('levels').innerText.replace(/\\n/g,' ')`));
  await go("/learn#spaces"); await b.sleep(600);
  c.ok(await b.eval(`document.querySelector('.step.watching')!==null`), "a desktop-verified step shows 'watching'");
  await b.shot(`${OUT}/03-learn-watching.png`);

  console.log("from macOS");
  await go("/mac");
  c.ok(await b.eval(`document.querySelectorAll('.t').length===Portal.data.mac.reduce((n,g)=>n+g[2].length,0)`), "every macOS translation is listed", await b.eval(`document.querySelectorAll('.t').length+' of '+Portal.data.mac.reduce((n,g)=>n+g[2].length,0)`));
  await b.eval(`(()=>{const i=document.getElementById('q');i.value='screenshot';i.dispatchEvent(new Event('input'))})()`);
  c.ok(await b.eval(`document.querySelectorAll('.t').length>=2&&document.querySelectorAll('.t').length<8`), "search narrows the list", await b.eval(`document.querySelectorAll('.t').length`));
  await b.eval(`(()=>{const i=document.getElementById('q');i.value='';i.dispatchEvent(new Event('input'))})()`);
  await b.eval(`document.querySelector('[data-how=different]').click()`);
  c.ok(await b.eval(`[...document.querySelectorAll('.t .badge')].every(x=>x.className.includes('how-different'))`), "'new concept' filter works");
  c.ok(await b.eval(`!document.body.innerText.includes('not bound')`), "every Mac translation resolves to a real shortcut");
  await b.eval(`document.querySelector('[data-how=all]').click()`); await b.shot(`${OUT}/04-mac.png`);

  console.log("your MacBook");
  await go("/macbook"); await b.sleep(1200);
  c.ok(await b.eval(`document.querySelectorAll('.hw').length===13`), "13 hardware items");
  c.ok(await b.eval(`(()=>{const r={bad:0,warn:1,ok:2};const v=[...document.querySelectorAll('.hw .dot')].map(d=>r[['bad','warn','ok'].find(k=>d.classList.contains(k))]);return v.every((x,i)=>i===0||v[i-1]<=x)})()`), "problems are listed first");
  c.ok(await b.eval(`[...document.querySelectorAll('.livebox')].some(l=>/Intel|NVIDIA/.test(l.innerText)&&l.innerText.includes('°C'))`), "live GPU/temperature readings shown", await b.eval(`[...document.querySelectorAll('.livebox')].map(l=>l.innerText).join(' | ')`));
  await b.shot(`${OUT}/05-macbook.png`);
  c.ok(await b.eval(`[...document.querySelectorAll('.livebox')].some(l=>l.innerText.includes('Auto profile'))`), "battery box shows whether the power profile follows the charger");
  c.ok(await b.eval(`[...document.querySelectorAll('.livebox')].some(l=>l.innerText.includes('Sleeps seen'))`), "sleep box shows the real suspend history");

  console.log("setup log");
  await go("/setup"); await b.sleep(600);
  c.ok(await b.eval(`D.status.every(([,,rows])=>rows.every(r=>D.checks[r[0]]))`), "every status row has a live check (none stuck on 'manual check')", await b.eval(`JSON.stringify(D.status.flatMap(([,,rows])=>rows.map(r=>r[0])).filter(k=>!D.checks[k]))`));
  c.ok(await b.eval(`(t=>t.includes('mac habits')&&t.includes('backups'))(document.getElementById('status').innerText.toLowerCase())`), "Mac habits and Backups groups are listed");
  c.ok(await b.eval(`D.todo.length>=6&&document.querySelectorAll('#todo .card').length===D.todo.length&&[...document.querySelectorAll('#todo .badge')].length===D.todo.length`), "every open item is listed with who it waits on", await b.eval(`document.querySelectorAll('#todo .card').length+' of '+D.todo.length`));
  c.ok(await b.eval(`document.querySelectorAll('#skipped .card').length===D.skipped.length&&D.skipped.length>=3`), "'looked at and left alone' is listed");
  c.ok(await b.eval(`D.log.every(e=>e.length===5&&e[2]&&e[3])`), "every log entry has English and Spanish text");
  c.ok(await b.eval(`D.todo.every(t=>t[3]&&t[4])&&D.skipped.every(t=>t[2]&&t[3])`), "every open item has English and Spanish text");
  await b.eval(`document.getElementById('bLang').click()`); await b.sleep(200);
  c.ok(await b.eval(`document.getElementById('todo').innerText.includes('Mide cuánta batería')&&document.getElementById('skipped').innerText.includes('Fuente del sistema')`), "Spanish switch translates the new sections");
  await b.eval(`document.getElementById('bLang').click()`); await b.sleep(200);
  await b.shot(`${OUT}/05b-setup.png`);

  console.log("reference");
  await go("/reference");
  c.ok(await b.eval(`document.querySelectorAll('#p-menu .tree > li').length===10`), "menu tree has the 10 top-level sections");
  c.ok(await b.eval(`document.querySelectorAll('#p-menu [data-menu]').length>=10`), "'Show me' buttons present");
  await b.eval(`document.querySelector('[data-tab=cmds]').click()`); await b.sleep(200);
  c.ok(await b.eval(`document.querySelectorAll('.cmdrow').length===200`), "commands tab lists commands");
  await b.eval(`(()=>{const i=document.getElementById('cq');i.value='theme';i.dispatchEvent(new Event('input'))})()`);
  c.ok(await b.eval(`document.querySelectorAll('.cmdrow').length>3&&document.querySelectorAll('.cmdrow').length<60`), "command search works", await b.eval(`document.querySelectorAll('.cmdrow').length`));
  await b.eval(`document.querySelector('[data-tab=gloss]').click()`);
  c.ok(await b.eval(`document.querySelectorAll('.gl dt').length===Portal.data.glossary.length`), "every glossary term is listed", await b.eval(`document.querySelectorAll('.gl dt').length+' of '+Portal.data.glossary.length`));
  await b.eval(`document.querySelector('[data-tab=themes]').click()`);
  c.ok(await b.eval(`document.querySelectorAll('.theme').length===22&&document.querySelectorAll('.theme.cur').length===1`), "22 themes, current one highlighted");
  await b.eval(`document.querySelector('[data-tab=menu]').click()`); await b.shot(`${OUT}/06-reference.png`);

  console.log("phone width + light theme");
  await b.viewport(400, 900, true);
  for (const p of ["/", "/learn#super", "/mac", "/macbook", "/reference"]) { await go(p); c.ok(await b.eval(`document.documentElement.scrollWidth<=innerWidth+1`), `${p}: no horizontal overflow at 400px`, await b.eval(`document.documentElement.scrollWidth`)); }
  await go("/"); await b.shot(`${OUT}/07-mobile.png`);
  await b.viewport(1280, 1000); await b.scheme("light"); await go("/learn#accents"); await b.shot(`${OUT}/08-light.png`); await b.scheme("dark");
  await b.eval(`localStorage.removeItem('kit-progress')`);
  c.ok(b.errors.length === 0, "no console errors anywhere", b.errors.join(" | "));
} catch (e) { console.log("HARNESS ERROR", e.message); c.ok(false, "harness ran to completion", e.message); }
const f = c.done(); b.close(); process.exit(f ? 1 : 0);
