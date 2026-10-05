// Angle sweep: captures the stage at 6 tilts x 7 rotations. CDP_ATTACH=9334 uses a running GPU Brave; otherwise headless.
// Sweep camera angles and capture the stage at each. usage: node sweep.mjs <outdir> <page> [extra js]
import { launch } from "./cdp.mjs";
import { mkdirSync, writeFileSync } from "node:fs";
const [out, page="keyboard", extra=""] = process.argv.slice(2); mkdirSync(out,{recursive:true});
const b = await launch();
const real = !!process.env.CDP_ATTACH;
await b.send("Emulation.setDeviceMetricsOverride",{width:880,height:1075,deviceScaleFactor:real?1.6:1,mobile:false});
await b.goto((process.env.BASE||"http://127.0.0.1:8787")+"/"+page); await b.sleep(1200);
if(extra) await b.eval(extra);
const RX=[0,20,40,60,75,86], RZ=[-75,-45,-20,0,20,45,75];
for(const x of RX) for(const z of RZ){
  await b.eval(`(()=>{cancelAnimationFrame(window.tw||0);rx=${x};rz=${z};zoom=1;applyTilt(true);document.getElementById('stage').scrollIntoView()})()`);
  await b.sleep(350);
  const r=await b.eval(`(()=>{const r=document.getElementById('stage').getBoundingClientRect();return {x:r.x+scrollX,y:r.y+scrollY,width:r.width,height:r.height}})()`);
  const s=await b.send("Page.captureScreenshot",{format:"png",clip:{...r,scale:real?0.32:0.5}});
  writeFileSync(`${out}/rx${String(x).padStart(2,"0")}_rz${z>=0?"+":""}${z}.png`,Buffer.from(s.data,"base64"));
}
await b.send("Emulation.clearDeviceMetricsOverride");
console.log("errors:",b.errors.length?b.errors:"none"); b.close(); process.exit(0);
