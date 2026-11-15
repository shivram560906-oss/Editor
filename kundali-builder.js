/* ═══════════════════════════════════════════════════════════════════
   Kundali Manual Timeline Builder
   ------------------------------------------------------------------
   This module is loaded after the editor script, so it reuses the real
   chart, table, card and SVG builders from index.html. Nothing here
   replaces the original 32-slide default path. It only creates a manual
   element timeline when the user explicitly selects elements.
   ═══════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  const q = id => document.getElementById(id);
  const KB_VERSION = 1;
  const KB_SAFE = { l: 46, r: 46, t: 112, b: 56 };
  const KB_FONT = '"Noto Sans Devanagari","Mukta","Hind",sans-serif';
  const KB_NUM = ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९'];

  /* ───────────────────────── templates ───────────────────────── */

  const KB_TPLS = {
    cosmic: {
      id: 'cosmic', name: 'Cosmic 3D', ne: 'कस्मिक ३डी', tag: 'SPACE · DEPTH',
      desc: 'ब्रह्माण्ड, कक्षा र गहिराइमा आधारित सिनेम्याटिक 3D.',
      bg: ['#040814', '#0b1b3a', '#02040a'], accent: '#f6d365', accent2: '#6ee7ff',
      ink: '#f8fbff', mut: '#9fb0d0', card: 'rgba(10,24,52,.72)', line: 'rgba(246,211,101,.35)',
      font: 'Mukta', display: 'Rozha One', motion: 'cosmic', radius: 24, seed: 11
    },
    nebula: {
      id: 'nebula', name: 'Nebula Glass', ne: 'नेबुला ग्लास', tag: 'NEBULA · GLASS',
      desc: 'बैजनी–निलो नीहारिका, तैरिने काँचका प्यानल र नरम प्रकाश.',
      bg: ['#0b0422', '#241052', '#05010f'], accent: '#e9d5ff', accent2: '#22d3ee',
      ink: '#f8f5ff', mut: '#c4b5fd', card: 'rgba(23,11,52,.74)', line: 'rgba(233,213,255,.32)',
      font: 'Hind', display: 'Baloo 2', motion: 'nebula', radius: 26, seed: 41
    },
    vedic: {
      id: 'vedic', name: 'Vedic Parchment', ne: 'वैदिक पोथी', tag: 'PARCHMENT · MANDALA',
      desc: 'पुरानो पोथीको कागज, मारुन–सुनौलो किनारा र राशि मण्डल.',
      bg: ['#f6e7c8', '#efdcb8', '#e7cfa6'], accent: '#8a1c1c', accent2: '#a16207',
      ink: '#2b160d', mut: '#5b3d26', card: 'rgba(251,241,220,.93)', line: 'rgba(138,28,28,.28)',
      font: 'Tiro Devanagari Hindi', display: 'Rozha One', motion: 'vedic', radius: 6, seed: 53
    },
    orbit: {
      id: 'orbit', name: 'Solar Orbit', ne: 'सोलार अर्बिट', tag: 'SOLAR · HUD',
      desc: 'सौर्यमण्डलको कक्षीय गति, नियोन HUD र गाढा टिल प्यानल.',
      bg: ['#020e10', '#06252a', '#010607'], accent: '#a3e635', accent2: '#22d3ee',
      ink: '#ecfeff', mut: '#8fd8cf', card: 'rgba(4,24,28,.82)', line: 'rgba(163,230,53,.32)',
      font: 'Mukta', display: 'Yatra One', motion: 'orbit', radius: 10, seed: 67
    },
    royal: {
      id: 'royal', name: 'Royal Heritage', ne: 'रोयल हेरिटेज', tag: 'HERITAGE · GOLD',
      desc: 'राजसी मारुन, सुनौलो किनारा र परम्परागत आर्क.',
      bg: ['#21070e', '#5b1e2b', '#140308'], accent: '#f1c46a', accent2: '#d95c6a',
      ink: '#fff4df', mut: '#d9b98f', card: 'rgba(54,16,26,.82)', line: 'rgba(241,196,106,.45)',
      font: 'Tiro Devanagari Hindi', display: 'Rozha One', motion: 'royal', radius: 10, seed: 23
    },
    glass: {
      id: 'glass', name: 'Glassmorphism Pro', ne: 'ग्लासमोर्फिज्म प्रो', tag: 'GLASS · LIGHT',
      desc: 'काँचजस्तो पारदर्शी तह, नरम प्रकाश र गहिराइ.',
      bg: ['#eef4ff', '#dbeafe', '#f5e9ff'], accent: '#7c3aed', accent2: '#06b6d4',
      ink: '#172554', mut: '#475569', card: 'rgba(255,255,255,.55)', line: 'rgba(124,58,237,.24)',
      font: 'Hind', display: 'Mukta', motion: 'glass', radius: 26, seed: 37
    },
    cinematic: {
      id: 'cinematic', name: 'Cinematic Universe', ne: 'सिनेम्याटिक युनिभर्स', tag: 'CINEMA · FRAME',
      desc: 'कालो फ्रेम, एम्बर प्रकाश र चलचित्रजस्तो ट्रान्जिसन.',
      bg: ['#050505', '#1a1005', '#000000'], accent: '#e8b04b', accent2: '#ff6b3d',
      ink: '#fff7e8', mut: '#b9a98f', card: 'rgba(18,14,8,.88)', line: 'rgba(232,176,75,.4)',
      font: 'Tiro Devanagari Hindi', display: 'Rozha One', motion: 'cinematic', radius: 6, seed: 41
    },
    neon: {
      id: 'neon', name: 'Futuristic Neon', ne: 'फ्युचरिस्टिक नियोन', tag: 'NEON · GRID',
      desc: 'भविष्यको नियोन ग्रिड, HUD र चम्किलो ऊर्जा.',
      bg: ['#02040a', '#06121f', '#000000'], accent: '#22d3ee', accent2: '#f472b6',
      ink: '#eaffff', mut: '#7dd3fc', card: 'rgba(3,17,30,.82)', line: 'rgba(34,211,238,.4)',
      font: 'Mukta', display: 'Yatra One', motion: 'neon', radius: 12, seed: 53
    },
    minimal: {
      id: 'minimal', name: 'Minimal Luxury', ne: 'मिनिमल लक्जरी', tag: 'MINIMAL · LUXE',
      desc: 'सफा सेतो, पातलो रेखा र प्रिमियम शान्तता.',
      bg: ['#fbf7ef', '#f3ead9', '#e9dcc7'], accent: '#1f1a14', accent2: '#b8863b',
      ink: '#17130e', mut: '#6b5b47', card: 'rgba(255,255,255,.72)', line: 'rgba(31,26,20,.16)',
      font: 'Laila', display: 'Rozha One', motion: 'minimal', radius: 2, seed: 67
    },
    ancient: {
      id: 'ancient', name: 'Ancient Astrology', ne: 'प्राचीन ज्योतिष', tag: 'VEDIC · PARCHMENT',
      desc: 'पुरानो पोथी, मण्डल र वैदिक ज्योतिषीय भाव.',
      bg: ['#f4e4c3', '#e8cfa5', '#d8b47e'], accent: '#7f1d1d', accent2: '#b45309',
      ink: '#2b160d', mut: '#6b4a2f', card: 'rgba(255,247,230,.84)', line: 'rgba(127,29,29,.35)',
      font: 'Tiro Devanagari Hindi', display: 'Yatra One', motion: 'ancient', radius: 4, seed: 71
    },
    floating: {
      id: 'floating', name: 'Floating Dimensions', ne: 'फ्लोटिङ डाइमेन्सन्स', tag: 'FLOAT · 3D',
      desc: 'हावामा तैरिएका तह, परिप्रेक्ष्य र नरम छाया.',
      bg: ['#060b1a', '#0f1f3d', '#03060f'], accent: '#a78bfa', accent2: '#38bdf8',
      ink: '#f5f7ff', mut: '#a5b4fc', card: 'rgba(18,32,64,.65)', line: 'rgba(167,139,250,.4)',
      font: 'Hind', display: 'Baloo 2', motion: 'floating', radius: 22, seed: 83
    },
    golden: {
      id: 'golden', name: 'Golden Galaxy', ne: 'गोल्डेन ग्यालेक्सी', tag: 'GALAXY · GOLD',
      desc: 'सुनौलो आकाशगंगा, तारा र शाही चमक.',
      bg: ['#050505', '#12100a', '#000000'], accent: '#ffd76a', accent2: '#d4af37',
      ink: '#fff8e1', mut: '#c7a86a', card: 'rgba(20,16,8,.78)', line: 'rgba(255,215,106,.42)',
      font: 'Laila', display: 'Rozha One', motion: 'golden', radius: 18, seed: 97
    },
    nextgen: {
      id: 'nextgen', name: 'Next-Gen Interactive', ne: 'नेक्स्ट-जेन इन्टरएक्टिभ', tag: 'HUD · LIVE',
      desc: 'HUD, लाइभ डेटा र चलायमान 3D इन्टरफेस.',
      bg: ['#031414', '#062a2a', '#010b0b'], accent: '#a3e635', accent2: '#2dd4bf',
      ink: '#ecfeff', mut: '#67e8f9', card: 'rgba(5,35,35,.72)', line: 'rgba(163,230,53,.35)',
      font: 'Hind', display: 'Mukta', motion: 'nextgen', radius: 14, seed: 101
    }
  };
  const KB_TPL_LIST = Object.values(KB_TPLS);

  const KB_ANIM = {
    auto: 'Template default', fade: 'Fade', rise: 'Rise', zoom: 'Zoom', flip3d: '3D Flip',
    rotate3d: '3D Rotate', cinematic: 'Cinematic', parallax: 'Parallax', reveal: 'Reveal',
    glow: 'Glow bloom', float: 'Float', slide: 'Slide', depth: 'Depth push'
  };
  const KB_ENTRY = {
    auto: 'Template default', fade: 'Fade', rise: 'Rise', zoom: 'Zoom', flip: 'Flip',
    rotate: 'Rotate', slide: 'Slide', reveal: 'Wipe reveal', glow: 'Glow'
  };
  const KB_EXIT = { none: 'None', fade: 'Fade out', zoom: 'Zoom out', slide: 'Slide out', glow: 'Glow out' };
  const KB_TRANS = { smooth: 'Smooth', dissolve: 'Dissolve', cut: 'Cut', wipe: 'Wipe', zoom: 'Zoom through' };
  const KB_BG = { auto: 'Template card', glass: 'Glass', dark: 'Dark solid', light: 'Light solid', none: 'No card' };
  const KB_ALIGN = { center: 'Center', left: 'Left', right: 'Right' };

  function kbNum(n) { return String(n).replace(/\d/g, d => KB_NUM[+d]); }
  function kbEsc(s) { return esc(s == null ? '' : String(s)); }
  function kbAttr(s) { return kbEsc(s).replace(/"/g, '&quot;'); }
  function kbU(W, H) { return Math.sqrt(W * H / (720 * 1280)); }
  function kbClamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function kbHash(s) { let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) } return (h >>> 0).toString(36) }

  /* ───────────────────── element catalog ───────────────────── */

  let kbSeq = 0;
  function kbDur(type) {
    return ({ heading: 5.2, chart: 8.4, table: 8, report: 7.4, graph: 8, banner: 6, cards: 7, footer: 5, art: 7, list: 7.4, note: 6.2 })[type] || 6.8;
  }
  function kbEl(page, pageTitle, type, name, bbox, inner, dur) {
    return { id: 'kbe-' + page + '-' + (++kbSeq), page: page, pageTitle: pageTitle, type: type, name: name, bbox: bbox, inner: inner, dur: dur || kbDur(type) };
  }
  function kbPage(no, title, sub, elements) {
    return { no: no, title: title, sub: sub, elements: elements.filter(Boolean) };
  }
  function kbHeader(no, title, sub) {
    /* Only the real title is shown. The old small "page number + subtitle"
       line at the top-left has been removed from every manual card. */
    let s = '';
    s += '<rect x="46" y="76" width="56" height="4" rx="2" fill="#e8b923"/>';
    s += kunT(46, 116, title, 32, '#f6d365', 700);
    s += '<line x1="46" y1="148" x2="674" y2="148" stroke="#2b3856" stroke-width="1.5"/>';
    return kbEl(no, title, 'heading', title + ' — शीर्षक', [46, 64, 628, 100], s, 5.2);
  }
  function kbFooter(no, title) {
    let s = '<line x1="46" y1="1214" x2="674" y2="1214" stroke="#2b3856" stroke-width="1"/>';
    s += kunT(46, 1238, 'Kundali-Desktop · वास्तविक गणना', 12, '#7183a8', 500);
    s += kunT(674, 1238, 'पृष्ठ ' + neNum(no), 12, '#7183a8', 500, 'end');
    return kbEl(no, title, 'footer', 'फुटर — पृष्ठ ' + neNum(no), [46, 1204, 628, 54], s, 4.8);
  }
  function kbChartEl(no, title, houses, lagna, name, x, y, size, opts) {
    return kbEl(no, title, 'chart', name, [x, y, size, size], kunChart(houses, lagna, x, y, size, opts), 8.4);
  }
  function kbCardEl(no, title, name, x, y, w, h, label, value, accent, opts, type) {
    return kbEl(no, title, type || 'cards', name, [x, y, w, h], kunCard(x, y, w, h, label, value, accent, opts), 6.6);
  }
  function kbTableEl(no, title, name, x, y, w, cols, rows, opts, dur) {
    const rowH = opts.rowH || 56, headH = opts.headH || 50;
    return kbEl(no, title, 'table', name, [x, y, w, headH + rows.length * rowH], kunTable(x, y, w, cols, rows, opts), dur || 8);
  }
  function kbN(v) { return v == null || v === '' ? '—' : neNum(v); }
  function kbParse(v) {
    const s = String(v == null ? '' : v).replace(/[०-९]/g, d => String(KB_NUM.indexOf(d))).replace(/[^\d.-]/g, '');
    return s === '' || s === '-' ? NaN : +s;
  }
  function kbJdIso(jd) {
    try {
      const r = kunJulianToGregorian(+jd);
      return r && r[0] ? r[0] : '';
    } catch (e) { return ''; }
  }
  function kbJdNe(jd) {
    const iso = kbJdIso(jd);
    return iso ? kunDateNe(iso) : '—';
  }
  function kbSignOfLon(lon) {
    const v = ((+lon % 360) + 360) % 360;
    return Math.floor(v / 30) + 1;
  }
  function kbLonInSign(lon) {
    const v = ((+lon % 360) + 360) % 360;
    return v - Math.floor(v / 30) * 30;
  }
  function kbPointHouses(points, lagna) {
    const out = {};
    for (let h = 1; h <= 12; h++) out[h] = [];
    (points || []).forEach(pt => {
      const h = (((+pt.sign || 1) - (+lagna || 1)) % 12 + 12) % 12 + 1;
      if (out[h]) out[h].push(pt.ab);
    });
    return out;
  }
  function kbIsoBsYear(iso) {
    try {
      const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || '');
      if (!m) return '';
      const b = adToBs(new Date(Date.UTC(+m[1], +m[2] - 1, +m[3])));
      return b ? b.y : '';
    } catch (e) { return ''; }
  }
  function kbYearBs(y) {
    try {
      const b = adToBs(new Date(Date.UTC(+y, 0, 1)));
      return b ? b.y : '';
    } catch (e) { return ''; }
  }
  function kbYearRangeBs(a, b) {
    const y1 = kbYearBs(a), y2 = kbYearBs(b);
    if (!y1 && !y2) return '—';
    return neNum(y1 || 0) + ' – ' + neNum(y2 || 0);
  }
  function kbAb(name) { return KUN_AB[name] || KUN_NE[name] || name || '—'; }
  function kbLord(name) {
    if (!name) return '—';
    if (KUN_NE[name]) return KUN_NE[name];
    return String(name).split('/').map(n => KUN_NE[n] || n).join('/');
  }

  /* ─────────────── Janmapatrika (कुण्डली निर्माण) ───────────────
     The desktop app's Janmapatrika document, rebuilt as pure SVG so the
     same real element can be used by AUTOMATIC card 11 and by the manual
     element catalog. Every value comes from the live API response; this
     is not a screenshot and it has no placeholder data. */
  const KB_JP = {
    paper: '#f1f8eb', deep: '#e6f1df', red: '#9b183c', green: '#087329',
    blue: '#101453', gold: '#9a7a12', black: '#171717', gray: '#5f625b'
  };
  const KB_JP_FONT = 'Nirmala UI, Noto Sans Devanagari, Mangal, serif';
  const KB_JP_UNAVAILABLE = 'उपलब्ध छैन';
  const KB_JP_SIGNS = {
    1: 'मेष', 2: 'वृष', 3: 'मिथुन', 4: 'कर्कट', 5: 'सिंह', 6: 'कन्या',
    7: 'तुला', 8: 'वृश्चिक', 9: 'धनु', 10: 'मकर', 11: 'कुम्भ', 12: 'मीन'
  };
  const KB_JP_PLANETS = {
    Lagna: 'लग्न', Sun: 'सूर्य', Moon: 'चन्द्र', Mars: 'मङ्गल',
    Mercury: 'बुध', Jupiter: 'गुरु', Venus: 'शुक्र', Saturn: 'शनि',
    Rahu: 'राहु', Ketu: 'केतु'
  };
  const KB_JP_VIM = [
    ['Sun', 'सूर्य', 6], ['Moon', 'चन्द्र', 10], ['Mars', 'मङ्गल', 7],
    ['Rahu', 'राहु', 18], ['Jupiter', 'गुरु', 16], ['Saturn', 'शनि', 19],
    ['Mercury', 'बुध', 17], ['Ketu', 'केतु', 7], ['Venus', 'शुक्र', 20]
  ];
  const KB_JP_YOGINI = [
    ['Mangala', 'मङ्गला', 1], ['Pingala', 'पिङ्गला', 2],
    ['Dhanya', 'धान्या', 3], ['Bhramari', 'भ्रामरी', 4],
    ['Bhadrika', 'भद्रिका', 5], ['Ulka', 'उल्का', 6],
    ['Siddha', 'सिद्धा', 7], ['Sankata', 'संकटा', 8]
  ];
  const KB_JP_MONTHS = [
    'जनवरी', 'फेब्रुवरी', 'मार्च', 'अप्रिल', 'मे', 'जुन',
    'जुलाई', 'अगस्ट', 'सेप्टेम्बर', 'अक्टुबर', 'नोभेम्बर', 'डिसेम्बर'
  ];
  const KB_JP_HOUSE = {
    1: [250, 90], 2: [130, 50], 3: [50, 130], 4: [90, 250],
    5: [50, 370], 6: [130, 450], 7: [250, 410], 8: [370, 450],
    9: [450, 370], 10: [410, 250], 11: [450, 130], 12: [370, 50]
  };
  const KB_JP_SPECIAL = { Mars: '#ff5555', Jupiter: '#ffcc44', Saturn: '#88aaff' };
  const KB_JP_PCOLOR = {
    Sun: '#f97316', Moon: '#94a3b8', Mars: '#ef4444', Mercury: '#22c55e',
    Jupiter: '#eab308', Venus: '#ec4899', Saturn: '#6366f1',
    Rahu: '#78716c', Ketu: '#a78bfa'
  };

  let kbJpCanvas = null;
  const kbJpWidthCache = new Map();
  function kbJpMeasure(text, size, weight) {
    const s = String(text == null ? '' : text);
    const w = weight || 600;
    const key = size + '|' + w + '|' + s;
    const hit = kbJpWidthCache.get(key);
    if (hit != null) return hit;
    if (!kbJpCanvas) kbJpCanvas = document.createElement('canvas');
    const ctx = kbJpCanvas.getContext('2d');
    ctx.font = w + ' ' + size + 'px ' + KB_JP_FONT;
    const v = ctx.measureText(s).width;
    kbJpWidthCache.set(key, v);
    return v;
  }
  function kbJpNe(v) {
    if (v == null) return KB_JP_UNAVAILABLE;
    return String(v).replace(/[0-9]/g, d => KB_NUM[+d]);
  }
  function kbJpFirst() {
    for (let i = 0; i < arguments.length; i++) {
      const v = arguments[i];
      if (v == null) continue;
      const t = String(v).trim();
      if (t && t !== '—' && t !== '?' && t !== KB_JP_UNAVAILABLE) return t;
    }
    return KB_JP_UNAVAILABLE;
  }
  function kbJpNested(v) {
    if (v && typeof v === 'object') return kbJpFirst(v.nepali, v.name, v.time);
    return kbJpFirst(v);
  }
  function kbJpPlace(v) {
    const text = kbJpFirst(v);
    if (text === KB_JP_UNAVAILABLE) return text;
    if (text.indexOf('(') >= 0 && text.indexOf(')') > 0) {
      const inside = text.slice(text.lastIndexOf('(') + 1, text.indexOf(')', text.lastIndexOf('('))).trim();
      if (/[\u0900-\u097F]/.test(inside)) return inside;
    }
    let city = text.split(',')[0].trim();
    city = city.split(' - P')[0].trim();
    return city || KB_JP_UNAVAILABLE;
  }
  function kbJpCoord(value, positive, negative) {
    const n = parseFloat(value);
    if (!isFinite(n)) return KB_JP_UNAVAILABLE;
    const deg = Math.floor(Math.abs(n));
    const mf = (Math.abs(n) - deg) * 60;
    const min = Math.floor(mf);
    const sec = Math.round((mf - min) * 60);
    return kbJpNe(deg + '°' + String(min).padStart(2, '0') + '\'' + String(sec).padStart(2, '0') + '"' + (n < 0 ? negative : positive));
  }
  function kbJpTimezone(md) {
    const off = parseFloat(md && md.timezone);
    if (!isFinite(off)) return kbJpFirst(md && md.timezone_id);
    const sign = off >= 0 ? '+' : '−';
    const abs = Math.abs(off);
    const h = Math.floor(abs);
    const m = Math.round((abs - h) * 60);
    return kbJpNe(sign + String(h).padStart(2, '0') + ':' + String(m).padStart(2, '0'));
  }
  function kbJpDegree(value) {
    const n = parseFloat(value);
    if (!isFinite(n)) return KB_JP_UNAVAILABLE;
    const deg = Math.floor(Math.abs(n));
    const mf = (Math.abs(n) - deg) * 60;
    const min = Math.floor(mf);
    const sec = Math.round((mf - min) * 60);
    return kbJpNe(deg + '°' + String(min).padStart(2, '0') + '′' + String(sec).padStart(2, '0') + '″');
  }
  function kbJpTimeSeconds(value) {
    const parts = String(value == null ? '' : value).trim().split(':').map(x => parseInt(x, 10));
    if (parts.length < 2 || parts.some(x => !isFinite(x))) return null;
    return parts[0] * 3600 + parts[1] * 60 + (parts.length > 2 ? parts[2] : 0);
  }
  function kbJpGhati(start, end) {
    const a = kbJpTimeSeconds(start), b = kbJpTimeSeconds(end);
    if (a == null || b == null) return KB_JP_UNAVAILABLE;
    let elapsed = b - a;
    if (elapsed < 0) elapsed += 24 * 3600;
    const total = Math.round(elapsed / 0.4);
    const ghati = Math.floor(total / 3600);
    const rem = total % 3600;
    const pala = Math.floor(rem / 60);
    const vipala = rem % 60;
    return String(ghati).padStart(2, '0') + ':' + String(pala).padStart(2, '0') + ':' + String(vipala).padStart(2, '0');
  }
  function kbJpElapsed(start, end) {
    const a = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(start || ''));
    const b = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(end || ''));
    if (!a || !b) return ['—'];
    let months = (+b[1] - +a[1]) * 12 + (+b[2] - +a[2]);
    if (+b[3] < +a[3]) months -= 1;
    months = Math.max(0, months);
    const years = Math.floor(months / 12), rem = months % 12;
    const out = [kbJpNe(years) + ' वर्ष'];
    if (rem) out.push(kbJpNe(rem) + ' महिना');
    return out;
  }
  function kbJpText(x, y, text, size, color, weight, anchor, font) {
    return '<text x="' + x + '" y="' + y + '" font-family="' + (font || KB_JP_FONT) + '" font-size="' + size +
      '" font-weight="' + (weight || 600) + '" fill="' + color + '" text-anchor="' + (anchor || 'start') + '">' +
      kbEsc(text) + '</text>';
  }
  function kbJpFitSize(text, size, maxW, weight) {
    let s = size;
    while (s > 6 && kbJpMeasure(text, s, weight) > maxW) s -= 0.5;
    return s;
  }
  function kbJpSwastika(x, y, s, color) {
    const h = s / 2, q = s * 0.42;
    return '<path d="M ' + (x - h) + ' ' + y + ' H ' + (x + h) +
      ' M ' + x + ' ' + (y - h) + ' V ' + (y + h) +
      ' M ' + x + ' ' + (y - h) + ' H ' + (x + q) + ' V ' + (y - h + q) +
      ' M ' + (x + h) + ' ' + y + ' V ' + (y + q) + ' H ' + (x + h - q) +
      ' M ' + x + ' ' + (y + h) + ' H ' + (x - q) + ' V ' + (y + h - q) +
      ' M ' + (x - h) + ' ' + y + ' V ' + (y - q) + ' H ' + (x - h + q) +
      '" fill="none" stroke="' + color + '" stroke-width="' + (s * 0.14) + '" stroke-linecap="square"/>';
  }

  function kbJpModel(data, meta) {
    const md = Object.assign({}, meta || {}, data.metadata || {});
    const panchang = data.panchang || {};
    const daily = ((data.panchang_requested_day || {}).panchang) || {};
    const lagna = data.lagna || {};
    const planets = data.planets || [];
    const moon = planets.find(p => p.name === 'Moon') || {};
    const sun = planets.find(p => p.name === 'Sun') || {};
    const navamsha = ((data.vargas || {}).D9) || {};
    const av = data.avakahada_chakra || {};
    const tithi = panchang.tithi || {};
    const nakshatra = panchang.nakshatra || {};
    const yoga = panchang.yoga || {};
    const karana = panchang.karana || {};
    const dailyTithi = daily.tithi || {};
    const dailyNakshatra = daily.nakshatra || {};
    const dailyYoga = daily.yoga || {};
    const dailyKarana = daily.karana || {};

    let calendar = {
      ad: KB_JP_UNAVAILABLE, year: KB_JP_UNAVAILABLE, month: KB_JP_UNAVAILABLE,
      day: KB_JP_UNAVAILABLE, shaka: KB_JP_UNAVAILABLE, bs: KB_JP_UNAVAILABLE
    };
    try {
      const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(md.birth_date || ''));
      if (m) {
        const bs = adToBs(new Date(Date.UTC(+m[1], +m[2] - 1, +m[3])));
        calendar = {
          ad: kbJpNe(String(md.birth_date).slice(0, 10)),
          year: kbJpNe(m[1]),
          month: KB_JP_MONTHS[+m[2] - 1],
          day: kbJpNe(m[3]),
          shaka: kbJpNe(+m[1] - 78),
          bs: kbJpNe(bs ? bs.y : KB_JP_UNAVAILABLE)
        };
      }
    } catch (e) { }

    const sunrise = kbJpFirst(kbJpNested(daily.sunrise), kbJpNested(panchang.sunrise));
    const sunset = kbJpFirst(kbJpNested(daily.sunset), kbJpNested(panchang.sunset));
    const localTime = kbJpFirst(md.local_birth_time, md.birth_time);
    const sunSign = parseInt(sun.sign_number, 10) || 0;
    const seasons = ['वसन्त', 'वसन्त', 'ग्रीष्म', 'ग्रीष्म', 'वर्षा', 'वर्षा', 'शरद', 'शरद', 'हेमन्त', 'हेमन्त', 'शिशिर', 'शिशिर'];
    const ayana = (sunSign >= 10 || (sunSign >= 1 && sunSign <= 3)) ? 'उत्तरायण' : (sunSign ? 'दक्षिणायन' : KB_JP_UNAVAILABLE);
    const season = (sunSign >= 1 && sunSign <= 12) ? seasons[sunSign - 1] : kbJpNested(panchang.ritu);
    let paksha = kbJpFirst(tithi.paksha_nepali, tithi.paksha);
    if (paksha !== KB_JP_UNAVAILABLE) paksha = paksha.replace(/पक्ष$/, '').trim();
    let nakElapsed = KB_JP_UNAVAILABLE;
    if (typeof moon.sidereal_longitude === 'number' && isFinite(moon.sidereal_longitude)) {
      const span = 360 / 27;
      const progress = (moon.sidereal_longitude % span) / span;
      const total = Math.round(progress * 60 * 3600);
      const ghati = Math.floor(total / 3600), rem = total % 3600;
      const pala = Math.floor(rem / 60), vipala = rem % 60;
      nakElapsed = String(ghati).padStart(2, '0') + ':' + String(pala).padStart(2, '0') + ':' + String(vipala).padStart(2, '0');
    }
    let gender = parseInt(md.gender, 10);
    if (!isFinite(gender)) gender = 0;

    return {
      metadata: md, calendar: calendar,
      full_name: String(md.full_name || md.name || '').trim(),
      father: kbJpFirst(md.father_name), mother: kbJpFirst(md.mother_name),
      gotra: kbJpFirst(md.gotra), spouse: kbJpFirst(md.spouse_name),
      family: kbJpFirst(md.family_details), country: kbJpFirst(md.country),
      place: kbJpPlace(kbJpFirst(md.birth_place, md.city)),
      gender_label: gender === 1 ? 'पुत्री' : 'पुत्र',
      name_akshara: kbJpFirst(av.name_akshara, av.namaakshar),
      nakshatra_pada: kbJpFirst(av.pada, av.charan),
      gana: kbJpFirst(av.gana), yoni: kbJpFirst(av.yoni),
      viryoni: kbJpFirst(av.viryoni), nadi: kbJpFirst(av.nadi),
      varna: kbJpFirst(av.varna), vashya: kbJpFirst(av.vashya),
      asana: kbJpFirst(av.asana), varga: kbJpFirst(av.varga),
      shatru_varga: kbJpFirst(av.shatru_varga),
      samvatsara: kbJpNested(panchang.samvatsara), ayana: ayana, season: season,
      masa: kbJpFirst(kbJpNested(panchang.lunar_month), kbJpNested(daily.lunar_month), kbJpNested(panchang.masa), calendar.month),
      paksha: paksha,
      vara: kbJpFirst(kbJpNested(panchang.vara), kbJpNested(panchang.day)),
      sunrise_tithi: kbJpNested(dailyTithi),
      birth_tithi: kbJpFirst(tithi.birth_nepali, tithi.birth_name, tithi.nepali, tithi.name),
      sunrise_nakshatra: kbJpNested(dailyNakshatra),
      birth_nakshatra: kbJpNested(nakshatra),
      sunrise_yoga: kbJpNested(dailyYoga),
      birth_yoga: kbJpFirst(yoga.birth_nepali, yoga.birth_name, yoga.nepali, yoga.name),
      sunrise_karana: kbJpNested(dailyKarana),
      birth_karana: kbJpFirst(karana.birth_nepali, karana.birth_name, karana.nepali, karana.name),
      tithi_end: kbJpGhati(sunrise, dailyTithi.end_time),
      nakshatra_end: kbJpGhati(sunrise, dailyNakshatra.end_time),
      yoga_end: kbJpGhati(sunrise, dailyYoga.end_time),
      karana_end: kbJpGhati(sunrise, dailyKarana.end_time),
      nakshatra_elapsed: kbJpFirst(nakshatra.elapsed, nakshatra.bhukta_ghati, nakElapsed),
      nakshatra_total: kbJpFirst(nakshatra.bhabhoga, nakshatra.bhoga_ghati, nakElapsed !== KB_JP_UNAVAILABLE ? '60:00:00' : null),
      sunrise: sunrise, sunset: sunset, local_time: localTime,
      ishta_kala: kbJpGhati(sunrise, localTime),
      lagna_sign: KB_JP_SIGNS[parseInt(lagna.sign_number, 10) || 0] || KB_JP_UNAVAILABLE,
      lagna_degree: kbJpDegree(kbJpFirst(lagna.longitude_in_sign, lagna.degree_in_sign)),
      moon_sign: KB_JP_SIGNS[parseInt(moon.sign_number, 10) || 0] || KB_JP_UNAVAILABLE,
      navamsha_sign: KB_JP_SIGNS[parseInt((navamsha.lagna || {}).sign_number, 10) || 0] || KB_JP_UNAVAILABLE,
      solar_month: KB_JP_SIGNS[sunSign] || KB_JP_UNAVAILABLE,
      solar_days: sun.longitude_in_sign != null ? kbJpNe(Math.floor(parseFloat(sun.longitude_in_sign)) + 1) : KB_JP_UNAVAILABLE,
      latitude: kbJpCoord(md.latitude, 'उ.', 'द.'),
      longitude: kbJpCoord(md.longitude, 'पू.', 'प.'),
      timezone: kbJpTimezone(md)
    };
  }

  function kbJpProse(model) {
    const V = key => ({ t: kbJpNe(model[key]), v: true });
    const C = key => ({ t: kbJpNe(model.calendar[key]), v: true });
    const rashi = model.full_name
      ? { t: model.full_name, v: true, p: 'name' }
      : { t: '.........', v: true, p: 'name' };
    const p1 = [
      { t: 'अस्य श्रीमन्नृपतिवीरविक्रमादित्यराज्यतः श्रीशालिवाहनीय शकः ' }, C('shaka'),
      { t: ' श्रीवीरविक्रमादित्य संवत् ' }, C('bs'),
      { t: ' ईसवीय सन् ' }, C('ad'),
      { t: ' अत्रास्मिन् वर्षे ' }, V('samvatsara'),
      { t: ' नाम संवत्सरे श्रीसूर्य ' }, V('ayana'), { t: ' ' }, V('season'),
      { t: ' ऋतौ अथ चान्द्रमानेन ' }, V('masa'),
      { t: ' मासे ' }, V('paksha'),
      { t: ' पक्षे ' }, V('vara'),
      { t: ' वासरे सूर्योदयकालीन ' }, V('sunrise_tithi'),
      { t: ' तिथौ घट्यादिः ' }, V('tithi_end'),
      { t: ' जन्म तिथौ ' }, V('birth_tithi'),
      { t: ' तिथिः। सूर्योदयकालीन ' }, V('sunrise_nakshatra'),
      { t: ' नक्षत्रस्य समाप्तिघट्यादिः ' }, V('nakshatra_end'),
      { t: ' जन्मनक्षत्रं ' }, V('birth_nakshatra'),
      { t: ' तस्य जन्मसमये भुक्तघट्यादिः ' }, V('nakshatra_elapsed'),
      { t: ' भभोगघट्यादिः ' }, V('nakshatra_total'),
      { t: ' सूर्योदयकालीन ' }, V('sunrise_yoga'),
      { t: ' योगस्य समाप्तिघट्यादिः ' }, V('yoga_end'),
      { t: ' जन्मयोगः ' }, V('birth_yoga'),
      { t: ' सूर्योदयकालीन ' }, V('sunrise_karana'),
      { t: ' करणस्य समाप्तिघट्यादिः ' }, V('karana_end'),
      { t: ' जन्मकरणं ' }, V('birth_karana'),
      { t: ' इति पञ्चाङ्गम् ॥' }
    ];
    const p2 = [
      { t: 'अथ सौरमानेन ' }, V('solar_month'),
      { t: ' मासे सूर्यसंक्रमाद् गतदिनानि ' }, V('solar_days'),
      { t: ' तदनुसारम् ईसवीयमासः ' }, C('month'),
      { t: ' तारिका ' }, C('day'),
      { t: ' अत्र ' }, V('vara'),
      { t: ' वासरे स्थानीय जन्मसमयः ' }, V('local_time'),
      { t: ' श्रीसूर्योदयादिष्टकालघट्यादिः ' }, V('ishta_kala'),
      { t: ' तदा जन्मसमये ' }, V('lagna_sign'),
      { t: ' राशौ लग्नोदयः ' }, V('lagna_degree'),
      { t: ' अंशात्मकः ' }, V('navamsha_sign'),
      { t: ' नवमांशके ' }, V('moon_sign'),
      { t: ' राशिगते चन्द्रमसि एवंविधे पञ्चाङ्गशुद्धे देशे ' }, V('country'),
      { t: ' प्रान्तान्तर्गत ' }, V('place'),
      { t: ' मण्डले तदन्तर्गत जन्मस्थाने ' }, V('place'),
      { t: ' यत्र अक्षांशः ' }, V('latitude'),
      { t: ' देशान्तरः ' }, V('longitude'),
      { t: ' मानकसमय ' }, V('timezone'),
      { t: ' स्थानीय जन्मसमयः ' }, V('local_time'),
      { t: ' निवसतः ' }, V('gotra'),
      { t: ' गोत्रोत्पन्न श्रीमतः ' }, V('father'),
      { t: ' तस्य कुलोचितविवाहितायां भार्यायां श्रीमती ' }, V('mother'),
      { t: ' नाम्नी देव्यां गर्भस्थ ' }, V('gender_label'),
      { t: ' रत्नमजीजनत्। नामाक्षरः ' }, V('name_akshara'),
      { t: ' चरणः ' }, V('nakshatra_pada'),
      { t: ' इष्टकालः ' }, V('ishta_kala'),
      { t: ' सूर्योदयः ' }, V('sunrise'),
      { t: ' सूर्यास्तः ' }, V('sunset'),
      { t: ' योनिः ' }, V('yoni'),
      { t: ' विर्योनिः ' }, V('viryoni'),
      { t: ' नाडी ' }, V('nadi'),
      { t: ' गणः ' }, V('gana'),
      { t: ' वश्यः ' }, V('vashya'),
      { t: ' आसनम् ' }, V('asana'),
      { t: ' वर्णः ' }, V('varna'),
      { t: ' वर्गः ' }, V('varga'),
      { t: ' शत्रुवर्गः ' }, V('shatru_varga'),
      { t: '। शुभनाम श्री ' }, rashi,
      { t: ' इति प्रतिष्ठितम्।' }
    ];
    return [p1, p2];
  }

  function kbJpLayoutLines(segs, maxW, size, weight) {
    const words = [];
    (segs || []).forEach(seg => {
      String(seg.t == null ? '' : seg.t).split(/\s+/).filter(Boolean).forEach(t => {
        words.push({ t: t, v: !!seg.v, pg: seg.p || '', w: kbJpMeasure(t, size, weight) });
      });
    });
    const spaceW = kbJpMeasure(' ', size, weight);
    const lines = [];
    let cur = [], curW = 0;
    words.forEach(word => {
      const add = cur.length ? spaceW + word.w : word.w;
      if (cur.length && curW + add > maxW) { lines.push(cur); cur = [word]; curW = word.w; }
      else { cur.push(word); curW += add; }
    });
    if (cur.length) lines.push(cur);
    return { lines: lines, spaceW: spaceW };
  }
  function kbJpPara(segs, x, top, maxW, size, lineH, opts) {
    opts = opts || {};
    const weight = opts.weight || 600;
    const color = opts.color || KB_JP.black;
    const laid = kbJpLayoutLines(segs, maxW, size, weight);
    const capture = opts.capture || null;
    let out = '';
    laid.lines.forEach((line, li) => {
      const gaps = line.length - 1;
      const natural = line.reduce((a, w) => a + w.w, 0) + gaps * laid.spaceW;
      const extra = (opts.justify !== false && li < laid.lines.length - 1 && gaps > 0)
        ? Math.max(0, (maxW - natural) / gaps) : 0;
      let cx = x;
      let open = null;
      const baseline = top + size + li * lineH;
      line.forEach((word, wi) => {
        if (wi) cx += laid.spaceW + extra;
        out += kbJpText(cx, baseline, word.t, size, color, weight);
        if (word.v) {
          out += '<line x1="' + cx.toFixed(1) + '" y1="' + (baseline + 3).toFixed(1) +
            '" x2="' + (cx + word.w).toFixed(1) + '" y2="' + (baseline + 3).toFixed(1) +
            '" stroke="' + KB_JP.gray + '" stroke-width="1" stroke-dasharray="1.5 2"/>';
        }
        if (capture && word.pg) {
          const arr = capture[word.pg] || (capture[word.pg] = []);
          if (!open || open.pg !== word.pg || open.line !== li) {
            open = { pg: word.pg, line: li, r: { x: cx, y: top + li * lineH + size * .02, w: word.w, h: size * 1.45 } };
            arr.push(open.r);
          } else {
            open.r.w = cx + word.w - open.r.x;
          }
        } else {
          open = null;
        }
        cx += word.w;
      });
    });
    return { svg: out, height: laid.lines.length * lineH };
  }
  function kbJpCenterSegs(segs, cx, top, maxW, size, capture) {
    let total = 0;
    segs.forEach(s => { total += kbJpMeasure(s.t, s.b ? 700 : 600, size); });
    if (total > maxW) {
      const p = kbJpPara(segs, cx - maxW / 2, top, maxW, size, size * 1.45, { justify: false, capture: capture });
      return { svg: p.svg, height: p.height };
    }
    let x = cx - total / 2;
    let out = '';
    const baseline = top + size;
    segs.forEach(s => {
      const sw = kbJpMeasure(s.t, s.b ? 700 : 600, size);
      if (capture && s.p) (capture[s.p] || (capture[s.p] = [])).push({ x: x, y: top + size * .02, w: sw, h: size * 1.45 });
      out += kbJpText(x, baseline, s.t, size, KB_JP.black, s.b ? 700 : 600);
      x += sw;
    });
    return { svg: out, height: size * 1.45 };
  }

  function kbJpChart(data, varga, x, y, size) {
    const k = size / 500;
    let planets, lagnaSign;
    if (varga === 'Moon') {
      const moon = (data.planets || []).find(p => p.name === 'Moon') || {};
      lagnaSign = parseInt(moon.sign_number, 10) || 1;
      planets = (data.planets || []).map(p => Object.assign({}, p, {
        house: ((parseInt(p.sign_number, 10) || 1) - lagnaSign + 12) % 12 + 1
      }));
    } else {
      const d1 = ((data.vargas || {}).D1 && (data.vargas || {}).D1.planets) ? data.vargas.D1 : data;
      lagnaSign = parseInt(((d1.lagna || data.lagna || {}).sign_number), 10) || 1;
      planets = d1.planets || data.planets || [];
    }
    let s = '<g transform="translate(' + x + ',' + y + ') scale(' + k + ')">';
    s += '<rect x="0" y="0" width="500" height="500" fill="#dce8ff"/>';
    s += '<circle cx="250" cy="250" r="135" fill="#f59e0b" opacity=".055"/>';
    s += '<rect x="10" y="10" width="480" height="480" fill="none" stroke="#002288" stroke-width="2.2"/>';
    s += '<line x1="10" y1="10" x2="490" y2="490" stroke="#002288" stroke-width="2"/>';
    s += '<line x1="10" y1="490" x2="490" y2="10" stroke="#002288" stroke-width="2"/>';
    s += '<polygon points="250,10 490,250 250,490 10,250" fill="none" stroke="#002288" stroke-width="2"/>';
    for (let h = 1; h <= 12; h++) {
      const pos = KB_JP_HOUSE[h];
      const lx = pos[0], ly = pos[1];
      const sign = ((lagnaSign - 1 + h - 1) % 12) + 1;
      s += kbJpText(lx, ly - 24, kbJpNe(sign), 18, '#cc0000', 700, 'middle');
      if (h === 1) s += kbJpText(lx, ly - 52, '▲ ल', 14, '#0000cc', 700, 'middle');
      const occupants = planets.filter(p => (parseInt(p.house, 10) || 0) === h);
      if (!occupants.length) continue;
      const fs = Math.max(11, 20 - Math.floor((occupants.length - 1) * 1.1));
      const lh = fs + 7;
      const startY = ly + 28 - ((occupants.length - 1) * lh) / 2;
      occupants.forEach((p, i) => {
        const name = p.name || '';
        const ab = KUN_AB[name] || name.slice(0, 2);
        let suffix = '';
        if (p.is_retrograde && p.is_combust) suffix = '(ब,अ)';
        else if (p.is_retrograde) suffix = '(ब)';
        else if (p.is_combust) suffix = '(अ)';
        const color = KB_JP_SPECIAL[name] || KB_JP_PCOLOR[name] || '#0f172a';
        s += kbJpText(lx, startY + i * lh + fs * 0.35, ab + suffix, fs, color, 700, 'middle');
      });
    }
    return s + '</g>';
  }
  function kbJpChartFrame(data, varga, title, x, y, w, size) {
    const h = size + 44;
    let s = '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" fill="' + KB_JP.paper + '" stroke="#8db1e5" stroke-width="1.2"/>';
    s += kbJpText(x + w / 2, y + 20, title, 16, KB_JP.red, 800, 'middle');
    s += kbJpChart(data, varga, x + (w - size) / 2, y + 32, size);
    return { svg: s, height: h };
  }
  function kbJpPlanetTable(data, x, y, w) {
    const lagna = data.lagna || {};
    const planets = data.planets || [];
    const rows = [{ name: 'लग्न', item: lagna }];
    ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'].forEach(name => {
      rows.push({ name: KB_JP_PLANETS[name], item: planets.find(p => p.name === name) || {} });
    });
    const headH = 30, rowH = 30, H = headH + rows.length * rowH;
    const cw = [w * 0.18, w * 0.20, w * 0.38, w * 0.24];
    const xs = [x, x + cw[0], x + cw[0] + cw[1], x + cw[0] + cw[1] + cw[2]];
    let s = '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + H + '" fill="none" stroke="' + KB_JP.gray + '" stroke-width="1"/>';
    s += '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + headH + '" fill="' + KB_JP.deep + '"/>';
    const heads = ['ग्रह', 'राशि', 'स्पष्ट', 'स्थिति'];
    heads.forEach((t, i) => {
      s += kbJpText(xs[i] + cw[i] / 2, y + headH / 2 + 5, t, 14, KB_JP.red, 800, 'middle');
    });
    rows.forEach((row, ri) => {
      const item = row.item || {};
      const cy = y + headH + ri * rowH + rowH / 2;
      const status = [];
      if (item.is_retrograde) status.push('वक्री');
      if (item.is_combust) status.push('अस्त');
      if (item.exaltation_state === 'exalted') status.push('उच्च');
      else if (item.exaltation_state === 'debilitated') status.push('नीच');
      const sign = KB_JP_SIGNS[parseInt(item.sign_number, 10) || 0] || KB_JP_UNAVAILABLE;
      const degree = kbJpDegree(kbJpFirst(item.longitude_in_sign, item.degree_in_sign));
      const cells = [
        { t: row.name, w: 700, fs: 15 },
        { t: sign, w: 600, fs: 14 },
        { t: degree, w: 600, fs: 14 },
        { t: status.join(', ') || '—', w: 600, fs: 13 }
      ];
      cells.forEach((cell, ci) => {
        const fs = kbJpFitSize(cell.t, cell.fs, cw[ci] - 8, cell.w);
        s += kbJpText(xs[ci] + cw[ci] / 2, cy + fs * 0.36, cell.t, fs, KB_JP.black, cell.w, 'middle');
      });
    });
    for (let r = 1; r < rows.length; r++) {
      const yy = y + headH + r * rowH;
      s += '<line x1="' + x + '" y1="' + yy + '" x2="' + (x + w) + '" y2="' + yy + '" stroke="' + KB_JP.gray + '" stroke-width="0.9"/>';
    }
    for (let c = 1; c < 4; c++) {
      s += '<line x1="' + xs[c] + '" y1="' + y + '" x2="' + xs[c] + '" y2="' + (y + H) + '" stroke="' + KB_JP.gray + '" stroke-width="0.9"/>';
    }
    s += '<line x1="' + x + '" y1="' + (y + headH) + '" x2="' + (x + w) + '" y2="' + (y + headH) + '" stroke="' + KB_JP.gray + '" stroke-width="0.9"/>';
    return { svg: s, height: H };
  }
  function kbJpDashaSpec(periods) {
    const first = periods[0] || {};
    const isYogini = !!(first.name || first.nepali) && !first.lord_nepali;
    return isYogini ? { spec: KB_JP_YOGINI, heading: 'योगिनी' } : { spec: KB_JP_VIM, heading: 'ग्रह' };
  }
  function kbJpOrdered(periods, spec) {
    if (!periods || !periods.length) return [];
    const first = kbJpFirst(periods[0].lord, periods[0].name);
    const names = spec.map(x => x[0]);
    let start = names.indexOf(first);
    if (start < 0) start = 0;
    const expected = names.slice(start).concat(names.slice(0, start));
    const remaining = periods.slice();
    const out = [];
    expected.forEach(name => {
      const i = remaining.findIndex(n => kbJpFirst(n.lord, n.name) === name);
      if (i >= 0) { out.push(remaining[i]); remaining.splice(i, 1); }
    });
    return out.length ? out : periods.slice(0, spec.length);
  }
  function kbJpDashaTable(periods, childrenKey, x, y, w) {
    if (!periods || !periods.length) return null;
    const meta = kbJpDashaSpec(periods);
    const cycle = kbJpOrdered(periods, meta.spec);
    const durationByName = {};
    meta.spec.forEach(s => { durationByName[s[0]] = s[2]; });
    let s = '', H = 0;
    if (childrenKey) {
      const rows = cycle.map(p => ({ p: p, nodes: p[childrenKey] || [] })).filter(r => r.nodes.length);
      if (!rows.length) return null;
      const shown = rows.slice(0, 3);
      const maxRow = rows.reduce((a, b) => b.nodes.length > a.nodes.length ? b : a, rows[0]);
      const headerNodes = kbJpOrdered(maxRow.nodes, meta.spec).slice(0, meta.spec.length);
      const n = headerNodes.length + 1, cw = w / n;
      const headH = 26, rowH = 54;
      H = headH + shown.length * rowH;
      s += '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + H + '" fill="none" stroke="' + KB_JP.gray + '" stroke-width="1"/>';
      s += kbJpText(x + cw / 2, y + headH / 2 + 4, 'दशा', 12, KB_JP.red, 800, 'middle');
      headerNodes.forEach((node, i) => {
        const name = kbJpFirst(node.lord_nepali, node.nepali, node.lord, node.name);
        const fs = kbJpFitSize(name, 12, cw - 4, 700);
        s += kbJpText(x + cw * (i + 1.5), y + headH / 2 + 4, name, fs, KB_JP.red, 700, 'middle');
      });
      shown.forEach((row, ri) => {
        const cy = y + headH + ri * rowH + rowH / 2;
        s += kbJpText(x + cw / 2, cy - 8, 'बाँकी उमेर', 9.5, KB_JP.red, 600, 'middle');
        const parent = kbJpFirst(row.p.lord_nepali, row.p.nepali, row.p.lord, row.p.name);
        const pfs = kbJpFitSize(parent, 11, cw - 4, 700);
        s += kbJpText(x + cw / 2, cy + 7, parent, pfs, KB_JP.red, 700, 'middle');
        const nodes = kbJpOrdered(row.nodes, meta.spec).slice(0, meta.spec.length);
        for (let i = 0; i < headerNodes.length; i++) {
          const node = nodes[i];
          const cx = x + cw * (i + 1.5);
          if (!node) { s += kbJpText(cx, cy + 4, '—', 12, KB_JP.red, 600, 'middle'); continue; }
          const lines = kbJpElapsed(row.p.start, node.end);
          if (lines.length > 1) {
            s += kbJpText(cx, cy - 3, lines[0], 11, KB_JP.red, 600, 'middle');
            s += kbJpText(cx, cy + 10, lines[1], 11, KB_JP.red, 600, 'middle');
          } else {
            s += kbJpText(cx, cy + 4, lines[0], 11, KB_JP.red, 600, 'middle');
          }
        }
      });
      for (let r = 1; r <= shown.length; r++) {
        const yy = y + headH + (r - 1) * rowH;
        s += '<line x1="' + x + '" y1="' + yy + '" x2="' + (x + w) + '" y2="' + yy + '" stroke="' + KB_JP.gray + '" stroke-width="0.9"/>';
      }
      s += '<line x1="' + x + '" y1="' + (y + H) + '" x2="' + (x + w) + '" y2="' + (y + H) + '" stroke="' + KB_JP.gray + '" stroke-width="0.9"/>';
      for (let c = 1; c < n; c++) {
        s += '<line x1="' + (x + c * cw) + '" y1="' + y + '" x2="' + (x + c * cw) + '" y2="' + (y + H) + '" stroke="' + KB_JP.gray + '" stroke-width="0.9"/>';
      }
      return { svg: s, height: H };
    }
    const columns = cycle.slice(0, meta.spec.length);
    const n = columns.length + 1, cw = w / n;
    const headH = 26, yearH = 30, remH = 44;
    H = headH + yearH + remH;
    s += '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + H + '" fill="none" stroke="' + KB_JP.gray + '" stroke-width="1"/>';
    s += kbJpText(x + cw / 2, y + headH / 2 + 4, meta.heading, 12, KB_JP.red, 800, 'middle');
    columns.forEach((node, i) => {
      const name = kbJpFirst(node.lord_nepali, node.nepali, node.lord, node.name);
      const fs = kbJpFitSize(name, 12, cw - 4, 700);
      s += kbJpText(x + cw * (i + 1.5), y + headH / 2 + 4, name, fs, KB_JP.red, 700, 'middle');
    });
    s += kbJpText(x + cw / 2, y + headH + yearH / 2 + 4, 'वर्ष', 11, KB_JP.red, 700, 'middle');
    columns.forEach((node, i) => {
      const years = kbJpFirst(node.total_years, durationByName[kbJpFirst(node.lord, node.name)]);
      const text = kbJpNe(years) + ' वर्ष';
      const fs = kbJpFitSize(text, 12, cw - 4, 600);
      s += kbJpText(x + cw * (i + 1.5), y + headH + yearH / 2 + 4, text, fs, KB_JP.red, 600, 'middle');
    });
    const birthStart = columns[0] ? columns[0].start : null;
    s += kbJpText(x + cw / 2, y + headH + yearH + remH / 2 - 7, 'बाँकी', 9.5, KB_JP.red, 600, 'middle');
    s += kbJpText(x + cw / 2, y + headH + yearH + remH / 2 + 7, 'उमेर', 9.5, KB_JP.red, 600, 'middle');
    columns.forEach((node, i) => {
      const lines = kbJpElapsed(birthStart, node.end);
      const cx = x + cw * (i + 1.5);
      if (lines.length > 1) {
        s += kbJpText(cx, y + headH + yearH + remH / 2 - 3, lines[0], 11, KB_JP.red, 600, 'middle');
        s += kbJpText(cx, y + headH + yearH + remH / 2 + 10, lines[1], 11, KB_JP.red, 600, 'middle');
      } else {
        s += kbJpText(cx, y + headH + yearH + remH / 2 + 4, lines[0], 11, KB_JP.red, 600, 'middle');
      }
    });
    s += '<line x1="' + x + '" y1="' + (y + headH) + '" x2="' + (x + w) + '" y2="' + (y + headH) + '" stroke="' + KB_JP.gray + '" stroke-width="0.9"/>';
    s += '<line x1="' + x + '" y1="' + (y + headH + yearH) + '" x2="' + (x + w) + '" y2="' + (y + headH + yearH) + '" stroke="' + KB_JP.gray + '" stroke-width="0.9"/>';
    for (let c = 1; c < n; c++) {
      s += '<line x1="' + (x + c * cw) + '" y1="' + y + '" x2="' + (x + c * cw) + '" y2="' + (y + H) + '" stroke="' + KB_JP.gray + '" stroke-width="0.9"/>';
    }
    return { svg: s, height: H };
  }
  function kbJpDashaSection(title, periods, childrenKey, x, y, w) {
    const table = kbJpDashaTable(periods, childrenKey, x, y + 28, w);
    if (!table) return null;
    let s = kbJpText(x + w / 2, y + 18, title, 18, KB_JP.red, 800, 'middle');
    s += table.svg;
    return { svg: s, height: 28 + table.height };
  }

  function kbJanmapatrika(data, meta, opts) {
    opts = opts || {};
    const x0 = opts.x != null ? +opts.x : 58;
    const y0 = opts.y != null ? +opts.y : 170;
    const W = opts.w != null ? +opts.w : 604;
    const model = kbJpModel(data, meta);
    const parts = [];
    const cx = x0 + W / 2;
    const padX = Math.round(W * 0.111);
    const contentX = x0 + padX;
    const contentW = W - padX * 2;
    let y = y0 + 46;

    parts.push(kbJpText(cx, y + 28, 'ॐ', 34, KB_JP.red, 800, 'middle'));
    y += 36;
    parts.push(kbJpText(cx, y + 20, 'श्री गणेशाय नमः', 25, KB_JP.red, 800, 'middle'));
    y += 32;
    parts.push(kbJpText(cx, y + 16, 'श्रीमङ्गलमूर्तये नमः', 18, KB_JP.blue, 700, 'middle'));
    y += 26;
    parts.push(kbJpText(cx, y + 16, 'आदित्याद्या ग्रहासर्वे सनक्षत्राः सराशयः ॥', 17, KB_JP.gold, 700, 'middle'));
    y += 24;
    parts.push(kbJpText(cx, y + 16, 'कुर्वन्तुमङ्गल तस्य यस्यैषा जन्मपत्रिका॥', 17, KB_JP.gold, 700, 'middle'));
    y += 30;

    const prose = kbJpProse(model);
    const jpCapture = { name: [], family: [], spouse: [] };
    prose.forEach((segs, pi) => {
      const p = kbJpPara(segs, contentX, y, contentW, 18, 27, { justify: true, capture: jpCapture });
      parts.push(p.svg);
      y += p.height + (pi === 0 ? 14 : 0);
    });
    y += 8;

    parts.push(kbJpText(cx, y + 18, 'सदैव द्विजाशीर्वादैर्दीर्घमायुर्भूयात् ॥', 18, KB_JP.red, 800, 'middle'));
    y += 32;

    const chartSize = Math.min(210, Math.floor((contentW - 12) / 2) - 18);
    const frameW = (contentW - 12) / 2;
    const f1 = kbJpChartFrame(data, 'D1', 'जन्म कुण्डली (D1)', contentX, y, frameW, chartSize);
    const f2 = kbJpChartFrame(data, 'Moon', 'चन्द्र कुण्डली', contentX + frameW + 12, y, frameW, chartSize);
    parts.push(f1.svg, f2.svg);
    y += f1.height + 14;

    parts.push(kbJpText(cx, y + 18, 'ग्रह स्थिति तालिका', 18, KB_JP.red, 800, 'middle'));
    y += 28;
    const planetTable = kbJpPlanetTable(data, contentX, y, contentW);
    parts.push(planetTable.svg);
    y += planetTable.height + 14;

    const dashaSections = [
      ['विंशोत्तरी महादशा चक्रम्', data.dasha || [], null],
      ['विंशोत्तरी अन्तरदशा चक्रम्', data.dasha || [], 'children'],
      ['योगिनी महादशा चक्रम्', data.yogini_dasha || [], null],
      ['योगिनी अन्तरदशा चक्रम्', data.yogini_dasha || [], 'antardashas']
    ];
    dashaSections.forEach(d => {
      const sec = kbJpDashaSection(d[0], d[1], d[2], contentX, y, contentW);
      if (sec) { parts.push(sec.svg); y += sec.height + 10; }
    });

    if (model.family !== KB_JP_UNAVAILABLE || model.spouse !== KB_JP_UNAVAILABLE) {
      const segs = [
        { t: 'परिवारको विवरण: ', b: true },
        { t: model.family, p: model.family !== KB_JP_UNAVAILABLE ? 'family' : '' },
        { t: '   ' }, { t: 'पति वा पत्नी: ', b: true },
        { t: model.spouse, p: model.spouse !== KB_JP_UNAVAILABLE ? 'spouse' : '' }, { t: ' ॥' }
      ];
      const fam = kbJpCenterSegs(segs, cx, y, contentW, 16, jpCapture);
      parts.push(fam.svg);
      y += fam.height + 12;
    }

    y += 4;
    parts.push(kbJpText(cx, y + 18, '॥ इति जन्मपत्रिका ॥', 18, KB_JP.red, 800, 'middle'));
    y += 34;
    const H = Math.max(240, Math.round(y + 40 - y0));

    let bg = '<rect x="' + x0 + '" y="' + y0 + '" width="' + W + '" height="' + H + '" fill="' + KB_JP.paper + '" stroke="' + KB_JP.green + '" stroke-width="1.4"/>';
    bg += '<rect x="' + (x0 + 12) + '" y="' + (y0 + 12) + '" width="' + (W - 24) + '" height="' + (H - 24) + '" fill="none" stroke="' + KB_JP.green + '" stroke-width="2"/>';
    for (let sx = x0 + 30; sx <= x0 + W - 24; sx += 26) {
      bg += kbJpSwastika(sx, y0 + 22, 8, KB_JP.red);
      bg += kbJpSwastika(sx, y0 + H - 22, 8, KB_JP.red);
    }
    for (let sy = y0 + 50; sy <= y0 + H - 40; sy += 42) {
      bg += kbJpSwastika(x0 + 22, sy, 7, KB_JP.red);
      bg += kbJpSwastika(x0 + W - 22, sy, 7, KB_JP.red);
    }

    const privacy = [];
    const addCap = (id, label, arr) => {
      if (!arr || !arr.length) return;
      privacy.push({ id: id, label: label, rects: arr.map(r => ({ x: r.x - 3, y: r.y - 1, w: r.w + 6, h: r.h + 3 })) });
    };
    addCap('jp-name', 'जातकको नाम (जन्मपत्रिका)', jpCapture.name);
    addCap('jp-family', 'परिवारको विवरण (जन्मपत्रिका)', jpCapture.family);
    addCap('jp-spouse', 'पति वा पत्नी (जन्मपत्रिका)', jpCapture.spouse);

    return { inner: bg + parts.join(''), height: H, width: W, model: model, privacy: privacy };
  }

  window.KunJanmapatrika = { build: kbJanmapatrika, model: kbJpModel, prose: kbJpProse };

  function kbCatalog(data, meta) {
    kbSeq = 0;
    const pages = [];
    const lagna = data.lagna || {}, planets = data.planets || [];
    const lagnaSign = +lagna.sign_number || 1;
    const moon = planets.find(p => p.name === 'Moon') || {};
    const pc = data.panchang || {};
    const dateLabel = kunDateNe(meta.birth_date) + ' · ' + kunTime(meta.birth_time);
    const placeLabel = (meta.city || meta.birth_place || '—') + (meta.country ? ', ' + meta.country : '');

    /* 1 — cover */
    {
      const no = 1, title = 'जन्म कुण्डली';
      let art = '';
      const cx = 360, cy = 450, R = 180;
      art += '<circle cx="' + cx + '" cy="' + cy + '" r="' + R + '" fill="none" stroke="#e8b923" stroke-opacity=".25" stroke-width="2"/>';
      art += '<circle cx="' + cx + '" cy="' + cy + '" r="' + (R - 18) + '" fill="none" stroke="#e8b923" stroke-opacity=".12" stroke-width="1"/>';
      for (let i = 0; i < 12; i++) {
        const a = (i * 30 - 90) * Math.PI / 180;
        art += '<circle cx="' + (cx + (R - 9) * Math.cos(a)) + '" cy="' + (cy + (R - 9) * Math.sin(a)) + '" r="4" fill="#e8b923" opacity=".6"/>';
      }
      art += '<circle cx="' + cx + '" cy="' + cy + '" r="80" fill="#101a31" stroke="#e8b923" stroke-opacity=".35" stroke-width="2"/>';
      art += '<circle cx="' + (cx - 16) + '" cy="' + (cy - 7) + '" r="32" fill="#f6d365" opacity=".95"/>';
      art += '<path d="M ' + (cx + 2) + ' ' + (cy - 42) + ' a 42 42 0 1 0 0 84 a 33 33 0 1 1 0 -84" fill="#dfe8ff" opacity=".92"/>';
      art += kunT(cx, cy + 56, 'ॐ', 25, '#f6d365', 700, 'middle');
      let chips = '';
      const chipData = [
        ['लग्न', kunSignByNum(lagnaSign)],
        ['चन्द्र राशि', pc.chandra_rashi ? pc.chandra_rashi.nepali : kunSignNe(moon)],
        ['जन्म नक्षत्र', (moon.nakshatra_nepali || '—') + (moon.nakshatra_pada ? ' · पद ' + neNum(moon.nakshatra_pada) : '')]
      ];
      const cw = 196, gap = 16, x0 = 360 - (chipData.length * cw + (chipData.length - 1) * gap) / 2;
      chipData.forEach((c, i) => chips += kunCard(x0 + i * (cw + gap), 892, cw, 112, c[0], c[1], '#e8b923', { fs: 19, chars: 10, lh: 25 }));
      const coverNameEl = kbEl(no, title, 'heading', 'जातकको नाम', [46, 700, 628, 78], kunT(360, 750, meta.name || 'जातक', 44, '#f6d365', 700, 'middle'), 5.6);
      coverNameEl.privacy = [{ id: 'name', label: 'जातकको नाम (कभर)', rects: [{ x: 84, y: 704, w: 552, h: 64 }] }];
      pages.push(kbPage(no, title, 'वैदिक ज्योतिष प्रस्तुति', [
        kbHeader(no, title, 'वैदिक ज्योतिष प्रस्तुति'),
        kbEl(no, title, 'art', 'कवर मण्डल र चन्द्र कला', [140, 245, 440, 440], art, 7.2),
        coverNameEl,
        kbEl(no, title, 'note', 'जन्म मिति (BS) र समय', [46, 780, 628, 44], kunT(360, 800, dateLabel, 21, '#e9eefb', 600, 'middle'), 6.2),
        kbEl(no, title, 'note', 'जन्म स्थान', [46, 812, 628, 44], kunT(360, 838, placeLabel, 17, '#9fb0d0', 500, 'middle'), 6.2),
        kbEl(no, title, 'cards', 'लग्न · चन्द्र · नक्षत्र कार्ड', [46, 880, 628, 130], chips, 7.2),
        kbEl(no, title, 'note', 'अयनांश ब्याज', [46, 1040, 628, 56], kunT(360, 1070, 'Kundali-Desktop · ' + (meta.ayanamsha_type || 'LAHIRI') + ' अयनांश', 14, '#7183a8', 500, 'middle'), 5.6),
        kbFooter(no, title)
      ]));
    }

    /* 2 — birth details */
    {
      const no = 2, title = 'जन्म विवरण';
      const rows = [
        ['नाम', meta.name || '—'],
        ['लिङ्ग', meta.gender === 'female' ? 'महिला' : meta.gender === 'male' ? 'पुरुष' : '—'],
        ['जन्म मिति (AD)', neNum(meta.birth_date || '—')],
        ['जन्म मिति (BS)', kunDateNe(meta.birth_date)],
        ['जन्म समय', kunTime(meta.birth_time)],
        ['जन्म स्थान', placeLabel],
        ['अक्षांश', kunNum(meta.latitude, 4) + '°'],
        ['देशान्तर', kunNum(meta.longitude, 4) + '°'],
        ['समय क्षेत्र', 'UTC' + (+meta.timezone >= 0 ? '+' : '') + kunNum(meta.timezone, 2) + (meta.timezone_id ? ' · ' + meta.timezone_id : '')],
        ['अयनांश', (meta.ayanamsha_type || 'LAHIRI') + ' · ' + kunNum(meta.ayanamsha_value, 4) + '°'],
        ['भाव पद्धति', meta.house_system || 'WHOLE_SIGN'],
        ['राहु / केतु', meta.node_type === 'TRUE' ? 'True Node' : 'Mean Node'],
        ['गणना प्रणाली', (meta.ephemeris || 'SWISS') + ' · v' + (meta.calculation_version || '1.0.0')]
      ];
      const birthTable = kbTableEl(no, title, 'जन्म विवरण तालिका', 46, 184, 628, [{ t: 'विवरण', w: 210 }, { t: 'मान', w: 418 }], rows, { rowH: 60, headH: 50, fs: 17, hfs: 14, align: ['left', 'left'] }, 9);
      birthTable.privacy = [{ id: 'name', label: 'जातकको नाम (जन्म विवरण)', rects: [{ x: 250, y: 238, w: 416, h: 52 }] }];
      pages.push(kbPage(no, title, 'Birth Details', [
        kbHeader(no, title, 'Birth Details'),
        birthTable,
        kbEl(no, title, 'note', 'जन्म समय नोट', [46, 1040, 628, 44], kunT(46, 1060, 'जन्म समय स्थानीय समयमा हो। समय क्षेत्र DST सहित Kundali-Desktop ले मिलाएको छ।', 13, '#7183a8', 500), 6),
        kbFooter(no, title)
      ]));
    }

    /* 3 — D1 */
    {
      const no = 3, title = 'लग्न कुण्डली (D1)';
      const houses = kunHouses(planets, lagnaSign, 'd1');
      let chips = '';
      const chipData = [
        ['लग्न राशि', kunSignByNum(lagnaSign)],
        ['चन्द्र राशि', pc.chandra_rashi ? pc.chandra_rashi.nepali : kunSignNe(moon)],
        ['जन्म नक्षत्र', (moon.nakshatra_nepali || '—') + ' ' + neNum(moon.nakshatra_pada || '')]
      ];
      const cw = 196, gap = 16, x0 = 360 - (chipData.length * cw + (chipData.length - 1) * gap) / 2;
      chipData.forEach((c, i) => chips += kunCard(x0 + i * (cw + gap), 902, cw, 108, c[0], c[1], '#e8b923', { fs: 19, chars: 10, lh: 25 }));
      pages.push(kbPage(no, title, 'उत्तर भारतीय शैली', [
        kbHeader(no, title, 'उत्तर भारतीय शैली · Kundali-Desktop रेन्डरर'),
        kbChartEl(no, title, houses, lagnaSign, 'लग्न कुण्डली चार्ट', 60, 190, 600),
        kbEl(no, title, 'note', 'लग्न अंश', [46, 802, 628, 50], kunT(360, 822, 'लग्न: ' + kunSignByNum(lagnaSign) + ' · ' + kunDMS(lagna.longitude_in_sign || 0), 20, '#e9eefb', 700, 'middle'), 6.2),
        kbEl(no, title, 'note', 'ग्रह संकेत व्याख्या', [46, 842, 628, 40], kunT(360, 862, 'सू चं मं बु गु शु श रा के = ग्रह · (व) = वक्री', 13, '#9fb0d0', 500, 'middle'), 5.6),
        kbEl(no, title, 'cards', 'लग्न · चन्द्र · नक्षत्र कार्ड', [46, 890, 628, 120], chips, 7.2),
        kbFooter(no, title)
      ]));
    }

    /* 4 — planet table */
    {
      const no = 4, title = 'ग्रह स्थिति तालिका';
      const rows = KUN_ORDER.map(name => {
        const p = planets.find(x => x.name === name);
        if (!p) return null;
        return [KUN_NE[name], kunSignNe(p), kunDMS(p.longitude_in_sign), neNum(p.house), (p.nakshatra_nepali || '—') + ' ' + neNum(p.nakshatra_pada || ''), kunStateText(p) || '—'];
      }).filter(Boolean);
      pages.push(kbPage(no, title, 'नौ ग्रहको राशि, भाव र नक्षत्र', [
        kbHeader(no, title, 'सबै नौ ग्रहको राशि, भाव, नक्षत्र र अवस्था'),
        kbTableEl(no, title, 'ग्रह स्थिति तालिका', 46, 184, 628, [
          { t: 'ग्रह', w: 84 }, { t: 'राशि', w: 88 }, { t: 'अंश', w: 102 }, { t: 'भाव', w: 58 }, { t: 'नक्षत्र · पद', w: 140 }, { t: 'स्थिति', w: 188 }
        ], rows, { rowH: 64, headH: 52, fs: 15, hfs: 13 }, 9),
        kbEl(no, title, 'note', 'स्थिति व्याख्या', [46, 830, 628, 40], kunT(46, 850, 'स्थिति: वक्री = retrograde, अस्त = combust, वर्गोत्तम = vargottama, उच्च/नीच/स्वराशि = dignity', 12, '#7183a8', 500), 6),
        kbEl(no, title, 'note', 'भाव पद्धति नोट', [46, 862, 628, 40], kunT(46, 880, 'भाव: Whole Sign पद्धति अनुसार लग्नबाट गणना।', 12, '#7183a8', 500), 6),
        kbFooter(no, title)
      ]));
    }

    /* 5 — bhava table */
    {
      const no = 5, title = 'द्वादश भाव विवरण';
      const rows = [];
      for (let h = 1; h <= 12; h++) {
        const sign = ((lagnaSign - 1 + h - 1) % 12) + 1;
        const lord = KUN_SIGN_LORD[sign - 1];
        const inH = planets.filter(p => p.house === h).map(p => KUN_NE[p.name] || p.name).join(', ') || '—';
        rows.push([neNum(h), kunSignByNum(sign), KUN_NE[lord] || lord, inH, KUN_HOUSE_NE[h]]);
      }
      pages.push(kbPage(no, title, 'भाव, राशि, स्वामी र स्थित ग्रह', [
        kbHeader(no, title, 'भाव, राशि, स्वामी र स्थित ग्रह'),
        kbTableEl(no, title, 'द्वादश भाव तालिका', 46, 180, 628, [
          { t: 'भाव', w: 60 }, { t: 'राशि', w: 100 }, { t: 'स्वामी', w: 100 }, { t: 'स्थित ग्रह', w: 260 }, { t: 'भाव नाम', w: 120 }
        ], rows, { rowH: 55, headH: 50, fs: 16, hfs: 13 }, 9),
        kbEl(no, title, 'note', 'भाव नोट', [46, 920, 628, 44], kunT(46, 940, 'भाव स्वामी राशि स्वामीबाट लिइएको हो; स्थित ग्रह प्रत्येक ग्रहको भाव क्षेत्रबाट।', 12, '#7183a8', 500), 6),
        kbFooter(no, title)
      ]));
    }

    /* 6 — shadbala */
    {
      const no = 6, title = 'षड्बल (Shadbala)';
      const sb = data.shadbala || {}, sp = sb.planets || {};
      const names = KUN_ORDER.slice(0, 7).filter(n => sp[n]);
      if (names.length) {
        let max = 1;
        names.forEach(n => { const v = +sp[n].total_rupas || 0, r = +sp[n].required_rupas || 0; max = Math.max(max, v, r) });
        max *= 1.12;
        const rank = sb.ranking || [];
        let bars = '';
        const bx = 168, bw = 360;
        names.forEach((n, i) => {
          const p = sp[n], y = 300 + i * 82, v = +p.total_rupas || 0, req = +p.required_rupas || 0;
          const col = p.is_strong ? '#34d399' : '#fb7185';
          bars += kunT(46, y + 14, KUN_NE[n], 18, '#e9eefb', 700);
          bars += kunT(46, y + 36, '#' + neNum((rank.indexOf(n) + 1) || i + 1), 12, '#7183a8', 500);
          bars += '<rect x="' + bx + '" y="' + (y + 2) + '" width="' + bw + '" height="26" rx="13" fill="#0f172b" stroke="#223052" stroke-width="1"/>';
          bars += '<rect x="' + bx + '" y="' + (y + 2) + '" width="' + Math.max(2, bw * v / max) + '" height="26" rx="13" fill="' + col + '"/>';
          if (req > 0) bars += '<line x1="' + (bx + bw * req / max) + '" y1="' + (y - 4) + '" x2="' + (bx + bw * req / max) + '" y2="' + (y + 34) + '" stroke="#e8b923" stroke-width="2" stroke-dasharray="4 4"/>';
          bars += kunT(545, y + 16, kunNum(v, 2), 17, '#e9eefb', 700);
          bars += kunT(650, y + 16, p.is_strong ? 'बलवान' : 'दुर्बल', 12, col, 700, 'end');
        });
        pages.push(kbPage(no, title, 'ग्रह बल — रूपमा कुल योग', [
          kbHeader(no, title, 'ग्रह बल — रूपमा कुल योग'),
          kbCardEl(no, title, 'सर्वाधिक बल कार्ड', 46, 176, 300, 86, 'सर्वाधिक बल', (KUN_NE[sb.strongest] || sb.strongest || '—') + ' · ' + kunNum((sp[sb.strongest] || {}).total_rupas, 2) + ' रूप', '#34d399', { fs: 20, chars: 20 }),
          kbCardEl(no, title, 'सबैभन्दा कमजोर कार्ड', 374, 176, 300, 86, 'सबैभन्दा कमजोर', (KUN_NE[sb.weakest] || sb.weakest || '—') + ' · ' + kunNum((sp[sb.weakest] || {}).total_rupas, 2) + ' रूप', '#fb7185', { fs: 20, chars: 20 }),
          kbEl(no, title, 'graph', 'षड्बल बार चार्ट', [46, 286, 628, 620], bars, 8.6),
          kbEl(no, title, 'note', 'षड्बल व्याख्या', [46, 920, 628, 44], kunT(46, 940, 'हरियो पट्टी = required रूपभन्दा माथि; रातो = मुनि। धेरै ठूलो = बलियो।', 13, '#9fb0d0', 500), 6.2),
          kbEl(no, title, 'note', 'required रूप सूची', [46, 960, 628, 44], kunT(46, 972, 'required: ' + names.map(n => KUN_NE[n] + ' ' + kunNum(sp[n].required_rupas, 1)).join(' · '), 12, '#7183a8', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* 7 — shadbala table */
    {
      const no = 7, title = 'षड्बल घटक तालिका';
      const sb = data.shadbala || {}, sp = sb.planets || {};
      const rows = KUN_ORDER.slice(0, 7).filter(n => sp[n]).map(n => {
        const p = sp[n];
        return [KUN_NE[n], kunNum(p.sthana_bala, 2), kunNum(p.dig_bala, 2), kunNum(p.kala_bala, 2), kunNum(p.cheshta_bala, 2), kunNum(p.naisargika_bala, 2), kunNum(p.drik_bala, 2), kunNum(p.total_rupas, 2)];
      });
      if (rows.length) pages.push(kbPage(no, title, 'स्थान, दिग्, काल, चेष्टा, नैसर्गिक र दृक् बल', [
        kbHeader(no, title, 'स्थान, दिग्, काल, चेष्टा, नैसर्गिक र दृक् बल'),
        kbTableEl(no, title, 'षड्बल घटक तालिका', 46, 184, 628, [
          { t: 'ग्रह', w: 92 }, { t: 'स्थान', w: 80 }, { t: 'दिग्', w: 76 }, { t: 'काल', w: 76 }, { t: 'चेष्टा', w: 84 }, { t: 'नैसर्गिक', w: 92 }, { t: 'दृक्', w: 72 }, { t: 'कुल', w: 80 }
        ], rows, { rowH: 68, headH: 54, fs: 15, hfs: 12 }, 9),
        kbEl(no, title, 'note', 'रूप नोट', [46, 792, 628, 48], kunT(46, 820, 'सबै मान रूप (Rupa) मा; १ रूप = ६० शष्ट्यंश।', 13, '#9fb0d0', 500), 6.2),
        kbEl(no, title, 'note', 'बल नोट', [46, 842, 628, 48], kunT(46, 852, 'कुल रूप आवश्यक रूपभन्दा बढी भए ग्रह बलवान मानिन्छ।', 13, '#9fb0d0', 500), 6.2),
        kbFooter(no, title)
      ]));
    }

    /* 8 — chandra */
    {
      const no = 8, title = 'चन्द्र कुण्डली';
      const moonSign = +moon.sign_number || 1;
      const houses = kunHouses(planets, moonSign, 'chandra');
      let chips = '';
      const chipData = [
        ['चन्द्र नक्षत्र', (moon.nakshatra_nepali || '—') + ' · पद ' + neNum(moon.nakshatra_pada || '—')],
        ['नक्षत्र स्वामी', KUN_NE[moon.nakshatra_lord] || moon.nakshatra_lord || '—'],
        ['चन्द्र भाव', neNum(moon.house || '—') + ' (' + (KUN_HOUSE_NE[moon.house] || '—') + ')']
      ];
      const cw = 196, gap = 16, x0 = 360 - (chipData.length * cw + (chipData.length - 1) * gap) / 2;
      chipData.forEach((c, i) => chips += kunCard(x0 + i * (cw + gap), 902, cw, 108, c[0], c[1], '#e8b923', { fs: 18, chars: 10, lh: 25 }));
      pages.push(kbPage(no, title, 'Moon Chart · मन, भावना र मातृभाव', [
        kbHeader(no, title, 'Moon Chart · मन, भावना र मातृभाव'),
        kbChartEl(no, title, houses, moonSign, 'चन्द्र कुण्डली चार्ट', 60, 190, 600),
        kbEl(no, title, 'note', 'चन्द्र राशि अंश', [46, 802, 628, 50], kunT(360, 822, 'चन्द्र राशि: ' + kunSignByNum(moonSign) + ' · ' + kunDMS(moon.longitude_in_sign || 0), 20, '#e9eefb', 700, 'middle'), 6.2),
        kbEl(no, title, 'note', 'चन्द्र कुण्डली व्याख्या', [46, 842, 628, 40], kunT(360, 862, 'चन्द्र कुण्डलीमा चन्द्रलाई लग्न मानेर भाव राखिएको छ।', 13, '#9fb0d0', 500, 'middle'), 5.6),
        kbEl(no, title, 'cards', 'चन्द्र नक्षत्र कार्डहरू', [46, 890, 628, 120], chips, 7.2),
        kbFooter(no, title)
      ]));
    }

    /* 9 — D9 */
    {
      const no = 9, title = 'नवमांश कुण्डली (D9)';
      const d9 = (data.vargas || {}).D9 || {};
      const d9l = +((d9.lagna || {}).sign_number) || 1;
      const d9p = d9.planets || [];
      if (d9p.length) {
        const houses = kunHouses(d9p, d9l, 'd9');
        let chips = '';
        const chipData = [
          ['D9 लग्न', kunSignByNum(d9l)],
          ['D9 चन्द्र', kunSignNe(d9p.find(p => p.name === 'Moon') || {})],
          ['D9 सूर्य', kunSignNe(d9p.find(p => p.name === 'Sun') || {})]
        ];
        const cw = 196, gap = 16, x0 = 360 - (chipData.length * cw + (chipData.length - 1) * gap) / 2;
        chipData.forEach((c, i) => chips += kunCard(x0 + i * (cw + gap), 902, cw, 108, c[0], c[1], '#e8b923', { fs: 19, chars: 10, lh: 25 }));
        pages.push(kbPage(no, title, 'Navamsha · विवाह र धर्म', [
          kbHeader(no, title, 'Navamsha · विवाह र धर्म'),
          kbChartEl(no, title, houses, d9l, 'नवमांश चार्ट', 60, 190, 600),
          kbEl(no, title, 'note', 'D9 लग्न अंश', [46, 802, 628, 50], kunT(360, 822, 'D9 लग्न: ' + kunSignByNum(d9l) + ' · ' + kunDMS((d9.lagna || {}).longitude_in_sign || 0), 20, '#e9eefb', 700, 'middle'), 6.2),
          kbEl(no, title, 'note', 'D9 व्याख्या', [46, 842, 628, 40], kunT(360, 862, 'नवमांश कुण्डली — विवाह, धर्म, भाग्य र सूक्ष्म ग्रह स्थिति।', 13, '#9fb0d0', 500, 'middle'), 5.6),
          kbEl(no, title, 'cards', 'D9 लग्न · चन्द्र · सूर्य कार्ड', [46, 890, 628, 120], chips, 7.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* 10 — panchang */
    {
      const no = 10, title = 'पञ्चाङ्ग विवरण';
      const t = pc.tithi || {}, n = pc.nakshatra || {}, y = pc.yoga || {}, k = pc.karana || {};
      const cards = [
        ['तिथि', (t.birth_nepali || t.nepali || '—') + ' · ' + (t.paksha_nepali || '')],
        ['वार', (pc.vara || {}).nepali || '—'],
        ['नक्षत्र', (n.nepali || '—') + ' · पद ' + neNum(n.pada || '—')],
        ['योग', y.birth_nepali || y.nepali || '—'],
        ['करण', k.birth_nepali || k.nepali || '—'],
        ['चन्द्र राशि', (pc.chandra_rashi || {}).nepali || '—'],
        ['सम्वत्सर', pc.samvatsara || '—'],
        ['नेपाल संवत', pc.nepal_samvat ? neNum(pc.nepal_samvat.year) + ' ' + (pc.nepal_samvat.era || '') : '—'],
        ['सूर्योदय', neNum((pc.sunrise || {}).time || '—')],
        ['सूर्यास्त', neNum((pc.sunset || {}).time || '—')],
        ['दिनमान', neNum(pc.dinman || pc.day_duration || '—')],
        ['चान्द्र मास', (pc.lunar_month || {}).nepali || '—']
      ];
      const els = [kbHeader(no, title, 'जन्म समयको तिथि, वार, नक्षत्र, योग र करण')];
      cards.forEach((c, i) => {
        const col = i % 2, row = Math.floor(i / 2);
        const x = 46 + col * 328, yy = 180 + row * 142;
        els.push(kbCardEl(no, title, 'पञ्चाङ्ग कार्ड — ' + c[0], x, yy, 300, 126, c[0], c[1], '#e8b923', { fs: 20, chars: 19, lh: 26 }));
      });
      els.push(kbFooter(no, title));
      pages.push(kbPage(no, title, 'जन्म समयको पञ्चाङ्ग', els));
    }

    /* 11 — SAV */
    {
      const no = 11, title = 'अष्टकवर्ग (SAV)';
      const av = data.ashtakavarga || {}, sav = av.sav || [];
      if (sav.length) {
        const avLagna = +av.lagna_sign || lagnaSign;
        const houses = {};
        for (let h = 1; h <= 12; h++) {
          const signIdx = ((avLagna - 1 + h - 1) % 12);
          houses[h] = [neNum(sav[signIdx] == null ? '—' : sav[signIdx])];
        }
        const strong = av.strong_houses || [], weak = av.weak_houses || [];
        const els = [
          kbHeader(no, title, 'Samudaya Ashtakavarga · भाव बिन्दु बल'),
          kbChartEl(no, title, houses, avLagna, 'SAV चार्ट', 110, 180, 500, { sav: true }),
          kbEl(no, title, 'heading', 'SAV शीर्षक', [46, 680, 628, 50], kunT(360, 704, 'समुदाय अष्टकवर्ग (SAV) — प्रत्येक भावको बिन्दु', 19, '#e9eefb', 700, 'middle'), 5.4)
        ];
        for (let h = 1; h <= 12; h++) {
          const col = (h - 1) % 4, row = Math.floor((h - 1) / 4);
          const x = 46 + col * 158, yy = 738 + row * 108;
          const signNum = ((avLagna - 1 + h - 1) % 12) + 1;
          const v = sav[signNum - 1];
          const isS = strong.indexOf(signNum) >= 0, isW = weak.indexOf(signNum) >= 0;
          let inner = '<rect x="' + x + '" y="' + yy + '" width="146" height="96" rx="13" fill="#121d35" stroke="' + (isS ? '#34d399' : isW ? '#fb7185' : '#2b3856') + '" stroke-width="1.5"/>';
          inner += kunT(x + 14, yy + 24, 'भाव ' + neNum(h), 12, '#9fb0d0', 600);
          inner += kunT(x + 14, yy + 62, v == null ? '—' : neNum(v), 30, isS ? '#34d399' : isW ? '#fb7185' : '#f6d365', 700);
          els.push(kbEl(no, title, 'cards', 'SAV भाव ' + neNum(h) + ' कार्ड', [x, yy, 146, 96], inner, 6.2));
        }
        els.push(kbEl(no, title, 'note', 'SAV कुल बिन्दु नोट', [46, 1080, 628, 44], kunT(46, 1110, 'हरियो = बलियो भाव · रातो = कमजोर भाव · कुल बिन्दु ' + neNum(av.total_bindus || '—'), 13, '#9fb0d0', 500), 6.2));
        els.push(kbFooter(no, title));
        pages.push(kbPage(no, title, 'Samudaya Ashtakavarga · भाव बिन्दु बल', els));
      }
    }

    /* 12 — vimshopaka */
    {
      const no = 12, title = 'विंशोपक बल';
      const vim = data.vimshopaka_bala || {}, vp = vim.planets || {};
      const names = KUN_ORDER.filter(n => vp[n]);
      if (names.length) {
        const max = +vim.max_total || 20;
        const els = [kbHeader(no, title, 'Vimshopaka Bala · १६ वर्गको भारित बल')];
        names.forEach((n, i) => {
          const v = vp[n], yy = 190 + i * 88, total = +v.total || 0;
          const pct = clamp(total / max);
          let inner = kunT(46, yy + 16, v.name_ne || KUN_NE[n], 19, '#e9eefb', 700);
          inner += kunT(46, yy + 38, v.name_en || n, 11, '#7183a8', 500);
          inner += '<rect x="170" y="' + (yy + 8) + '" width="380" height="24" rx="12" fill="#0f172b" stroke="#223052" stroke-width="1"/>';
          inner += '<rect x="170" y="' + (yy + 8) + '" width="' + Math.max(2, 380 * pct) + '" height="24" rx="12" fill="' + (pct >= .75 ? '#34d399' : pct >= .5 ? '#e8b923' : '#fb7185') + '"/>';
          inner += kunT(570, yy + 21, kunNum(total, 2) + ' / ' + neNum(max), 17, '#e9eefb', 700);
          inner += kunT(660, yy + 21, (v.rating || '').toString(), 12, '#9fb0d0', 600, 'end');
          els.push(kbEl(no, title, 'graph', 'विंशोपक — ' + (v.name_ne || KUN_NE[n]), [46, yy - 16, 628, 72], inner, 6.4));
        });
        els.push(kbEl(no, title, 'note', 'विंशोपक नोट', [46, 990, 628, 50], kunT(46, 1000, 'विंशोपक बल १६ वर्गको भारित योग हो; अधिकतम ' + neNum(max) + '।', 13, '#9fb0d0', 500), 6.2));
        els.push(kbFooter(no, title));
        pages.push(kbPage(no, title, 'Vimshopaka Bala · १६ वर्गको भारित बल', els));
      }
    }

    /* 13 — avastha */
    {
      const no = 13, title = 'ग्रह अवस्था';
      const av = data.avasthas || {}, ap = av.planets || {};
      const rows = KUN_ORDER.filter(n => ap[n]).map(n => {
        const p = ap[n];
        return [KUN_NE[n], kunSignByNum(p.sign_number), (p.bala_avastha || {}).nepali || '—', (p.deeptadi_avastha || {}).nepali || '—'];
      });
      if (rows.length) pages.push(kbPage(no, title, 'Baladi र Deeptadi Avastha', [
        kbHeader(no, title, 'Baladi र Deeptadi Avastha'),
        kbTableEl(no, title, 'ग्रह अवस्था तालिका', 46, 190, 628, [
          { t: 'ग्रह', w: 120 }, { t: 'राशि', w: 120 }, { t: 'बालादि अवस्था', w: 190 }, { t: 'दीप्तादि अवस्था', w: 198 }
        ], rows, { rowH: 72, headH: 54, fs: 17, hfs: 13 }, 8.6),
        kbEl(no, title, 'note', 'अवस्था नोट', [46, 930, 628, 48], kunT(46, 950, 'बालादि अवस्था ग्रहको राशि-अंशबाट; दीप्तादि अवस्था ग्रहको बल र सम्बन्धबाट निर्धारण हुन्छ।', 13, '#9fb0d0', 500), 6.2),
        kbFooter(no, title)
      ]));
    }

    /* every remaining Kundali page and element (vargas, chalit, cusps,
       special points, avakahada, detailed panchang, BAV, yogini and
       ashtottari dasha, varshaphala, jaimini, KP, dasha chain, remedies) */
    kbCatalogExtras(pages, data, meta);

    /* yogas */
    {
      const yogas = data.parashara_yogas || [];
      if (yogas.length) {
        const sevNe = s => s === 'highly_auspicious' ? 'अति शुभ' : s === 'auspicious' ? 'शुभ' : s === 'challenging' ? 'चुनौतीपूर्ण' : s === 'neutral' ? 'सामान्य' : 'योग';
        const sevCol = s => s === 'highly_auspicious' ? '#f6d365' : s === 'auspicious' ? '#34d399' : s === 'challenging' ? '#fb7185' : '#9fb0d0';
        let pageNo = pages.length + 1, partNo = 1;
        for (let start = 0; start < yogas.length; start += 4) {
          const part = yogas.slice(start, start + 4);
          const title = 'शुभ योग (भाग ' + neNum(partNo) + ')';
          const els = [kbHeader(pageNo, title, 'पाराशरी योग — वास्तविक ग्रह संयोजनबाट')];
          part.forEach((y, i) => {
            const cy = 176 + i * 252, col = sevCol(y.severity), pct = clamp((+y.strength_pct || 0) / 100);
            let inner = '<rect x="46" y="' + cy + '" width="628" height="238" rx="16" fill="#121d35" stroke="#2b3856" stroke-width="1.5"/>';
            inner += '<rect x="46" y="' + cy + '" width="6" height="238" rx="3" fill="' + col + '"/>';
            inner += kunT(70, cy + 32, y.nepali || y.name || 'योग', 21, '#f6d365', 700);
            inner += kunT(650, cy + 32, sevNe(y.severity), 12, col, 700, 'end');
            inner += '<rect x="70" y="' + (cy + 50) + '" width="580" height="7" rx="3.5" fill="#0f172b"/>';
            inner += '<rect x="70" y="' + (cy + 50) + '" width="' + Math.max(2, 580 * pct) + '" height="7" rx="3.5" fill="' + col + '"/>';
            inner += kunPara(70, cy + 82, y.cause_ne || y.cause_en || '', 50, 14.5, 21, '#b9c6e4', 3);
            inner += kunPara(70, cy + 152, 'फल: ' + (y.result_ne || y.result_en || ''), 50, 14.5, 21, '#e9eefb', 3);
            els.push(kbEl(pageNo, title, 'report', 'योग कार्ड — ' + (y.nepali || y.name || 'योग'), [46, cy, 628, 238], inner, 7.6));
          });
          els.push(kbFooter(pageNo, title));
          pages.push(kbPage(pageNo, title, 'पाराशरी योग', els));
          pageNo++; partNo++;
        }
      }
    }

    /* dasha */
    {
      const no = pages.length + 1, title = 'विंशोत्तरी महादशा';
      const dasha = data.dasha || [];
      if (dasha.length) {
        const rows = dasha.slice(0, 9).map(d => [
          d.lord_nepali || KUN_NE[d.lord] || d.lord,
          d.start_bs_available ? kunBsShort(d.start_bs) : '—',
          d.end_bs_available ? kunBsShort(d.end_bs) : '—',
          kunNe(d.start), kunNe(d.end)
        ]);
        const activeIdx = dasha.slice(0, 9).findIndex(d => d.is_active);
        pages.push(kbPage(no, title, 'Vimshottari Mahadasha कालक्रम', [
          kbHeader(no, title, 'Vimshottari Mahadasha कालक्रम'),
          kbTableEl(no, title, 'महादशा तालिका', 46, 184, 628, [
            { t: 'महादशा', w: 100 }, { t: 'सुरु (BS)', w: 150 }, { t: 'अन्त्य (BS)', w: 150 }, { t: 'सुरु (AD)', w: 130 }, { t: 'अन्त्य (AD)', w: 130 }
          ], rows, {
            rowH: 64, headH: 52, fs: 14, hfs: 12,
            rowFill: ri => ri === activeIdx ? '#143024' : (ri % 2 ? '#0f172b' : '#121d35'),
            cellColor: (ri, ci, v) => ri === activeIdx ? '#34d399' : null
          }, 9),
          kbEl(no, title, 'note', 'महादशा नोट', [46, 838, 628, 44], kunT(46, 860, 'विंशोत्तरी महादशा — जन्मदेखि क्रमशः। हरियो पङ्क्ति वर्तमान महादशा हो।', 13, '#9fb0d0', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* antardasha */
    {
      const no = pages.length + 1, title = 'अन्तर्दशा कालक्रम';
      const md = (data.dasha || []).find(d => d.is_active);
      if (md) {
        const kids = (md.children || []).slice(0, 9);
        const rows = kids.map(d => [
          d.lord_nepali || KUN_NE[d.lord] || d.lord,
          d.start_bs_available ? kunBsShort(d.start_bs) : '—',
          d.end_bs_available ? kunBsShort(d.end_bs) : '—',
          kunNe(d.start), kunNe(d.end)
        ]);
        const activeIdx = kids.findIndex(d => d.is_active);
        pages.push(kbPage(no, title, 'Antardasha · सक्रिय महादशाभित्र', [
          kbHeader(no, title, 'Antardasha · सक्रिय महादशाभित्र'),
          kbEl(no, title, 'banner', 'सक्रिय महादशा', [46, 170, 628, 44], kunT(46, 182, 'सक्रिय महादशा: ' + (md.lord_nepali || KUN_NE[md.lord] || md.lord) + ' · ' + kunBsShort(md.start_bs) + ' — ' + kunBsShort(md.end_bs), 16, '#f6d365', 700), 6.2),
          kbTableEl(no, title, 'अन्तर्दशा तालिका', 46, 208, 628, [
            { t: 'अन्तर्दशा', w: 110 }, { t: 'सुरु (BS)', w: 150 }, { t: 'अन्त्य (BS)', w: 150 }, { t: 'सुरु (AD)', w: 125 }, { t: 'अन्त्य (AD)', w: 125 }
          ], rows, {
            rowH: 64, headH: 52, fs: 14, hfs: 12,
            rowFill: ri => ri === activeIdx ? '#143024' : (ri % 2 ? '#0f172b' : '#121d35'),
            cellColor: (ri, ci, v) => ri === activeIdx ? '#34d399' : null
          }, 9),
          kbEl(no, title, 'note', 'अन्तर्दशा नोट', [46, 858, 628, 44], kunT(46, 890, 'अन्तर्दशा सक्रिय महादशाभित्रको क्रम हो; हरियो पङ्क्ति वर्तमान अन्तर्दशा।', 13, '#9fb0d0', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* kaal sarp */
    {
      const no = pages.length + 1, title = 'कालसर्प दोष विश्लेषण';
      const k = data.kaal_sarp_dosha || {};
      const present = !!k.present;
      let banner = '<rect x="46" y="184" width="628" height="132" rx="18" fill="' + (present ? '#2a1720' : '#12281f') + '" stroke="' + (present ? '#fb7185' : '#34d399') + '" stroke-width="2"/>';
      banner += kunT(70, 222, 'कालसर्प दोष', 16, '#9fb0d0', 600);
      banner += kunT(70, 268, present ? 'उपस्थित छ' : 'छैन', 40, present ? '#fb7185' : '#34d399', 700);
      banner += kunT(650, 250, present ? 'विशेष विश्लेषण आवश्यक' : 'राहु-केतु अक्षभित्र सबै ग्रह छैनन्', 14, '#9fb0d0', 500, 'end');
      const rahu = k.rahu || {}, ketu = k.ketu || {};
      const inside = (k.grahas_in_ksd || []).map(g => KUN_NE[g.name] || g.name).join(', ') || '—';
      const outside = (k.grahas_outside || []).map(g => KUN_NE[g.name] || g.name).join(', ') || '—';
      pages.push(kbPage(no, title, 'Rahu-Ketu axis र ग्रह स्थिति', [
        kbHeader(no, title, 'Rahu-Ketu axis र ग्रह स्थिति'),
        kbEl(no, title, 'banner', 'कालसर्प स्थिति ब्यानर', [46, 184, 628, 132], banner, 6.4),
        kbCardEl(no, title, 'राहु कार्ड', 46, 340, 300, 120, 'राहु', kunSignByNum(rahu.sign_number) + ' · भाव ' + neNum(rahu.house || '—'), '#fb7185', { fs: 21, chars: 18 }),
        kbCardEl(no, title, 'केतु कार्ड', 374, 340, 300, 120, 'केतु', kunSignByNum(ketu.sign_number) + ' · भाव ' + neNum(ketu.house || '—'), '#e8b923', { fs: 21, chars: 18 }),
        kbCardEl(no, title, 'अक्षभित्रका ग्रह', 46, 486, 628, 120, 'अक्षभित्रका ग्रह', inside, present ? '#fb7185' : '#9fb0d0', { fs: 19, chars: 40 }),
        kbCardEl(no, title, 'अक्षबाहिरका ग्रह', 46, 626, 628, 120, 'अक्षबाहिरका ग्रह', outside, '#34d399', { fs: 19, chars: 40 }),
        kbEl(no, title, 'note', 'कालसर्प नोट', [46, 780, 628, 60], kunT(46, 800, 'कालसर्प दोष राहु-केतु अक्षभित्र सबै सात ग्रह परेमा मानिन्छ। यो गणना Kundali-Desktop बाट।', 13, '#9fb0d0', 500), 6.2),
        kbFooter(no, title)
      ]));
    }

    /* lal kitab */
    {
      const no = pages.length + 1, title = 'लालकिताब ग्रह स्थिति';
      const lk = data.lal_kitab || {}, list = lk.planet_status || [];
      if (list.length) {
        const rows = list.slice(0, 9).map(p => [
          p.name_ne || KUN_NE[p.name] || p.name,
          p.sign_name || kunSignByNum(p.sign_number),
          neNum(p.house),
          p.nek_manda || '—',
          p.soya || '—',
          p.kismat_jagane || '—'
        ]);
        pages.push(kbPage(no, title, 'Lal Kitab · भाव आधारित शुभ-अशुभ', [
          kbHeader(no, title, 'Lal Kitab · भाव आधारित शुभ-अशुभ'),
          kbTableEl(no, title, 'लालकिताब तालिका', 46, 184, 628, [
            { t: 'ग्रह', w: 100 }, { t: 'राशि', w: 100 }, { t: 'भाव', w: 66 }, { t: 'नेक/मन्द', w: 160 }, { t: 'सोया', w: 90 }, { t: 'किस्मत', w: 120 }
          ], rows, {
            rowH: 64, headH: 52, fs: 16, hfs: 13,
            cellColor: (ri, ci, v) => ci === 3 ? (list[ri].is_nek ? '#34d399' : '#fb7185') : null
          }, 9),
          kbEl(no, title, 'note', 'लालकिताब नोट', [46, 858, 628, 44], kunT(46, 880, 'लालकिताब ग्रह स्थिति — भाव अनुसार नेक/मन्द, सोया र किस्मत जाग्ने स्थिति।', 13, '#9fb0d0', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* remedies */
    {
      const no = pages.length + 1, title = 'रत्न तथा उपाय';
      const rem = data.remedies || {}, gems = rem.recommended_gemstones || [];
      if (gems.length) {
        const els = [kbHeader(no, title, 'Kundali-Desktop को लग्नेश/भाग्येश आधारित सिफारिस')];
        gems.slice(0, 3).forEach((g, i) => {
          const yy = 184 + i * 208;
          let inner = '<rect x="46" y="' + yy + '" width="628" height="192" rx="16" fill="#121d35" stroke="#2b3856" stroke-width="1.5"/>';
          inner += '<rect x="46" y="' + yy + '" width="6" height="192" rx="3" fill="#f6d365"/>';
          inner += kunT(70, yy + 26, g.category_name || 'रत्न', 12, '#9fb0d0', 600);
          inner += kunT(70, yy + 56, g.gemstone || '—', 23, '#f6d365', 700);
          inner += kunT(70, yy + 84, (KUN_NE[g.planet] || g.planet || '') + ' · ' + (g.upratna || ''), 13, '#e9eefb', 500);
          inner += kunT(70, yy + 110, 'मन्त्र: ' + (g.simple_mantra || g.beej_mantra || '—'), 13, '#b9c6e4', 500);
          inner += kunT(70, yy + 134, 'जप: ' + (g.jap_count || '—') + ' · ' + (g.day || ''), 12, '#7183a8', 500);
          inner += kunPara(70, yy + 154, 'फल: ' + (g.benefit || ''), 76, 12, 16, '#9fb0d0', 2);
          els.push(kbEl(no, title, 'report', 'रत्न कार्ड — ' + (g.gemstone || 'रत्न'), [46, yy, 628, 192], inner, 7.2));
        });
        els.push(kbEl(no, title, 'note', 'रत्न सल्लाह', [46, 824, 628, 50], kunT(46, 844, 'रत्न धारण गर्नुअघि योग्य ज्योतिषी वा रत्न विशेषज्ञसँग परामर्श गर्नुहोस्।', 13, '#9fb0d0', 500), 6.2));
        els.push(kbFooter(no, title));
        pages.push(kbPage(no, title, 'Kundali-Desktop को सिफारिस', els));
      }
    }

    /* graha pages */
    KUN_ORDER.forEach(name => {
      const p = planets.find(x => x.name === name);
      if (!p) return;
      const no = pages.length + 1, title = KUN_NE[name] + ' ग्रह विश्लेषण';
      const sb = ((data.shadbala || {}).planets || {})[name] || {};
      const vim = ((data.vimshopaka_bala || {}).planets || {})[name] || {};
      const av = ((data.avasthas || {}).planets || {})[name] || {};
      const lk = ((data.lal_kitab || {}).planet_status || []).find(x => x.name === name) || {};
      const states = kunStateText(p);
      let medal = '<circle cx="146" cy="300" r="86" fill="#121d35" stroke="#e8b923" stroke-opacity=".4" stroke-width="2"/>';
      medal += kunT(146, 282, KUN_AB[name] || name.slice(0, 2), 54, '#f6d365', 700, 'middle');
      medal += kunT(146, 338, KUN_NE[name] || name, 20, '#e9eefb', 700, 'middle');
      medal += kunT(146, 416, kunSignByNum(p.sign_number), 23, '#e8b923', 700, 'middle');
      medal += kunT(146, 448, 'भाव ' + neNum(p.house) + ' · ' + (KUN_HOUSE_NE[p.house] || ''), 15, '#9fb0d0', 600, 'middle');
      const stats = [
        ['राशि', kunSignNe(p)],
        ['भाव', neNum(p.house) + ' (' + (KUN_HOUSE_NE[p.house] || '—') + ')'],
        ['अंश', kunDMS(p.longitude_in_sign)],
        ['नक्षत्र', (p.nakshatra_nepali || '—') + ' · पद ' + neNum(p.nakshatra_pada || '—')],
        ['नक्षत्र स्वामी', KUN_NE[p.nakshatra_lord] || p.nakshatra_lord || '—'],
        ['स्थिति', states || '—'],
        ['षड्बल', kunNum(sb.total_rupas, 2) + ' रूप (' + (sb.is_strong ? 'बलवान' : 'दुर्बल') + ')'],
        ['विंशोपक', kunNum(vim.total, 2) + ' / २०'],
        ['बालादि अवस्था', (av.bala_avastha || {}).nepali || '—'],
        ['दीप्तादि अवस्था', (av.deeptadi_avastha || {}).nepali || '—']
      ];
      let statsSvg = '';
      stats.forEach((s, i) => {
        const col = i % 2, row = Math.floor(i / 2), x = 286 + col * 198, yy = 212 + row * 72;
        statsSvg += kunT(x, yy, s[0], 12, '#9fb0d0', 600);
        statsSvg += kunT(x, yy + 26, kunFit(s[1], 22), 16, '#e9eefb', 600);
      });
      let report = '<rect x="46" y="588" width="628" height="220" rx="18" fill="#121d35" stroke="#2b3856" stroke-width="1.5"/>';
      report += kunT(70, 624, 'लालकिताब फल (वास्तविक भाव स्थिति)', 17, '#e8b923', 700);
      report += kunPara(70, 662, lk.phal || 'यो ग्रहको लालकिताब फल उपलब्ध छैन।', 39, 16, 25, '#e9eefb', 4);
      let upay = '<rect x="46" y="822" width="628" height="104" rx="16" fill="#121d35" stroke="#2b3856" stroke-width="1.5"/>';
      upay += kunT(70, 850, 'उपाय', 15, '#34d399', 700);
      (lk.upayas || []).slice(0, 2).forEach((u, i) => upay += kunT(70, 880 + i * 30, '• ' + kunFit(u, 44), 14, '#b9c6e4', 500));
      pages.push(kbPage(no, title, name + ' · ' + (p.sign_name || ''), [
        kbHeader(no, title, name + ' · ' + (p.sign_name || '')),
        kbEl(no, title, 'art', 'ग्रह मेडलियन — ' + (KUN_NE[name] || name), [46, 200, 240, 300], medal, 7),
        kbEl(no, title, 'table', 'ग्रह विवरण ग्रिड', [286, 200, 392, 380], statsSvg, 8),
        kbEl(no, title, 'report', 'लालकिताब फल', [46, 588, 628, 220], report, 7.6),
        kbEl(no, title, 'report', 'उपाय', [46, 822, 628, 104], upay, 7),
        kbEl(no, title, 'note', 'ग्रह विश्लेषण नोट', [46, 940, 628, 50], kunT(46, 980, 'ग्रह स्थिति, षड्बल, विंशोपक र अवस्था Kundali-Desktop बाट गणना गरिएको हो।', 12, '#7183a8', 500), 6.2),
        kbFooter(no, title)
      ]));
    });

    /* end */
    {
      const no = pages.length + 1, title = 'धन्यवाद';
      const md = (data.dasha || []).find(d => d.is_active) || {};
      let chips = '';
      const chipData = [
        ['लग्न', kunSignByNum(lagnaSign)],
        ['चन्द्र राशि', (data.panchang && data.panchang.chandra_rashi) ? data.panchang.chandra_rashi.nepali : kunSignNe(moon)],
        ['जन्म नक्षत्र', (moon.nakshatra_nepali || '—')],
        ['सक्रिय महादशा', md.lord_nepali || KUN_NE[md.lord] || '—']
      ];
      const cw = 148, gap = 12, x0 = 360 - (chipData.length * cw + (chipData.length - 1) * gap) / 2;
      chipData.forEach((c, i) => chips += kunCard(x0 + i * (cw + gap), 680, cw, 112, c[0], c[1], '#e8b923', { fs: 18, chars: 8, lh: 24 }));
      const endNameEl = kbEl(no, title, 'heading', 'जातकको नाम', [46, 500, 628, 80], kunT(360, 548, meta.name || 'जातक', 40, '#e9eefb', 700, 'middle'), 5.6);
      endNameEl.privacy = [{ id: 'name', label: 'जातकको नाम (अन्तिम कार्ड)', rects: [{ x: 84, y: 504, w: 552, h: 64 }] }];
      pages.push(kbPage(no, title, 'जन्म कुण्डली प्रस्तुति समाप्त', [
        kbHeader(no, title, 'जन्म कुण्डली प्रस्तुति समाप्त'),
        kbEl(no, title, 'heading', 'शुभम्', [46, 340, 628, 80], kunT(360, 372, 'शुभम्', 66, '#f6d365', 700, 'middle'), 5.6),
        kbEl(no, title, 'note', 'मङ्गल मन्त्र', [46, 420, 628, 50], kunT(360, 442, '॥ सर्वे भवन्तु सुखिनः ॥', 22, '#9fb0d0', 500, 'middle'), 5.6),
        endNameEl,
        kbEl(no, title, 'note', 'जन्म मिति र स्थान', [46, 580, 628, 44], kunT(360, 592, kunDateNe(meta.birth_date) + ' · ' + (meta.city || meta.birth_place || ''), 17, '#9fb0d0', 500, 'middle'), 6.2),
        kbEl(no, title, 'cards', 'अन्तिम चिप कार्डहरू', [46, 660, 628, 140], chips, 7),
        kbEl(no, title, 'note', 'प्रस्तुति नोट १', [46, 870, 628, 50], kunT(360, 890, 'यो प्रस्तुति Kundali-Desktop को वास्तविक गणना डाटाबाट स्वतः बनाइएको हो।', 14, '#9fb0d0', 500, 'middle'), 6.2),
        kbEl(no, title, 'note', 'प्रस्तुति नोट २', [46, 910, 628, 44], kunT(360, 920, 'कुनै पनि फलादेश ग्रह स्थिति, षड्बल, दशा र योगको गणनामा आधारित छ।', 13, '#7183a8', 500, 'middle'), 6.2),
        kbFooter(no, title)
      ]));
    }

    return { pages: pages, dateLabel: dateLabel, placeLabel: placeLabel };
  }

  /* ═══════════════════════════════════════════════════════════════
     extended catalog — every remaining Kundali page and element
     ═══════════════════════════════════════════════════════════════ */
  function kbCatalogExtras(pages, data, meta) {
    const vargas = data.vargas || {};
    const planets = data.planets || [];
    const lagnaSign = +((data.lagna || {}).sign_number) || 1;
    const panchang = data.panchang || {};
    const houses = data.houses || {};
    const kp = data.kp_system || {};

    /* ── all sixteen vargas — one real chart page per varga ── */
    {
      const LB = {
        D2: ['होरा', 'धन, सम्पत्ति र वृत्ति'],
        D3: ['द्रेक्काण', 'भाई-बहिनी, साहस र पराक्रम'],
        D4: ['चतुर्थांश', 'गृह, भूमि, वाहन र सुख'],
        D7: ['सप्तमांश', 'सन्तान, सृजन र पितृत्व'],
        D10: ['दशमांश', 'करियर, पद र यश'],
        D12: ['द्वादशांश', 'माता-पिता, पूर्वज र मूल'],
        D16: ['षोडशांश', 'वाहन, सुख र भौतिक सुविधा'],
        D20: ['विंशांश', 'आध्यात्मिकता, उपासना र मन्त्र'],
        D24: ['चतुर्विंशांश', 'शिक्षा, विद्या र ज्ञान'],
        D27: ['सप्तविंशांश', 'बल, सहनशीलता र प्रतिरोध'],
        D30: ['त्रिंशांश', 'भाग्य, अशुभता र नैतिकता'],
        D40: ['चत्वारिंशांश', 'मातृ कुण्डली र मातृ सुख'],
        D45: ['पञ्चचत्वारिंशांश', 'पितृ कुण्डली र पितृ सुख'],
        D60: ['षष्ट्यंश', 'सूक्ष्म कर्म र पूर्वजन्म संस्कार']
      };
      Object.keys(LB).forEach(key => {
        const vd = vargas[key] || {};
        const vl = +((vd.lagna || {}).sign_number) || 0;
        const vp = vd.planets || [];
        if (!vl || !vp.length) return;
        const no = pages.length + 1, label = LB[key][0], title = key + ' — ' + label;
        const vh = kunHouses(vp, vl, 'varga');
        const moon = vp.find(p => p.name === 'Moon') || {};
        const sun = vp.find(p => p.name === 'Sun') || {};
        let chips = '';
        const chipData = [
          [key + ' लग्न', kunSignByNum(vl)],
          [key + ' चन्द्र', kunSignNe(moon)],
          [key + ' सूर्य', kunSignNe(sun)]
        ];
        const cw = 196, gap = 16, x0 = 360 - (chipData.length * cw + (chipData.length - 1) * gap) / 2;
        chipData.forEach((c, i) => chips += kunCard(x0 + i * (cw + gap), 894, cw, 108, c[0], c[1], '#e8b923', { fs: 19, chars: 10, lh: 25 }));
        pages.push(kbPage(no, title, label + ' · ' + LB[key][1], [
          kbHeader(no, title, label + ' · ' + LB[key][1]),
          kbChartEl(no, title, vh, vl, title + ' चार्ट', 60, 190, 600),
          kbEl(no, title, 'note', label + ' लग्न अंश', [46, 800, 628, 44], kunT(360, 820, label + ' लग्न: ' + kunSignByNum(vl) + ' · ' + kunDMS((vd.lagna || {}).longitude_in_sign || 0), 19, '#e9eefb', 700, 'middle'), 6.2),
          kbEl(no, title, 'note', label + ' फल क्षेत्र', [46, 842, 628, 36], kunT(360, 860, LB[key][1], 13, '#9fb0d0', 500, 'middle'), 5.6),
          kbEl(no, title, 'cards', label + ' लग्न · चन्द्र · सूर्य कार्ड', [46, 884, 628, 124], chips, 7.2),
          kbFooter(no, title)
        ]));
      });

      /* one summary table proves that all sixteen vargas are present */
      const no = pages.length + 1, title = 'षोडश वर्ग सारांश';
      const order = ['D1', 'D2', 'D3', 'D4', 'D7', 'D9', 'D10', 'D12', 'D16', 'D20', 'D24', 'D27', 'D30', 'D40', 'D45', 'D60'];
      const rows = order.map(key => {
        const vd = vargas[key] || {}, vp = vd.planets || [];
        const vl = +((vd.lagna || {}).sign_number) || 0;
        const moon = vp.find(p => p.name === 'Moon') || {};
        const sun = vp.find(p => p.name === 'Sun') || {};
        return [
          key,
          vl ? kunSignByNum(vl) : '—',
          moon.name ? kunSignNe(moon) : '—',
          sun.name ? kunSignNe(sun) : '—',
          vp.length ? neNum(vp.length) : '—'
        ];
      });
      pages.push(kbPage(no, title, 'सोह्र वर्गको लग्न, चन्द्र, सूर्य र ग्रह सङ्ख्या', [
        kbHeader(no, title, 'सोह्र वर्गको लग्न, चन्द्र, सूर्य र ग्रह सङ्ख्या'),
        kbTableEl(no, title, 'षोडश वर्ग तालिका', 46, 184, 628, [
          { t: 'वर्ग', w: 78 }, { t: 'लग्न', w: 128 }, { t: 'चन्द्र राशि', w: 138 }, { t: 'सूर्य राशि', w: 138 }, { t: 'ग्रह', w: 76 }
        ], rows, { rowH: 52, headH: 50, fs: 15, hfs: 13 }, 9),
        kbEl(no, title, 'note', 'षोडश वर्ग नोट', [46, 1074, 628, 40], kunT(46, 1092, 'D1 = राशि, D9 = नवमांश; सबै सोह्र वर्ग Kundali-Desktop बाट गणना गरिएका वास्तविक चार्ट हुन्।', 12, '#7183a8', 500), 6.2),
        kbFooter(no, title)
      ]));
    }

    /* ── bhava chalit — cusp based house shift ── */
    {
      const no = pages.length + 1, title = 'भाव चलित कुण्डली';
      const placements = houses.placements || {};
      const names = KUN_ORDER.filter(n => placements[n] != null);
      if (names.length) {
        const bh = {};
        for (let h = 1; h <= 12; h++) bh[h] = [];
        names.forEach(n => {
          const h = +placements[n];
          if (h >= 1 && h <= 12) bh[h].push(kbAb(n));
        });
        const rows = names.map(n => {
          const p = planets.find(x => x.name === n) || {};
          const ph = +placements[n], rh = +p.house || 0;
          return [KUN_NE[n], kunSignNe(p), kbN(rh), kbN(ph), ph === rh ? 'समान भाव' : 'भाव परिवर्तन'];
        });
        pages.push(kbPage(no, title, 'Cusp आधारित भाव स्थिति · भाव चलित', [
          kbHeader(no, title, 'Cusp आधारित भाव स्थिति · भाव चलित'),
          kbEl(no, title, 'chart', 'भाव चलित चार्ट', [110, 184, 500, 500], kunChart(bh, lagnaSign, 110, 184, 500), 8.4),
          kbEl(no, title, 'note', 'भाव चलित व्याख्या', [46, 690, 628, 38], kunT(46, 708, 'राशि भाव = whole-sign D1; भाव चलित = वास्तविक cusp भाव। भाव परिवर्तन भएका ग्रह तालिकामा देखिन्छ।', 12, '#9fb0d0', 500), 6.2),
          kbTableEl(no, title, 'भाव चलित तालिका', 46, 738, 628, [
            { t: 'ग्रह', w: 92 }, { t: 'राशि', w: 112 }, { t: 'राशि भाव', w: 92 }, { t: 'भाव चलित', w: 100 }, { t: 'भेद', w: 232 }
          ], rows, { rowH: 40, headH: 44, fs: 13, hfs: 12 }, 8.6),
          kbEl(no, title, 'note', 'भाव चलित नोट', [46, 1146, 628, 34], kunT(46, 1163, 'भाव चलित Kundali-Desktop को house placements बाट; कुनै गणना अनुमान गरिएको छैन।', 12, '#7183a8', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── house cusps ── */
    {
      const no = pages.length + 1, title = 'भाव कस्प तालिका';
      const cusps = houses.cusps || [];
      if (cusps.length) {
        const kmap = {};
        (kp.cusps || []).forEach(c => { if (c && c.house != null) kmap[+c.house] = c; });
        const rows = cusps.slice(0, 12).map((lon, i) => {
          const h = i + 1, kc = kmap[h] || {};
          return [
            neNum(h),
            kunSignByNum(kc.sign || kbSignOfLon(lon)),
            kunDMS(kbLonInSign(lon)),
            KUN_NE[kc.sign_lord] || kc.sign_lord || '—',
            KUN_NE[kc.star_lord] || kc.star_lord || '—',
            KUN_NE[kc.sub_lord] || kc.sub_lord || '—',
            KUN_NE[kc.sub_sub_lord] || kc.sub_sub_lord || '—'
          ];
        });
        pages.push(kbPage(no, title, (kp.house_system || houses.system || 'WHOLE_SIGN') + ' · १२ भाव कस्प', [
          kbHeader(no, title, (kp.house_system || houses.system || 'WHOLE_SIGN') + ' · १२ भाव कस्प'),
          kbTableEl(no, title, 'भाव कस्प तालिका', 46, 184, 628, [
            { t: 'भाव', w: 54 }, { t: 'राशि', w: 80 }, { t: 'अंश', w: 98 }, { t: 'राशि स्वामी', w: 100 }, { t: 'नक्षत्र स्वामी', w: 100 }, { t: 'सब स्वामी', w: 98 }, { t: 'सूक्ष्म स्वामी', w: 98 }
          ], rows, { rowH: 62, headH: 52, fs: 13, hfs: 11 }, 8.6),
          kbEl(no, title, 'note', 'कस्प नोट', [46, 996, 628, 40], kunT(46, 1014, 'कस्प देशान्तर घण्टामा; नक्षत्र/सब/सूक्ष्म स्वामी KP पद्धतिबाट।', 12, '#9fb0d0', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── special lagnas ── */
    {
      const no = pages.length + 1, title = 'विशेष लग्नहरू';
      const sl = data.special_lagnas || {};
      const defs = [
        ['Bhava', 'भाव लग्न', 'भा', 'भाव सम्बन्धी विशेष बिन्दु'],
        ['Hora', 'होरा लग्न', 'हो', 'धन र आर्थिक होरा बिन्दु'],
        ['Ghati', 'घटी लग्न', 'घ', 'समय-आधारित घटी बिन्दु'],
        ['Pranapada', 'प्राणपद लग्न', 'प्रा', 'प्राण र आयु बिन्दु']
      ].filter(d => sl[d[0]] != null);
      if (defs.length) {
        const pts = defs.map(d => {
          const lon = +sl[d[0]];
          return { key: d[0], ne: d[1], ab: d[2], meaning: d[3], lon: lon, sign: kbSignOfLon(lon), deg: kbLonInSign(lon) };
        });
        const rows = pts.map(p => [
          p.ne, kunSignByNum(p.sign), kunDMS(p.deg),
          kbN(((p.sign - lagnaSign) % 12 + 12) % 12 + 1), p.meaning
        ]);
        pages.push(kbPage(no, title, 'Special Lagnas · चार विशेष बिन्दु', [
          kbHeader(no, title, 'Special Lagnas · चार विशेष बिन्दु'),
          kbEl(no, title, 'chart', 'विशेष लग्न चार्ट', [130, 184, 460, 460], kunChart(kbPointHouses(pts, lagnaSign), lagnaSign, 130, 184, 460), 8.4),
          kbEl(no, title, 'note', 'विशेष लग्न व्याख्या', [46, 656, 628, 34], kunT(46, 674, 'विशेष लग्नहरू D1 लग्नको सन्दर्भमा राखिएका छन्; चार्टमा तिनको राशि-भाव देखिन्छ।', 12, '#9fb0d0', 500), 6.2),
          kbTableEl(no, title, 'विशेष लग्न तालिका', 46, 700, 628, [
            { t: 'विशेष लग्न', w: 142 }, { t: 'राशि', w: 92 }, { t: 'अंश', w: 110 }, { t: 'भाव', w: 56 }, { t: 'अर्थ', w: 228 }
          ], rows, { rowH: 64, headH: 50, fs: 13, hfs: 12 }, 7.6),
          kbEl(no, title, 'note', 'विशेष लग्न नोट', [46, 1014, 628, 36], kunT(46, 1032, 'भाव लग्न, होरा लग्न, घटी लग्न र प्राणपद — Kundali-Desktop को special_lagnas गणना।', 12, '#7183a8', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── upagrahas ── */
    {
      const no = pages.length + 1, title = 'उपग्रह स्थिति';
      const ug = data.upagrahas || {};
      const defs = [
        ['Kala', 'काल', 'का', 'शत्रु, रोग र मृत्यु संकेत'],
        ['Yamaghantaka', 'यमघण्टक', 'य', 'यम दण्ड, बाधा र कष्ट'],
        ['Gulika', 'गुलिक', 'गु', 'शनि पुत्र · कर्म र कष्ट'],
        ['Mandi', 'मान्दी', 'मा', 'नियति र मृत्यु संकेत']
      ].filter(d => ug[d[0]] != null);
      if (defs.length) {
        const pts = defs.map(d => {
          const lon = +ug[d[0]];
          return { key: d[0], ne: d[1], ab: d[2], meaning: d[3], lon: lon, sign: kbSignOfLon(lon), deg: kbLonInSign(lon) };
        });
        const rows = pts.map(p => [
          p.ne, kunSignByNum(p.sign), kunDMS(p.deg),
          kbN(((p.sign - lagnaSign) % 12 + 12) % 12 + 1), p.meaning
        ]);
        pages.push(kbPage(no, title, 'Upagrahas · काल, यमघण्टक, गुलिक र मान्दी', [
          kbHeader(no, title, 'Upagrahas · काल, यमघण्टक, गुलिक र मान्दी'),
          kbEl(no, title, 'chart', 'उपग्रह चार्ट', [130, 184, 460, 460], kunChart(kbPointHouses(pts, lagnaSign), lagnaSign, 130, 184, 460), 8.4),
          kbEl(no, title, 'note', 'उपग्रह व्याख्या', [46, 656, 628, 34], kunT(46, 674, 'उपग्रहहरू सूर्योदय-आधारित विशेष काल बिन्दु हुन्; D1 लग्नको सन्दर्भमा भाव देखाइएको छ।', 12, '#9fb0d0', 500), 6.2),
          kbTableEl(no, title, 'उपग्रह तालिका', 46, 700, 628, [
            { t: 'उपग्रह', w: 142 }, { t: 'राशि', w: 92 }, { t: 'अंश', w: 110 }, { t: 'भाव', w: 56 }, { t: 'अर्थ', w: 228 }
          ], rows, { rowH: 64, headH: 50, fs: 13, hfs: 12 }, 7.6),
          kbEl(no, title, 'note', 'उपग्रह नोट', [46, 1014, 628, 36], kunT(46, 1032, 'काल, यमघण्टक, गुलिक र मान्दी — Kundali-Desktop को upagrahas गणना।', 12, '#7183a8', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── avakahada chakra ── */
    {
      const no = pages.length + 1, title = 'अवकहडा चक्र';
      const av = data.avakahada_chakra || {};
      if (av.nakshatra || av.rashi) {
        const cw = 196, gap = 16, x0 = 360 - (3 * cw + 2 * gap) / 2;
        let chips = '';
        chips += kunCard(x0, 176, cw, 118, 'जन्म नक्षत्र', (av.nakshatra || '—') + ' · पद ' + kbN(av.pada), '#e8b923', { fs: 19, chars: 12, lh: 25 });
        chips += kunCard(x0 + cw + gap, 176, cw, 118, 'नाम अक्षर', av.name_akshara || '—', '#34d399', { fs: 28, chars: 6, lh: 30 });
        chips += kunCard(x0 + 2 * (cw + gap), 176, cw, 118, 'राशि · स्वामी', (av.rashi || '—') + ' · ' + (av.rashi_lord || '—'), '#e8b923', { fs: 19, chars: 12, lh: 25 });
        const pairs = [
          ['नक्षत्र', av.nakshatra || '—', 'पद', kbN(av.pada)],
          ['नाम अक्षर', av.name_akshara || '—', 'राशि', av.rashi || '—'],
          ['राशि स्वामी', av.rashi_lord || '—', 'वर्ण', av.varna || '—'],
          ['वश्य', av.vashya || '—', 'योनि', av.yoni || '—'],
          ['विर्योनि', av.viryoni || '—', 'गण', av.gana || '—'],
          ['नाडी', av.nadi || '—', 'आसन', av.asana || '—'],
          ['वर्ग', av.varga || '—', 'शत्रु वर्ग', av.shatru_varga || '—'],
          ['नक्षत्र समाप्ति', kunTime(av.nakshatra_end_time), 'सन्दर्भ', av.nakshatra_reference === 'birth_time' ? 'जन्म समय' : (av.nakshatra_reference || '—')]
        ];
        pages.push(kbPage(no, title, 'नक्षत्र, राशि, वर्ण, योनि, गण, नाडी र वर्ग', [
          kbHeader(no, title, 'नक्षत्र, राशि, वर्ण, योनि, गण, नाडी र वर्ग'),
          kbEl(no, title, 'cards', 'अवकहडा मुख्य कार्डहरू', [46, 176, 628, 124], chips, 7),
          kbTableEl(no, title, 'अवकहडा तालिका', 46, 318, 628, [
            { t: 'विवरण', w: 128 }, { t: 'मान', w: 186 }, { t: 'विवरण', w: 128 }, { t: 'मान', w: 186 }
          ], pairs, { rowH: 62, headH: 50, fs: 14, hfs: 12 }, 8.6),
          kbEl(no, title, 'note', 'अवकहडा नोट', [46, 862, 628, 38], kunT(46, 880, 'अवकहडा चक्र — विवाह, गुण मिलान, नामकरण र जन्म-आधारित परम्परागत विवरण।', 12, '#9fb0d0', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── detailed panchang ── */
    {
      const no = pages.length + 1, title = 'पञ्चाङ्ग विस्तृत';
      const pc = panchang;
      if (pc.tithi) {
        const tm = v => v ? neNum(v) : '—';
        const t = pc.tithi || {}, n = pc.nakshatra || {}, y = pc.yoga || {}, k = pc.karana || {};
        const lm = pc.lunar_month || {}, ns = pc.nepal_samvat || {}, bd = pc.bhadra || {};
        const rows = [
          ['तिथि', (t.birth_nepali || t.nepali || '—') + ' · ' + (t.paksha_nepali || ''), tm(t.end_time), t.next_nepali || '—'],
          ['नक्षत्र', (n.nepali || '—') + ' · पद ' + kbN(n.pada), tm(n.end_time), n.next_nepali || '—'],
          ['योग', (y.birth_nepali || y.nepali || '—'), tm(y.end_time), y.next_nepali || '—'],
          ['करण', (k.birth_nepali || k.nepali || '—'), tm(k.end_time), k.next_nepali || '—'],
          ['वार', (pc.vara || {}).nepali || '—', '—', '—'],
          ['चन्द्र राशि', (pc.chandra_rashi || {}).nepali || '—', '—', '—'],
          ['आनन्दादि योग', (pc.anandadi_yoga || {}).nepali || '—', '—', '—'],
          ['भद्रा', bd.nepali || '—', tm(bd.start_time), tm(bd.end_time)],
          ['सम्वत्सर', pc.samvatsara || '—', '—', '—'],
          ['नेपाल संवत', ns.year ? neNum(ns.year) + ' ' + (ns.era || '') : '—', '—', '—'],
          ['चान्द्र मास', (lm.nepali || '—') + ' (' + (lm.type_nepali || pc.month_type_nepali || '—') + ')', '—', '—'],
          ['दिनमान', neNum(pc.dinman || pc.day_duration || '—'), '—', '—']
        ];
        let chips = '';
        chips += kunCard(46, 900, 196, 108, 'सूर्योदय', (pc.sunrise || {}).time ? neNum((pc.sunrise || {}).time) : '—', '#f6d365', { fs: 25, chars: 8 });
        chips += kunCard(262, 900, 196, 108, 'सूर्यास्त', (pc.sunset || {}).time ? neNum((pc.sunset || {}).time) : '—', '#fb7185', { fs: 25, chars: 8 });
        chips += kunCard(478, 900, 196, 108, 'दिनमान', neNum(pc.dinman || pc.day_duration || '—'), '#34d399', { fs: 25, chars: 8 });
        pages.push(kbPage(no, title, 'तिथि, नक्षत्र, योग, करण, भद्रा, संवत र सूर्योदय', [
          kbHeader(no, title, 'तिथि, नक्षत्र, योग, करण, भद्रा, संवत र सूर्योदय'),
          kbTableEl(no, title, 'पञ्चाङ्ग विस्तृत तालिका', 46, 184, 628, [
            { t: 'पञ्चाङ्ग अङ्ग', w: 124 }, { t: 'मान', w: 258 }, { t: 'समाप्ति', w: 106 }, { t: 'अर्को', w: 140 }
          ], rows, { rowH: 54, headH: 50, fs: 14, hfs: 12 }, 9),
          kbEl(no, title, 'cards', 'सूर्योदय · सूर्यास्त · दिनमान कार्ड', [46, 900, 628, 116], chips, 7),
          kbEl(no, title, 'note', 'पञ्चाङ्ग सन्दर्भ', [46, 1032, 628, 54], kunPara(46, 1050, (data.panchang_context || {}).description_ne || 'यो पञ्चाङ्ग जन्म समयको आधारमा गणना गरिएको छ।', 76, 12, 17, '#9fb0d0', 2), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── panchang planetary positions ── */
    {
      const no = pages.length + 1, title = 'पञ्चाङ्ग ग्रह गणना';
      const pp = panchang.planetary_positions || {};
      if (Object.keys(pp).length) {
        const rows = KUN_ORDER.filter(n => pp[n]).map(n => {
          const p = pp[n];
          return [KUN_NE[n], p.rashi_nepali || '—', kunDMS(p.longitude == null ? null : (+p.longitude % 30)), kbN((+p.rashi_index || 0) + 1), p.formatted_en || '—'];
        });
        let chips = '';
        chips += kunCard(46, 780, 196, 110, 'सूर्य क्रान्ति', kunNum(panchang.sun_declination, 2) + '°', '#f6d365', { fs: 24, chars: 8 });
        chips += kunCard(262, 780, 196, 110, 'समीकरण (मिनेट)', kunNum(panchang.equation_of_time_min, 2), '#34d399', { fs: 24, chars: 8 });
        chips += kunCard(478, 780, 196, 110, 'गणना मोड', panchang.calculation_mode || 'DRIK', '#9fb0d0', { fs: 24, chars: 8 });
        pages.push(kbPage(no, title, 'पञ्चाङ्ग ग्रह स्थिति र सूर्य गणना', [
          kbHeader(no, title, 'पञ्चाङ्ग ग्रह स्थिति र सूर्य गणना'),
          kbTableEl(no, title, 'पञ्चाङ्ग ग्रह तालिका', 46, 184, 628, [
            { t: 'ग्रह', w: 88 }, { t: 'राशि', w: 100 }, { t: 'अंश', w: 142 }, { t: 'राशि क्रम', w: 88 }, { t: 'गणना रेखा', w: 210 }
          ], rows, { rowH: 58, headH: 52, fs: 14, hfs: 12 }, 8.6),
          kbEl(no, title, 'cards', 'सूर्य गणना कार्डहरू', [46, 780, 628, 118], chips, 7),
          kbEl(no, title, 'note', 'पञ्चाङ्ग ग्रह नोट', [46, 912, 628, 54], kunPara(46, 930, 'पञ्चाङ्ग ग्रह स्थिति जन्म समयकै दृक् (DRIK) गणना हो; राशि क्रम १ = मेष।', 76, 12, 17, '#9fb0d0', 2), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── bhinnashtakavarga per planet ── */
    {
      const no = pages.length + 1, title = 'भिन्नाष्टकवर्ग (BAV)';
      const av = data.ashtakavarga || {};
      const bav = av.bhinnashtakavarga || {};
      const names = KUN_ORDER.slice(0, 7).filter(n => Array.isArray(bav[n]));
      if (names.length) {
        const rows = [];
        for (let s = 0; s < 12; s++) {
          const row = [kunSignByNum(s + 1)];
          names.forEach(n => row.push(kbN(bav[n][s])));
          row.push(kbN((av.sav || [])[s]));
          rows.push(row);
        }
        const total = ['कुल'];
        names.forEach(n => total.push(kbN((av.totals_by_planet || {})[n])));
        total.push(kbN(av.total_bindus));
        rows.push(total);
        const cols = [{ t: 'राशि', w: 82 }].concat(names.map(n => ({ t: KUN_AB[n], w: 62 }))).concat([{ t: 'SAV', w: 74 }]);
        pages.push(kbPage(no, title, 'प्रत्येक ग्रहको भिन्नाष्टकवर्ग बिन्दु र SAV', [
          kbHeader(no, title, 'प्रत्येक ग्रहको भिन्नाष्टकवर्ग बिन्दु र SAV'),
          kbTableEl(no, title, 'BAV म्याट्रिक्स', 46, 184, 628, cols, rows, {
            rowH: 56, headH: 54, fs: 14, hfs: 11,
            rowFill: ri => ri === rows.length - 1 ? '#1b2743' : (ri % 2 ? '#0f172b' : '#121d35'),
            cellColor: (ri, ci, v) => {
              if (ri === rows.length - 1) return '#f6d365';
              if (ci === 0) return null;
              const num = kbParse(v);
              if (!isFinite(num)) return null;
              if (ci === cols.length - 1) return num >= 30 ? '#34d399' : num <= 25 ? '#fb7185' : null;
              return num >= 6 ? '#34d399' : num <= 2 ? '#fb7185' : null;
            }
          }, 9),
          kbEl(no, title, 'note', 'BAV नोट', [46, 980, 628, 50], kunT(46, 998, 'भिन्नाष्टकवर्ग = प्रत्येक ग्रहको १२ राशिमा बिन्दु; अन्तिम पङ्क्ति कुल र SAV। शास्त्रीय कुल बिन्दु ' + kbN(av.classical_total_bindus) + '।', 12, '#9fb0d0', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── yogini dasha ── */
    {
      const list = data.yogini_dasha || [];
      if (list.length) {
        const today = new Date().toISOString().slice(0, 10);
        for (let part = 0; part < list.length; part += 12) {
          const chunk = list.slice(part, part + 12);
          const no = pages.length + 1, title = 'योगिनी दशा (भाग ' + neNum(Math.floor(part / 12) + 1) + ')';
          const rows = chunk.map(y => [
            y.nepali || y.name || '—',
            KUN_NE[y.lord] || kbLord(y.lord),
            kbN(y.total_years),
            kunDateNe(y.start),
            kunDateNe(y.end)
          ]);
          const activeIdx = chunk.findIndex(y => y.start <= today && y.end >= today);
          pages.push(kbPage(no, title, '२४ योगिनीको क्रम र BS मिति', [
            kbHeader(no, title, '२४ योगिनीको क्रम र BS मिति'),
            kbTableEl(no, title, 'योगिनी दशा तालिका', 46, 184, 628, [
              { t: 'योगिनी', w: 150 }, { t: 'स्वामी', w: 100 }, { t: 'वर्ष', w: 70 }, { t: 'सुरु (BS)', w: 154 }, { t: 'अन्त्य (BS)', w: 154 }
            ], rows, {
              rowH: 64, headH: 52, fs: 14, hfs: 12,
              rowFill: ri => ri === activeIdx ? '#143024' : (ri % 2 ? '#0f172b' : '#121d35'),
              cellColor: (ri, ci, v) => ri === activeIdx ? '#34d399' : null
            }, 9),
            kbEl(no, title, 'note', 'योगिनी दशा नोट', [46, 1018, 628, 44], kunT(46, 1036, 'योगिनी दशा — मङ्गला, पिङ्गला, धन्या, भ्रामरी, भद्रिका, शङ्खटा, सङ्कटा आदि २४ योगिनी क्रम। हरियो पङ्क्ति वर्तमान।', 12, '#9fb0d0', 500), 6.2),
            kbFooter(no, title)
          ]));
        }
      }
    }

    /* ── ashtottari dasha ── */
    {
      const list = data.ashtottari_dasha || [];
      const no = pages.length + 1, title = 'अष्टोत्तरी दशा';
      if (list.length) {
        const rows = list.map(d => [
          d.lord_nepali || KUN_NE[d.lord] || d.lord || '—',
          kbN(d.total_years),
          d.start_bs_available ? kunBsShort(d.start_bs) : kunDateNe(d.start),
          d.end_bs_available ? kunBsShort(d.end_bs) : kunDateNe(d.end),
          d.is_partial ? 'आंशिक' : 'पूर्ण'
        ]);
        const activeIdx = list.findIndex(d => d.is_active);
        const active = activeIdx >= 0 ? list[activeIdx] : null;
        let card = '';
        if (active) {
          card = '<rect x="46" y="826" width="628" height="92" rx="14" fill="#143024" stroke="#34d399" stroke-width="1.5"/>';
          card += kunT(70, 854, 'सक्रिय अष्टोत्तरी दशा', 12, '#9fb0d0', 600);
          card += kunT(70, 886, (active.lord_nepali || KUN_NE[active.lord] || active.lord) + ' · ' + kunBsShort(active.start_bs) + ' — ' + kunBsShort(active.end_bs), 19, '#34d399', 700);
        } else {
          card = '<rect x="46" y="826" width="628" height="92" rx="14" fill="#121d35" stroke="#2b3856" stroke-width="1.5"/>';
          card += kunT(70, 856, 'यो जन्मको अष्टोत्तरी दशा क्रम', 12, '#9fb0d0', 600);
          card += kunT(70, 886, 'जन्म समयको दशा-सन्तुलन अनुसार पहिलो दशा आंशिक हुन सक्छ।', 14, '#e9eefb', 600);
        }
        pages.push(kbPage(no, title, 'Ashtottari Dasha · १०८ वर्षको चक्र', [
          kbHeader(no, title, 'Ashtottari Dasha · १०८ वर्षको चक्र'),
          kbTableEl(no, title, 'अष्टोत्तरी दशा तालिका', 46, 184, 628, [
            { t: 'दशा स्वामी', w: 136 }, { t: 'वर्ष', w: 64 }, { t: 'सुरु (BS)', w: 156 }, { t: 'अन्त्य (BS)', w: 156 }, { t: 'स्थिति', w: 116 }
          ], rows, {
            rowH: 68, headH: 52, fs: 14, hfs: 12,
            rowFill: ri => ri === activeIdx ? '#143024' : (ri % 2 ? '#0f172b' : '#121d35'),
            cellColor: (ri, ci, v) => ri === activeIdx ? '#34d399' : null
          }, 9),
          kbEl(no, title, 'banner', 'सक्रिय अष्टोत्तरी दशा ब्यानर', [46, 826, 628, 92], card, 7),
          kbEl(no, title, 'note', 'अष्टोत्तरी नोट', [46, 934, 628, 44], kunT(46, 952, 'अष्टोत्तरी दशा — ८ ग्रहको १०८ वर्षे चक्र; BS मिति Kundali-Desktop बाट।', 12, '#9fb0d0', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── varshaphala ── */
    {
      const v = data.varshaphala || {};
      const pos = v.positions || {};
      if (v.solar_return_jd != null && Object.keys(pos).length) {
        const no = pages.length + 1, title = 'वर्षफल — वार्षिक कुण्डली';
        const iso = kbJdIso(v.solar_return_jd), bsDate = kunDateNe(iso), bsYear = kbIsoBsYear(iso);
        const bala = v.panchavargiya_bala || {};
        const balaRank = Object.keys(bala).sort((a, b) => (+bala[b] || 0) - (+bala[a] || 0));
        const pNames = KUN_ORDER.slice(0, 7).filter(n => pos[n] != null);
        const rows = pNames.map(n => [
          KUN_NE[n],
          kunSignByNum(kbSignOfLon(pos[n])),
          kunDMS(kbLonInSign(pos[n])),
          kunNum(bala[n], 2),
          kbN(balaRank.indexOf(n) + 1)
        ]);
        let chips = '';
        chips += kunCard(46, 176, 148, 112, 'वर्ष (BS)', bsYear ? neNum(bsYear) : '—', '#e8b923', { fs: 24, chars: 8 });
        chips += kunCard(206, 176, 148, 112, 'सौर प्रवेश (BS)', bsDate, '#f6d365', { fs: 16, chars: 11, lh: 22 });
        chips += kunCard(366, 176, 148, 112, 'मुन्था', kunSignByNum(kbSignOfLon(v.muntha)) + ' · भाव ' + kbN(v.muntha_house), '#34d399', { fs: 16, chars: 11, lh: 22 });
        chips += kunCard(526, 176, 148, 112, 'वर्षेश', (KUN_NE[v.varsheshwara] || v.varsheshwara || '—') + ' · ' + (v.muntha_auspicious ? 'शुभ' : 'अशुभ'), '#9fb0d0', { fs: 18, chars: 11, lh: 23 });
        pages.push(kbPage(no, title, 'सौर वर्ष प्रवेश · मुन्था · वर्षेश · ग्रह स्थिति', [
          kbHeader(no, title, 'सौर वर्ष प्रवेश · मुन्था · वर्षेश · ग्रह स्थिति'),
          kbEl(no, title, 'cards', 'वर्षफल मुख्य कार्डहरू', [46, 176, 628, 118], chips, 7.2),
          kbTableEl(no, title, 'वार्षिक ग्रह स्थिति तालिका', 46, 312, 628, [
            { t: 'ग्रह', w: 92 }, { t: 'राशि', w: 100 }, { t: 'अंश', w: 136 }, { t: 'पञ्चवर्गीय बल', w: 142 }, { t: 'क्रम', w: 76 }
          ], rows, { rowH: 58, headH: 52, fs: 15, hfs: 12 }, 8.6),
          kbEl(no, title, 'note', 'वर्षफल नोट', [46, 782, 628, 54], kunPara(46, 800, 'वर्षफल वार्षिक सौर प्रवेश (सूर्यको जन्म-अंशमा फिर्ती) बाट; मुन्था ' + kunSignByNum(kbSignOfLon(v.muntha)) + ' राशिमा, भाव ' + kbN(v.muntha_house) + ', वर्षेश ' + (KUN_NE[v.varsheshwara] || v.varsheshwara || '—') + '।', 76, 12.5, 18, '#9fb0d0', 2), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── varshaphala tajika yogas ── */
    {
      const v = data.varshaphala || {}, list = v.tajika_yogas || [];
      if (list.length) {
        for (let part = 0; part < list.length; part += 6) {
          const chunk = list.slice(part, part + 6);
          const no = pages.length + 1, title = 'वर्षफल ताजिक योग (भाग ' + neNum(Math.floor(part / 6) + 1) + ')';
          const natNe = s => /Favorable/i.test(s) ? 'अनुकूल'
            : /Neutral/i.test(s) ? 'तटस्थ / बलियो'
            : /Inimical/i.test(s) ? 'प्रतिकूल / बाधा'
            : /Auspicious/i.test(s) ? 'मध्यस्थबाट शुभ' : (s || '—');
          const aspNe = s => {
            const t = String(s || '—');
            if (t.indexOf('Conjunction') === 0) return 'युति (सम्बन्ध)';
            if (t.indexOf('Sextile') === 0) return 'षष्ठक (३/११)';
            if (t.indexOf('Square') === 0) return 'चतुर्थक (४/१०)';
            if (t.indexOf('Transfer of Light') === 0) return 'चन्द्रबाट प्रकाश हस्तान्तरण';
            return t;
          };
          const rows = chunk.map(y => [
            (y.nepali_name || y.name || '—').split(' (')[0],
            (y.planets || []).map(p => KUN_AB[p] || p).join(' · '),
            aspNe(y.aspect),
            natNe(y.nature),
            y.orb != null ? kunNum(y.orb, 2) : '—'
          ]);
          pages.push(kbPage(no, title, 'ताजिक योग, दृष्टि, प्रकृति र अर्ब', [
            kbHeader(no, title, 'ताजिक योग, दृष्टि, प्रकृति र अर्ब'),
            kbTableEl(no, title, 'ताजिक योग तालिका', 46, 184, 628, [
              { t: 'योग', w: 118 }, { t: 'ग्रह', w: 94 }, { t: 'दृष्टि', w: 216 }, { t: 'प्रकृति', w: 124 }, { t: 'अर्ब', w: 76 }
            ], rows, { rowH: 62, headH: 52, fs: 12.5, hfs: 11 }, 8.6),
            kbEl(no, title, 'note', 'ताजिक नोट', [46, 650, 628, 44], kunT(46, 668, 'ताजिक योगहरू वार्षिक कुण्डलीका ग्रह दृष्टि र अर्बबाट; वास्तविक वर्षफल गणना।', 12, '#9fb0d0', 500), 6.2),
            kbFooter(no, title)
          ]));
        }
      }
    }

    /* ── varshaphala sahams ── */
    {
      const v = data.varshaphala || {}, sahams = v.all_sahams || v.sahams || {};
      const keys = Object.keys(sahams);
      const no = pages.length + 1, title = 'वर्षफल सहाम';
      if (keys.length) {
        const mSign = kbSignOfLon(v.muntha);
        const rows = keys.map(k => {
          const lon = +sahams[k];
          return [k, kunSignByNum(kbSignOfLon(lon)), kunDMS(kbLonInSign(lon)), kbN(((kbSignOfLon(lon) - mSign) % 12 + 12) % 12 + 1)];
        });
        pages.push(kbPage(no, title, 'सहाम बिन्दु · मुन्थाबाट भाव', [
          kbHeader(no, title, 'सहाम बिन्दु · मुन्थाबाट भाव'),
          kbTableEl(no, title, 'सहाम तालिका', 46, 184, 628, [
            { t: 'सहाम', w: 190 }, { t: 'राशि', w: 128 }, { t: 'अंश', w: 160 }, { t: 'मुन्थाबाट भाव', w: 150 }
          ], rows, { rowH: 64, headH: 54, fs: 15, hfs: 12 }, 8.6),
          kbEl(no, title, 'note', 'सहाम नोट', [46, 760, 628, 54], kunPara(46, 778, 'सहाम (Saham) वार्षिक फलका विशेष संवेदनशील बिन्दु हुन्; यहाँ मुन्था राशिबाट भाव देखाइएको छ।', 76, 12.5, 18, '#9fb0d0', 2), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── varshaphala mudda dasha ── */
    {
      const v = data.varshaphala || {}, list = v.mudda_dasha || [];
      const no = pages.length + 1, title = 'वर्षफल मुद्दा दशा';
      if (list.length) {
        const rows = list.slice(0, 12).map(d => [
          KUN_NE[d.lord] || d.lord || '—',
          kbJdNe(d.start_jd),
          kbJdNe(d.end_jd),
          kunNum(d.duration_days, 1)
        ]);
        pages.push(kbPage(no, title, 'वार्षिक मुद्दा दशा · BS मिति', [
          kbHeader(no, title, 'वार्षिक मुद्दा दशा · BS मिति'),
          kbTableEl(no, title, 'मुद्दा दशा तालिका', 46, 184, 628, [
            { t: 'स्वामी', w: 110 }, { t: 'सुरु (BS)', w: 214 }, { t: 'अन्त्य (BS)', w: 214 }, { t: 'दिन', w: 90 }
          ], rows, { rowH: 58, headH: 52, fs: 14, hfs: 12 }, 8.6),
          kbEl(no, title, 'note', 'मुद्दा दशा नोट', [46, 932, 628, 44], kunT(46, 950, 'मुद्दा दशा वर्षफलको वार्षिक दशा क्रम हो; मिति सौर वर्ष प्रवेशको JD बाट BS मा रूपान्तरण।', 12, '#9fb0d0', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── jaimini chara karakas ── */
    {
      const jk = data.jaimini || {}, ck = jk.chara_karakas || {};
      const defs = [
        ['Atmakaraka', 'आत्मकारक'], ['Amatyakaraka', 'अमात्यकारक'], ['Bhratrikaraka', 'भ्रातृकारक'],
        ['Matrikaraka', 'मातृकारक'], ['Putrakaraka', 'पुत्रकारक'], ['Gnatikaraka', 'ज्ञातिकारक'], ['Darakaraka', 'दारकारक']
      ];
      const no = pages.length + 1, title = 'जैमिनी चर कारक';
      if (Object.keys(ck).length) {
        const rows = defs.filter(d => ck[d[0]]).map(d => {
          const name = ck[d[0]], p = planets.find(x => x.name === name) || {};
          return [d[1], KUN_NE[name] || name, kunSignNe(p), kbN(p.house)];
        });
        const km = jk.karakamsha || {};
        const ar = jk.arudhas || {};
        let chips = '';
        chips += kunCard(46, 704, 196, 108, 'कारकम्श राशि', kunSignByNum(km.karakamsha_sign || 0), '#e8b923', { fs: 24, chars: 10 });
        chips += kunCard(262, 704, 196, 108, 'अरूढ लग्न', kunSignByNum(ar.Arudha_Lagna || 0), '#34d399', { fs: 24, chars: 10 });
        chips += kunCard(478, 704, 196, 108, 'उपपद', kunSignByNum(ar.Upapada || 0), '#9fb0d0', { fs: 24, chars: 10 });
        pages.push(kbPage(no, title, 'आत्मकारकदेखि दारकारकसम्म · योगकारक योजना', [
          kbHeader(no, title, 'आत्मकारकदेखि दारकारकसम्म · योगकारक योजना'),
          kbTableEl(no, title, 'चर कारक तालिका', 46, 184, 628, [
            { t: 'कारक', w: 180 }, { t: 'ग्रह', w: 160 }, { t: 'राशि', w: 160 }, { t: 'भाव', w: 128 }
          ], rows, { rowH: 64, headH: 52, fs: 16, hfs: 13 }, 8.6),
          kbEl(no, title, 'cards', 'कारकम्श · अरूढ लग्न · उपपद कार्ड', [46, 704, 628, 116], chips, 7),
          kbEl(no, title, 'note', 'चर कारक नोट', [46, 832, 628, 44], kunT(46, 850, 'कारक योजना: ' + kbN(jk.karaka_scheme) + ' ग्रह · आत्मकारक ' + (KUN_NE[km.atmakaraka] || km.atmakaraka || '—') + '।', 12, '#9fb0d0', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── jaimini arudha chakra ── */
    {
      const jk = data.jaimini || {}, ar = jk.arudhas || {};
      const no = pages.length + 1, title = 'जैमिनी अरूढ चक्र';
      const keys = ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12'].filter(k => ar[k] != null);
      if (keys.length) {
        const meaning = { A1: 'अरूढ लग्न', A2: 'धन', A3: 'भ्रातृ', A4: 'मातृ', A5: 'पुत्र', A6: 'शत्रु/रोग', A7: 'दारा', A8: 'मृत्यु', A9: 'भाग्य', A10: 'कर्म', A11: 'लाभ', A12: 'व्यय' };
        const rows = keys.map(k => {
          const sign = +ar[k] || 0;
          return [k, meaning[k] || '—', kunSignByNum(sign), KUN_NE[KUN_SIGN_LORD[(sign - 1 + 12) % 12]] || '—', kbN(((sign - lagnaSign) % 12 + 12) % 12 + 1)];
        });
        const km = jk.karakamsha || {};
        let chips = '';
        chips += kunCard(46, 176, 196, 108, 'अरूढ लग्न', kunSignByNum(ar.Arudha_Lagna || ar.A1 || 0), '#e8b923', { fs: 24, chars: 10 });
        chips += kunCard(262, 176, 196, 108, 'उपपद', kunSignByNum(ar.Upapada || ar.A12 || 0), '#34d399', { fs: 24, chars: 10 });
        chips += kunCard(478, 176, 196, 108, 'कारकम्श', kunSignByNum(km.karakamsha_sign || 0), '#9fb0d0', { fs: 24, chars: 10 });
        pages.push(kbPage(no, title, 'A1–A12 अरूढ, अरूढ लग्न, उपपद र कारकम्श', [
          kbHeader(no, title, 'A1–A12 अरूढ, अरूढ लग्न, उपपद र कारकम्श'),
          kbEl(no, title, 'cards', 'अरूढ मुख्य कार्डहरू', [46, 176, 628, 116], chips, 7),
          kbTableEl(no, title, 'अरूढ तालिका', 46, 318, 628, [
            { t: 'अरूढ', w: 78 }, { t: 'अर्थ', w: 146 }, { t: 'राशि', w: 118 }, { t: 'स्वामी', w: 116 }, { t: 'भाव', w: 72 }
          ], rows, { rowH: 56, headH: 52, fs: 14, hfs: 12 }, 8.6),
          kbEl(no, title, 'note', 'अरूढ नोट', [46, 1044, 628, 40], kunT(46, 1062, 'अरूढ पदहरू Jaimini पद्धतिबाट; भाव D1 लग्नको सन्दर्भमा।', 12, '#7183a8', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── jaimini chara dasha ── */
    {
      const jk = data.jaimini || {}, list = jk.chara_dasha || [];
      const no = pages.length + 1, title = 'जैमिनी चर दशा';
      if (list.length) {
        const rows = list.map(d => [
          kunSignByNum(d.sign),
          KUN_NE[d.lord] || d.lord || '—',
          kbN(d.duration_years),
          neNum(kbYearBs(d.start_year) || 0),
          neNum(kbYearBs(d.end_year) || 0)
        ]);
        pages.push(kbPage(no, title, 'राशि-आधारित चर दशा · BS वर्ष', [
          kbHeader(no, title, 'राशि-आधारित चर दशा · BS वर्ष'),
          kbTableEl(no, title, 'चर दशा तालिका', 46, 184, 628, [
            { t: 'राशि', w: 110 }, { t: 'स्वामी', w: 110 }, { t: 'वर्ष', w: 74 }, { t: 'सुरु (BS)', w: 166 }, { t: 'अन्त्य (BS)', w: 166 }
          ], rows, { rowH: 58, headH: 52, fs: 14, hfs: 12 }, 8.6),
          kbEl(no, title, 'note', 'चर दशा नोट', [46, 944, 628, 54], kunPara(46, 962, 'चर दशा वर्ष-आधारित हुन्छ; यहाँ AD वर्षको जनवरी १ बाट रूपान्तरित BS वर्ष देखाइएको छ।', 76, 12, 17, '#9fb0d0', 2), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── KP planets ── */
    {
      const sig = kp.significators || {}, pp = sig.planets || {};
      const no = pages.length + 1, title = 'KP ग्रह स्थिति';
      const names = KUN_ORDER.filter(n => pp[n]);
      if (names.length) {
        const rows = names.map(n => {
          const p = pp[n];
          return [KUN_NE[n], kunSignByNum(p.sign), kbN(p.house), KUN_NE[p.star_lord] || p.star_lord || '—', KUN_NE[p.sub_lord] || p.sub_lord || '—', KUN_NE[p.sub_sub_lord] || p.sub_sub_lord || '—'];
        });
        pages.push(kbPage(no, title, 'KP · नक्षत्र, स्टार, सब र सूक्ष्म स्वामी', [
          kbHeader(no, title, 'KP · नक्षत्र, स्टार, सब र सूक्ष्म स्वामी'),
          kbTableEl(no, title, 'KP ग्रह तालिका', 46, 184, 628, [
            { t: 'ग्रह', w: 84 }, { t: 'राशि', w: 86 }, { t: 'भाव', w: 60 }, { t: 'स्टार स्वामी', w: 128 }, { t: 'सब स्वामी', w: 128 }, { t: 'सूक्ष्म स्वामी', w: 134 }
          ], rows, { rowH: 62, headH: 54, fs: 14, hfs: 11 }, 8.6),
          kbEl(no, title, 'note', 'KP ग्रह नोट', [46, 796, 628, 44], kunT(46, 814, 'KP पद्धति — ग्रहको राशि, भाव, नक्षत्र (स्टार) स्वामी, सब स्वामी र सूक्ष्म स्वामी।', 12, '#9fb0d0', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── KP house significators ── */
    {
      const sig = kp.significators || {}, hh = sig.houses || {};
      const no = pages.length + 1, title = 'KP भाव सिग्निफिकेटर';
      const keys = Object.keys(hh).sort((a, b) => (+a || 0) - (+b || 0));
      if (keys.length) {
        const rows = keys.map(k => {
          const h = hh[k] || {};
          const occ = (h.occupants || []).map(n => KUN_AB[n] || n).join(' · ') || '—';
          const sg = (h.significators || []).map(n => KUN_AB[n] || n).join(' · ') || '—';
          const cs = h.cusp || {};
          return [neNum(k), KUN_NE[h.house_lord] || h.house_lord || '—', occ, sg, (KUN_NE[cs.sub_lord] || cs.sub_lord || '—')];
        });
        pages.push(kbPage(no, title, 'भावेश, स्थित ग्रह, सिग्निफिकेटर र कस्प सब', [
          kbHeader(no, title, 'भावेश, स्थित ग्रह, सिग्निफिकेटर र कस्प सब'),
          kbTableEl(no, title, 'KP भाव सिग्निफिकेटर तालिका', 46, 184, 628, [
            { t: 'भाव', w: 52 }, { t: 'भावेश', w: 84 }, { t: 'स्थित ग्रह', w: 128 }, { t: 'सिग्निफिकेटर', w: 254 }, { t: 'कस्प सब', w: 110 }
          ], rows, { rowH: 64, headH: 52, fs: 13, hfs: 11 }, 8.6),
          kbEl(no, title, 'note', 'KP सिग्निफिकेटर नोट', [46, 1006, 628, 44], kunT(46, 1024, 'KP भाव सिग्निफिकेटर — स्थित ग्रह, भावेश र सम्बन्धित ग्रहहरू; भाव फलको मुख्य आधार।', 12, '#9fb0d0', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── active dasha chain ── */
    {
      const list = data.dasha || [];
      const md = list.find(d => d.is_active);
      if (md) {
        const ad = (md.children || []).find(d => d.is_active);
        const pd = ad ? (ad.children || []).find(d => d.is_active) : null;
        const sd = pd ? (pd.children || []).find(d => d.is_active) : null;
        const chain = [['महादशा', md], ['अन्तर्दशा', ad], ['प्रत्यन्तर्दशा', pd], ['सूक्ष्मदशा', sd]].filter(x => x[1]);
        const no = pages.length + 1, title = 'सक्रिय दशा श्रृंखला';
        const rows = chain.map(c => [
          c[0],
          c[1].lord_nepali || KUN_NE[c[1].lord] || c[1].lord || '—',
          c[1].start_bs_available ? kunBsShort(c[1].start_bs) : kunDateNe(c[1].start),
          c[1].end_bs_available ? kunBsShort(c[1].end_bs) : kunDateNe(c[1].end),
          c[1].is_active ? 'सक्रिय' : '—'
        ]);
        let cards = '';
        chain.forEach((c, i) => {
          const x = 46 + i * 159;
          cards += '<rect x="' + x + '" y="620" width="147" height="112" rx="13" fill="#121d35" stroke="' + (c[1].is_active ? '#34d399' : '#2b3856') + '" stroke-width="1.5"/>';
          cards += kunT(x + 14, 644, c[0], 11, '#9fb0d0', 600);
          cards += kunT(x + 14, 676, c[1].lord_nepali || KUN_NE[c[1].lord] || c[1].lord || '—', 19, '#f6d365', 700);
          cards += kunT(x + 14, 704, c[1].start_bs_available ? kunBsShort(c[1].start_bs) : kunDateNe(c[1].start), 10, '#9fb0d0', 500);
          cards += kunT(x + 14, 718, c[1].end_bs_available ? kunBsShort(c[1].end_bs) : kunDateNe(c[1].end), 10, '#9fb0d0', 500);
        });
        pages.push(kbPage(no, title, 'महादशा → अन्तर्दशा → प्रत्यन्तर्दशा → सूक्ष्मदशा', [
          kbHeader(no, title, 'महादशा → अन्तर्दशा → प्रत्यन्तर्दशा → सूक्ष्मदशा'),
          kbTableEl(no, title, 'सक्रिय दशा तालिका', 46, 184, 628, [
            { t: 'स्तर', w: 130 }, { t: 'स्वामी', w: 120 }, { t: 'सुरु (BS)', w: 170 }, { t: 'अन्त्य (BS)', w: 170 }, { t: 'स्थिति', w: 70 }
          ], rows, {
            rowH: 84, headH: 54, fs: 14, hfs: 12,
            rowFill: ri => ri === chain.length - 1 ? '#143024' : (ri % 2 ? '#0f172b' : '#121d35')
          }, 8.6),
          kbEl(no, title, 'cards', 'सक्रिय दशा श्रृंखला कार्डहरू', [46, 620, 628, 124], cards, 7),
          kbEl(no, title, 'note', 'दशा श्रृंखला नोट', [46, 756, 628, 44], kunT(46, 774, 'सक्रिय महादशादेखि सूक्ष्मदशासम्मको श्रृंखला; सबै मिति BS मा।', 12, '#9fb0d0', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── pratyantardasha of the active antardasha ── */
    {
      const list = data.dasha || [];
      const md = list.find(d => d.is_active);
      const ad = md ? (md.children || []).find(d => d.is_active) : null;
      const kids = ad ? (ad.children || []) : [];
      const no = pages.length + 1, title = 'प्रत्यन्तर्दशा क्रम';
      if (kids.length) {
        const rows = kids.map(d => [
          d.lord_nepali || KUN_NE[d.lord] || d.lord || '—',
          d.start_bs_available ? kunBsShort(d.start_bs) : kunDateNe(d.start),
          d.end_bs_available ? kunBsShort(d.end_bs) : kunDateNe(d.end),
          kunNe(d.start), kunNe(d.end)
        ]);
        const activeIdx = kids.findIndex(d => d.is_active);
        pages.push(kbPage(no, title, 'सक्रिय अन्तर्दशाभित्र प्रत्यन्तर्दशा', [
          kbHeader(no, title, 'सक्रिय अन्तर्दशाभित्र प्रत्यन्तर्दशा'),
          kbTableEl(no, title, 'प्रत्यन्तर्दशा तालिका', 46, 184, 628, [
            { t: 'प्रत्यन्तर', w: 126 }, { t: 'सुरु (BS)', w: 154 }, { t: 'अन्त्य (BS)', w: 154 }, { t: 'सुरु (AD)', w: 97 }, { t: 'अन्त्य (AD)', w: 97 }
          ], rows, {
            rowH: 64, headH: 52, fs: 13, hfs: 11,
            rowFill: ri => ri === activeIdx ? '#143024' : (ri % 2 ? '#0f172b' : '#121d35'),
            cellColor: (ri, ci, v) => ri === activeIdx ? '#34d399' : null
          }, 9),
          kbEl(no, title, 'note', 'प्रत्यन्तर नोट', [46, 830, 628, 44], kunT(46, 848, 'सक्रिय अन्तर्दशाका प्रत्यन्तर्दशा; हरियो पङ्क्ति वर्तमान प्रत्यन्तर्दशा।', 12, '#9fb0d0', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── sookshma dasha of the active pratyantardasha ── */
    {
      const list = data.dasha || [];
      const md = list.find(d => d.is_active);
      const ad = md ? (md.children || []).find(d => d.is_active) : null;
      const pd = ad ? (ad.children || []).find(d => d.is_active) : null;
      const kids = pd ? (pd.children || []) : [];
      const no = pages.length + 1, title = 'सूक्ष्मदशा क्रम';
      if (kids.length) {
        const rows = kids.map(d => [
          d.lord_nepali || KUN_NE[d.lord] || d.lord || '—',
          d.start_bs_available ? kunBsShort(d.start_bs) : kunDateNe(d.start),
          d.end_bs_available ? kunBsShort(d.end_bs) : kunDateNe(d.end),
          kunNe(d.start), kunNe(d.end)
        ]);
        const activeIdx = kids.findIndex(d => d.is_active);
        pages.push(kbPage(no, title, 'सक्रिय प्रत्यन्तर्दशाभित्र सूक्ष्मदशा', [
          kbHeader(no, title, 'सक्रिय प्रत्यन्तर्दशाभित्र सूक्ष्मदशा'),
          kbTableEl(no, title, 'सूक्ष्मदशा तालिका', 46, 184, 628, [
            { t: 'सूक्ष्म', w: 126 }, { t: 'सुरु (BS)', w: 154 }, { t: 'अन्त्य (BS)', w: 154 }, { t: 'सुरु (AD)', w: 97 }, { t: 'अन्त्य (AD)', w: 97 }
          ], rows, {
            rowH: 64, headH: 52, fs: 13, hfs: 11,
            rowFill: ri => ri === activeIdx ? '#143024' : (ri % 2 ? '#0f172b' : '#121d35'),
            cellColor: (ri, ci, v) => ri === activeIdx ? '#34d399' : null
          }, 9),
          kbEl(no, title, 'note', 'सूक्ष्मदशा नोट', [46, 830, 628, 44], kunT(46, 848, 'सक्रिय प्रत्यन्तर्दशाका सूक्ष्मदशा; हरियो पङ्क्ति वर्तमान सूक्ष्मदशा।', 12, '#9fb0d0', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── forbidden gemstones ── */
    {
      const rem = data.remedies || {}, list = rem.forbidden_gemstones || [];
      if (list.length) {
        for (let part = 0; part < list.length; part += 4) {
          const chunk = list.slice(part, part + 4);
          const no = pages.length + 1, title = 'निषिद्ध रत्न' + (list.length > 4 ? ' (भाग ' + neNum(Math.floor(part / 4) + 1) + ')' : ' र सावधानी');
          let cards = '';
          chunk.forEach((g, i) => {
            const yy = 184 + i * 148;
            cards += '<rect x="46" y="' + yy + '" width="628" height="136" rx="15" fill="#2a1720" stroke="#7f1d2d" stroke-width="1.5"/>';
            cards += '<rect x="46" y="' + yy + '" width="6" height="136" rx="3" fill="#fb7185"/>';
            cards += kunT(70, yy + 26, (KUN_NE[g.planet] || g.planet || '—'), 12, '#fb7185', 700);
            cards += kunT(70, yy + 56, g.gemstone || '—', 21, '#f6d365', 700);
            cards += kunPara(70, yy + 84, g.reason || '—', 70, 12.5, 18, '#e9eefb', 3);
          });
          pages.push(kbPage(no, title, 'धारण नगर्नुहोस् — Kundali-Desktop को चेतावनी', [
            kbHeader(no, title, 'धारण नगर्नुहोस् — Kundali-Desktop को चेतावनी'),
            kbEl(no, title, 'report', 'निषिद्ध रत्न कार्डहरू', [46, 184, 628, chunk.length * 148 - 12], cards, 7.6),
            kbEl(no, title, 'note', 'निषिद्ध रत्न नोट', [46, 790, 628, 44], kunT(46, 808, 'विरोधाभास वा त्रिक भावेश भएका ग्रहका रत्न विशेष परामर्श बिना नलगाउनुहोस्।', 12, '#9fb0d0', 500), 6.2),
            kbFooter(no, title)
          ]));
        }
      }
    }

    /* ── gemstone safety guidelines ── */
    {
      const rem = data.remedies || {}, warns = rem.conflict_warnings || [], gl = rem.general_guidelines || [];
      const no = pages.length + 1, title = 'रत्न सावधानी र निर्देश';
      if (warns.length || gl.length) {
        let inner = '';
        let yy = 184;
        warns.slice(0, 4).forEach((w, i) => {
          const txt = typeof w === 'string' ? w : (w.message_ne || w.message || w.reason || JSON.stringify(w));
          inner += '<rect x="46" y="' + yy + '" width="628" height="78" rx="13" fill="#2a1720" stroke="#7f1d2d" stroke-width="1.5"/>';
          inner += kunT(66, yy + 24, 'चेतावनी ' + neNum(i + 1), 11, '#fb7185', 700);
          inner += kunPara(66, yy + 48, txt, 72, 12, 17, '#e9eefb', 2);
          yy += 90;
        });
        gl.slice(0, 5).forEach((g, i) => {
          inner += '<rect x="46" y="' + yy + '" width="628" height="74" rx="13" fill="#121d35" stroke="#2b3856" stroke-width="1.5"/>';
          inner += kunT(66, yy + 23, 'निर्देश ' + neNum(i + 1), 11, '#e8b923', 700);
          inner += kunPara(66, yy + 46, g, 72, 12.5, 17, '#e9eefb', 2);
          yy += 84;
        });
        pages.push(kbPage(no, title, 'रत्न धारण, शुद्धता र परामर्श', [
          kbHeader(no, title, 'रत्न धारण, शुद्धता र परामर्श'),
          kbEl(no, title, 'report', 'रत्न सावधानी सूची', [46, 184, 628, Math.max(120, yy - 184)], inner, 7.6),
          kbEl(no, title, 'note', 'रत्न परामर्श नोट', [46, Math.max(760, yy + 12), 628, 44], kunT(46, Math.max(778, yy + 30), 'रत्न/रुद्राक्ष धारण गर्नुअघि योग्य ज्योतिषी वा रत्न विशेषज्ञसँग परामर्श गर्नुहोस्।', 12, '#9fb0d0', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── rudraksha recommendations ── */
    {
      const rem = data.remedies || {}, list = rem.rudraksha_recommendations || [];
      const no = pages.length + 1, title = 'रुद्राक्ष सिफारिस';
      if (list.length) {
        let cards = '';
        list.slice(0, 3).forEach((r, i) => {
          const yy = 184 + i * 182;
          cards += '<rect x="46" y="' + yy + '" width="628" height="168" rx="15" fill="#121d35" stroke="#2b3856" stroke-width="1.5"/>';
          cards += '<rect x="46" y="' + yy + '" width="6" height="168" rx="3" fill="#e8b923"/>';
          cards += kunT(70, yy + 26, r.title || 'रुद्राक्ष', 12, '#9fb0d0', 600);
          cards += kunT(70, yy + 56, r.mukhi || '—', 22, '#f6d365', 700);
          cards += kunT(70, yy + 84, (KUN_NE[r.planet] || r.planet || '—') + ' · ' + (r.deity || '—'), 13, '#e9eefb', 500);
          cards += kunT(70, yy + 110, 'मन्त्र: ' + (r.mantra || '—'), 13, '#b9c6e4', 500);
          cards += kunPara(70, yy + 136, r.benefit || '', 68, 12, 16, '#9fb0d0', 2);
        });
        pages.push(kbPage(no, title, 'लग्नेश, भाग्येश र पीडित ग्रहका रुद्राक्ष', [
          kbHeader(no, title, 'लग्नेश, भाग्येश र पीडित ग्रहका रुद्राक्ष'),
          kbEl(no, title, 'report', 'रुद्राक्ष कार्डहरू', [46, 184, 628, Math.min(3, list.length) * 182 - 14], cards, 7.6),
          kbEl(no, title, 'note', 'रुद्राक्ष नोट', [46, 744, 628, 44], kunT(46, 762, 'रुद्राक्ष सिफारिस Kundali-Desktop को ग्रह-पीडा र लग्नेश/भाग्येश आधारित हो।', 12, '#9fb0d0', 500), 6.2),
          kbFooter(no, title)
        ]));
      }
    }

    /* ── mantras and charity per planet ── */
    {
      const rem = data.remedies || {}, list = rem.mantras_and_charity || [];
      if (list.length) {
        for (let part = 0; part < list.length; part += 5) {
          const chunk = list.slice(part, part + 5);
          const no = pages.length + 1, title = 'मन्त्र र दान (भाग ' + neNum(Math.floor(part / 5) + 1) + ')';
          let cards = '';
          chunk.forEach((m, i) => {
            const yy = 184 + i * 168;
            cards += '<rect x="46" y="' + yy + '" width="628" height="156" rx="15" fill="#121d35" stroke="#2b3856" stroke-width="1.5"/>';
            cards += '<rect x="46" y="' + yy + '" width="6" height="156" rx="3" fill="#34d399"/>';
            cards += kunT(70, yy + 24, (KUN_NE[m.planet] || m.planet || '—'), 17, '#e8b923', 700);
            cards += kunT(650, yy + 24, m.yantra || '', 11, '#7183a8', 500, 'end');
            cards += kunT(70, yy + 48, 'बीज: ' + (m.beej_mantra || '—'), 12.5, '#e9eefb', 500);
            cards += kunT(70, yy + 70, 'सरल: ' + (m.simple_mantra || '—'), 12, '#b9c6e4', 500);
            cards += kunT(70, yy + 92, 'जप: ' + (m.jap_count || '—') + ' · ' + (m.fasting_day || ''), 11.5, '#9fb0d0', 500);
            cards += kunPara(70, yy + 116, 'दान: ' + (m.charity_items || '—'), 68, 11.5, 16, '#b9c6e4', 2);
            cards += kunT(70, yy + 146, 'पात्र: ' + kunFit(m.charity_recipient || '—', 44), 11, '#7183a8', 500);
          });
          pages.push(kbPage(no, title, 'बीज मन्त्र, जप, दान, उपवास र यन्त्र', [
            kbHeader(no, title, 'बीज मन्त्र, जप, दान, उपवास र यन्त्र'),
            kbEl(no, title, 'report', 'मन्त्र र दान कार्डहरू', [46, 184, 628, chunk.length * 168 - 12], cards, 7.6),
            kbEl(no, title, 'note', 'मन्त्र नोट', [46, Math.min(1044, 184 + chunk.length * 168 + 6), 628, 36], kunT(46, Math.min(1062, 184 + chunk.length * 168 + 24), 'मन्त्र र दान — Kundali-Desktop को remedies.mantras_and_charity बाट।', 11, '#7183a8', 500), 6.2),
            kbFooter(no, title)
          ]));
        }
      }
    }

    /* ── Janmapatrika document (manual element catalog) ── */
    {
      const no = pages.length + 1, title = 'जन्मपत्रिका (कुण्डली निर्माण)';
      const jp = kbJanmapatrika(data, meta, { x: 58, y: 170, w: 604 });
      const jpEl = kbEl(no, title, 'report', 'जन्मपत्रिका (कुण्डली निर्माण) — पूर्ण दस्तावेज', [58, 170, 604, 1052], jp.inner, 18);
      jpEl.privacy = (jp.privacy || []).map(g => ({ id: g.id, label: g.label, rects: (g.rects || []).map(r => ({ x: r.x, y: r.y, w: r.w, h: r.h })) }));
      jpEl.scroll = true;
      jpEl.scrollBbox = [58, 170, 604, jp.height];
      jpEl.scrollDur = 28;
      jpEl.scrollDelay = .8;
      jpEl.hideScrollBar = true;
      pages.push(kbPage(no, title, 'परम्परागत जन्मपत्रिका — ॐ, पञ्चाङ्ग, D1, चन्द्र, ग्रह तालिका र दशा', [jpEl]));
    }
  }

  /* Element SVG is generated from the same vector markup. It is not a
     screenshot: the inner SVG is the live chart/table/report component. */
  function kbElSvg(el) {
    const b = el.scrollBbox || el.bbox || [0, 0, 720, 1280];
    const font = KB_FONT.replace(/"/g, "'");
    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + b[2] + '" height="' + b[3] + '" viewBox="' + b[0] + ' ' + b[1] + ' ' + b[2] + ' ' + b[3] + '">' +
      '<rect x="' + b[0] + '" y="' + b[1] + '" width="' + b[2] + '" height="' + b[3] + '" fill="none"/>' +
      '<g font-family="' + font + '">' + el.inner + '</g></svg>';
  }
  function kbElDataUri(el) {
    return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(kbElSvg(el));
  }

  const kbImgCache = new Map();
  const kbImgPending = new Set();
  function kbImgKey(el) { return 'e:' + (el.id || '') + ':' + (el.bbox || []).join(',') + ':' + (el.scrollBbox || []).join(',') + ':' + (el.inner || '').length + ':' + kbHash(el.inner || ''); }
  function kbImgFor(el) {
    const k = kbImgKey(el);
    const hit = kbImgCache.get(k);
    if (hit && hit.ok) return hit.img;
    if (hit && hit.loading) return null;
    const rec = { loading: true, ok: false, img: null };
    kbImgCache.set(k, rec);
    const im = new Image();
    im.decoding = 'async';
    const settle = img => {
      rec.loading = false; rec.ok = !!img; rec.img = img;
      const ws = rec.waiters || []; rec.waiters = [];
      ws.forEach(fn => { try { fn(img) } catch (e) { } });
    };
    im.onload = () => {
      /* Wait for the browser's decode before the first paint. Drawings of a
         large Janmapatrika SVG otherwise start as an empty paper card while
         the bitmap is still being decoded. */
      const finish = () => {
        settle(im);
        if (typeof draw === 'function' && !playing && !exporting) { try { draw(cur) } catch (e) { } }
        if (typeof kbPreviewRedraw === 'function') { try { kbPreviewRedraw() } catch (e) { } }
      };
      if (im.decode) im.decode().then(finish, finish); else finish();
    };
    im.onerror = () => settle(null);
    im.src = kbElDataUri(el);
    return null;
  }
  /* Ad photos are stored as compressed data URLs in the element state, not
     as page screenshots. They are cached once and drawn straight into the
     card, so Select / Replace / Remove is instant. */
  const kbAdCache = new Map();
  function kbAdImg(src) {
    if (!src) return null;
    let rec = kbAdCache.get(src);
    if (!rec) {
      rec = { img: null, ok: false, loading: true };
      kbAdCache.set(src, rec);
      const im = new Image();
      im.decoding = 'async';
      im.onload = () => {
        rec.loading = false; rec.ok = true; rec.img = im;
        if (typeof draw === 'function' && !playing && !exporting) { try { draw(cur) } catch (e) { } }
        if (typeof kbPreviewRedraw === 'function') { try { kbPreviewRedraw() } catch (e) { } }
      };
      im.onerror = () => { rec.loading = false; rec.ok = false; };
      im.src = src;
    }
    return rec.ok ? rec.img : null;
  }
  /* Shared portrait pipeline for the builder and the Timeline inspector:
     a photo is centre-drawn into a JPEG data URL, then gently downscaled
     until it comfortably fits the project/localStorage budget. The final
     card draws it as a circular portrait, so ~1000px is already ample. */
  function kbPhotoPrepare(file) {
    return new Promise((resolve, reject) => {
      if (!file) { reject(new Error('कुनै फोटो छानिएन।')); return; }
      if (!/^image\//.test(file.type || '')) { reject(new Error('कृपया JPG, PNG वा WebP फोटो छान्नुहोस्।')); return; }
      const reader = new FileReader();
      reader.onload = () => {
        const img = new Image();
        img.onload = () => {
          try {
            const render = (max, q) => {
              const k = Math.min(1, max / Math.max(img.width || 1, img.height || 1));
              const w = Math.max(1, Math.round((img.width || max) * k));
              const h = Math.max(1, Math.round((img.height || max) * k));
              const c = document.createElement('canvas'); c.width = w; c.height = h;
              const g = c.getContext('2d');
              g.fillStyle = '#0a1224'; g.fillRect(0, 0, w, h); g.drawImage(img, 0, 0, w, h);
              return c.toDataURL('image/jpeg', q);
            };
            let data = render(1000, .84);
            if (data.length > 900000) data = render(820, .76);
            if (data.length > 900000) data = render(680, .7);
            resolve(data);
          } catch (e) { reject(new Error('फोटो तयार गर्न सकिएन।')); }
        };
        img.onerror = () => reject(new Error('यो फोटो खोल्न सकिएन।'));
        img.src = reader.result;
      };
      reader.onerror = () => reject(new Error('फाइल पढ्न सकिएन।'));
      reader.readAsDataURL(file);
    });
  }
  window.KunPhoto = { prepare: kbPhotoPrepare };

  function kbPrimeEls(els) {
    const list = (els || []).filter(Boolean);
    return Promise.all(list.map(el => new Promise(res => {
      const k = kbImgKey(el), hit = kbImgCache.get(k);
      if (hit && hit.ok) return res(hit.img);
      if (hit && hit.loading) { (hit.waiters || (hit.waiters = [])).push(res); return; }
      const rec = { loading: true, ok: false, img: null, waiters: [res] };
      kbImgCache.set(k, rec);
      const done = img => {
        rec.loading = false; rec.ok = !!img; rec.img = img;
        const ws = rec.waiters || []; rec.waiters = [];
        ws.forEach(fn => { try { fn(img) } catch (e) { } });
      };
      const im = new Image(); im.decoding = 'async';
      im.onload = () => {
        const finish = () => done(im);
        if (im.decode) im.decode().then(finish, finish); else finish();
      };
      im.onerror = () => done(null);
      im.src = kbElDataUri(el);
    })));
  }
  function kbPrimeCustom() {
    const els = [];
    (clips || []).forEach(c => { if (c.kun) kbSceneEls(c.kun).forEach(e => els.push(e)) });
    if (els.length) kbPrimeEls(els).then(() => { if (typeof draw === 'function' && !playing && !exporting) { try { draw(cur) } catch (e) { } } });
  }
  window.kunPrimeCustom = kbPrimeCustom;
  window.kunPrimeAll = function () {
    const els = [];
    (clips || []).forEach(c => { if (c.kun) kbSceneEls(c.kun).forEach(e => els.push(e)) });
    return kbPrimeEls(els);
  };

  /* expose a small part of the catalog for tests and for the editor */
  window.KunBuilderCatalog = { build: kbCatalog, svg: kbElSvg };

  /* ═══════════════════════════════════════════════════════════════
     scene renderer — 720 × 1280 design space
     ═══════════════════════════════════════════════════════════════ */

  const KB_DW = 720, KB_DH = 1280;
  const KB_TPL_OV = Object.create(null);
  const KB_LIGHT = new Set(['glass', 'minimal', 'ancient', 'vedic']);

  function kbTplDef(id) {
    const base = KB_TPLS[id] || KB_TPLS.cosmic;
    const ov = KB_TPL_OV[base.id] || {};
    return Object.assign({}, base, {
      accent: ov.accent || base.accent,
      accent2: ov.accent2 || base.accent2,
      font: ov.font || base.font,
      display: ov.display || base.display,
      radius: ov.radius != null ? ov.radius : base.radius
    });
  }
  function kbRgba(hex, a) {
    if (!hex || hex[0] !== '#') return hex || ('rgba(0,0,0,' + a + ')');
    let h = hex.slice(1);
    if (h.length === 3) h = h.split('').map(c => c + c).join('');
    const n = parseInt(h, 16);
    if (!isFinite(n)) return 'rgba(0,0,0,' + a + ')';
    return 'rgba(' + (n >> 16 & 255) + ',' + (n >> 8 & 255) + ',' + (n & 255) + ',' + a + ')';
  }
  function kbSeed(seed) {
    let s = (seed >>> 0) || 1;
    return function () { s = (Math.imul(s, 1664525) + 1013904223) >>> 0; return s / 4294967296; };
  }
  function kbRR(g, x, y, w, h, r) {
    r = Math.max(0, Math.min(r || 0, Math.min(w, h) / 2));
    g.beginPath();
    if (g.roundRect) { g.roundRect(x, y, w, h, r); return; }
    g.moveTo(x + r, y); g.lineTo(x + w - r, y); g.quadraticCurveTo(x + w, y, x + w, y + r);
    g.lineTo(x + w, y + h - r); g.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    g.lineTo(x + r, y + h); g.quadraticCurveTo(x, y + h, x, y + h - r);
    g.lineTo(x, y + r); g.quadraticCurveTo(x, y, x + r, y);
  }
  function kbEllipsis(g, text, maxW) {
    text = String(text == null ? '' : text);
    if (g.measureText(text).width <= maxW) return text;
    let t = text;
    while (t.length > 1 && g.measureText(t + '…').width > maxW) t = t.slice(0, -1);
    return t + '…';
  }
  function kbLayout(w, h) {
    const u = Math.min(w / KB_DW, h / KB_DH);
    return { u: u, ox: (w - KB_DW * u) / 2, oy: (h - KB_DH * u) / 2 };
  }

  /* ── cosmic environment helpers ─────────────────────────────────
     The default model's backdrop is a layered deep-space scene rather than
     a flat gradient: nebula clouds, a spiral galaxy, a ringed planet with
     moons, orbital paths, twinkling stars, shooting stars and drifting dust.
     Contrast stays low and every layer sits behind the content card.
     Per-model particle budgets keep the compositor inside the 30fps target
     even when the background is drawn for an export-sized canvas. */
  const KB_BG_BUDGET = {
    cosmic: { stars: 190, galaxy: 150, dust: 22, shooting: 3 },
    nebula: { stars: 96 },
    vedic: { fibers: 110 },
    orbit: { orbits: 4 }
  };
  function kbCosNebula(g, x, y, r, w, h, c0, c1) {
    const gr = g.createRadialGradient(x, y, 0, x, y, r);
    gr.addColorStop(0, c0); gr.addColorStop(.55, c1); gr.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = gr; g.fillRect(0, 0, w, h);
  }
  function kbCosGalaxy(g, cx, cy, r, rot, t, k, seed, count) {
    g.save(); g.translate(cx, cy); g.rotate(rot + t * .01);
    const rnd = kbSeed(seed);
    const n = Math.max(24, count || 190);
    const core = g.createRadialGradient(0, 0, 0, 0, 0, r * .5);
    core.addColorStop(0, 'rgba(255,244,214,.20)');
    core.addColorStop(.42, 'rgba(246,211,101,.09)');
    core.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = core; g.beginPath(); g.arc(0, 0, r * .5, 0, 7); g.fill();
    for (let i = 0; i < n; i++) {
      const a = i * .23 + rnd() * .34;
      const rr = Math.pow(i / n, .62) * r;
      const x = Math.cos(a) * rr, y = Math.sin(a) * rr * .42;
      const s = (.5 + rnd() * 1.35) * k;
      g.fillStyle = 'rgba(' + (198 + Math.round(rnd() * 57)) + ',' + (218 + Math.round(rnd() * 34)) + ',255,' + (.09 + .32 * (1 - i / n)) + ')';
      g.beginPath(); g.arc(x, y, s, 0, 7); g.fill();
    }
    g.restore();
  }
  function kbCosPlanet(g, x, y, r, t, k) {
    const halo = g.createRadialGradient(x, y, r * .6, x, y, r * 2.1);
    halo.addColorStop(0, 'rgba(246,211,101,.15)');
    halo.addColorStop(.55, 'rgba(110,231,255,.06)');
    halo.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = halo; g.beginPath(); g.arc(x, y, r * 2.1, 0, 7); g.fill();
    /* rear half of the ring */
    g.save(); g.translate(x, y); g.rotate(-.32);
    g.strokeStyle = 'rgba(246,211,101,.28)'; g.lineWidth = 1.4 * k;
    g.beginPath(); g.ellipse(0, 0, r * 1.85, r * .5, 0, Math.PI, Math.PI * 2); g.stroke();
    g.restore();
    const sp = g.createRadialGradient(x - r * .38, y - r * .42, r * .1, x, y, r);
    sp.addColorStop(0, '#f9e6a8'); sp.addColorStop(.35, '#c9973f');
    sp.addColorStop(.72, '#6d4a1f'); sp.addColorStop(1, '#241a10');
    g.fillStyle = sp; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill();
    const sh = g.createRadialGradient(x + r * .55, y + r * .45, r * .1, x + r * .2, y + r * .2, r * 1.1);
    sh.addColorStop(0, 'rgba(2,6,14,.55)'); sh.addColorStop(.6, 'rgba(2,6,14,.16)'); sh.addColorStop(1, 'rgba(2,6,14,0)');
    g.fillStyle = sh; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill();
    /* front half of the ring */
    g.save(); g.translate(x, y); g.rotate(-.32);
    g.strokeStyle = 'rgba(246,211,101,.42)'; g.lineWidth = 1.6 * k;
    g.beginPath(); g.ellipse(0, 0, r * 1.85, r * .5, 0, 0, Math.PI); g.stroke();
    g.strokeStyle = 'rgba(255,240,198,.16)'; g.lineWidth = 3.4 * k;
    g.beginPath(); g.ellipse(0, 0, r * 2.08, r * .58, 0, 0, Math.PI); g.stroke();
    g.restore();
    [[r * 2.9, -.62, 2.6, 'rgba(233,238,255,.9)'], [r * 3.35, .28, 1.8, 'rgba(110,231,255,.85)']].forEach((m, i) => {
      const a = m[1] + Math.sin(t * .12 + i * 2.1) * .08;
      g.fillStyle = m[3];
      g.beginPath(); g.arc(x + Math.cos(a) * m[0], y + Math.sin(a) * m[0] * .42, m[2] * k, 0, 7); g.fill();
    });
  }
  function kbCosOrbits(g, cx, cy, w, h, k, t) {
    g.save(); g.translate(cx, cy); g.rotate(-.26);
    for (let i = 1; i <= 4; i++) {
      g.strokeStyle = 'rgba(246,211,101,' + (.12 - i * .012) + ')';
      g.lineWidth = 1 * k;
      g.beginPath(); g.ellipse(0, 0, w * (.20 + i * .075), h * (.05 + i * .017), 0, 0, 7); g.stroke();
    }
    for (let i = 0; i < 2; i++) {
      const rx = w * (.275 + i * .15), ry = h * (.067 + i * .034);
      const a = t * (.12 + i * .05) + i * 2.1;
      const px = Math.cos(a) * rx, py = Math.sin(a) * ry;
      g.fillStyle = i ? 'rgba(110,231,255,.70)' : 'rgba(246,211,101,.82)';
      g.beginPath(); g.arc(px, py, (1.8 + i) * k, 0, 7); g.fill();
      if (!i) { g.fillStyle = 'rgba(246,211,101,.13)'; g.beginPath(); g.arc(px, py, 6 * k, 0, 7); g.fill(); }
    }
    g.restore();
  }
  function kbCosShooting(g, w, h, t, k, seed, count) {
    const rnd = kbSeed(seed);
    const n = Math.max(0, count == null ? 3 : count);
    for (let i = 0; i < n; i++) {
      const sx = w * (.08 + rnd() * .78), sy = h * (.05 + rnd() * .45);
      const speed = .22 + rnd() * .16;
      const p = ((t * speed + rnd() * 4) % 6.4) / 6.4;
      if (p > .085) continue;
      const q = p / .085;
      const len = (120 + rnd() * 90) * k;
      const dx = Math.cos(.5) * len, dy = Math.sin(.5) * len;
      const hx = sx + dx * q, hy = sy + dy * q;
      const a = Math.sin(q * Math.PI) * .72;
      const gr = g.createLinearGradient(hx - dx, hy - dy, hx, hy);
      gr.addColorStop(0, 'rgba(255,255,255,0)');
      gr.addColorStop(.65, 'rgba(246,211,101,' + (.42 * a) + ')');
      gr.addColorStop(1, 'rgba(255,255,255,' + (.9 * a) + ')');
      g.strokeStyle = gr; g.lineWidth = 1.8 * k; g.lineCap = 'round';
      g.beginPath(); g.moveTo(hx - dx, hy - dy); g.lineTo(hx, hy); g.stroke();
      g.fillStyle = 'rgba(255,255,255,' + a + ')';
      g.beginPath(); g.arc(hx, hy, 1.9 * k, 0, 7); g.fill();
    }
    g.lineCap = 'butt';
  }
  function kbCosDust(g, w, h, t, k, count) {
    const n = Math.max(0, count == null ? 34 : count);
    for (let i = 0; i < n; i++) {
      const ph = i * 1.7;
      const x = ((i * 97.3) % w) + Math.sin(t * .18 + ph) * 9 * k;
      const y = ((i * 211.7) % h) + Math.cos(t * .14 + ph) * 12 * k;
      g.fillStyle = 'rgba(190,220,255,' + (.05 + .10 * Math.abs(Math.sin(t * .4 + ph))) + ')';
      g.beginPath(); g.arc(x, y, (.8 + (i % 3) * .45) * k, 0, 7); g.fill();
    }
  }
  function kbCosConstellation(g, pts, k, alpha) {
    g.strokeStyle = 'rgba(150,200,255,' + (alpha * .5) + ')'; g.lineWidth = .8 * k;
    g.beginPath();
    pts.forEach((p, i) => i ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1]));
    g.stroke();
    pts.forEach((p, i) => {
      g.fillStyle = 'rgba(220,238,255,' + (alpha * (i % 3 ? .8 : 1)) + ')';
      g.beginPath(); g.arc(p[0], p[1], (1 + (i % 3) * .5) * k, 0, 7); g.fill();
    });
  }
  function kbCosScrim(g, w, h) {
    const vg = g.createRadialGradient(w * .5, h * .46, Math.min(w, h) * .25, w * .5, h * .48, Math.max(w, h) * .72);
    vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(1,3,9,.55)');
    g.fillStyle = vg; g.fillRect(0, 0, w, h);
    const top = g.createLinearGradient(0, 0, 0, h * .17);
    top.addColorStop(0, 'rgba(1,3,10,.78)'); top.addColorStop(1, 'rgba(1,3,10,0)');
    g.fillStyle = top; g.fillRect(0, 0, w, h * .17);
    const bot = g.createLinearGradient(0, h * .87, 0, h);
    bot.addColorStop(0, 'rgba(1,3,10,0)'); bot.addColorStop(1, 'rgba(1,3,10,.74)');
    g.fillStyle = bot; g.fillRect(0, h * .87, w, h * .13);
  }
  function kbCosmicSky(g, w, h, def, t, k) {
    const B = KB_BG_BUDGET.cosmic;
    kbCosNebula(g, w * (.18 + Math.sin(t * .03) * .02), h * .20, w * .60, w, h, 'rgba(86,74,208,.30)', 'rgba(44,92,202,.11)');
    kbCosNebula(g, w * .86, h * (.40 + Math.cos(t * .025) * .02), w * .52, w, h, 'rgba(110,231,255,.15)', 'rgba(38,120,180,.06)');
    kbCosNebula(g, w * .46, h * .88, w * .58, w, h, 'rgba(246,211,101,.12)', 'rgba(150,96,26,.05)');
    kbCosGalaxy(g, w * .80, h * .12, w * .26, -.42, t, k, def.seed + 17, B.galaxy);
    const rnd = kbSeed(def.seed);
    for (let i = 0; i < B.stars; i++) {
      const x = rnd() * w, y = rnd() * h;
      const r = (.45 + rnd() * 1.7) * k;
      const tint = rnd();
      const ph = rnd() * 6.283, sp = .3 + rnd() * .85;
      const tw = .22 + .78 * Math.abs(Math.sin(t * sp + ph));
      const col = tint > .93 ? '246,211,101' : tint > .8 ? '150,205,255' : '235,243,255';
      g.fillStyle = 'rgba(' + col + ',' + (.12 + .62 * tw) + ')';
      g.beginPath(); g.arc(x, y, r, 0, 7); g.fill();
      if (i % 31 === 0) {
        g.strokeStyle = 'rgba(' + col + ',' + (.10 + .20 * tw) + ')'; g.lineWidth = .8 * k;
        g.beginPath(); g.moveTo(x - r * 4, y); g.lineTo(x + r * 4, y); g.moveTo(x, y - r * 4); g.lineTo(x, y + r * 4); g.stroke();
      }
    }
    kbCosConstellation(g, [
      [w * .07, h * .62], [w * .13, h * .57], [w * .18, h * .66], [w * .12, h * .72], [w * .06, h * .79]
    ], k, .12);
    kbCosOrbits(g, w * .5, h * .34, w, h, k, t);
    kbCosPlanet(g, w * .815, h * .085, w * .047, t, k);
    kbCosShooting(g, w, h, t, k, def.seed + 31, B.shooting);
    kbCosDust(g, w, h, t, k, B.dust);
    kbCosScrim(g, w, h);
  }

  function kbRenderBg(g, w, h, def, clock) {
    const t = clock || 0, k = Math.min(w / KB_DW, h / KB_DH), light = KB_LIGHT.has(def.motion);
    g.save();
    g.globalCompositeOperation = 'source-over';
    const gr = g.createLinearGradient(0, 0, w * .45, h);
    gr.addColorStop(0, def.bg[0]); gr.addColorStop(.55, def.bg[1]); gr.addColorStop(1, def.bg[2]);
    g.fillStyle = gr; g.fillRect(0, 0, w, h);

    if (def.motion === 'cosmic') {
      kbCosmicSky(g, w, h, def, t, k);
    } else if (def.motion === 'golden') {
      const rnd = kbSeed(def.seed);
      for (let i = 0; i < 96; i++) {
        const x = rnd() * w, y = rnd() * h, r = (.7 + rnd() * 1.8) * k;
        const tw = .25 + .75 * Math.abs(Math.sin(t * .65 + i * 1.7));
        g.fillStyle = 'rgba(255,255,255,' + (.12 + .5 * tw) + ')';
        g.beginPath(); g.arc(x, y, r, 0, 7); g.fill();
      }
      const n1 = g.createRadialGradient(w * .2, h * .2, 0, w * .2, h * .2, w * .62);
      n1.addColorStop(0, 'rgba(212,175,55,.28)');
      n1.addColorStop(.55, 'rgba(120,90,20,.10)');
      n1.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = n1; g.fillRect(0, 0, w, h);
      const n2 = g.createRadialGradient(w * .82, h * .68, 0, w * .82, h * .68, w * .5);
      n2.addColorStop(0, 'rgba(255,215,106,.16)');
      n2.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = n2; g.fillRect(0, 0, w, h);
      g.save(); g.translate(w * .68, h * .4); g.rotate(t * .035);
      const rnd2 = kbSeed(def.seed + 5);
      for (let i = 0; i < 220; i++) {
        const a = i * .31, r = Math.pow(i / 220, .62) * w * .43;
        const x = Math.cos(a) * r, y = Math.sin(a) * r * .5;
        const s = (.5 + rnd2() * 1.6) * k;
        g.fillStyle = 'rgba(255,215,106,' + (.16 + .5 * (1 - i / 220)) + ')';
        g.beginPath(); g.arc(x, y, s, 0, 7); g.fill();
      }
      g.restore();
    } else if (def.motion === 'royal') {
      g.save(); g.translate(w / 2, 0);
      for (let i = 0; i < 4; i++) {
        g.strokeStyle = 'rgba(241,196,106,' + (.16 - i * .025) + ')';
        g.lineWidth = 1.5 * k;
        g.beginPath(); g.arc(0, h * .28, w * (.24 + i * .075), Math.PI, 0); g.stroke();
      }
      g.restore();
      const rnd = kbSeed(def.seed);
      for (let y = h * .18; y < h * .92; y += 34 * k) {
        for (let x = 30 * k; x < w - 30 * k; x += 34 * k) {
          g.fillStyle = 'rgba(241,196,106,.075)';
          g.save(); g.translate(x + (rnd() - .5) * 4 * k, y + (rnd() - .5) * 4 * k); g.rotate(Math.PI / 4);
          g.fillRect(-1.2 * k, -1.2 * k, 2.4 * k, 2.4 * k); g.restore();
        }
      }
      const rv = g.createRadialGradient(w * .5, h * .45, w * .1, w * .5, h * .45, w * .78);
      rv.addColorStop(0, 'rgba(0,0,0,0)'); rv.addColorStop(1, 'rgba(10,0,3,.55)');
      g.fillStyle = rv; g.fillRect(0, 0, w, h);
    } else if (def.motion === 'glass') {
      const blobs = [
        [.2 + Math.sin(t * .17) * .03, .18, 'rgba(124,58,237,.36)'],
        [.82 + Math.cos(t * .14) * .03, .2, 'rgba(6,182,212,.30)'],
        [.62, .82 + Math.sin(t * .12) * .03, 'rgba(236,72,153,.22)']
      ];
      blobs.forEach((b, i) => {
        const r = w * .46;
        const bg = g.createRadialGradient(w * b[0], h * b[1], 0, w * b[0], h * b[1], r);
        bg.addColorStop(0, b[2]); bg.addColorStop(.55, b[2].replace(/[\d.]+\)$/, '.10)')); bg.addColorStop(1, 'rgba(255,255,255,0)');
        g.fillStyle = bg; g.fillRect(0, 0, w, h);
      });
      g.strokeStyle = 'rgba(23,37,84,.055)'; g.lineWidth = 1;
      for (let x = 0; x < w; x += 54 * k) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); }
      for (let y = 0; y < h; y += 54 * k) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); }
      g.fillStyle = 'rgba(255,255,255,.20)'; g.fillRect(0, 0, w, h * .035);
    } else if (def.motion === 'cinematic') {
      const s = g.createRadialGradient(w * .5, h * .06, 0, w * .5, h * .06, w * .72);
      s.addColorStop(0, 'rgba(232,176,75,.24)'); s.addColorStop(.5, 'rgba(120,70,20,.07)'); s.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = s; g.fillRect(0, 0, w, h);
      const rnd = kbSeed(def.seed);
      for (let i = 0; i < 40; i++) {
        const x = rnd() * w, y = rnd() * h, r = (.4 + rnd() * 1.2) * k;
        g.fillStyle = 'rgba(255,220,160,' + (.08 + rnd() * .18) + ')';
        g.beginPath(); g.arc(x, y, r, 0, 7); g.fill();
      }
      g.fillStyle = 'rgba(0,0,0,.86)'; g.fillRect(0, 0, w, h * .028); g.fillRect(0, h * .972, w, h * .028);
      g.strokeStyle = 'rgba(232,176,75,.14)'; g.lineWidth = 1.2 * k;
      g.strokeRect(w * .052, h * .052, w * .896, h * .896);
      g.strokeStyle = 'rgba(255,255,255,.05)';
      g.strokeRect(w * .058, h * .058, w * .884, h * .884);
    } else if (def.motion === 'neon') {
      g.save();
      const hy = h * .69;
      const fg = g.createLinearGradient(0, hy, 0, h);
      fg.addColorStop(0, 'rgba(34,211,238,.02)'); fg.addColorStop(1, 'rgba(34,211,238,.13)');
      g.fillStyle = fg; g.fillRect(0, hy, w, h - hy);
      g.strokeStyle = 'rgba(34,211,238,.16)'; g.lineWidth = 1;
      for (let i = -8; i <= 8; i++) { g.beginPath(); g.moveTo(w / 2, hy); g.lineTo(w / 2 + i * w * .14, h); g.stroke(); }
      for (let i = 1; i <= 8; i++) { const y = hy + Math.pow(i / 8, 2.1) * (h - hy); g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); }
      g.restore();
      const n1 = g.createRadialGradient(w * .18, h * .24, 0, w * .18, h * .24, w * .5);
      n1.addColorStop(0, 'rgba(34,211,238,.20)'); n1.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = n1; g.fillRect(0, 0, w, h);
      const n2 = g.createRadialGradient(w * .85, h * .55, 0, w * .85, h * .55, w * .45);
      n2.addColorStop(0, 'rgba(244,114,182,.15)'); n2.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = n2; g.fillRect(0, 0, w, h);
      g.fillStyle = 'rgba(34,211,238,.035)';
      for (let y = 0; y < h; y += 5 * k) g.fillRect(0, y, w, 1);
    } else if (def.motion === 'minimal') {
      g.fillStyle = 'rgba(184,134,59,.10)';
      g.fillRect(w * .08, h * .09, w * .84, 1);
      g.fillRect(w * .08, h * .91, w * .84, 1);
      g.strokeStyle = 'rgba(31,26,20,.12)'; g.lineWidth = 1 * k;
      g.beginPath(); g.arc(w * .84, h * .075, 12 * k, 0, 7); g.stroke();
      g.fillStyle = 'rgba(31,26,20,.30)';
      g.font = '600 ' + (9 * k) + 'px ' + KB_FONT;
      g.textAlign = 'center'; g.fillText('ॐ', w * .84, h * .078 + 3 * k); g.textAlign = 'left';
      const rnd = kbSeed(def.seed);
      for (let i = 0; i < 80; i++) {
        g.fillStyle = 'rgba(120,96,60,.05)';
        g.fillRect(rnd() * w, rnd() * h, 1.2 * k, 1.2 * k);
      }
    } else if (def.motion === 'ancient') {
      const rnd = kbSeed(def.seed);
      for (let i = 0; i < 70; i++) {
        g.fillStyle = 'rgba(120,80,40,' + (.025 + rnd() * .05) + ')';
        g.beginPath(); g.arc(rnd() * w, rnd() * h, (1 + rnd() * 5) * k, 0, 7); g.fill();
      }
      g.save(); g.translate(w * .82, h * .16);
      for (let i = 1; i <= 5; i++) {
        g.strokeStyle = 'rgba(127,29,29,' + (.13 - i * .018) + ')'; g.lineWidth = 1.2 * k;
        g.beginPath(); g.arc(0, 0, i * 34 * k, 0, 7); g.stroke();
      }
      for (let i = 0; i < 12; i++) {
        g.save(); g.rotate(i * Math.PI / 6);
        g.strokeStyle = 'rgba(127,29,29,.09)'; g.beginPath(); g.ellipse(0, -76 * k, 14 * k, 30 * k, 0, 0, 7); g.stroke();
        g.restore();
      }
      g.restore();
      g.fillStyle = 'rgba(127,29,29,.045)';
      g.font = '700 ' + (210 * k) + 'px ' + KB_FONT;
      g.textAlign = 'center'; g.fillText('ॐ', w * .5, h * .62); g.textAlign = 'left';
    } else if (def.motion === 'floating') {
      const rnd = kbSeed(def.seed);
      for (let i = 0; i < 6; i++) {
        const x = w * (.08 + rnd() * .7), y = h * (.1 + rnd() * .75);
        const rw = w * (.16 + rnd() * .26), rh = h * (.035 + rnd() * .08);
        g.save(); g.translate(x + Math.sin(t * .2 + i) * 5 * k, y + Math.cos(t * .17 + i) * 6 * k);
        g.rotate((rnd() - .5) * .5);
        g.fillStyle = 'rgba(167,139,250,.045)'; g.strokeStyle = 'rgba(167,139,250,.14)'; g.lineWidth = 1.2 * k;
        kbRR(g, 0, 0, rw, rh, 16 * k); g.fill(); g.stroke();
        g.restore();
      }
      const n1 = g.createRadialGradient(w * .3, h * .3, 0, w * .3, h * .3, w * .6);
      n1.addColorStop(0, 'rgba(56,189,248,.13)'); n1.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = n1; g.fillRect(0, 0, w, h);
    } else if (def.motion === 'nextgen') {
      g.strokeStyle = 'rgba(45,212,191,.08)'; g.lineWidth = 1;
      for (let x = 0; x < w; x += 44 * k) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); }
      for (let y = 0; y < h; y += 44 * k) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); }
      g.save(); g.translate(w * .78, h * .18);
      for (let i = 0; i < 3; i++) {
        g.strokeStyle = 'rgba(163,230,53,' + (.16 - i * .04) + ')'; g.lineWidth = 1.5 * k;
        g.beginPath(); g.arc(0, 0, (36 + i * 26) * k, -.8 + t * .1, 1.6 + t * .1); g.stroke();
      }
      g.restore();
      const n1 = g.createRadialGradient(w * .2, h * .8, 0, w * .2, h * .8, w * .55);
      n1.addColorStop(0, 'rgba(45,212,191,.15)'); n1.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = n1; g.fillRect(0, 0, w, h);
      const sy = (t * 42) % h;
      const sg = g.createLinearGradient(0, sy - 40 * k, 0, sy + 40 * k);
      sg.addColorStop(0, 'rgba(163,230,53,0)'); sg.addColorStop(.5, 'rgba(163,230,53,.07)'); sg.addColorStop(1, 'rgba(163,230,53,0)');
      g.fillStyle = sg; g.fillRect(0, sy - 40 * k, w, 80 * k);
    } else if (def.motion === 'nebula') {
      const rnd = kbSeed(def.seed);
      for (let i = 0; i < KB_BG_BUDGET.nebula.stars; i++) {
        const x = rnd() * w, y = rnd() * h, r = (.6 + rnd() * 1.9) * k;
        const tw = .3 + .7 * Math.abs(Math.sin(t * .5 + i * 2.1));
        g.fillStyle = 'rgba(255,255,255,' + (.10 + .42 * tw) + ')';
        g.beginPath(); g.arc(x, y, r, 0, 7); g.fill();
      }
      const blobs = [
        [.26 + Math.sin(t * .08) * .035, .22 + Math.cos(t * .07) * .025, .56, 'rgba(139,92,246,.34)'],
        [.80 + Math.cos(t * .06) * .035, .38 + Math.sin(t * .09) * .025, .48, 'rgba(34,211,238,.20)'],
        [.50 + Math.sin(t * .05) * .045, .84 + Math.cos(t * .04) * .02, .54, 'rgba(236,72,153,.14)']
      ];
      blobs.forEach(b => {
        const bg2 = g.createRadialGradient(w * b[0], h * b[1], 0, w * b[0], h * b[1], w * b[2]);
        bg2.addColorStop(0, b[3]); bg2.addColorStop(.52, b[3].replace(/[\d.]+\)$/, '.07)')); bg2.addColorStop(1, 'rgba(0,0,0,0)');
        g.fillStyle = bg2; g.fillRect(0, 0, w, h);
      });
      g.save(); g.translate(w * .5, h * .3); g.rotate(-.55 + Math.sin(t * .05) * .06);
      const streak = g.createLinearGradient(0, -h * .04, 0, h * .04);
      streak.addColorStop(0, 'rgba(233,213,255,0)'); streak.addColorStop(.5, 'rgba(233,213,255,.11)'); streak.addColorStop(1, 'rgba(233,213,255,0)');
      g.fillStyle = streak; g.fillRect(-w * .46, -h * .04, w * .92, h * .08);
      g.restore();
      g.strokeStyle = 'rgba(196,181,253,.07)'; g.lineWidth = 1;
      for (let y = h * .12; y < h * .96; y += 46 * k) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); }
    } else if (def.motion === 'vedic') {
      const rnd = kbSeed(def.seed);
      for (let i = 0; i < KB_BG_BUDGET.vedic.fibers; i++) {
        g.fillStyle = 'rgba(96,62,30,' + (.018 + rnd() * .04) + ')';
        g.fillRect(rnd() * w, rnd() * h, (1 + rnd() * 2.2) * k, 1 * k);
      }
      g.strokeStyle = 'rgba(120,80,40,.055)'; g.lineWidth = 1;
      for (let y = 0; y < h; y += 9 * k) {
        g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke();
      }
      g.save(); g.translate(w * .82, h * .16); g.rotate(t * .018);
      for (let i = 1; i <= 4; i++) {
        g.strokeStyle = 'rgba(138,28,28,' + (.10 - i * .018) + ')'; g.lineWidth = 1.1 * k;
        g.beginPath(); g.arc(0, 0, i * 36 * k, 0, 7); g.stroke();
      }
      for (let i = 0; i < 12; i++) {
        g.save(); g.rotate(i * Math.PI / 6);
        g.strokeStyle = 'rgba(138,28,28,.075)'; g.lineWidth = 1 * k;
        g.beginPath(); g.ellipse(0, -80 * k, 15 * k, 31 * k, 0, 0, 7); g.stroke();
        g.restore();
      }
      g.fillStyle = 'rgba(161,98,7,.10)';
      g.beginPath(); g.arc(0, 0, 13 * k, 0, 7); g.fill();
      g.restore();
      g.fillStyle = 'rgba(138,28,28,.035)';
      g.font = '700 ' + (220 * k) + 'px ' + KB_FONT;
      g.textAlign = 'center'; g.fillText('ॐ', w * .5, h * .63); g.textAlign = 'left';
      g.fillStyle = 'rgba(161,98,7,.05)';
      g.fillRect(w * .06, h * .07, w * .88, 2 * k);
      g.fillRect(w * .06, h * .93, w * .88, 2 * k);
    } else if (def.motion === 'orbit') {
      g.strokeStyle = 'rgba(34,211,238,.055)'; g.lineWidth = 1;
      for (let x = 0; x < w; x += 48 * k) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, h); g.stroke(); }
      for (let y = 0; y < h; y += 48 * k) { g.beginPath(); g.moveTo(0, y); g.lineTo(w, y); g.stroke(); }
      const cx = w * .78, cy = h * .2;
      const sun = g.createRadialGradient(cx, cy, 0, cx, cy, w * .42);
      sun.addColorStop(0, 'rgba(163,230,53,.30)'); sun.addColorStop(.35, 'rgba(34,211,238,.11)'); sun.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = sun; g.fillRect(0, 0, w, h);
      g.fillStyle = 'rgba(236,254,255,.92)';
      g.beginPath(); g.arc(cx, cy, 9 * k, 0, 7); g.fill();
      for (let i = 1; i <= 4; i++) {
        const rx = (52 + i * 30) * k, ry = rx * .42;
        g.strokeStyle = 'rgba(163,230,53,' + (.26 - i * .04) + ')'; g.lineWidth = 1.2 * k;
        g.beginPath(); g.ellipse(cx, cy, rx, ry, -.42, 0, 7); g.stroke();
        const a = t * (.5 - i * .06) + i * 1.9;
        const px = cx + Math.cos(a) * rx, py = cy + Math.sin(a) * ry;
        g.save(); g.translate(px, py); g.rotate(-.42);
        g.fillStyle = i === 2 ? 'rgba(34,211,238,.95)' : (i === 4 ? 'rgba(251,113,133,.9)' : 'rgba(163,230,53,.95)');
        g.beginPath(); g.arc(0, 0, (3.2 + i * .4) * k, 0, 7); g.fill(); g.restore();
      }
      g.strokeStyle = 'rgba(163,230,53,.14)'; g.lineWidth = 1 * k;
      g.beginPath(); g.moveTo(0, h * .69); g.lineTo(w, h * .69); g.stroke();
      const sy2 = (t * 26) % h;
      const sg2 = g.createLinearGradient(0, sy2 - 34 * k, 0, sy2 + 34 * k);
      sg2.addColorStop(0, 'rgba(34,211,238,0)'); sg2.addColorStop(.5, 'rgba(34,211,238,.06)'); sg2.addColorStop(1, 'rgba(34,211,238,0)');
      g.fillStyle = sg2; g.fillRect(0, sy2 - 34 * k, w, 68 * k);
    }

    const vg = g.createRadialGradient(w / 2, h * .44, Math.min(w, h) * .18, w / 2, h * .44, Math.max(w, h) * .76);
    vg.addColorStop(0, 'rgba(0,0,0,0)');
    vg.addColorStop(1, light ? 'rgba(40,24,8,.10)' : 'rgba(0,0,0,.38)');
    g.fillStyle = vg; g.fillRect(0, 0, w, h);
    g.restore();
  }

  /* Backgrounds are expensive particle scenes, but they move slowly. Render
     each model/size into an offscreen canvas at 15 Hz and reuse that layer
     for the two 30fps frames in between. This is the pre-rendered star /
     particle layer for the performance budget; transitions read the same
     cache, so a boundary frame cannot flash a different sky. */
  const KB_BG_HZ = 15;
  const kbBgCache = new Map();
  function kbDrawBg(g, w, h, def, clock) {
    const t = clock || 0;
    const bucket = Math.floor(t * KB_BG_HZ);
    const key = def.motion + '|' + w + 'x' + h;
    let rec = kbBgCache.get(key);
    if (!rec || rec.canvas.width !== Math.max(1, Math.round(w)) || rec.canvas.height !== Math.max(1, Math.round(h))) {
      const canvas = document.createElement('canvas');
      canvas.width = Math.max(1, Math.round(w));
      canvas.height = Math.max(1, Math.round(h));
      rec = { canvas: canvas, ctx: canvas.getContext('2d'), bucket: -1 };
      kbBgCache.set(key, rec);
      if (kbBgCache.size > 6) {
        const first = kbBgCache.keys().next().value;
        if (first && first !== key) kbBgCache.delete(first);
      }
    }
    if (rec.bucket !== bucket) {
      const c = rec.ctx;
      c.setTransform(1, 0, 0, 1, 0, 0);
      c.globalAlpha = 1; c.globalCompositeOperation = 'source-over'; c.shadowBlur = 0;
      c.clearRect(0, 0, w, h);
      kbRenderBg(c, w, h, def, t);
      rec.bucket = bucket;
    }
    g.drawImage(rec.canvas, 0, 0, w, h);
  }

  function kbDrawFrame(g, def) {
    const a = def.accent, line = def.line, k = 1;
    g.save();
    if (def.motion === 'royal' || def.motion === 'golden') {
      g.strokeStyle = kbRgba(a, .34); g.lineWidth = 1.5 * k;
      g.strokeRect(20, 20, 680, 1240);
      g.strokeStyle = kbRgba(a, .15); g.lineWidth = 1 * k;
      g.strokeRect(27, 27, 666, 1226);
      [[20, 20], [700, 20], [20, 1260], [700, 1260]].forEach(p => {
        g.save(); g.translate(p[0], p[1]); g.rotate(Math.PI / 4);
        g.fillStyle = kbRgba(a, .55); g.fillRect(-5, -5, 10, 10); g.restore();
      });
      g.strokeStyle = kbRgba(a, .30); g.lineWidth = 1.4 * k;
      g.beginPath(); g.arc(360, 20, 26, 0, Math.PI); g.stroke();
    } else if (def.motion === 'cosmic') {
      g.strokeStyle = kbRgba(a, .24); g.lineWidth = 1.4 * k;
      kbRR(g, 16, 16, 688, 1248, 34); g.stroke();
      g.strokeStyle = 'rgba(110,231,255,.10)'; g.lineWidth = 1 * k;
      kbRR(g, 23, 23, 674, 1234, 29); g.stroke();
      /* No corner brackets, edge ticks or bottom diamond: those read as
         measurement marks in the exported frame. Preview and export stay a
         clean poster with only the two hairline frame strokes. */
      g.save(); g.translate(360, 16);
      for (let i = 1; i <= 3; i++) {
        g.strokeStyle = kbRgba(a, .12 + i * .03); g.lineWidth = 1 * k;
        g.beginPath(); g.ellipse(0, 0, 26 + i * 13, 5 + i * 2.4, 0, 0, 7); g.stroke();
      }
      g.fillStyle = kbRgba(def.accent2, .5);
      g.beginPath(); g.arc(0, 0, 2.4, 0, 7); g.fill();
      g.restore();
    } else if (def.motion === 'glass') {
      g.fillStyle = 'rgba(255,255,255,.13)'; g.strokeStyle = 'rgba(255,255,255,.55)'; g.lineWidth = 1.2 * k;
      kbRR(g, 17, 17, 686, 1246, 30); g.fill(); g.stroke();
      g.strokeStyle = 'rgba(255,255,255,.32)'; g.beginPath(); g.moveTo(42, 23); g.lineTo(678, 23); g.stroke();
    } else if (def.motion === 'cinematic') {
      g.fillStyle = 'rgba(0,0,0,.9)'; g.fillRect(0, 0, 720, 36); g.fillRect(0, 1244, 720, 36);
      g.strokeStyle = 'rgba(232,176,75,.32)'; g.lineWidth = 1.2 * k;
      g.strokeRect(38, 38, 644, 1204);
      g.strokeStyle = 'rgba(255,255,255,.10)'; g.strokeRect(43, 43, 634, 1194);
    } else if (def.motion === 'neon' || def.motion === 'nextgen') {
      const c = def.motion === 'neon' ? a : '#a3e635';
      g.strokeStyle = kbRgba(c, .5); g.lineWidth = 2 * k;
      [[28, 28, 1, 1], [692, 28, -1, 1], [28, 1252, 1, -1], [692, 1252, -1, -1]].forEach(q => {
        g.beginPath(); g.moveTo(q[0], q[1] + q[3] * 26); g.lineTo(q[0], q[1]); g.lineTo(q[0] + q[2] * 26, q[1]); g.stroke();
      });
      g.strokeStyle = kbRgba(c, .13); g.lineWidth = 1 * k;
      for (let y = 210; y < 1080; y += 34) { g.beginPath(); g.moveTo(24, y); g.lineTo(30, y); g.stroke(); g.beginPath(); g.moveTo(690, y); g.lineTo(696, y); g.stroke(); }
    } else if (def.motion === 'minimal') {
      g.strokeStyle = 'rgba(31,26,20,.22)'; g.lineWidth = 1 * k;
      g.beginPath(); g.moveTo(46, 24); g.lineTo(674, 24); g.stroke();
      g.beginPath(); g.moveTo(46, 1256); g.lineTo(674, 1256); g.stroke();
      g.fillStyle = 'rgba(184,134,59,.7)'; g.fillRect(46, 24, 38, 2);
    } else if (def.motion === 'ancient') {
      g.strokeStyle = 'rgba(127,29,29,.28)'; g.lineWidth = 1.4 * k;
      g.strokeRect(20, 20, 680, 1240);
      g.setLineDash([5 * k, 7 * k]); g.strokeStyle = 'rgba(127,29,29,.16)';
      g.strokeRect(28, 28, 664, 1224); g.setLineDash([]);
      [[20, 20], [700, 20], [20, 1260], [700, 1260]].forEach(p => { g.fillStyle = 'rgba(127,29,29,.45)'; g.fillRect(p[0] - 4, p[1] - 4, 8, 8); });
    } else if (def.motion === 'nebula') {
      g.strokeStyle = kbRgba(a, .30); g.lineWidth = 1.4 * k;
      kbRR(g, 16, 16, 688, 1248, 34); g.stroke();
      g.strokeStyle = 'rgba(255,255,255,.12)'; g.lineWidth = 1 * k;
      kbRR(g, 23, 23, 674, 1234, 29); g.stroke();
      const gl = g.createLinearGradient(0, 16, 0, 210);
      gl.addColorStop(0, 'rgba(233,213,255,.14)'); gl.addColorStop(1, 'rgba(233,213,255,0)');
      g.fillStyle = gl; g.fillRect(30, 16, 660, 194);
      g.fillStyle = kbRgba(def.accent2, .22);
      g.fillRect(150, 21, 420, 2);
      g.fillStyle = kbRgba(a, .20);
      kbRR(g, 8, 250, 7, 300, 3.5); g.fill();
      kbRR(g, 705, 690, 7, 300, 3.5); g.fill();
    } else if (def.motion === 'vedic') {
      g.fillStyle = 'rgba(138,28,28,.82)';
      g.fillRect(20, 20, 680, 3); g.fillRect(20, 1257, 680, 3);
      g.strokeStyle = 'rgba(138,28,28,.42)'; g.lineWidth = 1.6 * k;
      g.strokeRect(24, 24, 672, 1232);
      g.setLineDash([4 * k, 6 * k]); g.strokeStyle = 'rgba(161,98,7,.30)'; g.lineWidth = 1 * k;
      g.strokeRect(32, 32, 656, 1216); g.setLineDash([]);
      [[24, 24], [696, 24], [24, 1256], [696, 1256]].forEach(p => {
        g.save(); g.translate(p[0], p[1]); g.rotate(Math.PI / 4);
        g.fillStyle = 'rgba(138,28,28,.62)'; g.fillRect(-4, -4, 8, 8); g.restore();
      });
      g.fillStyle = 'rgba(161,98,7,.55)';
      g.beginPath(); g.arc(360, 26, 4.5, 0, 7); g.fill();
      g.beginPath(); g.arc(360, 1254, 4.5, 0, 7); g.fill();
    } else if (def.motion === 'orbit') {
      const c = def.accent;
      g.strokeStyle = kbRgba(c, .62); g.lineWidth = 2.2 * k;
      [[24, 24, 1, 1], [696, 24, -1, 1], [24, 1256, 1, -1], [696, 1256, -1, -1]].forEach(q => {
        g.beginPath(); g.moveTo(q[0], q[1] + q[3] * 34); g.lineTo(q[0], q[1]); g.lineTo(q[0] + q[2] * 34, q[1]); g.stroke();
      });
      g.fillStyle = kbRgba(c, .7);
      for (let x = 88; x <= 632; x += 34) g.fillRect(x, 24, 12, 3);
      g.fillStyle = kbRgba(def.accent2, .45);
      for (let y = 240; y <= 1040; y += 34) g.fillRect(24, y, 3, 12);
      g.strokeStyle = kbRgba(def.accent2, .18); g.lineWidth = 1 * k;
      g.beginPath(); g.moveTo(24, 1088); g.lineTo(696, 1088); g.stroke();
      g.fillStyle = kbRgba(c, .55);
      g.fillRect(24, 1088, 96, 2.4);
    } else if (def.motion === 'floating') {
      g.fillStyle = 'rgba(167,139,250,.055)'; g.strokeStyle = 'rgba(167,139,250,.16)'; g.lineWidth = 1 * k;
      kbRR(g, 12, 160, 7, 960, 3); g.fill(); g.stroke();
      kbRR(g, 701, 160, 7, 960, 3); g.fill(); g.stroke();
    } else {
      g.strokeStyle = kbRgba(a, .18); g.lineWidth = 1 * k;
      g.strokeRect(22, 22, 676, 1236);
      g.strokeStyle = kbRgba(a, .4); g.beginPath(); g.moveTo(46, 22); g.lineTo(150, 22); g.stroke();
    }
    g.restore();
  }

  function kbDrawHeader(g, scene, def, alpha) {
    /* Template chrome only. Card numbers and the old top-left caption are
       intentionally gone: every card already carries its own real title,
       and a second label would duplicate it. */
    g.save();
    g.globalAlpha = g.globalAlpha * clamp(alpha, 0, 1);
    g.strokeStyle = kbRgba(def.accent, .12); g.lineWidth = 1;
    g.beginPath(); g.moveTo(46, 130); g.lineTo(674, 130); g.stroke();
    g.strokeStyle = kbRgba(def.accent, .72); g.lineWidth = 2.4;
    g.beginPath(); g.moveTo(46, 130); g.lineTo(136, 130); g.stroke();
    if (def.motion === 'royal' || def.motion === 'golden') {
      g.fillStyle = kbRgba(def.accent, .7);
      g.save(); g.translate(360, 130); g.rotate(Math.PI / 4); g.fillRect(-3, -3, 6, 6); g.restore();
    } else if (def.motion === 'cosmic') {
      const gl = g.createLinearGradient(46, 0, 674, 0);
      gl.addColorStop(0, kbRgba(def.accent, 0));
      gl.addColorStop(.18, kbRgba(def.accent, .55));
      gl.addColorStop(.5, kbRgba(def.accent2, .5));
      gl.addColorStop(.82, kbRgba(def.accent, .55));
      gl.addColorStop(1, kbRgba(def.accent, 0));
      g.strokeStyle = gl; g.lineWidth = 1.2;
      g.beginPath(); g.moveTo(46, 130); g.lineTo(674, 130); g.stroke();
      g.fillStyle = kbRgba(def.accent, .9);
      g.save(); g.translate(360, 130); g.rotate(Math.PI / 4); g.fillRect(-3.2, -3.2, 6.4, 6.4); g.restore();
      g.fillStyle = kbRgba(def.accent2, .55);
      [120, 156, 564, 600].forEach(x => { g.beginPath(); g.arc(x, 130, 1.7, 0, 7); g.fill(); });
    } else if (def.motion === 'nebula') {
      const gl = g.createLinearGradient(46, 0, 674, 0);
      gl.addColorStop(0, 'rgba(233,213,255,0)');
      gl.addColorStop(.24, kbRgba(def.accent, .42));
      gl.addColorStop(.55, kbRgba(def.accent2, .40));
      gl.addColorStop(.82, kbRgba(def.accent, .38));
      gl.addColorStop(1, 'rgba(233,213,255,0)');
      g.strokeStyle = gl; g.lineWidth = 1.1;
      g.beginPath(); g.moveTo(46, 130); g.lineTo(674, 130); g.stroke();
      g.fillStyle = kbRgba(def.accent, .75);
      [196, 236, 484, 524].forEach((x, i) => {
        g.beginPath(); g.arc(x, 130, 1.5 + (i % 2) * .6, 0, 7); g.fill();
      });
      g.fillStyle = kbRgba(def.accent2, .55);
      g.beginPath(); g.arc(360, 130, 2.2, 0, 7); g.fill();
      g.strokeStyle = 'rgba(255,255,255,.16)'; g.lineWidth = 1;
      kbRR(g, 300, 126, 120, 8, 4); g.stroke();
    } else if (def.motion === 'vedic') {
      g.strokeStyle = 'rgba(138,28,28,.62)'; g.lineWidth = 1.6;
      g.beginPath(); g.moveTo(46, 130); g.lineTo(674, 130); g.stroke();
      g.strokeStyle = 'rgba(161,98,7,.34)'; g.lineWidth = 1;
      g.beginPath(); g.moveTo(46, 134); g.lineTo(674, 134); g.stroke();
      g.fillStyle = 'rgba(138,28,28,.62)';
      [46, 674].forEach(x => { g.save(); g.translate(x, 130); g.rotate(Math.PI / 4); g.fillRect(-2.6, -2.6, 5.2, 5.2); g.restore(); });
      g.save(); g.translate(360, 132); g.rotate(Math.PI / 4);
      g.strokeStyle = 'rgba(161,98,7,.55)'; g.lineWidth = 1.1; g.strokeRect(-3.4, -3.4, 6.8, 6.8); g.restore();
    } else if (def.motion === 'orbit') {
      g.strokeStyle = kbRgba(def.accent2, .34); g.lineWidth = 1.2;
      g.beginPath(); g.moveTo(46, 130); g.lineTo(674, 130); g.stroke();
      g.fillStyle = kbRgba(def.accent, .62);
      for (let x = 70; x <= 646; x += 24) g.fillRect(x, 128, 12, 2);
      g.fillStyle = kbRgba(def.accent2, .55);
      g.fillRect(46, 130, 90, 2);
      g.fillRect(584, 130, 90, 2);
      g.fillStyle = 'rgba(2,14,16,.92)'; g.fillRect(314, 122, 92, 16);
      g.fillStyle = kbRgba(def.accent, .85);
      g.font = '700 8px "' + def.font + '","Noto Sans Devanagari",sans-serif';
      g.textAlign = 'center'; g.fillText('ORBIT · LIVE', 360, 133); g.textAlign = 'left';
    }
    g.restore();
  }

  function kbDrawFooter(g, scene, def, alpha, progress) {
    g.save();
    g.globalAlpha = g.globalAlpha * clamp(alpha, 0, 1);
    g.textBaseline = 'alphabetic'; g.textAlign = 'left';
    g.strokeStyle = kbRgba(def.accent, .12); g.lineWidth = 1;
    g.beginPath(); g.moveTo(46, 1198); g.lineTo(674, 1198); g.stroke();
    g.fillStyle = kbRgba(def.accent, .16); g.fillRect(46, 1191, 628, 2);
    g.fillStyle = kbRgba(def.accent, .9); g.fillRect(46, 1191, 628 * clamp(progress || 0), 2);
    g.font = '500 10.5px "' + def.font + '","Noto Sans Devanagari",sans-serif';
    g.fillStyle = def.mut;
    g.fillText('Kundali-Desktop · वास्तविक गणना', 46, 1218);
    g.textAlign = 'right';
    g.fillText(kbEllipsis(g, scene.date || '', 300), 674, 1218);
    g.textAlign = 'left';
    g.restore();
  }

  /* ── model composition layer ─────────────────────────────────────
     The four Automatic models share one data pipeline and one renderer.
     Each model gets its own composition language here: Nebula floats
     asymmetric glass panes behind element groups, Vedic turns the card
     into a ruled ledger page, and Orbit wraps groups in HUD brackets.
     Nothing in this layer moves or resizes an element box, so text
     accuracy, Timeline editing and privacy rectangles stay untouched. */
  function kbZones(scene, card) {
    const boxes = [];
    (scene.els || []).forEach(e => {
      if (!e || !e.box || e.visible === false) return;
      const x = +e.box[0], y = +e.box[1], w = +e.box[2], h = +e.box[3];
      if (!(w > 0 && h > 0)) return;
      boxes.push({ x: x, y: y, w: w, h: h });
    });
    boxes.sort((a, b) => a.y - b.y || a.x - b.x);
    const groups = [];
    boxes.forEach(b => {
      const hit = groups.find(gr => Math.min(gr.y + gr.h, b.y + b.h) - Math.max(gr.y, b.y) > 10);
      if (hit) {
        const x2 = Math.max(hit.x + hit.w, b.x + b.w), y2 = Math.max(hit.y + hit.h, b.y + b.h);
        hit.x = Math.min(hit.x, b.x); hit.y = Math.min(hit.y, b.y);
        hit.w = x2 - hit.x; hit.h = y2 - hit.y;
      } else {
        groups.push({ x: b.x, y: b.y, w: b.w, h: b.h });
      }
    });
    const inset = 7, top = card.y + 10, bot = card.y + card.h - 10;
    return groups.map(z => {
      const x = Math.max(card.x + 8, z.x - inset);
      const y = Math.max(top, z.y - 6);
      const x2 = Math.min(card.x + card.w - 8, z.x + z.w + inset);
      const y2 = Math.min(bot, z.y + z.h + 6);
      return { x: x, y: y, w: Math.max(0, x2 - x), h: Math.max(0, y2 - y) };
    }).filter(z => z.w > 24 && z.h > 14).sort((a, b) => a.y - b.y);
  }

  function kbCutBox(g, x, y, w, h, c) {
    c = Math.max(0, Math.min(c, w / 4, h / 4));
    g.beginPath();
    g.moveTo(x + c, y); g.lineTo(x + w - c, y); g.lineTo(x + w, y + c);
    g.lineTo(x + w, y + h - c); g.lineTo(x + w - c, y + h); g.lineTo(x + c, y + h);
    g.lineTo(x, y + h - c); g.lineTo(x, y + c); g.closePath();
  }

  function kbCornerBrackets(g, x, y, w, h, len, color, lw) {
    g.strokeStyle = color; g.lineWidth = lw || 1.6;
    [[x, y, 1, 1], [x + w, y, -1, 1], [x, y + h, 1, -1], [x + w, y + h, -1, -1]].forEach(p => {
      g.beginPath(); g.moveTo(p[0], p[1] + p[3] * len); g.lineTo(p[0], p[1]);
      g.lineTo(p[0] + p[2] * len, p[1]); g.stroke();
    });
  }

  function kbHeadBoards(scene, card) {
    let out = [];
    (scene.els || []).forEach(e => {
      if (e && e.el && e.el.type === 'heading' && e.visible !== false && e.box) {
        out.push({ x: +e.box[0], y: +e.box[1], w: +e.box[2], h: +e.box[3] });
      }
    });
    if (!out.length && scene.el && scene.el.type === 'heading') {
      out.push({ x: card.ix, y: card.iy, w: card.iw, h: card.ih });
    }
    return out.slice(0, 4);
  }

  function kbDrawModelBackdrop(g, card, def, lt, ep) {
    const m = def.motion;
    if (m === 'nebula') {
      const e = eo(clamp(ep == null ? 1 : ep));
      const off = 12 + (1 - e) * 18;
      g.save();
      const b1 = g.createLinearGradient(card.x + off, card.y - off, card.x + card.w, card.y + card.h);
      b1.addColorStop(0, 'rgba(139,92,246,.20)');
      b1.addColorStop(.55, 'rgba(99,102,241,.10)');
      b1.addColorStop(1, 'rgba(34,211,238,.055)');
      g.fillStyle = b1;
      kbRR(g, card.x + off, card.y - off * .72, card.w, card.h, 32); g.fill();
      g.strokeStyle = 'rgba(233,213,255,.20)'; g.lineWidth = 1;
      kbRR(g, card.x + off, card.y - off * .72, card.w, card.h, 32); g.stroke();
      const b2 = g.createLinearGradient(card.x, card.y, card.x + card.w, card.y + card.h);
      b2.addColorStop(0, 'rgba(34,211,238,.045)');
      b2.addColorStop(1, 'rgba(236,72,153,.075)');
      g.fillStyle = b2;
      kbRR(g, card.x - off * .52, card.y + off * .62, card.w, card.h, 30); g.fill();
      g.strokeStyle = 'rgba(196,181,253,.12)'; g.lineWidth = 1;
      kbRR(g, card.x - off * .52, card.y + off * .62, card.w, card.h, 30); g.stroke();
      g.restore();
    } else if (m === 'vedic') {
      g.save();
      g.fillStyle = 'rgba(231,207,166,.98)';
      kbRR(g, card.x + 7, card.y + 8, card.w - 1, card.h - 2, 5); g.fill();
      g.strokeStyle = 'rgba(120,80,40,.30)'; g.lineWidth = 1;
      kbRR(g, card.x + 7, card.y + 8, card.w - 1, card.h - 2, 5); g.stroke();
      g.fillStyle = 'rgba(120,80,40,.20)';
      const rnd = kbSeed(def.seed + 5);
      for (let i = 0; i < 18; i++) {
        const yy = card.y + 22 + rnd() * (card.h - 44);
        g.fillRect(card.x + card.w + 3 + (rnd() > .5 ? 0 : 1), yy, 1, 2 + rnd() * 3);
      }
      g.restore();
    } else if (m === 'orbit') {
      g.save();
      const c = def.accent, c2 = def.accent2;
      kbCutBox(g, card.x - 10, card.y - 10, card.w + 20, card.h + 20, 14);
      g.strokeStyle = kbRgba(c2, .20); g.lineWidth = 1.2; g.stroke();
      kbCutBox(g, card.x - 15, card.y - 15, card.w + 30, card.h + 30, 18);
      g.strokeStyle = kbRgba(c, .10); g.lineWidth = 1; g.stroke();
      g.fillStyle = kbRgba(c, .70);
      g.fillRect(card.x - 10, card.y + 110, 3, 54);
      g.fillRect(card.x + card.w + 7, card.y + card.h - 164, 3, 54);
      g.fillStyle = kbRgba(c2, .42);
      for (let i = 0; i < 12; i++) g.fillRect(card.x - 10 + 34 + i * 46, card.y - 10, 16, 2);
      g.fillStyle = 'rgba(2,14,16,.92)';
      g.fillRect(card.x - 9, card.y + 37, 50, 16);
      g.fillStyle = kbRgba(c, .86);
      g.font = '700 8px "' + def.font + '","Noto Sans Devanagari",sans-serif';
      g.textAlign = 'center'; g.fillText('SOL · HUD', card.x + 16, card.y + 48); g.textAlign = 'left';
      g.restore();
    }
  }

  function kbDrawModelInterior(g, scene, card, def, lt, ep) {
    const m = def.motion;
    if (m === 'cosmic') return;
    const zones = kbZones(scene, card);
    const heads = kbHeadBoards(scene, card);
    if (m === 'nebula') {
      g.save();
      const aura = g.createRadialGradient(card.x + card.w * .80, card.y + card.h * .14, 0, card.x + card.w * .80, card.y + card.h * .14, card.w * .86);
      aura.addColorStop(0, 'rgba(139,92,246,.20)');
      aura.addColorStop(.42, 'rgba(34,211,238,.075)');
      aura.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = aura; g.fillRect(card.x, card.y, card.w, card.h);
      zones.forEach((z, i) => {
        const shift = i % 2 ? 7 : -3;
        const px = z.x + shift, pw = z.w - shift;
        const gr = g.createLinearGradient(px, z.y, px + pw, z.y + z.h);
        gr.addColorStop(0, 'rgba(255,255,255,.075)');
        gr.addColorStop(.55, 'rgba(196,181,253,.032)');
        gr.addColorStop(1, 'rgba(34,211,238,.025)');
        g.fillStyle = gr;
        kbRR(g, px, z.y, pw, z.h, 15); g.fill();
        g.strokeStyle = 'rgba(255,255,255,.13)'; g.lineWidth = 1;
        kbRR(g, px, z.y, pw, z.h, 15); g.stroke();
        g.fillStyle = 'rgba(255,255,255,.30)';
        kbRR(g, px + 14, z.y + 1, Math.min(96, pw - 28), 1.4, 1); g.fill();
        g.fillStyle = kbRgba(def.accent2, .58);
        g.beginPath(); g.arc(px + pw - 13, z.y + 12, 2.1, 0, 7); g.fill();
      });
      heads.forEach((h, i) => {
        const gl = g.createRadialGradient(h.x + h.w * .5, h.y + h.h * .5, 0, h.x + h.w * .5, h.y + h.h * .5, h.w * .52);
        gl.addColorStop(0, 'rgba(233,213,255,.16)');
        gl.addColorStop(1, 'rgba(233,213,255,0)');
        g.fillStyle = gl; g.fillRect(h.x - 30, h.y - 18, h.w + 60, h.h + 36);
        const y = h.y + h.h - 2;
        const line = g.createLinearGradient(h.x, y, h.x + Math.min(150, h.w), y);
        line.addColorStop(0, kbRgba(def.accent, .52));
        line.addColorStop(.65, kbRgba(def.accent2, .30));
        line.addColorStop(1, 'rgba(233,213,255,0)');
        g.fillStyle = line; g.fillRect(h.x, y, Math.min(132, h.w), 1.5);
        for (let d = 0; d < 3; d++) {
          g.fillStyle = 'rgba(233,213,255,' + (.42 - d * .10) + ')';
          g.beginPath(); g.arc(h.x + Math.min(132, h.w) + 8 + d * 5.5, y + .5, 1.35, 0, 7); g.fill();
        }
      });
      g.restore();
    } else if (m === 'vedic') {
      g.save();
      const wash = g.createLinearGradient(card.x, card.y, card.x + card.w, card.y + card.h);
      wash.addColorStop(0, 'rgba(255,251,239,.56)');
      wash.addColorStop(.55, 'rgba(251,241,220,.22)');
      wash.addColorStop(1, 'rgba(226,198,154,.36)');
      g.fillStyle = wash; g.fillRect(card.x, card.y, card.w, card.h);
      const rnd = kbSeed(def.seed + 11);
      for (let i = 0; i < 120; i++) {
        g.fillStyle = 'rgba(96,62,30,' + (.012 + rnd() * .028) + ')';
        g.fillRect(card.x + 8 + rnd() * (card.w - 16), card.y + 10 + rnd() * (card.h - 20), .7 + rnd() * 1.8, .7);
      }
      g.strokeStyle = 'rgba(120,80,40,.045)'; g.lineWidth = 1;
      for (let y = card.y + 44; y < card.y + card.h - 34; y += 25) {
        g.beginPath(); g.moveTo(card.x + 34, y); g.lineTo(card.x + card.w - 20, y); g.stroke();
      }
      g.strokeStyle = 'rgba(138,28,28,.34)'; g.lineWidth = 1.2;
      g.beginPath(); g.moveTo(card.x + 13, card.y + 40); g.lineTo(card.x + 13, card.y + card.h - 40); g.stroke();
      g.strokeStyle = 'rgba(161,98,7,.22)'; g.lineWidth = 1;
      g.beginPath(); g.moveTo(card.x + 17, card.y + 40); g.lineTo(card.x + 17, card.y + card.h - 40); g.stroke();
      g.fillStyle = 'rgba(138,28,28,.28)';
      for (let y = card.y + 58; y < card.y + card.h - 50; y += 108) {
        g.beginPath(); g.arc(card.x + 10, y, 2.1, 0, 7); g.fill();
      }
      zones.forEach(z => {
        const y = z.y - 7;
        if (y < card.y + 34) return;
        g.strokeStyle = 'rgba(138,28,28,.20)'; g.lineWidth = 1;
        g.beginPath(); g.moveTo(card.x + 32, y); g.lineTo(card.x + card.w - 24, y); g.stroke();
        g.save(); g.translate(card.x + 30, y); g.rotate(Math.PI / 4);
        g.fillStyle = 'rgba(161,98,7,.42)'; g.fillRect(-2, -2, 4, 4); g.restore();
      });
      heads.forEach(h => {
        g.strokeStyle = 'rgba(138,28,28,.35)'; g.lineWidth = 1.1;
        g.beginPath(); g.moveTo(h.x, h.y + h.h - 1); g.lineTo(h.x + Math.min(158, h.w), h.y + h.h - 1); g.stroke();
        g.save(); g.translate(h.x - 7, h.y + h.h - 1); g.rotate(Math.PI / 4);
        g.fillStyle = 'rgba(138,28,28,.55)'; g.fillRect(-2.2, -2.2, 4.4, 4.4); g.restore();
      });
      g.textAlign = 'center';
      g.fillStyle = 'rgba(138,28,28,.50)';
      g.font = '600 9px "' + def.display + '","Noto Sans Devanagari",sans-serif';
      g.fillText('॥ ज्योतिष पत्र ॥', card.x + card.w / 2, card.y + 22);
      g.fillStyle = 'rgba(161,98,7,.28)';
      g.fillRect(card.x + card.w / 2 - 34, card.y + 27, 68, 1);
      g.fillStyle = 'rgba(138,28,28,.38)';
      g.font = '600 8.5px "' + def.font + '","Noto Sans Devanagari",sans-serif';
      g.textAlign = 'right';
      g.fillText('पत्र ' + kbNum(scene.no || 1), card.x + card.w - 24, card.y + card.h - 22);
      g.textAlign = 'left';
      g.restore();
    } else if (m === 'orbit') {
      g.save();
      g.strokeStyle = 'rgba(34,211,238,.035)'; g.lineWidth = 1;
      for (let x = card.x + 18; x < card.x + card.w - 8; x += 42) {
        g.beginPath(); g.moveTo(x, card.y + 8); g.lineTo(x, card.y + card.h - 8); g.stroke();
      }
      for (let y = card.y + 18; y < card.y + card.h - 8; y += 42) {
        g.beginPath(); g.moveTo(card.x + 8, y); g.lineTo(card.x + card.w - 8, y); g.stroke();
      }
      zones.forEach((z, i) => {
        kbCutBox(g, z.x + 2, z.y, z.w - 4, z.h, 7);
        g.fillStyle = 'rgba(2,18,21,.34)'; g.fill();
        g.strokeStyle = kbRgba(def.accent2, i === 0 ? .22 : .13); g.lineWidth = 1; g.stroke();
        kbCornerBrackets(g, z.x + 3, z.y + 2, z.w - 6, z.h - 4, 11, kbRgba(def.accent, .42), 1.3);
        g.fillStyle = kbRgba(def.accent2, .50);
        g.fillRect(z.x + 14, z.y + 6, Math.min(42, z.w - 28), 1);
      });
      const sy = card.y + 30 + ((lt * 34) % Math.max(80, card.h - 60));
      const sg = g.createLinearGradient(0, sy - 14, 0, sy + 14);
      sg.addColorStop(0, 'rgba(163,230,53,0)');
      sg.addColorStop(.5, 'rgba(163,230,53,.13)');
      sg.addColorStop(1, 'rgba(163,230,53,0)');
      g.fillStyle = sg; g.fillRect(card.x + 8, sy - 14, card.w - 16, 28);
      g.fillStyle = 'rgba(2,14,16,.90)';
      g.fillRect(card.x + 20, card.y + 13, card.w - 40, 17);
      g.fillStyle = kbRgba(def.accent, .92);
      g.font = '700 8px "' + def.font + '","Noto Sans Devanagari",sans-serif';
      g.textAlign = 'left';
      g.fillText('SOLAR · ORBIT', card.x + 27, card.y + 25);
      g.textAlign = 'right';
      g.fillStyle = kbRgba(def.accent2, .80);
      g.fillText('LIVE', card.x + card.w - 43, card.y + 25);
      g.textAlign = 'left';
      const blink = .35 + .55 * Math.abs(Math.sin(lt * 2.1));
      g.fillStyle = kbRgba(def.accent2, blink);
      g.beginPath(); g.arc(card.x + card.w - 34, card.y + 21.5, 2.4, 0, 7); g.fill();
      heads.forEach(h => {
        kbCornerBrackets(g, h.x - 4, h.y - 3, h.w + 8, h.h + 6, 9, kbRgba(def.accent, .50), 1.2);
        g.fillStyle = 'rgba(2,14,16,.92)';
        g.fillRect(h.x + h.w - 58, h.y - 8, 58, 12);
        g.fillStyle = kbRgba(def.accent2, .76);
        g.font = '700 7.5px "' + def.font + '","Noto Sans Devanagari",sans-serif';
        g.textAlign = 'right';
        g.fillText('SEC ' + ('0' + (scene.no || 1)).slice(-2), h.x + h.w - 6, h.y + 1.5);
        g.textAlign = 'left';
      });
      g.restore();
    }
  }

  function kbDrawCard(g, x, y, w, h, def, set, alpha) {
    const r = set.radius != null ? set.radius : def.radius;
    const bg = set.bg || 'auto';
    g.save();
    g.globalAlpha = g.globalAlpha * clamp(alpha, 0, 1);
    if (bg !== 'none') {
      g.shadowColor = KB_LIGHT.has(def.motion) ? 'rgba(40,30,15,.22)' : 'rgba(0,0,0,.62)';
      g.shadowBlur = set.shadow ? 38 : 0;
      g.shadowOffsetY = set.shadow ? 16 : 0;
      if (bg === 'glass') {
        if (def.motion === 'cosmic') {
          /* Deep-space glass, not white glass: keeps the card readable over
             the nebula while still letting a hint of the sky through. */
          const cg = g.createLinearGradient(x, y, x + w * .3, y + h);
          cg.addColorStop(0, 'rgba(16,34,68,.94)');
          cg.addColorStop(.55, 'rgba(8,20,44,.95)');
          cg.addColorStop(1, 'rgba(4,10,24,.97)');
          g.fillStyle = cg;
        } else {
          g.fillStyle = KB_LIGHT.has(def.motion) ? 'rgba(255,255,255,.56)' : 'rgba(255,255,255,.13)';
        }
      }
      else if (bg === 'dark') g.fillStyle = 'rgba(4,8,15,.90)';
      else if (bg === 'light') g.fillStyle = 'rgba(255,255,255,.93)';
      else g.fillStyle = def.card;
      kbRR(g, x, y, w, h, r); g.fill();
      g.shadowBlur = 0; g.shadowOffsetY = 0;
      if (set.border !== false) {
        g.strokeStyle = def.motion === 'cosmic' ? 'rgba(246,211,101,.42)' : (bg === 'glass' ? 'rgba(255,255,255,.58)' : def.line);
        g.lineWidth = 1.5;
        kbRR(g, x, y, w, h, r); g.stroke();
      }
      g.strokeStyle = KB_LIGHT.has(def.motion) ? 'rgba(255,255,255,.45)' : 'rgba(255,255,255,.12)';
      g.lineWidth = 1;
      g.beginPath(); g.moveTo(x + 22, y + 1.2); g.lineTo(x + w - 22, y + 1.2); g.stroke();
    }
    if (bg !== 'none' && (def.motion === 'royal' || def.motion === 'golden')) {
      g.strokeStyle = kbRgba(def.accent, .24); g.lineWidth = 1;
      kbRR(g, x + 8, y + 8, w - 16, h - 16, Math.max(2, r - 6)); g.stroke();
    }
    if (bg !== 'none' && (def.motion === 'neon' || def.motion === 'nextgen')) {
      const c = def.motion === 'neon' ? def.accent : '#a3e635';
      g.strokeStyle = kbRgba(c, .55); g.lineWidth = 1.8;
      const b = 14;
      [[x + 10, y + 10, 1, 1], [x + w - 10, y + 10, -1, 1], [x + 10, y + h - 10, 1, -1], [x + w - 10, y + h - 10, -1, -1]].forEach(q => {
        g.beginPath(); g.moveTo(q[0], q[1] + q[3] * b); g.lineTo(q[0], q[1]); g.lineTo(q[0] + q[2] * b, q[1]); g.stroke();
      });
    }
    if (bg !== 'none' && def.motion === 'ancient') {
      g.setLineDash([4, 6]); g.strokeStyle = 'rgba(127,29,29,.18)'; g.lineWidth = 1;
      kbRR(g, x + 9, y + 9, w - 18, h - 18, Math.max(1, r - 4)); g.stroke(); g.setLineDash([]);
    }
    if (bg !== 'none' && def.motion === 'minimal') {
      g.fillStyle = 'rgba(184,134,59,.8)'; g.fillRect(x, y + 18, 2, 34);
    }
    if (bg !== 'none' && def.motion === 'nebula') {
      g.save();
      kbRR(g, x, y, w, h, r); g.clip();
      const sh = g.createLinearGradient(0, y, 0, y + h * .42);
      sh.addColorStop(0, 'rgba(233,213,255,.12)'); sh.addColorStop(1, 'rgba(233,213,255,0)');
      g.fillStyle = sh; g.fillRect(x, y, w, h * .42);
      g.restore();
      g.strokeStyle = 'rgba(255,255,255,.20)'; g.lineWidth = 1;
      kbRR(g, x + 6, y + 6, w - 12, h - 12, Math.max(2, r - 6)); g.stroke();
      g.fillStyle = kbRgba(def.accent2, .65);
      g.beginPath(); g.arc(x + w - 24, y + 22, 3.2, 0, 7); g.fill();
    }
    if (bg !== 'none' && def.motion === 'cosmic') {
      g.save();
      kbRR(g, x, y, w, h, r); g.clip();
      const sheen = g.createLinearGradient(0, y, 0, y + h * .52);
      sheen.addColorStop(0, 'rgba(110,231,255,.10)');
      sheen.addColorStop(.45, 'rgba(246,211,101,.05)');
      sheen.addColorStop(1, 'rgba(0,0,0,0)');
      g.fillStyle = sheen; g.fillRect(x, y, w, h * .52);
      const rnd = kbSeed(83);
      for (let i = 0; i < 34; i++) {
        const sx = x + rnd() * w, sy = y + rnd() * h * .9;
        g.fillStyle = 'rgba(214,232,255,' + (.03 + rnd() * .13) + ')';
        g.beginPath(); g.arc(sx, sy, (.5 + rnd() * .9), 0, 7); g.fill();
      }
      /* Zodiac wheel watermark, very faint, upper-right. */
      g.save(); g.translate(x + w - 74, y + 86); g.rotate(-.2);
      g.strokeStyle = 'rgba(246,211,101,.10)'; g.lineWidth = 1;
      g.beginPath(); g.arc(0, 0, 52, 0, 7); g.stroke();
      g.beginPath(); g.arc(0, 0, 38, 0, 7); g.stroke();
      for (let i = 0; i < 12; i++) {
        const a = i * Math.PI / 6;
        g.beginPath(); g.moveTo(Math.cos(a) * 38, Math.sin(a) * 38); g.lineTo(Math.cos(a) * 52, Math.sin(a) * 52); g.stroke();
        if (i % 2 === 0) {
          g.fillStyle = 'rgba(246,211,101,.10)';
          g.beginPath(); g.arc(Math.cos(a) * 45, Math.sin(a) * 45, 1.8, 0, 7); g.fill();
        }
      }
      g.restore();
      g.restore();
      /* One clean gold hairline; no corner brackets, which looked like crop
         or measurement marks in the final frame. */
      g.strokeStyle = kbRgba(def.accent, .20); g.lineWidth = 1;
      kbRR(g, x + 8, y + 8, w - 16, h - 16, Math.max(3, r - 6)); g.stroke();
      g.fillStyle = kbRgba(def.accent2, .35);
      g.fillRect(x + w / 2 - 26, y + 1, 52, 2);
    }
    if (bg !== 'none' && def.motion === 'vedic') {
      g.strokeStyle = 'rgba(138,28,28,.48)'; g.lineWidth = 1.3;
      kbRR(g, x + 7, y + 7, w - 14, h - 14, Math.max(1, r - 3)); g.stroke();
      g.strokeStyle = 'rgba(161,98,7,.28)'; g.lineWidth = 1;
      kbRR(g, x + 12, y + 12, w - 24, h - 24, Math.max(1, r - 5)); g.stroke();
      g.fillStyle = 'rgba(138,28,28,.55)';
      [[x + 7, y + 7], [x + w - 7, y + 7], [x + 7, y + h - 7], [x + w - 7, y + h - 7]].forEach(p => {
        g.save(); g.translate(p[0], p[1]); g.rotate(Math.PI / 4); g.fillRect(-2.6, -2.6, 5.2, 5.2); g.restore();
      });
    }
    if (bg !== 'none' && def.motion === 'orbit') {
      const c = def.accent, b = 12;
      g.strokeStyle = kbRgba(c, .68); g.lineWidth = 1.8;
      [[x + 8, y + 8, 1, 1], [x + w - 8, y + 8, -1, 1], [x + 8, y + h - 8, 1, -1], [x + w - 8, y + h - 8, -1, -1]].forEach(q => {
        g.beginPath(); g.moveTo(q[0], q[1] + q[3] * b); g.lineTo(q[0], q[1]); g.lineTo(q[0] + q[2] * b, q[1]); g.stroke();
      });
      g.fillStyle = kbRgba(c, .82); g.fillRect(x, y + 20, 4, 64);
      g.fillStyle = kbRgba(def.accent2, .45);
      for (let tx = x + 22; tx < x + w - 22; tx += 18) g.fillRect(tx, y + 8, 7, 2);
      g.strokeStyle = kbRgba(def.accent2, .10); g.lineWidth = 1;
      for (let ty = y + 40; ty < y + h - 20; ty += 26) { g.beginPath(); g.moveTo(x + w - 18, ty); g.lineTo(x + w - 12, ty); g.stroke(); }
    }
    g.restore();
  }

  function kbDrawElement(g, el, x, y, w, h, def, alpha) {
    const im = kbImgFor(el);
    g.save();
    g.globalAlpha = g.globalAlpha * clamp(alpha, 0, 1);
    if (im) {
      g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
      g.drawImage(im, x, y, w, h);
    } else {
      g.fillStyle = KB_LIGHT.has(def.motion) ? 'rgba(31,26,20,.05)' : 'rgba(255,255,255,.045)';
      kbRR(g, x, y, w, h, 12); g.fill();
      g.strokeStyle = kbRgba(def.accent, .18); g.setLineDash([6, 6]);
      kbRR(g, x + 4, y + 4, w - 8, h - 8, 10); g.stroke(); g.setLineDash([]);
      g.fillStyle = def.mut; g.textAlign = 'center'; g.textBaseline = 'middle';
      g.font = '600 15px "' + def.font + '","Noto Sans Devanagari",sans-serif';
      g.fillText(kbEllipsis(g, el.name || '', Math.max(40, w - 30)), x + w / 2, y + h / 2 - 8);
      g.font = '500 11px "' + def.font + '","Noto Sans Devanagari",sans-serif';
      g.fillText('रेण्डर हुँदै…', x + w / 2, y + h / 2 + 14);
      g.textAlign = 'left'; g.textBaseline = 'alphabetic';
    }
    g.restore();
  }

  const KB_FIT_CAP = { chart: 1.15, table: 1.06, graph: 1.12, report: 1.06, cards: 2.2, heading: 2.0, note: 1.9, banner: 1.8, art: 1.2, footer: 1.15, list: 1.2 };

  /* ─────────────────── multi-element card renderer ───────────────────
     Every card can hold any number of real rendered elements. Boxes are
     absolute 720×1280 design coordinates, so the live preview, the main
     timeline and the exported canvas all use exactly the same layout. */
  const KB_TEXT_SAFE = { heading: 1, note: 1, table: 1, report: 1, graph: 1, list: 1, cards: 1, chart: 1, banner: 1, footer: 1 };

  function kbIsMulti(scene) {
    return !!(scene && (scene.mode === 'auto' || scene.mode === 'free' || (scene.els && scene.els.length > 1) || scene.cardBox));
  }
  function kbSceneEls(scene) {
    if (!scene) return [];
    if (scene.els && scene.els.length) return scene.els.map(e => e && e.el).filter(Boolean);
    return scene.el ? [scene.el] : [];
  }
  function kbCardBox(scene) {
    const c = (scene && scene.cardBox) || [46, 168, 628, 1056];
    return { x: c[0], y: c[1], w: c[2], h: c[3] };
  }
  function kbSceneHitBoxes(scene) {
    if (!kbIsMulti(scene)) return [];
    const out = [];
    (scene.els || []).forEach((e, i) => {
      if (e.visible === false || !e.box) return;
      out.push({ i: i, x: e.box[0], y: e.box[1], w: e.box[2], h: e.box[3], el: e.el, item: e });
    });
    return out;
  }
  function kbElAlpha(a, p) {
    if (a === 'none' || a === 'reveal' || a === 'grow-x' || a === 'grow-y' || a === 'hud') return 1;
    return eo(clamp(p));
  }
  function kbMultiElState(e, lt, scene, idx, speed) {
    const a = e.anim || {};
    const base = a.dur != null ? +a.dur : (scene.set && scene.set.animDur != null ? +scene.set.animDur : .72);
    const dur = Math.max(.12, base / speed);
    /* Schema v2 stores the real entrance time on the element. Older saved
       scenes have no `in`/`out`, so the previous stagger formula is kept as a
       exact fallback (same result as Phase 8). */
    const delay = Math.max(0, e.in != null ? +e.in : ((a.delay || 0) + (a.stagger == null ? (scene.set && scene.set.stagger != null ? scene.set.stagger : .07) * idx : a.stagger)));
    const outAt = e.out != null ? +e.out : scene.dur;
    const entry = e.scroll ? 'none' : (a.entry || (e.el && e.el.type === 'art' ? 'depth' : 'rise'));
    const exit = a.exit || 'fade';
    const p = clamp((lt - delay) / dur);
    const xp = clamp((outAt - lt) / Math.max(.12, .6 / speed));
    let alpha = kbElAlpha(entry, p);
    /* Entry 'none' is used by the long document layer; an explicit in/out
       window still has to hide it outside its trim. */
    if (lt < delay - .001 || lt > outAt + .001) alpha = 0;
    if (exit !== 'none') alpha *= eo(xp);
    let dx = 0, dy = 0, sc = 1, clipX = 1, clipY = 1, rot = 0, soft = 0, scan = 0;
    switch (entry) {
      case 'fade': break;
      case 'rise': dy = (1 - eq(p)) * 28; break;
      case 'slide': dx = -(1 - eq(p)) * 42; break;
      case 'slide-r': dx = (1 - eq(p)) * 42; break;
      /* Nebula: a soft-focus entrance. Scaling and a low bloom stand in for
         a canvas blur, which would cost a full offscreen filter pass on every
         frame of a chart while adding no readable information. */
      case 'zoom': sc = .90 + .10 * eo(p); dy = (1 - eo(p)) * 8; break;
      case 'soft': sc = .962 + .038 * eo(p); soft = 1 - eo(p); break;
      case 'depth': sc = .965 + .035 * eo(p); break;
      /* Vedic: a ruled page is wiped in from its top edge, never flipped or
         rotated, so every letter keeps its square shape. */
      case 'reveal': clipY = eq(p); break;
      case 'grow-x': clipX = eq(p); break;
      case 'grow-y': clipY = eq(p); break;
      case 'hud': clipX = eq(p); break;
      case 'none': break;
      default: dy = (1 - eq(p)) * 22;
    }
    const kind = a.kind || 'none';
    if (kind === 'float') dy += Math.sin(lt * .9 + idx * 1.7) * 4;
    else if (kind === 'parallax') { dx += Math.sin(lt * .55 + idx) * 5; dy += Math.cos(lt * .5 + idx * .7) * 3; }
    else if (kind === 'scan' && e.el && (e.el.type === 'chart' || e.el.type === 'art' || e.el.type === 'graph')) {
      scan = ((lt * .42 + idx * .17) % 1.15);
    }
    if (a.rot && e.el && e.el.type === 'art') rot = (+a.rot || 0) * Math.PI / 180;
    if (a.opacity != null) alpha *= clamp(+a.opacity, 0, 1);
    if (a.scale != null) sc *= clamp(+a.scale, .2, 3);
    return { alpha: clamp(alpha, 0, 1), dx: dx, dy: dy, sc: sc, clipX: clipX, clipY: clipY, rot: rot, soft: soft, scan: scan };
  }

  /* ─────────────────── name privacy overlays ───────────────────
     Every name-bearing element carries privacy rectangles in its own SVG
     coordinate space. The rectangles follow the same animation, scroll and
     aspect-fit transform as the element, so the blur covers the name and
     nothing else. */
  const KB_PRIVACY_STYLES = { soft: 'नरम ब्लर', strong: 'गाढा ब्लर', pixel: 'पिक्सेलेट', bar: 'गोप्य बार' };
  const kbPixelCache = new WeakMap();
  function kbPixelImage(im) {
    let c = kbPixelCache.get(im);
    if (c) return c;
    const nw = im.naturalWidth || 320, nh = im.naturalHeight || 320;
    c = document.createElement('canvas');
    c.width = Math.max(8, Math.round(nw / 14));
    c.height = Math.max(8, Math.round(nh / 14));
    const p = c.getContext('2d');
    p.imageSmoothingEnabled = true;
    p.imageSmoothingQuality = 'high';
    p.drawImage(im, 0, 0, c.width, c.height);
    kbPixelCache.set(im, c);
    return c;
  }
  /* True privacy blur: sample the already-rendered pixels of the name zone,
     shrink them and paint them back. Drawing a blurred copy of the element
     image is not enough because the sharp text underneath still shows. */
  function kbBlurRect(g, x, y, w, h, factor) {
    const cv = g.canvas;
    const m = g.getTransform();
    const pt = (a, b) => ({ x: m.a * a + m.c * b + m.e, y: m.b * a + m.d * b + m.f });
    const q = [pt(x, y), pt(x + w, y), pt(x, y + h), pt(x + w, y + h)];
    const sx = Math.max(0, Math.floor(Math.min(q[0].x, q[1].x, q[2].x, q[3].x)));
    const sy = Math.max(0, Math.floor(Math.min(q[0].y, q[1].y, q[2].y, q[3].y)));
    const ex = Math.min(cv.width, Math.ceil(Math.max(q[0].x, q[1].x, q[2].x, q[3].x)));
    const ey = Math.min(cv.height, Math.ceil(Math.max(q[0].y, q[1].y, q[2].y, q[3].y)));
    const sw = ex - sx, sh = ey - sy;
    if (sw < 2 || sh < 2) return;
    const f = Math.max(2, factor || 10);
    const tw = Math.max(1, Math.round(sw / f));
    const th = Math.max(1, Math.round(sh / f));
    const tmp = document.createElement('canvas');
    tmp.width = tw; tmp.height = th;
    const tc = tmp.getContext('2d');
    tc.imageSmoothingEnabled = true; tc.imageSmoothingQuality = 'high';
    tc.drawImage(cv, sx, sy, sw, sh, 0, 0, tw, th);
    g.save();
    /* The scene may be scaled for a larger export canvas; sample and paint
       the blur in device pixels so the zone lands exactly on the name. */
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.beginPath(); g.rect(sx, sy, sw, sh); g.clip();
    g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
    g.drawImage(tmp, sx, sy, sw, sh);
    g.restore();
  }
  function kbPrivacyBar(g, rx, ry, rw, rh, label, def) {
    const light = KB_LIGHT.has(def.motion);
    const rad = Math.min(8, rh / 2);
    g.fillStyle = light ? '#fafcff' : '#071022';
    kbRR(g, rx, ry, rw, rh, rad); g.fill();
    g.strokeStyle = kbRgba(def.accent, .55); g.lineWidth = 1;
    kbRR(g, rx, ry, rw, rh, rad); g.stroke();
    if (rw > 30 && rh > 13) {
      g.fillStyle = light ? def.ink : def.mut;
      g.font = '700 ' + Math.min(12, Math.max(8, rh * .46)).toFixed(1) + 'px "' + def.font + '","Noto Sans Devanagari",sans-serif';
      g.textAlign = 'center'; g.textBaseline = 'middle';
      g.fillText('गोप्य', rx + rw / 2, ry + rh / 2 + 1);
      g.textAlign = 'left'; g.textBaseline = 'alphabetic';
    }
  }
  function kbPrivacyPlate(g, rx, ry, rw, rh, label, def, light) {
    const rad = Math.min(10, rh / 2);
    if (light) {
      const lg = g.createLinearGradient(0, ry, 0, ry + rh);
      lg.addColorStop(0, 'rgba(255,252,246,.96)'); lg.addColorStop(1, 'rgba(240,232,214,.96)');
      g.fillStyle = lg; kbRR(g, rx, ry, rw, rh, rad); g.fill();
      g.strokeStyle = 'rgba(138,28,28,.30)'; g.lineWidth = 1;
      kbRR(g, rx + .5, ry + .5, rw - 1, rh - 1, rad); g.stroke();
    } else {
      const dg = g.createLinearGradient(0, ry, 0, ry + rh);
      dg.addColorStop(0, 'rgba(14,26,50,.95)'); dg.addColorStop(1, 'rgba(4,9,20,.96)');
      g.fillStyle = dg; kbRR(g, rx, ry, rw, rh, rad); g.fill();
      g.strokeStyle = kbRgba(def.accent, .40); g.lineWidth = 1;
      kbRR(g, rx + .5, ry + .5, rw - 1, rh - 1, rad); g.stroke();
      g.fillStyle = kbRgba(def.accent, .45);
      g.fillRect(rx + rw * .28, ry + 1, rw * .44, 1.4);
    }
    const ink = light ? '#6b1d1d' : '#f6e6bf';
    const size = Math.min(13, Math.max(9, rh * .19));
    const iconW = size * 1.25, gapI = size * .45;
    g.font = '700 ' + size.toFixed(1) + 'px "' + def.font + '","Noto Sans Devanagari",sans-serif';
    const tw = g.measureText(label).width;
    const total = iconW + gapI + tw;
    const cx = rx + (rw - total) / 2, cy = ry + rh / 2;
    const ix = cx + iconW / 2, iy = cy - size * .05;
    g.strokeStyle = ink; g.lineWidth = Math.max(1.3, size * .13);
    g.beginPath(); g.arc(ix, iy - size * .22, size * .26, Math.PI, Math.PI * 2); g.stroke();
    g.fillStyle = ink;
    kbRR(g, ix - size * .33, iy - size * .06, size * .66, size * .52, size * .1); g.fill();
    g.fillStyle = light ? 'rgba(255,252,246,.9)' : 'rgba(6,13,28,.9)';
    g.beginPath(); g.arc(ix, iy + size * .16, size * .055, 0, 7); g.fill();
    g.fillStyle = ink; g.textAlign = 'left'; g.textBaseline = 'middle';
    g.fillText(label, cx + iconW + gapI, cy + 1);
    g.textBaseline = 'alphabetic';
  }
  function kbDrawPrivacy(g, e, scene, x, y, w, h, im, off, isAd, def) {
    const groups = (e && e.el && e.el.privacy) || [];
    if (!groups.length || isAd) return;
    /* Generated cards ship privacy zones without a per-element on/off map.
       Those zones are ON by default so a name is never readable; the map is
       only used when the editor explicitly toggles a zone. */
    const map = e.privacy && typeof e.privacy === 'object' ? e.privacy : null;
    const on = groups.filter(gr => gr.rects && gr.rects.length && (!map || map[gr.id] === true));
    if (!on.length) return;
    const bb = e.scroll ? (e.el.scrollBbox || e.el.bbox || [0, 0, w, h]) : (e.el.bbox || [0, 0, w, h]);
    const sw = Math.max(1, bb[2]), sh = Math.max(1, bb[3]);
    let kx, ky, dx, dy, tx, ty, dw, dh;
    if (e.scroll) {
      kx = ky = w / sw;
      tx = x; ty = y - (off || 0); dw = w; dh = sh * ky;
      dx = tx - bb[0] * kx; dy = ty - bb[1] * ky;
    } else {
      const iw = im ? (im.naturalWidth || sw) : sw;
      const ih = im ? (im.naturalHeight || sh) : sh;
      const k = Math.min(w / Math.max(1, iw), h / Math.max(1, ih));
      dw = iw * k; dh = ih * k;
      tx = x + (w - dw) / 2; ty = y + (h - dh) / 2;
      kx = dw / sw; ky = dh / sh;
      dx = tx - bb[0] * kx; dy = ty - bb[1] * ky;
    }
    const style = (scene && scene.privacyStyle) || kb.privacyStyle || 'soft';
    g.save();
    g.beginPath(); g.rect(x, y, w, h); g.clip();
    on.forEach(gr => {
      (gr.rects || []).forEach(r => {
        const rx = dx + r.x * kx, ry = dy + r.y * ky;
        const rw = Math.max(2, r.w * kx), rh = Math.max(2, r.h * ky);
        const ix = Math.max(x, rx), iy = Math.max(y, ry);
        const iw2 = Math.min(x + w, rx + rw) - ix;
        const ih2 = Math.min(y + h, ry + rh) - iy;
        if (iw2 <= 1 || ih2 <= 1) return;
        g.save();
        g.beginPath(); g.rect(ix, iy, iw2, ih2); g.clip();
        if (style === 'bar') {
          kbPrivacyBar(g, rx, ry, rw, rh, gr.label || 'नाम गोप्य', def);
        } else if (style === 'pixel' && im) {
          const pc = kbPixelImage(im);
          g.imageSmoothingEnabled = false;
          g.drawImage(pc, tx, ty, dw, dh);
          g.imageSmoothingEnabled = true;
        } else if (style === 'strong') {
          /* Two blur generations compound the loss of detail; the near-opaque
             plate then guarantees the name cannot be reconstructed in a
             paused frame or a 1080 export. */
          kbBlurRect(g, ix, iy, iw2, ih2, 26);
          kbBlurRect(g, ix, iy, iw2, ih2, 14);
          const light = KB_LIGHT.has(def.motion);
          g.fillStyle = light ? 'rgba(250,244,232,.88)' : 'rgba(6,12,24,.88)';
          g.fillRect(ix, iy, iw2, ih2);
          if (iw2 > 60 && ih2 > 28) kbPrivacyPlate(g, ix, iy, iw2, ih2, 'नाम गोप्य', def, light);
        } else {
          kbBlurRect(g, ix, iy, iw2, ih2, 11);
        }
        g.restore();
      });
    });
    g.restore();
  }

  /* A scrolling document must always reach its last line inside the card's
     real duration. The designed 30s pace is kept whenever the clip is long
     enough; a shorter saved layout or Timeline trim compresses the travel
     instead of cutting the page off before the bottom. */
  function kbScrollWindow(scene, speed) {
    const dur = Math.max(.2, +(scene && scene.dur) || 0);
    const spd = clamp(speed || 1, .4, 3);
    const want = Math.max(0, +(scene && scene.scrollDelay != null ? scene.scrollDelay : .8));
    const delay = Math.min(want, Math.max(0, dur - .45));
    /* Leave the last line on screen for a moment, and finish before a card
       exit fade starts so the bottom is never shown half-transparent. */
    const exiting = !!(scene && scene.set && scene.set.exit && scene.set.exit !== 'none');
    const settle = exiting ? Math.max(.2, .6 / spd) + .05 : .3;
    const end = Math.max(delay + .05, dur - settle);
    const designed = Math.max(.5, +(scene && scene.scrollDur) || .5) / spd;
    return { delay: delay, travel: Math.max(.05, Math.min(designed, end - delay)) };
  }
  function kbScrollProgress(scene, lt, speed) {
    const win = kbScrollWindow(scene, speed);
    return clamp((lt - win.delay) / win.travel, 0, 1);
  }

  function kbDrawMultiCard(g, scene, lt, opts) {
    opts = opts || {};
    const def = kbTplDef(scene.tpl);
    const set = scene.set || {};
    if (set.visible === false) return null;
    const speed = clamp(set.speed || 1, .4, 3);
    const bgOn = scene.background ? scene.background.on !== false : set.bg !== 'none';
    const card = kbCardBox(scene);
    const entryDur = Math.max(.35, (set.animDur != null ? +set.animDur : .9) / speed);
    /* A model transition already places the incoming card frame during the
       gap. Replaying the card-level entrance at local zero would blink that
       frame off again, so auto cards after the first keep their frame. Their
       elements still run their full staggered entrances. */
    const cardEntered = scene.mode === 'auto' && (+scene.autoNo || +scene.no || 0) > 1;
    const ep = opts.forceFinal || scene.suppressEntry || cardEntered ? 1 : clamp(lt / entryDur);
    const xp = (opts.forceFinal || set.exit === 'none') ? 1 : clamp((scene.dur - lt) / Math.max(.2, .6 / speed));
    const gap = scene.gap || 0;
    let gapA = 1;
    if (!opts.forceFinal && lt > scene.dur && gap > 0) gapA = clamp(1 - (lt - scene.dur) / Math.min(gap, .55));
    let alpha = eo(ep) * xp * gapA;
    if (opts.extraAlpha != null) alpha *= opts.extraAlpha;
    const u = opts.u || 1, ox = opts.ox || 0, oy = opts.oy || 0;
    const cx = card.x + card.w / 2, cy = card.y + card.h / 2;
    let dy0 = 0, dx0 = 0, rot0 = 0, sc0 = .982 + .018 * eo(ep), reveal = 1;
    if (def.motion === 'cosmic') {
      dy0 = (1 - eq(ep)) * 26;
    } else if (def.motion === 'nebula') {
      dy0 = (1 - eo(ep)) * 16;
      sc0 = .972 + .028 * eo(ep);
      rot0 = -(1 - eo(ep)) * .005;
    } else if (def.motion === 'vedic') {
      dy0 = (1 - eq(ep)) * 6;
      sc0 = .994 + .006 * eq(ep);
      reveal = opts.forceFinal || scene.suppressEntry ? 1 : eq(ep);
    } else if (def.motion === 'orbit') {
      dx0 = -(1 - eq(ep)) * 118;
      sc0 = .988 + .012 * eo(ep);
    } else {
      dy0 = (1 - eq(ep)) * 26;
    }

    g.save();
    g.translate(ox, oy); g.scale(u, u);
    g.globalAlpha = g.globalAlpha * clamp(alpha, 0, 1);
    kbDrawFrame(g, def);
    g.restore();

    g.save();
    g.translate(ox, oy); g.scale(u, u);
    g.globalAlpha = clamp(alpha, 0, 1);
    g.globalCompositeOperation = 'source-over';
    g.translate(cx + dx0, cy + dy0);
    if (rot0) g.rotate(rot0);
    g.scale(sc0, sc0); g.translate(-cx, -cy);
    if (def.motion === 'vedic' && reveal < .999) {
      g.beginPath();
      g.rect(card.x - 24, card.y - 18, card.w + 48, (card.h + 36) * reveal);
      g.clip();
    }

    const depth = clamp(set.depth == null ? 30 : +set.depth, 0, 90);
    if (depth > 3 && set.bg !== 'none') {
      for (let i = 5; i >= 1; i--) {
        const d = depth * i / 5;
        g.fillStyle = KB_LIGHT.has(def.motion) ? 'rgba(50,40,25,.05)' : 'rgba(0,0,0,' + (.07 + i * .04) + ')';
        kbRR(g, card.x + d * .45, card.y + d * .62, card.w, card.h, set.radius != null ? set.radius : def.radius); g.fill();
      }
    }
    if (bgOn && set.bg !== 'none') kbDrawModelBackdrop(g, card, def, lt, ep);
    kbDrawCard(g, card.x, card.y, card.w, card.h, def, set, 1);

    /* A soft gold light sweep crosses the glass once as the card enters. It
       is drawn under the content, so it never touches the text contrast. */
    if (def.motion === 'cosmic' && !opts.forceFinal && ep < .999) {
      g.save();
      kbRR(g, card.x, card.y, card.w, card.h, set.radius != null ? set.radius : def.radius); g.clip();
      const sy = card.y - 120 + (card.h + 240) * eq(ep);
      const sw = g.createLinearGradient(0, sy - 150, 0, sy + 150);
      sw.addColorStop(0, 'rgba(110,231,255,0)');
      sw.addColorStop(.5, 'rgba(246,211,101,' + (.15 * (1 - ep)) + ')');
      sw.addColorStop(1, 'rgba(110,231,255,0)');
      g.globalCompositeOperation = 'lighter';
      g.fillStyle = sw; g.fillRect(card.x, sy - 150, card.w, 300);
      g.restore();
    }

    if (scene.chrome) kbDrawHeader(g, scene, def, 1);

    const radius = (set.radius != null ? +set.radius : def.radius) || 0;
    g.save();
    g.beginPath(); kbRR(g, card.x + 2, card.y + 2, card.w - 4, card.h - 4, Math.max(0, radius - 2)); g.clip();

    if (bgOn && set.bg !== 'none') kbDrawModelInterior(g, scene, card, def, lt, ep);
    /* The card interior stays inside the rounded frame, but element layers
       deliberately do not. A dragged caption, frame or panel keeps drawing
       at the canvas edge instead of vanishing under the card clip. */
    g.restore();

    const els = (scene.els || []).slice().sort((a, b) => (+a.z || 0) - (+b.z || 0));
    const scrollP = scene.scrollDur ? kbScrollProgress(scene, lt, speed) : 1;
    els.forEach((e, idx) => {
      if (!e || !e.box || !e.el) return;
      const isAd = !!(e.el && e.el.ad);
      /* An ad photo is an optional layer. Disabling it must not punch a hole
         in the card: the designed promo panel is the fallback and stays. */
      if (e.visible === false && !isAd) return;
      const st = kbMultiElState(e, lt, scene, idx, speed);
      if (st.alpha <= .002) return;
      const x = e.box[0] + st.dx, y = e.box[1] + st.dy, w = e.box[2], h = e.box[3];
      const adIm = isAd && e.visible !== false ? kbAdImg(e.adSrc) : null;
      const im = kbImgFor(e.el);
      g.save();
      g.globalAlpha = g.globalAlpha * st.alpha;
      g.globalCompositeOperation = 'source-over';
      if (st.rot) { g.translate(x + w / 2, y + h / 2); g.rotate(st.rot); g.translate(-x - w / 2, -y - h / 2); }
      /* Nebula soft-focus bloom sits behind the incoming image, so it never
         washes out chart labels or table text. */
      if (st.soft > .01) {
        const bg = g.createRadialGradient(x + w / 2, y + h / 2, 0, x + w / 2, y + h / 2, Math.max(w, h) * .62);
        bg.addColorStop(0, 'rgba(233,213,255,' + (.10 * st.soft) + ')');
        bg.addColorStop(.52, 'rgba(34,211,238,' + (.055 * st.soft) + ')');
        bg.addColorStop(1, 'rgba(139,92,246,0)');
        g.fillStyle = bg; g.fillRect(x - 16, y - 16, w + 32, h + 32);
      }
      /* Wipe entries are real clips now. The previous renderer computed
         clipX/clipY but never applied them, so Vedic text only faded. */
      if (st.clipX < .999 || st.clipY < .999) {
        g.beginPath();
        g.rect(x, y, Math.max(0, w * st.clipX), Math.max(0, h * st.clipY));
        g.clip();
      }
      if (e.scroll) {
        const bb = e.el.scrollBbox || e.el.bbox || [0, 0, w, h];
        const ih = w * Math.max(1, bb[3]) / Math.max(1, bb[2]);
        /* Chinā reads from its real beginning to the end: content starts at
           the top and travels upward as the scene plays. */
        const off = Math.max(0, ih - h) * scrollP;
        g.globalCompositeOperation = 'source-over';
        g.beginPath(); g.rect(x, y, w, h); g.clip();
        if (im) { g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high'; g.drawImage(im, x, y - off, w, ih); }
        else {
          /* Paper fallback while the (large) Janmapatrika SVG decodes. It
             matches the real page, so the first frame reads as a document,
             never as a dark empty card. */
          if (e.el && e.el.jp) {
            g.fillStyle = '#f1f8eb'; g.fillRect(x, y, w, h);
            g.strokeStyle = 'rgba(154,122,18,.28)'; g.lineWidth = 1;
            g.strokeRect(x + 10, y + 10, w - 20, h - 20);
          } else {
            g.fillStyle = kbRgba(def.accent, .1); g.fillRect(x, y, w, h);
          }
        }
        kbDrawPrivacy(g, e, scene, x, y, w, h, im, off, false, def);
        g.restore();
        return;
      }
      if (im) {
        /* Preserve the real component's aspect ratio when the user resizes
           its box; centred inside the box, never stretched or flattened. */
        const sw = im.naturalWidth || Math.max(1, (e.el.bbox || [0, 0, w, h])[2]);
        const sh = im.naturalHeight || Math.max(1, (e.el.bbox || [0, 0, w, h])[3]);
        const k = Math.min(w / Math.max(1, sw), h / Math.max(1, sh));
        const dw = sw * k, dh = sh * k;
        g.beginPath(); g.rect(x, y, w, h); g.clip();
        g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
        g.drawImage(im, x + (w - dw) / 2, y + (h - dh) / 2, dw, dh);
      } else if (isAd) {
        /* The designed poster is still decoding; keep a dark plate so the
           portrait never sits on a transparent hole. */
        g.fillStyle = 'rgba(8,17,31,.9)';
        kbRR(g, x, y, w, h, 10); g.fill();
      } else {
        g.fillStyle = kbRgba(def.accent, .06);
        kbRR(g, x, y, w, h, 10); g.fill();
        g.fillStyle = def.mut; g.textAlign = 'center'; g.textBaseline = 'middle';
        g.font = '600 12px "' + def.font + '","Noto Sans Devanagari",sans-serif';
        g.fillText(kbEllipsis(g, e.el.name || '', Math.max(30, w - 20)), x + w / 2, y + h / 2);
        g.textAlign = 'left'; g.textBaseline = 'alphabetic';
      }
      if (isAd && adIm) {
        /* Astrologer portrait: a circular crop over the designed promo panel.
           The panel caption and service lines stay readable around it, and the
           gold ring keeps the photo tied to the card's ornament language. */
        const ar = Math.min(w, h) * .255;
        const acx = x + w / 2, acy = y + h * .30;
        g.save();
        g.beginPath(); g.arc(acx, acy, ar + 7, 0, Math.PI * 2);
        g.fillStyle = 'rgba(6,13,26,.94)'; g.fill();
        g.beginPath(); g.arc(acx, acy, ar, 0, Math.PI * 2); g.clip();
        const k = Math.max((ar * 2) / Math.max(1, adIm.naturalWidth), (ar * 2) / Math.max(1, adIm.naturalHeight));
        const dw = adIm.naturalWidth * k, dh = adIm.naturalHeight * k;
        g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
        g.drawImage(adIm, acx - dw / 2, acy - dh / 2, dw, dh);
        g.restore();
        g.strokeStyle = kbRgba(def.accent, .95); g.lineWidth = 3;
        g.beginPath(); g.arc(acx, acy, ar + 2, 0, Math.PI * 2); g.stroke();
        g.strokeStyle = kbRgba(def.accent, .3); g.lineWidth = 1.2;
        g.beginPath(); g.arc(acx, acy, ar + 9, 0, Math.PI * 2); g.stroke();
      }
      if (!isAd) kbDrawPrivacy(g, e, scene, x, y, w, h, im, 0, false, def);
      /* Orbit HUD emphasis: one thin telemetry scan crosses charts and
         graphs. It is drawn over the component at very low opacity and never
         over body text. */
      if (st.scan > .01 && st.scan <= 1) {
        const sy = y + h * st.scan;
        const sg = g.createLinearGradient(0, sy - 20, 0, sy + 20);
        sg.addColorStop(0, 'rgba(163,230,53,0)');
        sg.addColorStop(.48, 'rgba(34,211,238,.08)');
        sg.addColorStop(.5, 'rgba(163,230,53,.26)');
        sg.addColorStop(.52, 'rgba(34,211,238,.08)');
        sg.addColorStop(1, 'rgba(163,230,53,0)');
        g.fillStyle = sg; g.fillRect(x, sy - 20, w, 40);
        g.fillStyle = 'rgba(163,230,53,.46)'; g.fillRect(x, sy, w, 1);
      }
      /* The moving page edge makes a Vedic reveal read as a ruled sheet
         being uncovered instead of an arbitrary crop. */
      if (st.clipY < .999 && st.clipY > .001) {
        g.fillStyle = KB_LIGHT.has(def.motion) ? 'rgba(138,28,28,.38)' : 'rgba(246,211,101,.58)';
        g.fillRect(x, y + h * st.clipY - 1.2, w, 1.6);
      }
      if (st.clipX < .999 && st.clipX > .001) {
        g.fillStyle = KB_LIGHT.has(def.motion) ? 'rgba(138,28,28,.30)' : 'rgba(110,231,255,.46)';
        g.fillRect(x + w * st.clipX - 1.2, y, 1.6, h);
      }
      g.restore();
    });
    if (def.motion === 'vedic' && reveal < .999) {
      const ey = card.y - 18 + (card.h + 36) * reveal;
      const eg = g.createLinearGradient(0, ey - 18, 0, ey + 8);
      eg.addColorStop(0, 'rgba(161,98,7,0)');
      eg.addColorStop(.72, kbRgba(def.accent2, .12));
      eg.addColorStop(.94, kbRgba(def.accent, .32));
      eg.addColorStop(1, 'rgba(138,28,28,.62)');
      g.fillStyle = eg; g.fillRect(card.x + 2, ey - 18, card.w - 4, 26);
    }

    if (scene.footerOn !== false) kbDrawFooter(g, scene, def, Math.min(1, alpha * 1.25), clamp((lt + .001) / Math.max(.1, scene.dur), 0, 1));
    if (scene.scrollDur && !scene.hideScrollBar) {
      g.save();
      g.globalAlpha = g.globalAlpha * clamp(alpha, 0, 1);
      const barY = card.y + card.h - 18, barW = card.w - 64;
      g.fillStyle = kbRgba(def.accent, .18); kbRR(g, card.x + 32, barY, barW, 4, 2); g.fill();
      g.fillStyle = kbRgba(def.accent, .9); kbRR(g, card.x + 32, barY, Math.max(3, barW * scrollP), 4, 2); g.fill();
      g.restore();
    }
    g.restore();

    if (opts.returnBox) return { x: ox + card.x * u, y: oy + card.y * u, w: card.w * u, h: card.h * u };
    return null;
  }


  function kbSceneCard(scene, def, set) {
    const el = scene.el || {}, b = el.bbox || [0, 0, 720, 1280];
    const pad = clamp(set.pad == null ? 26 : +set.pad, 0, 56);
    const maxW = 628 - pad * 2, maxH = 988 - pad * 2;
    const cap = KB_FIT_CAP[el.type] || 1.3;
    let k = Math.min(maxW / Math.max(1, b[2]), maxH / Math.max(1, b[3]), cap);
    if (!isFinite(k) || k <= 0) k = 1;
    const iw = b[2] * k, ih = b[3] * k;
    const cw = iw + pad * 2, ch = ih + pad * 2;
    let x = 360 - cw / 2;
    if (set.align === 'left') x = 46;
    else if (set.align === 'right') x = 674 - cw;
    const y = 664 - ch / 2;
    return { x: x, y: y, w: cw, h: ch, ix: x + pad, iy: y + pad, iw: iw, ih: ih, pad: pad, radius: set.radius != null ? set.radius : def.radius };
  }

  function kbEntryAlpha(kind, p) {
    switch (kind) {
      case 'rise': return eo(clamp(p * 1.5));
      case 'zoom': return eo(clamp(p * 1.6));
      case 'flip': return clamp(p * 2.2);
      case 'rotate': return clamp(p * 2.2);
      case 'slide': return eo(clamp(p * 1.5));
      case 'reveal': return 1;
      case 'glow': return eo(p);
      default: return clamp(p * 1.4);
    }
  }

  function kbDrawSceneContent(g, scene, lt, opts) {
    opts = opts || {};
    const def = kbTplDef(scene.tpl);
    const set = scene.set || {};
    if (set.visible === false) return null;
    if (kbIsMulti(scene)) return kbDrawMultiCard(g, scene, lt, opts);
    const speed = clamp(set.speed || 1, .4, 3);
    const entry = set.entry === 'auto' || !set.entry
      ? (def.motion === 'nebula' ? 'fade' : def.motion === 'vedic' ? 'reveal' : def.motion === 'orbit' ? 'slide'
        : def.motion === 'cinematic' ? 'zoom' : def.motion === 'neon' || def.motion === 'nextgen' ? 'slide' : 'rise')
      : set.entry;
    const exit = set.exit || 'fade';
    const anim = set.anim || 'auto';
    const entryDur = ({ fade: .55, rise: .78, zoom: .72, flip: .9, rotate: .9, slide: .8, reveal: .85, glow: 1 }[entry] || .72) / speed;
    const exitDur = .55 / speed;
    const singleEntered = scene.mode === 'auto' && (+scene.autoNo || +scene.no || 0) > 1;
    let ep = opts.forceFinal || scene.suppressEntry || singleEntered ? 1 : clamp(lt / entryDur);
    let xp = (opts.forceFinal || set.exit === 'none') ? 1 : clamp((scene.dur - lt) / exitDur);
    const gap = scene.gap || 0;
    let gapA = 1;
    if (!opts.forceFinal && lt > scene.dur && gap > 0) gapA = clamp(1 - (lt - scene.dur) / Math.min(gap, .55));
    let alpha = kbEntryAlpha(entry, ep) * xp * gapA;
    if (opts.extraAlpha != null) alpha *= opts.extraAlpha;

    let dx = 0, dy = 0, sc = clamp(set.scale || 1, .5, 1.6), rot = 0, sx = 1, sy = 1, glow = 0, reveal = 1;
    switch (entry) {
      case 'fade': dy = (1 - eo(ep)) * 10; break;
      case 'rise': dy = (1 - eq(ep)) * 38; break;
      case 'zoom': sc *= .93 + .07 * eo(ep); break;
      /* Text readability: flip/rotate entrances become a soft fade + rise
         instead of distorting letters. The template colours, layout and
         background motion remain exactly as they were. */
      case 'flip': dy = (1 - eo(ep)) * 18; sc *= .985 + .015 * eo(ep); break;
      case 'rotate': dx = -(1 - eq(ep)) * 16; sc *= .985 + .015 * eo(ep); break;
      case 'slide': dx = -(1 - eq(ep)) * 70; break;
      case 'reveal': reveal = eq(ep); break;
      case 'glow': sc *= 1 + (1 - eo(ep)) * .06; glow = 1 - ep; break;
    }
    switch (exit) {
      case 'zoom': sc *= 1 + (1 - xp) * .12; break;
      case 'slide': dx += (1 - xp) * 110; break;
      case 'glow': glow = Math.max(glow, 1 - xp); break;
    }

    const ph = lt * speed;
    if (anim === 'float') { dy += Math.sin(ph * 1.3) * 3; }
    else if (anim === 'parallax') { dx += Math.sin(ph * .8) * 4; dy += Math.cos(ph * .6) * 3; }
    else if (anim === 'depth') { sc *= 1 + Math.sin(ph * .9) * .012; }
    else if (anim === 'cinematic') { sc *= 1 + .025 * clamp(lt / Math.max(.1, scene.dur)); }
    else if (anim === 'glow') { glow = Math.max(glow, .2 + .2 * Math.sin(ph * 2)); }
    else if (anim === 'auto') {
      if (def.motion === 'cosmic' || def.motion === 'floating' || def.motion === 'glass') { dy += Math.sin(ph * .8) * 2; }
      else if (def.motion === 'cinematic') { sc *= 1 + .018 * clamp(lt / Math.max(.1, scene.dur)); }
      else if (def.motion === 'royal' || def.motion === 'golden') { glow = Math.max(glow, .08 + .06 * Math.sin(ph * .9)); }
    }

    let rx = clamp((set.rotX || 0) * Math.PI / 180, -.6, .6);
    let ry = clamp((set.rotY || 0) * Math.PI / 180, -.6, .6);
    const persp = clamp(set.persp || 900, 400, 1600) / 900;
    /* 3D emphasis stays a gentle perspective breath, never a spinning text
       block. Letter shapes remain square and readable at every frame. */
    if (anim === 'rotate3d') { dx += Math.sin(ph * .8) * 6; }
    if (anim === 'flip3d') { dy += Math.cos(ph * .7) * 5; }
    if (anim === 'auto' && (def.motion === 'cosmic' || def.motion === 'floating')) { ry += Math.sin(ph * .45) * .006; rx += Math.cos(ph * .38) * .004; }
    ry *= persp; rx *= persp;

    const card = kbSceneCard(scene, def, set);
    const cx = card.x + card.w / 2, cy = card.y + card.h / 2;
    const u = opts.u || 1, ox = opts.ox || 0, oy = opts.oy || 0;

    g.save();
    g.translate(ox, oy); g.scale(u, u);
    g.globalAlpha = g.globalAlpha * clamp(alpha, 0, 1);
    kbDrawFrame(g, def);
    g.restore();

    g.save();
    g.translate(ox, oy); g.scale(u, u);
    kbDrawHeader(g, scene, def, Math.min(1, alpha * 1.25));
    g.restore();

    g.save();
    g.translate(ox, oy); g.scale(u, u);
    g.globalAlpha = clamp(alpha, 0, 1);
    g.translate(cx + dx, cy + dy);
    g.rotate(rot);
    if (rx || ry) {
      g.transform(Math.cos(ry), Math.sin(ry) * .055, 0, 1, 0, 0);
      g.transform(1, 0, 0, Math.max(.05, Math.cos(rx)), 0, 0);
    }
    g.scale(sc * sx, sc * sy);
    g.translate(-cx, -cy);
    if (entry === 'reveal') {
      g.beginPath(); g.rect(card.x - 30, card.y + card.h * (1 - reveal) - 10, card.w + 60, card.h * reveal + 20); g.clip();
    }
    const depth = clamp(set.depth == null ? 24 : +set.depth, 0, 90);
    if (depth > 3 && set.bg !== 'none') {
      const dir = ry >= 0 ? 1 : -1;
      for (let i = 5; i >= 1; i--) {
        const d = depth * i / 5;
        g.fillStyle = KB_LIGHT.has(def.motion) ? 'rgba(50,40,25,.05)' : 'rgba(0,0,0,' + (.08 + i * .045) + ')';
        kbRR(g, card.x + d * .55 * dir, card.y + d * .72, card.w, card.h, card.radius); g.fill();
      }
    }
    if (glow > .02) {
      g.save(); g.shadowColor = def.accent; g.shadowBlur = 18 + glow * 38;
      g.strokeStyle = kbRgba(def.accent, .45 * Math.min(1, glow)); g.lineWidth = 2;
      kbRR(g, card.x, card.y, card.w, card.h, card.radius); g.stroke(); g.restore();
    }
    kbDrawCard(g, card.x, card.y, card.w, card.h, def, set, 1);
    if (set.bg !== 'none') {
      g.save();
      g.beginPath(); kbRR(g, card.x + 2, card.y + 2, card.w - 4, card.h - 4, Math.max(0, card.radius - 2)); g.clip();
      kbDrawModelInterior(g, scene, card, def, lt, ep);
      g.restore();
    }
    kbDrawElement(g, scene.el, card.ix, card.iy, card.iw, card.ih, def, 1);
    if (scene.el && scene.el.privacy && scene.el.privacy.length) {
      const pe = { el: scene.el, privacy: scene.privacy || null, box: [card.ix, card.iy, card.iw, card.ih] };
      kbDrawPrivacy(g, pe, scene, card.ix, card.iy, card.iw, card.ih, kbImgFor(scene.el), 0, false, def);
    }
    g.restore();

    const prog = clamp((lt + .001) / Math.max(.1, scene.dur), 0, 1);
    g.save(); g.translate(ox, oy); g.scale(u, u);
    if (scene.footerOn !== false) kbDrawFooter(g, scene, def, Math.min(1, alpha * 1.25), prog);
    g.restore();

    if (opts.returnBox) return { x: ox + card.x * u, y: oy + card.y * u, w: card.w * u, h: card.h * u };
    return null;
  }

  function kbDrawScene(g, w, h, scene, lt, opts) {
    opts = opts || {};
    const def = kbTplDef(scene.tpl);
    const lay = kbLayout(w, h);
    g.save();
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.shadowBlur = 0; g.textBaseline = 'alphabetic'; g.textAlign = 'left';
    kbDrawBg(g, w, h, def, opts.clock != null ? opts.clock : lt);
    g.restore();

    const gap = scene.gap || 0;
    const trans = (scene.set && scene.set.trans) || 'smooth';
    /* The boundary frame belongs to the transition. With a strict > the
       card is fully faded at local === dur, then the transition redraws its
       frame on the next tick: a visible one-frame blink on every cut. */
    const inGap = lt >= scene.dur && gap > 0;
    const common = { u: lay.u, ox: lay.ox, oy: lay.oy };

    if (!inGap) {
      return kbDrawSceneContent(g, scene, lt, Object.assign({}, common, { returnBox: true, forceFinal: !!opts.forceFinal, extraAlpha: opts.extraAlpha }));
    }

    const gp = clamp((lt - scene.dur) / gap, 0, 1);
    const next = opts.next;
    const nextDef = next ? kbTplDef(next.tpl) : def;
    if (!next || trans === 'cut') {
      return kbDrawSceneContent(g, scene, scene.dur, Object.assign({}, common, { forceFinal: true, extraAlpha: 1 - gp }));
    }
    const ease = gp * gp * (3 - 2 * gp);
    if (trans === 'wipe') {
      /* Vedic page reveal: the next page descends over the old one like a
         sheet of paper, with a warm inked edge instead of a hard cut. */
      kbDrawSceneContent(g, scene, scene.dur, Object.assign({}, common, { forceFinal: true, extraAlpha: 1 - ease * .45 }));
      g.save(); g.beginPath(); g.rect(0, 0, w, h * ease + 2); g.clip();
      kbDrawSceneContent(g, next, 0, Object.assign({}, common, { forceFinal: true, extraAlpha: 1 }));
      g.restore();
      const ey = h * ease;
      const eg = g.createLinearGradient(0, ey - 42, 0, ey + 8);
      eg.addColorStop(0, kbRgba(nextDef.accent2, 0));
      eg.addColorStop(.55, kbRgba(nextDef.accent2, .10));
      eg.addColorStop(.9, kbRgba(nextDef.accent, .22));
      eg.addColorStop(1, kbRgba(nextDef.accent, .62));
      g.fillStyle = eg; g.fillRect(0, ey - 42, w, 50);
      g.fillStyle = kbRgba(nextDef.accent, .48);
      g.fillRect(0, ey, w, 2);
      g.fillStyle = kbRgba(nextDef.accent2, .35);
      [w * .18, w * .5, w * .82].forEach(x => { g.beginPath(); g.arc(x, ey, 3, 0, 7); g.fill(); });
    } else if (trans === 'zoom') {
      if (nextDef.motion === 'orbit' || def.motion === 'orbit') {
        /* Orbit HUD push: the old dashboard pushes left while the new one
           slides in from the right under a fast telemetry scan. The incoming
           card fades in with the push instead of covering the old one on the
           first frame. */
        g.save(); g.translate(-w * .045 * ease, 0);
        g.translate(w / 2, h / 2); g.scale(1 + ease * .16, 1 + ease * .16); g.translate(-w / 2, -h / 2);
        kbDrawSceneContent(g, scene, scene.dur, Object.assign({}, common, { forceFinal: true, extraAlpha: 1 - ease * .9 }));
        g.restore();
        g.save(); g.translate(w * .055 * (1 - ease), 0);
        kbDrawSceneContent(g, next, 0, Object.assign({}, common, { forceFinal: true, extraAlpha: clamp(ease * 1.18) }));
        g.restore();
        const sy = h * (.2 + .6 * ease);
        const sg = g.createLinearGradient(0, sy - 24, 0, sy + 24);
        sg.addColorStop(0, kbRgba(nextDef.accent, 0));
        sg.addColorStop(.5, kbRgba(nextDef.accent2, .16));
        sg.addColorStop(1, kbRgba(nextDef.accent, 0));
        g.fillStyle = sg; g.fillRect(0, sy - 24, w, 48);
        g.fillStyle = kbRgba(nextDef.accent, .55);
        g.fillRect(w * .04, sy, w * .92, 1.4);
      } else {
        g.save(); g.translate(w / 2, h / 2); g.scale(1 + gp * .32, 1 + gp * .32); g.translate(-w / 2, -h / 2);
        kbDrawSceneContent(g, scene, scene.dur, Object.assign({}, common, { forceFinal: true, extraAlpha: 1 - gp }));
        g.restore();
        g.save(); g.translate(w / 2, h / 2); g.scale(.82 + gp * .18, .82 + gp * .18); g.translate(-w / 2, -h / 2);
        kbDrawSceneContent(g, next, 0, Object.assign({}, common, { forceFinal: true, extraAlpha: gp }));
        g.restore();
      }
    } else if (trans === 'dissolve') {
      /* Nebula soft dissolve: both cards drift through a violet bloom
         instead of a flat crossfade. */
      g.save(); g.translate(0, -ease * 16);
      kbDrawSceneContent(g, scene, scene.dur, Object.assign({}, common, { forceFinal: true, extraAlpha: 1 - ease }));
      g.restore();
      g.save(); g.translate(0, (1 - ease) * 22);
      kbDrawSceneContent(g, next, 0, Object.assign({}, common, { forceFinal: true, extraAlpha: ease }));
      g.restore();
      const va = Math.sin(Math.PI * gp);
      const vg = g.createRadialGradient(w * .5, h * .44, 0, w * .5, h * .44, Math.max(w, h) * .62);
      vg.addColorStop(0, 'rgba(233,213,255,' + (.13 * va) + ')');
      vg.addColorStop(.45, 'rgba(139,92,246,' + (.065 * va) + ')');
      vg.addColorStop(1, 'rgba(34,211,238,0)');
      g.fillStyle = vg; g.fillRect(0, 0, w, h);
    } else {
      kbDrawSceneContent(g, scene, scene.dur, Object.assign({}, common, { forceFinal: true, extraAlpha: 1 - gp }));
      kbDrawSceneContent(g, next, 0, Object.assign({}, common, { forceFinal: true, extraAlpha: gp }));
    }
    return null;
  }

  function kunDrawCustomClip(c, t) {
    const raw = t - c.start;
    if (!(raw >= 0 && raw <= c.dur)) { c.box = null; return; }
    const scene = c.kun;
    if (!scene || (!scene.el && !(scene.els && scene.els.length))) { c.box = null; return; }
    /* Phase 10 split: a clip may show only one scene-local window. The
       window is scene seconds, so trimming a split half never re-generates
       or re-times the card's text. */
    const win = Array.isArray(c.kunWin) && c.kunWin.length === 2 ? c.kunWin : null;
    const w0 = win ? clamp(+win[0] || 0, 0, Math.max(0, scene.dur)) : 0;
    const w1 = win ? clamp(+win[1] || 0, w0 + .05, Math.max(w0 + .05, scene.dur)) : scene.dur;
    const lt = raw + w0;
    let next = null;
    if (!win || w1 >= scene.dur - .001) {
      if ((scene.gap || 0) > 0 && scene.set && scene.set.trans !== 'cut') {
        const nx = (clips || []).find(x => x.kun && x.kun.no === (scene.no || 0) + 1);
        if (nx) next = nx.kun;
      }
    }
    const box = kbDrawScene(ctx, W, H, scene, Math.min(lt, w1), { next: next, clock: t });
    c.box = box || null;
  }
  window.kunDrawCustomClip = kunDrawCustomClip;
  window.kunDrawScene = kbDrawScene;
  /* Timeline schema helpers: index.html uses the same SVG text parser and
     element wrapper so a builder import and a Timeline edit agree exactly. */
  window.KunSceneAPI = {
    textRuns: kbTextRunsOf,
    sceneEl: kbSceneElOf,
    decodeEnt: kbDecodeEnt
  };
  window.kunRenderThumb = function (canvas, scene, win) {
    if (!canvas || !scene) return;
    const g = canvas.getContext('2d');
    const w = canvas.width, h = canvas.height;
    const w0 = Array.isArray(win) ? clamp(+win[0] || 0, 0, Math.max(0, scene.dur)) : 0;
    const w1 = Array.isArray(win) ? clamp(+win[1] || 0, w0, Math.max(w0, scene.dur)) : scene.dur;
    const at = w0 + Math.max(0, w1 - w0) * .45;
    kbDrawScene(g, w, h, scene, Math.min(at, scene.dur), { clock: (scene.no || 1) * 3.7, forceFinal: true });
  };

  /* ═══════════════════════════════════════════════════════════════
     builder state + UI
     ═══════════════════════════════════════════════════════════════ */

  const KB_TYPE_NE = {
    heading: 'शीर्षक', chart: 'चार्ट', table: 'तालिका', report: 'रिपोर्ट',
    graph: 'ग्राफ', banner: 'ब्यानर', cards: 'कार्ड', footer: 'फुटर',
    art: 'चित्र / कला', list: 'सूची', note: 'नोट', panel: 'प्यानल / फ्रेम'
  };
  const KB_FONT_LIST = ['Mukta', 'Hind', 'Noto Sans Devanagari', 'Rozha One', 'Tiro Devanagari Hindi', 'Yatra One', 'Laila', 'Baloo 2'];
  const KB_DEF_GAP = .55;
  let kbItemSeq = 0, kbSearchTimer = 0;

  const kb = {
    open: false, data: null, meta: null, catalog: null, byId: new Map(),
    items: [], cur: -1, tpl: 'cosmic', tplPreview: null, search: '',
    openPages: new Set(), rightTab: 'order', dateLabel: '', demo: null,
    play: { on: false, t: 0, raf: 0, last: 0 }, importing: false,
    sortTouch: false, primeT: 0, resolve: null, toastT: 0, key: null,
    auto: false, autoOpts: null, autoFp: '', elSel: -1, undo: [], redo: [],
    mode: 'edit', dirty: false, saveT: 0, adPick: false, baseEls: new Map(), transit: null,
    privacyStyle: 'soft', model: 'cosmic',
    layersOpen: true, quickOpen: false, lastTap: null, quickBusy: false, quickEdit: false, quickT: 0,
    detOpen: false
  };

  function kbCur() { return kb.items[kb.cur] || null; }
  function kbActiveItems() { return kb.items.filter(it => it.enabled !== false); }
  function kbAllEls() { const out = []; (kb.catalog ? kb.catalog.pages : []).forEach(p => p.elements.forEach(el => out.push(el))); return out; }
  function kbItemEls(it) { return it && it.els && it.els.length ? it.els : []; }
  function kbItemMainEl(it) { return (it && (it.el || (it.els && it.els[0] && it.els[0].el))) || null; }
  function kbHasEl(id) { return kb.items.some(it => it.el && it.el.id === id); }
  function kbDefaultSet(tplId) {
    const def = kbTplDef(tplId || kb.tpl);
    return {
      anim: 'auto', entry: 'auto', exit: 'fade', trans: 'smooth', speed: 1,
      depth: 24, rotX: 0, rotY: 0, scale: 1, persp: 900, shadow: true,
      border: true, bg: 'auto', align: 'center', visible: true, pad: 26, radius: def.radius
    };
  }
  function kbOriginalSet(tplId) {
    return Object.assign(kbDefaultSet(tplId), {
      depth: 0, rotX: 0, rotY: 0, scale: 1, shadow: true, border: false,
      bg: 'none', align: 'center', pad: 0, radius: 0, anim: 'auto', entry: 'auto',
      exit: 'fade', trans: 'smooth', speed: 1, visible: true
    });
  }
  function kbMakeItem(el) {
    const it = { uid: 'kbi' + (++kbItemSeq) + Date.now().toString(36), el: el, dur: el.dur || 6, gap: KB_DEF_GAP, tpl: kb.tpl, set: kbDefaultSet() };
    /* A catalog document that scrolls needs the multi-element renderer so
       its tall SVG is clipped and travelled through, not squeezed into one
       card-sized image. */
    if (el && el.scroll) {
      const box = [58, 170, 604, 1052];
      it.els = [{
        id: 'e1', key: el.id, el: el, box: box, z: 1, visible: true,
        scroll: true, scrollBbox: (el.scrollBbox || el.bbox || box).slice(),
        anim: { entry: 'fade', delay: .1, dur: .7, kind: 'none' }, group: '', locked: false
      }];
      it.mode = 'free';
      it.cardBox = [46, 168, 628, 1056];
      it.chrome = false;
      it.scrollDur = el.scrollDur || 28;
      it.scrollDelay = el.scrollDelay != null ? el.scrollDelay : .8;
      it.hideScrollBar = el.hideScrollBar !== false;
      it.dur = Math.max(it.dur, it.scrollDur + 4);
    }
    return it;
  }
  function kbEnsureFree(it) {
    if (!it) return [];
    if (it.els && it.els.length) return it.els;
    const scene = { tpl: it.tpl || kb.tpl, el: it.el, set: it.set || kbDefaultSet(), dur: it.dur || 6 };
    const card = kbSceneCard(scene, kbTplDef(scene.tpl), scene.set);
    it.els = [{ id: 'e1', key: it.el.id, el: it.el, box: [card.ix, card.iy, card.iw, card.ih], z: 1, visible: true, anim: { entry: 'fade' }, group: '', locked: false }];
    it.mode = 'free';
    it.cardBox = [card.x, card.y, card.w, card.h];
    it.chrome = true;
    return it.els;
  }
  /* ─────────────────── Timeline scene schema v2 ───────────────────
     The Timeline inspector edits the very same scene the builder renders.
     Every exported element therefore carries a small, stable edit model:
     text runs, manual flags and an explicit in/out window. The window is
     scene-local seconds; the renderer reads it instead of guessing from the
     stagger index, so a Timeline trim and the builder preview agree. */
  function kbDecodeEnt(s) {
    return String(s == null ? '' : s).replace(/&(#x?[0-9a-f]+|[a-z]+);/gi, (m, n) => {
      if (n[0] === '#') {
        const code = n[1] === 'x' || n[1] === 'X' ? parseInt(n.slice(2), 16) : parseInt(n.slice(1), 10);
        return isFinite(code) ? String.fromCharCode(code) : m;
      }
      const E = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ' };
      return E[n.toLowerCase()] != null ? E[n.toLowerCase()] : m;
    });
  }
  function kbTextRunsOf(el) {
    const out = [];
    const inner = el && el.inner || '';
    const re = /<text\b([^>]*)>([\s\S]*?)<\/text>/g;
    let m, guard = 0;
    while ((m = re.exec(inner)) && guard++ < 900) {
      const attrs = {};
      String(m[1] || '').replace(/([a-zA-Z-]+)\s*=\s*"([^"]*)"/g, (x, k, v) => { attrs[k] = v; return x; });
      const text = kbDecodeEnt(String(m[2] || '').replace(/<[^>]*>/g, ' ')).replace(/\s+/g, ' ').trim();
      if (!text) continue;
      out.push({
        id: (el.id || 'el') + '-t' + out.length,
        text: text,
        x: +attrs.x || 0, y: +attrs.y || 0,
        size: +attrs['font-size'] || 14,
        color: attrs.fill || '', weight: +attrs['font-weight'] || 500,
        font: attrs['font-family'] || '', anchor: attrs['text-anchor'] || 'start'
      });
    }
    return out;
  }
  function kbSceneElOf(e, idx, scene) {
    const el = Object.assign({}, e.el || {});
    const anim = Object.assign({}, e.anim || {});
    const stagger = scene.set && scene.set.stagger != null ? +scene.set.stagger : .07;
    const start = e.in != null ? +e.in : (+anim.delay || 0) + stagger * idx;
    const end = e.out != null ? +e.out : (scene.dur != null ? +scene.dur : (el.dur || 8));
    return {
      id: e.id || el.id || ('e' + (idx + 1)),
      key: e.key || el.id || '',
      el: el,
      box: e.box ? e.box.slice() : (el.bbox ? el.bbox.slice() : [0, 0, 720, 1280]),
      z: e.z || idx + 1, visible: e.visible !== false,
      scroll: !!e.scroll,
      scrollBbox: e.scrollBbox ? e.scrollBbox.slice() : null,
      anim: anim, group: e.group || '', locked: !!e.locked,
      in: Math.round(Math.max(0, start) * 1000) / 1000,
      out: Math.round(Math.max(0, end) * 1000) / 1000,
      /* The astrologer portrait is element state, not a page screenshot.
         Without copying adSrc here the photo would render in the builder
         preview but silently disappear the moment the card is imported. */
      adSrc: e.adSrc || '',
      privacy: e.privacy && typeof e.privacy === 'object' ? Object.assign({}, e.privacy) : null,
      manual: { text: false, style: false, box: false, timing: false, visibility: false, photo: !!e.photoTouched || !!e.adSrc },
      textRuns: kbTextRunsOf(el)
    };
  }
  function kbCloneElDef(el) {
    if (!el || typeof el !== 'object') return null;
    const c = Object.assign({}, el);
    if (el.bbox) c.bbox = el.bbox.slice();
    if (el.scrollBbox) c.scrollBbox = el.scrollBbox.slice();
    if (el.textStyle) c.textStyle = Object.assign({}, el.textStyle);
    if (el.panelStyle) c.panelStyle = Object.assign({}, el.panelStyle);
    return c;
  }
  function kbSceneOf(item, i, list, tplOverride) {
    const prev = i > 0 ? list[i - 1] : null;
    const main = kbItemMainEl(item) || {};
    const tpl = tplOverride || item.tpl || kb.tpl;
    const scene = {
      schema: 2, v: KB_VERSION, tpl: tpl, modelKey: item.modelKey || kb.model || tpl,
      el: main, dur: item.dur, gap: item.gap,
      /* Stable identity for the Phase 10 import merge. `autoKey` survives a
         model switch, so Cosmic → Nebula → Cosmic matches the same card even
         when element ids or card order shift. */
      autoKey: item.autoKey || '', autoNo: item.autoNo || (i + 1),
      no: i + 1, total: list.length, set: item.set, date: kb.dateLabel,
      transition: item.set && item.set.trans || 'smooth',
      background: { on: !(item.set && item.set.bg === 'none'), kind: (item.set && item.set.bg) || 'glass' },
      decorations: [],
      footerOn: true,
      manual: { dur: false, gap: false, transition: false, visible: false, background: false, footer: false },
      privacyStyle: item.privacyStyle || kb.privacyStyle || 'soft',
      privacy: item.privacy || null,
      prevTrans: prev ? prev.set.trans : 'cut', prevGap: prev ? prev.gap : 0,
      suppressEntry: !!(prev && prev.gap >= .2 && prev.set.trans !== 'cut')
    };
    if (item.els && item.els.length) {
      /* Clone the wrappers and element metadata. The builder keeps ownership
         of its own item objects; a later builder edit must not silently
         rewrite a scene already imported into the Timeline. */
      scene.els = item.els.map((e, idx) => kbSceneElOf(e, idx, scene));
      scene.mode = item.mode || 'free';
      scene.cardBox = item.cardBox ? item.cardBox.slice() : [46, 168, 628, 1056];
      scene.chrome = !!item.chrome;
      scene.title = item.title || '';
      scene.archetype = item.archetype || item.flow || item.autoKey || '';
      if (item.scrollDur) { scene.scrollDur = item.scrollDur; scene.scrollDelay = item.scrollDelay; }
      if (item.hideScrollBar) scene.hideScrollBar = true;
      if (item.ad) scene.ad = item.ad;
      if (item.hotspot) { scene.hotspot = item.hotspot; scene.hotspotUrl = item.hotspotUrl; }
      if (item.sav) scene.sav = item.sav;
    }
    return scene;
  }
  function kbTotalTime(items) { return (items || []).reduce((a, it) => a + it.dur + it.gap, 0); }
  function kbSceneStart(items, i) { let a = 0; for (let j = 0; j < i; j++) a += items[j].dur + items[j].gap; return a; }
  function kbSceneAt(items, t) {
    let acc = 0;
    for (let i = 0; i < items.length; i++) {
      const d = items[i].dur + items[i].gap;
      if (t < acc + d || i === items.length - 1) return { i: i, local: clamp(t - acc, 0, d) };
      acc += d;
    }
    return { i: 0, local: 0 };
  }
  function kbFmtTime(s) {
    s = Math.max(0, s || 0);
    const m = Math.floor(s / 60), r = Math.floor(s % 60);
    return m + ':' + String(r).padStart(2, '0');
  }
  function kbPreviewItems() {
    if (kb.tplPreview && !kb.items.length) return kbDemoItems();
    return kbActiveItems();
  }
  function kbDemoItems() {
    if (kb.demo) return kb.demo;
    const all = kbAllEls();
    const picked = [];
    ['chart', 'table', 'cards', 'report', 'heading'].forEach(type => {
      const e = all.find(x => x.type === type && picked.indexOf(x) < 0);
      if (e) picked.push(e);
    });
    all.forEach(e => { if (picked.length < 4 && picked.indexOf(e) < 0 && e.type !== 'footer') picked.push(e); });
    kb.demo = picked.slice(0, 4).map(e => ({ uid: 'kbdemo' + e.id, el: e, dur: 5.2, gap: .5, tpl: kb.tplPreview || kb.tpl, set: kbDefaultSet(kb.tplPreview || kb.tpl) }));
    return kb.demo;
  }
  function kbPrimeSoon(els) {
    if (!els || !els.length) return;
    clearTimeout(kb.primeT);
    kb.primeT = setTimeout(() => {
      if (!kb.open) return;
      kbPrimeEls(els).then(() => { if (kb.open) kbDrawPreview(kb.play.t); });
    }, 30);
  }
  function kbToast(msg, kind) {
    const t = q('kb-toast'); if (!t) return;
    t.textContent = msg; t.className = 'kb-toast on' + (kind ? ' ' + kind : '');
    clearTimeout(kb.toastT);
    kb.toastT = setTimeout(() => { t.className = 'kb-toast'; }, 2400);
  }
  function kbMsg(msg, kind) {
    const m = q('kb-msg'); if (!m) return;
    m.textContent = msg || ''; m.className = 'kb-msg' + (kind ? ' ' + kind : '');
  }

  const KB_HTML = `
<div id="kun-builder">
  <div class="kb-back"></div>
  <div class="kb-shell">
    <div class="kb-head">
      <div class="kb-brand">
        <div class="kb-orb"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="7.5"/><ellipse cx="12" cy="12" rx="11" ry="4" transform="rotate(-24 12 12)"/><circle cx="12" cy="12" r="1.8" fill="currentColor" stroke="none"/></svg></div>
        <div><b>कुण्डली ३डी टाइमलाइन</b><small id="kb-meta">—</small></div>
      </div>
      <div class="kb-head-mid">
        <span class="kb-step on"><i>1</i> स्क्यान</span>
        <span class="kb-step"><i>2</i> छान्नुहोस्</span>
        <span class="kb-step"><i>3</i> क्रम + 3D</span>
        <span class="kb-step"><i>4</i> प्रिभ्यू</span>
        <span class="kb-step"><i>5</i> लागू</span>
      </div>
      <div class="kb-head-actions">
        <button class="kb-auto-btn" id="kb-auto" title="AUTOMATIC — वास्तविक कुण्डली डेटाबाट पूर्ण कार्ड सेट बनाउनुहोस्" aria-label="AUTOMATIC Kundali timeline">
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="m12 3 1.55 4.45L18 9l-4.45 1.55L12 15l-1.55-4.45L6 9l4.45-1.55z"/><path d="m19 15 .8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/></svg>
          <span>AUTOMATIC</span>
        </button>
        <button class="kb-icon-btn" id="kb-undo" title="Undo"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M9 7 4 12l5 5"/><path d="M5 12h8a6 6 0 0 1 6 6v1"/></svg></button>
        <button class="kb-icon-btn" id="kb-redo" title="Redo"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="m15 7 5 5-5 5"/><path d="M19 12h-8a6 6 0 0 0-6 6v1"/></svg></button>
        <button class="kb-icon-btn" id="kb-save" title="Save layout"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M5 4h11l3 3v13H5z"/><path d="M8 4v6h8V4M8 20v-6h8v6"/></svg></button>
        <button class="kb-icon-btn" id="kb-mode" title="Editing / Presentation mode"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg></button>
        <button class="kb-icon-btn" id="kb-safe" title="Safe margin guides" aria-pressed="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="4" y="4" width="16" height="16" rx="2" stroke-dasharray="3 2"/><path d="M8 4v2M4 8h2M16 4v2M20 8h-2M8 20v-2M4 16h2M16 20v-2M20 16h-2"/></svg></button>
        <button class="kb-icon-btn" id="kb-focus" title="Focus preview"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7"><path d="M4 9V5a1 1 0 0 1 1-1h4M20 9V5a1 1 0 0 0-1-1h-4M4 15v4a1 1 0 0 0 1 1h4M20 15v4a1 1 0 0 1-1 1h-4"/></svg></button>
        <button class="kb-icon-btn" id="kb-close" title="Close"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="m6 6 12 12M18 6 6 18"/></svg></button>
      </div>
    </div>
    <div class="kb-mobile-tabs">
      <button data-mtab="elements">तत्व <span id="kb-mt-el">0</span></button>
      <button data-mtab="preview">प्रिभ्यू</button>
      <button data-mtab="settings">सेटिङ</button>
    </div>
    <div class="kb-main">
      <aside class="kb-left">
        <div class="kb-pane-head">
          <div class="kb-pane-title"><b>कुण्डली तत्वहरू</b><span class="kb-count" id="kb-elcount">0</span></div>
          <div class="kb-sub">हरेक पृष्ठ, चार्ट, तालिका, कार्ड, रिपोर्ट र सजावट छुट्टै दृश्य हो।</div>
          <input class="kb-search" id="kb-search" placeholder="तत्व, प्रकार वा पृष्ठ खोज्नुहोस्…">
          <div class="kb-mini-actions">
            <button class="kb-mini" id="kb-selall">Select All</button>
            <button class="kb-mini" id="kb-deselall">Deselect All</button>
            <button class="kb-mini" id="kb-expand">Expand</button>
          </div>
        </div>
        <div class="kb-tree" id="kb-tree"></div>
      </aside>
      <section class="kb-center">
        <div class="kb-stage-wrap">
          <div class="kb-stage safe" id="kb-stage">
            <canvas id="kb-canvas" width="720" height="1280"></canvas>
            <div class="kb-safe"></div>
            <div class="kb-overlay" id="kb-overlay">
              <div class="kb-selbox" id="kb-selbox" hidden>
                <span class="kb-selname" id="kb-selname"></span>
                <i class="kb-h nw" data-h="nw"></i><i class="kb-h n" data-h="n"></i><i class="kb-h ne" data-h="ne"></i>
                <i class="kb-h w" data-h="w"></i><i class="kb-h e" data-h="e"></i>
                <i class="kb-h sw" data-h="sw"></i><i class="kb-h s" data-h="s"></i><i class="kb-h se" data-h="se"></i>
                <span class="kb-guide v" id="kb-guide-v"></span>
                <span class="kb-guide hz" id="kb-guide-h"></span>
              </div>
            </div>
            <div class="kb-stage-badge"><i></i><span id="kb-stage-name">Live preview</span></div>
            <div class="kb-stage-info" id="kb-stage-info">—</div>
          </div>
        </div>
        <div class="kb-quickbar" id="kb-quickbar">
          <button class="kb-qbtn strong" data-quick="text" title="नयाँ पाठ थप्नुहोस्">＋ पाठ</button>
          <button class="kb-qbtn" data-quick="frame" title="छानिएको पाठको पछाडि फ्रेम थप्नुहोस्">▣ फ्रेम</button>
          <button class="kb-qbtn" data-quick="panel" title="पाठ राख्न प्यानल थप्नुहोस्">▤ प्यानल</button>
          <button class="kb-qbtn" data-quick="style" title="छानिएको तत्वको स्टाइल, इफेक्ट र समय">✨ स्टाइल</button>
          <button class="kb-qbtn" data-quick="layers" title="लेयर टाइमलाइन खोल्नुहोस् / बन्द गर्नुहोस्">☰ लेयर</button>
        </div>
        <div class="kb-transport">
          <input class="kb-scrub" id="kb-scrub" type="range" min="0" max="1000" step="0.5" value="0">
          <div class="kb-tr-row">
            <button class="kb-tr-btn" id="kb-prev" title="Previous scene"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 18-6-6 6-6"/></svg></button>
            <button class="kb-tr-btn play" id="kb-play" title="Play / pause"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5.5v13l11-6.5z"/></svg></button>
            <button class="kb-tr-btn" id="kb-next" title="Next scene"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg></button>
            <span class="kb-tr-live" id="kb-live">3D LIVE</span>
            <span class="kb-tr-time" id="kb-time">0:00 / 0:00</span>
          </div>
          <div class="kb-scroll-ctl" id="kb-scroll-ctl" hidden>
            <span class="kb-scroll-label">नेपाली चिना स्क्रोल</span>
            <button class="kb-mini" id="kb-scroll-pause">Pause</button>
            <button class="kb-mini" id="kb-scroll-replay">Replay</button>
            <span class="kb-scroll-pct" id="kb-scroll-pct">0%</span>
          </div>
        </div>
        <div class="kb-scene-strip" id="kb-scenes"></div>
        <div class="kb-layerbar" id="kb-layerbar"></div>
      </section>
      <aside class="kb-right">
        <div class="kb-right-tabs">
          <button class="kb-rtab on" data-tab="order">क्रम</button>
          <button class="kb-rtab" data-tab="templates">टेम्प्लेट</button>
          <button class="kb-rtab" data-tab="settings">सेटिङ</button>
        </div>
        <div class="kb-right-body" id="kb-right-body"></div>
      </aside>
    </div>
    <div class="kb-qsheet" id="kb-qsheet" hidden>
      <div class="kb-qsheet-back" data-q-close="1"></div>
      <div class="kb-qsheet-card" role="dialog" aria-modal="true" aria-label="तत्व स्टाइल">
        <div class="kb-qsheet-head">
          <div><b>तत्व स्टाइल</b><small id="kb-qsheet-sub">पाठ, फ्रेम, इफेक्ट र समय</small></div>
          <button class="kb-icon-btn" data-q-close="1" title="बन्द" aria-label="बन्द">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="m6 6 12 12M18 6 6 18"/></svg>
          </button>
        </div>
        <div class="kb-qsheet-body" id="kb-qsheet-body"></div>
      </div>
    </div>
    <div class="kb-foot">
      <div class="kb-foot-stat" id="kb-stat">—</div>
      <div class="kb-msg" id="kb-msg"></div>
      <div class="kb-foot-spacer"></div>
      <button class="kb-btn" id="kb-default">डिफल्ट टाइमलाइन</button>
      <button class="kb-btn" id="kb-cancel">रद्द</button>
      <button class="kb-btn primary" id="kb-import">टाइमलाइनमा लागू गर्नुहोस्</button>
    </div>
    <div class="kb-confirm" id="kb-confirm" hidden>
      <div class="kb-confirm-card" role="dialog" aria-modal="true" aria-label="Confirm timeline import">
        <h3>टाइमलाइनमा लागू गर्ने?</h3>
        <p>यो कुण्डलीका छानिएका तत्वहरूबाट नयाँ ३डी दृश्य टाइमलाइन बन्नेछ। हालको प्रोजेक्ट save हुन्छ, त्यसपछि नयाँ कुण्डली प्रोजेक्ट खुल्नेछ।</p>
        <div class="kb-confirm-sum" id="kb-confirm-sum"></div>
        <div class="kb-confirm-actions">
          <button class="kb-btn" id="kb-conf-preview">प्रिभ्यू हेर्नुहोस्</button>
          <button class="kb-btn" id="kb-conf-back">फिर्ता</button>
          <button class="kb-btn primary" id="kb-conf-ok">हो, लागू गर्नुहोस्</button>
        </div>
      </div>
    </div>
    <div class="kb-models" id="kb-models" hidden>
      <div class="kb-models-card" role="dialog" aria-modal="true" aria-label="डिजाइन मोडेल छान्नुहोस्">
        <div class="kb-models-head">
          <div>
            <h3>डिजाइन मोडेल छान्नुहोस्</h3>
            <p>एउटै कुण्डली सामग्री, चार फरक भिजुअल भाषा। तलको नमुना कार्ड र एनिमेसन चिप हेरेर छान्नुहोस् — ब्याकग्राउन्ड, कार्ड रचना, टाइपोग्राफी, एनिमेसन र ट्रान्जिसन सबै फरक छन्। पछि फेरि बदल्न सकिन्छ — पाठ सम्पादन सुरक्षित रहन्छ।</p>
          </div>
          <button class="kb-icon-btn" data-model-close="1" title="बन्द"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="m6 6 12 12M18 6 6 18"/></svg></button>
        </div>
        <div class="kb-models-grid" id="kb-models-grid"></div>
        <div class="kb-models-foot"><span>हाल सक्रिय: <b id="kb-model-active">—</b></span><button class="kb-btn" data-model-close="1">रद्द</button></div>
      </div>
    </div>
    <div class="kb-toast" id="kb-toast"></div>
  </div>
</div>`;

  function kbIsNarrow() { return !!(window.matchMedia && window.matchMedia('(max-width: 820px)').matches); }
  function kbSetMobileView(v) {
    const b = q('kun-builder'); if (!b) return;
    b.dataset.mview = v;
    b.querySelectorAll('.kb-mobile-tabs [data-mtab]').forEach(x => x.classList.toggle('on', x.dataset.mtab === v));
    if (v === 'preview') setTimeout(() => { if (kb.open) kbDrawPreview(kb.play.t); }, 30);
  }
  function kbHideConfirm() { const c = q('kb-confirm'); if (c) c.hidden = true; }
  function kbAskImport() {
    if (kb.importing) return;
    if (!kbActiveItems().length) {
      kbMsg('कम्तीमा एक दृश्य सक्रिय छान्नुहोस्, वा “डिफल्ट टाइमलाइन” थिच्नुहोस्।', 'err');
      kbToast('कुनै दृश्य सक्रिय छैन।', 'err');
      return;
    }
    kbStop();
    const counts = {};
    kbActiveItems().forEach(it => { const t = (it.el || {}).type || 'note'; counts[t] = (counts[t] || 0) + 1 });
    const typeLine = Object.keys(counts).map(t => (KB_TYPE_NE[t] || t) + ' ' + kbNum(counts[t])).join(' · ');
    const def = kbTplDef(kb.tplPreview || kb.tpl);
    const sum = q('kb-confirm-sum');
    const active = kbActiveItems();
    if (sum) sum.innerHTML =
      '<b>' + kbNum(active.length) + '</b> दृश्य · कुल <b>' + kbFmtTime(kbTotalTime(active)) + '</b><br>' +
      'टेम्प्लेट: <b>' + kbEsc(def.name) + '</b><br>' +
      'समावेश: ' + kbEsc(kb.auto ? 'वास्तविक कुण्डली कार्ड' : typeLine) + '<br>' +
      '<span style="color:var(--kb-dim)">पहिलो दृश्य: ' + kbEsc(active[0].title || active[0].el.name) + ' · अन्तिम: ' + kbEsc(active[active.length - 1].title || active[active.length - 1].el.name) + '</span>';
    const c = q('kb-confirm'); if (c) c.hidden = false;
  }
  function kbMount() {
    const old = q('kun-builder'); if (old) old.remove();
    document.body.insertAdjacentHTML('beforeend', KB_HTML);
    q('kb-close').onclick = kbCancel;
    q('kb-cancel').onclick = kbCancel;
    const autoBtn = q('kb-auto');
    if (autoBtn) autoBtn.onclick = () => kbShowModels();
    const modelBox = q('kb-models');
    if (modelBox) modelBox.addEventListener('click', ev => {
      const pick = ev.target.closest('[data-model-pick]');
      if (pick) { kbPickModel(pick.getAttribute('data-model-pick')); return; }
      if (ev.target === modelBox || ev.target.closest('[data-model-close]')) kbHideModels();
    });
    q('kb-default').onclick = kbDefault;
    q('kb-import').onclick = kbAskImport;
    q('kb-conf-back').onclick = kbHideConfirm;
    q('kb-conf-preview').onclick = () => {
      kbHideConfirm(); kb.play.t = 0; kbSetMobileView('preview');
      kbSeek(0); if (!kb.play.on) kbPlayToggle();
    };
    q('kb-conf-ok').onclick = () => { kbHideConfirm(); kbImport(); };
    document.querySelector('#kun-builder .kb-back').onclick = kbCancel;
    document.querySelectorAll('#kun-builder .kb-mobile-tabs [data-mtab]').forEach(b => {
      b.onclick = () => kbSetMobileView(b.dataset.mtab);
    });
    kbSetMobileView(kbIsNarrow() ? 'elements' : 'preview');
    q('kb-safe').onclick = () => {
      const st = q('kb-stage'); st.classList.toggle('safe');
      q('kb-safe').setAttribute('aria-pressed', st.classList.contains('safe') ? 'true' : 'false');
    };
    q('kb-focus').onclick = () => {
      q('kun-builder').classList.toggle('kb-focus');
      if (kbIsNarrow()) kbSetMobileView('preview');
      setTimeout(() => kbDrawPreview(kb.play.t), 40);
    };
    const undoBtn = q('kb-undo');
    if (undoBtn) undoBtn.onclick = kbUndo;
    const redoBtn = q('kb-redo');
    if (redoBtn) redoBtn.onclick = kbRedo;
    const saveBtn = q('kb-save');
    if (saveBtn) saveBtn.onclick = () => {
      if (kb.auto) kbAutoSave(true);
      else kbToast('लेआउट सुरक्षित गर्न AUTOMATIC मोड प्रयोग गर्नुहोस्।');
    };
    const modeBtn = q('kb-mode');
    if (modeBtn) modeBtn.onclick = () => {
      kb.mode = kb.mode === 'present' ? 'edit' : 'present';
      const root = q('kun-builder'); if (root) root.dataset.mode = kb.mode;
      modeBtn.setAttribute('aria-pressed', kb.mode === 'present' ? 'true' : 'false');
      if (kb.mode === 'present') { q('kb-selbox') && (q('kb-selbox').hidden = true); if (!kb.play.on) kbPlayToggle(); }
      else { kbSyncOverlay(); if (kb.play.on) kbPlayToggle(); }
      setTimeout(() => kbDrawPreview(kb.play.t), 40);
    };
    const rootEl = q('kun-builder'); if (rootEl) rootEl.dataset.mode = kb.mode || 'edit';
    q('kb-selall').onclick = () => { kbAllEls().forEach(el => { if (!kbHasEl(el.id)) kb.items.push(kbMakeItem(el)); }); if (kb.cur < 0 && kb.items.length) kb.cur = 0; kbPrimeSoon(kb.items.map(it => it.el)); kbRenderAll(); kbToast('सबै ' + kb.items.length + ' तत्व छानिए।'); };
    q('kb-deselall').onclick = () => { kb.items.length = 0; kb.cur = -1; kbStop(); kbRenderAll(); kbToast('सबै तत्व हटाइए — अब डिफल्ट टाइमलाइन राख्न सकिन्छ।'); };
    q('kb-expand').onclick = () => {
      const all = (kb.catalog ? kb.catalog.pages : []).every(p => kb.openPages.has(p.no));
      if (all) kb.openPages.clear(); else (kb.catalog ? kb.catalog.pages : []).forEach(p => kb.openPages.add(p.no));
      kbRenderTree();
    };
    q('kb-search').oninput = e => {
      clearTimeout(kbSearchTimer);
      const v = e.target.value;
      kbSearchTimer = setTimeout(() => { kb.search = v; kbRenderTree(); }, 110);
    };
    q('kb-tree').addEventListener('click', e => {
      if (e.target.closest('input')) return;
      const all = e.target.closest('[data-page-all]');
      if (all) { e.stopPropagation(); kbSelectPage(+all.dataset.pageAll); return; }
      const head = e.target.closest('[data-page-head]');
      if (head) {
        const p = +head.dataset.pageHead;
        if (kb.openPages.has(p)) kb.openPages.delete(p); else kb.openPages.add(p);
        kbRenderTree(); return;
      }
      const add = e.target.closest('[data-el-add]');
      if (add) { const f = kb.byId.get(add.dataset.elAdd); if (f) kbAddEl(f.el); return; }
      const row = e.target.closest('[data-el]');
      if (row) { const f = kb.byId.get(row.dataset.el); if (f) kbToggleEl(f.el); }
    });
    q('kb-tree').addEventListener('change', e => {
      const t = e.target;
      if (t.matches('[data-page-check]')) {
        const p = +t.dataset.pageCheck;
        if (t.checked) kbSelectPage(p); else kbDeselectPage(p);
      } else if (t.matches('[data-el-check]')) {
        const f = kb.byId.get(t.dataset.elCheck); if (f) kbToggleEl(f.el);
      }
    });
    q('kb-right-body').addEventListener('click', kbRightClick);
    q('kb-right-body').addEventListener('input', e => kbRightField(e, false));
    q('kb-right-body').addEventListener('change', e => kbRightField(e, true));
    const rTabs = document.querySelector('#kun-builder .kb-right-tabs');
    if (rTabs) rTabs.addEventListener('click', kbRightClick);
    kbBindOrderDnd();
    kbBindSceneSort();
    kbBindLayerBar();
    kbBindLayerSort();
    const quickbar = q('kb-quickbar');
    if (quickbar) quickbar.addEventListener('click', ev => {
      const b = ev.target.closest('[data-quick]');
      if (b) kbQuickMain(b.dataset.quick);
    });
    const qsheet = q('kb-qsheet');
    if (qsheet) {
      qsheet.addEventListener('click', ev => {
        if (ev.target.closest('[data-q-close]')) { kbCloseQuick(); return; }
        const a = ev.target.closest('[data-qact]');
        if (a) { kbQuickAct(a.dataset.qact, +a.dataset.j, a.dataset.val); return; }
      });
      qsheet.addEventListener('input', ev => { if (ev.target.matches('[data-q]')) kbQuickField(ev.target, false); });
      qsheet.addEventListener('change', ev => { if (ev.target.matches('[data-q]')) kbQuickField(ev.target, true); });
    }
    kb.layersOpen = !kbIsNarrow();
    q('kb-right-body').addEventListener('toggle', ev => {
      if (ev.target && ev.target.matches && ev.target.matches('.kb-details')) kb.detOpen = ev.target.open;
    }, true);
    q('kb-play').onclick = kbPlayToggle;
    q('kb-prev').onclick = () => kbStep(-1);
    q('kb-next').onclick = () => kbStep(1);
    const scPause = q('kb-scroll-pause'), scReplay = q('kb-scroll-replay');
    if (scPause) scPause.onclick = () => { kbPlayToggle(); kbDrawPreview(kb.play.t); };
    if (scReplay) scReplay.onclick = () => {
      const items = kbPreviewItems(); if (!items.length) return;
      const at = kbSceneAt(items, kb.play.t);
      kbStop(); kbSeek(kbSceneStart(items, at.i));
      if (!kb.play.on) kbPlayToggle();
    };
    q('kb-scrub').oninput = e => {
      kbStop();
      const items = kbPreviewItems(), total = kbTotalTime(items);
      kbSeek((+e.target.value / 1000) * total);
    };
    q('kb-scenes').onclick = e => {
      const b = e.target.closest('[data-scene]'); if (!b) return;
      const items = kbPreviewItems(), i = +b.dataset.scene;
      kbStop(); kbSeek(kbSceneStart(items, i));
      kbFocusItem(items, i);
    };
    kb.key = kbKey;
    document.addEventListener('keydown', kb.key);
    kbBindOverlay();
    setTimeout(kbSyncOverlay, 80);
    const totalEls = kbAllEls().length;
    q('kb-meta').textContent = (kb.meta.name || '—') + ' · ' + kb.dateLabel + ' · ' + (kb.meta.city || kb.meta.birth_place || '') + ' · ' + (kb.catalog ? kb.catalog.pages.length : 0) + ' पृष्ठ / ' + totalEls + ' तत्व';
  }

  function kbKey(e) {
    if (!kb.open) return;
    const typing = /INPUT|TEXTAREA|SELECT/.test((document.activeElement && document.activeElement.tagName) || '');
    if (e.key === 'Escape') {
      e.preventDefault();
      const cf = q('kb-confirm');
      if (cf && !cf.hidden) { kbHideConfirm(); return; }
      const el = q('kun-builder');
      if (el && el.classList.contains('kb-focus')) el.classList.remove('kb-focus');
      else kbCancel();
    } else if (!typing && e.code === 'Space') { e.preventDefault(); kbPlayToggle(); }
    else if (!typing && e.key === 'ArrowRight') { e.preventDefault(); kbStep(1); }
    else if (!typing && e.key === 'ArrowLeft') { e.preventDefault(); kbStep(-1); }
  }

  function kbRenderAll() {
    if (!kb.open) return;
    if (kb.items.length && (kb.cur < 0 || kb.cur >= kb.items.length)) kb.cur = Math.max(0, Math.min(kb.items.length - 1, kb.cur));
    if (!kb.items.length) kb.cur = -1;
    kbRenderTree();
    kbRenderRight();
    kbRenderScenes();
    kbRenderLayers();
    if (kb.quickOpen) kbRenderQuickSheet();
    kbUpdateStat();
    kbDrawPreview(kb.play.t);
  }

  function kbRenderTree() {
    const tree = q('kb-tree'); if (!tree) return;
    const keep = tree.scrollTop;
    const search = kb.search.trim().toLowerCase();
    let html = '';
    (kb.catalog ? kb.catalog.pages : []).forEach(page => {
      const els = page.elements.filter(el => {
        if (!search) return true;
        const hay = (el.name + ' ' + el.type + ' ' + page.title + ' ' + page.no + ' ' + (KB_TYPE_NE[el.type] || '')).toLowerCase();
        return hay.indexOf(search) >= 0;
      });
      if (!els.length) return;
      const open = search ? true : kb.openPages.has(page.no);
      const allSel = els.every(el => kbHasEl(el.id));
      html += '<div class="kb-page' + (open ? ' open' : '') + '" data-page="' + page.no + '">' +
        '<div class="kb-page-head" data-page-head="' + page.no + '">' +
        '<input type="checkbox" data-page-check="' + page.no + '"' + (allSel ? ' checked' : '') + ' aria-label="Select page">' +
        '<svg class="kb-page-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 6 6 6-6 6"/></svg>' +
        '<div class="kb-page-meta"><b>' + page.no + '. ' + kbEsc(page.title) + '</b><small>' + kbEsc(page.sub || '') + '</small></div>' +
        '<span class="kb-page-n">' + els.length + '</span>' +
        '<button class="kb-mini" data-page-all="' + page.no + '" title="Select Page">पृष्ठ</button>' +
        '</div><div class="kb-page-els">' +
        els.map(el => {
          const on = kbHasEl(el.id);
          return '<div class="kb-el' + (on ? ' on' : '') + '" data-el="' + kbAttr(el.id) + '">' +
            '<input type="checkbox" data-el-check="' + kbAttr(el.id) + '"' + (on ? ' checked' : '') + ' aria-label="Select element">' +
            '<div class="kb-el-main"><b>' + kbEsc(el.name) + '</b><small>' + (KB_TYPE_NE[el.type] || el.type) + ' · पृष्ठ ' + kbNum(page.no) + '</small></div>' +
            '<button class="kb-el-add" data-el-add="' + kbAttr(el.id) + '" title="Add another copy" aria-label="Add another copy">+</button>' +
            '<span class="kb-type">' + kbEsc(el.type) + '</span></div>';
        }).join('') + '</div></div>';
    });
    tree.innerHTML = html || '<div class="kb-empty">कुनै तत्व भेटिएन।<br>खोज शब्द फेर्नुहोस् वा सबै पृष्ठ खोल्नुहोस्।</div>';
    tree.scrollTop = keep;
    const cnt = q('kb-elcount'); if (cnt) cnt.textContent = kb.items.length + ' छानिएको';
  }

  function kbAddEl(el) {
    kb.items.push(kbMakeItem(el));
    kb.cur = kb.items.length - 1;
    kbPrimeSoon([el]);
    kbRenderAll();
    kbToast('अर्को प्रतिलिपि थपियो: ' + el.name);
  }
  function kbToggleEl(el) {
    if (kbHasEl(el.id)) kbRemoveEl(el.id);
    else {
      kb.items.push(kbMakeItem(el));
      kb.cur = kb.items.length - 1;
      kbPrimeSoon([el]);
    }
    kbRenderAll();
  }
  function kbRemoveEl(id) {
    const at = kb.items.findIndex(it => it.el.id === id);
    if (at < 0) return;
    kb.items.splice(at, 1);
    if (kb.cur >= kb.items.length) kb.cur = kb.items.length - 1;
    kbRenderAll();
  }
  function kbSelectPage(no) {
    const page = (kb.catalog ? kb.catalog.pages : []).find(p => p.no === no);
    if (!page) return;
    let added = 0;
    page.elements.forEach(el => { if (!kbHasEl(el.id)) { kb.items.push(kbMakeItem(el)); added++; } });
    if (kb.cur < 0 && kb.items.length) kb.cur = 0;
    if (added) kbPrimeSoon(page.elements);
    kbRenderAll();
  }
  function kbDeselectPage(no) {
    const page = (kb.catalog ? kb.catalog.pages : []).find(p => p.no === no);
    if (!page) return;
    const ids = new Set(page.elements.map(e => e.id));
    kb.items = kb.items.filter(it => !ids.has(it.el.id));
    if (kb.cur >= kb.items.length) kb.cur = kb.items.length - 1;
    kbRenderAll();
  }

  /* Element id identifies a card across AUTO rebuilds of the same model;
     autoKey is the stable fallback when a design model swaps the card's
     first element. Both are saved so a hand-picked order survives a
     reopen and a model switch. */
  function kbOrderBase(it) {
    const el = it && (it.el || (it.els && it.els[0] && it.els[0].el));
    if (el && el.id) return String(el.id);
    return it && it.autoKey ? String(it.autoKey) : '';
  }
  function kbMoveTo(from, to) {
    if (from === to || from < 0 || from >= kb.items.length) return;
    to = clamp(to, 0, kb.items.length - 1);
    const it = kb.items.splice(from, 1)[0];
    kb.items.splice(to, 0, it);
    if (kb.cur === from) kb.cur = to;
    else if (from < kb.cur && to >= kb.cur) kb.cur--;
    else if (from > kb.cur && to <= kb.cur) kb.cur++;
    kbMarkDirty();
    kbRenderAll();
  }
  /* The scene strip only shows enabled cards. Put the new active sequence
     back into the same active slots so disabled cards keep their place,
     then land the preview on the moved card. */
  function kbReorderActive(from, to) {
    const active = kbActiveItems();
    if (from === to || from < 0 || from >= active.length) return false;
    kbSnap();
    const moved = active.splice(from, 1)[0];
    to = clamp(to, 0, active.length);
    active.splice(to, 0, moved);
    let ai = 0;
    for (let i = 0; i < kb.items.length; i++) {
      if (kb.items[i].enabled !== false) kb.items[i] = active[ai++];
    }
    kb.cur = kb.items.indexOf(moved);
    kb.elSel = (moved.els && moved.els.length) ? 0 : -1;
    kb.tplPreview = null;
    const items = kbPreviewItems();
    const at = items.indexOf(moved);
    if (at >= 0) kb.play.t = kbSceneStart(items, at);
    kbMarkDirty();
    kbRenderAll();
    kbSyncOverlay();
    kbToast('कार्ड क्रम बदलियो: ' + (moved.title || moved.el.name));
    return true;
  }
  function kbMoveItem(i, d) { kbMoveTo(i, i + d); }
  function kbDuplicateItem(i) {
    const it = kb.items[i]; if (!it) return;
    const copy = { uid: 'kbi' + (++kbItemSeq) + Date.now().toString(36), el: it.el, dur: it.dur, gap: it.gap, tpl: it.tpl, set: Object.assign({}, it.set) };
    if (it.els && it.els.length) {
      copy.els = it.els.map((e, n) => Object.assign({}, e, { id: 'e' + Date.now().toString(36) + n, box: e.box ? e.box.slice() : null, anim: Object.assign({}, e.anim || {}), privacy: e.privacy ? Object.assign({}, e.privacy) : null }));
      copy.mode = it.mode || 'free'; copy.cardBox = it.cardBox ? it.cardBox.slice() : null; copy.chrome = it.chrome;
      copy.title = it.title; copy.scrollDur = it.scrollDur; copy.scrollDelay = it.scrollDelay;
      copy.hideScrollBar = !!it.hideScrollBar;
      copy.ad = it.ad ? Object.assign({}, it.ad) : null; copy.hotspot = it.hotspot ? it.hotspot.slice() : null; copy.hotspotUrl = it.hotspotUrl;
      copy.privacyStyle = it.privacyStyle; copy.privacy = it.privacy ? Object.assign({}, it.privacy) : null;
    }
    kb.items.splice(i + 1, 0, copy);
    kb.cur = i + 1;
    kbPrimeSoon(kbSceneEls(kbSceneOf(copy, i + 1, kb.items, null)));
    kbRenderAll();
  }
  function kbReplaceItem(i, elId) {
    const f = kb.byId.get(elId); if (!f) return;
    const it = kb.items[i]; if (!it) return;
    it.el = f.el;
    if (it.dur <= 0) it.dur = f.el.dur;
    kbPrimeSoon([f.el]);
    kbRenderAll();
    kbToast('तत्व बदलियो: ' + f.el.name);
  }

  /* ─────────── pointer sort: mouse + touch card reorder ───────────
     HTML5 drag never fires for touch, so the scene strip and the order
     rows use Pointer Events. A mouse lifts after a few pixels; a finger
     waits for a short press so a horizontal swipe still scrolls the
     card strip. The drop line and the floating ghost make the exact
     landing slot obvious on a phone. */
  let kbSortClickLock = 0;
  document.addEventListener('touchmove', ev => {
    if (kb.sortTouch) { if (ev.cancelable) ev.preventDefault(); }
  }, { passive: false });

  function kbSortClickBlock(box) {
    if (!box || box.dataset.kbSortClick === '1') return;
    box.dataset.kbSortClick = '1';
    box.addEventListener('click', ev => {
      if (performance.now() > kbSortClickLock) return;
      kbSortClickLock = 0;
      ev.preventDefault();
      ev.stopImmediatePropagation();
    }, true);
  }

  function kbBindSortable(box, spec) {
    if (!box || !spec || box.dataset.kbSortable === '1') return;
    box.dataset.kbSortable = '1';
    const axis = spec.axis === 'x' ? 'x' : 'y';
    const itemAt = el => (el && el.closest ? el.closest(spec.item) : null);
    const liveItems = () => Array.prototype.slice.call(box.querySelectorAll(spec.item))
      .filter(el => !el.classList.contains('kb-sort-source'));
    const coord = ev => (axis === 'x' ? ev.clientX : ev.clientY);
    const scrollOf = () => (spec.scroller ? spec.scroller() : box);
    let press = null, drag = null;

    function detach() {
      document.removeEventListener('pointermove', onMove);
      document.removeEventListener('pointerup', onUp, true);
      document.removeEventListener('pointercancel', onCancel, true);
    }
    function clearPress() {
      if (press && press.hold) clearTimeout(press.hold);
      if (press) press.hold = 0;
      detach();
      press = null;
    }
    function cleanup(commit) {
      const d = drag;
      drag = null;
      if (d) {
        if (d.ghost && d.ghost.parentNode) d.ghost.parentNode.removeChild(d.ghost);
        if (d.line && d.line.parentNode) d.line.parentNode.removeChild(d.line);
        d.src.classList.remove('kb-sort-source');
        if (d.raf) cancelAnimationFrame(d.raf);
        document.body.classList.remove('kb-sort-active');
        kb.sortTouch = false;
        if (commit && d.from >= 0 && d.target != null && d.from !== d.target) {
          kbSortClickLock = performance.now() + 320;
          spec.onDrop(d.from, d.target);
        } else if (commit && d.from >= 0 && d.target != null) {
          kbSortClickLock = performance.now() + 180;
        }
      }
      clearPress();
    }
    function place(ev) {
      if (!drag) return;
      drag.last = ev;
      drag.ghost.style.left = (ev.clientX - drag.offX) + 'px';
      drag.ghost.style.top = (ev.clientY - drag.offY) + 'px';
      const sc = scrollOf();
      if (sc) {
        const r = sc.getBoundingClientRect();
        const p = coord(ev);
        const pad = Math.min(54, (axis === 'x' ? r.width : r.height) * .24);
        drag.dir = p < (axis === 'x' ? r.left : r.top) + pad ? -1
          : p > (axis === 'x' ? r.right : r.bottom) - pad ? 1 : 0;
      }
      const els = liveItems();
      let target = els.length;
      for (let i = 0; i < els.length; i++) {
        const r = els[i].getBoundingClientRect();
        const mid = axis === 'x' ? r.left + r.width / 2 : r.top + r.height / 2;
        if (coord(ev) < mid) { target = i; break; }
      }
      drag.target = target;
      const base = box.getBoundingClientRect();
      if (axis === 'x') {
        const edge = els[target] ? els[target].getBoundingClientRect().left
          : (els.length ? els[els.length - 1].getBoundingClientRect().right : base.left);
        drag.line.style.left = edge + 'px';
        drag.line.style.top = base.top + 'px';
        drag.line.style.height = Math.max(16, base.height) + 'px';
      } else {
        const edge = els[target] ? els[target].getBoundingClientRect().top
          : (els.length ? els[els.length - 1].getBoundingClientRect().bottom : base.top);
        drag.line.style.top = edge + 'px';
        drag.line.style.left = base.left + 'px';
        drag.line.style.width = base.width + 'px';
      }
    }
    function tick() {
      if (!drag) return;
      const sc = scrollOf();
      if (sc && drag.dir) {
        const step = 12;
        if (axis === 'x') {
          const max = Math.max(0, sc.scrollWidth - sc.clientWidth);
          const was = sc.scrollLeft;
          sc.scrollLeft = clamp(was + drag.dir * step, 0, max);
          if (sc.scrollLeft !== was && drag.last) place(drag.last);
        } else {
          const max = Math.max(0, sc.scrollHeight - sc.clientHeight);
          const was = sc.scrollTop;
          sc.scrollTop = clamp(was + drag.dir * step, 0, max);
          if (sc.scrollTop !== was && drag.last) place(drag.last);
        }
      }
      drag.raf = requestAnimationFrame(tick);
    }
    function begin(ev) {
      if (!press || drag) return;
      if (spec.canDrag && !spec.canDrag()) { clearPress(); return; }
      const src = press.src;
      const r = src.getBoundingClientRect();
      if (!r.width && !r.height) { clearPress(); return; }
      const ghost = src.cloneNode(true);
      ghost.removeAttribute('id');
      const ids = ghost.querySelectorAll('[id]');
      for (let i = 0; i < ids.length; i++) ids[i].removeAttribute('id');
      ghost.classList.add('kb-sort-ghost');
      ghost.style.width = r.width + 'px';
      ghost.style.height = r.height + 'px';
      ghost.style.left = r.left + 'px';
      ghost.style.top = r.top + 'px';
      document.body.appendChild(ghost);
      const line = document.createElement('div');
      line.className = 'kb-sort-line ' + axis;
      document.body.appendChild(line);
      drag = {
        src: src, ghost: ghost, line: line, last: ev,
        from: liveItems().indexOf(src),
        offX: ev.clientX - r.left, offY: ev.clientY - r.top,
        target: null, dir: 0, raf: 0
      };
      if (drag.from < 0) { cleanup(false); return; }
      if (press.hold) { clearTimeout(press.hold); press.hold = 0; }
      src.classList.add('kb-sort-source');
      document.body.classList.add('kb-sort-active');
      if (press.touch) kb.sortTouch = true;
      place(ev);
      drag.raf = requestAnimationFrame(tick);
    }
    function onMove(ev) {
      if (!press) return;
      press.last = ev;
      const dx = ev.clientX - press.x, dy = ev.clientY - press.y;
      const far = Math.hypot(dx, dy);
      if (drag) {
        if (ev.cancelable) ev.preventDefault();
        place(ev);
        return;
      }
      if (press.touch) {
        if (far < 9) return;
        if (!press.handle && spec.touchHold === false) { clearPress(); return; }
        if (press.handle) {
          if (press.hold) { clearTimeout(press.hold); press.hold = 0; }
          begin(ev);
          if (drag) { if (ev.cancelable) ev.preventDefault(); place(ev); }
          return;
        }
        if (press.hold) { clearTimeout(press.hold); press.hold = 0; }
        if (axis === 'x' && Math.abs(dx) > Math.abs(dy) * 1.15) {
          /* A quick horizontal swipe is still a strip scroll. */
          const sc = scrollOf();
          if (sc) {
            sc.scrollLeft = press.scroll0 - dx;
            press.scrolling = true;
            if (ev.cancelable) ev.preventDefault();
          }
        } else {
          /* Let the page / panel scroll normally. */
          clearPress();
        }
        return;
      }
      if (far < 4) return;
      begin(ev);
      if (drag) { if (ev.cancelable) ev.preventDefault(); place(ev); }
    }
    function onUp(ev) {
      if (!press) return;
      if (drag) { if (ev.cancelable) ev.preventDefault(); cleanup(true); return; }
      if (press.scrolling) kbSortClickLock = performance.now() + 320;
      clearPress();
    }
    function onCancel() { cleanup(false); }

    box.addEventListener('pointerdown', ev => {
      if (ev.button != null && ev.button !== 0) return;
      if (spec.ignore && ev.target.closest(spec.ignore)) return;
      const src = itemAt(ev.target);
      if (!src || src.classList.contains('kb-sort-source')) return;
      const ctrl = ev.target.closest('input,textarea,select,a,button');
      if (ctrl && ctrl !== src) return;
      if (spec.canDrag && !spec.canDrag()) return;
      const sc = scrollOf();
      const handle = spec.handle && ev.target.closest(spec.handle);
      press = {
        src: src, x: ev.clientX, y: ev.clientY,
        touch: ev.pointerType === 'touch' || ev.pointerType === 'pen',
        hold: 0, scrolling: false, last: ev, handle: !!handle,
        scroll0: sc ? (axis === 'x' ? sc.scrollLeft : sc.scrollTop) : 0
      };
      if (press.touch && !press.handle && spec.touchHold !== false) {
        press.hold = setTimeout(() => {
          if (press && !drag) begin({ clientX: press.x, clientY: press.y, cancelable: false });
        }, 230);
      }
      document.addEventListener('pointermove', onMove, { passive: false });
      document.addEventListener('pointerup', onUp, true);
      document.addEventListener('pointercancel', onCancel, true);
    }, { passive: true });
  }

  function kbBindOrderDnd() {
    const body = q('kb-right-body'); if (!body) return;
    kbBindSortable(body, {
      item: '.kb-orow', axis: 'y', scroller: () => body, handle: '.grip',
      canDrag: () => kb.items.length > 0,
      onDrop: (from, to) => {
        if (from === to) return;
        kbSnap();
        kbMoveTo(from, to);
      }
    });
    kbSortClickBlock(body);
  }

  function kbBindSceneSort() {
    const strip = q('kb-scenes'); if (!strip) return;
    kbBindSortable(strip, {
      item: '[data-scene]', axis: 'x', scroller: () => strip,
      canDrag: () => !!(kb.items.length && kbActiveItems().length),
      onDrop: (from, to) => kbReorderActive(from, to)
    });
    kbSortClickBlock(strip);
  }

  function kbRenderRight() {
    const body = q('kb-right-body'); if (!body) return;
    const keep = body.scrollTop;
    document.querySelectorAll('#kun-builder .kb-rtab').forEach(b => b.classList.toggle('on', b.dataset.tab === kb.rightTab));
    if (kb.rightTab === 'order') body.innerHTML = kbOrderHTML();
    else if (kb.rightTab === 'templates') body.innerHTML = kbTemplatesHTML();
    else body.innerHTML = kbSettingsHTML();
    body.scrollTop = keep;
  }

  function kbOrderHTML() {
    if (!kb.items.length) return '<div class="kb-empty">अझै कुनै तत्व छानिएको छैन।<br>बायाँको सूचीबाट चार्ट, तालिका, कार्ड वा शीर्षक छान्नुहोस्।<br><br>केही नछानेमा पुरानै ३२ स्लाइड डिफल्ट टाइमलाइन रहन्छ।</div>';
    const active = kbActiveItems();
    let h = '<div class="kb-section"><div class="kb-section-title">' + (kb.auto ? 'स्वचालित कार्ड क्रम' : 'दृश्य क्रम') + ' <span>' + active.length + ' / ' + kb.items.length + ' सक्रिय</span></div>';
    if (kb.auto) h += '<div class="kb-sub" style="margin:-2px 0 8px">कार्ड वा ⠿ तानेर माथि/तल सार्नुहोस् — बाँकी क्रम स्वतः मिल्छ। चेकबक्स हटाउँदा त्यो कार्ड प्रिभ्यू/टाइमलाइनबाट हट्छ।</div>';
    h += '<div class="kb-order">';
    kb.items.forEach((it, i) => {
      const on = i === kb.cur;
      const en = it.enabled !== false;
      const elCount = it.els && it.els.length ? it.els.length : 1;
      const label = it.title || it.el.name;
      const small = it.autoNo ? ('कार्ड ' + neNum(it.autoNo) + ' · ' + elCount + ' तत्व · ' + it.dur.toFixed(1) + 's') : ('पृष्ठ ' + kbNum(it.el.page) + ' · ' + (KB_TYPE_NE[it.el.type] || it.el.type) + ' · ' + it.dur.toFixed(1) + 's + ' + it.gap.toFixed(1) + 's');
      h += '<div class="kb-orow' + (on ? ' on' : '') + (en ? '' : ' off') + '" data-row="' + i + '">' +
        '<span class="grip" title="तानेर क्रम बदल्नुहोस्">⠿</span>' +
        '<input class="kb-oen" type="checkbox" data-order-enable="' + i + '"' + (en ? ' checked' : '') + ' title="Enable / disable this card" aria-label="Enable card">' +
        '<input class="kb-onum" type="number" min="1" max="' + kb.items.length + '" value="' + (i + 1) + '" data-order-pos="' + i + '" title="Position number">' +
        '<div class="kb-oinfo" data-order-pick="' + i + '"><b>' + kbEsc(label) + '</b><small>' + kbEsc(small) + '</small></div>' +
        '<div class="kb-oacts">' +
        '<button data-order-act="up" data-i="' + i + '" title="Move up">↑</button>' +
        '<button data-order-act="down" data-i="' + i + '" title="Move down">↓</button>' +
        '<button data-order-act="dup" data-i="' + i + '" title="Duplicate">⧉</button>' +
        '<button data-order-act="rm" data-i="' + i + '" title="Remove">✕</button>' +
        '</div></div>';
      if (on && it.els && it.els.length) {
        h += '<div class="kb-els">' + it.els.map((e, j) => {
          const sel = kb.elSel === j;
          return '<div class="kb-elrow' + (sel ? ' on' : '') + (e.visible === false ? ' off' : '') + '" data-el-pick="' + j + '">' +
            '<span class="kb-elz">' + (j + 1) + '</span>' +
            '<div class="kb-elinfo"><b>' + kbEsc(e.el.name || 'तत्व') + '</b><small>' + kbEsc((KB_TYPE_NE[e.el.type] || e.el.type) + ' · ' + Math.round(e.box[2]) + '×' + Math.round(e.box[3]) + ' · z' + (e.z || 1)) + '</small></div>' +
            '<button data-el-act="vis" data-j="' + j + '" title="Show / hide">' + (e.visible === false ? '◌' : '◉') + '</button>' +
            '<button data-el-act="front" data-j="' + j + '" title="Bring to front">⬆</button>' +
            '<button data-el-act="back" data-j="' + j + '" title="Send to back">⬇</button>' +
            '<button data-el-act="dup" data-j="' + j + '" title="Duplicate">⧉</button>' +
            '<button data-el-act="rm" data-j="' + j + '" title="Remove">✕</button>' +
            '</div>';
        }).join('') + '</div>';
        h += '<div class="kb-eladd"><button class="kb-btn sm" data-el-add-current="1">+ तत्व थप्नुहोस्</button><button class="kb-btn sm" data-el-group="1">Group / Ungroup</button></div>';
      }
      if (on && !it.els) h += '<select class="kb-replace" data-replace="' + i + '"><option value="">यो तत्व बदल्नुहोस्…</option>' + kbReplaceOptions(it.el.id) + '</select>';
    });
    h += '</div></div>';
    return h;
  }
  function kbReplaceOptions(selected) {
    let h = '';
    (kb.catalog ? kb.catalog.pages : []).forEach(p => {
      h += '<optgroup label="' + kbAttr(p.no + '. ' + p.title) + '">';
      p.elements.forEach(el => { h += '<option value="' + kbAttr(el.id) + '"' + (el.id === selected ? ' selected' : '') + '>' + kbEsc(el.name) + '</option>'; });
      h += '</optgroup>';
    });
    return h;
  }
  function kbTemplatesHTML() {
    let h = '<div class="kb-section"><div class="kb-section-title">' + kbNum(KB_TPL_LIST.length) + ' टेम्प्लेट <span>' + kbEsc(kbTplDef(kb.tpl).name) + ' सक्रिय</span></div>';
    h += '<div class="kb-sub" style="margin:-2px 0 9px">Live Preview = हेर्नुहोस् · Select = भविष्यका दृश्यका लागि · Apply = सबै दृश्यमा लागू · Customize = रङ/फन्ट · Reset = मूल रूप।</div>';
    h += '<div class="kb-tpl-grid">';
    KB_TPL_LIST.forEach(t => {
      const on = kb.tpl === t.id, prev = kb.tplPreview === t.id;
      h += '<div class="kb-tpl-card' + (on || prev ? ' on' : '') + '" data-tpl-card="' + t.id + '">' +
        '<div class="kb-tpl-art" style="background:linear-gradient(145deg,' + t.bg[0] + ' 0%,' + t.bg[1] + ' 55%,' + t.bg[2] + ' 100%)"><b style="font-family:\'' + kbAttr(t.display) + '\',sans-serif">' + kbEsc(t.name) + '</b><span>' + kbEsc(t.tag) + '</span></div>' +
        '<div class="kb-tpl-body"><b>' + kbEsc(t.ne) + '</b><small>' + kbEsc(t.desc) + '</small>' +
        '<div class="kb-tpl-btns">' +
        '<button data-act="preview" data-tpl="' + t.id + '">Live Preview</button>' +
        '<button data-act="select" data-tpl="' + t.id + '">Select</button>' +
        '<button data-act="customize" data-tpl="' + t.id + '">Customize</button>' +
        '<button data-act="apply" data-tpl="' + t.id + '">Apply</button>' +
        '<button data-act="reset" data-tpl="' + t.id + '">Reset</button>' +
        '</div></div></div>';
    });
    h += '</div></div>';
    return h;
  }
  function kbLookHTML() {
    const def = kbTplDef(kb.tpl);
    const fo = KB_FONT_LIST.map(f => '<option value="' + kbAttr(f) + '"' + (def.display === f ? ' selected' : '') + '>' + f + '</option>').join('');
    const bo = KB_FONT_LIST.map(f => '<option value="' + kbAttr(f) + '"' + (def.font === f ? ' selected' : '') + '>' + f + '</option>').join('');
    return '<div class="kb-section kb-look"><div class="kb-section-title">टेम्प्लेट लुक <span>' + kbEsc(def.name) + '</span></div>' +
      '<div class="kb-grid2">' +
      '<div class="kb-field"><label>Accent</label><input type="color" data-look="accent" value="' + kbAttr(def.accent) + '"></div>' +
      '<div class="kb-field"><label>Secondary</label><input type="color" data-look="accent2" value="' + kbAttr(def.accent2) + '"></div>' +
      '</div>' +
      '<div class="kb-field" style="margin-top:7px"><label>Display font</label><select data-look="display">' + fo + '</select></div>' +
      '<div class="kb-field" style="margin-top:7px"><label>Body font</label><select data-look="font">' + bo + '</select></div>' +
      '<div class="kb-actions"><button class="kb-btn sm" data-look-act="apply">लुक लागू</button><button class="kb-btn sm danger" data-look-act="reset">Reset Template</button></div>' +
      '<div class="kb-field"><span class="kb-hint">यी परिवर्तन तुरुन्तै प्रिभ्यूमा देखिन्छन्। Apply गरेपछि सबै दृश्यमा रहन्छ।</span></div></div>';
  }
  function kbOpts(map, val) {
    return Object.keys(map).map(k => '<option value="' + kbAttr(k) + '"' + (k === val ? ' selected' : '') + '>' + kbEsc(map[k]) + '</option>').join('');
  }
  function kbAutoPanelHTML() {
    const cust = kbCustomList();
    const opt = cust.map(c => '<option value="' + kbAttr(c.name) + '">' + kbEsc(c.name) + '</option>').join('');
    const active = kbActiveItems().length;
    const model = window.KunAutoBuild ? KunAutoBuild.modelByKey(kb.model) : null;
    const adEl = kbAdTarget(false);
    const hasAd = !!(adEl && adEl.adSrc);
    return '<div class="kb-auto-panel">' +
      '<div class="kb-section-title">AUTOMATIC · ' + kb.items.length + ' कार्ड <span>' + active + ' सक्रिय</span></div>' +
      (model ? '<div class="kb-model-current"><i style="background:' + kbAttr(model.colors.accent) + '"></i><div><b>' + kbEsc(model.ne) + '</b><span>' + kbEsc(model.tag) + '</span></div><button class="kb-btn sm" data-auto-act="model">मोडेल बदल्नुहोस्</button></div>' : '') +
      '<div class="kb-auto-status" id="kb-auto-status"><i></i>Auto Save सक्रिय</div>' +
      '<div class="kb-photo-panel">' +
      '<div class="kb-photo-thumb' + (hasAd ? ' has' : '') + '">' + (hasAd ? '<img src="' + kbAttr(adEl.adSrc) + '" alt="ज्योतिषीको फोटो">' : '<span>फोटो</span>') + '</div>' +
      '<div class="kb-photo-copy"><b>ज्योतिषीको फोटो</b><small>अन्तिम परामर्श कार्ड · गोलो पोर्ट्रेट</small></div>' +
      '<div class="kb-photo-btns">' +
      '<button class="kb-btn sm" data-auto-act="ad-select">' + (hasAd ? 'बदल्नुहोस्' : 'छान्नुहोस्') + '</button>' +
      (hasAd ? '<button class="kb-btn sm danger" data-auto-act="ad-remove">हटाउनुहोस्</button>' : '') +
      '</div></div>' +
      '<div class="kb-grid2">' +
      '<button class="kb-btn sm" data-auto-act="save">Manual Save</button>' +
      '<button class="kb-btn sm" data-auto-act="reset">Reset Layout</button>' +
      '<button class="kb-btn sm" data-auto-act="custom-save">Save as Custom Template</button>' +
      '<button class="kb-btn sm" data-auto-act="enable-all">Enable All</button>' +
      '</div>' +
      '<div class="kb-field" style="margin-top:7px"><label>Custom template लागू</label><select id="kb-custom-list">' + (opt || '<option value="">— कुनै custom छैन —</option>') + '</select></div>' +
      '<div class="kb-actions"><button class="kb-btn sm" data-auto-act="custom-load">Apply Custom</button><button class="kb-btn sm danger" data-auto-act="reset">Restore Original Layout</button></div>' +
      '<div class="kb-hint" style="margin-top:5px">Auto Save: हरेक परिवर्तन १.२ सेकेन्डमा यही कुण्डलीको fingerprint मा सुरक्षित हुन्छ। फेरि खोल्दा लेआउट फर्कन्छ।</div>' +
      '</div>';
  }

  function kbElControlsHTML(it) {
    if (!it || !it.els) return '';
    const j = kb.elSel >= 0 && it.els[kb.elSel] ? kb.elSel : 0;
    const e = it.els[j];
    if (!e) return '';
    const pick = it.els.map((x, i) => '<option value="' + i + '"' + (i === j ? ' selected' : '') + '>' + kbEsc((i + 1) + '. ' + (x.el.name || x.el.type)) + '</option>').join('');
    const anim = e.anim || {};
    let h = '<div class="kb-section"><div class="kb-section-title">कार्ड तत्वहरू <span>' + it.els.length + ' तत्व</span></div>' +
      '<div class="kb-field"><label>सम्पादन गर्न तत्व छान्नुहोस्</label><select data-pick-el="1">' + pick + '</select></div>' +
      '<div class="kb-elhead"><b>' + kbEsc(e.el.name || 'तत्व') + '</b><span>' + kbEsc((KB_TYPE_NE[e.el.type] || e.el.type) || '') + '</span></div>';
    if (e.el.editable) {
      h += '<div class="kb-field"><label>पाठ सम्पादन (content)</label><textarea data-el="text" data-el-idx="' + j + '" rows="3">' + kbEsc(e.text || e.el.defaultText || '') + '</textarea></div>';
    }
    h += '<div class="kb-grid2">' +
      '<div class="kb-field"><label>X</label><input type="number" step="1" data-el="x" data-el-idx="' + j + '" value="' + Math.round(e.box[0]) + '"></div>' +
      '<div class="kb-field"><label>Y</label><input type="number" step="1" data-el="y" data-el-idx="' + j + '" value="' + Math.round(e.box[1]) + '"></div>' +
      '<div class="kb-field"><label>Width</label><input type="number" step="1" min="12" data-el="w" data-el-idx="' + j + '" value="' + Math.round(e.box[2]) + '"></div>' +
      '<div class="kb-field"><label>Height</label><input type="number" step="1" min="12" data-el="h" data-el-idx="' + j + '" value="' + Math.round(e.box[3]) + '"></div>' +
      '</div>' +
      '<div class="kb-chips">' +
      '<label class="kb-chip"><input type="checkbox" data-el="aspect" data-el-idx="' + j + '"' + (e.aspectLock !== false ? ' checked' : '') + '> Aspect lock</label>' +
      '<label class="kb-chip"><input type="checkbox" data-el="lock" data-el-idx="' + j + '"' + (e.locked ? ' checked' : '') + '> Lock</label>' +
      '<label class="kb-chip"><input type="checkbox" data-el="visible" data-el-idx="' + j + '"' + (e.visible !== false ? ' checked' : '') + '> Visible</label>' +
      '</div>' +
      '<div class="kb-grid2" style="margin-top:7px">' +
      '<div class="kb-field"><label>Z-order</label><input type="number" step="1" data-el="z" data-el-idx="' + j + '" value="' + (+e.z || 1) + '"></div>' +
      '<div class="kb-field"><label>Group</label><input type="text" data-el="group" data-el-idx="' + j + '" value="' + kbAttr(e.group || '') + '"></div>' +
      '</div>' +
      '<div class="kb-grid2" style="margin-top:7px">' +
      '<div class="kb-field"><label>Entry</label><select data-el="entry" data-el-idx="' + j + '">' + kbOpts({ fade: 'Fade', rise: 'Rise', slide: 'Slide left', 'slide-r': 'Slide right', zoom: 'Zoom', soft: 'Soft focus', depth: 'Depth push', reveal: 'Page reveal', 'grow-x': 'Grow X', 'grow-y': 'Grow Y', hud: 'HUD wipe', none: 'None' }, anim.entry || 'fade') + '</select></div>' +
      '<div class="kb-field"><label>Emphasis</label><select data-el="kind" data-el-idx="' + j + '">' + kbOpts({ none: 'None', float: 'Float', parallax: 'Parallax' }, anim.kind || 'none') + '</select></div>' +
      '<div class="kb-field"><label>Exit</label><select data-el="exit" data-el-idx="' + j + '">' + kbOpts({ fade: 'Fade out', none: 'None' }, anim.exit || 'fade') + '</select></div>' +
      '<div class="kb-field"><label>Opacity</label><input type="number" min="0" max="1" step="0.05" data-el="opacity" data-el-idx="' + j + '" value="' + (anim.opacity == null ? 1 : anim.opacity) + '"></div>' +
      '<div class="kb-field"><label>Anim duration (s)</label><input type="number" min="0.12" max="4" step="0.05" data-el="dur" data-el-idx="' + j + '" value="' + (anim.dur == null ? .72 : anim.dur) + '"></div>' +
      '<div class="kb-field"><label>Delay (s)</label><input type="number" min="0" max="8" step="0.05" data-el="delay" data-el-idx="' + j + '" value="' + (anim.delay || 0) + '"></div>' +
      '</div>' +
      '<div class="kb-actions">' +
      '<button class="kb-btn sm" data-el-act="dup" data-j="' + j + '">Duplicate</button>' +
      '<button class="kb-btn sm" data-el-act="forward" data-j="' + j + '">Forward</button>' +
      '<button class="kb-btn sm" data-el-act="backward" data-j="' + j + '">Backward</button>' +
      '<button class="kb-btn sm" data-el-act="front" data-j="' + j + '">Bring Front</button>' +
      '<button class="kb-btn sm" data-el-act="back" data-j="' + j + '">Send Back</button>' +
      '<button class="kb-btn sm" data-el-act="resetpos" data-j="' + j + '">Reset Position</button>' +
      '<button class="kb-btn sm" data-el-act="resetsize" data-j="' + j + '">Reset Size</button>' +
      '<button class="kb-btn sm danger" data-el-act="rm" data-j="' + j + '">Remove</button>' +
      '</div>' +
      '<div class="kb-field" style="margin-top:7px"><label>Replace with catalog element</label><select data-el-replace="1"><option value="">— बदल्नुहोस् —</option>' + kbReplaceOptions(e.el.id) + '</select></div>' +
      '<div class="kb-actions"><button class="kb-btn sm" data-el-add-current="1">+ नयाँ तत्व थप्नुहोस्</button><button class="kb-btn sm" data-el-group="1">Group / Ungroup</button></div>';
    if (e.el.ad) {
      h += '<div class="kb-section-title" style="margin-top:12px">ज्योतिषीको फोटो</div>' +
        '<div class="kb-hint" style="margin:0 0 7px">यही फोटो अन्तिम “ज्योतिषीय परामर्श” कार्डमा गोलो पोर्ट्रेटका रूपमा देखिन्छ। JPG / PNG / WebP।</div>' +
        '<div class="kb-grid2">' +
        '<button class="kb-btn sm" data-auto-act="ad-select">' + (e.adSrc ? 'बदल्नुहोस्' : 'फोटो छान्नुहोस्') + '</button>' +
        '<button class="kb-btn sm" data-auto-act="ad-toggle">' + (e.visible === false ? 'Enable' : 'Disable') + '</button>' +
        '<button class="kb-btn sm" data-auto-act="ad-preview">Preview</button>' +
        '<button class="kb-btn sm danger" data-auto-act="ad-remove">Remove</button>' +
        '</div>' +
        '<div class="kb-ad-preview' + (e.visible === false ? ' off' : '') + '">' + (e.adSrc ? '<img src="' + kbAttr(e.adSrc) + '" alt="ज्योतिषीको फोटो">' + (e.visible === false ? '<span class="kb-ad-off">बन्द छ — Enable गर्नुहोस्</span>' : '') : '<span>अझै फोटो छैन — “फोटो छान्नुहोस्” थिच्नुहोस्</span>') + '</div>';
    }
    h += '<input type="file" id="kb-ad-file" data-ad-file="1" accept="image/*" hidden>';
    h += '</div>';
    return h;
  }

  function kbPrivacySeed(target, groups) {
    if (!target || !groups || !groups.length) return {};
    if (!target.privacy || typeof target.privacy !== 'object') {
      target.privacy = {};
      groups.forEach(g => { target.privacy[g.id] = true; });
    }
    return target.privacy;
  }
  function kbPrivacyGroups(it) {
    const out = [];
    if (!it) return out;
    if (it.els && it.els.length) {
      it.els.forEach((e, j) => {
        const gs = (e && e.el && e.el.privacy) || [];
        const map = e && e.privacy && typeof e.privacy === 'object' ? e.privacy : null;
        gs.forEach(g => out.push({
          key: j + ':' + g.id, j: j, id: g.id, label: g.label || g.id,
          on: !map || map[g.id] === true
        }));
      });
    } else if (it.el && it.el.privacy) {
      const map = it.privacy && typeof it.privacy === 'object' ? it.privacy : null;
      it.el.privacy.forEach(g => out.push({
        key: 's:' + g.id, j: -1, id: g.id, label: g.label || g.id,
        on: !map || map[g.id] === true
      }));
    }
    return out;
  }
  function kbPrivacyHTML(it) {
    const groups = kbPrivacyGroups(it);
    const style = it.privacyStyle || kb.privacyStyle || 'soft';
    let h = '<div class="kb-section"><div class="kb-section-title">नाम गोपनीयता <span>' + groups.length + ' स्थान</span></div>' +
      '<div class="kb-field"><label>ब्लर शैली</label><select data-privacy-style="1">' + kbOpts(KB_PRIVACY_STYLES, style) + '</select></div>';
    if (!groups.length) {
      h += '<div class="kb-hint">यो कार्डमा नाम भएको ठाउँ छैन। तलको बटनले सबै कार्डका नाम ढाक्छ।</div>';
    } else {
      h += '<div class="kb-chips">';
      groups.forEach(g => {
        h += '<label class="kb-chip"><input type="checkbox" data-privacy-zone="' + kbAttr(g.key) + '"' + (g.on ? ' checked' : '') + '> ' + kbEsc(g.label) + '</label>';
      });
      h += '</div>';
    }
    h += '<div class="kb-actions"><button class="kb-btn sm" data-privacy-act="all">सबै नाम ब्लर</button>' +
      '<button class="kb-btn sm" data-privacy-act="none">सबै देखाउनु</button></div>' +
      '<div class="kb-hint">नाम भएको ठाउँ मात्र छानिएर ब्लर हुन्छ — पूरा कार्ड होइन। “सबै नाम ब्लर” ले सबै कार्ड र manual कार्डका नाम ढाक्छ।</div></div>';
    return h;
  }
  function kbPrivacyGlobalHTML() {
    const style = kb.privacyStyle || 'soft';
    let zones = 0;
    (kb.items || []).forEach(it => {
      if (!it) return;
      if (it.els && it.els.length) it.els.forEach(e => { zones += ((e && e.el && e.el.privacy) || []).length; });
      else zones += ((it.el && it.el.privacy) || []).length;
    });
    return '<div class="kb-section"><div class="kb-section-title">सबै कार्डको नाम गोपनीयता <span>' + zones + ' स्थान</span></div>' +
      '<div class="kb-field"><label>ब्लर शैली (सबै कार्ड)</label><select data-privacy-global-style="1">' + kbOpts(KB_PRIVACY_STYLES, style) + '</select></div>' +
      '<div class="kb-actions"><button class="kb-btn sm" data-privacy-act="all">सबै नाम ब्लर</button>' +
      '<button class="kb-btn sm" data-privacy-act="none">सबै देखाउनु</button></div>' +
      '<div class="kb-hint">कुनै कार्ड नछानी यहाँबाटै जातकको नाम भएका सबै ठाउँ ढाक्न वा देखाउन सकिन्छ।</div></div>';
  }
  function kbPrivacyApplyAll(on) {
    (kb.items || []).forEach(it => {
      if (!it) return;
      if (it.els && it.els.length) {
        it.els.forEach(e => {
          const gs = (e && e.el && e.el.privacy) || [];
          if (!gs.length) return;
          if (!on) { e.privacy = {}; return; }
          e.privacy = e.privacy || {};
          gs.forEach(g => { e.privacy[g.id] = true; });
        });
      } else if (it.el && it.el.privacy) {
        if (!on) { it.privacy = {}; return; }
        it.privacy = it.privacy || {};
        it.el.privacy.forEach(g => { it.privacy[g.id] = true; });
      }
    });
  }
  function kbPrivacyAct(act) {
    kbPrivacyApplyAll(act === 'all');
    kbMarkDirty();
    kbRefresh();
    kbRenderRight();
    kbToast(act === 'all' ? 'सबै नाम ब्लर गरियो।' : 'सबै नाम देखाइयो।');
  }

  function kbSettingsHTML() {
    let h = kb.auto ? kbAutoPanelHTML() : '';
    h += kbLookHTML();
    h += kbPrivacyGlobalHTML();
    const it = kbCur();
    if (!it) {
      h += '<div class="kb-section"><div class="kb-section-title">दृश्य सेटिङ</div><div class="kb-empty" style="padding:16px 8px">क्रम सूचीबाट एउटा दृश्य छान्नुहोस्, त्यसपछि यहाँ एनिमेसन, 3D गहिराइ, छाया र समय मिलाउनुहोस्।</div></div>';
      return h;
    }
    const s = it.set;
    h += '<div class="kb-section"><div class="kb-section-title">' + (it.autoNo ? 'कार्ड ' + neNum(it.autoNo) : 'दृश्य ' + (kb.cur + 1)) + ' <span>' + kbEsc(it.title || it.el.pageTitle) + '</span></div>' +
      (it.autoNo ? '<div class="kb-field"><label>कार्ड शीर्षक (क्रम सूचीमा)</label><input type="text" data-card-title="1" value="' + kbAttr(it.title || '') + '"></div>' : '') +
      '<div class="kb-field"><label>तत्व</label><div style="font-size:11px;line-height:1.45;padding:6px 7px;border:1px solid var(--kb-line);border-radius:7px;background:var(--kb-panel2)">' + kbEsc(it.el.name) + '<br><span style="color:var(--kb-dim);font-size:9.5px">' + (KB_TYPE_NE[it.el.type] || it.el.type) + ' · पृष्ठ ' + kbNum(it.el.page) + '</span></div></div>' +
      '<div class="kb-grid2" style="margin-top:7px">' +
      '<div class="kb-field"><label>Display duration (s)</label><input type="number" min="1" max="60" step="0.1" data-item="dur" value="' + it.dur.toFixed(1) + '"></div>' +
      '<div class="kb-field"><label>Spacing (s)</label><input type="number" min="0" max="4" step="0.1" data-item="gap" value="' + it.gap.toFixed(1) + '"></div>' +
      '</div>' +
      '<div class="kb-field" style="margin-top:7px"><label>Animation speed <b data-live="speed">' + s.speed.toFixed(2) + '×</b></label><input type="range" min="0.5" max="2" step="0.05" data-set="speed" value="' + s.speed + '"></div>' +
      '</div>';
    h += kbPrivacyHTML(it);
    h += '<div class="kb-section"><div class="kb-section-title">एनिमेसन</div><div class="kb-grid2">' +
      '<div class="kb-field"><label>Entry</label><select data-set="entry">' + kbOpts(KB_ENTRY, s.entry) + '</select></div>' +
      '<div class="kb-field"><label>Emphasis</label><select data-set="anim">' + kbOpts(KB_ANIM, s.anim) + '</select></div>' +
      '<div class="kb-field"><label>Exit</label><select data-set="exit">' + kbOpts(KB_EXIT, s.exit) + '</select></div>' +
      '<div class="kb-field"><label>Transition</label><select data-set="trans">' + kbOpts(KB_TRANS, s.trans) + '</select></div>' +
      '</div></div>';
    h += '<div class="kb-section"><div class="kb-section-title">3D + प्रकाश</div>' +
      '<div class="kb-field"><label>3D depth <b data-live="depth">' + s.depth + '</b></label><input type="range" min="0" max="90" step="1" data-set="depth" value="' + s.depth + '"></div>' +
      '<div class="kb-grid2">' +
      '<div class="kb-field"><label>Rotate X <b data-live="rotX">' + s.rotX + '°</b></label><input type="range" min="-25" max="25" step="1" data-set="rotX" value="' + s.rotX + '"></div>' +
      '<div class="kb-field"><label>Rotate Y <b data-live="rotY">' + s.rotY + '°</b></label><input type="range" min="-25" max="25" step="1" data-set="rotY" value="' + s.rotY + '"></div>' +
      '</div>' +
      '<div class="kb-grid2" style="margin-top:7px">' +
      '<div class="kb-field"><label>Scale <b data-live="scale">' + s.scale.toFixed(2) + '×</b></label><input type="range" min="0.6" max="1.5" step="0.01" data-set="scale" value="' + s.scale + '"></div>' +
      '<div class="kb-field"><label>Perspective <b data-live="persp">' + s.persp + '</b></label><input type="range" min="400" max="1600" step="10" data-set="persp" value="' + s.persp + '"></div>' +
      '</div>' +
      '<div class="kb-grid2" style="margin-top:7px">' +
      '<label class="kb-check"><input type="checkbox" data-set="shadow"' + (s.shadow ? ' checked' : '') + '> Shadow</label>' +
      '<label class="kb-check"><input type="checkbox" data-set="border"' + (s.border ? ' checked' : '') + '> Border</label>' +
      '<label class="kb-check"><input type="checkbox" data-set="visible"' + (s.visible ? ' checked' : '') + '> Visible</label>' +
      '</div></div>';
    h += '<div class="kb-section"><div class="kb-section-title">लेआउट</div><div class="kb-grid2">' +
      '<div class="kb-field"><label>Background</label><select data-set="bg">' + kbOpts(KB_BG, s.bg) + '</select></div>' +
      '<div class="kb-field"><label>Alignment</label><select data-set="align">' + kbOpts(KB_ALIGN, s.align) + '</select></div>' +
      '</div>' +
      '<div class="kb-field" style="margin-top:7px"><label>Card padding <b data-live="pad">' + s.pad + '</b></label><input type="range" min="0" max="52" step="1" data-set="pad" value="' + s.pad + '"></div>' +
      '<div class="kb-actions"><button class="kb-btn sm" data-item-act="all">सबै दृश्यमा लागू</button><button class="kb-btn sm" data-item-act="orig">Reset to Original</button><button class="kb-btn sm danger" data-item-act="default">Reset to Default</button></div>' +
      '</div>';
    h += '<div class="kb-section kb-qsection"><div class="kb-section-title">द्रुत सम्पादन <span>प्रिभ्युमा तान्नुहोस्</span></div>' + kbQuickHTML() + '</div>';
    h += '<details class="kb-details"' + (kb.detOpen ? ' open' : '') + '><summary>विस्तृत तत्व सेटिङ · पाठ, आकार, इफेक्ट, 3D</summary><div class="kb-details-body">';
    h += kbElControlsHTML(it);
    h += '<div class="kb-section"><div class="kb-section-title">Multi-element कार्ड</div>' +
      '<div class="kb-hint">एउटै कार्डमा जति पनि तत्व राख्नुहोस् — चार्ट, तालिका, रिपोर्ट वा पाठ। तल खोजेर थप्नुहोस्, त्यसपछि क्यानभासमा सार्न र Resize गर्न सकिन्छ।</div>' +
      '<div class="kb-actions" style="margin-bottom:7px"><button class="kb-btn sm" data-el-add-current="1">+ नयाँ पाठ तत्व</button></div>' +
      '<input class="kb-search" data-mel-search="1" autocomplete="off" placeholder="कार्डमा थप्न तत्व खोज्नुहोस्…">' +
      '<div class="kb-mel-list" id="kb-mel-list">' + kbMelListHTML('') + '</div></div>';
    h += '</div></details>';
    return h;
  }

  function kbRightClick(e) {
    const tab = e.target.closest('[data-tab]');
    if (tab) { kb.tplPreview = null; kb.rightTab = tab.dataset.tab; kbRenderRight(); return; }
    const qa = e.target.closest('[data-qact]');
    if (qa) { kbQuickAct(qa.dataset.qact, +qa.dataset.j, qa.dataset.val); return; }
    const elPick = e.target.closest('[data-el-pick]');
    if (elPick) { kb.elSel = +elPick.dataset.elPick; kb.rightTab = 'settings'; kbRenderRight(); kbDrawPreview(kb.play.t); return; }
    const elAct = e.target.closest('[data-el-act]');
    if (elAct) { kbElementAct(elAct.dataset.elAct, +elAct.dataset.j); return; }
    const pAct = e.target.closest('[data-privacy-act]');
    if (pAct) { kbPrivacyAct(pAct.dataset.privacyAct); return; }
    const melAdd = e.target.closest('[data-mel-add]');
    if (melAdd) { kbAddCatalogElToCard(melAdd.dataset.melAdd); return; }
    if (e.target.closest('[data-el-add-current]')) { kbElementAdd(); return; }
    if (e.target.closest('[data-el-group]')) { kbElementGroup(); return; }
    const tplBtn = e.target.closest('[data-act]');
    if (tplBtn) { kbTemplateAct(tplBtn.dataset.act, tplBtn.dataset.tpl); return; }
    const ord = e.target.closest('[data-order-act]');
    if (ord) {
      const i = +ord.dataset.i, a = ord.dataset.orderAct;
      if (a === 'up') kbMoveItem(i, -1);
      else if (a === 'down') kbMoveItem(i, 1);
      else if (a === 'dup') kbDuplicateItem(i);
      else if (a === 'rm') { kbSnap(); kb.items.splice(i, 1); if (kb.cur >= kb.items.length) kb.cur = kb.items.length - 1; kb.elSel = -1; kbMarkDirty(); kbRenderAll(); }
      return;
    }
    const pick = e.target.closest('[data-order-pick]');
    if (pick) { kb.cur = +pick.dataset.orderPick; kb.elSel = -1; kb.tplPreview = null; kb.rightTab = 'settings'; kbRenderRight(); kbRenderScenes(); kbDrawPreview(kb.play.t); return; }
    const itemAct = e.target.closest('[data-item-act]');
    if (itemAct) { kbItemAct(itemAct.dataset.itemAct); return; }
    const autoAct = e.target.closest('[data-auto-act]');
    if (autoAct) { kbAutoAct(autoAct.dataset.autoAct); return; }
    const lookAct = e.target.closest('[data-look-act]');
    if (lookAct) {
      if (lookAct.dataset.lookAct === 'reset') {
        delete KB_TPL_OV[kb.tpl];
        kbRenderRight(); kbDrawPreview(kb.play.t);
        kbToast('टेम्प्लेट मूल रूपमा फर्कियो।');
      } else {
        kb.items.forEach(it => { it.tpl = kb.tpl; });
        kbRenderRight(); kbDrawPreview(kb.play.t);
        kbToast('टेम्प्लेट लुक लागू भयो।');
      }
    }
  }

  function kbRightField(e, final) {
    const t = e.target;
    if (kb.tplPreview) kb.tplPreview = null;
    if (t.matches('[data-q]')) { kbQuickField(t, final); return; }
    if (t.matches('[data-mel-search]')) {
      const list = q('kb-mel-list');
      if (list) list.innerHTML = kbMelListHTML(t.value);
      return;
    }
    if (t.matches('[data-order-enable]')) {
      const i = +t.dataset.orderEnable;
      if (kb.items[i]) { kbSnap(); kb.items[i].enabled = !!t.checked; kbMarkDirty(); kbRenderAll(); kbToast(t.checked ? 'कार्ड सक्रिय भयो।' : 'कार्ड हटाइयो — क्रमका खाली ठाउँ मिलाइयो।'); }
      return;
    }
    if (t.matches('[data-privacy-global-style]')) {
      kb.privacyStyle = t.value;
      (kb.items || []).forEach(it => { if (it) it.privacyStyle = t.value; });
      kbMarkDirty(); kbRefresh(); kbRenderRight();
      return;
    }
    if (t.matches('[data-privacy-style]')) {
      const it = kbCur(); if (!it) return;
      it.privacyStyle = t.value;
      kb.privacyStyle = t.value;
      kbMarkDirty(); kbRefresh();
      return;
    }
    if (t.matches('[data-privacy-zone]')) {
      const it = kbCur(); if (!it) return;
      const key = String(t.dataset.privacyZone || '');
      const on = !!t.checked;
      const cut = key.indexOf(':');
      const j = key.slice(0, cut), gid = key.slice(cut + 1);
      if (j === 's') {
        const map = kbPrivacySeed(it, it.el && it.el.privacy);
        if (on) map[gid] = true; else delete map[gid];
      } else {
        const e = it.els && it.els[+j];
        if (!e) return;
        const map = kbPrivacySeed(e, e.el && e.el.privacy);
        if (on) map[gid] = true; else delete map[gid];
      }
      kbMarkDirty(); kbRefresh();
      return;
    }
    if (t.matches('[data-item]')) {
      const it = kbCur(); if (!it) return;
      const k = t.dataset.item;
      it[k] = Math.max(k === 'dur' ? 1 : 0, +t.value || 0);
      kbMarkDirty(); kbRefresh();
      return;
    }
    if (t.matches('[data-set]')) {
      const it = kbCur(); if (!it) return;
      const k = t.dataset.set;
      if (t.type === 'checkbox') it.set[k] = t.checked;
      else if (t.type === 'range') it.set[k] = +t.value;
      else it.set[k] = t.value;
      const live = t.parentElement && t.parentElement.querySelector('[data-live]');
      if (live) live.textContent = k === 'scale' ? (+t.value).toFixed(2) + '×' : (k === 'rotX' || k === 'rotY' ? t.value + '°' : (k === 'speed' ? (+t.value).toFixed(2) + '×' : t.value));
      kbMarkDirty(); kbRefresh();
      return;
    }
    if (t.matches('[data-pick-el]')) {
      kb.elSel = +t.value;
      kb.rightTab = 'settings';
      kbRenderRight(); kbDrawPreview(kb.play.t); kbSyncOverlay();
      return;
    }
    if (t.matches('[data-card-title]')) {
      const it = kbCur(); if (!it) return;
      it.title = t.value;
      kbMarkDirty(); kbRenderScenes();
      return;
    }
    if (t.matches('[data-el]')) {
      const it = kbCur(); if (!it || !it.els) return;
      const j = +t.dataset.elIdx, els = it.els[j]; if (!els) return;
      const k = t.dataset.el;
      if (k === 'text') { if (final) { kbSnap(); els.text = t.value; kbApplyElText(els); } else { els.text = t.value; kbApplyElText(els); } }
      else if (k === 'x' || k === 'y') {
        kbSnap();
        const v = +t.value;
        if (k === 'x') els.box[0] = clamp(isFinite(v) ? v : els.box[0], 0, Math.max(0, 720 - els.box[2]));
        else els.box[1] = clamp(isFinite(v) ? v : els.box[1], 0, Math.max(0, 1280 - els.box[3]));
      }
      else if (k === 'w' || k === 'h') {
        kbSnap();
        const v = Math.max(12, +t.value || 12);
        if (k === 'w') els.box[2] = Math.min(v, 720 - els.box[0]);
        else els.box[3] = Math.min(v, 1280 - els.box[1]);
      }
      else if (k === 'z') { els.z = +t.value; }
      else if (k === 'aspect') { els.aspectLock = !!t.checked; }
      else if (k === 'lock') { els.locked = !!t.checked; }
      else if (k === 'visible') { els.visible = !!t.checked; }
      else if (k === 'group') { els.group = t.value; }
      else if (k === 'dur') { els.anim = els.anim || {}; els.anim.dur = Math.max(.12, +t.value); }
      else if (k === 'delay') { els.anim = els.anim || {}; els.anim.delay = Math.max(0, +t.value); }
      else if (k === 'entry' || k === 'kind' || k === 'exit') { els.anim = els.anim || {}; els.anim[k] = t.value; }
      else if (k === 'opacity') { els.anim = els.anim || {}; els.anim.opacity = clamp(+t.value, 0, 1); }
      kbMarkDirty(); kbRefresh(); kbSyncOverlay();
      return;
    }
    if (t.matches('[data-el-replace]')) {
      const it = kbCur(); if (!it || !it.els) return;
      const f = kb.byId.get(t.value);
      const j = kb.elSel;
      if (f && it.els[j]) {
        kbSnap();
        const old = it.els[j];
        it.els[j] = Object.assign({}, old, { key: f.el.id, el: f.el, box: f.el.bbox.slice(), visible: true });
        kbMarkDirty(); kbPrimeSoon([f.el]); kbRenderAll();
        kbToast('तत्व बदलियो: ' + f.el.name);
      }
      return;
    }
    if (t.matches('[data-ad-file]')) {
      kbAdPick(t.files && t.files[0]);
      return;
    }
    if (t.matches('[data-look]')) {
      const d = KB_TPL_OV[kb.tpl] || (KB_TPL_OV[kb.tpl] = {});
      d[t.dataset.look] = t.value;
      kbDrawPreview(kb.play.t); kbUpdateStat();
      return;
    }
    if (t.matches('[data-order-pos]')) {
      const from = +t.dataset.orderPos, to = clamp((+t.value || 1) - 1, 0, kb.items.length - 1);
      if (to !== from) kbMoveTo(from, to);
      return;
    }
    if (t.matches('[data-replace]')) {
      if (t.value) kbReplaceItem(+t.dataset.replace, t.value);
    }
  }

  function kbItemAct(act) {
    const it = kbCur(); if (!it) return;
    if (act === 'all') {
      kb.items.forEach(x => { x.set = Object.assign({}, it.set); x.dur = it.dur; x.gap = it.gap; });
      kbRenderAll(); kbToast('सेटिङ सबै ' + kb.items.length + ' दृश्यमा लागू भयो।');
    } else if (act === 'orig') {
      it.set = kbOriginalSet(); it.dur = it.el.dur || 6; it.gap = KB_DEF_GAP;
      kbRenderRight(); kbRefresh(); kbToast('तत्व मूल रूपमा फर्कियो।');
    } else if (act === 'default') {
      it.set = kbDefaultSet(); it.dur = it.el.dur || 6; it.gap = KB_DEF_GAP;
      kbRenderRight(); kbRefresh(); kbToast('टेम्प्लेट डिफल्ट सेटिङ लागू भयो।');
    }
  }

  function kbTemplateAct(act, id) {
    const def = KB_TPLS[id]; if (!def) return;
    if (act === 'preview') {
      kb.tplPreview = id; kb.demo = null; kbStop();
      kb.play.t = 0; kbDrawPreview(0); kbPlayToggle();
      kbRenderRight(); kbToast('Live Preview: ' + def.name + ' — Apply गरेपछि स्थायी हुन्छ।');
    } else if (act === 'select') {
      kb.tpl = id; kb.tplPreview = null;
      kb.items.forEach(it => { it.tpl = id; });
      kbRenderAll(); kbToast('टेम्प्लेट छानियो: ' + def.name + '।');
    } else if (act === 'apply') {
      kb.tpl = id; kb.tplPreview = null;
      kb.items.forEach(it => { it.tpl = id; });
      kbRenderAll(); kbToast('सबै ' + kb.items.length + ' दृश्यमा ' + def.name + ' लागू भयो।');
    } else if (act === 'customize') {
      kb.tpl = id; kb.tplPreview = null; kb.rightTab = 'settings'; kbRenderRight();
      setTimeout(() => { const l = q('kun-builder') && q('kun-builder').querySelector('.kb-look'); if (l && l.scrollIntoView) l.scrollIntoView({ block: 'start' }); }, 30);
      kbToast('रङ र फन्ट मिलाउनुहोस्, त्यसपछि Apply गर्नुहोस्।');
    } else if (act === 'reset') {
      delete KB_TPL_OV[id];
      kb.demo = null;
      if (kb.tpl === id || kb.tplPreview === id) { kbDrawPreview(kb.play.t); }
      kbRenderRight(); kbToast('टेम्प्लेट मूल रूपमा फर्कियो: ' + def.name + '।');
    }
  }

  function kbRefresh() {
    kbRenderScenes();
    kbUpdateStat();
    kbDrawPreview(kb.play.t);
  }

  /* ─────────────────── automatic mode: persistence + actions ─────────────────── */

  function kbApplyElText(e) {
    if (!e || !e.el || e.el.editable !== true) return;
    const text = e.text != null ? String(e.text) : String(e.el.defaultText || '');
    const st = Object.assign({
      x: 0, y: 0, size: 26, color: '#f2f6ff', weight: 700, single: true,
      lineH: 36, chars: 36, lines: 4, anchor: 'start', auto: true
    }, e.el.textStyle || {});
    const bb = (e.box || e.el.bbox || [0, 0, 300, 60]).slice();
    if (e.el.custom) e.el.bbox = bb.slice();
    const maxChars = Math.max(6, Math.floor((bb[2] - 32) / Math.max(6, (st.size || 26) * .55)));
    if (st.single) {
      const anchor = st.anchor || 'start';
      st.x = anchor === 'middle' ? bb[0] + bb[2] / 2
        : anchor === 'end' ? bb[0] + bb[2] - 16 : bb[0] + 16;
      st.y = bb[1] + Math.round((st.size || 26) * 1.45);
      e.el.inner = kunT(st.x, st.y, kunFit(text || ' ', st.max || maxChars), st.size || 26, st.color || '#f2f6ff', st.weight || 700, anchor);
    } else {
      const chars = st.chars || maxChars;
      e.el.inner = kunPara(st.x, st.y, text || ' ', chars, st.size || 22, st.lineH || 32, st.color || '#a9b8d8', st.lines || 4);
    }
    e.el.textStyle = st;
    if (e.el.custom) e.el.name = kbTextName(text);
  }
  function kbTextName(text) {
    const s = String(text == null ? '' : text).replace(/\s+/g, ' ').trim();
    return 'पाठ · ' + (s.length > 20 ? s.slice(0, 20) + '…' : (s || 'खाली'));
  }
  function kbTextSize(e) {
    const st = e && e.el && e.el.textStyle;
    return clamp(+(st && st.size) || 26, 10, 96);
  }
  function kbTextStyleSet(e, patch) {
    if (!e || !e.el) return;
    if (!e.box && e.el.bbox) e.box = e.el.bbox.slice();
    if (!e.el.bbox && e.box) e.el.bbox = e.box.slice();
    const bb = (e.box || e.el.bbox).slice();
    if (e.el.custom) e.el.bbox = bb.slice();
    const st = Object.assign({
      x: bb[0] + 16, y: bb[1] + 42, size: 26, color: '#f2f6ff',
      weight: 700, single: true, lineH: 36, chars: 36, lines: 4,
      anchor: 'start', auto: true
    }, e.el.textStyle || {});
    Object.assign(st, patch || {});
    st.size = clamp(+st.size || 26, 10, 96);
    st.lineH = Math.max(st.size + 4, Math.round(st.size * 1.42));
    if (st.single) {
      const anchor = st.anchor || 'start';
      st.x = anchor === 'middle' ? bb[0] + bb[2] / 2
        : anchor === 'end' ? bb[0] + bb[2] - 16 : bb[0] + 16;
      st.y = bb[1] + Math.round(st.size * 1.45);
    } else {
      st.lineH = Math.max(st.size + 6, Math.round(st.size * 1.5));
      st.chars = Math.max(8, Math.floor((bb[2] - 32) / Math.max(6, st.size * .56)));
    }
    if (st.auto) {
      const h = st.single
        ? Math.max(36, Math.round(st.size * 1.95))
        : Math.max(64, Math.round(st.lineH * clamp(st.lines || 4, 1, 8)));
      e.el.bbox[3] = h;
      e.box[3] = h;
    }
    e.el.textStyle = st;
    e.el.name = kbTextName(e.text != null ? e.text : e.el.defaultText);
    kbApplyElText(e);
    kbPrimeSoon([e.el]);
  }

  function kbSnapItems() {
    return kb.items.map(it => {
      const o = {};
      Object.keys(it).forEach(k => { if (k !== 'el' && k !== 'els') o[k] = it[k]; });
      o.elId = it.el && it.el.id;
      o.elObj = (it.el && (it.el.custom || !kb.baseEls.has(it.el.id))) ? kbCloneElDef(it.el) : null;
      if (it.els) o.els = it.els.map(e => {
        const x = {};
        Object.keys(e).forEach(k => { if (k !== 'el') x[k] = e[k]; });
        x.elId = e.el && e.el.id;
        x.elObj = (e.el && (e.el.custom || !kb.baseEls.has(e.el.id))) ? kbCloneElDef(e.el) : null;
        return x;
      });
      return o;
    });
  }

  function kbRestoreItems(recs) {
    kb.items = recs.map(rec => {
      const it = {};
      Object.keys(rec).forEach(k => { if (k !== 'elId' && k !== 'elObj' && k !== 'els') it[k] = rec[k]; });
      it.el = rec.elObj || kb.baseEls.get(rec.elId) || rec.el || { id: 'missing', inner: '', bbox: [58, 200, 604, 100], type: 'note', name: 'तत्व', pageTitle: '' };
      if (rec.els) it.els = rec.els.map(x => {
        const e = {};
        Object.keys(x).forEach(k => { if (k !== 'elId' && k !== 'elObj') e[k] = x[k]; });
        e.el = x.elObj || kb.baseEls.get(x.elId) || x.el || it.el;
        return e;
      });
      return it;
    });
    kb.items.forEach(it => { if (it.els) it.els.forEach(kbApplyElText); });
  }

  function kbSnap() {
    kb.undo.push(JSON.stringify(kbSnapItems()));
    if (kb.undo.length > 48) kb.undo.shift();
    kb.redo.length = 0;
  }
  function kbUndo() {
    if (!kb.undo.length) { kbToast('Undo इतिहास खाली छ।', 'err'); return; }
    const cur = JSON.stringify(kbSnapItems());
    const recs = JSON.parse(kb.undo.pop());
    kb.redo.push(cur);
    kbRestoreItems(recs);
    kb.cur = Math.min(kb.cur, kb.items.length - 1);
    if (kb.elSel >= 0 && (!kbCur() || !kbCur().els || kb.elSel >= kbCur().els.length)) kb.elSel = -1;
    kbMarkDirty(); kbRenderAll(); kbSyncOverlay();
    kbToast('Undo भयो।');
  }
  function kbRedo() {
    if (!kb.redo.length) { kbToast('Redo इतिहास खाली छ।', 'err'); return; }
    const cur = JSON.stringify(kbSnapItems());
    const recs = JSON.parse(kb.redo.pop());
    kb.undo.push(cur);
    kbRestoreItems(recs);
    kb.cur = Math.min(kb.cur, kb.items.length - 1);
    kbMarkDirty(); kbRenderAll(); kbSyncOverlay();
    kbToast('Redo भयो।');
  }

  function kbLayoutOf() {
    return {
      v: 3, fp: kb.autoFp, saved: Date.now(), tpl: kb.tpl,
      privacyStyle: kb.privacyStyle || 'soft',
      /* Card order is part of the layout. The element id survives AUTO
         rebuilds, so reopening or switching a model keeps the hand-picked
         sequence instead of snapping back to the catalog order. */
      order: kb.items.map(kbOrderBase).filter(Boolean),
      cards: kb.items.map(it => ({
        autoKey: it.autoKey || '', orderKey: kbOrderBase(it),
        title: it.title || '', enabled: it.enabled !== false,
        dur: it.dur, gap: it.gap, tpl: it.tpl, set: Object.assign({}, it.set),
        cardBox: it.cardBox ? it.cardBox.slice() : null, chrome: !!it.chrome,
        scrollDur: it.scrollDur, scrollDelay: it.scrollDelay, hideScrollBar: !!it.hideScrollBar,
        hotspot: it.hotspot ? it.hotspot.slice() : null, hotspotUrl: it.hotspotUrl || '',
        privacyStyle: it.privacyStyle || '', privacy: it.privacy ? Object.assign({}, it.privacy) : null,
        elId: it.el && it.el.id || '',
        els: it.els ? it.els.map(e => ({
          key: e.key || (e.el && e.el.id) || '', elId: e.el && e.el.id || '',
          /* Hand-made text and frame layers are not in the generated
             catalog, so their tiny vector definition travels with the
             layout. Without this they vanished after a reopen. */
          elObj: e.el && e.el.custom ? kbCloneElDef(e.el) : null,
          box: e.box ? e.box.slice() : null, z: e.z || 1, visible: e.visible !== false,
          group: e.group || '', locked: !!e.locked, text: e.text || '', adSrc: e.adSrc || '',
          photoTouched: !!e.photoTouched,
          privacy: e.privacy ? Object.assign({}, e.privacy) : null,
          anim: Object.assign({}, e.anim || {})
        })) : null
      }))
    };
  }

  function kbApplyLayout(lay) {
    if (!lay || !lay.cards) return;
    /* v2 top padding was 112px. v3 starts the card at the 112px safe line
       (TOP_SAFE 56), so every saved card, element box and hotspot moves up
       56px together. The card height grows by the same amount, keeping its
       bottom edge fixed. Old layouts are migrated on read, then re-saved as
       v3, so a designer's manual positions survive the global shift. */
    const dy = (lay.v || 2) < 3 ? -56 : 0;
    if (lay.tpl) kb.tpl = lay.tpl;
    if (lay.privacyStyle) kb.privacyStyle = lay.privacyStyle;
    /* Each saved card is claimed once. Keying only by autoKey makes every
       continuation card of a long note land on the first sibling, so match
       the stable element id first and keep a pool of unclaimed cards. */
    const orderPool = kb.items.slice();
    lay.cards.forEach((c, i) => {
      let it = null;
      if (c.orderKey) {
        const k = orderPool.findIndex(x => kbOrderBase(x) === c.orderKey);
        if (k >= 0) it = orderPool.splice(k, 1)[0];
      }
      if (!it && c.autoKey) it = kb.items.find(x => x.autoKey && x.autoKey === c.autoKey && orderPool.indexOf(x) >= 0);
      if (!it) it = kb.items[i];
      if (!it) return;
      const claimed = orderPool.indexOf(it);
      if (claimed >= 0) orderPool.splice(claimed, 1);
      if (c.title) it.title = c.title;
      it.enabled = c.enabled !== false;
      if (c.dur != null) it.dur = +c.dur;
      if (c.gap != null) it.gap = +c.gap;
      if (c.tpl) it.tpl = c.tpl;
      if (c.set) it.set = Object.assign({}, it.set, c.set);
      if (c.cardBox) {
        const cb = c.cardBox.slice();
        cb[1] += dy; cb[3] -= dy;
        it.cardBox = cb;
      }
      if (c.chrome != null) it.chrome = !!c.chrome;
      if (c.scrollDur != null) { it.scrollDur = c.scrollDur; it.scrollDelay = c.scrollDelay; }
      it.hideScrollBar = !!c.hideScrollBar;
      if (c.hotspot) { const hs = c.hotspot.slice(); hs[1] += dy; it.hotspot = hs; }
      if (c.hotspotUrl) it.hotspotUrl = c.hotspotUrl;
      if (c.privacyStyle) it.privacyStyle = c.privacyStyle;
      if (c.privacy) it.privacy = Object.assign({}, c.privacy);
      if (c.els) {
        if (!it.els) it.els = [];
        c.els.forEach(se => {
          let e = it.els.find(x => (x.key || (x.el && x.el.id)) === se.key);
          if (!e) {
            /* A hand-made text/frame layer, or a catalog element added by
               hand, is not part of the generated base card. Re-attach the
               saved vector definition first, then fall back to the live
               catalog. */
            const rec = se.elId ? (kb.baseEls.get(se.elId) || kb.byId.get(se.elId)) : null;
            const baseEl = se.elObj ? kbCloneElDef(se.elObj) : (rec && (rec.el || rec));
            if (!baseEl || !se.box) return;
            const nbox = se.box.slice(); nbox[1] += dy;
            e = {
              id: se.key || ('kbe' + Date.now().toString(36)),
              key: se.key || baseEl.id,
              el: baseEl,
              box: nbox,
              z: se.z || 1,
              visible: se.visible !== false,
              anim: Object.assign({}, se.anim || {}),
              group: se.group || '',
              locked: !!se.locked,
              text: se.text || '',
              adSrc: se.adSrc || '',
              photoTouched: !!se.photoTouched,
              privacy: se.privacy ? Object.assign({}, se.privacy) : null
            };
            if (baseEl.scroll) {
              e.scroll = true;
              e.scrollBbox = (baseEl.scrollBbox || baseEl.bbox || e.box).slice();
            }
            it.els.push(e);
            kb.baseEls.set(baseEl.id, baseEl);
          } else {
            const base = se.elId ? (kb.baseEls.get(se.elId) || kb.byId.get(se.elId)) : null;
            if (se.elObj) e.el = kbCloneElDef(se.elObj);
            else if (base) e.el = base.el || base;
            if (se.box) { const nb = se.box.slice(); nb[1] += dy; e.box = nb; }
            if (se.z != null) e.z = +se.z;
            e.visible = se.visible !== false;
            e.group = se.group || '';
            e.locked = !!se.locked;
            e.text = se.text || '';
            e.adSrc = se.adSrc || '';
            e.photoTouched = !!se.photoTouched;
            if (se.privacy) e.privacy = Object.assign({}, se.privacy);
            e.anim = Object.assign({}, e.anim || {}, se.anim || {});
          }
          kbApplyElText(e);
        });
        it.el = (it.els[0] || {}).el || it.el;
      }
    });
    /* Rebuild the saved sequence. Unknown/missing cards stay appended in
       their generated order, so a new AUTO card can never disappear. A
       design model can swap a card's first element (and therefore its
       element id), so fall back to the card's stable autoKey mapping. */
    if (Array.isArray(lay.order) && lay.order.length) {
      const pool = kb.items.slice(), ordered = [];
      const savedAuto = new Map();
      lay.cards.forEach(c => { if (c.orderKey && c.autoKey) savedAuto.set(c.orderKey, c.autoKey); });
      lay.order.forEach(k => {
        let idx = pool.findIndex(x => kbOrderBase(x) === k);
        if (idx < 0 && savedAuto.has(k)) {
          const ak = savedAuto.get(k);
          idx = pool.findIndex(x => x.autoKey && x.autoKey === ak);
        }
        if (idx >= 0) ordered.push(pool.splice(idx, 1)[0]);
      });
      pool.forEach(it => ordered.push(it));
      if (ordered.length === kb.items.length) kb.items = ordered;
    }
  }

  function kbAutoSave(manual) {
    if (!kb.auto || !kb.autoFp) return;
    try {
      localStorage.setItem('kunAuto:v2:' + kb.autoFp, JSON.stringify(kbLayoutOf()));
      kb.dirty = false;
      kbUpdateAutoStatus();
      if (manual) kbToast('लेआउट सुरक्षित भयो।');
    } catch (e) {
      if (manual) kbToast('Save गर्न सकिएन: ' + ((e && e.message) || e), 'err');
    }
  }
  function kbAutoLoad() {
    if (!kb.autoFp) return null;
    try {
      const raw = localStorage.getItem('kunAuto:v2:' + kb.autoFp);
      if (!raw) return null;
      const lay = JSON.parse(raw);
      if (!lay || !lay.cards) return null;
      return lay;
    } catch (e) { return null; }
  }
  function kbMarkDirty() {
    kb.dirty = true;
    kbUpdateAutoStatus();
    clearTimeout(kb.saveT);
    kb.saveT = setTimeout(() => { if (kb.open && kb.auto) kbAutoSave(false); }, 1200);
  }
  function kbUpdateAutoStatus() {
    const st = q('kb-auto-status'); if (!st) return;
    st.innerHTML = '<i class="' + (kb.dirty ? 'dirty' : '') + '"></i>' + (kb.dirty ? 'Auto Save पर्खाइमा…' : 'Auto Saved · फेरि खोल्दा यही लेआउट') + '<span style="margin-left:auto">' + kb.undo.length + ' undo</span>';
  }

  /* ─────────────────── four design models ─────────────────── */
  function kbHideModels() { const m = q('kb-models'); if (m) m.hidden = true; }
  function kbModelThumb(key) {
    const bars = '<b class="kbs-h"></b><b class="kbs-h2"></b><span class="kbs-row"><i></i><i></i><i></i></span><span class="kbs-bar"></span>';
    if (key === 'cosmic') {
      return '<span class="kbs-scene kbs-cosmic">' +
        '<i class="kbs-star s1"></i><i class="kbs-star s2"></i><i class="kbs-star s3"></i><i class="kbs-star s4"></i><i class="kbs-star s5"></i>' +
        '<i class="kbs-orbit o1"></i><i class="kbs-orbit o2"></i><i class="kbs-planet"></i>' +
        '<span class="kbs-card kbs-card-cosmic"><em class="kbs-kicker">COSMIC GOLD</em>' + bars + '</span></span>';
    }
    if (key === 'nebula') {
      return '<span class="kbs-scene kbs-nebula">' +
        '<i class="kbs-blob b1"></i><i class="kbs-blob b2"></i><i class="kbs-blob b3"></i>' +
        '<span class="kbs-pane p1"></span><span class="kbs-pane p2"></span>' +
        '<span class="kbs-card kbs-card-nebula"><em class="kbs-kicker">NEBULA GLASS</em>' + bars + '</span></span>';
    }
    if (key === 'vedic') {
      return '<span class="kbs-scene kbs-vedic">' +
        '<i class="kbs-mandala"></i><i class="kbs-fiber"></i>' +
        '<span class="kbs-paper"><i class="kbs-om">ॐ</i><em class="kbs-kicker">वैदिक पोथी</em>' + bars +
        '<span class="kbs-stitch"></span><span class="kbs-stamp">॥</span></span></span>';
    }
    return '<span class="kbs-scene kbs-orbit">' +
      '<i class="kbs-grid"></i><i class="kbs-ring r1"></i><i class="kbs-ring r2"></i><i class="kbs-ring r3"></i>' +
      '<span class="kbs-card kbs-card-orbit"><i class="kbs-scan"></i>' +
      '<i class="kbs-br tl"></i><i class="kbs-br tr"></i><i class="kbs-br bl"></i><i class="kbs-br br"></i>' +
      '<em class="kbs-kicker">SOLAR · ORBIT</em>' + bars + '</span></span>';
  }
  function kbModelsHTML() {
    if (!window.KunAutoBuild || !KunAutoBuild.models) return '<div class="kb-hint">AUTOMATIC generator लोड भएको छैन।</div>';
    const active = (kb.model || 'cosmic');
    return KunAutoBuild.modelKeys.map(k => {
      const m = KunAutoBuild.models[k];
      const on = k === active;
      const fx = (m.fx || []).map(x => '<em>' + kbEsc(x) + '</em>').join('');
      return '<div class="kb-model-tile' + (on ? ' on' : '') + '" data-model-pick="' + kbAttr(k) + '">' +
        '<div class="kb-model-art kb-ma-' + kbAttr(k) + '">' + kbModelThumb(k) + '</div>' +
        '<div class="kb-model-info">' +
        '<span class="kb-model-badge">' + kbEsc(m.badge) + '</span>' +
        '<b>' + kbEsc(m.ne) + '</b>' +
        '<span class="kb-model-en">' + kbEsc(m.name) + '</span>' +
        '<p>' + kbEsc(m.desc) + '</p>' +
        (fx ? '<div class="kb-model-fx">' + fx + '</div>' : '') +
        '<div class="kb-model-meta"><i style="background:' + kbAttr(m.colors.accent) + '"></i><i style="background:' + kbAttr(m.colors.accent2) + '"></i><em>' + kbEsc(m.tag) + '</em></div>' +
        '</div>' +
        '<button class="kb-btn sm' + (on ? ' accent' : '') + '" data-model-pick="' + kbAttr(k) + '">' + (on ? 'सक्रिय मोडेल' : 'यो मोडेल प्रयोग गर्नुहोस्') + '</button>' +
        '</div>';
    }).join('');
  }
  function kbShowModels() {
    if (!window.KunAutoBuild) { kbToast('AUTOMATIC generator लोड भएको छैन।', 'err'); return; }
    const grid = q('kb-models-grid');
    if (grid) grid.innerHTML = kbModelsHTML();
    const act = q('kb-model-active');
    if (act) act.textContent = KunAutoBuild.modelByKey(kb.model).ne;
    const m = q('kb-models'); if (m) m.hidden = false;
  }
  function kbPickModel(key) {
    kbHideModels();
    if (!window.KunAutoBuild) return;
    const m = KunAutoBuild.modelByKey(key);
    if (kb.items.length && kb.auto) kbSwitchModel(m.key);
    else kbEnterAuto({ model: m.key });
  }
  async function kbSwitchModel(modelKey) {
    if (!window.KunAutoBuild) return false;
    const m = KunAutoBuild.modelByKey(modelKey);
    if (kb.auto && kb.items.length && kb.model === m.key) { kbToast('यही मोडेल पहिले नै सक्रिय छ।'); return true; }
    const oldModelKey = kb.model || 'cosmic';
    const oldLayout = kb.items.length && kb.auto ? kbLayoutOf() : null;
    if (oldLayout) kbAutoSave(false);
    const btn = q('kb-auto'); if (btn) btn.disabled = true;
    kbMsg('मोडेल बदल्दै: ' + m.ne + ' …', '');
    try {
      kb.model = m.key;
      kb.auto = true;
      kb.autoOpts = Object.assign({}, kb.autoOpts || {}, { model: m.key });
      kb.autoFp = KunAutoBuild.fingerprint(kb.data, kb.meta, m.key);
      if (!kb.transit) kb.transit = await kbFetchTransit(kb.data, kb.meta);
      const base = KunAutoBuild.build(kb.data, kb.meta, { transit: kb.transit, model: m.key });
      if (!base.length) throw new Error('कार्ड बनाउन डेटा पर्याप्त छैन।');
      kb.items = base;
      kb.baseEls = new Map();
      kb.items.forEach(it => {
        it.set = KunAutoBuild.set(it.tpl || m.tpl);
        (it.els || []).forEach(e => { if (e.el && e.el.id) kb.baseEls.set(e.el.id, e.el); });
      });
      /* Carry the user's real edits into the new model. Template/set fields
         are stripped so the new model's own visuals win; text, boxes, titles,
         durations, visibility and hand-added elements are preserved. Only a
         value that differs from the outgoing model's AUTO default counts as
         a real edit: otherwise the incoming model keeps its own reading time,
         gap and motion preset. */
      if (oldLayout && oldLayout.cards) {
        const oldBase = KunAutoBuild.build(kb.data, kb.meta, { transit: kb.transit, model: oldModelKey });
        const oldByKey = new Map((oldBase || []).map(it => [it.autoKey, it]));
        const cards = oldLayout.cards.map(c => {
          const d = oldByKey.get(c.autoKey);
          const out = Object.assign({}, c, { tpl: null, set: null });
          if (!d) return out;
          if (c.dur != null && Math.abs(+c.dur - +d.dur) < .05) delete out.dur;
          if (c.gap != null && Math.abs(+c.gap - +d.gap) < .05) delete out.gap;
          if (c.scrollDur != null && d.scrollDur != null && Math.abs(+c.scrollDur - +d.scrollDur) < .05) {
            delete out.scrollDur; delete out.scrollDelay;
          }
          if (Array.isArray(c.els)) {
            out.els = c.els.map(se => {
              const de = (d.els || []).find(x => (x.key || (x.el && x.el.id)) === se.key);
              if (!de) return se;
              const so = Object.assign({}, se);
              if (JSON.stringify(se.anim || {}) === JSON.stringify(de.anim || {})) delete so.anim;
              return so;
            });
          }
          return out;
        });
        kbApplyLayout({ privacyStyle: oldLayout.privacyStyle, order: oldLayout.order, cards: cards });
      }
      const saved = kbAutoLoad();
      if (saved) kbApplyLayout(saved);
      kb.tpl = m.tpl;
      kb.cur = clamp(kb.cur < 0 ? 0 : kb.cur, 0, kb.items.length - 1);
      if (kbCur() && kbCur().els) kb.elSel = clamp(kb.elSel < 0 ? 0 : kb.elSel, 0, kbCur().els.length - 1);
      kbMarkDirty(); kbRenderAll(); kbSyncOverlay();
      kbSeek(kb.play.t);
      kbPrimeSoon((kbCur() && kbCur().els || []).map(e => e.el));
      kbMsg('मोडेल सक्रिय: ' + m.ne + ' — पाठ सम्पादन सुरक्षित छ।', 'ok');
      kbToast('मोडेल बदलियो: ' + m.ne);
      const st = q('st'); if (st) st.textContent = 'AUTOMATIC: ' + m.ne + ' — ' + kb.items.length + ' कार्ड तयार।';
      return true;
    } catch (err) {
      kbMsg('मोडेल बदल्न सकिएन: ' + ((err && err.message) || err), 'err');
      kbToast('मोडेल बदल्न सकिएन।', 'err');
      return false;
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  /* AUTOMATIC lives inside the 3D timeline builder. It reads the currently
     opened Kundali (kb.data) and replaces the scene list with the real
     automatic card set. Existing manual edits are only discarded after the user
     confirms, so a stray click can never destroy work. */
  async function kbEnterAuto(opts) {
    if (!kb.open || !kb.data) {
      kbToast('पहिले कुण्डली खोल्नुहोस्।', 'err');
      return false;
    }
    if (!window.KunAutoBuild) {
      kbToast('AUTOMATIC generator लोड भएको छैन।', 'err');
      return false;
    }
    if (kb.items.length && !(opts && opts.skipConfirm)) {
      const ok = window.confirm('AUTOMATIC ले हालको ' + kb.items.length + ' दृश्यको लेआउटलाई स्वचालित कुण्डली कार्डले प्रतिस्थापन गर्नेछ।\n\nअघि बढ्ने?');
      if (!ok) return false;
    }
    const btn = q('kb-auto');
    if (btn) btn.disabled = true;
    kbMsg('AUTOMATIC: वास्तविक कुण्डली डेटा र गोचर पढ्दै…', '');
    try {
      const modelKey = KunAutoBuild.modelByKey((opts && opts.model) || kb.model || 'cosmic').key;
      kb.model = modelKey;
      kb.auto = true;
      kb.autoOpts = Object.assign({}, opts || {}, { model: modelKey });
      kb.autoFp = KunAutoBuild.fingerprint(kb.data, kb.meta, modelKey);
      kb.baseEls = new Map();
      kb.transit = await kbFetchTransit(kb.data, kb.meta);
      const base = KunAutoBuild.build(kb.data, kb.meta, { transit: kb.transit, model: modelKey });
      if (!base.length) throw new Error('कार्ड बनाउन डेटा पर्याप्त छैन।');
      kb.items = base;
      kb.items.forEach(it => {
        it.set = KunAutoBuild.set(it.tpl || 'cosmic');
        (it.els || []).forEach(e => { if (e.el && e.el.id) kb.baseEls.set(e.el.id, e.el); });
      });
      const lay = kbAutoLoad();
      if (lay) kbApplyLayout(lay);
      kb.tpl = kb.items[0].tpl || 'cosmic';
      kb.cur = 0; kb.elSel = 0; kb.rightTab = 'settings'; kb.tplPreview = null;
      kb.dirty = false; kb.undo.length = 0; kb.redo.length = 0;
      kbMarkDirty();
      kbRenderAll(); kbSyncOverlay(); kbSeek(0);
      kbPrimeSoon((kbCur() && kbCur().els || []).map(e => e.el));
      const mne = KunAutoBuild.modelByKey(modelKey).ne;
      kbMsg('AUTOMATIC तयार — ' + kb.items.length + ' कार्ड (' + mne + ') प्रिभ्यू गरेर “टाइमलाइनमा लागू गर्नुहोस्” थिच्नुहोस्।', 'ok');
      kbToast('AUTOMATIC: ' + kb.items.length + ' कार्ड तयार भए।');
      const st = q('st'); if (st) st.textContent = 'AUTOMATIC: ' + mne + ' — ' + kb.items.length + ' कार्ड तयार, प्रिभ्यू जाँच्नुहोस्।';
      return true;
    } catch (err) {
      kbMsg('AUTOMATIC बनाउन सकिएन: ' + ((err && err.message) || err), 'err');
      kbToast('AUTOMATIC बनाउन सकिएन।', 'err');
      return false;
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  function kbCustomList() {
    try { return JSON.parse(localStorage.getItem('kunAutoCustom:v1') || '[]') } catch (e) { return [] }
  }
  function kbCustomSave() {
    const name = prompt('Custom टेम्प्लेटको नाम:', (kb.meta && kb.meta.name ? kb.meta.name + ' कुण्डली' : 'मेरो कुण्डली लेआउट'));
    if (!name) return;
    const list = kbCustomList();
    list.unshift({ name: String(name).slice(0, 60), saved: Date.now(), layout: kbLayoutOf() });
    try {
      localStorage.setItem('kunAutoCustom:v1', JSON.stringify(list.slice(0, 20)));
      kbToast('Custom टेम्प्लेट सुरक्षित भयो: ' + name);
      kbRenderRight();
    } catch (e) { kbToast('Custom टेम्प्लेट सुरक्षित गर्न सकिएन।', 'err') }
  }
  function kbCustomApply(name) {
    const item = kbCustomList().find(x => x.name === name);
    if (!item) return false;
    kbSnap();
    kbApplyLayout(item.layout);
    kbMarkDirty(); kbRenderAll(); kbSyncOverlay();
    kbToast('Custom टेम्प्लेट लागू भयो: ' + name);
    return true;
  }

  function kbAutoReset() {
    if (!window.KunAutoBuild) return;
    const modelKey = KunAutoBuild.modelByKey(kb.model || 'cosmic').key;
    kb.autoFp = KunAutoBuild.fingerprint(kb.data, kb.meta, modelKey);
    const base = KunAutoBuild.build(kb.data, kb.meta, { transit: kb.transit, model: modelKey });
    if (!base.length) return;
    kbSnap();
    kb.items = base;
    kb.baseEls = new Map();
    kb.items.forEach(it => { it.set = KunAutoBuild.set(it.tpl); (it.els || []).forEach(e => kb.baseEls.set(e.el.id, e.el)); });
    kb.tpl = KunAutoBuild.modelByKey(modelKey).tpl;
    kb.cur = 0; kb.elSel = 0; kb.undo.length = 0; kb.redo.length = 0;
    kb.dirty = true; kbAutoSave(false); kbRenderAll(); kbSyncOverlay();
    kbToast('मूल स्वचालित लेआउट फर्कियो (' + KunAutoBuild.modelByKey(modelKey).ne + ')।');
  }

  function kbAutoAct(act) {
    if (act === 'undo') { kbUndo(); return; }
    if (act === 'redo') { kbRedo(); return; }
    if (act === 'save') { kbAutoSave(true); return; }
    if (act === 'reset') { kbAutoReset(); return; }
    if (act === 'model') { kbShowModels(); return; }
    if (act === 'custom-save') { kbCustomSave(); return; }
    if (act === 'custom-load') {
      const sel = q('kb-custom-list'); if (sel && sel.value) kbCustomApply(sel.value);
      return;
    }
    if (act === 'ad-select' || act === 'ad-replace') {
      if (!kbAdTarget(true)) { kbToast('यो कुण्डलीमा फोटो राख्ने तत्व भेटिएन।', 'err'); return; }
      kbRenderRight();
      const f = q('kb-ad-file'); if (f) { f.value = ''; f.click(); }
      return;
    }
    if (act === 'ad-remove') {
      const e = kbAdTarget(true);
      if (e) {
        if (!e.adSrc) { kbToast('हटाउन फोटो पहिले थप्नुहोस्।', 'err'); return; }
        kbSnap(); e.adSrc = ''; e.photoTouched = true; kbMarkDirty(); kbRefresh(); kbRenderRight(); kbSyncOverlay();
        kbToast('ज्योतिषीको फोटो हटाइयो।');
      }
      return;
    }
    if (act === 'ad-toggle') {
      const e = kbAdTarget(true);
      if (e) { kbSnap(); e.visible = e.visible === false; kbMarkDirty(); kbRefresh(); kbRenderRight(); kbSyncOverlay(); kbToast(e.visible === false ? 'फोटो बन्द।' : 'फोटो खुला।'); }
      return;
    }
    if (act === 'ad-preview') {
      const e = kbAdTarget(true);
      if (!e || !e.el || !e.el.ad) return;
      if (!e.adSrc) { kbToast('पहिले फोटो छान्नुहोस्।', 'err'); return; }
      kbSnap(); e.visible = true; e.locked = false;
      kbMarkDirty(); kbRefresh(); kbRenderRight(); kbSyncOverlay();
      kbToast('ज्योतिषीको फोटो प्रिभ्यू — अन्तिम परामर्श कार्डमा देखियो।');
      return;
    }
    if (act === 'enable-all') {
      kbSnap(); kb.items.forEach(it => { it.enabled = true }); kbMarkDirty(); kbRenderAll(); kbToast('सबै कार्ड सक्रिय भए।');
      return;
    }
  }

  function kbSelectedEl() {
    const it = kbCur();
    return it && it.els && kb.elSel >= 0 ? it.els[kb.elSel] : null;
  }

  function kbElementAct(act, j) {
    const it = kbCur(); if (!it || !it.els) return;
    const e = it.els[j]; if (!e) return;
    kbSnap();
    if (act === 'vis') e.visible = e.visible === false;
    else if (act === 'front') e.z = Math.max.apply(null, it.els.map(x => +x.z || 1)) + 1;
    else if (act === 'back') e.z = Math.min.apply(null, it.els.map(x => +x.z || 1)) - 1;
    else if (act === 'forward') e.z = (+e.z || 1) + 1;
    else if (act === 'backward') e.z = (+e.z || 1) - 1;
    else if (act === 'resetpos') {
      const bb = e.el.bbox || e.box;
      e.box[0] = bb[0]; e.box[1] = bb[1];
    } else if (act === 'resetsize') {
      const bb = e.el.bbox || e.box;
      e.box[2] = bb[2]; e.box[3] = bb[3];
    } else if (act === 'dup') {
      const copyId = 'kbe' + Date.now().toString(36) + Math.random().toString(36).slice(2, 5);
      let copyEl = e.el;
      if (e.el && e.el.custom) {
        copyEl = kbCloneElDef(e.el);
        if (copyEl) copyEl.id = copyId;
      }
      const copy = Object.assign({}, e, {
        id: copyId, key: copyEl ? copyEl.id : ((e.el && e.el.id) || 'el') + '-copy-' + Date.now().toString(36),
        el: copyEl, box: e.box.slice(), z: (+e.z || 1) + .5,
        anim: Object.assign({}, e.anim || {})
      });
      copy.box[0] = clamp(copy.box[0] + 16, 0, Math.max(0, 720 - copy.box[2]));
      copy.box[1] = clamp(copy.box[1] + 16, 0, Math.max(0, 1280 - copy.box[3]));
      if (copyEl && copyEl.custom) {
        copyEl.bbox = copy.box.slice();
        kb.baseEls.set(copyEl.id, copyEl);
      }
      it.els.splice(j + 1, 0, copy);
      kb.elSel = j + 1;
    } else if (act === 'rm') {
      if (it.els.length <= 1) { kbToast('कम्तीमा एक तत्व चाहिन्छ।', 'err'); return; }
      it.els.splice(j, 1);
      if (kb.elSel >= it.els.length) kb.elSel = it.els.length - 1;
    } else if (act === 'lock') e.locked = !e.locked;
    kbMarkDirty(); kbRenderAll(); kbSyncOverlay();
    if (kb.quickOpen) kbRenderQuickSheet();
    kbToast(act === 'rm' ? 'तत्व हटाइयो।' : act === 'dup' ? 'तत्व प्रतिलिपि भयो।' : 'तत्व अपडेट भयो।');
  }

  /* Catalog picker for the multi-element card. The builder lets a user put
     any real chart, table, report, card or text into an existing card; the
     list is filtered live so 400+ elements stay easy to find. */
  function kbMelListHTML(query) {
    if (!kb.catalog) return '<div class="kb-mel-empty">कुनै तत्व उपलब्ध छैन।</div>';
    const q = String(query || '').trim().toLowerCase();
    const hits = [];
    kb.catalog.pages.forEach(p => {
      (p.elements || []).forEach(el => {
        const hay = (el.name + ' ' + el.pageTitle + ' ' + el.type + ' ' + (KB_TYPE_NE[el.type] || '')).toLowerCase();
        if (q && hay.indexOf(q) < 0) return;
        hits.push({ el, page: p });
      });
    });
    if (!hits.length) return '<div class="kb-mel-empty">“' + kbEsc(query) + '” भेटिएन।</div>';
    return hits.slice(0, 16).map(x =>
      '<button type="button" class="kb-mel" data-mel-add="' + kbAttr(x.el.id) + '">' +
      '<b>' + kbEsc(x.el.name) + '</b>' +
      '<small>' + (KB_TYPE_NE[x.el.type] || x.el.type) + ' · पृष्ठ ' + kbNum(x.page.no) + '</small>' +
      '</button>'
    ).join('');
  }

  function kbAddCatalogElToCard(elId) {
    const it = kbCur();
    if (!it) { kbToast('पहिले दृश्य छान्नुहोस्।', 'err'); return; }
    const rec = kb.byId.get(elId);
    if (!rec) { kbToast('तत्व भेटिएन।', 'err'); return; }
    const el = rec.el;
    kbSnap();
    kbEnsureFree(it);
    const bb = el.bbox || [58, 196, 604, 120];
    const ratio = bb[2] > 0 ? bb[3] / bb[2] : .35;
    const card = it.cardBox || [46, 168, 628, 1056];
    const top = card[1] + 30, bottom = card[1] + card[3] - 30;
    let y = top;
    it.els.forEach(e => { if (e.box && e.visible !== false) y = Math.max(y, e.box[1] + e.box[3] + 10); });
    let w = 604, h = Math.round(w * ratio);
    if (y + h > bottom) {
      const avail = bottom - y;
      if (avail >= 90) { h = Math.round(avail); w = Math.round(h / ratio); if (w > 604) { w = 604; h = Math.round(w * ratio); } }
      else y = top; /* no free strip: intentional overlap, user drags it */
    }
    const id = 'kbe' + Date.now().toString(36);
    if (el.scroll) {
      /* A full-page document keeps its real page proportions and fills the
         card, then travels through its whole height. */
      const box = [58, 170, 604, 1052];
      it.els.push({
        id: id, key: id, el: el, box: box,
        z: Math.max.apply(null, it.els.map(e => +e.z || 1)) + 1,
        visible: true, scroll: true, scrollBbox: (el.scrollBbox || el.bbox || box).slice(),
        anim: { entry: 'fade', delay: .1, dur: .7, kind: 'none' },
        group: '', locked: false
      });
      it.scrollDur = el.scrollDur || 28;
      it.scrollDelay = el.scrollDelay != null ? el.scrollDelay : .8;
      it.hideScrollBar = el.hideScrollBar !== false;
      it.dur = Math.max(it.dur || 0, it.scrollDur + 4);
    } else {
      it.els.push({
        id: id, key: id, el: el, box: [Math.round(360 - w / 2), y, w, h],
        z: Math.max.apply(null, it.els.map(e => +e.z || 1)) + 1,
        visible: true, anim: { entry: 'fade', delay: .1, dur: .7, kind: 'none' },
        group: '', locked: false
      });
    }
    kb.baseEls.set(el.id, el);
    kb.elSel = it.els.length - 1;
    kbMarkDirty(); kbRenderAll(); kbSyncOverlay();
    kbToast('कार्डमा थपियो: ' + (el.name || 'तत्व'));
  }

  function kbNewTextEl(it, box, text) {
    const def = kbTplDef(it.tpl || kb.tpl);
    const id = 'kbe' + Date.now().toString(36) + Math.random().toString(36).slice(2, 5);
    const size = 30;
    const st = {
      x: box[0] + 16, y: box[1] + 44, size: size,
      color: def.ink || '#f2f6ff', weight: 700, single: true, auto: true,
      lineH: 44, chars: 36, lines: 4, anchor: 'start'
    };
    const el = {
      id: id, page: it.autoNo || 0, pageTitle: it.title || '',
      type: 'note', name: kbTextName(text), bbox: box.slice(),
      inner: kunT(st.x, st.y, text, size, st.color, st.weight, st.anchor),
      dur: 6.4, editable: true, defaultText: text,
      textStyle: st, custom: true
    };
    const wrapper = {
      id: id, key: id, el: el, box: box.slice(), z: 60,
      visible: true, anim: { entry: 'rise', delay: .12, dur: .7, kind: 'none' },
      group: '', locked: false, text: text
    };
    it.els.push(wrapper);
    kb.baseEls.set(id, el);
    kb.elSel = it.els.length - 1;
    return wrapper;
  }

  function kbQuickAddText() {
    const it = kbCur();
    if (!it) { kbToast('पहिले कुनै कार्ड छान्नुहोस्।', 'err'); return; }
    kbSnap();
    kbEnsureFree(it);
    const card = it.cardBox || [46, 168, 628, 1056];
    const w = Math.min(560, Math.max(240, card[2] - 70));
    const n = it.els.filter(e => e.el && e.el.editable).length;
    let x = Math.round(card[0] + (card[2] - w) / 2);
    let y = Math.round(card[1] + card[3] * .38 + n * 54);
    if (kb.lastTap) {
      x = Math.round(clamp(kb.lastTap.x - w / 2, 8, 720 - w - 8));
      y = Math.round(clamp(kb.lastTap.y - 36, 8, 1280 - 90));
      kb.lastTap = null;
    }
    const wrapper = kbNewTextEl(it, [x, y, w, 72], 'नयाँ पाठ');
    kbTextStyleSet(wrapper, { size: 30 });
    wrapper.z = Math.max.apply(null, it.els.map(e => +e.z || 0)) + 1;
    kbMarkDirty(); kbRenderAll(); kbSyncOverlay();
    kbOpenQuick();
    setTimeout(() => {
      const ta = q('kb-qsheet-body') && q('kb-qsheet-body').querySelector('[data-q="text"]');
      if (ta) { ta.focus(); ta.select(); }
    }, 180);
    kbToast('पाठ थपियो — प्रिभ्युमा तान्नुहोस्, तल स्टाइल मिलाउनुहोस्।');
  }

  function kbPanelTheme(kind) {
    const def = kbTplDef(kb.tpl);
    const light = KB_LIGHT.has(def.motion);
    return {
      kind: kind || 'panel',
      fill: light ? 'rgba(255,255,255,.78)' : 'rgba(8,14,26,.62)',
      stroke: def.accent || '#f6d365',
      radius: kind === 'frame' ? 14 : 20,
      width: kind === 'frame' ? 2 : 1.5
    };
  }

  function kbApplyPanelStyle(e) {
    if (!e || !e.el) return;
    const bb = (e.box || e.el.bbox || [0, 0, 100, 100]).slice();
    if (!e.box) e.box = bb.slice();
    if (e.el.custom) e.el.bbox = bb.slice();
    const st = Object.assign(kbPanelTheme('panel'), e.el.panelStyle || {});
    const x = bb[0], y = bb[1], w = Math.max(10, bb[2]), h = Math.max(10, bb[3]);
    const r = Math.max(0, Math.min(+st.radius || 0, Math.min(w, h) / 2));
    const fill = st.fill || 'rgba(8,14,26,.62)';
    const stroke = st.stroke || '#f6d365';
    const sw = Math.max(1, +st.width || 1.5);
    let inner = '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="' + r + '" fill="' + fill + '" stroke="' + stroke + '" stroke-width="' + sw + '"/>';
    if (st.kind === 'frame') {
      inner += '<rect x="' + (x + 6) + '" y="' + (y + 6) + '" width="' + Math.max(2, w - 12) + '" height="' + Math.max(2, h - 12) + '" rx="' + Math.max(2, r - 5) + '" fill="none" stroke="' + stroke + '" stroke-opacity=".34" stroke-width="1"/>';
      inner += '<rect x="' + (x + Math.min(20, w * .18)) + '" y="' + (y - 1.5) + '" width="' + Math.min(74, w * .28) + '" height="3" rx="1.5" fill="' + stroke + '"/>';
    } else {
      inner += '<rect x="' + (x + 14) + '" y="' + (y + 14) + '" width="' + Math.min(92, Math.max(18, w * .22)) + '" height="4" rx="2" fill="' + stroke + '"/>';
      inner += '<rect x="' + (x + 14) + '" y="' + (y + h - 20) + '" width="' + Math.max(10, w - 28) + '" height="1" rx=".5" fill="' + stroke + '" fill-opacity=".22"/>';
    }
    e.el.panelStyle = st;
    e.el.inner = inner;
    e.el.name = st.kind === 'frame' ? 'फ्रेम' : 'प्यानल';
  }

  function kbNewPanelEl(it, box, kind, z) {
    const id = 'kbe' + Date.now().toString(36) + Math.random().toString(36).slice(2, 5);
    const st = kbPanelTheme(kind);
    const el = {
      id: id, page: it.autoNo || 0, pageTitle: it.title || '',
      type: 'panel', name: kind === 'frame' ? 'फ्रेम' : 'प्यानल',
      bbox: box.slice(), inner: '', dur: 6.4,
      custom: true, panelStyle: st
    };
    const wrapper = {
      id: id, key: id, el: el, box: box.slice(), z: z,
      visible: true, anim: { entry: 'fade', delay: .05, dur: .6, kind: 'none' },
      group: '', locked: false
    };
    kbApplyPanelStyle(wrapper);
    it.els.push(wrapper);
    kb.baseEls.set(id, el);
    kb.elSel = it.els.length - 1;
    return wrapper;
  }

  function kbTextLayerFor(it, around) {
    if (!it || !it.els) return null;
    const texts = it.els.filter(e => e && e.el && e.el.editable && e.visible !== false && e.box);
    if (!texts.length) return null;
    const sel = kbSelectedEl();
    if (sel && sel.el && sel.el.editable) return sel;
    if (around) {
      const inside = texts.filter(e => {
        const cx = e.box[0] + e.box[2] / 2, cy = e.box[1] + e.box[3] / 2;
        return cx >= around[0] && cx <= around[0] + around[2] && cy >= around[1] && cy <= around[1] + around[3];
      });
      if (inside.length) return inside.sort((a, b) => (+b.z || 0) - (+a.z || 0))[0];
    }
    return texts.sort((a, b) => (+b.z || 0) - (+a.z || 0))[0];
  }

  function kbQuickAddFrame() {
    const it = kbCur();
    if (!it) { kbToast('पहिले कुनै कार्ड छान्नुहोस्।', 'err'); return; }
    const text = kbTextLayerFor(it);
    if (!text) { kbToast('पहिले ＋ पाठ थप्नुहोस्, त्यसपछि फ्रेम स्वतः त्यसैको पछाडि बन्छ।', 'err'); return; }
    kbSnap(); kbEnsureFree(it);
    const pad = 18;
    const box = [
      clamp(text.box[0] - pad, 0, 720), clamp(text.box[1] - pad, 0, 1280),
      text.box[2] + pad * 2, text.box[3] + pad * 2
    ];
    const w = kbNewPanelEl(it, box, 'frame', (+text.z || 1) - .4);
    kbMarkDirty(); kbRenderAll(); kbSyncOverlay();
    if (kb.quickOpen) kbRenderQuickSheet();
    kbToast('फ्रेम पाठको तल थपियो — रङ र आकार स्टाइलमा मिलाउनुहोस्।');
  }

  function kbQuickAddPanel() {
    const it = kbCur();
    if (!it) { kbToast('पहिले कुनै कार्ड छान्नुहोस्।', 'err'); return; }
    kbSnap(); kbEnsureFree(it);
    const text = kbTextLayerFor(it);
    let box, z;
    if (text) {
      const pad = 28;
      box = [clamp(text.box[0] - pad, 0, 720), clamp(text.box[1] - pad, 0, 1280), text.box[2] + pad * 2, text.box[3] + pad * 2];
      z = (+text.z || 1) - .5;
    } else {
      const card = it.cardBox || [46, 168, 628, 1056];
      const w = Math.min(560, Math.max(280, card[2] - 80));
      const h = Math.min(640, Math.max(260, card[3] - 180));
      box = [Math.round(card[0] + (card[2] - w) / 2), Math.round(card[1] + (card[3] - h) / 2), w, h];
      z = Math.min.apply(null, it.els.map(e => +e.z || 1)) - .5;
    }
    kbNewPanelEl(it, box, 'panel', z);
    kbMarkDirty(); kbRenderAll(); kbSyncOverlay();
    if (kb.quickOpen) kbRenderQuickSheet();
    kbToast('प्यानल थपियो — अक्षर त्यसको माथिको लेयरमा राख्नुहोस्।');
  }

  function kbQuickFitPanel() {
    const it = kbCur(), e = kbSelectedEl();
    if (!it || !e || !e.el || e.el.type !== 'panel') { kbToast('पहिले फ्रेम वा प्यानल छान्नुहोस्।', 'err'); return; }
    const text = kbTextLayerFor(it, e.box);
    if (!text) { kbToast('यो फ्रेमभित्र कुनै पाठ भेटिएन।', 'err'); return; }
    kbSnap();
    const pad = e.el.panelStyle && e.el.panelStyle.kind === 'frame' ? 18 : 26;
    const box = [clamp(text.box[0] - pad, 0, 720), clamp(text.box[1] - pad, 0, 1280), text.box[2] + pad * 2, text.box[3] + pad * 2];
    e.box = box;
    e.el.bbox = box.slice();
    kbApplyPanelStyle(e);
    kbMarkDirty(); kbRenderAll(); kbSyncOverlay();
    if (kb.quickOpen) kbRenderQuickSheet();
    kbToast('फ्रेम पाठसँग मिलाइयो।');
  }

  /* ─────────────────── quick style sheet ───────────────────
     One small card for the 90% moves: text, size, colour, frame,
     effect and in/out timing. The dense controls stay available
     in the collapsible section below it. */
  const KB_QCOLORS = ['#f2f6ff', '#f6d365', '#ffffff', '#34d399', '#22d3ee', '#fb7185', '#a78bfa', '#fbbf24'];

  function kbHexColor(c, fallback) {
    c = String(c == null ? '' : c).trim();
    if (/^#[0-9a-f]{6}$/i.test(c)) return c;
    if (/^#[0-9a-f]{3}$/i.test(c)) return '#' + c.charAt(1) + c.charAt(1) + c.charAt(2) + c.charAt(2) + c.charAt(3) + c.charAt(3);
    const m = /^rgba?\(([^)]+)\)/i.exec(c);
    if (m) {
      const n = m[1].split(',').slice(0, 3).map(x => clamp(Math.round(+x || 0), 0, 255));
      if (n.length === 3) return '#' + n.map(x => (x < 16 ? '0' : '') + x.toString(16)).join('');
    }
    return fallback || '#f2f6ff';
  }
  function kbSameColor(a, b) {
    return kbHexColor(a, '').toLowerCase() === kbHexColor(b, '').toLowerCase();
  }

  function kbQuickHTML() {
    const it = kbCur();
    if (!it) return '<div class="kb-qempty">पहिले क्रम सूचीबाट एउटा कार्ड छान्नुहोस्।</div>';
    const els = it.els || [];
    const e = kbSelectedEl() || els[0] || null;
    if (!e) {
      return '<div class="kb-qempty"><b>यो कार्डमा अझै तत्व छैन।</b>' +
        '<div class="kb-qaddonly">' +
        '<button data-qact="add-text" class="strong">＋ पाठ</button>' +
        '<button data-qact="add-panel">▤ प्यानल</button>' +
        '<button data-qact="add-frame">▣ फ्रेम</button>' +
        '</div><small>पाठ थपेपछि प्रिभ्युमा औंलाले तान्नुहोस्।</small></div>';
    }
    const j = els.indexOf(e);
    const tag = kbLayerTag(e);
    const st = (e.el && e.el.textStyle) || {};
    const size = kbTextSize(e);
    let h = '<div class="kb-qhero"><span class="kb-qkind">' + kbEsc(tag) + '</span>' +
      '<b data-qhero-name="' + j + '">' + kbEsc((e.el && e.el.name) || 'तत्व') + '</b>' +
      '<span class="kb-qz">z ' + (Math.round((+e.z || 1) * 10) / 10) + '</span></div>';

    if (e.el && e.el.editable) {
      h += '<div class="kb-qblock">' +
        '<div class="kb-qrow kb-qtextrow"><textarea class="kb-qtext" data-q="text" data-j="' + j + '" rows="2" placeholder="पाठ लेख्नुहोस्…">' + kbEsc(e.text != null ? e.text : (e.el.defaultText || '')) + '</textarea></div>' +
        '<div class="kb-qrow kb-qsize">' +
        '<button data-qact="size-down" data-j="' + j + '" aria-label="अक्षर सानो">A−</button>' +
        '<input type="range" min="10" max="96" step="1" data-q="size" data-j="' + j + '" value="' + size + '" aria-label="अक्षर आकार">' +
        '<button data-qact="size-up" data-j="' + j + '" aria-label="अक्षर ठूलो">A+</button>' +
        '<b class="kb-qval" data-qsize-val="' + j + '">' + size + '</b></div>' +
        '<div class="kb-qrow kb-qswatches">' +
        KB_QCOLORS.map(c => '<button class="kb-qsw' + (kbSameColor(st.color, c) ? ' on' : '') + '" data-qact="swatch" data-val="' + c + '" data-j="' + j + '" style="background:' + c + '" aria-label="रङ ' + c + '"></button>').join('') +
        '<label class="kb-qcolor" title="अरू रङ"><input type="color" data-q="color" data-j="' + j + '" value="' + kbHexColor(st.color) + '"></label></div>' +
        '<div class="kb-qrow kb-qminirow">' +
        '<button data-qact="align" data-val="start" data-j="' + j + '" class="' + ((st.anchor || 'start') === 'start' ? 'on' : '') + '" title="बायाँ">⬅</button>' +
        '<button data-qact="align" data-val="middle" data-j="' + j + '" class="' + (st.anchor === 'middle' ? 'on' : '') + '" title="बीच">↔</button>' +
        '<button data-qact="weight" data-j="' + j + '" class="' + ((+st.weight || 700) >= 600 ? 'on' : '') + '" title="बोल्ड">ब</button>' +
        '<button data-qact="line" data-j="' + j + '" class="' + (st.single ? 'on' : '') + '" title="एक / अनेक लाइन">' + (st.single ? 'एक लाइन' : 'अनेक लाइन') + '</button>' +
        '</div></div>';
    }

    if (e.el && e.el.type === 'panel') {
      const ps = e.el.panelStyle || {};
      const kind = ps.kind === 'frame' ? 'frame' : 'panel';
      h += '<div class="kb-qblock"><div class="kb-qlabel">प्यानल / फ्रेम</div>' +
        '<div class="kb-qseg">' +
        '<button data-qact="pkind" data-val="panel" data-j="' + j + '" class="' + (kind === 'panel' ? 'on' : '') + '">▤ प्यानल</button>' +
        '<button data-qact="pkind" data-val="frame" data-j="' + j + '" class="' + (kind === 'frame' ? 'on' : '') + '">▣ फ्रेम</button>' +
        '</div>' +
        '<div class="kb-qrow kb-qminirow">' +
        '<label class="kb-qmini">भित्री रङ<input type="color" data-q="pfill" data-j="' + j + '" value="' + kbHexColor(ps.fill, '#08101a') + '"></label>' +
        '<label class="kb-qmini">किनारा<input type="color" data-q="pstroke" data-j="' + j + '" value="' + kbHexColor(ps.stroke, '#f6d365') + '"></label>' +
        '<label class="kb-qmini">गोलाइ <b class="kb-qval" data-qrad-val="' + j + '">' + Math.round(+ps.radius || 0) + '</b><input type="range" min="0" max="40" step="1" data-q="pradius" data-j="' + j + '" value="' + Math.round(+ps.radius || 0) + '"></label>' +
        '</div>' +
        '<div class="kb-qrow kb-qminirow"><button data-qact="fit" data-j="' + j + '">पाठसँग मिलाउने</button>' +
        '<button data-qact="behind" data-j="' + j + '">पाठको पछाडि</button></div></div>';
    }

    const anim = e.anim || {};
    const chip = (val, label, on) => '<button data-qact="entry" data-val="' + val + '" data-j="' + j + '" class="' + (on ? 'on' : '') + '">' + label + '</button>';
    const exitChip = (val, label, on) => '<button data-qact="exit" data-val="' + val + '" data-j="' + j + '" class="' + (on ? 'on' : '') + '">' + label + '</button>';
    h += '<div class="kb-qblock"><div class="kb-qlabel">इफेक्ट</div>' +
      '<div class="kb-qrow kb-qchips">' +
      chip('fade', 'फेड', (anim.entry || 'fade') === 'fade') +
      chip('rise', 'माथि', anim.entry === 'rise') +
      chip('slide', 'स्लाइड', anim.entry === 'slide') +
      chip('zoom', 'जुम', anim.entry === 'zoom') +
      chip('none', 'कुनै नहुने', anim.entry === 'none') +
      '</div>' +
      '<div class="kb-qrow kb-qchips">' +
      exitChip('fade', 'फेड आउट', (anim.exit || 'fade') === 'fade') +
      exitChip('none', 'अचानक', anim.exit === 'none') +
      '</div>' +
      '<div class="kb-qrow kb-qminirow">' +
      '<label class="kb-qmini">गति (से)<input type="number" min="0.2" max="4" step="0.05" data-q="animdur" data-j="' + j + '" value="' + (anim.dur == null ? .72 : anim.dur) + '"></label>' +
      '<label class="kb-qmini">ढिलाइ<input type="number" min="0" max="8" step="0.05" data-q="delay" data-j="' + j + '" value="' + (+anim.delay || 0) + '"></label>' +
      '<label class="kb-qmini">अपारदर्शी<input type="number" min="0" max="1" step="0.05" data-q="opacity" data-j="' + j + '" value="' + (anim.opacity == null ? 1 : anim.opacity) + '"></label>' +
      '</div></div>';

    const win = kbElWindow(it, e, j);
    const dur = Math.max(.4, +it.dur || .4);
    h += '<div class="kb-qblock"><div class="kb-qlabel">यो कार्डभित्रको समय</div>' +
      '<div class="kb-qrow kb-qtime">' +
      '<label>इन <input type="number" min="0" max="' + Math.max(0, dur - .2).toFixed(2) + '" step="0.1" data-q="in" data-j="' + j + '" value="' + win[0].toFixed(2) + '"></label>' +
      '<label>आउट <input type="number" min="0.2" max="' + dur.toFixed(2) + '" step="0.1" data-q="out" data-j="' + j + '" value="' + win[1].toFixed(2) + '"></label>' +
      '<button data-qact="cardtime" data-j="' + j + '" title="पूरा कार्ड">पूरा</button>' +
      '<button data-qact="halftime" data-j="' + j + '" title="पछि आधा">आधा</button>' +
      '<button data-qact="preview" data-j="' + j + '" class="strong">▶ हेर्नुहोस्</button>' +
      '</div></div>';

    h += '<div class="kb-qrow kb-qactions">' +
      '<button data-qact="front" data-j="' + j + '" title="सबैभन्दा माथि">⬆ अगाडि</button>' +
      '<button data-qact="back" data-j="' + j + '" title="सबैभन्दा पछाडि">⬇ पछाडि</button>' +
      '<button data-qact="lock" data-j="' + j + '">' + (e.locked ? '🔓 खोल्ने' : '🔒 लक') + '</button>' +
      '<button data-qact="vis" data-j="' + j + '">' + (e.visible === false ? '◉ देखाउने' : '◌ लुकाउने') + '</button>' +
      '<button data-qact="dup" data-j="' + j + '">⧉ प्रतिलिपि</button>' +
      '<button data-qact="rm" data-j="' + j + '" class="danger">✕ हटाउने</button>' +
      '</div>';
    h += '<div class="kb-qaddonly kb-qaddmore">' +
      '<button data-qact="add-text" class="strong">＋ पाठ</button>' +
      '<button data-qact="add-panel">▤ प्यानल</button>' +
      '<button data-qact="add-frame">▣ फ्रेम</button>' +
      '</div>';
    return h;
  }

  function kbRenderQuickSheet() {
    const body = q('kb-qsheet-body');
    if (!body) return;
    body.innerHTML = kbQuickHTML();
    const sub = q('kb-qsheet-sub'), it = kbCur(), e = kbSelectedEl();
    if (sub) sub.textContent = it ? ((e && e.el && e.el.name) || it.title || 'तत्व') + ' · ' + kbLayerTag(e || { el: it.el || {} }) : 'पाठ, फ्रेम, इफेक्ट र समय';
  }
  function kbOpenQuick() {
    const it = kbCur();
    if (!it) { kbToast('पहिले कुनै कार्ड छान्नुहोस्।', 'err'); return; }
    if (kb.play.on) kbStop();
    kb.quickOpen = true;
    const sheet = q('kb-qsheet');
    if (sheet) sheet.hidden = false;
    kbRenderQuickSheet();
  }
  function kbCloseQuick() {
    kb.quickOpen = false;
    const sheet = q('kb-qsheet');
    if (sheet) sheet.hidden = true;
  }

  function kbQuickMain(kind) {
    if (kind === 'text') { kbQuickAddText(); return; }
    if (kind === 'frame') { kbQuickAddFrame(); return; }
    if (kind === 'panel') { kbQuickAddPanel(); return; }
    if (kind === 'style') { kbOpenQuick(); return; }
    if (kind === 'layers') {
      kb.layersOpen = !kb.layersOpen;
      kbRenderLayers();
      setTimeout(() => { if (kb.open) kbDrawPreview(kb.play.t); }, 30);
    }
  }

  function kbQuickField(t, final) {
    if (!t.matches('[data-q]')) return false;
    const it = kbCur();
    if (!it || !it.els) return true;
    const j = +t.dataset.j;
    const e = it.els[j];
    if (!e) return true;
    const key = t.dataset.q;
    if (key === 'text') {
      e.text = t.value;
      kbApplyElText(e);
      const hd = document.querySelector('[data-qhero-name="' + j + '"]');
      if (hd) hd.textContent = (e.el && e.el.name) || 'तत्व';
      const row = document.querySelector('#kb-layerbar [data-lay-row="' + j + '"] .kb-lay-name b');
      if (row) row.textContent = (e.el && e.el.name) || 'तत्व';
    } else if (key === 'size') {
      const v = clamp(Math.round(+t.value || 30), 10, 96);
      kbTextStyleSet(e, { size: v });
      const lbl = document.querySelector('[data-qsize-val="' + j + '"]');
      if (lbl) lbl.textContent = v;
      const slider = document.querySelector('#kb-qsheet-body [data-q="size"][data-j="' + j + '"]');
      if (slider && slider !== t && +slider.value !== v) slider.value = v;
    } else if (key === 'color') {
      kbTextStyleSet(e, { color: t.value });
      document.querySelectorAll('.kb-qsw').forEach(b => b.classList.toggle('on', kbSameColor(b.dataset.val, t.value)));
    } else if (key === 'align') {
      kbTextStyleSet(e, { anchor: t.value });
    } else if (key === 'in' || key === 'out') {
      const dur = Math.max(.4, +it.dur || .4);
      const win = kbElWindow(it, e, j);
      const v = clamp(+t.value || 0, 0, dur);
      if (key === 'in') e.in = clamp(v, 0, win[1] - .2);
      else e.out = clamp(v, win[0] + .2, dur);
      kbPaintLayerBar(it, e, j);
    } else if (key === 'animdur' || key === 'delay' || key === 'opacity') {
      e.anim = e.anim || {};
      if (key === 'opacity') e.anim.opacity = clamp(+t.value, 0, 1);
      else if (key === 'delay') e.anim.delay = Math.max(0, +t.value || 0);
      else e.anim.dur = clamp(+t.value || .72, .2, 4);
    } else if (key === 'pfill' || key === 'pstroke' || key === 'pradius') {
      e.el.panelStyle = Object.assign(kbPanelTheme('panel'), e.el.panelStyle || {});
      if (key === 'pfill') e.el.panelStyle.fill = kbRgba(t.value, .74);
      else if (key === 'pstroke') e.el.panelStyle.stroke = t.value;
      else e.el.panelStyle.radius = clamp(+t.value || 0, 0, 40);
      kbApplyPanelStyle(e);
      const rv = document.querySelector('[data-qrad-val="' + j + '"]');
      if (rv) rv.textContent = Math.round(+e.el.panelStyle.radius || 0);
    } else if (key === 'visible') {
      e.visible = !!t.checked;
    } else if (key === 'lock') {
      e.locked = !!t.checked;
    }
    kbMarkDirty();
    if (final) kbRenderLayers();
    kbDrawPreview(kb.play.t);
    kbSyncOverlay();
    return true;
  }

  function kbQuickAct(act, j, val) {
    const it = kbCur();
    if (!it) return;
    if (act === 'close') { kbCloseQuick(); return; }
    if (act === 'add-text') { kbQuickAddText(); return; }
    if (act === 'add-panel') { kbQuickAddPanel(); return; }
    if (act === 'add-frame') { kbQuickAddFrame(); return; }
    const e = it.els && it.els[j] ? it.els[j] : kbSelectedEl();
    if (!e) { kbToast('पहिले कुनै तत्व छान्नुहोस्।', 'err'); return; }
    if (!it.els || it.els.indexOf(e) < 0) return;
    const idx = it.els.indexOf(e);
    if (act === 'preview') {
      const items = kbPreviewItems(), at = items.indexOf(it);
      const win = kbElWindow(it, e, idx);
      if (at >= 0) {
        kbStop();
        kbSeek(kbSceneStart(items, at) + win[0]);
        kbPlayToggle();
      }
      return;
    }
    if (act === 'front' || act === 'back' || act === 'forward' || act === 'backward' || act === 'dup' || act === 'rm' || act === 'vis' || act === 'lock') {
      kbElementAct(act, idx);
      if (kb.quickOpen) kbRenderQuickSheet();
      return;
    }
    if (act === 'fit') { kbQuickFitPanel(); return; }
    kbSnap();
    if (act === 'size-down' || act === 'size-up') {
      kbTextStyleSet(e, { size: kbTextSize(e) + (act === 'size-up' ? 2 : -2) });
    } else if (act === 'swatch') {
      kbTextStyleSet(e, { color: val || '#f2f6ff' });
    } else if (act === 'align') {
      kbTextStyleSet(e, { anchor: val || 'start' });
    } else if (act === 'weight') {
      const st = e.el.textStyle || {};
      kbTextStyleSet(e, { weight: (+st.weight || 700) >= 600 ? 400 : 700 });
    } else if (act === 'line') {
      const st = e.el.textStyle || {};
      kbTextStyleSet(e, { single: !st.single });
    } else if (act === 'entry' || act === 'exit') {
      e.anim = e.anim || {};
      e.anim[act] = val || (act === 'exit' ? 'fade' : 'fade');
      if (act === 'entry') { e.anim.delay = Math.max(0, +e.anim.delay || 0); if (e.in == null) { const w = kbElWindow(it, e, idx); e.in = w[0]; } }
    } else if (act === 'pkind') {
      e.el.panelStyle = Object.assign(kbPanelTheme('panel'), e.el.panelStyle || {});
      e.el.panelStyle.kind = val === 'frame' ? 'frame' : 'panel';
      e.el.panelStyle.radius = e.el.panelStyle.kind === 'frame' ? 14 : 20;
      e.el.custom = true;
      kbApplyPanelStyle(e);
    } else if (act === 'behind') {
      const text = kbTextLayerFor(it, e.box);
      const minZ = Math.min.apply(null, it.els.map(x => +x.z || 0));
      e.z = text && text !== e ? (+text.z || 1) - .2 : minZ - .5;
    } else if (act === 'cardtime') {
      e.in = 0; e.out = Math.max(.4, +it.dur || .4);
    } else if (act === 'halftime') {
      e.in = Math.round((+it.dur || .4) * .5 * 100) / 100;
      e.out = Math.max(e.in + .2, +it.dur || .4);
    }
    kbMarkDirty();
    kbRenderAll();
    kbSyncOverlay();
    if (kb.quickOpen) kbRenderQuickSheet();
    kbToast('अपडेट भयो।');
  }

  function kbElementAdd() {
    kbQuickAddText();
  }

  function kbElementGroup() {
    const it = kbCur(); if (!it || !it.els) return;
    const e = kbSelectedEl(); if (!e) { kbToast('पहिले तत्व छान्नुहोस्।', 'err'); return; }
    kbSnap();
    if (e.group) {
      const g = e.group;
      it.els.forEach(x => { if (x.group === g) x.group = '' });
      kbToast('Group खोलियो।');
    } else {
      const j = it.els.indexOf(e), next = it.els[j + 1];
      const g = 'g' + Date.now().toString(36);
      e.group = g;
      if (next) next.group = g;
      kbToast(next ? 'तत्व Group भयो — अब सँगै सर्नेछ।' : 'Group बनाउन अर्को तत्व थप्नुहोस्।');
    }
    kbMarkDirty(); kbRenderAll();
  }

  function kbAdTarget(focus) {
    const sel = kbSelectedEl();
    if (sel && sel.el && sel.el.ad) return sel;
    for (let i = 0; i < kb.items.length; i++) {
      const it = kb.items[i];
      const j = (it.els || []).findIndex(e => e && e.el && e.el.ad);
      if (j >= 0) {
        if (focus) { kb.cur = i; kb.elSel = j; kb.rightTab = 'settings'; }
        return it.els[j];
      }
    }
    return null;
  }

  function kbAdPick(file) {
    if (!file) return;
    kbPhotoPrepare(file).then(data => {
      const target = kbAdTarget(true);
      if (!target) { kbToast('यो कुण्डलीमा फोटो राख्ने तत्व भेटिएन।', 'err'); return; }
      kbSnap();
      target.adSrc = data; target.visible = true; target.photoTouched = true;
      kbMarkDirty(); kbRefresh(); kbSyncOverlay(); kbRenderRight();
      kbToast('ज्योतिषीको फोटो थपियो · ' + Math.round(data.length / 1024) + ' KB');
    }).catch(err => kbToast((err && err.message) || 'फोटो थप्न सकिएन।', 'err'));
  }

  function kbHotspotHit(it, p) {
    const b = it && it.hotspot;
    return !!(b && b.length === 4 && p.x >= b[0] && p.x <= b[0] + b[2] && p.y >= b[1] && p.y <= b[1] + b[3]);
  }
  function kbOpenHotspot(it) {
    const url = (it && it.hotspotUrl) || '';
    if (!/^https:\/\//i.test(url)) return false;
    window.open(url, '_blank', 'noopener');
    return true;
  }

  function kbSyncOverlay() {
    const box = q('kb-selbox'), stage = q('kb-stage');
    if (!box || !stage) return;
    const it = kbCur(), e = kbSelectedEl();
    if (!kb.open || kb.mode === 'present' || !it || !e || e.visible === false || !e.box) { box.hidden = true; return; }
    const scale = stage.clientWidth / 720;
    box.hidden = false;
    box.style.left = (e.box[0] * scale) + 'px';
    box.style.top = (e.box[1] * scale) + 'px';
    box.style.width = Math.max(6, e.box[2] * scale) + 'px';
    box.style.height = Math.max(6, e.box[3] * scale) + 'px';
    const nm = q('kb-selname'); if (nm) nm.textContent = (e.el && e.el.name || 'तत्व') + (e.locked ? ' · लक' : '');
    box.style.opacity = e.locked ? '.55' : '1';
  }

  function kbBindOverlay() {
    const stage = q('kb-stage'), box = q('kb-selbox');
    if (!stage || !box) return;
    const pt = ev => { const r = stage.getBoundingClientRect(); return { x: (ev.clientX - r.left) * 720 / r.width, y: (ev.clientY - r.top) * 1280 / r.height } };
    const snapVal = (v, list, tol) => {
      let best = null, bd = tol;
      list.forEach(x => { const d = Math.abs(v - x); if (d < bd) { bd = d; best = x } });
      return best;
    };
    const guides = (it, e, cand) => {
      const vs = [0, 360, 720], hs = [0, 640, 1280];
      it.els.forEach(x => {
        if (x === e || !x.box || x.visible === false) return;
        vs.push(x.box[0], x.box[0] + x.box[2] / 2, x.box[0] + x.box[2]);
        hs.push(x.box[1], x.box[1] + x.box[3] / 2, x.box[1] + x.box[3]);
      });
      let gx = null, gy = null;
      const left = snapVal(cand[0], vs, 6), center = snapVal(cand[0] + cand[2] / 2, vs, 6), right = snapVal(cand[0] + cand[2], vs, 6);
      if (left != null) gx = left;
      else if (center != null) gx = center - cand[2] / 2;
      else if (right != null) gx = right - cand[2];
      const top = snapVal(cand[1], hs, 6), mid = snapVal(cand[1] + cand[3] / 2, hs, 6), bot = snapVal(cand[1] + cand[3], hs, 6);
      if (top != null) gy = top;
      else if (mid != null) gy = mid - cand[3] / 2;
      else if (bot != null) gy = bot - cand[3];
      const gv = q('kb-guide-v'), gh = q('kb-guide-h');
      if (gv) { if (gx != null) { gv.style.display = 'block'; gv.style.left = (gx / 720 * 100) + '%'; } else gv.style.display = 'none' }
      if (gh) { if (gy != null) { gh.style.display = 'block'; gh.style.top = (gy / 1280 * 100) + '%'; } else gh.style.display = 'none' }
      return [gx != null ? gx : cand[0], gy != null ? gy : cand[1]];
    };
    const hideGuides = () => {
      const gv = q('kb-guide-v'), gh = q('kb-guide-h');
      if (gv) gv.style.display = 'none';
      if (gh) gh.style.display = 'none';
    };
    const hitAt = (it, p, pointerType) => {
      const pad = pointerType === 'touch' || pointerType === 'pen' ? 16 : 5;
      return it.els.map((e, j) => ({ e: e, j: j }))
        .filter(x => x.e && x.e.visible !== false && x.e.box)
        .filter(x => {
          const b = x.e.box;
          return p.x >= b[0] - pad && p.x <= b[0] + b[2] + pad && p.y >= b[1] - pad && p.y <= b[1] + b[3] + pad;
        })
        .sort((a, b) => (+b.e.z || 0) - (+a.e.z || 0))[0] || null;
    };
    const startDrag = (ev, e, j, handle) => {
      const it = kbCur();
      if (!it || !e || kb.mode === 'present' || e.locked) return;
      ev.preventDefault(); ev.stopPropagation();
      if (kb.play.on) kbStop();
      const p = pt(ev), b = e.box.slice(), aspect = b[2] / Math.max(1, b[3]);
      const others = e.group ? it.els.filter(x => x.group === e.group && x.box) : [e];
      const starts = others.map(x => ({ e: x, x: x.box.slice() }));
      let moved = false, snapped = false;
      const move = mv => {
        const q2 = pt(mv), dx = q2.x - p.x, dy = q2.y - p.y;
        if (!moved) {
          const sc = stage.getBoundingClientRect().width / 720 || 1;
          if (Math.hypot(dx, dy) * sc < 2.5) return;
          moved = true;
          if (!snapped) { kbSnap(); snapped = true; }
          document.body.classList.add('kb-dragging');
        }
        if (mv.cancelable) mv.preventDefault();
        let nb = b.slice();
        if (!handle) {
          const g = guides(it, e, [b[0] + dx, b[1] + dy, b[2], b[3]]);
          let ddx = Math.round((g[0] - b[0]) / 2) * 2;
          let ddy = Math.round((g[1] - b[1]) / 2) * 2;
          const gx0 = Math.min.apply(null, starts.map(s => s.x[0]));
          const gy0 = Math.min.apply(null, starts.map(s => s.x[1]));
          const gx1 = Math.max.apply(null, starts.map(s => s.x[0] + s.x[2]));
          const gy1 = Math.max.apply(null, starts.map(s => s.x[1] + s.x[3]));
          ddx = clamp(ddx, -gx0, Math.max(-gx0, 720 - gx1));
          ddy = clamp(ddy, -gy0, Math.max(-gy0, 1280 - gy1));
          starts.forEach(s => {
            s.e.box[0] = Math.round(s.x[0] + ddx);
            s.e.box[1] = Math.round(s.x[1] + ddy);
          });
          nb[0] = Math.round(b[0] + ddx); nb[1] = Math.round(b[1] + ddy);
          e.box = nb;
        } else {
          const minW = 24, minH = 20;
          if (handle.indexOf('e') >= 0) nb[2] = Math.max(minW, b[2] + dx);
          if (handle.indexOf('w') >= 0) { nb[2] = Math.max(minW, b[2] - dx); nb[0] = b[0] + (b[2] - nb[2]); }
          if (handle.indexOf('s') >= 0) nb[3] = Math.max(minH, b[3] + dy);
          if (handle.indexOf('n') >= 0) { nb[3] = Math.max(minH, b[3] - dy); nb[1] = b[1] + (b[3] - nb[3]); }
          if ((handle.length === 2) && e.aspectLock !== false) {
            nb[3] = nb[2] / aspect;
            if (handle.indexOf('n') >= 0) nb[1] = b[1] + (b[3] - nb[3]);
            if (handle.indexOf('w') >= 0) nb[0] = b[0] + (b[2] - nb[2]);
          }
          nb[2] = Math.round(nb[2] / 2) * 2; nb[3] = Math.round(nb[3] / 2) * 2;
          nb[0] = clamp(nb[0], 0, Math.max(0, 720 - 24));
          nb[1] = clamp(nb[1], 0, Math.max(0, 1280 - 20));
          nb[2] = Math.min(nb[2], 720 - nb[0]);
          if ((handle.length === 2) && e.aspectLock !== false) nb[3] = Math.round((nb[2] / aspect) / 2) * 2;
          nb[3] = Math.min(nb[3], 1280 - nb[1]);
          e.box = nb;
        }
        kbSyncOverlay(); kbDrawPreview(kb.play.t);
      };
      const up = () => {
        document.removeEventListener('pointermove', move);
        document.removeEventListener('pointerup', up);
        document.removeEventListener('pointercancel', up);
        document.body.classList.remove('kb-dragging');
        hideGuides();
        if (!moved) return;
        kbMarkDirty();
        starts.forEach(s => {
          const x = s.e;
          if (x.el && x.el.custom) {
            x.el.bbox = x.box.slice();
            if (x.el.editable) kbApplyElText(x);
            else if (x.el.type === 'panel') kbApplyPanelStyle(x);
          }
        });
        kbPrimeSoon(starts.map(s => s.e.el).filter(Boolean));
        kbRenderLayers();
        if (kb.rightTab === 'settings') kbRenderRight();
        if (kb.quickOpen) kbRenderQuickSheet();
        kbPrimeSoon(e.el ? [e.el] : []);
      };
      document.addEventListener('pointermove', move, { passive: false });
      document.addEventListener('pointerup', up);
      document.addEventListener('pointercancel', up);
    };

    let press = null;
    stage.addEventListener('pointerdown', ev => {
      if (kb.mode === 'present') return;
      if (ev.button != null && ev.button !== 0) return;
      if (ev.target.closest('.kb-h')) {
        const handle = ev.target.closest('.kb-h').dataset.h;
        const e = kbSelectedEl(), it = kbCur();
        if (e && it) { press = { x: ev.clientX, y: ev.clientY }; startDrag(ev, e, it.els.indexOf(e), handle); }
        return;
      }
      if (ev.target.closest('#kb-selbox')) {
        const e = kbSelectedEl(), it = kbCur();
        if (e && it) { press = { x: ev.clientX, y: ev.clientY }; startDrag(ev, e, it.els.indexOf(e), null); }
        return;
      }
      const it = kbCur();
      if (!it || !it.els) return;
      const p = pt(ev);
      press = { x: ev.clientX, y: ev.clientY };
      const hit = hitAt(it, p, ev.pointerType);
      if (hit) {
        const now = Date.now();
        if (kb.play.on) kbStop();
        kb.elSel = hit.j;
        kb.rightTab = 'settings';
        kbRenderRight();
        kbRenderLayers();
        kbDrawPreview(kb.play.t);
        kbSyncOverlay();
        if (kb.lastTap && kb.lastTap.j === hit.j && now - kb.lastTap.t < 380) {
          kb.lastTap = null;
          kbOpenQuick();
          return;
        }
        kb.lastTap = { x: p.x, y: p.y, t: now, j: hit.j };
        startDrag(ev, hit.e, hit.j, null);
      } else {
        kb.lastTap = { x: p.x, y: p.y, t: Date.now(), j: -1 };
        kb.elSel = -1;
        kbDrawPreview(kb.play.t);
        kbSyncOverlay();
        kbRenderRight();
        kbRenderLayers();
      }
    });
    stage.addEventListener('pointerup', ev => {
      if (!press) return;
      const moved = Math.hypot(ev.clientX - press.x, ev.clientY - press.y);
      press = null;
      if (moved > 7 || ev.target.closest('#kb-selbox')) return;
      const it = kbCur();
      if (it && kbHotspotHit(it, pt(ev))) kbOpenHotspot(it);
    });
    window.addEventListener('resize', () => setTimeout(kbSyncOverlay, 40));
    setTimeout(kbSyncOverlay, 60);
  }

  /* ─────────────────── layer timeline (current card) ───────────────────
     One row per real card element. The bar is the element's own in/out
     window, so trimming here is exactly what the renderer reads. */
  function kbElWindow(it, e, j) {
    const dur = Math.max(.4, +(it && it.dur) || .4);
    const anim = (e && e.anim) || {};
    const defIn = Math.max(0, (+anim.delay || 0) + .07 * j);
    let a = e && e.in != null ? +e.in : defIn;
    let b = e && e.out != null ? +e.out : dur;
    a = clamp(isFinite(a) ? a : 0, 0, dur);
    b = clamp(isFinite(b) ? b : dur, Math.min(dur, a + .2), dur);
    return [Math.round(a * 100) / 100, Math.round(b * 100) / 100];
  }
  function kbLayerOrder(it) {
    return (it && it.els ? it.els : []).map((e, j) => ({ e: e, j: j }))
      .filter(x => x.e)
      .sort((a, b) => (+b.e.z || 0) - (+a.e.z || 0));
  }
  function kbLayerTag(e) {
    if (!e || !e.el) return '';
    if (e.el.type === 'panel') return e.el.panelStyle && e.el.panelStyle.kind === 'frame' ? 'फ्रेम' : 'प्यानल';
    if (e.el.editable) return 'पाठ';
    return KB_TYPE_NE[e.el.type] || e.el.type || '';
  }
  function kbRenderLayers() {
    const box = q('kb-layerbar'); if (!box) return;
    const it = kbCur();
    const els = it && it.els ? it.els : [];
    const rowsEl = q('kb-lay-rows');
    const keep = rowsEl ? rowsEl.scrollTop : 0;
    const open = !!kb.layersOpen && !!els.length;
    box.classList.toggle('open', open);
    let h = '<div class="kb-lay-head">' +
      '<button class="kb-lay-toggle" data-lay-toggle="1" aria-expanded="' + (open ? 'true' : 'false') + '">' +
      '<span class="kb-lay-chev">' + (open ? '▾' : '▸') + '</span><b>लेयर टाइमलाइन</b>' +
      '<span class="kb-lay-count">' + els.length + '</span></button>' +
      '<div class="kb-lay-head-actions">' +
      '<button data-quick="text" title="नयाँ पाठ">＋ पाठ</button>' +
      '<button data-quick="style" title="छानिएको तत्व स्टाइल">✨ स्टाइल</button>' +
      '</div></div>';
    if (open) {
      const dur = Math.max(.4, +it.dur || .4);
      h += '<div class="kb-lay-body"><div class="kb-lay-ruler"><span>0s</span><span>' + dur.toFixed(1) + 's</span></div><div class="kb-lay-rows" id="kb-lay-rows">';
      kbLayerOrder(it).forEach(x => {
        const e = x.e, j = x.j;
        const [a, b] = kbElWindow(it, e, j);
        const left = clamp(a / dur * 100, 0, 100);
        const width = clamp((b - a) / dur * 100, 1.2, 100 - left);
        const sel = kb.elSel === j;
        const vis = e.visible !== false;
        h += '<div class="kb-lay-row' + (sel ? ' on' : '') + (vis ? '' : ' off') + (e.locked ? ' locked' : '') + '" data-lay-row="' + j + '">' +
          '<span class="kb-lay-grip" title="तानेर लेयर क्रम बदल्नुहोस्">⠿</span>' +
          '<button class="kb-lay-eye" data-lay-act="vis" data-j="' + j + '" title="देखाउने / लुकाउने">' + (vis ? '◉' : '◌') + '</button>' +
          '<div class="kb-lay-main" data-lay-pick="' + j + '">' +
          '<div class="kb-lay-name"><b>' + kbEsc((e.el && e.el.name) || 'तत्व') + '</b>' +
          '<span class="kb-lay-z">z' + Math.round((+e.z || 1) * 10) / 10 + '</span>' +
          '<span class="kb-lay-tag">' + kbEsc(kbLayerTag(e)) + '</span></div>' +
          '<div class="kb-lay-track" data-lay-track="' + j + '">' +
          '<span class="kb-lay-bar" data-lay-bar="' + j + '" style="left:' + left.toFixed(2) + '%;width:' + width.toFixed(2) + '%">' +
          '<i class="kb-lay-trim in" data-lay-trim="in" data-j="' + j + '"></i>' +
          '<span class="kb-lay-t">' + a.toFixed(1) + '–' + b.toFixed(1) + 's</span>' +
          '<i class="kb-lay-trim out" data-lay-trim="out" data-j="' + j + '"></i>' +
          '</span></div></div>' +
          '<button class="kb-lay-lock" data-lay-act="lock" data-j="' + j + '" title="लक / अनलक">' + (e.locked ? '🔒' : '🔓') + '</button>' +
          '</div>';
      });
      h += '</div><div class="kb-lay-hint">⠿ तान्नुहोस् = लेयर क्रम · बार तान्नुहोस् = समय सार्नुहोस् · छेउ तान्नुहोस् = इन/आउट</div></div>';
    }
    box.innerHTML = h;
    const rows = q('kb-lay-rows'); if (rows) rows.scrollTop = keep;
    document.querySelectorAll('#kb-quickbar [data-quick="layers"]').forEach(b => b.classList.toggle('on', open));
  }
  function kbSelectLayer(j) {
    const it = kbCur();
    if (!it || !it.els || !it.els[j]) return;
    if (kb.play.on) kbStop();
    kb.elSel = j;
    kb.rightTab = 'settings';
    kbRenderRight();
    kbRenderLayers();
    kbDrawPreview(kb.play.t);
    kbSyncOverlay();
    if (kb.quickOpen) kbRenderQuickSheet();
  }
  function kbLayerReorder(from, to) {
    const it = kbCur();
    if (!it || !it.els || from === to) return;
    const order = kbLayerOrder(it);
    const moved = order[from];
    if (!moved) return;
    kbSnap();
    order.splice(from, 1);
    order.splice(clamp(to, 0, order.length), 0, moved);
    order.forEach((x, pos) => { x.e.z = order.length - pos; });
    kb.elSel = moved.j;
    kbMarkDirty();
    kbRenderLayers();
    kbRenderRight();
    kbDrawPreview(kb.play.t);
    kbSyncOverlay();
    kbToast('लेयर क्रम बदलियो।');
  }
  function kbPaintLayerBar(it, e, j) {
    const bar = document.querySelector('#kb-layerbar [data-lay-bar="' + j + '"]');
    if (!bar) return;
    const dur = Math.max(.4, +it.dur || .4);
    const [a, b] = kbElWindow(it, e, j);
    bar.style.left = clamp(a / dur * 100, 0, 100).toFixed(2) + '%';
    bar.style.width = clamp((b - a) / dur * 100, 1.2, 100 - a / dur * 100).toFixed(2) + '%';
    const t = bar.querySelector('.kb-lay-t');
    if (t) t.textContent = a.toFixed(1) + '–' + b.toFixed(1) + 's';
    document.querySelectorAll('#kb-qsheet-body [data-q="in"], #kb-right-body [data-q="in"]').forEach(x => { if (x !== document.activeElement) x.value = a.toFixed(2); });
    document.querySelectorAll('#kb-qsheet-body [data-q="out"], #kb-right-body [data-q="out"]').forEach(x => { if (x !== document.activeElement) x.value = b.toFixed(2); });
  }
  function kbBindLayerBar() {
    const box = q('kb-layerbar'); if (!box) return;
    box.addEventListener('click', ev => {
      if (ev.target.closest('[data-lay-toggle]')) {
        kb.layersOpen = !kb.layersOpen;
        kbRenderLayers();
        setTimeout(() => { if (kb.open) kbDrawPreview(kb.play.t); }, 30);
        return;
      }
      const qb = ev.target.closest('[data-quick]');
      if (qb) { kbQuickMain(qb.dataset.quick); return; }
      const act = ev.target.closest('[data-lay-act]');
      if (act) { kbElementAct(act.dataset.layAct, +act.dataset.j); return; }
      const row = ev.target.closest('[data-lay-pick]');
      if (row) { kbSelectLayer(+row.dataset.layPick); return; }
    });
    box.addEventListener('pointerdown', ev => {
      if (ev.button != null && ev.button !== 0) return;
      const trim = ev.target.closest('[data-lay-trim]');
      const bar = ev.target.closest('[data-lay-bar]');
      if (!trim && !bar) return;
      const it = kbCur();
      const j = +((trim || bar).dataset.j);
      const e = it && it.els ? it.els[j] : null;
      if (!e || e.locked) return;
      const track = (trim || bar).closest('.kb-lay-track');
      if (!track) return;
      const w = track.getBoundingClientRect().width;
      if (!w) return;
      ev.preventDefault();
      ev.stopPropagation();
      if (ev.target.closest('[data-lay-trim]')) ev.stopImmediatePropagation();
      const dur = Math.max(.4, +it.dur || .4);
      const startX = ev.clientX;
      const [a0, b0] = kbElWindow(it, e, j);
      if (e.in == null) e.in = a0;
      if (e.out == null) e.out = b0;
      let changed = false;
      const snap = v => Math.round(v / .05) * .05;
      const move = mv => {
        const dt = (mv.clientX - startX) / w * dur;
        if (Math.abs(mv.clientX - startX) < 1) return;
        if (!changed) { changed = true; kbSnap(); }
        if (trim) {
          if (trim.dataset.layTrim === 'in') e.in = clamp(snap(a0 + dt), 0, b0 - .2);
          else e.out = clamp(snap(b0 + dt), a0 + .2, dur);
        } else {
          const len = b0 - a0;
          const na = clamp(snap(a0 + dt), 0, Math.max(0, dur - len));
          e.in = na; e.out = Math.min(dur, na + len);
        }
        kbPaintLayerBar(it, e, j);
        kbDrawPreview(kb.play.t);
      };
      const up = () => {
        document.removeEventListener('pointermove', move);
        document.removeEventListener('pointerup', up);
        document.removeEventListener('pointercancel', up);
        if (!changed) return;
        kbMarkDirty();
        kbRenderLayers();
        if (kb.rightTab === 'settings') kbRenderRight();
      };
      document.addEventListener('pointermove', move, { passive: false });
      document.addEventListener('pointerup', up);
      document.addEventListener('pointercancel', up);
    }, { passive: false });
  }
  function kbBindLayerSort() {
    const box = q('kb-layerbar'); if (!box) return;
    kbBindSortable(box, {
      item: '.kb-lay-row', axis: 'y', scroller: () => q('kb-lay-rows'),
      handle: '.kb-lay-grip', touchHold: false, ignore: '[data-lay-track]',
      canDrag: () => !!(kbCur() && kbCur().els && kbCur().els.length > 1),
      onDrop: (from, to) => kbLayerReorder(from, to)
    });
  }

  function kbRenderScenes() {
    const strip = q('kb-scenes'); if (!strip) return;
    const keep = strip.scrollLeft;
    const items = kbPreviewItems();
    if (!items.length) { strip.innerHTML = ''; return; }
    strip.innerHTML = items.map((it, i) => {
      const nm = it.title || it.el.name;
      return '<button class="kb-scene-chip" data-scene="' + i + '" title="तानेर क्रम बदल्नुहोस् · ' + kbAttr(nm) + '">' +
        '<span class="kb-scene-grip" aria-hidden="true">⠿</span>' +
        '<span class="kb-scene-name">' + (i + 1) + '. ' + kbEsc(nm) + '</span></button>';
    }).join('');
    strip.scrollLeft = keep;
  }

  function kbUpdateStat() {
    const st = q('kb-stat'); if (!st) return;
    const items = kb.items;
    const total = kbTotalTime(items);
    const def = kbTplDef(kb.tpl);
    st.innerHTML = '<b>' + items.length + '</b> दृश्य · कुल <b>' + kbFmtTime(total) + '</b> · टेम्प्लेट <b>' + kbEsc(def.name) + '</b>';
    const cnt = q('kb-elcount'); if (cnt) cnt.textContent = items.length + ' छानिएको';
    const mt = q('kb-mt-el'); if (mt) mt.textContent = items.length;
  }

  function kbDrawEmpty(g, w, h) {
    const def = kbTplDef(kb.tplPreview || kb.tpl);
    g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.shadowBlur = 0;
    kbDrawBg(g, w, h, def, kb.play.t);
    const lay = kbLayout(w, h);
    g.save(); g.translate(lay.ox, lay.oy); g.scale(lay.u, lay.u);
    kbDrawFrame(g, def);
    g.textAlign = 'center'; g.textBaseline = 'alphabetic';
    g.fillStyle = kbRgba(def.accent, .9);
    g.font = '600 11px "' + def.font + '","Noto Sans Devanagari",sans-serif';
    g.fillText((def.tag || '') + ' · 3D TIMELINE', 360, 520);
    g.fillStyle = def.ink;
    g.font = '700 34px "' + def.display + '","Noto Sans Devanagari",sans-serif';
    g.fillText('तत्व छान्नुहोस्', 360, 578);
    g.fillStyle = def.mut;
    g.font = '500 17px "' + def.font + '","Noto Sans Devanagari",sans-serif';
    g.fillText('बायाँको सूचीबाट चार्ट, तालिका, कार्ड वा शीर्षक छान्नुहोस्।', 360, 622);
    g.font = '500 14px "' + def.font + '","Noto Sans Devanagari",sans-serif';
    g.fillText('हरेक तत्व छुट्टै 3D दृश्य बन्न सक्छ।', 360, 652);
    g.strokeStyle = kbRgba(def.accent, .35); g.lineWidth = 1.2;
    g.beginPath(); g.moveTo(300, 690); g.lineTo(420, 690); g.stroke();
    g.restore();
  }

  function kbDrawPreview(t) {
    if (!kb.open) return;
    const cv = q('kb-canvas'); if (!cv) return;
    const g = cv.getContext('2d');
    const items = kbPreviewItems();
    const sctlEmpty = q('kb-scroll-ctl');
    if (!items.length) {
      kbDrawEmpty(g, cv.width, cv.height);
      const scrub = q('kb-scrub'); if (scrub) scrub.value = 0;
      const time = q('kb-time'); if (time) time.textContent = '0:00 / 0:00';
      const info = q('kb-stage-info'); if (info) info.textContent = '—';
      const nm = q('kb-stage-name'); if (nm) nm.textContent = 'Live preview';
      if (sctlEmpty) sctlEmpty.hidden = true;
      return;
    }
    const total = kbTotalTime(items);
    t = clamp(t, 0, total);
    const at = kbSceneAt(items, t);
    const scene = kbSceneOf(items[at.i], at.i, items, kb.tplPreview || null);
    const nextItem = items[at.i + 1];
    const next = nextItem ? kbSceneOf(nextItem, at.i + 1, items, kb.tplPreview || null) : null;
    const sctl = q('kb-scroll-ctl');
    if (sctl) {
      const isScroll = !!(scene.scrollDur || (scene.els || []).some(e => e && e.scroll));
      sctl.hidden = !isScroll;
      if (isScroll) {
        const pb = q('kb-scroll-pause');
        if (pb) pb.textContent = kb.play.on ? 'Pause' : 'Play';
        const spd = clamp((scene.set && scene.set.speed) || 1, .4, 3);
        const pct = scene.scrollDur ? kbScrollProgress(scene, at.local, spd) : 0;
        const pc = q('kb-scroll-pct');
        if (pc) pc.textContent = Math.round(pct * 100) + '%';
      }
    }
    /* Prime the visible card and the next one ahead of time. SVG charts are
       real generated components, so this only pre-decodes their images and
       removes the one-frame placeholder when moving to the next card. */
    const pre = kbSceneEls(scene).concat(next ? kbSceneEls(next) : []);
    let miss = false;
    for (let i = 0; i < pre.length; i++) {
      const el = pre[i]; if (!el) continue;
      if (!kbImgCache.get(kbImgKey(el))) { miss = true; break; }
    }
    if (miss) kbPrimeEls(pre).then(() => { if (kb.open) kbDrawPreview(kb.play.t); });
    kbDrawScene(g, cv.width, cv.height, scene, at.local, { next: next, clock: t });
    const scrub = q('kb-scrub');
    if (scrub && document.activeElement !== scrub) scrub.value = total ? (t / total) * 1000 : 0;
    const time = q('kb-time'); if (time) time.textContent = kbFmtTime(t) + ' / ' + kbFmtTime(total);
    const info = q('kb-stage-info');
    if (info) info.textContent = (at.i + 1) + '/' + items.length + ' · ' + (KB_TYPE_NE[scene.el.type] || scene.el.type) + ' · ' + scene.dur.toFixed(1) + 's';
    const nm = q('kb-stage-name');
    if (nm) nm.textContent = kb.tplPreview ? ('टेम्प्लेट प्रिभ्यू · ' + kbTplDef(kb.tplPreview).name) : 'Live 3D preview';
    document.querySelectorAll('#kb-scenes [data-scene]').forEach(b => b.classList.toggle('on', +b.dataset.scene === at.i));
  }
  function kbPreviewRedraw() { if (kb.open) kbDrawPreview(kb.play.t); }
  window.kbPreviewRedraw = kbPreviewRedraw;

  function kbStop() {
    kb.play.on = false;
    if (kb.play.raf) cancelAnimationFrame(kb.play.raf);
    kb.play.raf = 0;
    const b = q('kb-play');
    if (b) b.innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5.5v13l11-6.5z"/></svg>';
  }
  function kbPlayToggle() {
    if (kb.play.on) { kbStop(); return; }
    const items = kbPreviewItems();
    if (!items.length) { kbToast('पहिले बायाँबाट कम्तीमा एउटा तत्व छान्नुहोस्।', 'err'); return; }
    const total = kbTotalTime(items);
    if (kb.play.t >= total - .02) kb.play.t = 0;
    kb.play.on = true; kb.play.last = performance.now();
    const b = q('kb-play');
    if (b) b.innerHTML = '<svg viewBox="0 0 24 24" fill="currentColor"><rect x="7" y="5" width="3.6" height="14" rx="1"/><rect x="13.4" y="5" width="3.6" height="14" rx="1"/></svg>';
    const loop = ts => {
      if (!kb.play.on) return;
      const dt = Math.min(.06, (ts - kb.play.last) / 1000 || 0);
      kb.play.last = ts;
      kb.play.t += dt;
      const items2 = kbPreviewItems(), tot = kbTotalTime(items2);
      if (kb.play.t >= tot) { kb.play.t = tot; kbDrawPreview(tot); kbStop(); return; }
      kbDrawPreview(kb.play.t);
      kb.play.raf = requestAnimationFrame(loop);
    };
    kb.play.raf = requestAnimationFrame(loop);
  }
  function kbSeek(t) {
    const items = kbPreviewItems(), total = kbTotalTime(items);
    kb.play.t = clamp(t, 0, total);
    kbDrawPreview(kb.play.t);
  }
  function kbStep(dir) {
    const items = kbPreviewItems(); if (!items.length) return;
    kbStop();
    const at = kbSceneAt(items, kb.play.t);
    let i = at.i + (dir > 0 ? 1 : 0);
    if (dir < 0 && at.local > .35) i = at.i;
    else if (dir < 0) i = at.i - 1;
    i = clamp(i, 0, items.length - 1);
    kbSeek(kbSceneStart(items, i));
    kbFocusItem(items, i);
  }

  /* Selecting a scene in the strip or with Prev/Next also targets that
     card in the settings panel, so element actions never edit a hidden
     card by mistake. */
  function kbFocusItem(items, i) {
    const it = items && items[i];
    if (!it) return;
    const idx = kb.items.indexOf(it);
    if (idx >= 0) kb.cur = idx;
    kb.elSel = (it.els && it.els.length) ? 0 : -1;
    kb.rightTab = 'settings';
    kbRenderScenes();
    kbRenderRight();
    kbSyncOverlay();
  }

  function kbClose(mode) {
    if (!kb.open) return;
    kbStop();
    clearTimeout(kb.primeT); clearTimeout(kb.toastT);
    if (kb.key) document.removeEventListener('keydown', kb.key);
    kb.key = null;
    const el = q('kun-builder'); if (el) el.remove();
    kb.open = false;
    clearTimeout(kb.saveT);
    if (kb.auto && kb.autoFp) kbAutoSave(false);
    const resolve = kb.resolve; kb.resolve = null;
    kb.items = []; kb.cur = -1; kb.catalog = null; kb.byId = new Map();
    kb.data = null; kb.meta = null; kb.demo = null; kb.tplPreview = null; kb.importing = false;
    kb.auto = false; kb.autoFp = ''; kb.autoOpts = null; kb.transit = null;
    kb.baseEls = new Map(); kb.undo.length = 0; kb.redo.length = 0; kb.elSel = -1;
    if (mode === 'cancel') {
      const st = q('st'); if (st) st.textContent = 'कुण्डली रद्द गरियो — हालको प्रोजेक्ट जस्ताको तस्तै छ।';
    }
    if (resolve) resolve(mode || 'cancel');
  }
  function kbCancel() { kbClose('cancel'); }
  function kbDefault() {
    const st = q('st'); if (st) st.textContent = 'डिफल्ट कुण्डली टाइमलाइन बनाइँदै…';
    kbClose('default');
  }

  async function kbImport() {
    if (kb.importing) return;
    kbHideConfirm();
    const active = kbActiveItems();
    if (!active.length) {
      kbMsg('कम्तीमा एक दृश्य सक्रिय छान्नुहोस्, वा “डिफल्ट टाइमलाइन” थिच्नुहोस्।', 'err');
      kbToast('कुनै दृश्य सक्रिय छैन।', 'err');
      return;
    }
    kb.importing = true;
    const btn = q('kb-import'); if (btn) { btn.disabled = true; btn.textContent = 'बनाइँदै…'; }
    kbMsg('टाइमलाइन बनाइँदै…', '');
    try {
      const items = active.slice();
      /* Phase 10: remember every Timeline edit before the rebuild so a model
         switch or re-generation can merge text/style/box/timing back. */
      const prevScenes = window.kunCaptureScenes ? window.kunCaptureScenes() : null;
      let mergeRep = null;
      await saveNow(true);
      hideHome();
      newProject();
      /* Keep the brand watermark out of the card text. Kundali cards use the
         full 9:16 safe area, so a bouncing watermark would cross charts and
         reports. Pin it to the bottom strip and keep it subtle. */
      try {
        if (Array.isArray(WMS)) {
          WMS.forEach(w => {
            w.pos = 'bc'; w.mv = 'none';
            w.size = Math.min(+w.size || 18, 10);
            w.op = Math.min(+w.op || 55, 65);
          });
          if (typeof renderWm === 'function') renderWm();
        }
      } catch (e) { }
      slides.length = 0; clips.length = 0;
      const total = items.length;
      for (let i = 0; i < total; i++) {
        const it = items[i];
        const main = kbItemMainEl(it) || { name: 'कुण्डली', pageTitle: '' };
        const s = mk(it.title || main.name, main.pageTitle || '', '');
        s.noText = true;
        s.kunManual = true;
        s.dur = Math.max(1, it.dur + it.gap);
        slides.push(s);
        const scene = kbSceneOf(it, i, items, kb.tpl);
        scene.tpl = kb.tpl;
        clips.push({
          id: nid(), sid: s.id, cover: true, pos: 'custom', name: it.title || main.name,
          mh: .5, size: 100, shape: 'round', fx: '', kun: scene
        });
      }
      applyState(capture(), {}, null, false);
      if (prevScenes && window.kunMergeImportScenes) {
        try { mergeRep = window.kunMergeImportScenes(prevScenes); } catch (e) { mergeRep = null; }
      }
      cur = 0; sel = 0; selT = 's'; layout(); renderCl(); renderTL(); renderEd();
      if (window.kunPrimeAll) await window.kunPrimeAll();
      draw(0); head();
      await saveNow(true);
      const st = q('st');
      if (st) {
        const kept = mergeRep && (mergeRep.text + mergeRep.style + mergeRep.box + mergeRep.timing + mergeRep.added + (mergeRep.photo || 0));
        const lost = mergeRep && (mergeRep.missing + mergeRep.runsMissing);
        st.textContent = 'कुण्डली ३डी टाइमलाइन तयार — ' + slides.length + ' दृश्य, ' + kbTplDef(kb.tpl).name + ' टेम्प्लेट।' +
          (kept ? ' Manual सम्पादन जोगियो (' + kept + ')।' : '') +
          (lost ? ' ' + lost + ' element/run भेटिएन — report मा हेर्नुहोस्।' : '');
      }
      kbClose('import');
      /* Phase 9: land on the Timeline and open the card inspector. The old
         "Write / New project" sheet must not cover the generated timeline. */
      if (window.kunAfterImport) {
        try { window.kunAfterImport(); } catch (e) { }
      } else {
        tab('auto'); openSheet();
      }
    } catch (err) {
      kb.importing = false;
      if (btn) { btn.disabled = false; btn.textContent = 'टाइमलाइनमा लागू गर्नुहोस्'; }
      kbMsg('लागू गर्न सकिएन: ' + ((err && err.message) || err), 'err');
      const st = q('st'); if (st) st.textContent = 'गल्ती: ' + ((err && err.message) || err);
    }
  }

  function kbFetchTransit(data, meta) {
    const m = meta || (data && data.metadata) || {};
    const aya = encodeURIComponent(String(m.ayanamsha_type || 'LAHIRI').toUpperCase());
    const node = encodeURIComponent(String(m.node_type || 'MEAN').toUpperCase());
    const date = new Date().toISOString().slice(0, 10);
    const url = '/api/kundali/transit?planet=Saturn&date=' + date + '&ayanamsha=' + aya + '&node=' + node;
    return new Promise(resolve => {
      let done = false;
      const finish = v => { if (!done) { done = true; resolve(v); } };
      const timer = setTimeout(() => finish(null), 25000);
      try {
        fetch(url, { cache: 'no-store' }).then(r => r.ok ? r.json() : null).then(j => {
          clearTimeout(timer);
          finish(j && j.current ? j : null);
        }).catch(() => { clearTimeout(timer); finish(null); });
      } catch (e) { clearTimeout(timer); finish(null); }
    });
  }

  window.kunBuilderOpen = function (data, params, opts) {
    if (kb.open) kbClose('cancel');
    opts = opts || {};
    return new Promise(async resolve => {
      kb.resolve = resolve;
      kb.data = data;
      const meta = Object.assign({}, data.metadata || {}, params || {});
      if (params) {
        if (params.name) meta.name = params.name;
        if (params.gender) meta.gender = params.gender;
        if (params.city) meta.city = params.city;
        if (params.country) meta.country = params.country;
      }
      kb.meta = meta;
      try { KUN_META = meta; } catch (e) { }
      kb.catalog = KunBuilderCatalog.build(data, meta);
      kb.byId = new Map();
      kb.catalog.pages.forEach(p => p.elements.forEach(el => kb.byId.set(el.id, { el: el, page: p })));
      kb.dateLabel = kunDateNe(meta.birth_date) + ' · ' + kunTime(meta.birth_time);
      kb.items = []; kb.cur = -1; kb.tpl = 'cosmic'; kb.tplPreview = null; kb.search = '';
      kb.openPages = new Set(); kb.rightTab = 'order'; kb.demo = null;
      kb.play = { on: false, t: 0, raf: 0, last: 0 }; kb.importing = false;
      kb.auto = false; kb.autoFp = ''; kb.autoOpts = null; kb.model = 'cosmic';
      kb.baseEls = new Map(); kb.transit = null;
      kb.undo.length = 0; kb.redo.length = 0; kb.elSel = -1; kb.dirty = false;
      kb.mode = 'edit'; kb.open = true;

      if (opts.auto && window.KunAutoBuild) {
        const st = q('st');
        if (st) st.textContent = 'AUTOMATIC: वास्तविक गोचर र कुण्डली डेटा पढ्दै…';
        const modelKey = KunAutoBuild.modelByKey(opts.model || 'cosmic').key;
        kb.model = modelKey;
        kb.auto = true;
        kb.autoOpts = Object.assign({}, opts, { model: modelKey });
        kb.autoFp = KunAutoBuild.fingerprint(data, meta, modelKey);
        kb.transit = await kbFetchTransit(data, meta);
        const base = KunAutoBuild.build(data, meta, { transit: kb.transit, model: modelKey });
        kb.items = base;
        kb.items.forEach(it => {
          it.set = KunAutoBuild.set(it.tpl || 'cosmic');
          (it.els || []).forEach(e => { if (e.el && e.el.id) kb.baseEls.set(e.el.id, e.el); });
        });
        const lay = kbAutoLoad();
        if (lay) kbApplyLayout(lay);
        /* The Timeline portrait is the source of truth: opening the builder
           from an edited card must preview that photo instead of an older
           auto-saved layout. `photoSet` separates "no photo yet" from a
           deliberate removal, so a fresh card keeps its saved layout. */
        if (opts.photoSet) {
          kb.items.forEach(it => (it.els || []).forEach(e => {
            if (e.el && e.el.ad) { e.adSrc = opts.photoSrc || ''; e.photoTouched = true; }
          }));
        }
        kb.tpl = KunAutoBuild.modelByKey(modelKey).tpl;
        kb.cur = 0; kb.elSel = 0; kb.rightTab = 'settings';
        if (st) st.textContent = 'AUTOMATIC: ' + KunAutoBuild.modelByKey(modelKey).ne + ' — ' + kb.items.length + ' कार्ड तयार, प्रिभ्यू जाँच्नुहोस्।';
      }

      kbMount();
      kbRenderAll();
      kbUpdateAutoStatus();
      kbSeek(0);
      kbSyncOverlay();
      const first = kb.cur >= 0 ? kbCur() : (kb.catalog.pages[0] && kb.catalog.pages[0].elements[0]);
      if (opts.auto) {
        kbPrimeSoon((kbCur() && kbCur().els || []).map(e => e.el));
      } else if (first) kbPrimeSoon([first]);
    });
  };
})();
