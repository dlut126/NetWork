// POST /api/claude  { prompt: string, tier?: "default" | "quick" | "complex", images?: [{media_type, data}] }  ->  { text, truncated }
// Holds the Anthropic API key on the server so it never reaches the browser or the repo.
// Works as a Vercel serverless function and is reused by server.js for local runs.

const MODELS = {
  quick: process.env.CLAUDE_MODEL_QUICK || "claude-haiku-4-5-20251001",
  default: process.env.CLAUDE_MODEL || "claude-sonnet-5-5",
  complex: process.env.CLAUDE_MODEL || "claude-sonnet-5-5",
};
const MAX_PROMPT_CHARS = 200_000;
const IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp", "image/gif"]);
const MAX_IMAGES = 4, MAX_IMAGE_B64 = 4_000_000;   // about 3 MB per photo after the browser shrinks it

async function readBody(req) {
  if (req.body && typeof req.body === "object") return req.body;
  if (typeof req.body === "string") return JSON.parse(req.body || "{}");
  const chunks = [];
  for await (const c of req) chunks.push(c);
  return JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}");
}

function send(res, status, obj) {
  res.statusCode = status;
  res.setHeader("content-type", "application/json");
  res.end(JSON.stringify(obj));
}

export default async function handler(req, res) {
  if (req.method === "GET") return send(res, 200, { ok: true });   // the app checks this to know the AI is available
  if (req.method !== "POST") return send(res, 405, { error: "Use POST" });

  // ANTHROPIC_API_KEY is the standard name; "anthro" is accepted because Vercel won't rename a sensitive variable once saved.
  const key = process.env.ANTHROPIC_API_KEY || process.env.anthro;
  if (!key) return send(res, 500, { error: "ANTHROPIC_API_KEY is not set on the server" });

  // Optional: require an access code so a public link can't run up your API bill
  const code = process.env.ACCESS_CODE;
  if (code && req.headers["x-access-code"] !== code) return send(res, 401, { error: "Access code required" });

  let body;
  try { body = await readBody(req); } catch { return send(res, 400, { error: "Invalid JSON" }); }
  const prompt = typeof body.prompt === "string" ? body.prompt : "";
  if (!prompt.trim()) return send(res, 400, { error: "Missing prompt" });
  if (prompt.length > MAX_PROMPT_CHARS) return send(res, 413, { error: "Prompt too long" });

  const images = Array.isArray(body.images) ? body.images : [];
  if (images.length > MAX_IMAGES) return send(res, 413, { error: "Too many images" });
  for (const im of images) {
    if (!im || !IMAGE_TYPES.has(im.media_type) || typeof im.data !== "string") return send(res, 400, { error: "Unsupported image" });
    if (im.data.length > MAX_IMAGE_B64) return send(res, 413, { error: "Image too large" });
  }
  const content = images.length
    ? [...images.map(im => ({ type: "image", source: { type: "base64", media_type: im.media_type, data: im.data } })), { type: "text", text: prompt }]
    : prompt;

  try {
    const r = await fetch("https://api.anthropic.com/v1/messages", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
      },
      body: JSON.stringify({
        model: MODELS[body.tier] || MODELS.default,
        max_tokens: 4000,
        messages: [{ role: "user", content }],
      }),
    });
    if (r.status === 429) return send(res, 429, { error: "Rate limited" });
    if (!r.ok) return send(res, 502, { error: `Claude API error ${r.status}`, detail: (await r.text()).slice(0, 500) });
    const data = await r.json();
    const text = (data.content || []).filter(b => b.type === "text").map(b => b.text).join("");
    return send(res, 200, { text, truncated: data.stop_reason === "max_tokens" });
  } catch (e) {
    return send(res, 502, { error: "Could not reach the Claude API" });
  }
}
