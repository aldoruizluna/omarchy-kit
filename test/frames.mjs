// Presented frames/s while the keyboard sways (JS-driven vs compositor-driven). Needs CDP_ATTACH and a visible window.
import { launch } from "./cdp.mjs";
const b=await launch();
async function count(label,start,stop){
  await b.goto("http://127.0.0.1:8787/keyboard");await b.sleep(1000);
  await b.eval(`document.getElementById('stage').scrollIntoView()`);await b.sleep(300);
  const ev=[];const done=new Promise(res=>{globalThis.__cdpHook=m=>{if(m.method==="Tracing.dataCollected")ev.push(...m.params.value);if(m.method==="Tracing.tracingComplete")res()}});
  await b.send("Tracing.start",{categories:"viz,cc,disabled-by-default-devtools.timeline.frame",transferMode:"ReportEvents"});
  await b.eval(start);await b.sleep(3000);await b.eval(stop);
  await b.send("Tracing.end");await done;
  const draws=ev.filter(e=>e.name==="Display::DrawAndSwap").length;
  console.log(label.padEnd(26),(draws/3).toFixed(1),"presented frames/s");
}
await count("JS sway (current)",`document.getElementById('bSway').click()`,`document.getElementById('bSway').click()`);
await count("compositor (WAAPI) sway",
 `window.__a=document.getElementById('board').animate([{transform:'rotateX(34deg) rotateZ(-16deg)'},{transform:'rotateX(46deg) rotateZ(16deg)'}],{duration:2500,direction:'alternate',iterations:Infinity,easing:'ease-in-out'})`,
 `window.__a.cancel()`);
b.close();process.exit(0);
