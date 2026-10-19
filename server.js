// Local runner: serves index.html and /api/claude with no dependencies.
//   ANTHROPIC_API_KEY=sk-ant-... node server.js
// Then open http://localhost:3000

import http from "node:http";
import { readFile } from "node:fs/promises";
import handler from "./api/claude.js";

const PORT = process.env.PORT || 3000;

http.createServer(async (req, res) => {
  const path = new URL(req.url, "http://localhost").pathname;
  if (path === "/api/claude") return handler(req, res);
  if (path === "/" || path === "/index.html") {
    res.setHeader("content-type", "text/html; charset=utf-8");
    return res.end(await readFile(new URL("./index.html", import.meta.url)));
  }
  res.statusCode = 404;
  res.end("Not found");
}).listen(PORT, () => {
  console.log(`NetWork running at http://localhost:${PORT}`);
  if (!process.env.ANTHROPIC_API_KEY) console.log("Warning: ANTHROPIC_API_KEY is not set, so the AI features will fail.");
});
