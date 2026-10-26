// Runs every test photo through the app's own photo step (extractPhoto, the same function the Photo button uses).
// How: open the live site, open the browser console, paste this file, and wait about a minute.
// Results land in window.__photoEval.results; copy them into eval/photos/results.json and run `npm run eval:photos`.
(async () => {
  const truth = await (await fetch("eval/photos/truth.json")).json();
  window.__photoEval = {started: new Date().toISOString(), done: 0, total: truth.length, results: []};
  const one = async t => {
    const blob = await (await fetch("eval/photos/" + t.file)).blob();
    const t0 = performance.now(); let out = null, err = null;
    try { out = await extractPhoto(blob); } catch (e) { err = e?.code || String(e); }
    window.__photoEval.results.push({id: t.id, seconds: Math.round((performance.now() - t0) / 100) / 10, out, err});
    window.__photoEval.done++;
  };
  const queue = [...truth];
  await Promise.all([1, 2, 3].map(async () => { while (queue.length) await one(queue.shift()); }));   // three at a time
  window.__photoEval.results.sort((a, b) => a.id - b.id);
  console.log("Photo eval done:", JSON.stringify(window.__photoEval.results));
})();
