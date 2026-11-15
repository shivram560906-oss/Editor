/* ═══════════════════════════════════════════════════════════════════
   AUTOMATIC Kundali Timeline — full multi-card generator
   ------------------------------------------------------------------
   Builds the full free-layout card set from the actual Kundali-Desktop response.
   Every element is a live chart / table / report component, not a
   screenshot. Only layout, animation and optional text overrides are
   persisted by the builder.
   ═══════════════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  /* TikTok safe area: the top tabs (Following / For You), status bar and the
     bottom caption band are not part of the visible design. The card frame
     starts at the 112px safe line and the first readable line sits below it.
     The earlier 112px padding left a visibly empty band above every card;
     the card now begins at the safe line while keeping the same bottom edge,
     so the whole composition moves up together. */
  const TOP_SAFE = 56;
  const CARD = [46, 56 + TOP_SAFE, 628, 1168 - TOP_SAFE];
  const L = 58, W = 604, R = L + W;
  const FOOT_Y = 1160;
  const GOLD = '#f6d365', GOLD2 = '#e8b923', INK = '#f2f6ff', MUT = '#a9b8d8', DIM = '#7c8dab';
  const GOOD = '#34d399', BAD = '#fb7185', MID = '#fbbf24';
  const BS_MONTHS_NE = ['बैशाख', 'जेठ', 'असार', 'साउन', 'भदौ', 'असोज', 'कात्तिक', 'मंसिर', 'पुष', 'माघ', 'फागुन', 'चैत'];

  /* ═══════════════════════════════════════════════════════════════
     FOUR AUTOMATIC DESIGN MODELS
     ------------------------------------------------------------------
     Each model owns its palette, fonts, card-surface treatment, header
     composition, animation rhythm and transition. The content builders
     below emit one canonical SVG; `themeSvg()` remaps the palette and
     fonts per model. Charts keep their real Vedic colours so data stays
     readable and accurate in every model. Models are isolated through
     their own template id and their own saved layout fingerprint.
     ═══════════════════════════════════════════════════════════════ */
  const MODELS = {
    cosmic: {
      id: 1, key: 'cosmic', tpl: 'cosmic', badge: 'DEFAULT',
      name: 'Cosmic Gold', ne: 'कस्मिक गोल्ड', tag: 'ब्रह्माण्ड · गहिराइ',
      desc: 'गहिरो नीलो ब्रह्माण्ड, सुनौलो प्रकाश, कक्षा र ताराहरू — सुधारिएको डिफल्ट मोडेल।',
      body: 'Mukta', display: 'Rozha One', textScale: 1, lineScale: 1, durScale: 1,
      minDur: 7, maxDur: 28, readWps: 3.0,
      seqStep: .10, seqBand: .16, seqMax: 2.0,
      colors: {
        accent: '#f6d365', accent2: '#e8b923', ink: '#f4f8ff', mut: '#b3c2de', dim: '#91a5c7',
        good: '#34d399', bad: '#fb7185', mid: '#fbbf24', panel: '#0c1830', panel2: '#122241',
        deep: '#081226', chrome: '#142848', line: '#26375c', line2: '#33456e',
        tableHead: '#1d2e52', tableRow: '#0e1a32', tableRow2: '#13213d',
        badPanel: '#22101c', cyan: '#6ee7ff', violet: '#c4b5fd', blue: '#60a5fa',
        badText: '#ffb4bd', goodText: '#b9f6d9', violetText: '#d8ccff', badMut: '#d6a5ae'
      },
      set: { speed: 1, entry: 'fade', exit: 'none', trans: 'smooth', depth: 24, radius: 20, stagger: .09, animDur: .82, gap: .65 },
      anim: {
        heading: 'fade', caption: 'fade', text: 'rise', chart: 'depth', art: 'depth',
        cards: 'rise', table: 'rise', graph: 'rise', report: 'rise', note: 'rise',
        delay: .10, kind: 'float'
      },
      fx: ['Rise + float', 'Smooth crossfade', 'Orbit depth']
    },
    nebula: {
      id: 2, key: 'nebula', tpl: 'nebula', badge: 'NEW · 2',
      name: 'Nebula Glass', ne: 'नेबुला ग्लास', tag: 'नीहारिका · काँच',
      desc: 'बैजनी–निलो नीहारिका, तैरिने काँचका प्यानल, नरम प्रकाश र डिसोल्भ ट्रान्जिसन।',
      body: 'Hind', display: 'Baloo 2', textScale: 1.02, lineScale: 1.04, durScale: 1,
      minDur: 7, maxDur: 28, readWps: 2.82,
      seqStep: .13, seqBand: .20, seqMax: 2.1,
      colors: {
        accent: '#e9d5ff', accent2: '#22d3ee', ink: '#f8f5ff', mut: '#c4b5fd', dim: '#8b7bb8',
        good: '#34d399', bad: '#fb7185', mid: '#fbbf24', panel: '#170b34', panel2: '#211048',
        deep: '#0b0422', chrome: '#2a1550', line: '#4b2d78', line2: '#5b3a8a',
        tableHead: '#2a1550', tableRow: '#150a30', tableRow2: '#1b0e3b',
        badPanel: '#2a0e2a', cyan: '#67e8f9', violet: '#d8b4fe', blue: '#93c5fd',
        badText: '#fecdd3', goodText: '#bbf7d0', violetText: '#ede9fe', badMut: '#e9a5b0'
      },
      set: { speed: .98, entry: 'fade', exit: 'none', trans: 'dissolve', depth: 30, radius: 26, stagger: .13, animDur: .96, gap: .72 },
      anim: {
        heading: 'zoom', caption: 'soft', text: 'soft', chart: 'zoom', art: 'zoom',
        cards: 'soft', table: 'rise', graph: 'rise', report: 'soft', note: 'rise',
        delay: .14, kind: 'float'
      },
      fx: ['Zoom + float', 'Dissolve', 'Glass panes']
    },
    vedic: {
      id: 3, key: 'vedic', tpl: 'vedic', badge: 'NEW · 3',
      name: 'Vedic Parchment', ne: 'वैदिक पोथी', tag: 'पोथी · मण्डल',
      desc: 'पुरानो पोथीको कागज, मारुन–सुनौलो किनारा, घुम्ने राशि मण्डल र सफा टाइपोग्राफी।',
      body: 'Tiro Devanagari Hindi', display: 'Rozha One', textScale: .99, lineScale: 1.05, durScale: 1,
      minDur: 7, maxDur: 28, readWps: 2.78,
      seqStep: .09, seqBand: .14, seqMax: 1.9,
      colors: {
        accent: '#8a1c1c', accent2: '#a16207', ink: '#2b160d', mut: '#5b3d26', dim: '#7a5c3a',
        good: '#1f6b3a', bad: '#a51c30', mid: '#b45309', panel: '#fbf1dc', panel2: '#f6e7c8',
        deep: '#efdcb8', chrome: '#e7cfa6', line: '#c8a978', line2: '#d6bd93',
        tableHead: '#e7cfa6', tableRow: '#fdf6e7', tableRow2: '#f7e9cf',
        badPanel: '#f7e2dc', cyan: '#0e7490', violet: '#6d28d9', blue: '#1d4ed8',
        badText: '#8a1c1c', goodText: '#1f6b3a', violetText: '#5b21b6', badMut: '#7f1d1d'
      },
      set: { speed: 1.02, entry: 'reveal', exit: 'none', trans: 'wipe', depth: 10, radius: 5, stagger: .09, animDur: .90, gap: .58 },
      anim: {
        heading: 'grow-x', caption: 'fade', text: 'reveal', chart: 'grow-y', art: 'fade',
        cards: 'reveal', table: 'grow-y', graph: 'grow-y', report: 'reveal', note: 'fade',
        delay: .09, kind: 'none'
      },
      fx: ['Page reveal', 'Wipe', 'Ruled parchment']
    },
    orbit: {
      id: 4, key: 'orbit', tpl: 'orbit', badge: 'NEW · 4',
      name: 'Solar Orbit', ne: 'सोलार अर्बिट', tag: 'सौर्यमण्डल · HUD',
      desc: 'सौर्यमण्डलको कक्षीय गति, नियोन HUD, गाढा टिल प्यानल र छिटो स्लाइड एनिमेसन।',
      body: 'Mukta', display: 'Yatra One', textScale: 1, lineScale: 1.03, durScale: 1,
      minDur: 7, maxDur: 28, readWps: 3.12,
      seqStep: .06, seqBand: .10, seqMax: 1.5,
      colors: {
        accent: '#a3e635', accent2: '#22d3ee', ink: '#ecfeff', mut: '#8fd8cf', dim: '#5b9a94',
        good: '#4ade80', bad: '#fb7185', mid: '#facc15', panel: '#04181c', panel2: '#06252a',
        deep: '#020e10', chrome: '#083036', line: '#0f4a44', line2: '#13645b',
        tableHead: '#083036', tableRow: '#031214', tableRow2: '#04191c',
        badPanel: '#2a0e14', cyan: '#22d3ee', violet: '#c4b5fd', blue: '#60a5fa',
        badText: '#fecdd3', goodText: '#bbf7d0', violetText: '#ddd6fe', badMut: '#e9a5b0'
      },
      set: { speed: 1.02, entry: 'slide', exit: 'none', trans: 'zoom', depth: 18, radius: 8, stagger: .06, animDur: .68, gap: .50 },
      anim: {
        heading: 'slide', caption: 'slide', text: 'slide', chart: 'zoom', art: 'zoom',
        cards: 'slide', table: 'slide', graph: 'slide', report: 'slide', note: 'slide',
        delay: .075, kind: 'scan'
      },
      fx: ['HUD slide', 'Zoom push', 'Telemetry rail']
    }
  };
  const MODEL_KEYS = ['cosmic', 'nebula', 'vedic', 'orbit'];

  /* Playback order — one source of truth for the presentation sequence.
     The content id (`no`) of a card never changes; only this priority puts
     it in the story. Continuation pages use the base priority plus 0.5 so
     they always stay directly after their first page.
     Story flow: birth chart → other charts → planet analysis → strength →
     yogas → time (dasha) → document → closing. */
  const ORDER = {
    birth: 10,
    moon: 20,
    d9: 30,
    relation: 40,
    strength: 50,
    pillars: 60,
    sav: 70,
    savHouses: 75,
    goodYoga: 80,
    badYoga: 90,
    sadeSati: 95,
    lalKitab: 100,
    dasha: 110,
    dashaEffect: 120,
    yoginiEffect: 130,
    janmapatrika: 140,
    wishes: 150,
    consult: 160
  };

  let MODEL = MODELS.cosmic;
  let ALIAS = null;

  function aliasMap(c) {
    const ALIAS = {
      '#0d1830': c.panel, '#0c1930': c.panel, '#121d35': c.panel,
      '#101d36': c.panel2, '#17233e': c.panel2,
      '#0a1224': c.deep, '#0a1726': c.deep, '#0b1a33': c.deep,
      '#12233f': c.chrome, '#1b2743': c.tableHead,
      '#0f172b': c.tableRow, '#101d36': c.tableRow2,
      '#1a0d16': c.badPanel,
      '#223052': c.line, '#2b3856': c.line2,
      '#f6d365': c.accent, '#e8b923': c.accent2,
      '#f2f6ff': c.ink, '#e9eefb': c.ink, '#e6ecfa': c.ink,
      '#a9b8d8': c.mut, '#9fb0d0': c.mut, '#b9c6e4': c.mut, '#d9b98f': c.mut,
      '#7c8dab': c.dim, '#7183a8': c.dim,
      '#34d399': c.good, '#fb7185': c.bad, '#fbbf24': c.mid,
      '#6ee7ff': c.cyan, '#c4b5fd': c.violet, '#60a5fa': c.blue,
      '#ffb4bd': c.badText, '#b9f6d9': c.goodText, '#d8ccff': c.violetText, '#d6a5ae': c.badMut,
      '#d6a5ae': c.badMut
    };
    return ALIAS;
  }
  function themeSvg(inner, type, extra) {
    if (!inner || (extra && extra.jp)) return inner;
    const c = MODEL.colors;
    if (!ALIAS) ALIAS = aliasMap(c);
    let s = inner.replace(/#[0-9a-fA-F]{6}/g, m => ALIAS[m.toLowerCase()] || m);
    const fam = (type === 'heading' ? MODEL.display : MODEL.body) + ',Noto Sans Devanagari,sans-serif';
    s = s.replace(/font-family="Noto Sans Devanagari, Mukta, sans-serif"/g, 'font-family="' + fam + '"');
    return s;
  }
  function fitTitle(title, maxW, maxSize) {
    const n = String(title || '').length || 1;
    let fs = maxSize;
    while (fs > 15 && n * fs * .54 > maxW) fs -= .5;
    return Math.round(fs * 2) / 2;
  }
  function modelByKey(k) { return MODELS[k] || MODELS.cosmic; }

  let SEQ = 0;
  function el(page, title, type, name, box, inner, dur, extra) {
    const shifted = [box[0], box[1] + TOP_SAFE, box[2], box[3]];
    const o = {
      id: 'auto-c' + String(page).padStart(2, '0') + '-e' + String(++SEQ).padStart(2, '0'),
      page: page, pageTitle: title, type: type, name: name,
      bbox: shifted,
      /* One shared vertical offset moves every component, chart and table
         below the TikTok top UI without resizing or distorting any text. */
      inner: '<g transform="translate(0,' + TOP_SAFE + ')">' + themeSvg(inner, type, extra) + '</g>',
      dur: dur || 7
    };
    if (extra) {
      Object.assign(o, extra);
      if (extra.textStyle) o.textStyle = Object.assign({}, extra.textStyle, { y: extra.textStyle.y + TOP_SAFE });
      if (extra.scrollBbox) o.scrollBbox = [extra.scrollBbox[0], extra.scrollBbox[1] + TOP_SAFE, extra.scrollBbox[2], extra.scrollBbox[3]];
    }
    return o;
  }
  function T(x, y, txt, size, color, weight, anchor) {
    return kunT(x, y, txt == null ? '' : String(txt), Math.round((size || 14) * MODEL.textScale * 10) / 10, color || INK, weight == null ? 500 : weight, anchor || 'start');
  }
  function P(x, y, txt, chars, size, lineH, color, maxLines) {
    const sc = MODEL.textScale, lh = Math.round((lineH || 20) * MODEL.lineScale * 10) / 10;
    return kunPara(x, y, txt == null ? '' : String(txt), chars, Math.round((size || 14) * sc * 10) / 10, lh, color || INK, maxLines || 4);
  }
  function num(v, d) { return (v == null || !isFinite(+v)) ? '—' : kunNum(v, d == null ? 2 : d); }
  function ne(v) { return neNum(v == null ? '—' : v); }
  function sign(n) { return kunSignByNum(n); }
  function pName(n) { return KUN_NE[n] || n || '—'; }
  function dt(iso) { return /^\d{4}-\d{2}-\d{2}/.test(String(iso || '')) ? kunDateNe(iso) : '—'; }
  function bsText(s) {
    if (!s) return '—';
    if (/^\d{4}-\d{2}-\d{2}/.test(String(s))) return dt(s);
    return kunBsShort(s);
  }
  /* Prefer the backend's BS value when it exists (format: BS YYYY-MM-DD);
     only convert from AD when the BS field is unavailable. */
  function bsOf(bs, ad) {
    if (bs) return kunBsShort(bs);
    return ad ? dt(ad) : '—';
  }
  function range(a, b) { return bsText(a) + ' – ' + bsText(b); }
  function houseName(h) { return KUN_HOUSE_NE[h] || '—'; }
  function dignity(p) { return kunStateText(p) || '—'; }
  function short(txt, n) { return kunFit(txt == null ? '—' : txt, n || 46); }

  function header(no, title, sub) {
    /* Every model gets its own title composition. The heading is never
       truncated: the font size is derived from the real title width. */
    const m = MODEL.key;
    let s = '', box = [L - 6, 88, W + 12, 90], st = null;
    if (m === 'nebula') {
      const fs = fitTitle(title, 552, 33);
      s += T(360, 104, '✦  नेबुला ज्योतिष  ✦', 13, MODEL.colors.dim, 600, 'middle');
      s += T(360, 146, title, fs, GOLD, 700, 'middle');
      s += '<line x1="58" y1="166" x2="300" y2="166" stroke="' + GOLD2 + '" stroke-opacity=".40" stroke-width="1.2"/>';
      s += '<line x1="420" y1="166" x2="662" y2="166" stroke="' + GOLD2 + '" stroke-opacity=".40" stroke-width="1.2"/>';
      s += '<rect x="354" y="161" width="12" height="10" rx="2" transform="rotate(45 360 166)" fill="' + GOLD + '" opacity=".7"/>';
      box = [L - 6, 84, W + 12, 94];
      st = { x: 360, y: 146, size: fs, color: GOLD, weight: 700, single: true, anchor: 'middle' };
    } else if (m === 'vedic') {
      const fs = fitTitle(title, 492, 31);
      s += '<rect x="58" y="94" width="604" height="78" rx="7" fill="' + MODEL.colors.panel + '" stroke="' + GOLD2 + '" stroke-opacity=".62" stroke-width="1.6"/>';
      s += '<rect x="65" y="101" width="590" height="64" rx="4" fill="none" stroke="' + GOLD2 + '" stroke-opacity=".30" stroke-width="1"/>';
      s += T(76, 137, '॥', 17, GOLD2, 700);
      s += T(644, 137, '॥', 17, GOLD2, 700, 'end');
      s += T(360, 143, title, fs, GOLD, 700, 'middle');
      s += '<circle cx="360" cy="181" r="3" fill="' + GOLD2 + '"/><circle cx="348" cy="181" r="2" fill="' + GOLD2 + '" opacity=".6"/><circle cx="372" cy="181" r="2" fill="' + GOLD2 + '" opacity=".6"/>';
      box = [L - 6, 88, W + 12, 98];
      st = { x: 360, y: 143, size: fs, color: GOLD, weight: 700, single: true, anchor: 'middle' };
    } else if (m === 'orbit') {
      const fs = fitTitle(title, 486, 32);
      s += '<path d="M58 100h24M58 100v54" fill="none" stroke="' + GOLD + '" stroke-width="2.4" stroke-linecap="round"/>';
      s += '<path d="M662 100h-24M662 100v54" fill="none" stroke="' + GOLD + '" stroke-width="2.4" stroke-linecap="round" opacity=".55"/>';
      s += T(78, 114, '◈  अटो मोड्युल ' + ne(no), 12.5, MODEL.colors.dim, 700);
      s += T(78, 153, title, fs, GOLD, 700);
      s += '<line x1="58" y1="170" x2="662" y2="170" stroke="' + GOLD + '" stroke-opacity=".22" stroke-width="1.2"/>';
      s += '<rect x="58" y="178" width="46" height="3" rx="1.5" fill="' + MODEL.colors.accent2 + '"/>';
      s += '<rect x="110" y="178" width="8" height="3" rx="1.5" fill="' + GOLD + '" opacity=".6"/>';
      box = [L - 6, 88, W + 12, 98];
      st = { x: 78, y: 153, size: fs, color: GOLD, weight: 700, single: true };
    } else {
      const n = String(title || '').length;
      const fs = n <= 24 ? 34 : n <= 29 ? 30 : n <= 34 ? 27 : n <= 40 ? 23 : 20;
      s += '<rect x="' + L + '" y="96" width="54" height="4" rx="2" fill="' + GOLD2 + '"/>';
      s += '<circle cx="636" cy="99" r="3.2" fill="' + GOLD + '" opacity=".65"/>';
      s += '<circle cx="650" cy="99" r="1.8" fill="' + GOLD + '" opacity=".35"/>';
      s += T(L, 138, title, fs, GOLD, 700);
      s += '<line x1="' + L + '" y1="168" x2="' + R + '" y2="168" stroke="' + GOLD2 + '" stroke-opacity=".30" stroke-width="1.4"/>';
      st = { x: L, y: 138, size: fs, color: GOLD, weight: 700, single: true };
    }
    return el(no, title, 'heading', 'शीर्षक — ' + title, box, s, 5.4, { editable: true, textStyle: st, defaultText: title });
  }
  function pz(el, id, label, x, y, w, h) {
    /* Privacy rectangle in the element's own SVG coordinate space. Design
       coordinates are shifted by TOP_SAFE just like the element itself. */
    (el.privacy || (el.privacy = [])).push({ id: id, label: label, rects: [{ x: x, y: y + TOP_SAFE, w: w, h: h }] });
    return el;
  }
  function balanceAutoCard(els) {
    /* Anchor the masthead (title + its caption/section stack) to the designed
       top edge and rebalance only the body below it. The old version moved
       every element as one block; on sparse cards that pushed the header into
       the middle of the card and left a dead band above it. */
    if (!els || !els.length) return 0;
    if (els.some(e => e && e.scroll)) return 0;
    const cardTop = CARD[1], cardBottom = CARD[1] + CARD[3] - 64;

    const headTypes = { heading: 1, caption: 1 };
    let hi = 0;
    while (hi < els.length) {
      const e = els[hi];
      if (!e || !e.bbox || !headTypes[e.type]) break;
      if (e.bbox[1] > cardTop + 260) break;
      hi++;
    }
    if (hi && !els.slice(0, hi).some(e => e.type === 'heading')) hi = 0;
    const head = els.slice(0, hi), body = els.slice(hi);
    if (!body.length) return 0;

    let headBottom = cardTop;
    head.forEach(e => { if (e && e.bbox) headBottom = Math.max(headBottom, e.bbox[1] + e.bbox[3]); });

    /* Group body elements into vertical bands. Layered components (the art
       halo behind a chart) stay locked together as one band. */
    const bands = [];
    body.forEach(e => {
      if (!e || !e.bbox) return;
      const top = e.bbox[1], bot = top + e.bbox[3];
      const hit = bands.find(b => top < b.bot - 1 && bot > b.top + 1);
      if (hit) { hit.top = Math.min(hit.top, top); hit.bot = Math.max(hit.bot, bot); hit.els.push(e); }
      else bands.push({ top: top, bot: bot, els: [e] });
    });
    if (!bands.length) return 0;
    bands.sort((a, b) => a.top - b.top);
    for (let i = 1; i < bands.length; i++) {
      if (bands[i].top < bands[i - 1].bot - 1) {
        bands[i - 1].bot = Math.max(bands[i - 1].bot, bands[i].bot);
        bands[i - 1].els = bands[i - 1].els.concat(bands[i].els);
        bands.splice(i, 1); i--;
      }
    }

    const span = bands[bands.length - 1].bot - bands[0].top;
    const bodyTop = headBottom > cardTop ? headBottom + 18 : cardTop + 18;
    const available = cardBottom - bodyTop;
    const top = span <= available ? bodyTop : Math.max(headBottom, cardBottom - span);
    /* Sparse pages gain breathing room between their body bands instead of a
       single empty band at the bottom. Dense pages keep their designed rhythm
       and are only nudged back above the caption-safe floor. */
    const gapAdd = (bands.length > 1 && span < available) ? Math.min(120, (available - span) / (bands.length - 1)) : 0;

    let cursor = top, prevBot = null;
    bands.forEach((b, bi) => {
      if (prevBot != null) cursor += (b.top - prevBot) + gapAdd;
      const dy = Math.round(cursor - b.top);
      b.dy = dy;
      b.els.forEach(e => {
        e.bbox[1] += dy;
        if (e.textStyle) e.textStyle.y += dy;
        if (e.privacy) (e.privacy || []).forEach(g => (g.rects || []).forEach(r => { r.y += dy; }));
        e.inner = '<g transform="translate(0,' + dy + ')">' + e.inner + '</g>';
      });
      prevBot = b.bot;
      cursor += b.bot - b.top;
    });

    /* Card 14 uses this value to place its tappable WhatsApp hotspot. */
    const banner = body.find(e => e && e.type === 'banner');
    if (banner) {
      const bb = bands.find(b => b.els.indexOf(banner) >= 0);
      if (bb) return bb.dy;
    }
    return bands[0].dy;
  }
  function footer(no, title) {
    /* A footer line on every card would sit inside TikTok's bottom caption
       band. The AUTO layout intentionally omits the footer; card numbers and
       extra top captions were removed as well, leaving only real content. */
    return null;
  }
  function note(no, title, name, box, txt, opts) {
    opts = opts || {};
    const x = box[0] + (opts.pad == null ? 0 : opts.pad), y = box[1] + (opts.head == null ? 27 : opts.head);
    const size = opts.size || 16, lh = opts.lh || 26, chars = opts.chars || Math.max(20, Math.floor(box[2] / (size * .60)));
    /* Use the rendered line height for wrapping, not the unscaled design
       value, and reserve the descender of the last line. */
    const layoutLH = flowLineH(lh);
    const maxLines = opts.lines || Math.max(1, Math.floor((box[3] - (opts.head == null ? 27 : opts.head) - size * .6) / layoutLH) + 1);
    /* A note gets the whole box before it is split. The remainder becomes a
       real continuation page through push(), so no sentence is silently
       replaced by an ellipsis. */
    const fit = splitTextFit(txt, chars, maxLines);
    const inner = P(x, y, fit.head, chars, size, lh, opts.color || MUT, maxLines);
    const o = el(no, title, 'note', name, box, inner, opts.dur || 6.4, { editable: true, textStyle: { x: x, y: y, size: size, color: opts.color || MUT, chars: chars, lineH: lh, max: opts.max || 64 }, defaultText: fit.head });
    if (fit.split) o.flowOverflow = { text: fit.tail, chars: chars, size: size, lh: lh, maxLines: maxLines, color: opts.color || MUT, head: opts.head == null ? 27 : opts.head, box: box.slice(), name: name };
    return o;
  }
  function card(no, title, name, x, y, w, h, label, value, accent, opts) {
    opts = Object.assign({ lfs: 14, lh: 27 }, opts || {});
    return el(no, title, 'cards', name, [x, y, w, h], kunCard(x, y, w, h, label, value, accent, opts), 6.6);
  }
  /* Dasha cards stack the lord and both BS dates on their own lines, so a
     long end date can never be pushed out of the visible card. */
  function dashaBox(no, title, name, x, y, w, h, label, main, start, end, accent) {
    const col = accent || GOLD2;
    let s = '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="15" fill="#0d1830" stroke="#223052" stroke-width="1.5"/>';
    s += '<rect x="' + x + '" y="' + y + '" width="5" height="' + h + '" rx="2.5" fill="' + col + '"/>';
    s += T(x + 20, y + 30, label, 14, MUT, 600);
    s += T(x + 20, y + 66, short(main, 24), 21, col, 700);
    s += '<line x1="' + (x + 18) + '" y1="' + (y + 84) + '" x2="' + (x + w - 18) + '" y2="' + (y + 84) + '" stroke="#223052"/>';
    s += T(x + 20, y + 108, 'सुरु', 13, DIM, 600);
    s += T(x + 66, y + 108, bsText(start), 15, INK, 600);
    s += T(x + 20, y + 142, 'अन्त्य', 13, DIM, 600);
    s += T(x + 66, y + 142, bsText(end), 15, INK, 600);
    return el(no, title, 'cards', name, [x, y, w, h], s, 6.6);
  }
  function table(no, title, name, x, y, w, cols, rows, opts, dur) {
    opts = opts || {};
    const rowH = opts.rowH || 58, headH = opts.headH || 50;
    const e = el(no, title, 'table', name, [x, y, w, headH + rows.length * rowH], kunTable(x, y, w, cols, rows, opts), dur || 8);
    e.readRows = rows.length;
    return e;
  }
  function chart(no, title, name, houses, lagna, x, y, size, opts) {
    return el(no, title, 'chart', name, [x, y, size, size], kunChart(houses, lagna, x, y, size, opts), 8.6);
  }
  function graphEl(no, title, name, box, inner, dur) {
    return el(no, title, 'graph', name, box, inner, dur || 8.2);
  }
  function artEl(no, title, name, box, inner, dur) {
    return el(no, title, 'art', name, box, inner, dur || 7.4);
  }

  /* ── reading-time engine v2 ──────────────────────────────────────
     Words per second drive the reading estimate; a chart has its own
     4–6s visual scan cost, a table row 1.2–1.5s. The final duration is
     the larger of that estimate and the real entrance timeline plus a
     1.5s settle window, so no text is still moving when a transition
     begins. Generated cards are clamped to 7–28s; the Janmapatrika
     document keeps its own 30–35s scroll window and grows beyond 35s
     when a slower model or a longer scroll needs more time. */
  function elText(e) {
    if (!e) return '';
    let txt = e.defaultText || '';
    if (!txt) {
      const hits = String(e.inner || '').match(/<text[^>]*>[\s\S]*?<\/text>/g) || [];
      txt = hits.map(x => x.replace(/<[^>]*>/g, ' ')).join(' ');
    }
    return String(txt).replace(/&[a-z#0-9]+;/gi, ' ').replace(/\s+/g, ' ').trim();
  }
  function elChars(e) { return elText(e).length; }
  function elWords(e) {
    const words = elText(e).match(/[\u0900-\u097F]+|[A-Za-z]+|[0-9]+(?:[.,][0-9]+)?/g);
    return words ? words.length : 0;
  }
  function readDuration(it, M) {
    if (!it || !it.els) return 8;
    const isDoc = it.els.some(e => e && e.el && e.el.scroll);
    if (isDoc) {
      /* The document has to finish its whole scroll before the next card
         takes over. Keep the established 35s reading window as a floor,
         and extend it whenever the model speed stretches the scroll. */
      const spd = Math.max(.4, Math.min(3, (M && M.set && M.set.speed) || 1));
      const delay = Math.max(0, +(it.scrollDelay != null ? it.scrollDelay : .8));
      const need = delay + Math.max(.5, +(it.scrollDur || 30)) / spd + 1.2;
      return Math.round(Math.max(35, need) * 10) / 10;
    }
    const wps = (M && M.readWps) || 2.9;
    let sec = 1.0;
    it.els.forEach(e => {
      const el = e && e.el; if (!el) return;
      const words = elWords(el), t = el.type, rows = el.readRows || 0;
      switch (t) {
        case 'chart':
          /* Charts are read as a shape, not as their label text. Nine-planet
             D1 charts get the full 5–6s; a small varga chart stays near 4.5s. */
          sec += 4.2 + Math.min(1.4, words / 30);
          break;
        case 'table':
          sec += 1.2 + rows * 1.35;
          break;
        case 'graph':
        case 'list':
          sec += .9 + Math.min(10, words / wps);
          break;
        case 'cards':
          sec += .4 + Math.min(4.2, words / wps);
          break;
        case 'report':
        case 'note':
          sec += .5 + Math.min(9, words / wps);
          break;
        case 'art':
        case 'banner':
          sec += .9 + Math.min(1.2, words / (wps * 5));
          break;
        case 'heading':
        case 'caption':
          sec += .2 + words / (wps * 5);
          break;
        default:
          sec += .3 + words / wps;
      }
    });
    sec *= (M && M.durScale) || 1;
    /* The entrance timeline is part of the duration. settle keeps the last
       line still for at least 1.5s before the model transition takes over. */
    const animEnd = it.els.reduce((m, e) => Math.max(m, e && e.anim ? (+e.anim.delay || 0) + (+e.anim.dur || 0) : 0), 0);
    const settle = 1.5;
    sec = Math.max(sec, animEnd + settle, (M && M.minDur) || 7);
    sec = Math.min((M && M.maxDur) || 28, sec);
    return Math.round(sec * 10) / 10;
  }

  /* Semantic, top-to-bottom entrance order. Header lines lead, the main
     visual follows, supporting cards/tables then notes. Elements sharing a
     horizontal band cascade sideways instead of waiting a full band gap, so
     a 13-box card still finishes entering in about two seconds. */
  function motionPlan(els, M) {
    const list = (els || []).map((e, i) => ({
      i: i, y: +(e.bbox && e.bbox[1]) || 0, x: +(e.bbox && e.bbox[0]) || 0,
      w: +(e.bbox && e.bbox[2]) || 0, h: +(e.bbox && e.bbox[3]) || 0
    })).sort((a, b) => (a.y - b.y) || (a.x - b.x));
    const step = M.seqStep != null ? +M.seqStep : .1;
    const band = M.seqBand != null ? +M.seqBand : .16;
    const maxDelay = M.seqMax != null ? +M.seqMax : 2;
    const map = {};
    let t = .08, prev = null;
    list.forEach(it => {
      if (prev) {
        const overlap = Math.min(prev.y + prev.h, it.y + it.h) - Math.max(prev.y, it.y);
        const sameBand = overlap > Math.min(prev.h, it.h) * .45;
        t += sameBand ? step : band;
      }
      map[it.i] = Math.round(Math.min(maxDelay, t) * 1000) / 1000;
      prev = it;
    });
    return map;
  }
  function animFor(e, i, M, delay) {
    /* A scroll document (Janmapatrika) is a complete paper page, not a
       floating component. Its entry animation used to hide the whole page
       at t=0, which read as an empty dark card. The scroll itself is the
       animation, so the document must be fully visible from frame one. */
    if (e && e.scroll) return { entry: 'none', exit: 'none', delay: 0, dur: M.set.animDur, stagger: 0, kind: 'none' };
    const a = M.anim;
    let entry = a.text;
    const byType = {
      heading: a.heading, caption: a.caption, chart: a.chart, art: a.art, banner: a.art,
      cards: a.cards, table: a.table, graph: a.graph, report: a.report, note: a.note
    };
    if (byType[e.type]) entry = byType[e.type];
    /* Orbit HUD panels converge from both edges instead of every box
       sliding from the same side. */
    if (entry === 'slide' && +(e.bbox && e.bbox[0]) > 340) entry = 'slide-r';
    const kind = (a.kind && a.kind !== 'none' && (e.type === 'art' || e.type === 'chart' || e.type === 'graph')) ? a.kind : 'none';
    return {
      entry: entry, exit: 'none',
      delay: delay != null ? +delay : Math.min(1.6, i * a.delay),
      dur: M.set.animDur, stagger: 0, kind: kind
    };
  }

  /* ── real data helpers ─────────────────────────────────────────── */

  function findPlanet(data, name) { return (data.planets || []).find(p => p.name === name) || {}; }
  function lagnaSignOf(data) { return +((data.lagna || {}).sign_number) || 1; }

  function activeVim(data) {
    const rep = ((data.dasha_reports || {}).vimshottari || {}).active_path;
    if (rep && rep.length) return rep.map(x => ({
      lord: x.lord, lordNe: x.lord_nepali || pName(x.lord), level: x.level || 0,
      start: x.start, end: x.end, startBs: x.start_bs, endBs: x.end_bs
    }));
    const out = [];
    const walk = (arr, lv) => (arr || []).forEach(n => {
      if (n.is_active) {
        out.push({ lord: n.lord, lordNe: n.lord_nepali || pName(n.lord), level: lv, start: n.start, end: n.end, startBs: n.start_bs, endBs: n.end_bs });
        if (n.children) walk(n.children, lv + 1);
      }
    });
    walk(data.dasha, 0);
    return out;
  }
  function activeYogini(data) {
    const rep = ((data.dasha_reports || {}).yogini || {}).active_path;
    if (rep && rep.length) return rep.map(x => ({
      name: x.yogini || x.lord || '—', nameNe: x.yogini_nepali || x.lord_nepali || x.yogini || x.lord || '—',
      lord: x.planet_lord || x.lord, level: x.level || 0,
      start: x.start, end: x.end, startBs: x.start_bs, endBs: x.end_bs
    }));
    const today = new Date().toISOString().slice(0, 10);
    const out = [];
    (data.yogini_dasha || []).forEach(md => {
      if (String(md.start) <= today && String(md.end) > today) {
        out.push({ name: md.name, nameNe: md.nepali, lord: md.lord, level: 1, start: md.start, end: md.end, startBs: md.start_bs, endBs: md.end_bs });
        (md.antardashas || []).forEach(ad => {
          if (String(ad.start) <= today && String(ad.end) > today) out.push({ name: ad.name, nameNe: ad.nepali, lord: ad.lord || md.lord, level: 2, start: ad.start, end: ad.end, startBs: ad.start_bs, endBs: ad.end_bs });
        });
      }
    });
    return out;
  }
  function lordEffect(data, lord) {
    const p = findPlanet(data, lord) || {};
    const h = +p.house || 0;
    const hn = houseName(h);
    const dg = dignity(p);
    const rel = p.relationship === 'karaka' ? 'कारक' : p.relationship === 'maraka' ? 'मारक' : p.relationship === 'sama' ? 'सम' : '';
    return (p.sign_number ? sign(p.sign_number) + ' राशि · ' + ne(h) + ' भाव (' + hn + ')' : 'ग्रह स्थिति उपलब्ध छैन') +
      (dg && dg !== '—' ? ' · ' + dg : '') + (rel ? ' · ' + rel : '');
  }
  function yogaRows(list, good) {
    const out = [];
    (list || []).forEach(y => {
      const sev = String(y.severity || '').toLowerCase();
      const cat = String(y.category || '').toLowerCase();
      const isBad = /inauspicious|malefic|bad|dosha|arishta/.test(sev) || /dosha|arishta/.test(cat);
      if (good ? !isBad : isBad) out.push(y);
    });
    if (good) out.sort((a, b) => (/highly/.test(b.severity || '') ? 1 : 0) - (/highly/.test(a.severity || '') ? 1 : 0));
    return out;
  }

  function yogaListInner(items, x, y0, w, rowH, good, startNo) {
    let s = '';
    items.forEach((yg, i) => {
      const ry = y0 + i * rowH;
      const accent = good ? (i % 2 ? '#22c55e' : GOLD2) : BAD;
      const boxH = rowH - 10;
      const maxLines = Math.max(1, Math.min(4, Math.floor((boxH - 40) / 22)));
      const contentH = 36 + maxLines * 22;
      const top = Math.max(8, Math.round((boxH - contentH) / 2));
      const nameY = ry + top + 18;
      const descY = ry + top + 46;
      s += '<rect x="' + x + '" y="' + ry + '" width="' + w + '" height="' + boxH + '" rx="12" fill="#0d1830" stroke="' + accent + '" stroke-opacity=".34" stroke-width="1.2"/>';
      s += '<rect x="' + x + '" y="' + (ry + 10) + '" width="4" height="' + (boxH - 20) + '" rx="2" fill="' + accent + '"/>';
      s += T(x + 20, nameY, ne(startNo + i) + '. ' + (yg.nepali || yg.name || 'योग'), 19, good ? GOLD : '#ffb4bd', 700);
      s += T(x + w - 18, nameY - 2, String(yg.category || 'yoga').toUpperCase(), 12.5, DIM, 600, 'end');
      s += P(x + 20, descY, yg.result_ne || yg.result || yg.cause_ne || '—', Math.max(24, Math.floor((w - 40) / 8.2)), 14.5, 22, MUT, maxLines);
    });
    return s;
  }

  /* Compact full list used when every real yoga must fit on one card.
     Row height is supplied by the caller so a long list can never run past
     the card edge; the name and description stay centred in each row. */
  function yogaCompactInner(items, x, y0, w, rowH, startNo) {
    let s = '';
    const nameY = Math.min(20, Math.max(14, rowH * .42));
    const descY = Math.min(36, rowH - 8);
    items.forEach((yg, i) => {
      const ry = y0 + i * rowH;
      s += '<rect x="' + x + '" y="' + ry + '" width="' + w + '" height="' + (rowH - 5) + '" rx="9" fill="' + (i % 2 ? '#101d36' : '#0d1830') + '" stroke="#223052" stroke-width="1"/>';
      s += '<rect x="' + x + '" y="' + (ry + 7) + '" width="3" height="' + (rowH - 18) + '" rx="1.5" fill="' + (i % 2 ? GOOD : GOLD2) + '"/>';
      s += T(x + 14, ry + nameY, ne(startNo + i) + '. ' + (yg.nepali || yg.name || 'योग'), 14, GOLD, 700);
      s += T(x + w - 12, ry + nameY, String(yg.category || 'yoga').toUpperCase(), 9.5, DIM, 600, 'end');
      s += T(x + 14, ry + descY, short(yg.result_ne || yg.result || yg.cause_ne || '—', 84), 11.5, MUT, 500);
    });
    return s;
  }

  /* ── intelligent overflow engine ─────────────────────────────────
     Every text block is measured with the same character wrapper that
     paints it. If a block does not fit, the page is allowed to grow to its
     real safe limit first; only then is the text split. Splits happen at
     sentence boundaries (Nepali danda, question/exclamation marks and
     sentence-ending periods). A single sentence larger than one full card
     is the only case that falls back to a word boundary, so no sentence is
     ever cut just because a page happened to end. */
  function flowWrap(txt, chars) {
    return kunWrap(String(txt == null ? '' : txt).replace(/\s+/g, ' ').trim(), Math.max(8, Math.floor(chars || 40)));
  }
  function flowSentences(txt) {
    const s = String(txt == null ? '' : txt).replace(/\r/g, '').replace(/[ \t]+/g, ' ').trim();
    if (!s) return [];
    const out = [];
    let buf = '';
    for (let i = 0; i < s.length; i++) {
      const c = s[i];
      buf += c;
      const end = c === '।' || c === '!' || c === '?' ||
        (c === '.' && (i + 1 >= s.length || /\s/.test(s[i + 1])) && !/[0-9]/.test(s[i - 1] || ''));
      if (end) { const t = buf.trim(); if (t) out.push(t); buf = ''; }
      else if (c === '\n') { const t = buf.trim(); if (t) out.push(t); buf = ''; }
    }
    if (buf.trim()) out.push(buf.trim());
    return out.length ? out : [s];
  }
  function splitTextFit(txt, chars, maxLines) {
    /* Returns { head, tail, lines, split, sentenceSplit }. `head` is the
       exact text that fits, `tail` is the untouched remainder. */
    const full = String(txt == null ? '' : txt).replace(/\s+/g, ' ').trim();
    const limit = Math.max(1, Math.floor(maxLines || 1));
    if (!full) return { head: '', tail: '', lines: 0, split: false, sentenceSplit: false };
    const all = flowWrap(full, chars);
    if (all.length <= limit) return { head: full, tail: '', lines: all.length, split: false, sentenceSplit: false };
    const sentences = flowSentences(full);
    let head = '', used = 0;
    for (let i = 0; i < sentences.length; i++) {
      const cand = head ? head + ' ' + sentences[i] : sentences[i];
      if (flowWrap(cand, chars).length <= limit) { head = cand; used = i + 1; }
      else break;
    }
    if (head) {
      return { head: head, tail: sentences.slice(used).join(' ').trim(), lines: flowWrap(head, chars).length, split: true, sentenceSplit: true };
    }
    /* One sentence is taller than a whole card: keep whole words, never
       cut inside a word. */
    const words = full.split(' ');
    let wordHead = '', wi = 0;
    for (; wi < words.length; wi++) {
      const cand = wordHead ? wordHead + ' ' + words[wi] : words[wi];
      if (flowWrap(cand, chars).length > limit) break;
      wordHead = cand;
    }
    if (!wordHead) {
      const hard = Math.max(8, Math.floor(chars || 40) * limit);
      wordHead = full.slice(0, hard).trim();
      return { head: wordHead, tail: full.slice(wordHead.length).trim(), lines: flowWrap(wordHead, chars).length, split: true, sentenceSplit: false };
    }
    return { head: wordHead, tail: words.slice(wi).join(' ').trim(), lines: flowWrap(wordHead, chars).length, split: true, sentenceSplit: false };
  }
  function fitFlowSize(txt, maxW, maxSize, minSize) {
    const n = String(txt == null ? '' : txt).length || 1;
    let fs = maxSize;
    while (fs > minSize && n * fs * .54 > maxW) fs -= .5;
    return Math.round(fs * 2) / 2;
  }
  function flowPageTitle(base, page, total) {
    return total > 1 ? base + ' (' + ne(page) + '/' + ne(total) + ')' : base;
  }
  /* The renderer multiplies every paragraph line height by the model's
     lineScale (P() -> kunPara). Layout math must use that same rounded value,
     otherwise a full page overflows only in nebula/vedic/orbit. */
  function flowLineH(base) {
    return Math.round((base || 20) * MODEL.lineScale * 10) / 10;
  }
  /* Pack measured rows into real pages. The caller supplies the usable top
     and bottom of the first and follow-up pages. A row that is too tall for
     the remaining space is split; its remainder becomes a continuation row
     on the next page with the same entry number and title. */
  function paginateFlowRows(entries, cfg) {
    const pages = [];
    let page = [], first = true;
    let y = cfg.firstTop;
    const top = () => first ? cfg.firstTop : cfg.nextTop;
    const bottom = () => first ? cfg.firstBottom : cfg.nextBottom;
    const flush = () => {
      if (!page.length) return;
      pages.push(page); page = []; first = false; y = cfg.nextTop;
    };
    (entries || []).forEach(src => {
      let body = String(src.body == null ? '' : src.body);
      let cont = false, guard = 0;
      while (guard++ < 4000) {
        const headH = cfg.headerHeight(src, cont);
        /* Before splitting a row, try it whole on a fresh page. Splitting
           only because the current page happened to be nearly full would
           create needless one-line continuation cards. */
        if (!cont && page.length) {
          const fullLines = flowWrap(body, cfg.bodyChars).length;
          const fullH = headH + cfg.padTop + cfg.padBottom + fullLines * cfg.bodyLH;
          if (y + fullH > bottom()) { flush(); continue; }
        }
        const room = bottom() - y - headH - cfg.padTop - cfg.padBottom;
        const maxLines = Math.max(1, Math.floor(room / cfg.bodyLH));
        const fit = splitTextFit(body, cfg.bodyChars, maxLines);
        const h = headH + cfg.padTop + cfg.padBottom + fit.lines * cfg.bodyLH;
        if (y + h > bottom() && page.length) { flush(); continue; }
        page.push({ src: src, body: fit.head, cont: cont, h: h, lines: fit.lines, split: fit.split });
        y += h + cfg.rowGap;
        if (!fit.split) break;
        body = fit.tail;
        cont = true;
        flush();
      }
    });
    if (page.length) pages.push(page);
    return pages;
  }

  function yogaFlowRow(row, x, y, w, good) {
    const src = row.src, h = row.h;
    const accent = src.accent || (good ? (src.no % 2 ? '#22c55e' : GOLD2) : BAD);
    const nameLabel = ne(src.no) + '. ' + (src.name || 'योग');
    const nameFs = fitFlowSize(nameLabel, w - 150, 19, 14.5);
    const cat = String(src.category || 'yoga').toUpperCase() + (row.cont ? ' · क्रमशः' : '');
    const catFs = fitFlowSize(cat, 170, 12.5, 11);
    let s = '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="12" fill="#0d1830" stroke="' + accent + '" stroke-opacity=".34" stroke-width="1.2"/>';
    s += '<rect x="' + x + '" y="' + (y + 9) + '" width="4" height="' + Math.max(10, h - 18) + '" rx="2" fill="' + accent + '"/>';
    s += T(x + 20, y + 28, nameLabel, nameFs, good ? GOLD : MODEL.colors.badText, 700);
    s += T(x + w - 18, y + 27, cat, catFs, DIM, 600, 'end');
    if (row.lines > 0) s += P(x + 20, y + 50, row.body, Math.max(24, Math.floor((w - 40) / 8.2)), 14.5, 22, MUT, row.lines);
    return s;
  }
  function lalFlowRow(row, x, y, w) {
    const src = row.src, h = row.h, good = src.good !== false;
    const col = good ? GOOD : BAD;
    const name = pName(src.name);
    const status = String(src.status || (good ? 'शुभ' : 'अशुभ')) + (row.cont ? ' · क्रमशः' : '');
    let s = '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="14" fill="' + (good ? '#0d1830' : '#1a0d16') + '" stroke="' + col + '" stroke-opacity=".42" stroke-width="1.3"/>';
    s += '<rect x="' + x + '" y="' + (y + 10) + '" width="4" height="' + Math.max(10, h - 20) + '" rx="2" fill="' + col + '"/>';
    s += T(x + 22, y + 32, name, 20, good ? GOLD : MODEL.colors.badText, 700);
    s += T(x + 22, y + 54, status, 13.5, col, 700);
    s += '<circle cx="' + (x + w - 28) + '" cy="' + (y + 32) + '" r="7" fill="' + col + '" opacity=".75"/>';
    if (row.lines > 0) s += P(x + 22, y + 74, row.body, Math.max(24, Math.floor((w - 44) / 8.2)), 14, 20, MUT, row.lines);
    return s;
  }

  /* ── Sade Sati ─────────────────────────────────────────────────── */

  function sadeSati(data, transit) {
    const moon = findPlanet(data, 'Moon') || {};
    const ms = +moon.sign_number || 0;
    const cur = transit && transit.current;
    if (!cur || !cur.sign) return { known: false, text: 'गोचर डेटा उपलब्ध भएन — शनिको वर्तमान राशि पाइएन।', phase: '—', moonSign: ms };
    const ss = +cur.sign;
    const diff = ((ss - ms) % 12 + 12) % 12;
    let phase = 'सक्रिय छैन';
    let detail = 'चन्द्र राशिबाट शनि १२औं, १औं वा २औं भावमा छैन, त्यसैले साढे साती सक्रिय छैन।';
    if (diff === 11) { phase = 'साढे साती — प्रथम चरण'; detail = 'शनि चन्द्र राशिबाट १२औं भावमा — साढे सातीको सुरुवाती चरण।'; }
    else if (diff === 0) { phase = 'साढे साती — मध्य चरण'; detail = 'शनि चन्द्र राशिमा — साढे सातीको सबैभन्दा प्रभावशाली चरण।'; }
    else if (diff === 1) { phase = 'साढे साती — अन्तिम चरण'; detail = 'शनि चन्द्र राशिबाट २औं भावमा — साढे सातीको अन्तिम चरण।'; }
    return {
      known: true, phase: phase, text: detail, moonSign: ms, saturnSign: ss,
      start: cur.start, end: cur.end
    };
  }

  /* ── builders ──────────────────────────────────────────────────── */

  function build(data, meta, opts) {
    SEQ = 0;
    opts = opts || {};
    MODEL = modelByKey(opts.model || 'cosmic');
    ALIAS = aliasMap(MODEL.colors);
    const transit = opts.transit || null;
    const items = [];
    const planets = data.planets || [];
    const lagna = data.lagna || {};
    const ls = lagnaSignOf(data);
    const moon = findPlanet(data, 'Moon');
    const sun = findPlanet(data, 'Sun');
    const pc = data.panchang || {};
    const av = data.avakahada_chakra || {};
    const dashas = activeVim(data);
    const yoginis = activeYogini(data);
    const sav = (data.ashtakavarga || {}).sav || [];
    const K = data.kaal_sarp_dosha || {};
    const name = meta.name || (data.metadata || {}).name || 'जातक';
    const place = (meta.city || meta.birth_place || (data.metadata || {}).city || '—') + (meta.country ? ', ' + meta.country : '');
    const dateBs = dt(meta.birth_date || (data.metadata || {}).birth_date);
    const timeNe = kunTime(meta.birth_time || (data.metadata || {}).birth_time);
    const dateLine = dateBs + ' · ' + timeNe;

    const push = (no, title, shortTitle, rawEls, extra) => {
      const els = (rawEls || []).filter(Boolean);
      const autoShift = balanceAutoCard(els);
      const seq = motionPlan(els, MODEL);
      const main = els.find(e => e.type === 'heading') || els[0];
      const it = {
        uid: 'kauto' + no + '_' + items.length + '_' + Date.now().toString(36),
        autoKey: (extra && extra.key) || ('card-' + String(no).padStart(2, '0')),
        autoNo: no,
        order: extra && extra.priority != null ? extra.priority : no * 10,
        seq: items.length,
        title: title,
        el: main,
        els: els.map((e, i) => ({
          id: e.id, key: e.id, el: e, box: e.bbox.slice(), z: i + 1, visible: true,
          scroll: !!e.scroll, anim: animFor(e, i, MODEL, seq[i]),
          group: '', locked: false
        })),
        mode: 'auto',
        cardBox: CARD.slice(),
        chrome: false,
        autoShift: autoShift,
        dur: 8.2,
        gap: extra && extra.gap != null ? extra.gap : ((MODEL.set && MODEL.set.gap != null) ? MODEL.set.gap : .55),
        tpl: (extra && extra.tpl) || MODEL.tpl,
        modelKey: MODEL.key,
        modelName: MODEL.ne,
        privacyStyle: (extra && extra.privacyStyle) || '',
        flow: (extra && extra.flow) || null,
        set: null
      };
      items.push(it);
      /* Any note that did not fit is turned into real continuation cards.
         This is deliberately downstream of push(), so every appended card
         receives the same model theme, animation, duration and Timeline
         editability as a hand-authored card. */
      const over = els.filter(e => e && e.flowOverflow);
      if (over.length) {
        const baseKey = it.autoKey, baseOrder = it.order;
        const chunks = [];
        over.forEach(el => {
          const src = el.flowOverflow;
          let tail = src.text, guard = 0;
          const contLH = flowLineH(src.lh);
          const contMax = Math.max(1, Math.floor((842 - 27 - src.size * .6) / contLH) + 1);
          while (tail && guard++ < 500) {
            const fit = splitTextFit(tail, src.chars, contMax);
            chunks.push({ src: src, fit: fit });
            if (!fit.split) break;
            tail = fit.tail;
          }
          delete el.flowOverflow;
        });
        chunks.forEach((ch, ci) => {
          const total = chunks.length + 1;
          const contTitle = title + ' · क्रमशः (' + ne(ci + 2) + '/' + ne(total) + ')';
          const noteName = (ch.src.name || 'नोट') + ' (क्रमशः)';
          const nEl = note(no, contTitle, noteName, [L, 206, W, 842], ch.fit.head, {
            size: ch.src.size, lh: ch.src.lh, chars: ch.src.chars,
            lines: Math.max(1, ch.fit.lines), color: ch.src.color
          });
          /* Keep the whole note chain inside the parent's own priority band.
             A paginated parent's next page starts at +0.5, so spreading the
             chain over +0.01..+0.41 guarantees every continuation appears
             immediately after the parent and before the next page/card. */
          const step = chunks.length > 1 ? (ci / (chunks.length - 1)) * 0.4 : 0.2;
          push(no, contTitle, shortTitle + ' · क्रमशः', [
            header(no, contTitle, 'क्रमशः'),
            nEl
          ], {
            priority: baseOrder + 0.01 + step, key: baseKey + '-flow-' + (ci + 2),
            flow: { kind: 'noteOverflow', page: ci + 2, pages: total, parent: baseKey, textChars: ch.fit.head.length }
          });
        });
        /* Do not overwrite a paginated parent's own flow ledger. The note
           chain lives beside it, so both the yoga/Lal rows and the note
           pages remain auditable. */
        const noteFlow = { pages: chunks.length + 1, continuationPages: chunks.length };
        if (it.flow) it.flow.noteOverflow = noteFlow;
        else it.flow = Object.assign({ kind: 'noteOverflowParent' }, noteFlow);
      }
    };

    /* 01 — name, BS date/time/place, heading, then D1 at the bottom */
    {
      const no = 1, title = 'जन्म कुण्डली';
      const houses = kunHouses(planets, ls, 'd1');
      const chipW = 190, gap = 17, x0 = L + (W - (chipW * 3 + gap * 2)) / 2;
      const chip = (i, label, value, accent) => card(no, title, label, x0 + i * (chipW + gap), 878, chipW, 116, label, value, accent, { fs: 20, chars: 11, lh: 27, lfs: 13, vtop: 62, lines: 2 });
      /* Fit the name inside the fixed privacy rect, not just inside the card.
         A long name must never extend past the blurred band. */
      const nameFs = fitFlowSize(name, 452, 40, 12.5);
      const nameEl = pz(el(no, title, 'heading', 'जातकको नाम', [L, 100, W, 80], T(360, 150, name, nameFs, GOLD, 700, 'middle'), 5.8, { editable: true, textStyle: { x: 360, y: 150, size: nameFs, color: GOLD, weight: 700, single: true, anchor: 'middle' }, defaultText: name }), 'name', 'जातकको नाम (मुख्य शीर्षक)', 122, 108, 476, 70);
      const coords = 'अक्षांश ' + num(meta.latitude, 4) + '°  ·  देशान्तर ' + num(meta.longitude, 4) + '°';
      push(no, title, 'जन्म परिचय', [
        el(no, title, 'caption', 'शीर्षक रेखा', [L, 84, W, 22],
          '<rect x="334" y="92" width="52" height="4" rx="2" fill="' + GOLD2 + '"/>', 5.2, { editable: false }),
        nameEl,
        el(no, title, 'caption', 'जन्म मिति र समय', [L, 171, W, 36], T(360, 192, dateLine, 18, INK, 600, 'middle'), 5.4, { editable: true, textStyle: { x: 360, y: 192, size: 18, color: INK, weight: 600, single: true, anchor: 'middle' }, defaultText: dateLine }),
        el(no, title, 'caption', 'जन्म स्थान', [L, 210, W, 30], T(360, 228, place, 14.5, MUT, 500, 'middle'), 5.4, { editable: true, textStyle: { x: 360, y: 228, size: 14.5, color: MUT, weight: 500, single: true, anchor: 'middle' }, defaultText: place }),
        el(no, title, 'heading', 'जन्म कुण्डली शीर्षक', [L, 248, W, 58],
          '<line x1="200" y1="277" x2="316" y2="277" stroke="' + GOLD2 + '" stroke-opacity=".5" stroke-width="1.3"/>' +
          '<line x1="404" y1="277" x2="520" y2="277" stroke="' + GOLD2 + '" stroke-opacity=".5" stroke-width="1.3"/>' +
          T(360, 281, 'जन्म कुण्डली', 30, GOLD, 700, 'middle'), 6, { editable: true, textStyle: { x: 360, y: 281, size: 30, color: GOLD, weight: 700, single: true, anchor: 'middle' }, defaultText: 'जन्म कुण्डली' }),
        artEl(no, title, 'सूर्य-चन्द्र मण्डल', [82, 306, 556, 556], (() => {
          let s = '<circle cx="360" cy="584" r="238" fill="none" stroke="' + GOLD2 + '" stroke-opacity=".18" stroke-width="2"/>';
          for (let i = 0; i < 24; i++) {
            const a = (i * 15 - 90) * Math.PI / 180;
            s += '<circle cx="' + (360 + 238 * Math.cos(a)) + '" cy="' + (584 + 238 * Math.sin(a)) + '" r="' + (i % 6 === 0 ? 4 : 2) + '" fill="' + GOLD + '" opacity="' + (i % 6 === 0 ? .65 : .28) + '"/>';
          }
          s += T(360, 362, 'ॐ', 36, GOLD, 700, 'middle');
          return s;
        })(), 7.4),
        chart(no, title, 'लग्न कुण्डली D1', houses, ls, 82, 310, 556),
        chip(0, 'लग्न राशि', sign(ls) + ' · ' + kunDMS(lagna.longitude_in_sign || 0), GOLD2),
        chip(1, 'चन्द्र राशि', sign(moon.sign_number || 1) + ' · ' + (moon.nakshatra_nepali || '—'), '#6ee7ff'),
        chip(2, 'जन्म नक्षत्र', (moon.nakshatra_nepali || '—') + ' · पद ' + ne(moon.nakshatra_pada || '—'), '#c4b5fd'),
        note(no, title, 'जन्म निर्देशांक', [L, 1000, W, 44], coords, { size: 14.5, lh: 20, lines: 1, color: MUT }),
        footer(no, title)
      ], { priority: ORDER.birth, privacyStyle: 'strong' });
    }

    /* 02 — karaka / maraka / sama (own card for readability) */
    {
      const no = 2, title = 'ग्रह सम्बन्ध';
      const groups = { karaka: [], maraka: [], sama: [] };
      planets.forEach(p => { const k = (p.relationship || '').toLowerCase(); if (groups[k]) groups[k].push(pName(p.name)); });
      const relRows = [
        ['कारक', groups.karaka, GOOD, 'शुभ फल दिने ग्रह'],
        ['मारक', groups.maraka, BAD, 'चुनौती वा हानिसँग जोडिने ग्रह'],
        ['सम', groups.sama, '#60a5fa', 'सन्तुलित प्रभाव दिने ग्रह']
      ];
      const rowEl = (i, label, list, accent, meaning) => el(no, title, 'cards', label + ' ग्रह पङ्क्ति', [L, 206 + i * 156, W, 144], (() => {
        let s = '<rect x="' + L + '" y="' + (206 + i * 156) + '" width="' + W + '" height="144" rx="15" fill="#0d1830" stroke="' + accent + '" stroke-opacity=".38" stroke-width="1.4"/>';
        s += '<rect x="' + L + '" y="' + (216 + i * 156) + '" width="5" height="124" rx="2.5" fill="' + accent + '"/>';
        s += T(L + 24, 242 + i * 156, label, 20, accent, 700);
        s += T(L + 24, 270 + i * 156, meaning, 13.5, DIM, 600);
        s += T(R - 24, 242 + i * 156, ne(list.length) + ' ग्रह', 14, MUT, 600, 'end');
        s += P(L + 24, 308 + i * 156, list.length ? list.join(', ') : 'कुनै ग्रह यो वर्गमा छैन', Math.max(24, Math.floor((W - 48) / 9.6)), 18, 27, INK, 2);
        return s;
      })(), 7.4);
      push(no, title, 'ग्रह सम्बन्ध', [
        header(no, title, 'कारक · मारक · सम'),
        rowEl(0, 'कारक', groups.karaka, GOOD, 'शुभ फल दिने ग्रह'),
        rowEl(1, 'मारक', groups.maraka, BAD, 'चुनौती वा हानिसँग जोडिने ग्रह'),
        rowEl(2, 'सम', groups.sama, '#60a5fa', 'सन्तुलित प्रभाव दिने ग्रह'),
        el(no, title, 'report', 'ग्रह सम्बन्ध व्याख्या', [L, 684, W, 190], (() => {
          let s = '<rect x="' + L + '" y="684" width="' + W + '" height="190" rx="16" fill="#0d1830" stroke="' + GOLD2 + '" stroke-opacity=".32" stroke-width="1.4"/>';
          s += '<rect x="' + L + '" y="696" width="4" height="166" rx="2" fill="' + GOLD2 + '"/>';
          s += T(L + 24, 714, 'वर्गीकरणको अर्थ', 16, MUT, 700);
          s += T(L + 24, 754, 'कारक', 16.5, GOOD, 700);
          s += T(L + 118, 754, 'शुभ फल दिने', 16, INK, 500);
          s += T(L + 24, 792, 'मारक', 16.5, BAD, 700);
          s += T(L + 118, 792, 'चुनौती / हानि सम्बन्धी', 16, INK, 500);
          s += T(L + 24, 830, 'सम', 16.5, '#60a5fa', 700);
          s += T(L + 118, 830, 'सन्तुलित प्रभाव', 16, INK, 500);
          s += T(R - 24, 714, 'कुल ' + ne(groups.karaka.length + groups.maraka.length + groups.sama.length) + ' ग्रह', 13.5, DIM, 600, 'end');
          s += T(R - 24, 858, 'स्रोत: Kundali-Desktop · relationship', 12.5, DIM, 500, 'end');
          return s;
        })(), 8),
        footer(no, title)
      ], { priority: ORDER.relation, key: 'card-02' });
    }

    /* 02b — Sade Sati + Kaal Sarp as their own readable card */
    {
      const no = 2, title = 'साढे साती र कालसर्प';
      const ss = sadeSati(data, transit);
      const ssBody = (ss.known ? ('वर्तमान शनि गोचर: ' + sign(ss.saturnSign) + ' (' + (transit.current.start ? dt(String(transit.current.start).slice(0, 10)) : '—') + ' – ' + (transit.current.end ? dt(String(transit.current.end).slice(0, 10)) : '—') + ')\n') : '') + ss.text;
      const kNarr = K.narrative_ne || (K.present ? ('कालसर्प दोष सक्रिय छ — ' + (K.type || '') + '।') : 'कालसर्प दोष सम्बन्धी विवरण उपलब्ध छैन।');
      const kBody = (K.present && !/सक्रिय/.test(kNarr) ? 'कालसर्प दोष सक्रिय छ।\n' : '') + short(kNarr, 260);
      push(no, title, 'साढे साती र कालसर्प', [
        header(no, title, 'शनि गोचर · कालसर्प दोष'),
        el(no, title, 'report', 'साढे साती कार्ड', [L, 208, W, 268], (() => {
          const col = ss.phase.indexOf('सक्रिय छैन') >= 0 ? GOOD : MID;
          let s = '<rect x="' + L + '" y="208" width="' + W + '" height="268" rx="16" fill="#0d1830" stroke="' + col + '" stroke-opacity=".45" stroke-width="1.6"/>';
          s += '<rect x="' + L + '" y="220" width="4" height="244" rx="2" fill="' + col + '"/>';
          s += T(L + 24, 244, 'साढे साती · शनि गोचर', 16, MUT, 600);
          s += T(L + 24, 288, ss.phase, 30, col === GOOD ? GOOD : GOLD, 700);
          s += P(L + 24, 328, ssBody, 52, 16, 24, MUT, 4);
          s += T(R - 22, 244, 'चन्द्र: ' + sign(ss.moonSign) + (ss.known ? ' · शनि: ' + sign(ss.saturnSign) : ''), 13.5, DIM, 600, 'end');
          return s;
        })(), 8.6),
        el(no, title, 'report', 'कालसर्प कार्ड', [L, 492, W, 268], (() => {
          const col = K.present ? BAD : GOOD;
          let s = '<rect x="' + L + '" y="492" width="' + W + '" height="268" rx="16" fill="#0d1830" stroke="' + col + '" stroke-opacity=".45" stroke-width="1.6"/>';
          s += '<rect x="' + L + '" y="504" width="4" height="244" rx="2" fill="' + col + '"/>';
          s += T(L + 24, 528, 'कालसर्प दोष', 16, MUT, 600);
          s += T(L + 24, 572, K.present ? 'सक्रिय' : 'छैन', 31, col, 700);
          s += P(L + 24, 612, kBody, 52, 15.5, 24, MUT, 5);
          return s;
        })(), 8.6),
        note(no, title, 'गोचर तथा दोष नोट', [L, 776, W, 92], 'साढे साती शनिको गोचरमा आधारित छ; कालसर्प दोषको विवरण Kundali-Desktop को kaal_sarp_dosha बाट लिइएको हो।', { size: 14, lh: 21, lines: 3 }),
        footer(no, title)
      ], { priority: ORDER.sadeSati, key: 'card-02b' });
    }

    /* 03 — planet strength */
    {
      const no = 3, title = 'ग्रह बल (षड्बल)';
      const sb = data.shadbala || {}, sp = sb.planets || {};
      const names = KUN_ORDER.slice(0, 7).filter(n => sp[n]);
      let max = 1; names.forEach(n => { max = Math.max(max, +sp[n].total_rupas || 0, +sp[n].required_rupas || 0) }); max *= 1.12;
      const rank = sb.ranking || names;
      let bars = '';
      names.forEach((n, i) => {
        const p = sp[n], y = 360 + i * 84, v = +p.total_rupas || 0, req = +p.required_rupas || 0;
        const col = p.is_strong ? GOOD : BAD;
        const bx = 172, bw = 330;
        bars += T(L + 4, y + 14, pName(n), 19, INK, 700);
        bars += T(L + 4, y + 38, '#' + ne((rank.indexOf(n) + 1) || i + 1), 13, DIM, 500);
        bars += '<rect x="' + bx + '" y="' + (y + 2) + '" width="' + bw + '" height="28" rx="14" fill="#0a1224" stroke="#223052" stroke-width="1"/>';
        bars += '<rect x="' + bx + '" y="' + (y + 2) + '" width="' + Math.max(2, bw * v / max) + '" height="28" rx="14" fill="' + col + '"/>';
        if (req > 0) bars += '<line x1="' + (bx + bw * req / max) + '" y1="' + (y - 3) + '" x2="' + (bx + bw * req / max) + '" y2="' + (y + 34) + '" stroke="' + GOLD + '" stroke-width="2" stroke-dasharray="4 4"/>';
        bars += T(520, y + 18, num(v, 2) + ' रूप', 17, INK, 700);
        bars += T(R - 4, y + 18, p.is_strong ? 'बलवान' : 'दुर्बल', 13, col, 700, 'end');
      });
      const nodeNote = 'राहु/केतुको षड्बल यो backend प्रतिक्रियामा उपलब्ध छैन — ती दुईको मान “—” राखिएको छ।';
      push(no, title, 'ग्रह बल', [
        header(no, title, 'शुद्ध षड्बल · रूपमा कुल योग'),
        card(no, title, 'सर्वाधिक बल', L, 210, 290, 108, 'सर्वाधिक बल', pName(sb.strongest) + ' · ' + num((sp[sb.strongest] || {}).total_rupas, 2) + ' रूप', GOOD, { fs: 20, chars: 17, lh: 26, lfs: 13.5 }),
        card(no, title, 'सबैभन्दा कमजोर', L + 314, 210, 290, 108, 'सबैभन्दा कमजोर', pName(sb.weakest) + ' · ' + num((sp[sb.weakest] || {}).total_rupas, 2) + ' रूप', BAD, { fs: 20, chars: 17, lh: 26, lfs: 13.5 }),
        graphEl(no, title, 'षड्बल बार चार्ट', [L, 338, W, 632], bars, 9.4),
        note(no, title, 'षड्बल नोट', [L, 964, W, 90], 'हरियो = आवश्यक रूपभन्दा माथि, रातो = मुनि। सुनौलो थोप्लो = required रूप। ' + nodeNote, { size: 14, lh: 21, lines: 3 }),
        footer(no, title)
      ], { priority: ORDER.strength, key: 'card-03' });
    }

    /* 04 — real 3D planet pillars: height = actual degree inside the sign */
    {
      const no = 4, title = 'ग्रह स्तम्भ';
      const retro = planets.filter(p => p.is_retrograde).length;
      const combust = planets.filter(p => p.is_combust).length;
      const varg = planets.filter(p => p.is_vargottama).length;
      const baseY = 786, minH = 38, maxH = 512, colW = 54, gap = 11;
      const x0 = Math.round(L + (W - (colW * 9 + gap * 8)) / 2);
      let cols = T(L, 214, 'स्तम्भको उचाइ = राशिभित्रको वास्तविक अंश (०–३०°)', 13.5, DIM, 500);
      cols += '<line x1="' + L + '" y1="' + (baseY + 2) + '" x2="' + R + '" y2="' + (baseY + 2) + '" stroke="#2b3856" stroke-width="1.2"/>';
      KUN_ORDER.forEach((n, i) => {
        const p = planets.find(x => x.name === n);
        if (!p) return;
        const deg = Math.max(0, Math.min(30, +p.longitude_in_sign || 0));
        const h = minH + (maxH - minH) * deg / 30;
        const x = x0 + i * (colW + gap), y = baseY - h;
        const dg = dignity(p);
        const col = /उच्च/.test(dg) ? GOLD2 : /नीच/.test(dg) ? BAD : /(स्वराशि|मूलत्रिकोण)/.test(dg) ? GOOD : '#60a5fa';
        const cx = x + colW / 2;
        cols += '<ellipse cx="' + cx + '" cy="' + (baseY + 4) + '" rx="' + (colW * .62) + '" ry="7" fill="#000" opacity=".34"/>';
        cols += '<polygon points="' + (x + colW) + ',' + y + ' ' + (x + colW + 9) + ',' + (y - 9) + ' ' + (x + colW + 9) + ',' + (baseY - 9) + ' ' + (x + colW) + ',' + baseY + '" fill="' + col + '" opacity=".38"/>';
        cols += '<polygon points="' + x + ',' + y + ' ' + (x + 9) + ',' + (y - 9) + ' ' + (x + colW + 9) + ',' + (y - 9) + ' ' + (x + colW) + ',' + y + '" fill="' + col + '" opacity=".72"/>';
        cols += '<rect x="' + x + '" y="' + y + '" width="' + colW + '" height="' + h + '" rx="3" fill="' + col + '" opacity=".82" stroke="' + col + '" stroke-opacity=".9"/>';
        cols += '<rect x="' + (x + 5) + '" y="' + (y + 9) + '" width="4" height="' + Math.max(6, h - 18) + '" rx="2" fill="#ffffff" opacity=".22"/>';
        cols += T(cx, y - 16, pName(n), 13.5, INK, 700, 'middle');
        cols += T(cx, baseY + 23, sign(p.sign_number || 1), 12.5, MUT, 600, 'middle');
        cols += T(cx, baseY + 43, kunDMS(deg).replace(/″$/, ''), 12.5, GOLD, 700, 'middle');
      });
      push(no, title, 'ग्रह स्तम्भ', [
        header(no, title, 'नौ ग्रह — ३डी स्तम्भ, वास्तविक अंश र रङ'),
        graphEl(no, title, '३डी ग्रह स्तम्भ चार्ट', [L, 196, W, 648], cols, 10.2),
        card(no, title, 'वक्री ग्रह', L, 848, 192, 108, 'वक्री ग्रह', ne(retro) + ' ग्रह', '#6ee7ff', { fs: 22, chars: 10, lh: 27, lfs: 13.5 }),
        card(no, title, 'अस्त ग्रह', L + 206, 848, 192, 108, 'अस्त ग्रह', ne(combust) + ' ग्रह', '#fbbf24', { fs: 22, chars: 10, lh: 27, lfs: 13.5 }),
        card(no, title, 'वर्गोत्तम', L + 412, 848, 192, 108, 'वर्गोत्तम', ne(varg) + ' ग्रह', '#c4b5fd', { fs: 22, chars: 10, lh: 27, lfs: 13.5 }),
        note(no, title, 'स्तम्भ व्याख्या', [L, 966, W, 84], 'हरियो = स्वराशि/मूलत्रिकोण, सुनौलो = उच्च, रातो = नीच, नीलो = सामान्य। उचाइ राशिभित्रको वास्तविक अंशबाट, नाम/राशि/अंश सबै Kundali-Desktop गणनाबाट लिइएका हुन्।', { size: 14, lh: 21, lines: 3 }),
        footer(no, title)
      ], { priority: ORDER.pillars, key: 'card-04' });
    }

    /* 05 — Vimshottari + Yogini dasha with BS dates */
    {
      const no = 5, title = 'महादशा, अन्तर्दशा र योगिनी दशा';
      const vim = dashas.length ? dashas : [];
      const md = vim.find(x => +x.level === 1) || vim[0] || {};
      const ad = vim.find(x => +x.level === 2) || {};
      const ymd = yoginis.find(x => +x.level === 1) || {};
      const yad = yoginis.find(x => +x.level === 2) || yoginis[1] || {};
      const rows = vim.slice(0, 5).map((x, i) => [['महादशा', 'अन्तर्दशा', 'प्रत्यन्तर्दशा', 'सूक्ष्मदशा', 'प्राणदशा'][i] || ('स्तर ' + ne(x.level)), x.lordNe || pName(x.lord), bsOf(x.startBs, x.start), bsOf(x.endBs, x.end)]);
      if (!rows.length) rows.push(['महादशा', '—', '—', '—']);
      push(no, title, 'दशा काल', [
        header(no, title, 'विंशोत्तरी + योगिनी · वास्तविक BS मिति'),
        dashaBox(no, title, 'विंशोत्तरी महादशा', L, 204, 290, 164, 'विंशोत्तरी महादशा', md.lordNe || '—', bsOf(md.startBs, md.start), bsOf(md.endBs, md.end), GOLD2),
        dashaBox(no, title, 'विंशोत्तरी अन्तर्दशा', L + 314, 204, 290, 164, 'विंशोत्तरी अन्तर्दशा', ad.lordNe || '—', bsOf(ad.startBs, ad.start), bsOf(ad.endBs, ad.end), '#6ee7ff'),
        dashaBox(no, title, 'योगिनी महादशा', L, 384, 290, 164, 'योगिनी महादशा', (ymd.nameNe || '—') + ' · ' + (ymd.lord ? pName(ymd.lord) : '—'), bsOf(ymd.startBs, ymd.start), bsOf(ymd.endBs, ymd.end), '#c4b5fd'),
        dashaBox(no, title, 'योगिनी अन्तर्दशा', L + 314, 384, 290, 164, 'योगिनी अन्तर्दशा', yad.nameNe || '—', bsOf(yad.startBs, yad.start), bsOf(yad.endBs, yad.end), GOOD),
        table(no, title, 'सक्रिय दशा स्तर तालिका', L, 568, W, [
          { t: 'स्तर', w: 138 }, { t: 'दशा स्वामी', w: 134 }, { t: 'सुरु (BS)', w: 158 }, { t: 'अन्त्य (BS)', w: 174 }
        ], rows, { rowH: 56, headH: 50, fs: 15, hfs: 13, align: ['left', 'left', 'left', 'left'] }, 9.4),
        note(no, title, 'दशा नोट', [L, 912, W, 90], 'सबै मिति BS मा देखाइएका छन्; AD मिति आन्तरिक गणनाका लागि मात्र हो। सक्रिय दशा Kundali-Desktop को dasha_reports बाट लिइएको हो।', { size: 14, lh: 21, lines: 3 }),
        footer(no, title)
      ], { priority: ORDER.dasha, key: 'card-05' });
    }

    /* 06 — auspicious yogas, dynamically paginated by measured height.
       Every yoga keeps its full result text. A long result continues on a
       titled follow-up card at a sentence boundary; its number and category
       carry over so the sequence stays continuous. */
    const pushYogaFlow = (no, baseTitle, list, good, priority, keyBase, noteTxt, fallback) => {
      const entries = (list || []).map((yg, i) => ({
        no: i + 1,
        name: yg.nepali || yg.name || 'योग',
        category: yg.category || 'yoga',
        body: yg.result_ne || yg.result || yg.cause_ne || '—',
        accent: good ? (i % 2 ? '#22c55e' : GOLD2) : BAD
      }));
      const bodyLH = flowLineH(22);
      const pages = entries.length ? paginateFlowRows(entries, {
        firstTop: 318, nextTop: 206,
        firstBottom: 962, nextBottom: 1048,
        rowGap: 8, bodyChars: Math.max(24, Math.floor((W - 40) / 8.2)),
        bodyLH: bodyLH, padTop: 10, padBottom: 6,
        headerHeight: () => 34
      }) : [[]];
      const total = pages.length;
      pages.forEach((rows, pi) => {
        const first = pi === 0;
        const pgTitle = flowPageTitle(baseTitle, pi + 1, total);
        const listTop = first ? 318 : 206;
        let inner = '';
        if (rows.length) {
          let y = listTop;
          rows.forEach(row => { inner += yogaFlowRow(row, L, y, W, good); y += row.h + 8; });
        } else {
          inner = fallback;
        }
        const listH = rows.length ? rows.reduce((a, r) => a + r.h, 0) + (rows.length - 1) * 8 : 220;
        const els = [header(no, pgTitle, good ? 'राज · धन · महापुरुष · चन्द्र योग' : 'दोष, अशुभ ग्रह र उपाय')];
        if (first) els.push(card(no, pgTitle, good ? 'शुभ योग संख्या' : 'अशुभ योग संख्या', L, 204, W, 96, good ? 'कुल शुभ योग' : 'कुल अशुभ योग', ne(list.length) + ' योग' + (good ? ' · उच्च ' + ne(list.filter(y => /highly/.test(y.severity || '')).length) : ''), good ? GOOD : BAD, { fs: 23, chars: 22, lh: 28, lfs: 13.5 }));
        els.push(graphEl(no, pgTitle, good ? 'शुभ योग सूची' : 'अशुभ संकेत सूची', [L, listTop - 6, W, listH + 12], inner, good ? 9.4 : 9.8));
        if (first && rows.length) els.push(note(no, pgTitle, good ? 'योग स्रोत' : 'दोष नोट', [L, listTop + listH + 18, W, 68], noteTxt, { size: 13.5, lh: 20, lines: 2, color: good ? undefined : MODEL.colors.badMut }));
        push(no, pgTitle, good ? 'शुभ योग' : 'अशुभ योग', els, {
          priority: priority + pi * 0.5, key: pi ? keyBase + '-p' + (pi + 1) : keyBase,
          flow: {
            kind: good ? 'goodYoga' : 'badYoga', page: pi + 1, pages: total,
            rows: rows.map(r => ({ no: r.src.no, name: r.src.name, category: r.src.category, cont: r.cont, lines: r.lines, body: r.body }))
          }
        });
      });
    };

    {
      const no = 6, title = 'शुभ योगहरू';
      const good = yogaRows(data.parashara_yogas, true);
      const fallback = '<rect x="' + L + '" y="320" width="' + W + '" height="220" rx="16" fill="#0d1830" stroke="' + MID + '" stroke-opacity=".4"/><text x="360" y="410" text-anchor="middle" font-size="22" font-weight="700" fill="' + MID + '">कुनै शुभ योग भेटिएन</text><text x="360" y="448" text-anchor="middle" font-size="14" fill="' + MUT + '">यो कुण्डलीमा backend ले शुभ योग फेला पारेन।</text>';
      pushYogaFlow(no, title, good, true, ORDER.goodYoga, 'card-06',
        'परासर योग · Kundali-Desktop को parashara_yogas बाट; सबै उपस्थित शुभ योग, श्रेणी र फल वास्तविक प्रतिक्रियाबाट।', fallback);
    }

    /* 07 — inauspicious yogas / doshas use the same measured flow engine.
       The Lal Kitab signals get their own card (07b). */
    {
      const no = 7, title = 'अशुभ योग र दोष';
      const bad = yogaRows(data.parashara_yogas, false);
      const fallback = '<rect x="' + L + '" y="320" width="' + W + '" height="220" rx="16" fill="#0d1830" stroke="' + GOOD + '" stroke-opacity=".45"/><text x="360" y="410" text-anchor="middle" font-size="22" font-weight="700" fill="' + GOOD + '">कुनै अशुभ योग भेटिएन</text><text x="360" y="448" text-anchor="middle" font-size="14" fill="' + MUT + '">backend को parashara_yogas मा अशुभ श्रेणीको योग छैन।</text>';
      pushYogaFlow(no, title, bad, false, ORDER.badYoga, 'card-07',
        'रातो बाकस = अशुभ संकेत। उपायका लागि Kundali-Desktop को remedies खण्ड हेर्नुहोस्।', fallback);
    }

    /* 07b — Lal Kitab signals on their own readable card. Long phal text is
       split at sentence boundaries across continuous numbered pages. */
    {
      const no = 7, title = 'लालकिताब संकेत';
      const lal = ((data.lal_kitab || {}).planet_status || []).slice();
      const entries = lal.map(p => ({
        name: p.name,
        status: p.nek_manda || ((p.is_nek !== false) ? 'शुभ' : 'अशुभ'),
        good: p.is_nek !== false,
        body: p.phal || 'विवरण उपलब्ध छैन।'
      }));
      const bodyLH = flowLineH(20);
      const pages = entries.length ? paginateFlowRows(entries, {
        firstTop: 206, nextTop: 206,
        firstBottom: 968, nextBottom: 1048,
        rowGap: 6, bodyChars: Math.max(24, Math.floor((W - 44) / 8.2)),
        bodyLH: bodyLH, padTop: 10, padBottom: 6,
        headerHeight: () => 50
      }) : [[]];
      const total = pages.length;
      pages.forEach((rows, pi) => {
        const first = pi === 0;
        const pgTitle = flowPageTitle(title, pi + 1, total);
        let inner = '', y = 206;
        if (rows.length) {
          rows.forEach(row => { inner += lalFlowRow(row, L, y, W); y += row.h + 6; });
        } else {
          inner = '<rect x="' + L + '" y="206" width="' + W + '" height="150" rx="16" fill="#0d1830" stroke="' + MID + '" stroke-opacity=".4"/><text x="360" y="280" text-anchor="middle" font-size="21" font-weight="700" fill="' + MID + '">लालकिताब विवरण उपलब्ध छैन</text>';
        }
        const listH = rows.length ? rows.reduce((a, r) => a + r.h, 0) + (rows.length - 1) * 6 : 150;
        const els = [
          header(no, pgTitle, 'लालकिताब · शुभ/अशुभ ग्रह संकेत'),
          graphEl(no, pgTitle, 'लालकिताब सूची', [L, 200, W, listH + 12], inner, 9.2)
        ];
        if (first) els.push(note(no, pgTitle, 'लालकिताब नोट', [L, 206 + listH + 12, W, 68], 'हरियो = शुभ (नेक), रातो = अशुभ (मन्द)। संकेत र फल Kundali-Desktop को lal_kitab.planet_status बाट।', { size: 13.5, lh: 20, lines: 2 }));
        push(no, pgTitle, 'लालकिताब', els, {
          priority: ORDER.lalKitab + pi * 0.5, key: pi ? 'card-07b-p' + (pi + 1) : 'card-07b',
          flow: {
            kind: 'lalKitab', page: pi + 1, pages: total,
            rows: rows.map(r => ({ name: r.src.name, status: r.src.status, good: r.src.good, cont: r.cont, lines: r.lines, body: r.body }))
          }
        });
      });
    }

    /* 08 — Navamsha (D9) on its own card */
    {
      const no = 8, title = 'नवमांश (D9)';
      const d9 = (data.vargas || {}).D9 || {};
      const d9l = +((d9.lagna || {}).sign_number) || 1;
      const d9p = d9.planets || [];
      const d9H = d9p.length ? kunHouses(d9p, d9l, 'd9') : {};
      const d9Moon = d9p.find(p => p.name === 'Moon') || {};
      let grid = '';
      d9p.forEach((p, i) => {
        const col = i % 2, row = Math.floor(i / 2);
        const x = L + col * 312, y = 570 + row * 68;
        grid += '<rect x="' + x + '" y="' + y + '" width="292" height="60" rx="10" fill="' + (i % 2 ? '#0d1830' : '#101d36') + '" stroke="#223052"/>';
        grid += T(x + 14, y + 30, pName(p.name), 15.5, GOLD, 700);
        grid += T(x + 90, y + 30, sign(p.sign_number) + ' · भाव ' + ne(p.house || '—'), 14, MUT, 500);
        grid += T(x + 278, y + 30, short(dignity(p), 182), 12.5, DIM, 500, 'end');
      });
      push(no, title, 'D9', [
        header(no, title, 'नवमांश · सूक्ष्म ग्रह · विवाह र भाग्य'),
        chart(no, title, 'नवमांश चार्ट D9', d9H, d9l, L, 206, 360),
        card(no, title, 'D9 लग्न', 430, 206, 232, 106, 'D9 लग्न', sign(d9l) + ' · ' + kunDMS((d9.lagna || {}).longitude_in_sign || 0), GOLD2, { fs: 18, chars: 13, lh: 22, lfs: 13.5, vtop: 54, lines: 2 }),
        card(no, title, 'D9 चन्द्र', 430, 324, 232, 106, 'D9 चन्द्र', sign(d9Moon.sign_number || 1) + ' · भाव ' + ne(d9Moon.house || '—'), '#c4b5fd', { fs: 18, chars: 13, lh: 22, lfs: 13.5, vtop: 54, lines: 2 }),
        card(no, title, 'D9 चन्द्र नक्षत्र', 430, 442, 232, 106, 'D9 चन्द्र नक्षत्र', (d9Moon.nakshatra_nepali || '—') + (d9Moon.nakshatra_pada ? ' · पद ' + ne(d9Moon.nakshatra_pada) : ''), GOOD, { fs: 17, chars: 14, lh: 22, lfs: 13.5, vtop: 54, lines: 2 }),
        graphEl(no, title, 'D9 ग्रह सूची', [L, 564, W, Math.max(1, Math.ceil(d9p.length / 2)) * 68 + 12], grid, 9.2),
        note(no, title, 'D9 व्याख्या', [L, 934, W, 70], 'D9 = विवाह, धर्म, भाग्य र सूक्ष्म ग्रहबल। सबै अंश, राशि र भाव Kundali-Desktop को D9 वर्गबाट लिइएका हुन्।', { size: 14, lh: 21, lines: 2 }),
        footer(no, title)
      ], { priority: ORDER.d9, key: 'card-08' });
    }

    /* 08b — Moon chart and lunar details on their own card */
    {
      const no = 8, title = 'चन्द्र कुण्डली';
      const moonH = kunHouses(planets, +moon.sign_number || 1, 'chandra');
      const tithi = pc.tithi || {}, nak = pc.nakshatra || {};
      const nakName = moon.nakshatra_nepali || nak.nepali || '—';
      const nakPada = moon.nakshatra_pada || nak.pada;
      const cw = 192, gap = 14, x0 = L + (W - (cw * 3 + gap * 2)) / 2;
      const mcard = (i, label, value, accent, fs) => card(no, title, label, x0 + (i % 3) * (cw + gap), 660 + Math.floor(i / 3) * 128, cw, 118, label, value, accent, { fs: fs || 18, chars: 14, lh: 24, lfs: 13.5, vtop: 60, lines: 3 });
      push(no, title, 'चन्द्र कुण्डली', [
        header(no, title, 'चन्द्र लग्न · नक्षत्र · पक्ष'),
        chart(no, title, 'चन्द्र कुण्डली चार्ट', moonH, +moon.sign_number || 1, 140, 206, 440),
        mcard(0, 'चन्द्र राशि', sign(moon.sign_number || 1), '#6ee7ff'),
        mcard(1, 'चन्द्र भाव', ne(moon.house || '—'), GOLD2),
        mcard(2, 'चन्द्र अंश', kunDMS(moon.longitude_in_sign || 0).replace(/″$/, ''), '#c4b5fd', 17),
        mcard(3, 'जन्म नक्षत्र', (nakName || '—') + (nakPada ? ' · पद ' + ne(nakPada) : ''), GOOD, 16.5),
        mcard(4, 'नक्षत्र स्वामी', KUN_NE[moon.nakshatra_lord] || moon.nakshatra_lord || '—', '#60a5fa', 17),
        mcard(5, 'तिथि र पक्ष', (tithi.birth_nepali || tithi.nepali || '—') + (tithi.paksha_nepali ? ' · ' + tithi.paksha_nepali : ''), MID, 15.5),
        note(no, title, 'चन्द्र व्याख्या', [L, 918, W, 70], 'चन्द्र कुण्डलीमा चन्द्रलाई लग्न मानिएको छ। राशि, भाव, नक्षत्र, पद र स्वामी सबै वास्तविक जन्म विवरणबाट लिइएका हुन्।', { size: 14, lh: 21, lines: 2 }),
        footer(no, title)
      ], { priority: ORDER.moon, key: 'card-08b' });
    }

    /* 09 — active Vimshottari MD/AD effects */
    {
      const no = 9, title = 'सक्रिय महादशा र अन्तर्दशा प्रभाव';
      const md = dashas.find(x => +x.level === 1) || dashas[0] || {};
      const ad = dashas.find(x => +x.level === 2) || {};
      const pd = dashas.find(x => +x.level === 3) || {};
      const rows = dashas.slice(0, 5).map((x, i) => [['महादशा', 'अन्तर्दशा', 'प्रत्यन्तर्दशा', 'सूक्ष्मदशा', 'प्राणदशा'][i] || ne(x.level), x.lordNe || pName(x.lord), bsOf(x.startBs, x.start), bsOf(x.endBs, x.end)]);
      if (!rows.length) rows.push(['महादशा', '—', '—', '—']);
      const mdEffect = 'महादशा स्वामी ' + (md.lordNe || '—') + ': ' + lordEffect(data, md.lord) + '। यस अवधिमा जीवनको मुख्य दिशा र दीर्घकालीन कर्म प्रभावित रहन्छ।';
      const adEffect = 'अन्तर्दशा स्वामी ' + (ad.lordNe || '—') + ': ' + lordEffect(data, ad.lord) + '। दैनिक घटना, काम र सम्बन्धमा यसको प्रभाव देखिन्छ।';
      const pdEffect = pd.lord ? ('प्रत्यन्तर्दशा स्वामी ' + (pd.lordNe || pName(pd.lord)) + ': ' + lordEffect(data, pd.lord) + '। छोटो अवधिका विषय र निर्णयमा प्रभाव।') : '';
      push(no, title, 'सक्रिय दशा प्रभाव', [
        header(no, title, 'विंशोत्तरी सक्रिय श्रृंखला · BS मिति'),
        el(no, title, 'report', 'महादशा प्रभाव कार्ड', [L, 204, W, 150], (() => {
          let s = '<rect x="' + L + '" y="204" width="' + W + '" height="150" rx="14" fill="#0d1830" stroke="' + GOLD2 + '" stroke-opacity=".38"/>';
          s += T(L + 22, 234, 'सक्रिय महादशा · ' + (md.lordNe || '—'), 18, GOLD, 700);
          s += T(R - 22, 234, bsOf(md.startBs, md.start) + ' – ' + bsOf(md.endBs, md.end), 13.5, MUT, 500, 'end');
          s += P(L + 22, 266, mdEffect, 52, 15, 20, MUT, 4);
          return s;
        })(), 8.2),
        el(no, title, 'report', 'अन्तर्दशा प्रभाव कार्ड', [L, 368, W, 150], (() => {
          let s = '<rect x="' + L + '" y="368" width="' + W + '" height="150" rx="14" fill="#0d1830" stroke="#6ee7ff" stroke-opacity=".35"/>';
          s += T(L + 22, 398, 'सक्रिय अन्तर्दशा · ' + (ad.lordNe || '—'), 18, '#8be9ff', 700);
          s += T(R - 22, 398, bsOf(ad.startBs, ad.start) + ' – ' + bsOf(ad.endBs, ad.end), 13.5, MUT, 500, 'end');
          s += P(L + 22, 430, adEffect, 52, 15, 20, MUT, 4);
          return s;
        })(), 8.2),
        table(no, title, 'सक्रिय दशा तालिका', L, 534, W, [
          { t: 'स्तर', w: 138 }, { t: 'स्वामी', w: 128 }, { t: 'सुरु (BS)', w: 162 }, { t: 'अन्त्य (BS)', w: 176 }
        ], rows, { rowH: 58, headH: 50, fs: 15, hfs: 13.5, align: ['left', 'left', 'left', 'left'] }, 9),

        note(no, title, 'प्रत्यन्तर्दशा प्रभाव', [L, 884, W, 92], pdEffect || 'प्रत्यन्तर्दशा विवरण उपलब्ध छैन।', { size: 14.5, lh: 21, lines: 3 }),
        footer(no, title)
      ], { priority: ORDER.dashaEffect, key: 'card-09' });
    }

    /* 10 — active Yogini MD/AD effects */
    {
      const no = 10, title = 'सक्रिय योगिनी दशा प्रभाव';
      const md = yoginis.find(x => +x.level === 1) || {};
      const ad = yoginis.find(x => +x.level === 2) || yoginis[1] || {};
      const pd = yoginis.find(x => +x.level === 3) || {};
      const rows = yoginis.slice(0, 4).map((x, i) => [['योगिनी महादशा', 'योगिनी अन्तर्दशा', 'योगिनी प्रत्यन्तर', 'योगिनी सूक्ष्म'][i] || ('स्तर ' + ne(x.level)), (x.nameNe || '—') + ' · ' + (x.lord ? pName(x.lord) : '—'), bsOf(x.startBs, x.start), bsOf(x.endBs, x.end)]);
      if (!rows.length) rows.push(['योगिनी महादशा', '—', '—', '—']);
      const mdEffect = 'योगिनी ' + (md.nameNe || '—') + ' (ग्रह ' + (md.lord ? pName(md.lord) : '—') + ') — ' + (md.lord ? lordEffect(data, md.lord) : 'ग्रह विवरण उपलब्ध छैन') + '। योगिनी दशाले मन, शक्ति र ग्रहको चक्रीय प्रभाव देखाउँछ।';
      const adEffect = 'योगिनी अन्तर्दशा ' + (ad.nameNe || '—') + (ad.lord ? ' (ग्रह ' + pName(ad.lord) + ') — ' + lordEffect(data, ad.lord) : '') + '। यस अवधिमा योगिनीको मुख्य प्रवृत्ति अन्तर्दशामा झल्किन्छ।';
      push(no, title, 'योगिनी दशा प्रभाव', [
        header(no, title, 'योगिनी महादशा · अन्तर्दशा · BS मिति'),
        dashaBox(no, title, 'योगिनी महादशा', L, 204, 290, 176, 'सक्रिय योगिनी महादशा', (md.nameNe || '—') + ' · ' + (md.lord ? pName(md.lord) : '—'), bsOf(md.startBs, md.start), bsOf(md.endBs, md.end), '#c4b5fd'),
        dashaBox(no, title, 'योगिनी अन्तर्दशा', L + 314, 204, 290, 176, 'सक्रिय योगिनी अन्तर्दशा', ad.nameNe || '—', bsOf(ad.startBs, ad.start), bsOf(ad.endBs, ad.end), GOOD),
        el(no, title, 'report', 'योगिनी महादशा प्रभाव', [L, 396, W, 140], (() => {
          let s = '<rect x="' + L + '" y="396" width="' + W + '" height="140" rx="14" fill="#0d1830" stroke="#c4b5fd" stroke-opacity=".35"/>';
          s += T(L + 22, 424, 'महादशा प्रभाव', 16.5, '#d8ccff', 700);
          s += P(L + 22, 456, mdEffect, 52, 15, 20, MUT, 4);
          return s;
        })(), 8.2),
        el(no, title, 'report', 'योगिनी अन्तर्दशा प्रभाव', [L, 550, W, 140], (() => {
          let s = '<rect x="' + L + '" y="550" width="' + W + '" height="140" rx="14" fill="#0d1830" stroke="' + GOOD + '" stroke-opacity=".35"/>';
          s += T(L + 22, 578, 'अन्तर्दशा प्रभाव', 16.5, '#b9f6d9', 700);
          s += P(L + 22, 610, adEffect, 52, 15, 20, MUT, 4);
          return s;
        })(), 8.2),
        table(no, title, 'योगिनी दशा तालिका', L, 706, W, [
          { t: 'स्तर', w: 150 }, { t: 'योगिनी · ग्रह', w: 172 }, { t: 'सुरु (BS)', w: 140 }, { t: 'अन्त्य (BS)', w: 142 }
        ], rows, { rowH: 58, headH: 50, fs: 14.5, hfs: 13, align: ['left', 'left', 'left', 'left'] }, 9),
        footer(no, title)
      ], { priority: ORDER.yoginiEffect, key: 'card-10' });
    }

    /* 11 — the real Janmapatrika (कुण्डली निर्माण) document. Same page,
       same colours, same justified prose, charts, tables and scroll as
       Kundali-Desktop's जन्मपत्रिका page. The shared TOP_SAFE offset moves
       the whole paper below the TikTok top UI. */
    {
      const no = 11, title = 'जन्मपत्रिका (कुण्डली निर्माण)';
      const jp = window.KunJanmapatrika.build(data, meta, { x: L, y: 58, w: W });
      const jpEl = el(no, title, 'report', 'जन्मपत्रिका (कुण्डली निर्माण) — पूर्ण दस्तावेज',
        [L, 58, W, 1052], jp.inner, 18,
        { scroll: true, jp: true, scrollBbox: [L, 58, W, jp.height] });
      /* The name is embedded in the justified prose. The document builder
         returns its exact line rectangles so the privacy overlay can cover
         only the name, not the whole page. */
      if (jp.privacy && jp.privacy.length) {
        jpEl.privacy = jp.privacy.map(g => ({
          id: g.id, label: g.label,
          rects: (g.rects || []).map(r => ({ x: r.x, y: r.y + TOP_SAFE, w: r.w, h: r.h }))
        }));
      }
      push(no, title, 'जन्मपत्रिका', [jpEl], { priority: ORDER.janmapatrika, key: 'card-11', gap: .7 });
      const it = items[items.length - 1];
      it.scrollDur = 30;
      it.scrollDelay = .8;
      it.hideScrollBar = true;
    }

    /* 12 — SAV chart and the house summary (readable, larger cards) */
    {
      const no = 12, title = 'सर्वाष्टकवर्ग (SAV)';
      const savH = {};
      for (let h = 1; h <= 12; h++) {
        const sg = ((ls - 1 + h - 1) % 12) + 1;
        savH[h] = [sav.length ? ne(sav[sg - 1]) : '—'];
      }
      const vals = [];
      for (let h = 1; h <= 12; h++) {
        const sg = ((ls - 1 + h - 1) % 12) + 1;
        vals.push({ h: h, v: sav.length ? +sav[sg - 1] : NaN });
      }
      const known = vals.filter(x => isFinite(x.v));
      const maxV = known.length ? known.reduce((a, b) => b.v > a.v ? b : a) : { h: 0, v: NaN };
      const minV = known.length ? known.reduce((a, b) => b.v < a.v ? b : a) : { h: 0, v: NaN };
      push(no, title, 'SAV', [
        header(no, title, 'सर्वाष्टकवर्ग · बिन्दु विश्लेषण'),
        chart(no, title, 'सर्वाष्टकवर्ग चार्ट', savH, ls, 130, 206, 460, { sav: true }),
        note(no, title, 'SAV रङ संकेत', [L, 680, W, 48], 'हरियो = ३०+ बलियो · पहेँलो = २५–२९ सन्तुलित · रातो = २४ वा कम कमजोर।', { size: 14.5, lh: 20, lines: 1 }),
        card(no, title, 'सर्वाधिक SAV भाव', L, 742, 290, 126, 'सर्वाधिक बिन्दु', (maxV.h ? 'भाव ' + ne(maxV.h) + ' · ' + houseName(maxV.h) + '\n' + ne(maxV.v) + ' बिन्दु' : '—'), GOOD, { fs: 20, chars: 20, lh: 27, lfs: 13.5, vtop: 64, lines: 2 }),
        card(no, title, 'सबैभन्दा कम SAV भाव', L + 314, 742, 290, 126, 'सबैभन्दा कम बिन्दु', (minV.h ? 'भाव ' + ne(minV.h) + ' · ' + houseName(minV.h) + '\n' + ne(minV.v) + ' बिन्दु' : '—'), BAD, { fs: 20, chars: 20, lh: 27, lfs: 13.5, vtop: 64, lines: 2 }),
        note(no, title, 'SAV व्याख्या', [L, 884, W, 72], 'सर्वाष्टकवर्गले नौ ग्रहको कुल अष्टकवर्ग बिन्दु भावअनुसार देखाउँछ; बिन्दु बढी भएको भाव बलियो मानिन्छ।', { size: 14, lh: 21, lines: 2 }),
        footer(no, title)
      ], { priority: ORDER.sav, key: 'card-12' });
    }

    /* 12b — all twelve SAV houses as large, readable glass cards */
    {
      const no = 12, title = 'SAV भाव विवरण';
      const bw = 288, bh = 114, gapx = 28, gapy = 10;
      const boxes = [];
      for (let i = 0; i < 12; i++) {
        const h = i + 1, sg = ((ls - 1 + i) % 12) + 1, v = sav.length ? +sav[sg - 1] : NaN;
        const col = v >= 30 ? GOOD : v <= 24 ? BAD : MID;
        const bx = L + (i % 2) * (bw + gapx), by = 210 + Math.floor(i / 2) * (bh + gapy);
        let s = '<rect x="5" y="8" width="' + bw + '" height="' + bh + '" rx="15" fill="#000" opacity=".32"/>';
        s += '<rect x="0" y="0" width="' + bw + '" height="' + bh + '" rx="15" fill="#0d1830" stroke="' + col + '" stroke-opacity=".55" stroke-width="1.4"/>';
        s += '<rect x="1.5" y="1.5" width="' + (bw - 3) + '" height="' + (bh - 3) + '" rx="13.5" fill="' + col + '" fill-opacity=".06"/>';
        s += '<rect x="0" y="0" width="5" height="' + bh + '" rx="2.5" fill="' + col + '"/>';
        s += '<circle cx="' + (bw - 18) + '" cy="20" r="4" fill="' + col + '" opacity=".8"/>';
        s += T(18, 31, 'भाव ' + ne(h) + ' · ' + houseName(h), 14.5, MUT, 600);
        s += T(18, 76, isFinite(v) ? ne(v) : '—', 34, col, 700);
        s += T(18, 102, 'राशि ' + sign(sg) + ' · ' + (v >= 30 ? 'बलियो' : v <= 24 ? 'कमजोर' : 'सन्तुलित'), 13, DIM, 500);
        s += T(bw - 20, 76, isFinite(v) ? ne(v * 8) + ' बिन्दु' : '—', 13, DIM, 600, 'end');
        /* The element box includes the soft shadow margin so the drop
           shadow is never cut off by the SVG viewport. */
        boxes.push(el(no, title, 'cards', 'SAV भाव ' + ne(h) + ' ग्लास बाकस', [bx, by, bw + 6, bh + 10], '<g transform="translate(' + bx + ',' + by + ')">' + s + '</g>', 7.2));
      }
      push(no, title, 'SAV भाव', [
        header(no, title, 'सर्वाष्टकवर्ग · १२ भावको पूर्ण विवरण'),
        ...boxes,
        note(no, title, 'भाव नोट', [L, 966, W, 54], 'तलको सानो अंक = वास्तविक SAV बिन्दु; ठूलो अंक त्यही भावको बल देखाउँछ।', { size: 14, lh: 21, lines: 2 }),
        footer(no, title)
      ], { priority: ORDER.savHouses, key: 'card-12b' });
    }

    /* 13 — wishes */
    {
      const no = 13, title = 'शुभकामना र आशीर्वाद';
      const house10 = (((ls - 1) + 9) % 12) + 1;
      const house7 = (((ls - 1) + 6) % 12) + 1;
      const house2 = (((ls - 1) + 1) % 12) + 1;
      const lord10 = KUN_SIGN_LORD[house10 - 1], lord7 = KUN_SIGN_LORD[house7 - 1], lord2 = KUN_SIGN_LORD[house2 - 1];
      const houseOfLord = n => {
        const p = planets.find(x => x.name === n);
        return p && p.house ? ' भाव ' + ne(p.house) + ' मा' : '';
      };
      const wish10 = '१०औं भावेश ' + pName(lord10) + houseOfLord(lord10) + ' — कर्ममा निरन्तर उन्नति होस्।';
      const wish2 = '२औं भावेश ' + pName(lord2) + houseOfLord(lord2) + ' — आय स्थिर र समृद्धि बढोस्।';
      const wish7 = '७औं भावेश ' + pName(lord7) + houseOfLord(lord7) + ' — पारिवारिक सुख र सामञ्जस्य होस्।';
      const wishMoon = 'चन्द्र ' + sign(moon.sign_number || 1) + ' भाव ' + ne(moon.house || 1) + ' मा — मन र शरीर स्वस्थ रहोस्।';
      const orb = (() => {
        let s = '<circle cx="360" cy="350" r="112" fill="none" stroke="' + GOLD2 + '" stroke-opacity=".3" stroke-width="2"/>';
        s += '<circle cx="360" cy="350" r="86" fill="none" stroke="' + GOLD + '" stroke-opacity=".18"/>';
        for (let i = 0; i < 12; i++) {
          const a = (i * 30 - 90) * Math.PI / 180;
          s += '<circle cx="' + (360 + 112 * Math.cos(a)) + '" cy="' + (350 + 112 * Math.sin(a)) + '" r="3.5" fill="' + GOLD + '" opacity=".75"/>';
        }
        s += T(360, 340, 'ॐ', 44, GOLD, 700, 'middle');
        s += T(360, 382, 'शुभम्', 20, MUT, 600, 'middle');
        return s;
      })();
      push(no, title, 'शुभकामना', [
        header(no, title, 'सुनौलो आशीर्वाद · कुण्डली अनुसार'),
        artEl(no, title, 'सुनौलो कवच', [232, 196, 256, 256], orb, 7.4),
        note(no, title, 'मुख्य आशीर्वाद', [L, 456, W, 78], 'तपाईंको भविष्य उज्ज्वल, सुखमय, सफल र मंगलमय रहोस्। हार्दिक शुभकामना!', { size: 17, lh: 25, lines: 2, color: GOLD }),
        card(no, title, 'कर्म र प्रतिष्ठा', L, 560, 290, 158, 'कर्म र प्रतिष्ठा', wish10, GOLD2, { fs: 15, chars: 26, lh: 22, lfs: 13.5, lines: 4, vtop: 58 }),
        card(no, title, 'धन र समृद्धि', L + 314, 560, 290, 158, 'धन र समृद्धि', wish2, GOOD, { fs: 15, chars: 26, lh: 22, lfs: 13.5, lines: 4, vtop: 58 }),
        card(no, title, 'सम्बन्ध र सुख', L, 736, 290, 158, 'सम्बन्ध र सुख', wish7, '#6ee7ff', { fs: 15, chars: 26, lh: 22, lfs: 13.5, lines: 4, vtop: 58 }),
        card(no, title, 'स्वास्थ्य र आयु', L + 314, 736, 290, 158, 'स्वास्थ्य र आयु', wishMoon, '#c4b5fd', { fs: 15, chars: 26, lh: 22, lfs: 13.5, lines: 4, vtop: 58 }),
        note(no, title, 'आशीर्वाद नोट', [L, 912, W, 92], 'यी शुभकामना वास्तविक भाव, ग्रह स्वामी र स्थितिका आधारमा तयार गरिएका हुन्; कुनै निश्चित भविष्यवाणी होइनन्।', { size: 14, lh: 21, lines: 3 }),
        footer(no, title)
      ], { priority: ORDER.wishes, key: 'card-13' });
    }

    /* 14 — astrologer + WhatsApp + portrait photo */
    {
      const no = 14, title = 'ज्योतिषीय परामर्श';
      /* Name and number can be supplied by the caller. Both fall back to the
         studio's real contact details so the finished card never shows a
         placeholder. */
      const astroName = String(meta.astrologer_name || '').trim() || 'ज्योतिष पण्डित शिवराम पराजुली';
      const waRaw = String(meta.whatsapp_number || '').trim();
      const numText = waRaw ? ne(waRaw) : '९८४७४५२९०६';
      const waDigits = waRaw.replace(/\D/g, '') || '9847452906';
      const waUrl = 'https://wa.me/' + (waDigits.length === 10 ? '977' + waDigits : waDigits);
      const nameFs = astroName.length <= 30 ? 26 : astroName.length <= 38 ? 23 : 20;

      /* identity panel */
      const idY = 190, idH = 92;
      let ident = '<rect x="' + L + '" y="' + idY + '" width="' + W + '" height="' + idH + '" rx="16" fill="#0c1930" stroke="' + GOLD + '" stroke-opacity=".38" stroke-width="1.3"/>';
      ident += '<rect x="' + (L + 10) + '" y="' + (idY + 10) + '" width="' + (W - 20) + '" height="' + (idH - 20) + '" rx="11" fill="none" stroke="' + GOLD + '" stroke-opacity=".14"/>';
      ident += '<circle cx="100" cy="236" r="28" fill="#12233f" stroke="' + GOLD + '" stroke-opacity=".5" stroke-width="1.3"/>';
      ident += T(100, 236, 'ॐ', 28, GOLD, 700, 'middle');
      ident += T(142, 220, astroName, nameFs, GOLD, 700);
      ident += T(142, 253, 'वैदिक ज्योतिष · कुण्डली विश्लेषण · परामर्श', 14, MUT, 500);

      /* three service chips */
      const chipY = 330, chipH = 68, chipW = 194, chipGap = 11;
      const chipDefs = [
        ['०१', 'कुण्डली निर्माण'],
        ['०२', 'ग्रह बल'],
        ['०३', 'दशा–उपाय']
      ];
      let chips = '';
      chipDefs.forEach((c, i) => {
        const cx = L + i * (chipW + chipGap);
        chips += '<rect x="' + cx + '" y="' + chipY + '" width="' + chipW + '" height="' + chipH + '" rx="14" fill="#0d1830" stroke="' + GOLD + '" stroke-opacity=".3" stroke-width="1.2"/>';
        chips += '<circle cx="' + (cx + 33) + '" cy="' + (chipY + chipH / 2) + '" r="17" fill="#12233f" stroke="' + GOLD + '" stroke-opacity=".38" stroke-width="1.1"/>';
        chips += T(cx + 33, chipY + chipH / 2, c[0], 13.5, GOLD, 700, 'middle');
        chips += T(cx + 59, chipY + chipH / 2, c[1], 14.5, INK, 600);
      });

      /* WhatsApp call to action — the biggest tap target on the card */
      let wa = '<defs><linearGradient id="waGrad14" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#12452c"/><stop offset="1" stop-color="#0a2317"/></linearGradient></defs>';
      wa += '<rect x="110" y="416" width="500" height="124" rx="62" fill="url(#waGrad14)" stroke="#25D366" stroke-opacity=".6" stroke-width="1.8"/>';
      wa += '<rect x="120" y="426" width="480" height="104" rx="52" fill="none" stroke="#ffffff" stroke-opacity=".05" stroke-width="1.2"/>';
      wa += '<circle cx="178" cy="478" r="40" fill="#25D366"/>';
      wa += '<g transform="translate(178,478) scale(1.2) translate(-58,-52)">';
      wa += '<path d="M46 68l4-12a22 22 0 1 1 8 8l-12 4z" fill="#0b2418" opacity=".18"/>';
      wa += '<path d="M58 33c-10.5 0-19 8.5-19 19 0 3.6 1 7 2.8 9.9L39 72l10.4-2.7A19 19 0 1 0 58 33zm0 34.4c-8.5 0-15.4-6.9-15.4-15.4S49.5 36.6 58 36.6 73.4 43.5 73.4 52 66.5 67.4 58 67.4z" fill="#ffffff"/>';
      wa += '<path d="M65.5 56.2c-.3-.2-1.9-.9-2.2-1-.3-.1-.5-.2-.7.1-.2.3-.8 1-1 1.2-.2.2-.4.3-.7.1-.3-.1-1.2-.4-2.3-1.4-.9-.8-1.5-1.7-1.7-2-.1-.3 0-.5.1-.6l.5-.6c.2-.2.2-.3.3-.5.1-.2 0-.4 0-.5l-1-2.3c-.3-.7-.6-.6-.9-.6h-.8c-.3 0-.7.1-1 .5-.3.3-1.3 1.3-1.3 3.2s1.3 3.7 1.5 4c.2.2 2.6 4 6.3 5.5 2.2.9 3.1 1 4.2.8.6-.1 1.9-.8 2.2-1.5.3-.8.3-1.4.2-1.5-.1-.2-.3-.2-.6-.4z" fill="#ffffff"/>';
      wa += '</g>';
      wa += '<circle cx="576" cy="478" r="17" fill="none" stroke="#ffffff" stroke-opacity=".25" stroke-width="1.2"/>';
      wa += '<path d="M572 471l7 7-7 7" fill="none" stroke="#ffffff" stroke-opacity=".85" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>';
      wa += T(238, 452, 'WhatsApp मा सम्पर्क गर्नुहोस्', 15, '#9fe8bd', 600);
      wa += T(238, 490, numText, 32, '#ffffff', 700);
      wa += T(238, 524, 'छिटो जवाफ · सिधै म्यासेज पठाउनुहोस्', 14, '#bfe9cd', 500);

      /* hero / advertisement panel. The photo is an optional layer drawn over
         this finished poster, so an empty slot never looks like an upload box. */
      const adBox = [82, 554, 556, 314];
      let adInner = '<defs><radialGradient id="heroGlow14"><stop offset="0" stop-color="' + GOLD + '" stop-opacity=".16"/><stop offset="1" stop-color="' + GOLD + '" stop-opacity="0"/></radialGradient></defs>';
      adInner += '<rect x="' + adBox[0] + '" y="' + adBox[1] + '" width="' + adBox[2] + '" height="' + adBox[3] + '" rx="18" fill="#0a1726" stroke="' + GOLD + '" stroke-opacity=".48" stroke-width="1.4"/>';
      adInner += '<rect x="' + (adBox[0] + 10) + '" y="' + (adBox[1] + 10) + '" width="' + (adBox[2] - 20) + '" height="' + (adBox[3] - 20) + '" rx="13" fill="none" stroke="' + GOLD + '" stroke-opacity=".16"/>';
      adInner += '<circle cx="360" cy="642" r="118" fill="url(#heroGlow14)"/>';
      adInner += '<circle cx="360" cy="642" r="78" fill="none" stroke="' + GOLD + '" stroke-opacity=".18"/>';
      adInner += '<circle cx="360" cy="642" r="54" fill="none" stroke="' + GOLD + '" stroke-opacity=".26"/>';
      for (let d = 0; d < 12; d++) {
        const a = d * Math.PI / 6;
        adInner += '<circle cx="' + (360 + Math.cos(a) * 78).toFixed(1) + '" cy="' + (642 + Math.sin(a) * 78).toFixed(1) + '" r="' + (d % 3 === 0 ? 3.2 : 2) + '" fill="' + GOLD + '" fill-opacity=".55"/>';
      }
      adInner += '<path d="M360 603l10 29 29 11-29 10-10 30-10-30-29-10 29-11z" fill="' + GOLD + '" fill-opacity=".92"/>';
      adInner += '<path d="M286 642h-14M434 642h14" stroke="' + GOLD + '" stroke-opacity=".5" stroke-width="1.6"/>';
      adInner += T(360, 758, 'ज्योतिषीय परामर्श केन्द्र', 28, GOLD, 700, 'middle');
      adInner += '<line x1="284" y1="780" x2="436" y2="780" stroke="' + GOLD + '" stroke-opacity=".5" stroke-width="1.4"/>';
      adInner += T(360, 807, 'कुण्डली निर्माण · ग्रह बल · दशा विश्लेषण', 15, MUT, 500, 'middle');
      adInner += T(360, 838, 'वैदिक ज्योतिषको शास्त्रीय मार्गदर्शन', 14, DIM, 500, 'middle');

      /* trust strip + one-line hint */
      let trust = '<rect x="' + L + '" y="882" width="' + W + '" height="40" rx="20" fill="#0b2418" stroke="#25D366" stroke-opacity=".22" stroke-width="1.1"/>';
      trust += '<circle cx="88" cy="902" r="5" fill="' + GOOD + '"/>';
      trust += T(360, 902, '१००% गोपनीयता · विश्वास · शास्त्र · अनुभव', 14.5, '#9fe8bd', 600, 'middle');

      const noteTxt = 'बटन थिच्नुहोस् — WhatsApp सिधै खुल्छ';
      const noteEl = el(no, title, 'note', 'सम्पर्क नोट', [L, 936, W, 44], T(360, 958, noteTxt, 14.5, MUT, 500, 'middle'), 6.4, {
        editable: true,
        textStyle: { x: 360, y: 958, size: 14.5, color: MUT, weight: 500, single: true, anchor: 'middle', max: 42 },
        defaultText: noteTxt
      });

      push(no, title, 'परामर्श', [
        header(no, title, 'ज्योतिषीय परामर्श र सम्पर्क'),
        el(no, title, 'heading', 'ज्योतिषीय परिचय', [L, idY, W, idH], ident, 6.4),
        el(no, title, 'cards', 'सेवा सूची', [L, chipY, W, chipH], chips, 7),
        el(no, title, 'banner', 'WhatsApp सम्पर्क', [110, 416, 500, 124], wa, 7.4),
        el(no, title, 'art', 'ज्योतिषीको फोटो', adBox, adInner, 7.4, { ad: true, adSrc: '' }),
        el(no, title, 'note', 'विश्वास पट्टी', [L, 882, W, 40], trust, 6.4),
        noteEl,
        footer(no, title)
      ], { priority: ORDER.consult, key: 'card-14' });
      items[items.length - 1].hotspot = [110, 416 + TOP_SAFE + (items[items.length - 1].autoShift || 0), 500, 124];
      items[items.length - 1].hotspotUrl = waUrl;
      const adEl = items[items.length - 1].els.find(e => e.el.ad);
      if (adEl) adEl.adSrc = '';
    }

    /* Logical playback order. Every card keeps its real content; only the
       sequence changed. Additional pages created above inherit their base
       card's place through their `order` priority. */
    items.sort((a, b) => (a.order - b.order) || (a.seq - b.seq));
    items.forEach((it, i) => {
      it.autoNo = i + 1;
      it.seq = i;
      it.title = it.title || ('कार्ड ' + (i + 1));
      it.set = autoSet(it.tpl || MODEL.tpl);
      /* Duration follows the real reading load of each card. The Janmapatrika
         document keeps its long scroll window; users can still edit it in
         the Timeline. */
      it.dur = readDuration(it, modelByKey(it.modelKey));
    });
    return items;
  }

  function autoSet(tpl) {
    const m = MODELS[tpl] ? MODELS[tpl] : modelByKey(MODEL.key);
    return {
      speed: m.set.speed, entry: m.set.entry, anim: 'none', exit: m.set.exit,
      trans: m.set.trans, depth: m.set.depth, rotX: 0, rotY: 0, scale: 1,
      persp: 900, shadow: true, border: false, visible: true, bg: 'glass',
      align: 'center', pad: 22, radius: m.set.radius, stagger: m.set.stagger,
      animDur: m.set.animDur
    };
  }

  function fingerprint(data, meta, modelKey) {
    const m = Object.assign({}, (data && data.metadata) || {}, meta || {});
    /* The version prefix intentionally isolates layouts produced by earlier
       card structures. The model key is part of the fingerprint, so each of
       the four design models keeps its own saved edits and durations. */
    return ['auto-v10-timing', modelByKey(modelKey || MODEL.key).key,
      m.name || '', m.birth_date || '', m.birth_time || '',
      m.city || m.birth_place || '', m.ayanamsha_type || '', m.node_type || ''].join('|');
  }

  window.KunAutoBuild = {
    build: build, set: autoSet, fingerprint: fingerprint,
    models: MODELS, modelKeys: MODEL_KEYS, modelByKey: modelByKey,
    overflow: { wrap: flowWrap, sentences: flowSentences, split: splitTextFit, paginate: paginateFlowRows, title: flowPageTitle },
    CARD: CARD, HERO: { name: 'ज्योतिष पण्डित शिवराम पराजुली', phone: '९८४७४५२९०६', url: 'https://wa.me/9779847452906' }
  };
})();
