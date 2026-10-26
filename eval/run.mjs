// Scores the app's capture router (the code that decides "save this as a name now" vs "send it to the AI")
// against the labeled test sets. Run: npm run eval
// It reads the router straight out of index.html, so it always tests the code that's actually deployed.
import fs from "node:fs";
const html = fs.readFileSync(new URL("../index.html", import.meta.url), "utf8");
const a = html.indexOf("const NAME_STOP = new Set(["), b = html.indexOf("function isJustName(t)");
const routeCapture = new Function(html.slice(a, b) + "\nreturn routeCapture;")();

for (const file of ["training.json", "heldout.json"]){
  const set = JSON.parse(fs.readFileSync(new URL(file, import.meta.url), "utf8"));
  let right = 0; const badContacts = [], sentToAI = [];
  for (const [text, label] of set){
    const r = routeCapture(text);
    if (label === "description" && r === "name") badContacts.push(text);          // would save a wrong contact
    else if (label === "name" && r === "ai") { sentToAI.push(text); }              // fine, just slower
    if ((label === "name" && r === "name") || (label === "description" && r === "ai")) right++;
  }
  const descs = set.filter(x => x[1] === "description").length;
  console.log(`${file}: routed right ${right}/${set.length} (${Math.round(right / set.length * 100)}%), bad contacts ${badContacts.length}/${descs}, names sent to AI ${sentToAI.length}`);
  if (badContacts.length) console.log("  bad contacts:", badContacts.join(" | "));
  if (sentToAI.length) console.log("  names sent to AI:", sentToAI.join(" | "));
}
