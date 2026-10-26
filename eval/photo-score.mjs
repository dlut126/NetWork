// Scores photo extraction against hand-written answer keys. Usage: node eval/photo-score.mjs [results.json]
import fs from "fs";
const dir = new URL("./photos/", import.meta.url);
const truth = JSON.parse(fs.readFileSync(new URL(process.argv[3] || "truth.json", dir)));
const resFile = process.argv[2] ? new URL(process.argv[2], `file://${process.cwd()}/`) : new URL("results.json", dir);
const results = JSON.parse(fs.readFileSync(resFile));

const fold = s => String(s || "").normalize("NFD").replace(/\p{M}/gu, "").toLowerCase().replace(/\s+/g, " ").trim();
const exact = s => String(s || "").normalize("NFC").toLowerCase().replace(/\s+/g, " ").trim();
const co = s => fold(s).replace(/&/g, " and ").replace(/[^a-z0-9 ]/g, "").replace(/\s+/g, " ").trim();
const digits = s => String(s || "").replace(/\D/g, "");
const li = s => fold(s).replace(/^https?:\/\//, "").replace(/^www\./, "").replace(/\/$/, "");
function lev(a, b){ const d = Array.from({length: a.length + 1}, (_, i) => [i]); for (let j = 1; j <= b.length; j++) d[0][j] = j;
  for (let i = 1; i <= a.length; i++) for (let j = 1; j <= b.length; j++) d[i][j] = Math.min(d[i-1][j] + 1, d[i][j-1] + 1, d[i-1][j-1] + (a[i-1] === b[j-1] ? 0 : 1));
  return d[a.length][b.length]; }
const sim = (a, b) => { a = fold(a); b = fold(b); return 1 - lev(a, b) / Math.max(a.length, b.length, 1); };
const same = {name: (a, b) => exact(a) === exact(b), email: (a, b) => exact(a) === exact(b), firm: (a, b) => co(a) === co(b),
  phone: (a, b) => digits(a) === digits(b), linkedin: (a, b) => li(a) === li(b)};
const FIELDS = ["email", "firm", "phone", "linkedin"];

const FL = {wrong: 0, wrongFlagged: 0, right: 0, rightFlagged: 0};
const T = {people: 0, found: 0, nameExact: 0, rowsPerfect: 0, extra: 0, invented: 0, skipLeaked: 0, skipTotal: 0, failed: 0, secs: []};
const F = Object.fromEntries(FIELDS.map(f => [f, {right: 0, of: 0}]));
const rows = [], misses = [];
for (const t of truth){
  const r = results.find(x => x.id === t.id);
  const got = (r?.out?.people || []).filter(p => p && String(p.name || "").trim()).map(p => ({...p, used: false}));
  if (!r || r.err || !r.out) T.failed++;
  if (r?.seconds) T.secs.push(r.seconds);
  let found = 0, nameOk = 0, perfect = 0, invented = 0;
  for (const p of t.people){
    T.people++;
    let best = null, bs = 0;
    for (const g of got) if (!g.used){ const s = sim(p.name, g.name); if (s > bs){ bs = s; best = g; } }
    if (!best || bs < 0.75){ misses.push(`#${t.id} missed ${p.name}`); continue; }
    best.used = true; found++;
    const fl = new Set(Array.isArray(best.unsure) ? best.unsure : []);
    const tally = (ok, f) => { if (ok){ FL.right++; if (fl.has(f)) FL.rightFlagged++; } else { FL.wrong++; if (fl.has(f)) FL.wrongFlagged++; } };
    const nOk = same.name(p.name, best.name); tally(nOk, "name"); if (nOk) nameOk++; else misses.push(`#${t.id} name "${p.name}" read as "${best.name}"${fl.has("name") ? " [flagged]" : ""}`);
    let allOk = nOk;
    for (const f of FIELDS){
      if (p[f]){ F[f].of++; const ok = same[f](p[f], best[f]); if (String(best[f] || "").trim()) tally(ok, f);
        if (ok) F[f].right++; else { allOk = false; misses.push(`#${t.id} ${p.name} ${f}: "${p[f]}" read as "${best[f] || ""}"${fl.has(f) ? " [flagged]" : ""}`); } }
      else if (String(best[f] || "").trim()){ invented++; allOk = false; misses.push(`#${t.id} ${p.name} ${f}: blank on sheet, app put "${best[f]}"`); }
    }
    if (allOk) perfect++;
  }
  const extras = got.filter(g => !g.used);
  for (const x of extras) misses.push(`#${t.id} extra person "${x.name}"${t.should_skip.some(s => sim(s, x.name) > 0.75) ? " (crossed out or unreadable on the sheet)" : ""}`);
  const leaked = t.should_skip.filter(s => extras.some(x => sim(s, x.name) > 0.75)).length;
  T.found += found; T.nameExact += nameOk; T.rowsPerfect += perfect; T.extra += extras.length; T.invented += invented;
  T.skipLeaked += leaked; T.skipTotal += t.should_skip.length;
  rows.push(`| ${t.id} | ${t.desc} | ${found}/${t.people.length} | ${nameOk} | ${perfect} | ${extras.length} | ${invented} | ${r?.seconds ?? "–"}s |`);
}
const pct = (a, b) => b ? Math.round(100 * a / b) + "%" : "–";
console.log(`| # | Sheet | People found | Names exact | Rows fully right | Extra people | Invented fields | Time |\n|---|---|---|---|---|---|---|---|\n${rows.join("\n")}`);
console.log(`\nTOTAL: found ${T.found}/${T.people} (${pct(T.found, T.people)}), names exact ${T.nameExact}/${T.people} (${pct(T.nameExact, T.people)}), rows fully right ${T.rowsPerfect}/${T.people} (${pct(T.rowsPerfect, T.people)})`);
console.log(FIELDS.map(f => `${f} right ${F[f].right}/${F[f].of} (${pct(F[f].right, F[f].of)})`).join(", "));
console.log(`extra people ${T.extra}, crossed-out/unreadable rows wrongly added ${T.skipLeaked}/${T.skipTotal}, invented fields ${T.invented}, failed photos ${T.failed}, median time ${T.secs.sort((a, b) => a - b)[Math.floor(T.secs.length / 2)] ?? "–"}s`);
console.log(`"Hard to read" flags: caught ${FL.wrongFlagged} of ${FL.wrong} wrong values; flagged ${FL.rightFlagged} of ${FL.right} correct values unnecessarily`);
console.log("\nEvery miss:\n" + (misses.join("\n") || "(none)"));
