// usage: CDP_ATTACH=9334 node realshot.mjs <path> <name> [js-to-run-before-capture]
import { launch } from "./cdp.mjs";
import { execSync } from "node:child_process";
const [path,name,js]=process.argv.slice(2);
const S=process.env.SHOT_DIR||"/tmp/omarchy-kit-shots"; (await import("node:fs")).mkdirSync(S,{recursive:true});
const b=await launch();
await b.goto("http://127.0.0.1:8787"+path);await b.sleep(900);
await b.eval(`document.getElementById("stage").scrollIntoView()`);
if(js)await b.eval(js);
await b.sleep(900);
// Brave's own GPU-composited screenshot of the page (never the user's screen)
await b.shot(`${S}/${name}.png`);
console.log("errors:",b.errors.length?b.errors:"none");b.close();process.exit(0);
