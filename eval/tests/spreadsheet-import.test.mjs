// Headless test (jsdom). Run: npm install, then node eval/tests/<file>
import { JSDOM } from "jsdom";
import fs from "fs";
const html = fs.readFileSync(new URL("../../index.html", import.meta.url),"utf8");
const XLSRC = fs.readFileSync(new URL("../../node_modules/xlsx/dist/xlsx.full.min.js", import.meta.url),"utf8");
const dir = new URL("../spreadsheets/", import.meta.url).pathname;
const truth = JSON.parse(fs.readFileSync(dir + "truth.json"));
async function boot(withAI){
  const errors = [], prompts = [];
  const dom = new JSDOM(`<!doctype html><html><body>${html}</body></html>`, {runScripts:"dangerously", url:"https://claude.ai/", pretendToBeVisual:true,
    beforeParse(w){ w.addEventListener("error", e=>errors.push(e.message)); w.HTMLElement.prototype.scrollIntoView=()=>{}; w.scrollTo=()=>{};
      w.eval(XLSRC);
      const sample = Object.assign(async()=>({text:""}), {json: async (p)=>{ prompts.push(p);
        // what a model would answer for file 4's header
        if (p.includes("typed as free text")){   // stand-in for the model: split the known test sentences
          const rows = [...p.matchAll(/^(\d+)\. (.*)$/gm)].map(m => ({row:Number(m[1]), text:m[2]}));
          const known = [["Jake Morales","Bain","","jake.morales@bain.com","",""],["Nina Shah","Deloitte","senior consultant","","2026-10-14",""],
            ["Priya Raman","McKinsey","associate","priya_raman@mckinsey.com","",""],["Sam Lee","Google","PM","","",""],["Carlos Vega","BCG","principal","cvega@bcg.com","",""]];
          return {rows: rows.map(r => ({row:r.row, people: known.filter(k => r.text.includes(k[0])).map(k => ({name:k[0], firm:k[1], role:k[2], email:k[3], date:k[4], followUp:k[5]}))}))};
        }
        if (p.includes("Attendance")) return {headerRow:0, columns:{name:-1, first:-1, last:-1, firm:-1, role:-1, email:-1, phone:-1, linkedin:-1, industry:-1, howMet:-1, lastContact:1, followUp:-1, tags:-1, notes:-1}};
        if (p.includes("Attendance") === false && p.includes("Tech Trek")) return {headerRow:0, columns:{name:0}};
        return {headerRow:0, columns:{name:0, first:-1, last:-1, firm:1, role:2, email:3, phone:-1, linkedin:-1, industry:-1, howMet:-1, lastContact:4, followUp:-1, tags:-1, notes:-1}}; }});
      w.claude = withAI ? { use: async (n) => n==="sample" ? sample : null } : undefined; }});
  await new Promise(r => setTimeout(r, 400));
  return {w: dom.window, errors, prompts};
}
const cmp = (want, got) => { const bad = []; for (const [k, v] of Object.entries(want)) if (String(got?.[k] ?? "") !== String(v)) bad.push(`${k}: want "${v}" got "${got?.[k] ?? ""}"`); return bad; };
let ok = 0, total = 0;
for (const withAI of [true, false]){
  const {w, errors, prompts} = await boot(withAI);
  console.log(`\n=== ${withAI ? "with AI" : "no AI"} ===`);
  for (const t of truth){
    const buf = fs.readFileSync(dir + t.file);
    const file = new w.File([buf], t.file);
    const r = await w.readAnyContactsFile(file);
    const bad = [];
    if (!withAI && t.file.startsWith("7-")){ if (!r.error) bad.push("without AI this should explain sentences need AI"); }
    else if (!withAI && t.file.startsWith("6-")){ if (r.error || r.unsplitCount !== 2 || r.people.length !== 4) bad.push(`without AI should keep 4 rows with 2 unsplit, got ${r.error || r.people?.length + "/" + r.unsplitCount}`); }
    else if (!withAI && t.file.startsWith("4-")){ if (!r.error) bad.push("without AI this should ask for a Name header"); }
    else if (!t.people.length){ if (!r.error) bad.push("should have refused, got " + (r.people||[]).length); }
    else if (r.error) bad.push("ERROR " + r.error);
    else {
      if (r.people.length !== t.people.length) bad.push(`count ${r.people.length} vs ${t.people.length}: ${r.people.map(p=>p.name).join(", ")}`);
      t.people.forEach((p, i) => bad.push(...cmp(p, r.people[i]).map(x => p.name + " " + x)));
    }
    total++; if (!bad.length) ok++;
    console.log(`${bad.length ? "FAIL" : "ok  "} ${t.file}${r.byAI ? " (AI mapped)" : ""}${r.sheet ? ` [tab ${r.sheet}]` : ""} ${r.error ? "→ " + r.error : "→ " + Object.entries(r.used||{}).map(([f,h]) => h + "→" + f).join(", ")}`);
    bad.forEach(b => console.log("     ", b));
  }
  // full import through the UI path for file 2
  const d = w.document; d.querySelector("#addBtn").click(); await new Promise(r=>setTimeout(r,20));
  d.querySelector("#aq-imp")?.click(); await new Promise(r=>setTimeout(r,20));
  const inp = d.querySelector("#impFile");
  const dt = { files: [new w.File([fs.readFileSync(dir + "2-messy-recruiting.xlsx")], "2-messy-recruiting.xlsx")] };
  Object.defineProperty(inp, "files", {value: dt.files});
  await inp.onchange(); await new Promise(r=>setTimeout(r,30));
  console.log("preview:", d.querySelector("#impOut")?.textContent.replace(/\s+/g," ").trim().slice(0, 420));
  d.querySelector("#impGo").click(); await new Promise(r=>setTimeout(r,60));
  const ppl = w.eval("people");
  const raj = ppl.find(p => p.name === "Raj Iyer");
  console.log("imported:", ppl.length, "| Raj:", JSON.stringify({firm:raj.firm, role:raj.role, howMet:raj.howMet, last:raj.lastContact, followUp:raj.followUp, tags:raj.tags, notes:raj.notes}));
  const today = w.eval("buildNetwork().list").filter(e => e.nudge).map(e => e.name + ": " + e.nudge.r[0]);
  console.log("to-dos after import:", today);
  console.log("AI calls:", prompts.length, "| ERRORS:", errors);
}
console.log(`\n${ok}/${total} file checks passed`);
