// Presented frames/s while each page sits idle (should be ~0). Needs CDP_ATTACH.
import { launch } from "./cdp.mjs";
const b=await launch();
for(const path of ["/keyboard","/trackpad"]){
  await b.goto("http://127.0.0.1:8787"+path);await b.sleep(7000); // let the trackpad demo finish its 3 loops
  const ev=[];const done=new Promise(res=>{globalThis.__cdpHook=m=>{if(m.method==="Tracing.dataCollected")ev.push(...m.params.value);if(m.method==="Tracing.tracingComplete")res()}});
  await b.send("Tracing.start",{categories:"viz",transferMode:"ReportEvents"});await b.sleep(2500);await b.send("Tracing.end");await done;
  console.log((path+" idle").padEnd(18),(ev.filter(e=>e.name==="Display::DrawAndSwap").length/2.5).toFixed(1),"frames/s");
}
b.close();process.exit(0);
