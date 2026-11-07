/* Free Nepali narration through Microsoft Edge's online neural voice.
   The service needs the same v2 Sec-MS-GEC token and browser headers that the
   Edge Read Aloud extension uses. No API key is required. */

const crypto = require("crypto");
const WebSocket = require("ws");

const EDGE_TOKEN = "6A5AA1D4EAFF4E9FB37E23D68491D6F4";
const EDGE_CHROMIUM = "143.0.3650.75";
const EDGE_GEC_VERSION = "2-" + EDGE_CHROMIUM;
const EDGE_WSS = "wss://speech.platform.bing.com/consumer/speech/synthesize/readaloud/edge/v1";
const EDGE_ORIGIN = "chrome-extension://jdiccldimpdaibmpdkjnbmckianbfold";
const EDGE_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0";
const WIN_EPOCH = 11644473600;
const U32 = 0xFFFFFFFF;

/* Microsoft's v2 token uses a modified SHA-256 plus a 64-bit mixing digest.
   It is not the same as a normal SHA-256 hash, so it is implemented here. */
const ROUND = [
  0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5, 0x3956C25B, 0x59F111F1, 0x923F82A4, 0xAB1C5ED5,
  0xD807AA98, 0x12835B01, 0x243185BE, 0x550C7DC3, 0x72BE5D74, 0x80DEB1FE, 0x9BDC06A7, 0xC19BF174,
  0xE49B69C1, 0xEFBE4786, 0x0FC19DC6, 0x240CA1CC, 0x2DE92C6F, 0x4A7484AA, 0x5CB0A9DC, 0x76F988DA,
  0x983E5152, 0xA831C66D, 0xB00327C8, 0xBF597FC7, 0xC6E00BF3, 0xD5A79147, 0x06CA6351, 0x14292967,
  0x27B70A85, 0x2E1B2138, 0x4D2C6DFC, 0x53380D13, 0x650A7354, 0x766A0ABB, 0x81C2C92E, 0x92722C85,
  0xA2BFE8A1, 0xA81A664B, 0xC24B8B70, 0xC76C51A3, 0xD192E819, 0xD6990624, 0xF40E3585, 0x106AA070,
  0x19A4C116, 0x1E376C08, 0x2748774C, 0x34B0BCB5, 0x391C0CB3, 0x4ED8AA4A, 0x5B9CCA4F, 0x682E6FF3,
  0x748F82EE, 0x78A5636F, 0x84C87814, 0x8CC70208, 0x90BEFFFA, 0xA4506CEB, 0xBEF9A3F7, 0xC67178F2,
];
const BLOCK = [...ROUND.slice(0, 14), 0xC9DC06A7, ...ROUND.slice(15)];
const INITIAL = [0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A, 0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19];
const STATE0 = [0xFD9FBEA2, 0x91243CE7, 0xBE499094, 0xCD2E1E0A, 0x6C006F49, 0x04BD35AB, 0xFEB0A7E4, 0x03EFFBD2];
const SCHEDULE = [0xEB24BF9E, 0x1558691F, 0xA0C09EE2, 0x0CFA32BA, 0xA622EE8C, 0xD1DD9491, 0xC0DD25A0, 0xF9E70AB6, 0xF0C31573, 0x7058CE4E, 0x7188E606, 0x00E5AB33, 0xD258B060, 0x72766564];
const ADJ = 0xC9DC06A7;
const SIGMA0_ADJ = 0x059C0B80;
const SIGMA1_ADJ = 0x000B92C0;

const rotr = (x, n) => ((x >>> n) | (x << (32 - n))) >>> 0;
const sigma0 = v => ((v >>> 7) ^ (v << 25) ^ (v >>> 18) ^ (v << 14) ^ (v >>> 3)) >>> 0;
const sigma1 = v => ((v >>> 17) ^ (v << 15) ^ (v >>> 19) ^ (v << 13) ^ (v >>> 10)) >>> 0;

function rounds(state, words, first) {
  let [a, b, c, d, e, f, g, h] = state;
  const K = first === 14 ? BLOCK : ROUND;
  for (let i = first; i < 64; i++) {
    const S1 = (rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)) >>> 0;
    const ch = (g ^ (e & (f ^ g))) >>> 0;
    const t1 = (h + S1 + ch + K[i] + words[i]) >>> 0;
    const S0 = (rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)) >>> 0;
    const maj = ((a & b) | (c & (a | b))) >>> 0;
    const t2 = (S0 + maj) >>> 0;
    h = g; g = f; f = e; e = (d + t1) >>> 0; d = c; c = b; b = a; a = (t1 + t2) >>> 0;
  }
  return [a, b, c, d, e, f, g, h];
}
function expand(words, first = 16) {
  for (let i = first; i < 64; i++) {
    words[i] = (sigma1(words[i - 2]) + words[i - 7] + sigma0(words[i - 15]) + words[i - 16]) >>> 0;
  }
}
function shaInit(d7) {
  const words = new Array(14).fill(0);
  words.push(((d7[0] << 16) | (d7[1] << 8) | d7[2]) >>> 0);
  words.push(((d7[3] << 24) | (d7[4] << 16) | (d7[5] << 8) | d7[6]) >>> 0);
  for (let i = 16; i < 30; i++) {
    let v = SCHEDULE[i - 16];
    if (i - 2 >= 14) v += i === 16 ? (sigma1(words[i - 2]) ^ SIGMA1_ADJ) : sigma1(words[i - 2]);
    if (i - 7 >= 14) v += words[i - 7];
    if (i - 15 >= 14) v += i === 29 ? (sigma0(words[i - 15]) ^ SIGMA0_ADJ) : sigma0(words[i - 15]);
    words.push(v >>> 0);
  }
  words.push((sigma1(words[28]) + words[23] + sigma0(words[15]) + words[14] + ADJ - ROUND[14]) >>> 0);
  expand(words, 31);
  return rounds(STATE0, words, 14).map((x, i) => (x + INITIAL[i]) >>> 0);
}
function shaDigest(data) {
  const length = 57 + data.length;
  const zeros = ((55 - length) % 64 + 64) % 64;
  const lb = Buffer.alloc(8); lb.writeBigUInt64BE(BigInt(length * 8));
  const padded = Buffer.concat([data.subarray(7), Buffer.from([0x80]), Buffer.alloc(zeros), lb]);
  let state = shaInit(data.subarray(0, 7));
  for (let off = 0; off < padded.length; off += 64) {
    const words = [];
    for (let j = 0; j < 16; j++) words.push(padded.readUInt32BE(off + j * 4));
    expand(words);
    const work = rounds(state, words, 0);
    state = state.map((x, i) => (x + work[i]) >>> 0);
  }
  const out = Buffer.alloc(32);
  state.forEach((x, i) => out.writeUInt32BE(x, i * 4));
  return out;
}

const COEFF = [
  [0xE82E91B1, 0xB32700D0], [0x44DE24C6, 0x88DFF51D], [0x3BEB65BC, 0x29514038], [0xC89C5933, 0xB328CBDF],
  [0x8D1EC211, 0xD405B4D5], [0x314EF5D5, 0x26E55F3C], [0xE92491B1, 0x607801C6], [0xF0A5B9D5, 0x82B2C1FB],
  [0x06064CF3, 0xFA51A3DA], [0xDA79FA60, 0x207CC464], [0xBED20560, 0x3C3C74F3], [0x89F9C9F8, 0xD2D14B61],
  [0x35FA38C6, 0xBB04A2C1], [0xCB49E3C6, 0xC5626167],
];
const M = 0xFFFFFFFFn;
const rol16 = v => { v &= M; return ((v << 16n) | (v >> 16n)) & M; };
function wordsLe4Even(buf) {
  const pad = (4 - (buf.length % 4)) % 4;
  const b = Buffer.concat([buf, Buffer.alloc(pad)]);
  const out = [];
  for (let i = 0; i < b.length; i += 4) out.push(BigInt(b.readUInt32LE(i)));
  if (out.length % 2) out.push(0n);
  return out;
}
function cs64(data, digest) {
  const keyA = BigInt(digest.readUInt32LE(0)) | 1n;
  const keyB = BigInt(digest.readUInt32LE(4)) | 1n;
  const factors = [(keyA * 0x82893933n) & M, (keyB * 0x82893933n) & M];
  const terms = [], offsets = [];
  for (let i = 0; i < COEFF.length; i++) {
    terms.push((BigInt(COEFF[i][0]) * factors[i % 2]) & M);
    offsets.push(BigInt(COEFF[i][1]));
  }
  wordsLe4Even(Buffer.concat([Buffer.from([0]), data])).forEach((word, index) => {
    let term = (word * (index % 2 === 0 ? keyA : keyB)) & M;
    let off = (rol16(word) * (index % 2 === 0 ? 0xEF0569FBn : 0xC31713DBn)) & M;
    if (index === 0) {
      term = (term + 0xF2F90B1An * factors[0]) & M;
      off = (off + 0x0B1A0000n) & M;
    }
    terms.push(term); offsets.push(off);
  });
  let swapAcc = 0n, swapLast = 0n, state = 0n, acc = 0n;
  for (let i = 0; i < terms.length; i += 2) {
    const x = terms[i], y = terms[i + 1];
    let t = rol16((offsets[i] + x) & M);
    let q = (t * 0x76F50F34n) & M;
    swapAcc = (swapAcc + ((rol16(q) * 0xC3EFEA97n + q) & M)) & M;
    t = rol16((offsets[i + 1] + y) & M);
    q = (t * 0x1881CE3Cn) & M;
    swapLast = (rol16(q) * 0x35BD1EC9n + q) & M;
    swapAcc = (swapAcc + swapLast) & M;

    state = (state * keyA + x) & M;
    state = (rol16(state) * 0xCF98B111n) & M;
    state = (rol16(state) * 0x87085B9Fn) & M;
    state = (rol16(state) * 0x12CEB96Dn) & M;
    state = (rol16(state) * 0x257E1D83n) & M;
    acc = (acc + state) & M;
    t = (state * keyB + y) & M;
    t = (rol16(t) * 0xA27416F5n) & M;
    t = (rol16(t) * 0xD38396FFn) & M;
    state = (rol16((rol16(t) * 0x7C932B89n) & M) * 0xBFA49F69n) & M;
    acc = (acc + state) & M;
  }
  const out = Buffer.alloc(8);
  out.writeUInt32LE(Number(swapLast ^ state), 0);
  out.writeUInt32LE(Number(swapAcc ^ acc), 4);
  return out.toString("hex").toUpperCase();
}
function tokenHash(data) {
  const digest = shaDigest(data);
  return { cs64: cs64(data, digest), sha256: digest.toString("hex").toUpperCase() };
}
function secMsGec(timestamp = Date.now() / 1000) {
  let ticks = timestamp + WIN_EPOCH;
  ticks -= ticks % 300;
  ticks *= 1e7;
  const { cs64: mixed, sha256 } = tokenHash(Buffer.from(ticks.toFixed(0) + EDGE_TOKEN, "ascii"));
  return mixed + "-" + sha256;
}

function escapeXml(value) {
  return String(value).replace(/[<>&'"]/g, c => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", "'": "&apos;", '"': "&quot;" }[c]));
}

/* The service accepts about 4 KB of SSML per request, so long narration is
   split on word boundaries and the MP3 chunks are joined. */
function splitText(text, maxBytes = 3000) {
  const out = [];
  let rest = String(text || "").trim();
  while (Buffer.byteLength(rest, "utf8") > maxBytes) {
    let bytes = 0, cut = 0, lastSpace = -1;
    for (const ch of rest) {
      const n = Buffer.byteLength(ch, "utf8");
      if (bytes + n > maxBytes) break;
      bytes += n; cut += ch.length;
      if (/\s/.test(ch)) lastSpace = cut;
    }
    if (lastSpace > 0) cut = lastSpace;
    if (cut <= 0) cut = 1;
    out.push(rest.slice(0, cut).trim());
    rest = rest.slice(cut).trim();
  }
  if (rest) out.push(rest);
  return out.filter(Boolean);
}

function edgeChunk(text, voice) {
  return new Promise((resolve, reject) => {
    const id = crypto.randomUUID().replace(/-/g, "");
    const gec = secMsGec();
    const url = `${EDGE_WSS}?TrustedClientToken=${EDGE_TOKEN}&ConnectionId=${id}&Sec-MS-GEC=${encodeURIComponent(gec)}&Sec-MS-GEC-Version=${EDGE_GEC_VERSION}`;
    let ws;
    try {
      ws = new WebSocket(url, {
        headers: {
          "Pragma": "no-cache",
          "Cache-Control": "no-cache",
          "Origin": EDGE_ORIGIN,
          "User-Agent": EDGE_UA,
          "Accept-Encoding": "gzip, deflate, br, zstd",
          "Accept-Language": "en-US,en;q=0.9",
          "Cookie": "muid=" + crypto.randomBytes(16).toString("hex").toUpperCase() + ";",
        },
      });
    } catch (e) { reject(e); return }
    const chunks = [];
    let settled = false;
    const timer = setTimeout(() => finish(new Error("Edge TTS timed out")), 30000);
    function finish(err) {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      try { ws.close() } catch (e) { }
      if (err) reject(err);
      else if (!chunks.length) reject(new Error("Edge TTS returned no audio"));
      else resolve(Buffer.concat(chunks));
    }
    ws.on("open", () => {
      const now = new Date().toUTCString();
      ws.send(`X-Timestamp:${now}\r\nContent-Type:application/json; charset=utf-8\r\nPath:speech.config\r\n\r\n` +
        '{"context":{"synthesis":{"audio":{"metadataoptions":{"sentenceBoundaryEnabled":"false","wordBoundaryEnabled":"false"},"outputFormat":"audio-24khz-48kbitrate-mono-mp3"}}}}');
      const ssml = `<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='ne-NP'><voice name='${voice}'><prosody pitch='+0Hz' rate='+0%' volume='+0%'>${escapeXml(text)}</prosody></voice></speak>`;
      ws.send(`X-RequestId:${id}\r\nContent-Type:application/ssml+xml\r\nX-Timestamp:${now}Z\r\nPath:ssml\r\n\r\n${ssml}`);
    });
    ws.on("message", (data, isBinary) => {
      if (!isBinary) {
        if (data.toString().includes("Path:turn.end")) finish();
        return;
      }
      const buf = Buffer.from(data);
      if (buf.length < 2) return;
      const hl = buf.readUInt16BE(0);
      if (buf.length < 2 + hl) return;
      const header = buf.subarray(2, 2 + hl).toString("utf8");
      if (/Path:\s*audio/i.test(header)) chunks.push(buf.subarray(2 + hl));
    });
    ws.on("error", e => finish(e instanceof Error ? e : new Error("Edge TTS connection failed")));
    ws.on("close", () => { if (!settled) finish(new Error("Edge TTS connection closed")); });
  });
}

async function synthesizeEdge(text, voice = "ne-NP-HemkalaNeural") {
  const clean = String(text || "").replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F]/g, " ").replace(/\s+/g, " ").trim();
  if (!clean) throw new Error("Empty text");
  const parts = splitText(clean, 3000);
  const out = [];
  for (const part of parts) {
    out.push(await edgeChunk(part, voice));
    await new Promise(r => setTimeout(r, 80));
  }
  return Buffer.concat(out);
}

module.exports = { synthesizeEdge, secMsGec, splitText };
