// Headless test (jsdom). Run: npm install, then node eval/tests/<file>
import { JSDOM } from "jsdom";
import fs from "fs";
const html = fs.readFileSync(new URL("../../index.html", import.meta.url),"utf8");
async function run(withAI){
  const errors=[]; const prompts=[];
  const dom = new JSDOM(`<!doctype html><html><body>${html}</body></html>`, {runScripts:"dangerously", url:"https://claude.ai/", pretendToBeVisual:true,
    beforeParse(w){ w.addEventListener("error", e=>errors.push(e.message)); w.HTMLElement.prototype.scrollIntoView=()=>{}; w.scrollTo=()=>{};
      const sample = Object.assign(async()=>({text:"x"}), {json: async (p)=>{ prompts.push(p);
        if (p.includes("THE USER WANTS TO MEET")) return {matches:[], introducers:[{key:"sam rivera|bain & company", why:"Former Figma intern per notes"}], linkedin:[{label:"Figma PMs", keywords:"Figma product manager"}], google:[], tip:"Lead with the shared connection."};
        return {channel:"LinkedIn", subject:"", message:"Hi Leo, quick ask about Figma…"}; }});
      w.claude = withAI ? { use: async (n) => n==="sample" ? sample : null } : undefined; }});
  const w = dom.window, d = w.document; const sleep = ms => new Promise(r=>setTimeout(r,ms));
  const txt = s => d.querySelector(s)?.textContent.replace(/\s+/g," ").trim();
  await sleep(400);
  w.savePerson({name:"Dana Kim", firm:"Figma", role:"Product Manager", lastContact:"2026-10-20"});
  w.savePerson({name:"Leo Park", firm:"Google", role:"Designer", notes:"Used to work at Figma, still close with the design team", lastContact:"2026-09-01"});
  w.savePerson({name:"Sam Rivera", firm:"Bain & Company", role:"Consultant", lastContact:"2026-09-01"});
  w.render(); await sleep(30);
  const tod = [...d.querySelectorAll("button")].find(b => /Today/.test(b.textContent)); if (tod) tod.click(); await sleep(30);
  console.log(`--- ${withAI ? "with AI" : "no AI"} --- intro box on Today:`, !!d.querySelector("#introIn"));
  d.querySelector("#introIn").value = "Who do I know at Figma?"; d.querySelector("#introGo").click(); await sleep(80);
  const sec = [...d.querySelectorAll("#findOut .section")].map(s => s.textContent.replace(/\s+/g," ").trim().slice(0,160));
  console.log(sec.join("\n"));
  const ask = [...d.querySelectorAll("[data-intro]")].find(b => b.dataset.intro.startsWith("leo"));
  ask.click(); await sleep(80);
  console.log("draft:", txt("[data-dtext]")?.slice(0,120), "| label:", txt(".draft .label"));
  d.querySelector("[data-isent]").click(); await sleep(40);
  const p = w.eval("people").find(x => x.name==="Leo Park");
  console.log("after sent:", txt(".draft .hint"), "| owes:", JSON.stringify(p.owes?.map(o=>[o.what,o.due])), "| log:", p.log.at(-1).kind, p.log.at(-1).note);
  console.log("prompts:", prompts.length, "| ERRORS:", errors);
}
await run(true); await run(false);
