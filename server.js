const http = require("http");
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");

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

/* Pollinations is the fallback provider. It is used automatically when
   Cloudflare is out of quota, rate-limited, or otherwise failing. Both the
   prompt summary and the picture can fall back independently. */
const POLLINATIONS_API = (process.env.POLLINATIONS_API || process.env.POLLINATIONS_API_KEY || "").trim();
const POLLINATIONS_BASE = "https://gen.pollinations.ai";
const POLLINATIONS_IMAGE_MODEL = process.env.POLLINATIONS_IMAGE_MODEL || "flux";
const POLLINATIONS_TEXT_MODEL = (process.env.POLLINATIONS_TEXT_MODEL || "").trim();
const HAS_CLOUDFLARE = !!(ACCOUNT_ID && API_TOKEN);
const HAS_POLLINATIONS = !!POLLINATIONS_API;

/* Nepali narration through YourVoice (https://yourvoic.com). The API key stays
   on the server and is never sent to the browser. Default voice: Vijay (male). */
const YOURVOICE_API_KEY = (process.env.YOURVOICE_API_KEY || "").trim();
const YOURVOICE_VOICE = (process.env.YOURVOICE_VOICE || "Vijay").trim();
const YOURVOICE_LANGUAGE = (process.env.YOURVOICE_LANGUAGE || "ne").trim();
const YOURVOICE_MODEL = (process.env.YOURVOICE_MODEL || "aura-lite").trim();
const TTS_CACHE_DIR = path.join(__dirname, ".tts-cache");
const TTS_MAX_CHARS = 2000;
const HAS_YOURVOICE = !!YOURVOICE_API_KEY;

/* The editor is used for religious and cultural videos, so every picture must
   stay respectful and family-friendly. The summary prompt below is instructed
   to produce safe scenes, explicit "@img" prompts are screened, and every
   final prompt gets positive safety wording. */
const SAFE_FALLBACK =
  "A peaceful Nepali temple courtyard at sunrise with modestly dressed people in traditional attire, warm golden light, respectful and family-friendly, no text";

const IMAGE_SAFETY =
  ", respectful family-friendly scene, modest traditional clothing, serene and dignified atmosphere, high quality";

const UNSAFE_PATTERNS = [
  /\bnude\b/i, /\bnudity\b/i, /\bnaked\b/i, /\btopless\b/i, /\bbottomless\b/i,
  /\blingerie\b/i, /\bunderwear\b/i, /\bunderpants\b/i, /\bpanties\b/i, /\bbra\b/i,
  /\bbikini\b/i, /\bswimsuit\b/i, /\bswimwear\b/i, /\bcleavage\b/i, /\bbreasts?\b/i,
  /\bhalf[- ]?naked\b/i, /\bundress(?:ed|ing)?\b/i, /\bsexual\w*\b/i, /\bsex\b/i,
  /\berotic\w*\b/i, /\bporn\w*\b/i, /\bseductive\b/i, /\bsensual\b/i,
  /\bkiss(?:es|ing)?\b/i, /\bromantic\b/i,
  /\bblood\w*\b/i, /\bgore\b/i, /\bviolence\b/i, /\bviolent\b/i, /\bweapons?\b/i,
  /\bguns?\b/i, /\bknife\b/i, /\bknives\b/i, /\bswords?\b/i, /\bkill\w*\b/i,
  /\bmurder\w*\b/i, /\bcorpse\b/i, /\btorture\w*\b/i, /\bterroris\w*\b/i,
  /\bdrugs?\b/i, /\bcocaine\b/i, /\bheroin\b/i, /\balcohol\b/i, /\bbeers?\b/i,
  /\bwine\w*\b/i, /\bwhiskey\b/i, /\bcigarette\w*\b/i, /\bsmoking\b/i,
  /\bgambling\b/i, /\bcasino\b/i, /\bhorror\b/i, /\bdemons?\b/i, /\bdevils?\b/i,
];

/* Common Nepali/Devanagari words for the same unsafe topics. */
const UNSAFE_NEPALI = [
  "नग्न", "निर्वस्त्र", "अर्धनग्न", "सेक्स", "यौन", "कामुक", "अश्लील", "पोर्न",
  "बलात्कार", "रक्त", "हिंसा", "हत्या", "हतियार", "आतंक", "मदिरा", "रक्सी",
  "धूम्रपान", "जुवा", "डरलाग्दो",
];

function unsafePrompt(text) {
  const value = String(text || "");
  if (UNSAFE_NEPALI.some((word) => value.includes(word))) return true;
  return UNSAFE_PATTERNS.some((re) => re.test(value));
}

function safeImagePrompt(prompt) {
  const base = String(prompt || "").replace(/[.\s]+$/, "").trim().slice(0, 700);
  if (!base) return SAFE_FALLBACK;
  return `${base}${IMAGE_SAFETY}`.slice(0, 1000);
}

const MAX_BODY = 100 * 1024;
const RATE_WINDOW = 10 * 60 * 1000;
const RATE_LIMIT = 80;
const rate = new Map();

class HttpError extends Error {
  constructor(status, message, code) {
    super(message);
    this.status = status;
    this.code = code || "";
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

/* Cloudflare circuit breaker. A daily-quota error stops all Cloudflare calls
   until the next UTC midnight, so the remaining slides go straight to the
   fallback instead of waiting for the same error on every picture. */
let cfDownUntil = 0;
let cfDownReason = "";

function nextUtcMidnight() {
  const now = new Date();
  return Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1);
}

function cloudflareAvailable() {
  return HAS_CLOUDFLARE && Date.now() >= cfDownUntil;
}

function noteCloudflareFailure(err) {
  const wasDown = Date.now() < cfDownUntil;
  if (err && err.code === "daily_quota") {
    cfDownUntil = Math.max(cfDownUntil, nextUtcMidnight());
    cfDownReason = "daily free limit reached";
  } else if (err && err.code !== "not_configured") {
    cfDownUntil = Math.max(cfDownUntil, Date.now() + 60 * 1000);
    cfDownReason = err.message || "temporary error";
  } else {
    return;
  }
  if (!wasDown) {
    const next = HAS_POLLINATIONS ? "Falling back to Pollinations." : "No fallback provider is configured.";
    console.warn(`Cloudflare unavailable (${cfDownReason}). ${next}`);
  }
}

async function cloudflare(model, input, timeoutMs) {
  if (!HAS_CLOUDFLARE) {
    throw new HttpError(503, "Cloudflare is not configured on the server. Set CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN.", "not_configured");
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
      throw new HttpError(504, "Cloudflare took too long. Please try again.", "timeout");
    }
    throw new HttpError(502, "Could not reach Cloudflare.", "network");
  }
  const text = await r.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch (e) {
    throw new HttpError(502, "Cloudflare returned an invalid response.", "invalid_response");
  }
  if (!r.ok || !data.success) {
    const detail = data.errors && data.errors[0] && data.errors[0].message ? data.errors[0].message : `HTTP ${r.status}`;
    if (r.status === 401 || r.status === 403) {
      throw new HttpError(502, "Cloudflare rejected the API credentials. Check the server settings.", "auth");
    }
    const daily = /daily free allocation|neurons/i.test(detail);
    if (r.status === 429 || daily) {
      throw new HttpError(
        429,
        daily
          ? "The daily free Cloudflare AI limit is used up."
          : "Cloudflare rate limit reached. Please wait a minute and try again.",
        daily ? "daily_quota" : "rate_limit"
      );
    }
    throw new HttpError(502, `Cloudflare error: ${String(detail).slice(0, 180)}`, "service");
  }
  return data.result || {};
}

const PROMPT_SYSTEM = `You write English prompts for a photorealistic text-to-image model.
Read the slide text below. It may be written in Nepali or another language.
Reply with ONE English image prompt of at most 35 words that captures the main idea.
Describe a concrete scene: the setting, people or objects, and the lighting.
Do not include any text, captions, letters, logos or watermarks in the image.

Safety rules that must always be followed:
- The picture will be used in religious and cultural videos, so it must be respectful and suitable for all ages.
- Every person must be fully clothed in modest traditional attire. Never show nudity, underwear, swimwear, revealing or tight clothing, bare chests, or sexual or romantic poses.
- No violence, blood, weapons, drugs, alcohol, smoking, gambling, horror or disturbing imagery.
- Never mock or disrespect any religion, deity, temple, holy place, flag or community.
- If the slide text suggests anything unsafe, choose a calm, respectful and symbolic alternative instead.

Return only the prompt. No quotes, labels, or explanation.`;

function cleanPrompt(value) {
  return String(value || "")
    .replace(/\r?\n+/g, " ")
    .replace(/^["'\s]+|["'\s]+$/g, "")
    .replace(/^(?:image\s+)?prompt\s*:\s*/i, "")
    .replace(/\s+/g, " ")
    .trim();
}

async function pollinationsFetch(pathAndQuery, timeoutMs, init) {
  if (!HAS_POLLINATIONS) {
    throw new HttpError(503, "Pollinations fallback is not configured. Set POLLINATIONS_API.", "not_configured");
  }
  let r;
  try {
    r = await fetch(POLLINATIONS_BASE + pathAndQuery, {
      ...(init || {}),
      headers: {
        Authorization: `Bearer ${POLLINATIONS_API}`,
        ...((init && init.headers) || {}),
      },
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch (e) {
    if (e && (e.name === "TimeoutError" || e.name === "AbortError")) {
      throw new HttpError(504, "Pollinations took too long. Please try again.", "timeout");
    }
    throw new HttpError(502, "Could not reach Pollinations.", "network");
  }
  return r;
}

function pollinationsError(status, detail) {
  if (status === 401 || status === 403) {
    return new HttpError(502, "Pollinations rejected the API key. Check POLLINATIONS_API.", "auth");
  }
  if (status === 402) {
    return new HttpError(502, "The Pollinations balance is used up. Add Pollen or wait for the free allowance.", "payment");
  }
  if (status === 429) {
    return new HttpError(429, "Pollinations rate limit reached. Please wait and try again.", "rate_limit");
  }
  return new HttpError(502, `Pollinations error: ${String(detail).slice(0, 180)}`, "service");
}

async function summarizeCloudflare(text) {
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
  const prompt = cleanPrompt(result.response);
  if (!prompt) throw new HttpError(502, "Cloudflare could not write an image prompt.", "invalid_response");
  return prompt;
}

async function summarizePollinations(text) {
  const r = await pollinationsFetch("/v1/chat/completions", 45000, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: POLLINATIONS_TEXT_MODEL || "openai",
      messages: [
        { role: "system", content: PROMPT_SYSTEM },
        { role: "user", content: text.slice(0, 4000) },
      ],
      max_tokens: 120,
      temperature: 0.5,
    }),
  });
  const body = await r.text();
  if (!r.ok) throw pollinationsError(r.status, body);
  let data = null;
  try {
    data = JSON.parse(body);
  } catch (e) {
    throw new HttpError(502, "Pollinations returned an invalid text response.", "invalid_response");
  }
  const content = data && data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content;
  const prompt = cleanPrompt(content);
  if (!prompt) throw new HttpError(502, "Pollinations could not write an image prompt.", "invalid_response");
  return prompt;
}

async function summarize(text) {
  const errors = [];
  let prompt = "";
  if (cloudflareAvailable()) {
    try {
      prompt = await summarizeCloudflare(text);
    } catch (e) {
      noteCloudflareFailure(e);
      errors.push(`Cloudflare: ${e.message}`);
    }
  } else if (HAS_CLOUDFLARE) {
    errors.push(`Cloudflare: temporarily unavailable (${cfDownReason}).`);
  }
  if (!prompt && HAS_POLLINATIONS) {
    try {
      prompt = await summarizePollinations(text);
    } catch (e) {
      errors.push(`Pollinations: ${e.message}`);
    }
  }
  if (!prompt) {
    console.warn(`AI prompt summary failed; using the safe fallback scene. ${errors.join(" ")}`);
    return SAFE_FALLBACK;
  }
  if (unsafePrompt(prompt)) return SAFE_FALLBACK;
  return prompt.slice(0, 600);
}

async function generateCloudflareImage(prompt) {
  const result = await cloudflare(
    IMAGE_MODEL,
    { prompt, steps: IMAGE_STEPS },
    60000
  );
  if (!result.image) throw new HttpError(502, "Cloudflare did not return an image.", "invalid_response");
  return `data:image/jpeg;base64,${result.image}`;
}

async function generatePollinationsImage(prompt) {
  const u = new URL(`${POLLINATIONS_BASE}/image/${encodeURIComponent(prompt)}`);
  u.searchParams.set("model", POLLINATIONS_IMAGE_MODEL);
  u.searchParams.set("width", "1024");
  u.searchParams.set("height", "1024");
  u.searchParams.set("safe", "true");
  u.searchParams.set("nologo", "true");
  u.searchParams.set("seed", String(Math.floor(Math.random() * 1e9)));
  u.searchParams.set("negative_prompt", "nudity, naked, sexual, violence, blood, weapons, drugs, alcohol, text, watermark, logo");
  const r = await pollinationsFetch(u.pathname + u.search, 90000);
  if (!r.ok) {
    const detail = await r.text();
    throw pollinationsError(r.status, detail);
  }
  const type = String(r.headers.get("content-type") || "").split(";")[0].trim().toLowerCase();
  if (!type.startsWith("image/")) {
    const detail = await r.text();
    throw new HttpError(502, `Pollinations returned ${type || "an unknown response"} instead of an image: ${String(detail).slice(0, 120)}`, "invalid_response");
  }
  const image = Buffer.from(await r.arrayBuffer());
  if (!image.length) throw new HttpError(502, "Pollinations returned an empty image.", "invalid_response");
  return `data:${type};base64,${image.toString("base64")}`;
}

async function generateImage(prompt) {
  const safePrompt = safeImagePrompt(prompt);
  const errors = [];
  if (cloudflareAvailable()) {
    try {
      return { image: await generateCloudflareImage(safePrompt), provider: "cloudflare" };
    } catch (e) {
      noteCloudflareFailure(e);
      errors.push(`Cloudflare: ${e.message}`);
    }
  } else if (HAS_CLOUDFLARE) {
    errors.push(`Cloudflare: temporarily unavailable (${cfDownReason}).`);
  }
  if (HAS_POLLINATIONS) {
    try {
      return { image: await generatePollinationsImage(safePrompt), provider: "pollinations" };
    } catch (e) {
      errors.push(`Pollinations: ${e.message}`);
    }
  } else {
    errors.push("Pollinations: fallback is not configured (set POLLINATIONS_API).");
  }
  throw new HttpError(502, `Could not create the picture. ${errors.join(" ")}`, "all_failed");
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
    let prompt;
    if (explicit && !unsafePrompt(explicit)) prompt = explicit;
    else if (text) prompt = await summarize(text);
    else prompt = SAFE_FALLBACK;
    if (unsafePrompt(prompt)) prompt = SAFE_FALLBACK;
    if (explicit && prompt !== explicit) console.warn("Unsafe @img prompt was replaced with a safe scene.");
    const result = await generateImage(prompt);
    console.log(`AI picture ${Date.now() - started}ms via ${result.provider} | ${prompt.slice(0, 100)}`);
    sendJSON(res, 200, { success: true, prompt, image: result.image, provider: result.provider });
  } catch (e) {
    const status = e instanceof HttpError ? e.status : 500;
    if (!(e instanceof HttpError)) console.error("slide-image:", e);
    sendJSON(res, status, { success: false, error: e.message || "Picture generation failed." });
  }
}

const RASHI_DIR = path.join(__dirname, "Rashi");
const RASHI_MIME = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".gif": "image/gif",
  ".svg": "image/svg+xml",
};

/* Serve the local rashi pictures. The template asks for "0.png"; older
   copies may only have "0.jpg", so a missing .png falls back to the same name
   with a .jpg extension. Only plain file names inside Rashi/ are allowed.
   These pictures are replaced locally, so the browser must revalidate them. */
function serveRashi(req, res, pathname) {
  if (req.method !== "GET" && req.method !== "HEAD") {
    res.writeHead(405, { "Content-Type": "text/plain; charset=utf-8", Allow: "GET, HEAD" });
    return res.end("Method not allowed");
  }
  let name = pathname.replace(/^\/[Rr]ashi\//, "");
  try {
    name = decodeURIComponent(name);
  } catch (e) {
    name = "";
  }
  name = path.basename(name);
  if (!name || name === "." || name === ".." || !/^[A-Za-z0-9._-]+$/.test(name)) {
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    return res.end("Not found");
  }
  const candidates = [name];
  if (/\.png$/i.test(name)) candidates.push(name.replace(/\.png$/i, ".jpg"));
  if (/\.jpe?g$/i.test(name)) candidates.push(name.replace(/\.jpe?g$/i, ".png"));
  const send404 = () => {
    res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    res.end("Not found");
  };
  const next = (i) => {
    if (i >= candidates.length) return send404();
    const file = path.join(RASHI_DIR, candidates[i]);
    if (!file.startsWith(RASHI_DIR + path.sep)) return send404();
    fs.readFile(file, (err, data) => {
      if (err) return next(i + 1);
      const ext = path.extname(candidates[i]).toLowerCase();
      res.writeHead(200, {
        "Content-Type": RASHI_MIME[ext] || "application/octet-stream",
        "Cache-Control": "no-cache",
      });
      res.end(req.method === "HEAD" ? undefined : data);
    });
  };
  next(0);
}

/* ============================== Nepali TTS ============================== */
function looksLikeWav(buf) {
  return !!buf && buf.length > 12 && buf.toString("ascii", 0, 4) === "RIFF" && buf.toString("ascii", 8, 12) === "WAVE";
}

async function ttsYourVoice(text) {
  const r = await fetch("https://yourvoic.com/api/v1/tts/stream", {
    method: "POST",
    headers: {
      "X-API-Key": YOURVOICE_API_KEY,
      "Content-Type": "application/json",
    },
    signal: AbortSignal.timeout(90000),
    body: JSON.stringify({
      text,
      voice: YOURVOICE_VOICE,
      language: YOURVOICE_LANGUAGE,
      model: YOURVOICE_MODEL,
      speed: 1,
      pitch: 1,
      response_format: "wav",
    }),
  });
  if (!r.ok) {
    let detail = "";
    try {
      const data = await r.json();
      const err = data && data.error;
      detail = typeof err === "string" ? err : (err && (err.message || err.details)) || "";
    } catch (e) {
      try { detail = (await r.text()).slice(0, 300); } catch (e2) { }
    }
    throw new Error("YourVoice HTTP " + r.status + (detail ? ": " + detail : ""));
  }
  const buf = Buffer.from(await r.arrayBuffer());
  if (!looksLikeWav(buf)) {
    let detail = "";
    try {
      const data = JSON.parse(buf.toString("utf8"));
      const err = data && data.error;
      detail = typeof err === "string" ? err : (err && (err.message || err.details)) || "";
    } catch (e) { }
    throw new Error(detail ? "YourVoice: " + detail : "YourVoice returned non-WAV audio");
  }
  return buf;
}

function ttsCacheFile(text) {
  const voice = [YOURVOICE_VOICE, YOURVOICE_LANGUAGE, YOURVOICE_MODEL].join("|");
  const hash = crypto.createHash("sha256").update("yourvoice|" + voice + "|" + text).digest("hex");
  return path.join(TTS_CACHE_DIR, hash + ".wav");
}

async function synthesizeTts(text) {
  const clean = String(text || "").replace(/\s+/g, " ").trim().slice(0, TTS_MAX_CHARS);
  if (!clean) throw new Error("Empty text");
  if (!HAS_YOURVOICE) throw new Error("YourVoice is not configured. Add YOURVOICE_API_KEY to .env.");
  const file = ttsCacheFile(clean);
  if (fs.existsSync(file)) return { buf: fs.readFileSync(file), provider: "yourvoice", cached: true };
  const buf = await ttsYourVoice(clean);
  fs.mkdirSync(TTS_CACHE_DIR, { recursive: true });
  fs.writeFileSync(file, buf);
  return { buf, provider: "yourvoice", cached: false };
}

function serveTts(req, res) {
  if (req.method !== "POST") {
    res.writeHead(405, { "Content-Type": "text/plain; charset=utf-8", Allow: "POST" });
    return res.end("Method not allowed");
  }
  let body = "";
  req.on("data", (chunk) => {
    body += chunk;
    if (body.length > 30000) { try { req.destroy(); } catch (e) { } }
  });
  req.on("end", async () => {
    try {
      const data = JSON.parse(body || "{}");
      const result = await synthesizeTts(data.text);
      res.writeHead(200, {
        "Content-Type": "audio/wav",
        "Content-Length": result.buf.length,
        "Cache-Control": "public, max-age=86400",
        "X-TTS-Provider": result.provider,
        "X-TTS-Cached": result.cached ? "1" : "0",
      });
      res.end(result.buf);
    } catch (e) {
      res.writeHead(500, { "Content-Type": "application/json; charset=utf-8" });
      res.end(JSON.stringify({ error: String((e && e.message) || e) }));
    }
  });
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

  if (url.pathname === "/api/tts") {
    serveTts(req, res);
    return;
  }

  if (/^\/[Rr]ashi\//.test(url.pathname)) {
    serveRashi(req, res, url.pathname);
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

if (require.main === module) {
  server.listen(PORT, "0.0.0.0", () => {
    console.log(`Server running on port ${PORT}`);
    const providers = [];
    if (HAS_CLOUDFLARE) providers.push("Cloudflare");
    if (HAS_POLLINATIONS) providers.push("Pollinations");
    if (!providers.length) {
      console.warn("No AI provider is configured. Set CLOUDFLARE_ACCOUNT_ID/CLOUDFLARE_API_TOKEN or POLLINATIONS_API.");
    } else {
      console.log(`AI providers: ${providers.join(" -> ")}`);
      if (!HAS_CLOUDFLARE) console.warn("Cloudflare is not configured; using Pollinations only.");
      if (!HAS_POLLINATIONS) console.warn("Pollinations fallback is not configured; using Cloudflare only.");
    }
    if (HAS_YOURVOICE) console.log("Nepali TTS: YourVoice (" + YOURVOICE_VOICE + ", " + YOURVOICE_LANGUAGE + ")");
    else console.warn("Nepali TTS: YourVoice is not configured. Set YOURVOICE_API_KEY in .env.");
  });
}

module.exports = { unsafePrompt, safeImagePrompt, SAFE_FALLBACK, summarize, generateImage };
