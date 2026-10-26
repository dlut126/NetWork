// Headless test (jsdom). Run: npm install, then node eval/tests/<file>
import { JSDOM } from "jsdom";
import fs from "fs";
const html = fs.readFileSync(new URL("../../index.html", import.meta.url),"utf8");
const errors=[];
const dom = new JSDOM(`<!doctype html><html><body>${html}</body></html>`, {runScripts:"dangerously", url:"https://claude.ai/", pretendToBeVisual:true,
  beforeParse(w){ w.addEventListener("error", e=>errors.push(e.message)); w.HTMLElement.prototype.scrollIntoView=()=>{}; w.scrollTo=()=>{};
    const sample = Object.assign(async()=>({text:"x"}), {limits: async()=>({images:{maxCount:4}}), json: async (p)=>({event:"Mixer", unreadable:2, people:[
      {name:"Max Morgan", firm:"Google", email:"", unsure:["name"]}, {name:"Kara Mitchell", firm:"Meta", email:"kmitchell@meta.com", unsure:["firm","email","bogus"]}, {name:"Zoe Park", firm:"Pinterest", email:"zpark@pinterest.com", unsure:[]}]})});
    w.claude = { use: async (n) => n==="sample" ? sample : null }; }});
const w = dom.window, d = w.document; const sleep = ms => new Promise(r=>setTimeout(r,ms));
await sleep(400);
d.querySelector("#addBtn").click(); await sleep(20);
await w.eval('runPhoto("aq", new Blob(["x"],{type:"image/jpeg"}))'); await sleep(30);
console.log("status:", d.querySelector("#aq-st").textContent);
console.log("cards:", [...d.querySelectorAll(".pcard")].map(c => (c.classList.contains("unsure")?"[!] ":"") + c.querySelector(".cname").textContent.trim() + " | " + (c.querySelector(".unsure-note")?.textContent||"")));
d.querySelector(".pcard.unsure [data-edit]").click(); await sleep(10); d.querySelector(".pcard [data-edit]").click(); await sleep(10);
console.log("after edit+close unsure count:", d.querySelectorAll(".pcard.unsure").length);
console.log("ERRORS:", errors);
