const http = require("http");
const fs = require("fs");
const path = require("path");

/* Local development: load .env if it exists. On a host, set the variables in
   the dashboard instead. Never commit real credentials. */
function loadEnv() {
  const file = path.join(__dirname, ".env");
  if (!fs.existsSync(file)) return;
  for (const line of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
    if (/^\s*#/.test(line)) continue;
    const m = /^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$/.exec(line);
    if (!m) continue;
    let v = m[2].trim();
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) v = v.slice(1, -1);
    if (process.env[m[1]] === undefined) process.env[m[1]] = v;
  }
}
loadEnv();

const PORT = process.env.PORT || 10000;
const ACCOUNT_ID = (process.env.CLOUDFLARE_ACCOUNT_ID || "").trim();
const API_TOKEN = (process.env.CLOUDFLARE_API_TOKEN || "").trim();
const TEXT_MODEL = process.env.CLOUDFLARE_TEXT_MODEL || "@cf/meta/llama-3.1-8b-instruct-fp8";
const IMAGE_MODEL = process.env.CLOUDFLARE_IMAGE_MODEL || "@cf/black-forest-labs/flux-1-schnell";
const IMAGE_STEPS = Math.min(8, Math.max(1, parseInt(process.env.CLOUDFLARE_IMAGE_STEPS || "4", 10) || 4));
const CF_BASE = `https://api.cloudflare.com/client/v4/accounts/${ACCOUNT_ID}/ai/run/`;

const MAX_BODY = 100 * 1024;
const RATE_WINDOW = 10 * 60 * 1000;
const RATE_LIMIT = 80;
const rate = new Map();

class HttpError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function sendJSON(res, status, data, extra) {
  const body = JSON.stringify(data);
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    ...(extra || {}),
  });
  res.end(body);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on("data", (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY) {
        reject(new HttpError(413, "Request body is too large."));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

function clientIP(req) {
  const fwd = req.headers["x-forwarded-for"];
  return String(fwd ? fwd.split(",")[0] : req.socket.remoteAddress || "unknown").trim();
}

function limited(ip) {
  const now = Date.now();
  let b = rate.get(ip);
  if (!b || now - b.start > RATE_WINDOW) {
    b = { start: now, count: 0 };
    rate.set(ip, b);
  }
  b.count += 1;
  if (rate.size > 5000) {
    for (const [key, value] of rate) if (now - value.start > RATE_WINDOW) rate.delete(key);
  }
  return b.count > RATE_LIMIT;
}

async function cloudflare(model, input, timeoutMs) {
  if (!ACCOUNT_ID || !API_TOKEN) {
    throw new HttpError(503, "AI is not configured on the server. Set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN.");
  }
  let r;
  try {
    r = await fetch(CF_BASE + model, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${API_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(input),
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch (e) {
    if (e && (e.name === "TimeoutError" || e.name === "AbortError")) {
      throw new HttpError(504, "The AI service took too long. Please try again.");
    }
    throw new HttpError(502, "Could not reach the AI service.");
  }
  const text = await r.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch (e) {
    throw new HttpError(502, "The AI service returned an invalid response.");
  }
  if (!r.ok || !data.success) {
    const detail = data.errors && data.errors[0] && data.errors[0].message ? data.errors[0].message : `HTTP ${r.status}`;
    if (r.status === 401 || r.status === 403) {
      throw new HttpError(502, "Cloudflare rejected the API credentials. Check the server settings.");
    }
    if (r.status === 429) {
      throw new HttpError(429, "AI rate limit reached. Please wait a minute and try again.");
    }
    throw new HttpError(502, `AI service error: ${String(detail).slice(0, 180)}`);
  }
  return data.result || {};
}

const PROMPT_SYSTEM = `You write English prompts for a photorealistic text-to-image model.
Read the slide text below. It may be written in Nepali or another language.
Reply with ONE English image prompt of at most 35 words that captures the main idea.
Describe a concrete scene: the setting, people or objects, and the lighting.
Do not include any text, captions, letters, logos or watermarks in the image.
Return only the prompt. No quotes, labels, or explanation.`;

async function summarize(text) {
  const result = await cloudflare(
    TEXT_MODEL,
    {
      messages: [
        { role: "system", content: PROMPT_SYSTEM },
        { role: "user", content: text.slice(0, 4000) },
      ],
      max_tokens: 120,
      temperature: 0.5,
    },
    30000
  );
  let prompt = typeof result.response === "string" ? result.response : "";
  prompt = prompt
    .replace(/\r?\n+/g, " ")
    .replace(/^["'\s]+|["'\s]+$/g, "")
    .replace(/^(?:image\s+)?prompt\s*:\s*/i, "")
    .replace(/\s+/g, " ")
    .trim();
  if (!prompt) throw new HttpError(502, "The AI could not write an image prompt for this slide.");
  return prompt.slice(0, 600);
}

async function generateImage(prompt) {
  const result = await cloudflare(
    IMAGE_MODEL,
    { prompt: prompt.slice(0, 2000), steps: IMAGE_STEPS },
    60000
  );
  if (!result.image) throw new HttpError(502, "The AI did not return an image.");
  return `data:image/jpeg;base64,${result.image}`;
}

async function slideImage(req, res) {
  if (req.method === "OPTIONS") {
    res.writeHead(204, {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Headers": "Content-Type",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
    });
    return res.end();
  }
  if (req.method !== "POST") return sendJSON(res, 405, { success: false, error: "Use POST." });
  if (limited(clientIP(req))) {
    return sendJSON(res, 429, { success: false, error: "Too many picture requests. Please wait a few minutes." }, { "Retry-After": "120" });
  }
  try {
    let body;
    try {
      body = JSON.parse(await readBody(req));
    } catch (e) {
      if (e instanceof HttpError) throw e;
      throw new HttpError(400, "Invalid JSON body.");
    }
    const text = typeof body.text === "string" ? body.text.trim().slice(0, 4000) : "";
    const explicit = typeof body.prompt === "string" ? body.prompt.trim().slice(0, 1000) : "";
    if (!text && !explicit) throw new HttpError(400, "Slide text or an image prompt is required.");

    const started = Date.now();
    const prompt = explicit || (await summarize(text));
    const image = await generateImage(prompt);
    console.log(`AI picture ${Date.now() - started}ms | ${prompt.slice(0, 100)}`);
    sendJSON(res, 200, { success: true, prompt, image });
  } catch (e) {
    const status = e instanceof HttpError ? e.status : 500;
    if (!(e instanceof HttpError)) console.error("slide-image:", e);
    sendJSON(res, status, { success: false, error: e.message || "Picture generation failed." });
  }
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, "http://localhost");

  if (url.pathname === "/ping") {
    res.writeHead(200, { "Content-Type": "text/plain; charset=utf-8" });
    return res.end("pong");
  }

  if (url.pathname === "/api/slide-image") {
    slideImage(req, res);
    return;
  }

  if (req.method !== "GET" && req.method !== "HEAD") {
    res.writeHead(405, { "Content-Type": "text/plain; charset=utf-8" });
    return res.end("Method not allowed");
  }

  if (url.pathname !== "/" && url.pathname !== "/index.html") {
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    return res.end("Not found");
  }

  fs.readFile(path.join(__dirname, "index.html"), (err, data) => {
    if (err) {
      res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      return res.end("Server error");
    }
    res.writeHead(200, {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-cache",
    });
    res.end(req.method === "HEAD" ? undefined : data);
  });
});

server.listen(PORT, "0.0.0.0", () => {
  console.log(`Server running on port ${PORT}`);
  if (!ACCOUNT_ID || !API_TOKEN) {
    console.warn("Cloudflare credentials are missing. Add them to .env or the host environment.");
  }
});
