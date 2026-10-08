import { launch, checker } from "./cdp.mjs";
import { mkdirSync } from "node:fs";
if ((process.argv[2] || "").startsWith("-")) { console.log("usage: node test/verify-trackpad.mjs [output-folder]   (drives the running portal in a browser; see README)"); process.exit(["-h", "--help"].includes(process.argv[2]) ? 0 : 2); }
const OUT = process.argv[2] || "/tmp/tpshots"; mkdirSync(OUT, { recursive: true });
const URL = process.env.BASE ? process.env.BASE + "/trackpad" : "file://" + process.cwd().replace(/\/test$/, "") + "/trackpad.html";
const c = checker("trackpad.html"); const b = await launch({ width: 1280, height: 1000 });
const lastResult = () => b.eval(`JSON.stringify(lastResult)`);
try {
  await b.goto(URL); await b.sleep(700);
  await b.shot(`${OUT}/01-default.png`);
  console.log("structure");
  c.ok(await b.eval(`!!document.querySelector('.pad')`), "trackpad rendered");
  c.ok(await b.eval(`!!document.querySelector('.lid .screen')`), "lid + screen rendered");
  c.ok(await b.eval(`document.querySelectorAll('.card').length===GEST.length`), "one card per gesture", await b.eval(`document.querySelectorAll('.card').length+'/'+GEST.length`));
  c.ok(await b.eval(`document.querySelectorAll('.dots b').length===4`), "four finger dots");
  c.ok(await b.eval(`document.documentElement.scrollWidth<=innerWidth`), "no horizontal overflow");
  c.ok(await b.eval(`document.getElementById('info').innerText.includes('hl.gesture')`), "info panel shows the Hyprland config line");
  c.ok(await b.eval(`getComputedStyle(document.querySelector('.board')).transformStyle==='preserve-3d'`), "board is preserve-3d");

  console.log("playing gestures from the cards");
  const play = async (id) => { await b.eval(`document.querySelector('[data-g="${id}"]').click()`); await b.sleep(1700); };
  const DRAG3 = await b.eval(`DRAG3`); console.log(`  (page built for three fingers = ${DRAG3 ? "drag" : "swipe"})`);
  c.ok(await b.eval(`selId===(DRAG3?'swipe4':'swipe3')`), "starts on the space swipe");
  c.ok(await b.eval(`GEST.find(g=>g.id==='drag3').st===(DRAG3?'cfg':'opt')&&GEST.find(g=>g.id==='swipe3').st===(DRAG3?'opt':'cfg')`), "exactly one of the three-finger swipe / drag is configured, the other optional");
  await play("up4");
  c.ok(await b.eval(`document.querySelector('.card.sel')?.dataset.g==='up4'`), "clicking a card selects it");
  c.ok(await b.eval(`dots[0].getAnimations().length>0&&dots[3].getAnimations().length>0`), "4 finger dots animate for the 4-finger gesture");
  c.ok(await b.eval(`dots[4]===undefined`) , "only four dots exist");
  c.ok(await b.eval(`document.getElementById('ovMenu').classList.contains('on')`), "screen shows the Omarchy menu for swipe up");
  await b.shot(`${OUT}/02-up4-menu.png`);
  await play("pinch4"); c.ok(await b.eval(`document.getElementById('ovApps').classList.contains('on')`), "screen shows the apps grid for pinch");
  await b.shot(`${OUT}/03-pinch-apps.png`);
  await play("down4"); c.ok(await b.eval(`document.getElementById('scratch').classList.contains('on')`), "screen slides the scratchpad for swipe down");
  await play("click2"); c.ok(await b.eval(`document.getElementById('ctx').classList.contains('on')`), "two-finger click opens a context menu");
  await play("smart"); c.ok(await b.eval(`document.getElementById('note').classList.contains('on')`), "unavailable gesture says so on the screen");
  const ws0 = await b.eval(`wsNow`); await play("swipe4");
  c.ok(await b.eval(`wsNow`) !== ws0, "4-finger swipe changes the active space", `${ws0} -> ${await b.eval(`wsNow`)}`);
  await play("drag3"); c.ok(await b.eval(`document.querySelector('.swin').style.transform.includes('translate')`), "three-finger drag moves a window on the screen");

  console.log("filters");
  await b.eval(`document.querySelector('[data-filter="no"]').click()`);
  c.ok(await b.eval(`document.querySelectorAll('.card').length===GEST.filter(g=>g.st==='no').length`), "filter shows only 'not available'");
  await b.eval(`document.querySelector('[data-filter="cfg"]').click()`);
  c.ok(await b.eval(`[...document.querySelectorAll('.card')].every(x=>GEST.find(g=>g.id===x.dataset.g).st==='cfg')`), "filter shows only 'configured'");
  await b.eval(`document.querySelector('[data-filter="all"]').click()`);

  console.log("try it (drag on the trackpad)");
  await b.eval(`document.getElementById('bTry').click()`);
  c.ok(await b.eval(`!document.getElementById('fingBtns').hidden&&padEl.classList.contains('try')`), "Try it reveals finger buttons and arms the pad");
  const tp = await b.center('.pad');
  c.ok(await b.eval(`padPoint({clientX:${tp.x},clientY:${tp.y}})`), "pointer over the pad is recognised");
  const swipe = async (n, dx, dy) => { await b.eval(`document.querySelector('[data-f="${n}"]').click()`); await b.drag(tp.x, tp.y, tp.x + dx, tp.y + dy, 6); };
  const ws1 = await b.eval(`wsNow`);
  await swipe(4, -120, 0);
  c.ok(await b.eval(`lastResult&&lastResult.id==='swipe4'&&lastResult.dir==='l'`), "4 fingers ← performs 'swipe4'", await lastResult());
  c.ok(await b.eval(`wsNow`) === (ws1 % 9) + 1, "…and goes to the next space", `${ws1} -> ${await b.eval(`wsNow`)}`);
  await b.shot(`${OUT}/04-try-swipe.png`);
  await swipe(4, 120, 0); c.ok(await b.eval(`lastResult.id==='swipe4'&&lastResult.dir==='r'&&wsNow===${ws1}`), "4 fingers → returns to the previous space", await lastResult());
  await swipe(4, 0, -90); c.ok(await b.eval(`lastResult.id==='up4'&&document.getElementById('ovMenu').classList.contains('on')`), "4 fingers ↑ opens the Omarchy menu", await lastResult());
  await swipe(4, 0, 90); c.ok(await b.eval(`lastResult.id==='down4'&&document.getElementById('scratch').classList.contains('on')`), "4 fingers ↓ toggles the scratchpad", await lastResult());
  await swipe(2, 0, -90); c.ok(await b.eval(`lastResult.id==='scroll2'`), "2 fingers vertical scrolls", await lastResult());
  await swipe(3, 80, 40);
  c.ok(await b.eval(`lastResult.id===(DRAG3?'drag3':'swipe3')&&(!DRAG3||document.querySelector('.swin').style.transform.includes('translate'))`), DRAG3 ? "3 fingers sliding performs the three-finger drag" : "3 fingers sliding performs the 3-finger space swipe", await lastResult());
  await swipe(1, 120, 0); c.ok(await b.eval(`lastResult.id===null`), "a 1-finger swipe has no gesture (and says so)", await lastResult());
  c.ok(await b.eval(`document.getElementById('toast').classList.contains('on')&&document.getElementById('toast').innerText.length>5`), "a toast explains it", await b.eval(`document.getElementById('toast').innerText`));
  await swipe(1, 2, 1); c.ok(await b.eval(`lastResult.id==='tap1'`), "1-finger tap performs 'tap1'", await lastResult());
  await b.eval(`document.querySelector('[data-pinch]').click()`); c.ok(await b.eval(`lastResult.id==='pinch4'&&document.getElementById('ovApps').classList.contains('on')`), "4-finger pinch button opens the apps grid", await lastResult());
  await b.eval(`document.getElementById('bTry').click()`);

  console.log("3D interaction");
  await b.eval(`document.getElementById('stage').scrollIntoView()`); await b.sleep(200);
  const st = await b.eval(`(()=>{const r=document.getElementById('stage').getBoundingClientRect();return {x:r.left+40,y:Math.min(innerHeight-40,r.top+r.height*.55)}})()`);
  const r0 = await b.eval(`({rx,rz})`); await b.drag(st.x, st.y, st.x + 180, st.y - 60);
  const r1 = await b.eval(`({rx,rz})`);
  c.ok(r1.rz > r0.rz + 10 && r1.rx > r0.rx + 8, "drag outside the pad rotates the model", JSON.stringify({ r0, r1 }));
  for (let i = 0; i < 3; i++) await b.wheel(st.x, st.y, -300);   // the point inside the stage that the drag used, not a fixed pixel
  c.ok(await b.eval(`zoom`) > 1.1, "wheel zooms", await b.eval(`zoom`));
  await b.dblclick(st.x, st.y); await b.sleep(700);
  c.ok(await b.eval(`rx===38&&rz===0&&zoom===1`), "double-click resets");
  for (const v of ["top", "low"]) { await b.eval(`document.querySelector('[data-view="${v}"]').click()`); await b.sleep(700); await b.shot(`${OUT}/05-view-${v}.png`); }
  await b.eval(`document.querySelector('[data-view="tilt"]').click()`); await b.sleep(600);

  console.log("angle sweep (nothing clipped by the stage)");
  const clipped = await b.eval(`(()=>{const bad=[];for(const x of [0,20,40,60,75,86])for(const z of [-75,-45,-20,0,20,45,75]){rx=x;rz=z;zoom=1;applyTilt(true);
    const s=document.getElementById('stage').getBoundingClientRect();
    for(const el of [document.querySelector('.case'),document.querySelector('.lid')]){const r=el.getBoundingClientRect();
      if(r.left<s.left-1||r.right>s.right+1||r.top<s.top-1||r.bottom>s.bottom+1)bad.push(x+'/'+z+' '+el.className)}}
    rx=38;rz=0;applyTilt(true);return bad})()`);
  c.ok(clipped.length === 0, "laptop stays inside the stage at all 42 angles", clipped.slice(0, 6).join(", "));
  c.ok(await b.eval(`document.querySelectorAll('.case .key').length===10&&!document.querySelector('.box.key')`), "key row is painted on the deck (no per-key 3D boxes)");
  console.log("language, themes, responsive");
  await b.eval(`document.getElementById('bLang').click()`);
  c.ok(await b.eval(`document.querySelector('h1').innerText.includes('gestos')`), "ES title");
  c.ok(await b.eval(`document.querySelector('.card').innerText.includes('Deslizar')`), "ES cards");
  c.ok(await b.eval(`document.getElementById('info').innerText.includes('Configuración de Hyprland')`), "ES info panel");
  await b.shot(`${OUT}/06-es.png`);
  await b.eval(`document.getElementById('bLang').click()`);
  await b.scheme("light"); await b.sleep(400); await b.shot(`${OUT}/07-light.png`); await b.scheme("dark");
  await b.viewport(400, 900, true); await b.sleep(900);
  c.ok(await b.eval(`document.documentElement.scrollWidth<=innerWidth+1`), "no horizontal overflow at 400px", await b.eval(`document.documentElement.scrollWidth+' vs '+innerWidth`));
  await b.shot(`${OUT}/08-mobile.png`);
  process.env.CDP_ATTACH ? await b.resetViewport() : await b.viewport(1280, 1000);

  console.log("errors");
  c.ok(b.errors.length === 0, "no console errors / exceptions", b.errors.join(" | "));
} catch (e) { console.log("HARNESS ERROR", e.message); c.ok(false, "harness ran to completion", e.message); }
const fails = c.done(); b.close(); process.exit(fails ? 1 : 0);
