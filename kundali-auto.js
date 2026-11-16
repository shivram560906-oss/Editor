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

  const KUN_ORDER_ACTIVE = (typeof KUN_ORDER !== 'undefined') ? KUN_ORDER : ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu'];
  const KUN_NE_ACTIVE = (typeof KUN_NE !== 'undefined') ? KUN_NE : { Sun: 'सूर्य', Moon: 'चन्द्र', Mars: 'मङ्गल', Mercury: 'बुध', Jupiter: 'गुरु', Venus: 'शुक्र', Saturn: 'शनि', Rahu: 'राहु', Ketu: 'केतु' };
  const KUN_SIGN_LORD_ACTIVE = (typeof KUN_SIGN_LORD !== 'undefined') ? KUN_SIGN_LORD : ['Mars', 'Venus', 'Mercury', 'Moon', 'Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Saturn', 'Jupiter'];
  const KUN_HOUSE_NE_ACTIVE = (typeof KUN_HOUSE_NE !== 'undefined') ? KUN_HOUSE_NE : ['', 'तनु', 'धन', 'सहज', 'सुख', 'सन्तान', 'रोग', 'कलत्र', 'आयु', 'भाग्य', 'कर्म', 'लाभ', 'व्यय'];

  /* ═══════════════════════════════════════════════════════════════
     AUTOMATIC DESIGN MODEL — COSMIC GOLD (EXCLUSIVE)
     ------------------------------------------------------------------
     Only one premium, celestial Vedic model is active.
     Deep cosmic space, glowing orbits, gold/cyan highlights.
     ═══════════════════════════════════════════════════════════════ */
  const MODELS = {
    cosmic: {
      id: 1, key: 'cosmic', tpl: 'cosmic', badge: 'DEFAULT',
      name: 'Cosmic Gold', ne: 'कस्मिक गोल्ड', tag: 'ब्रह्माण्ड · गहिराइ',
      desc: 'गहिरो नीलो ब्रह्माण्ड, सुनौलो प्रकाश, कक्षा र ताराहरू — आधिकारिक वैदिक मोडेल।',
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
    }
  };
  const MODEL_KEYS = ['cosmic'];

  /* Playback order — EXACT 11 CARDS SEQUENCE */
  const ORDER = {
    birth: 10,
    avakahada: 20,
    vimshottari: 30,
    yogini: 40,
    pillars: 50,
    thisYear: 60,
    janmapatrika: 70,
    remedies: 80,
    yogas: 90,
    youthQA: 100,
    consult: 110
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
    if (typeof kunT === 'function') {
      return kunT(x, y, txt == null ? '' : String(txt), Math.round((size || 14) * MODEL.textScale * 10) / 10, color || INK, weight == null ? 500 : weight, anchor || 'start');
    }
    const fs = Math.round((size || 14) * MODEL.textScale * 10) / 10;
    const anch = anchor === 'middle' ? ' text-anchor="middle"' : anchor === 'end' ? ' text-anchor="end"' : '';
    return '<text x="' + x + '" y="' + y + '" font-size="' + fs + '" fill="' + (color || INK) + '" font-weight="' + (weight || 500) + '"' + anch + '>' + String(txt == null ? '' : txt).replace(/&/g, '&amp;').replace(/</g, '&lt;') + '</text>';
  }
  function P(x, y, txt, chars, size, lineH, color, maxLines) {
    if (typeof kunPara === 'function') {
      const sc = MODEL.textScale, lh = Math.round((lineH || 20) * MODEL.lineScale * 10) / 10;
      return kunPara(x, y, txt == null ? '' : String(txt), chars, Math.round((size || 14) * sc * 10) / 10, lh, color || INK, maxLines || 4);
    }
    return T(x, y, txt, size, color);
  }
  function num(v, d) { return (v == null || !isFinite(+v)) ? '—' : (typeof kunNum === 'function' ? kunNum(v, d == null ? 2 : d) : ne(Number(v).toFixed(d == null ? 2 : d))); }
  function ne(v) { return typeof neNum === 'function' ? neNum(v == null ? '—' : v) : String(v == null ? '—' : v); }
  function sign(n) { return typeof kunSignByNum === 'function' ? kunSignByNum(n) : ('राशि ' + n); }
  function dms(v) {
    if (typeof kunDMS === 'function') return kunDMS(v);
    if (v == null || !isFinite(+v)) return '—';
    const a = Math.abs(+v), d = Math.floor(a), mf = (a - d) * 60, m = Math.floor(mf), s = Math.round((mf - m) * 60);
    return ne(d) + '°' + ne(String(m).padStart(2, '0')) + '′' + ne(String(s).padStart(2, '0')) + '″';
  }
  function pName(n) { return KUN_NE_ACTIVE[n] || n || '—'; }
  function dt(iso) { return /^\d{4}-\d{2}-\d{2}/.test(String(iso || '')) ? (typeof kunDateNe === 'function' ? kunDateNe(iso) : iso) : '—'; }
  function bsText(s) {
    if (!s) return '—';
    if (/^\d{4}-\d{2}-\d{2}/.test(String(s))) return dt(s);
    return typeof kunBsShort === 'function' ? kunBsShort(s) : s;
  }
  /* Prefer the backend's BS value when it exists (format: BS YYYY-MM-DD);
     only convert from AD when the BS field is unavailable. */
  function bsOf(bs, ad) {
    if (bs) return (typeof kunBsShort === 'function' ? kunBsShort(bs) : bs);
    return ad ? dt(ad) : '—';
  }
  function range(a, b) { return bsText(a) + ' – ' + bsText(b); }
  function houseName(h) { return KUN_HOUSE_NE_ACTIVE[h] || '—'; }
  function dignity(p) { return typeof kunStateText === 'function' ? kunStateText(p) : '—'; }
  function short(txt, n) { return typeof kunFit === 'function' ? kunFit(txt == null ? '—' : txt, n || 46) : String(txt || '').slice(0, n || 46); }

  function cosmicCardBg(x, y, w, h, col, rx) {
    const r = rx || 16;
    const c = col || GOLD;
    let s = '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="' + r + '" fill="#0b1730" fill-opacity=".92" stroke="' + c + '" stroke-opacity=".52" stroke-width="1.5"/>';
    s += '<rect x="' + (x + 1) + '" y="' + (y + 1) + '" width="' + (w - 2) + '" height="' + Math.min(36, h * .3) + '" rx="' + (r - 1) + '" fill="' + c + '" fill-opacity=".06"/>';
    s += '<rect x="' + x + '" y="' + (y + 14) + '" width="5.5" height="' + (h - 28) + '" rx="2.5" fill="' + c + '"/>';
    return s;
  }

  function header(no, title) {
    const fs = 36;
    let s = '<circle cx="' + (L + 20) + '" cy="126" r="16" fill="#132446" stroke="' + GOLD + '" stroke-opacity=".85" stroke-width="1.4"/>';
    s += T(L + 20, 126, 'ॐ', 19, GOLD, 700, 'middle');
    s += T(L + 48, 137, title, fs, GOLD, 700);
    s += '<line x1="' + L + '" y1="158" x2="' + R + '" y2="158" stroke="' + GOLD2 + '" stroke-opacity=".55" stroke-width="1.8"/>';
    s += '<circle cx="' + (R - 6) + '" cy="158" r="3.2" fill="' + GOLD + '"/>';
    const box = [L - 6, 92, W + 12, 74];
    const st = { x: L + 48, y: 137, size: fs, color: GOLD, weight: 700, single: true };
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

  function getPlanetsList(data) {
    if (!data || !data.planets) return [];
    if (Array.isArray(data.planets)) return data.planets;
    if (typeof data.planets === 'object') {
      return Object.keys(data.planets).map(k => Object.assign({ name: k, planet: k }, data.planets[k]));
    }
    return [];
  }
  function findPlanet(data, name) {
    const list = getPlanetsList(data);
    return list.find(p => p.name === name || p.planet === name) || {};
  }
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
    if (typeof kunWrap === 'function') {
      return kunWrap(String(txt == null ? '' : txt).replace(/\s+/g, ' ').trim(), Math.max(8, Math.floor(chars || 40)));
    }
    const str = String(txt == null ? '' : txt).replace(/\s+/g, ' ').trim();
    const max = Math.max(8, Math.floor(chars || 40));
    const words = str.split(' ');
    const lines = [];
    let cur = '';
    for (const w of words) {
      if ((cur + ' ' + w).trim().length > max) {
        if (cur) lines.push(cur);
        cur = w;
      } else {
        cur = (cur + ' ' + w).trim();
      }
    }
    if (cur) lines.push(cur);
    return lines;
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
    const planets = getPlanetsList(data);
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

    /* ═══════════════════════════════════════════════════════════════
       ११ पूर्ण स्वचालित कार्डहरू (11 CANONICAL AUTOMATIC CARDS)
       - ठूलो, स्पष्ट र आकर्षक फन्ट (Large, legible & prominent text)
       - अनावश्यक हेडर र फुटर हटाइएको (No useless filler notes/footers)
       - पूर्ण भर्टिकल स्पेसको सही उपयोग (Full vertical canvas utilization)
       - प्रिमियम कस्मिक ग्लास ब्याकग्राउन्ड (Luxury Cosmic Glass Styling)
       ═══════════════════════════════════════════════════════════════ */

    /* ── CARD 01: जन्म विवरण (Birth Details & Entry Form with Animated Space BG) ── */
    {
      const no = 1, title = 'जन्म विवरण';
      const nameFs = fitFlowSize(name, 480, 44, 28);
      const coords = 'अक्षांश: ' + num(meta.latitude, 4) + '°  ·  देशान्तर: ' + num(meta.longitude, 4) + '°';
      const fName = meta.father_name || (data.metadata || {}).father_name || '';
      const mName = meta.mother_name || (data.metadata || {}).mother_name || '';
      const gotra = meta.gotra || (data.metadata || {}).gotra || '';
      const adDate = meta.birth_date || (data.metadata || {}).birth_date || '';

      const spaceArt = (() => {
        let s = '<defs>';
        s += '<radialGradient id="spcGlow" cx="50%" cy="45%" r="65%"><stop offset="0%" stop-color="#f6d365" stop-opacity=".25"/><stop offset="35%" stop-color="#3b82f6" stop-opacity=".18"/><stop offset="85%" stop-color="#050b18" stop-opacity="0"/></radialGradient>';
        s += '<linearGradient id="orbG1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#f6d365" stop-opacity=".75"/><stop offset="100%" stop-color="#38bdf8" stop-opacity=".3"/></linearGradient>';
        s += '</defs>';
        s += '<rect x="' + L + '" y="80" width="' + W + '" height="980" rx="24" fill="url(#spcGlow)"/>';
        const stars = [
          [90, 110, 2.6, .9], [160, 130, 1.8, .6], [230, 95, 3.0, .95], [320, 115, 2.0, .7], [500, 105, 2.8, .9], [590, 125, 2.0, .7],
          [78, 230, 1.8, .6], [626, 210, 2.6, .85], [98, 370, 2.2, .75], [612, 390, 2.0, .7], [88, 520, 2.4, .8], [632, 540, 2.2, .75],
          [82, 690, 1.9, .65], [618, 710, 2.8, .9], [105, 860, 2.2, .75], [604, 880, 1.8, .6], [240, 980, 2.6, .85], [480, 970, 2.2, .75],
          [135, 460, 1.6, .5], [575, 480, 1.8, .6], [175, 640, 2.3, .75], [535, 660, 2.0, .7], [360, 120, 3.5, 1.0]
        ];
        stars.forEach(st => {
          s += '<circle cx="' + st[0] + '" cy="' + st[1] + '" r="' + st[2] + '" fill="#ffffff" opacity="' + st[3] + '"/>';
        });
        s += '<ellipse cx="360" cy="530" rx="285" ry="120" fill="none" stroke="url(#orbG1)" stroke-width="1.8" stroke-dasharray="8 6" transform="rotate(-18 360 530)"/>';
        s += '<ellipse cx="360" cy="530" rx="230" ry="92" fill="none" stroke="' + GOLD2 + '" stroke-opacity=".38" stroke-width="1.4" transform="rotate(22 360 530)"/>';
        s += '<ellipse cx="360" cy="530" rx="170" ry="65" fill="none" stroke="#60a5fa" stroke-opacity=".42" stroke-width="1.3"/>';
        const pls = [
          [170, 495, 8.5, GOLD], [545, 590, 7.5, '#6ee7ff'], [235, 570, 6.5, '#fb7185'],
          [480, 485, 6.0, '#34d399'], [360, 465, 9.0, '#fbbf24'], [430, 615, 7.5, '#c4b5fd'], [275, 480, 7.0, '#60a5fa']
        ];
        pls.forEach(p => {
          s += '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="' + (p[2] + 4) + '" fill="' + p[3] + '" opacity=".25"/>';
          s += '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="' + p[2] + '" fill="' + p[3] + '"/>';
        });
        return s;
      })();

      const infoBox = (() => {
        let s = '';
        s += '<circle cx="360" cy="116" r="32" fill="#132446" stroke="' + GOLD + '" stroke-opacity=".8" stroke-width="1.6"/>';
        s += T(360, 116, 'ॐ', 32, GOLD, 700, 'middle');
        s += T(360, 178, name, nameFs, GOLD, 700, 'middle');
        s += T(360, 216, '॥ वैदिक जन्म पत्रिका विवरण ॥', 18, MUT, 600, 'middle');
        s += '<line x1="180" y1="234" x2="540" y2="234" stroke="' + GOLD2 + '" stroke-opacity=".45" stroke-width="1.6"/>';

        const fields = [
          ['📅', 'जन्म मिति', dateBs + (adDate ? '  (ई.सं. ' + adDate + ')' : ''), GOLD],
          ['⏰', 'जन्म समय', timeNe, '#6ee7ff'],
          ['📍', 'जन्म स्थान', place, '#34d399'],
          ['🌐', 'भौगोलिक स्थिति', coords, '#c4b5fd']
        ];
        fields.forEach((f, idx) => {
          const fy = 256 + idx * 124;
          s += cosmicCardBg(L, fy, W, 112, f[3], 18);
          s += T(L + 28, fy + 38, f[0] + '  ' + f[1], 19, MUT, 600);
          s += T(L + 28, fy + 82, f[2], 28, f[3], 700);
        });

        const extraList = [];
        if (fName) extraList.push('बुबा: ' + fName);
        if (mName) extraList.push('आमा: ' + mName);
        if (gotra) extraList.push('गोत्र: ' + gotra);
        if (extraList.length) {
          s += '<rect x="' + L + '" y="760" width="' + W + '" height="68" rx="16" fill="#0d1f3c" stroke="#2b3e6b" stroke-width="1.3"/>';
          s += T(360, 802, extraList.join('   ·   '), 20, '#f8fbff', 600, 'middle');
        }

        const cy = extraList.length ? 846 : 764;
        const cw = 190, cg = 17;
        const chips = [
          ['लग्न राशि', sign(ls) + ' (' + dms(lagna.longitude_in_sign || 0) + ')', GOLD2],
          ['चन्द्र राशि', sign(moon.sign_number || 1) + ' · ' + (moon.nakshatra_nepali || '—'), '#6ee7ff'],
          ['जन्म नक्षत्र', (moon.nakshatra_nepali || '—') + ' · पद ' + ne(moon.nakshatra_pada || '१'), '#c4b5fd']
        ];
        chips.forEach((c, i) => {
          const cx = L + i * (cw + cg);
          s += cosmicCardBg(cx, cy, cw, 150, c[2], 16);
          s += T(cx + 18, cy + 38, c[0], 17, MUT, 600);
          s += T(cx + 18, cy + 82, c[1], 24, c[2], 700);
          s += T(cx + 18, cy + 122, 'प्राकृतिक प्रभाव', 14.5, DIM, 500);
        });

        return s;
      })();

      push(no, title, 'जन्म परिचय', [
        artEl(no, title, 'अन्तरिक्ष पृष्ठभूमि कला', [L, 80, W, 980], spaceArt, 7.8),
        el(no, title, 'report', 'जन्म विवरण फाराम', [L, 84, W, 980], infoBox, 8.4)
      ], { priority: ORDER.birth, key: 'card-01', privacyStyle: 'strong' });
    }

    /* ── CARD 02: अवकाहडा चक्र (Avakahada Chakra Details) ── */
    {
      const no = 2, title = 'अवकाहडा चक्र';
      const itemsGrid = [
        ['जन्म राशि', av.rashi || sign(moon.sign_number || 1), GOLD, 'चन्द्रमा रहेको मूल राशि'],
        ['राशि स्वामी', av.rashi_lord || KUN_NE_ACTIVE[KUN_SIGN_LORD_ACTIVE[(moon.sign_number || 1) - 1]] || '—', '#6ee7ff', 'राशिको अधिपती ग्रह'],
        ['जन्म नक्षत्र', (av.nakshatra || moon.nakshatra_nepali || '—') + ' (' + ne(av.pada || moon.nakshatra_pada || 1) + ' पद)', '#c4b5fd', 'जन्मकालीन नक्षत्र र चरण'],
        ['नक्षत्र स्वामी', KUN_NE_ACTIVE[moon.nakshatra_lord] || moon.nakshatra_lord || '—', '#34d399', 'नक्षत्रको ग्रह स्वामी'],
        ['नामाक्षर', av.name_akshara || '—', GOLD2, 'राशिअनुसारको आदि अक्षर'],
        ['वर्ण', av.varna || 'विप्र', '#60a5fa', 'प्रवृत्ति र कार्य तत्त्व'],
        ['वश्य', av.vashya || 'जलचर', '#38bdf8', 'प्रकृतिको आकर्षण तत्त्व'],
        ['योनि', (av.yoni || '—') + (av.viryoni ? ' (वैर: ' + av.viryoni + ')' : ''), '#f472b6', 'स्वभाव र जैविक प्रकृति'],
        ['गण', av.gana || 'देव', '#a78bfa', 'विचार र मानसिक प्रकृति'],
        ['नाडी', av.nadi || 'आदि', '#fbbf24', 'स्वास्थ्य र शारीरिक त्रिदोष'],
        ['वर्ग / शत्रु', (av.varga || '—') + ' / ' + (av.shatru_varga || '—'), '#fb7185', 'नामाक्षर शत्रु/मित्र वर्ग'],
        ['तिथि र करण', ((pc.tithi && (pc.tithi.nepali || pc.tithi.birth_nepali)) || '—') + ' · ' + ((pc.karana && pc.karana.nepali) || '—'), '#34d399', 'पञ्चाङ्ग तिथि र करण']
      ];

      const bw = 292, bh = 144, gx = 20, gy = 16;
      let gridSvg = '';
      itemsGrid.forEach((it, idx) => {
        const col = idx % 2, row = Math.floor(idx / 2);
        const bx = L + col * (bw + gx), by = 176 + row * (bh + gy);
        gridSvg += cosmicCardBg(bx, by, bw, bh, it[2], 16);
        gridSvg += T(bx + 20, by + 36, it[0], 18, it[2], 700);
        gridSvg += T(bx + 20, by + 82, it[1], 28, '#ffffff', 700);
        gridSvg += T(bx + 20, by + 120, it[3], 15.5, '#b3c2de', 500);
      });

      push(no, title, 'अवकाहडा', [
        header(no, title),
        graphEl(no, title, 'अवकाहडा ग्रिड', [L, 172, W, 960], gridSvg, 8.8)
      ], { priority: ORDER.avakahada, key: 'card-02' });
    }

    /* ── CARD 03: सक्रिय विंशोत्तरी महादशा र अन्तर्दशा (Active Vimshottari Dasha) ── */
    {
      const no = 3, title = 'सक्रिय विंशोत्तरी दशा';
      const vim = dashas.length ? dashas : [];
      const md = vim.find(x => +x.level === 1) || vim[0] || {};
      const ad = vim.find(x => +x.level === 2) || {};
      const rows = vim.slice(0, 4).map((x, i) => [['महादशा', 'अन्तर्दशा', 'प्रत्यन्तर', 'सूक्ष्म'][i] || ('स्तर ' + ne(x.level)), x.lordNe || pName(x.lord), bsOf(x.startBs, x.start), bsOf(x.endBs, x.end)]);
      if (!rows.length) rows.push(['महादशा', '—', '—', '—']);

      const mdEffect = 'महादशा स्वामी ' + (md.lordNe || '—') + ' (' + lordEffect(data, md.lord) + ')। यस अवधिमा जीवनको मुख्य दिशा, दीर्घकालीन कर्म, प्रतिष्ठा र भाग्यको मूल प्रवाह निर्धारित हुन्छ।';
      const adEffect = 'अन्तर्दशा स्वामी ' + (ad.lordNe || '—') + ' (' + lordEffect(data, ad.lord) + ')। वर्तमान समयमा दैनिक कार्य, पारिवारिक वातावरण, आम्दानी र तत्कालीन निर्णयहरू यसबाट प्रभावित छन्।';

      const mdBoxSvg = (() => {
        let s = cosmicCardBg(L, 176, 292, 196, GOLD, 18);
        s += T(L + 22, 214, 'सक्रिय महादशा', 19, MUT, 600);
        s += T(L + 22, 268, md.lordNe || '—', 40, GOLD, 700);
        s += T(L + 22, 318, 'अवधि: ' + bsOf(md.startBs, md.start), 17.5, '#ffffff', 600);
        s += T(L + 22, 348, 'देखि ' + bsOf(md.endBs, md.end) + ' सम्म', 17.5, '#ffffff', 600);
        return s;
      })();

      const adBoxSvg = (() => {
        let s = cosmicCardBg(L + 312, 176, 292, 196, '#6ee7ff', 18);
        s += T(L + 334, 214, 'सक्रिय अन्तर्दशा', 19, MUT, 600);
        s += T(L + 334, 268, ad.lordNe || '—', 40, '#6ee7ff', 700);
        s += T(L + 334, 318, 'अवधि: ' + bsOf(ad.startBs, ad.start), 17.5, '#ffffff', 600);
        s += T(L + 334, 348, 'देखि ' + bsOf(ad.endBs, ad.end) + ' सम्म', 17.5, '#ffffff', 600);
        return s;
      })();

      const mdRepSvg = (() => {
        let s = cosmicCardBg(L, 390, W, 178, GOLD2, 18);
        s += T(L + 26, 426, 'महादशा प्रभाव · ' + (md.lordNe || '—'), 23, GOLD, 700);
        s += P(L + 26, 462, mdEffect, 50, 19.5, 28, INK, 4);
        return s;
      })();

      const adRepSvg = (() => {
        let s = cosmicCardBg(L, 584, W, 178, '#6ee7ff', 18);
        s += T(L + 26, 620, 'अन्तर्दशा प्रभाव · ' + (ad.lordNe || '—'), 23, '#8be9ff', 700);
        s += P(L + 26, 656, adEffect, 50, 19.5, 28, INK, 4);
        return s;
      })();

      push(no, title, 'विंशोत्तरी दशा', [
        header(no, title),
        el(no, title, 'cards', 'सक्रिय महादशा', [L, 176, 292, 196], mdBoxSvg, 8.2),
        el(no, title, 'cards', 'सक्रिय अन्तर्दशा', [L + 312, 176, 292, 196], adBoxSvg, 8.2),
        el(no, title, 'report', 'महादशा प्रभाव विवरण', [L, 390, W, 178], mdRepSvg, 8.4),
        el(no, title, 'report', 'अन्तर्दशा प्रभाव विवरण', [L, 584, W, 178], adRepSvg, 8.4),
        table(no, title, 'विंशोत्तरी दशा स्तर तालिका', L, 780, W, [
          { t: 'स्तर', w: 136 }, { t: 'दशा स्वामी', w: 134 }, { t: 'सुरु (वि.सं.)', w: 164 }, { t: 'अन्त्य (वि.सं.)', w: 170 }
        ], rows, { rowH: 60, headH: 50, fs: 19, hfs: 17, align: ['left', 'left', 'left', 'left'] }, 9)
      ], { priority: ORDER.vimshottari, key: 'card-03' });
    }

    /* ── CARD 04: सक्रिय योगिनी महादशा र अन्तर्दशा (Active Yogini Dasha) ── */
    {
      const no = 4, title = 'सक्रिय योगिनी दशा';
      const md = yoginis.find(x => +x.level === 1) || {};
      const ad = yoginis.find(x => +x.level === 2) || yoginis[1] || {};
      const rows = yoginis.slice(0, 4).map((x, i) => [['योगिनी महादशा', 'योगिनी अन्तर्दशा', 'योगिनी प्रत्यन्तर', 'योगिनी सूक्ष्म'][i] || ('स्तर ' + ne(x.level)), (x.nameNe || '—') + ' (' + (x.lord ? pName(x.lord) : '—') + ')', bsOf(x.startBs, x.start), bsOf(x.endBs, x.end)]);
      if (!rows.length) rows.push(['योगिनी महादशा', '—', '—', '—']);

      const yoginiPhalMap = {
        'Mangala': 'मङ्गला दशा (चन्द्र स्वामी) अत्यन्त शुभ मानिन्छ। यसले मनमा शान्ति, गृहसुख, नयाँ काममा सफलता र पारिवारिक सौहार्दता प्रदान गर्दछ।',
        'Pingala': 'पिङ्गला दशा (सूर्य स्वामी) ले पराक्रम र मान-सम्मान बढाउँछ। स्वास्थ्य र क्रोधमा संयम अपनाउनु लाभदायक हुन्छ।',
        'Dhanya': 'धान्या दशा (गुरु स्वामी) ले विद्या, धन-धान्य, ज्ञान र ईश्वरीय कृपा दिलाउँछ। आर्थिक संचयका लागि उत्तम समय रहन्छ।',
        'Bhramari': 'भ्रामरी दशा (मङ्गल स्वामी) ले यात्रा, स्थान परिवर्तन र साहस बढाउँछ। हतारमा गरिने निर्णयबाट बच्नुपर्छ।',
        'Bhadrika': 'भद्रिका दशा (बुध स्वामी) ले बुद्धि, व्यापार, अध्ययन र मित्रवर्गबाट लाभ गराउँछ। कार्यक्षेत्रमा बौद्धिक प्रगति हुन्छ।',
        'Ulka': 'उल्का दशा (शनि स्वामी) ले कडा परिश्रम र धैर्यको माग गर्दछ। मुद्दा-मामिला र अनावश्यक दौडधुपबाट सतर्क रहनुपर्छ।',
        'Siddha': 'सिद्धा दशा (शुक्र स्वामी) ले कार्यसिद्धि, भौतिक समृद्धि, विवाह वा प्रेम सम्बन्धमा अनुकूलता र यश दिलाउँछ।',
        'Sankata': 'संकटा दशा (राहु स्वामी) मा विशेष सतर्कता र कुलदेवताको साधना आवश्यक हुन्छ। मानसिक शान्तिका लागि उपाय गर्नु उत्तम हुन्छ।'
      };
      const mdPhal = yoginiPhalMap[md.name] || ('योगिनी ' + (md.nameNe || '—') + ' (ग्रह ' + (md.lord ? pName(md.lord) : '—') + ') को चक्रीय प्रभाव सक्रिय छ। मन, कर्म र आत्मबलमा अनुकूल प्रभाव पर्नेछ।');
      const adPhal = 'अन्तर्दशा ' + (ad.nameNe || '—') + (ad.lord ? ' (ग्रह ' + pName(ad.lord) + ')' : '') + ' ले तत्कालीन परिस्थिति, स्वास्थ्य र मनोबलमा योगिनीको फललाई प्रत्यक्ष रूपमा प्रकट गर्दछ।';

      const mdBoxSvg = (() => {
        let s = cosmicCardBg(L, 176, 292, 196, '#c4b5fd', 18);
        s += T(L + 22, 214, 'योगिनी महादशा', 19, MUT, 600);
        s += T(L + 22, 268, md.nameNe || '—', 38, '#d8ccff', 700);
        s += T(L + 22, 318, 'अवधि: ' + bsOf(md.startBs, md.start), 17.5, '#ffffff', 600);
        s += T(L + 22, 348, 'देखि ' + bsOf(md.endBs, md.end) + ' सम्म', 17.5, '#ffffff', 600);
        return s;
      })();

      const adBoxSvg = (() => {
        let s = cosmicCardBg(L + 312, 176, 292, 196, GOOD, 18);
        s += T(L + 334, 214, 'योगिनी अन्तर्दशा', 19, MUT, 600);
        s += T(L + 334, 268, ad.nameNe || '—', 38, '#b9f6d9', 700);
        s += T(L + 334, 318, 'अवधि: ' + bsOf(ad.startBs, ad.start), 17.5, '#ffffff', 600);
        s += T(L + 334, 348, 'देखि ' + bsOf(ad.endBs, ad.end) + ' सम्म', 17.5, '#ffffff', 600);
        return s;
      })();

      const mdRepSvg = (() => {
        let s = cosmicCardBg(L, 390, W, 178, '#c4b5fd', 18);
        s += T(L + 26, 426, 'महादशा प्रभाव · ' + (md.nameNe || '—'), 23, '#d8ccff', 700);
        s += P(L + 26, 462, mdPhal, 50, 19.5, 28, INK, 4);
        return s;
      })();

      const adRepSvg = (() => {
        let s = cosmicCardBg(L, 584, W, 178, GOOD, 18);
        s += T(L + 26, 620, 'अन्तर्दशा प्रभाव · ' + (ad.nameNe || '—'), 23, '#b9f6d9', 700);
        s += P(L + 26, 656, adPhal, 50, 19.5, 28, INK, 4);
        return s;
      })();

      push(no, title, 'योगिनी दशा', [
        header(no, title),
        el(no, title, 'cards', 'योगिनी महादशा', [L, 176, 292, 196], mdBoxSvg, 8.2),
        el(no, title, 'cards', 'योगिनी अन्तर्दशा', [L + 312, 176, 292, 196], adBoxSvg, 8.2),
        el(no, title, 'report', 'योगिनी महादशा फल', [L, 390, W, 178], mdRepSvg, 8.4),
        el(no, title, 'report', 'योगिनी अन्तर्दशा फल', [L, 584, W, 178], adRepSvg, 8.4),
        table(no, title, 'योगिनी दशा तालिका', L, 780, W, [
          { t: 'स्तर', w: 148 }, { t: 'योगिनी (स्वामी)', w: 172 }, { t: 'सुरु (वि.सं.)', w: 142 }, { t: 'अन्त्य (वि.सं.)', w: 142 }
        ], rows, { rowH: 60, headH: 50, fs: 19, hfs: 17, align: ['left', 'left', 'left', 'left'] }, 9)
      ], { priority: ORDER.yogini, key: 'card-04' });
    }

    /* ── CARD 05: ग्रह स्तम्भ (3D Bar Chart) + कारक / मारक / सम ग्रह ── */
    {
      const no = 5, title = 'ग्रह स्तम्भ र सम्बन्ध';
      const baseY = 560, minH = 32, maxH = 330, colW = 54, gap = 11;
      const x0 = Math.round(L + (W - (colW * 9 + gap * 8)) / 2);

      let cols = T(L, 186, 'स्तम्भको उचाइ = राशिभित्रको वास्तविक अंश (०°–३०°)', 16, MUT, 600);
      cols += '<line x1="' + L + '" y1="' + (baseY + 2) + '" x2="' + R + '" y2="' + (baseY + 2) + '" stroke="#2b3856" stroke-width="1.4"/>';
      KUN_ORDER_ACTIVE.forEach((n, i) => {
        const p = planets.find(x => x.name === n);
        if (!p) return;
        const deg = Math.max(0, Math.min(30, +p.longitude_in_sign || 0));
        const h = minH + (maxH - minH) * deg / 30;
        const x = x0 + i * (colW + gap), y = baseY - h;
        const dg = dignity(p);
        const col = /उच्च/.test(dg) ? GOLD2 : /नीच/.test(dg) ? BAD : /(स्वराशि|मूलत्रिकोण)/.test(dg) ? GOOD : '#60a5fa';
        const cx = x + colW / 2;
        cols += '<ellipse cx="' + cx + '" cy="' + (baseY + 5) + '" rx="' + (colW * .62) + '" ry="7" fill="#000" opacity=".4"/>';
        cols += '<polygon points="' + (x + colW) + ',' + y + ' ' + (x + colW + 9) + ',' + (y - 9) + ' ' + (x + colW + 9) + ',' + (baseY - 9) + ' ' + (x + colW) + ',' + baseY + '" fill="' + col + '" opacity=".42"/>';
        cols += '<polygon points="' + x + ',' + y + ' ' + (x + 9) + ',' + (y - 9) + ' ' + (x + colW + 9) + ',' + (y - 9) + ' ' + (x + colW) + ',' + y + '" fill="' + col + '" opacity=".82"/>';
        cols += '<rect x="' + x + '" y="' + y + '" width="' + colW + '" height="' + h + '" rx="3" fill="' + col + '" opacity=".88" stroke="' + col + '" stroke-opacity=".95"/>';
        cols += '<rect x="' + (x + 5) + '" y="' + (y + 9) + '" width="4" height="' + Math.max(6, h - 18) + '" rx="2" fill="#ffffff" opacity=".25"/>';
        cols += T(cx, y - 16, pName(n), 18, '#ffffff', 700, 'middle');
        cols += T(cx, baseY + 24, sign(p.sign_number || 1), 16, MUT, 600, 'middle');
        cols += T(cx, baseY + 48, dms(deg).replace(/″$/, ''), 16, GOLD, 700, 'middle');
      });

      const groups = { karaka: [], maraka: [], sama: [] };
      planets.forEach(p => {
        const k = (p.relationship || '').toLowerCase();
        if (groups[k]) groups[k].push(pName(p.name));
      });

      const relBox = (() => {
        let s = '';
        const rows = [
          ['कारक ग्रह (शुभ फलदायी)', groups.karaka.join('  ·  ') || 'कुनै छैन', GOOD, '#0f291c', 'उन्नति, प्रतिष्ठा र कार्यसिद्धि दिने सहयोगी ग्रहहरू'],
          ['मारक ग्रह (सतर्कता चाहिने)', groups.maraka.join('  ·  ') || 'कुनै छैन', BAD, '#2b0f17', 'स्वास्थ्य, खर्च र वादविवादमा सचेत रहनुपर्ने ग्रहहरू'],
          ['सम ग्रह (तटस्थ/सन्तुलित)', groups.sama.join('  ·  ') || 'कुनै छैन', '#60a5fa', '#0f1d30', 'सन्तुलित, निष्पक्ष र कर्म अनुसार फल दिने ग्रहहरू']
        ];
        rows.forEach((r, idx) => {
          const ry = 644 + idx * 156;
          s += '<rect x="' + L + '" y="' + ry + '" width="' + W + '" height="142" rx="18" fill="' + r[3] + '" stroke="' + r[2] + '" stroke-opacity=".55" stroke-width="1.6"/>';
          s += '<rect x="' + L + '" y="' + (ry + 16) + '" width="6" height="110" rx="3" fill="' + r[2] + '"/>';
          s += T(L + 28, ry + 38, r[0], 21, r[2], 700);
          s += T(L + 28, ry + 82, r[1], 30, '#ffffff', 700);
          s += T(L + 28, ry + 120, r[4], 16, MUT, 500);
        });
        return s;
      })();

      push(no, title, 'ग्रह स्तम्भ', [
        header(no, title),
        graphEl(no, title, '३डी स्तम्भ चार्ट', [L, 172, W, 450], cols, 9.8),
        el(no, title, 'report', 'कारक मारक सम प्यानल', [L, 640, W, 480], relBox, 8.4)
      ], { priority: ORDER.pillars, key: 'card-05' });
    }

    /* ── CARD 06: यो वर्ष (This Year Forecast: Career, Love, Color, Gemstone, Number) ── */
    {
      const no = 6, title = 'यो वर्षको कुण्डली फल';
      const house10 = (((ls - 1) + 9) % 12) + 1;
      const lord10 = KUN_SIGN_LORD_ACTIVE[house10 - 1];
      const p10 = planets.find(x => x.name === lord10) || {};
      const house7 = (((ls - 1) + 6) % 12) + 1;
      const lord7 = KUN_SIGN_LORD_ACTIVE[house7 - 1];
      const p7 = planets.find(x => x.name === lord7) || {};

      const careerPhal = '१०औं भावेश ' + pName(lord10) + ' (' + sign(p10.sign_number || 1) + ' राशि) को प्रभावले कर्मक्षेत्रमा नयाँ अवसर, व्यापार-व्यवसायमा वृद्धि र लगनशीलताले प्रतिष्ठा प्राप्त हुने अनुकूल संकेत गर्दछ।';
      const lovePhal = '७औं भावेश ' + pName(lord7) + ' र शुक्रको स्थितिले सम्बन्धमा समझदारी, पारिवारिक सामञ्जस्य र प्रियजनको सहयोग मिल्नेछ। बोली र व्यवहारमा नम्रता राख्नु लाभदायक हुन्छ।';

      const lagnaLord = KUN_SIGN_LORD_ACTIVE[ls - 1];
      const colorMap = {
        'Sun': ['रातो तथा सुन्तला', '#ef4444'], 'Moon': ['सेतो तथा चम्किलो चाँदी', '#e2e8f0'],
        'Mars': ['गाढा रातो तथा सिन्दुरे', '#dc2626'], 'Mercury': ['पन्ना हरियो', '#22c55e'],
        'Jupiter': ['सुनौलो तथा पहेँलो', '#eab308'], 'Venus': ['सेतो, रेशमी तथा गुलाबी', '#f472b6'],
        'Saturn': ['गाढा नीलो तथा कालो', '#3b82f6'], 'Rahu': ['धुवाँलो तथा नीलो', '#818cf8'], 'Ketu': ['बहुरङ्गी तथा पहेँलो', '#f59e0b']
      };
      const gemMap = {
        'Sun': 'माणिक (Ruby)', 'Moon': 'मोती (Pearl)', 'Mars': 'मूँगा (Red Coral)',
        'Mercury': 'पन्ना (Emerald)', 'Jupiter': 'पुखराज (Yellow Sapphire)', 'Venus': 'हीरा वा ओपल (Diamond)',
        'Saturn': 'नीलम वा कटैला (Blue Sapphire)', 'Rahu': 'गोमेद (Hessonite)', 'Ketu': 'लहसुनिया (Cat\'s Eye)'
      };
      const numMap = { 'Sun': '१ र ९', 'Moon': '२ र ७', 'Mars': '९ र ३', 'Mercury': '५ र ६', 'Jupiter': '३, १ र ९', 'Venus': '६ र ५', 'Saturn': '८ र ४', 'Rahu': '४ र ८', 'Ketu': '७ र २' };

      const myColor = colorMap[lagnaLord] || colorMap['Sun'];
      const myGem = gemMap[lagnaLord] || 'माणिक';
      const myNum = numMap[lagnaLord] || '१, ३, ५';

      const forecastBox = (() => {
        let s = '';
        const items = [
          ['💼 १. पेशा र आम्दानी', careerPhal, GOLD],
          ['❤️ २. प्रेम तथा सम्बन्ध', lovePhal, '#f472b6'],
          ['🎨 ३. शुभ रंग', myColor[0] + ' (दैनिक कार्य तथा महत्वपूर्ण भेटघाटमा प्राथमिकता दिनुहोस्)', myColor[1]],
          ['💎 ४. शुभ रत्न', myGem + ' (विज्ञ ज्योतिषीको सल्लाहमा विधिवत धारण गर्नुहोस्)', '#6ee7ff'],
          ['🔢 ५. शुभ अंक', myNum + ' (नयाँ कार्य शुभारम्भ र शुभ निर्णयका लागि उत्तम अंक)', '#34d399']
        ];
        items.forEach((it, idx) => {
          const iy = 176 + idx * 190;
          s += cosmicCardBg(L, iy, W, 176, it[2], 18);
          s += T(L + 28, iy + 40, it[0], 23, it[2], 700);
          s += P(L + 28, iy + 76, it[1], 50, 19.5, 28, '#ffffff', 3);
        });
        return s;
      })();

      push(no, title, 'यो वर्षको फल', [
        header(no, title),
        el(no, title, 'report', 'यो वर्ष फल सूची', [L, 172, W, 960], forecastBox, 9.4)
      ], { priority: ORDER.thisYear, key: 'card-06' });
    }

    /* ── CARD 07: जन्मपत्रिका (कुण्डली निर्माण - Full Scrollable Document) ── */
    {
      const no = 7, title = 'जन्मपत्रिका (कुण्डली निर्माण)';
      const jp = (window.KunJanmapatrika && typeof window.KunJanmapatrika.build === 'function')
        ? window.KunJanmapatrika.build(data, meta, { x: L, y: 58, w: W })
        : { inner: '<text x="360" y="300" text-anchor="middle" fill="#f6d365">जन्मपत्रिका उपलब्ध छैन</text>', height: 1052, privacy: [] };
      const jpEl = el(no, title, 'report', 'जन्मपत्रिका (कुण्डली निर्माण) — पूर्ण दस्तावेज',
        [L, 58, W, 1052], jp.inner, 18,
        { scroll: true, jp: true, scrollBbox: [L, 58, W, jp.height] });
      if (window.KunJanmapatrika && window.KunJanmapatrika.apply) {
        window.KunJanmapatrika.apply(jpEl, jp);
      }
      if (jp.privacy && jp.privacy.length) {
        jpEl.privacy = jp.privacy.map(g => ({
          id: g.id, label: g.label,
          rects: (g.rects || []).map(r => ({ x: r.x, y: r.y + TOP_SAFE, w: r.w, h: r.h }))
        }));
      }
      push(no, title, 'जन्मपत्रिका', [jpEl], { priority: ORDER.janmapatrika, key: 'card-07', gap: .7 });
      const it = items[items.length - 1];
      it.scrollDur = 32;
      it.scrollDelay = .8;
      it.hideScrollBar = true;
    }

    /* ── CARD 08: यो वर्ष जीवनमा आइपर्ने कठिनाइहरु र समाधान ── */
    {
      const no = 8, title = 'कठिनाइ र समाधान';
      const remediesBox = (() => {
        let s = '';
        const items = [
          [
            '⚠️ कार्यक्षेत्रमा तनाव तथा अनावश्यक चुनौती',
            'कर्मक्षेत्रमा अचानक कार्यभार थपिने, सहकर्मीसँग असमझदारी वा ढिलासुस्ती हुन सक्ने सम्भावना।',
            '✨ शास्त्रीय समाधान: प्रत्येक शनिबार पीपलमा जल चढाउने, कुलदेवताको नियमित स्मरण र नित्य बिहान सूर्यलाई तामाको लोटाबाट अर्घ्य अर्पण गर्नुहोस्।'
          ],
          [
            '⚠️ आर्थिक खर्चमा असन्तुलन तथा लगानीमा सतर्कता',
            'अनावश्यक खर्च बढ्ने, ऋण वा ठूलो आर्थिक लगानीमा हतार गर्दा घाटा हुन सक्ने जोखिम।',
            '✨ शास्त्रीय समाधान: बुधबार हरियो मुगको दाल वा हरियो घाँस गाईलाई खुवाउने र श्रीसूक्त पाठ वा लक्ष्मीजीको आराधना गर्नुहोस्।'
          ],
          [
            '⚠️ स्वास्थ्य र पारिवारिक सम्बन्धमा उतारचढाव',
            'मानसिक अशान्ति, निन्द्राको कमी वा परिवारका सदस्यसँग स-साना कुरामा मनमुटाव।',
            '✨ शास्त्रीय समाधान: प्रत्येक सोमबार शिवजीलाई दुग्ध-जलाभिषेक गर्ने, "ॐ नमः शिवाय" मन्त्र नित्य १०८ पटक जप गर्नुहोस्।'
          ]
        ];

        items.forEach((it, idx) => {
          const iy = 176 + idx * 316;
          s += cosmicCardBg(L, iy, W, 302, BAD, 18);
          s += T(L + 28, iy + 42, it[0], 23, '#ff8a98', 700);
          s += P(L + 28, iy + 78, it[1], 50, 18.5, 27, '#f4f6fb', 2);
          s += '<line x1="' + (L + 24) + '" y1="' + (iy + 144) + '" x2="' + (R - 24) + '" y2="' + (iy + 144) + '" stroke="#2b3e6b" stroke-width="1.3"/>';
          s += T(L + 28, iy + 180, 'वैदिक समाधान (शास्त्रीय उपाय):', 21, GOOD, 700);
          s += P(L + 28, iy + 216, it[2], 50, 19, 28, '#b9f6d9', 3);
        });
        return s;
      })();

      push(no, title, 'कठिनाइ र उपाय', [
        header(no, title),
        el(no, title, 'report', 'कठिनाइ समाधान सूची', [L, 172, W, 960], remediesBox, 9.4)
      ], { priority: ORDER.remedies, key: 'card-08' });
    }

    /* ── CARD 09: कुण्डलीमा भएका शुभ योग र फल ── */
    {
      const no = 9, title = 'कुण्डलीमा शुभ योगहरू';
      const goodYogas = yogaRows(data.parashara_yogas, true);

      const yogasBox = (() => {
        let s = '';
        if (goodYogas.length) {
          const shown = goodYogas.slice(0, 4);
          shown.forEach((yg, idx) => {
            const yy = 176 + idx * 236;
            const accent = idx % 2 ? GOOD : GOLD2;
            s += cosmicCardBg(L, yy, W, 222, accent, 18);
            s += T(L + 28, yy + 44, ne(idx + 1) + '. ' + (yg.nepali || yg.name || 'शुभ योग'), 26, GOLD, 700);
            s += T(R - 28, yy + 44, String(yg.category || 'राजयोग').toUpperCase(), 17, accent, 700, 'end');
            s += P(L + 28, yy + 88, yg.result_ne || yg.result || yg.cause_ne || 'शुभ फल प्राप्त हुनेछ।', 50, 19.5, 29, '#ffffff', 4);
          });
        } else {
          s += cosmicCardBg(L, 260, W, 300, GOLD, 20);
          s += T(360, 360, 'कुण्डलीमा विशेष ग्रह बल उपस्थित छ', 28, GOLD, 700, 'middle');
          s += P(360, 410, 'यस कुण्डलीमा ग्रहहरूको पारस्परिक दृष्टि र केन्द्र-त्रिकोण सम्बन्धले सामान्य जीवनमा प्रगति, उन्नति र यश सुनिश्चित गर्दछ।', 46, 20, 30, '#ffffff', 4);
        }
        return s;
      })();

      push(no, title, 'शुभ योगहरू', [
        header(no, title),
        el(no, title, 'report', 'शुभ योग सूची', [L, 172, W, 960], yogasBox, 9.2)
      ], { priority: ORDER.yogas, key: 'card-09' });
    }

    /* ── CARD 10: युवापुस्ताका ५ प्रमुख ज्योतिषीय प्रश्नोत्तर ── */
    {
      const no = 10, title = 'युवा पुस्ताका ज्योतिषीय प्रश्न';

      const house10 = (((ls - 1) + 9) % 12) + 1;
      const lord10 = KUN_SIGN_LORD_ACTIVE[house10 - 1];

      const q1Ans = '९औं (भाग्य) र १२औं (विदेश) भावको सम्बन्ध तथा चन्द्र/राहुको प्रभावले वैदेशिक अध्ययन, यात्रा र करियरमा अत्यन्त उच्च सम्भावना देखाउँछ। प्रयास गरेमा सफलता मिल्नेछ।';
      const q2Ans = '१०औं भावेश ' + pName(lord10) + ' को प्रभाव अनुसार व्यवस्थापन, प्रविधि, व्यापार वा प्रशासनिक क्षेत्रमा लाग्दा स्थायित्व, मान-प्रतिष्ठा र छिटो उन्नति हुनेछ।';
      const q3Ans = '५औं र ७औं भावको स्थितिले आपसी समझदारी, बौद्धिक तालमेल र मन मिल्ने जीवनसाथीसँग सुखी दाम्पत्य जीवन रहने प्रबल योग देखाउँछ।';
      const q4Ans = 'वर्तमान सक्रिय दशा र आगामी बृहस्पतिको अनुकूल गोचरले आगामी समयमा नयाँ अवसर, आर्थिक फड्को र भाग्य चम्किने उत्कृष्ट समय सुरु हुनेछ।';
      const q5Ans = '२औं (धन) र ११औं (लाभ) भावको अध्ययन अनुसार आफ्नै परिश्रम र योजनाबद्ध लगानीले ३० वर्षपछि दीर्घकालीन धन संचय र आफ्नै घर-सम्पत्ति जोडिनेछ।';

      const qaBox = (() => {
        let s = '';
        const qList = [
          ['✈️ १. म विदेश (Study/PR/Job) जान पाउँछु कि पाउँदिनँ?', q1Ans, '#6ee7ff'],
          ['💼 २. मेरो करियर कुन क्षेत्रमा सबैभन्दा सफल हुन्छ?', q2Ans, GOLD],
          ['💍 ३. मेरो प्रेम विवाह कि मागी विवाह? दाम्पत्य कस्तो रहला?', q3Ans, '#f472b6'],
          ['⭐ ४. मेरो जीवनको "Golden Time" (भाग्य चम्किने समय) कहिले?', q4Ans, '#34d399'],
          ['💰 ५. मेरो आर्थिक स्थिति र धन सम्पत्ति कस्तो रहला?', q5Ans, '#c4b5fd']
        ];
        qList.forEach((q, idx) => {
          const qy = 176 + idx * 190;
          s += cosmicCardBg(L, qy, W, 178, q[2], 18);
          s += T(L + 28, qy + 40, q[0], 22, q[2], 700);
          s += P(L + 28, qy + 76, '👉 उत्तर: ' + q[1], 50, 19.5, 28, '#ffffff', 3);
        });
        return s;
      })();

      push(no, title, 'युवा प्रश्नोत्तर', [
        header(no, title),
        el(no, title, 'report', 'युवा प्रश्नोत्तर सूची', [L, 172, W, 960], qaBox, 9.6)
      ], { priority: ORDER.youthQA, key: 'card-10' });
    }

    /* ── CARD 11: ज्योतिष विज्ञापन तथा परामर्श (Astrologer Advertisement) ── */
    {
      const no = 11, title = 'ज्योतिषीय परामर्श';
      const astroName = String(meta.astrologer_name || '').trim() || 'ज्योतिष पण्डित शिवराम पराजुली';
      const waRaw = String(meta.whatsapp_number || '').trim();
      const numText = waRaw ? ne(waRaw) : '९८४७४५२९०६';
      const waDigits = waRaw.replace(/\D/g, '') || '9847452906';
      const waUrl = 'https://wa.me/' + (waDigits.length === 10 ? '977' + waDigits : waDigits);
      const nameFs = astroName.length <= 26 ? 34 : astroName.length <= 34 ? 29 : 25;

      const idY = 170, idH = 120;
      let ident = cosmicCardBg(L, idY, W, idH, GOLD, 20);
      ident += '<circle cx="116" cy="230" r="34" fill="#132446" stroke="' + GOLD + '" stroke-opacity=".8" stroke-width="1.6"/>';
      ident += T(116, 230, 'ॐ', 34, GOLD, 700, 'middle');
      ident += T(168, 218, astroName, nameFs, GOLD, 700);
      ident += T(168, 258, 'वैदिक ज्योतिष · कुण्डली विश्लेषण · प्रत्यक्ष परामर्श', 18, MUT, 500);

      const chipY = 306, chipH = 82, chipW = 194, chipGap = 11;
      const chipDefs = [
        ['०१', 'कुण्डली निर्माण'],
        ['०२', 'दशा विश्लेषण'],
        ['०३', 'शास्त्रीय उपाय']
      ];
      let chips = '';
      chipDefs.forEach((c, i) => {
        const cx = L + i * (chipW + chipGap);
        chips += cosmicCardBg(cx, chipY, chipW, chipH, GOLD, 16);
        chips += '<circle cx="' + (cx + 36) + '" cy="' + (chipY + chipH / 2) + '" r="20" fill="#132446" stroke="' + GOLD + '" stroke-opacity=".5" stroke-width="1.2"/>';
        chips += T(cx + 36, chipY + chipH / 2, c[0], 16, GOLD, 700, 'middle');
        chips += T(cx + 66, chipY + chipH / 2, c[1], 18, '#ffffff', 600);
      });

      let wa = '<defs><linearGradient id="waGrad14" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#145233"/><stop offset="1" stop-color="#0a2a1a"/></linearGradient></defs>';
      wa += '<rect x="90" y="404" width="540" height="156" rx="78" fill="url(#waGrad14)" stroke="#25D366" stroke-opacity=".7" stroke-width="2"/>';
      wa += '<rect x="100" y="414" width="520" height="136" rx="68" fill="none" stroke="#ffffff" stroke-opacity=".08" stroke-width="1.2"/>';
      wa += '<circle cx="170" cy="482" r="48" fill="#25D366"/>';
      wa += '<g transform="translate(170,482) scale(1.4) translate(-58,-52)">';
      wa += '<path d="M46 68l4-12a22 22 0 1 1 8 8l-12 4z" fill="#0b2418" opacity=".18"/>';
      wa += '<path d="M58 33c-10.5 0-19 8.5-19 19 0 3.6 1 7 2.8 9.9L39 72l10.4-2.7A19 19 0 1 0 58 33zm0 34.4c-8.5 0-15.4-6.9-15.4-15.4S49.5 36.6 58 36.6 73.4 43.5 73.4 52 66.5 67.4 58 67.4z" fill="#ffffff"/>';
      wa += '<path d="M65.5 56.2c-.3-.2-1.9-.9-2.2-1-.3-.1-.5-.2-.7.1-.2.3-.8 1-1 1.2-.2.2-.4.3-.7.1-.3-.1-1.2-.4-2.3-1.4-.9-.8-1.5-1.7-1.7-2-.1-.3 0-.5.1-.6l.5-.6c.2-.2.2-.3.3-.5.1-.2 0-.4 0-.5l-1-2.3c-.3-.7-.6-.6-.9-.6h-.8c-.3 0-.7.1-1 .5-.3.3-1.3 1.3-1.3 3.2s1.3 3.7 1.5 4c.2.2 2.6 4 6.3 5.5 2.2.9 3.1 1 4.2.8.6-.1 1.9-.8 2.2-1.5.3-.8.3-1.4.2-1.5-.1-.2-.3-.2-.6-.4z" fill="#ffffff"/>';
      wa += '</g>';
      wa += '<circle cx="586" cy="482" r="20" fill="none" stroke="#ffffff" stroke-opacity=".3" stroke-width="1.4"/>';
      wa += '<path d="M582 473l8 9-8 9" fill="none" stroke="#ffffff" stroke-opacity=".95" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>';
      wa += T(236, 452, 'WhatsApp मा सम्पर्क गर्नुहोस्', 19, '#bbf7d0', 600);
      wa += T(236, 496, numText, 40, '#ffffff', 700);
      wa += T(236, 534, 'छिटो जवाफ · सिधै म्यासेज पठाउनुहोस्', 16, '#86efac', 500);

      const adBox = [L, 580, W, 490];
      let adInner = '<defs><radialGradient id="heroGlow14"><stop offset="0" stop-color="' + GOLD + '" stop-opacity=".22"/><stop offset="1" stop-color="' + GOLD + '" stop-opacity="0"/></radialGradient></defs>';
      adInner += '<rect x="' + adBox[0] + '" y="' + adBox[1] + '" width="' + adBox[2] + '" height="' + adBox[3] + '" rx="20" fill="#0b1730" fill-opacity=".94" stroke="' + GOLD + '" stroke-opacity=".55" stroke-width="1.6"/>';
      adInner += '<rect x="' + (adBox[0] + 12) + '" y="' + (adBox[1] + 12) + '" width="' + (adBox[2] - 24) + '" height="' + (adBox[3] - 24) + '" rx="15" fill="none" stroke="' + GOLD + '" stroke-opacity=".18"/>';
      adInner += '<circle cx="360" cy="700" r="140" fill="url(#heroGlow14)"/>';
      adInner += '<circle cx="360" cy="700" r="92" fill="none" stroke="' + GOLD + '" stroke-opacity=".22"/>';
      adInner += '<circle cx="360" cy="700" r="64" fill="none" stroke="' + GOLD + '" stroke-opacity=".3"/>';
      for (let d = 0; d < 12; d++) {
        const a = d * Math.PI / 6;
        adInner += '<circle cx="' + (360 + Math.cos(a) * 92).toFixed(1) + '" cy="' + (700 + Math.sin(a) * 92).toFixed(1) + '" r="' + (d % 3 === 0 ? 3.6 : 2.2) + '" fill="' + GOLD + '" fill-opacity=".65"/>';
      }
      adInner += '<path d="M360 655l12 34 34 11-34 12-12 34-12-34-34-12 34-11z" fill="' + GOLD + '" fill-opacity=".95"/>';
      adInner += '<path d="M265 700h-16M455 700h16" stroke="' + GOLD + '" stroke-opacity=".55" stroke-width="1.8"/>';
      adInner += T(360, 836, 'ज्योतिषीय परामर्श केन्द्र', 34, GOLD, 700, 'middle');
      adInner += '<line x1="260" y1="860" x2="460" y2="860" stroke="' + GOLD + '" stroke-opacity=".5" stroke-width="1.6"/>';
      adInner += T(360, 894, 'कुण्डली निर्माण · ग्रह बल · दशा विश्लेषण', 19, '#f4f8ff', 600, 'middle');
      adInner += T(360, 930, 'जीवनका महत्त्वपूर्ण निर्णयहरूमा शास्त्रीय वैदिक मार्गदर्शन', 17, MUT, 500, 'middle');
      adInner += T(360, 978, '॥ सर्वे भवन्तु सुखिनः सर्वे सन्तु निरामयाः ॥', 18, GOLD2, 600, 'middle');

      const trust = '<rect x="' + L + '" y="1084" width="' + W + '" height="52" rx="26" fill="#0b2418" stroke="#25D366" stroke-opacity=".35" stroke-width="1.3"/>' +
        '<circle cx="86" cy="1110" r="6" fill="' + GOOD + '"/>' +
        T(360, 1110, '१००% गोपनीयता · शास्त्रीय प्रमाण · प्रत्यक्ष अनुभव', 17, '#9fe8bd', 600, 'middle');

      push(no, title, 'परामर्श', [
        header(no, title),
        el(no, title, 'heading', 'ज्योतिषीय परिचय', [L, idY, W, idH], ident, 6.4),
        el(no, title, 'cards', 'सेवा सूची', [L, chipY, W, chipH], chips, 7),
        el(no, title, 'banner', 'WhatsApp सम्पर्क', [90, 404, 540, 156], wa, 7.4),
        el(no, title, 'art', 'ज्योतिषीको फोटो', adBox, adInner, 7.4, { ad: true, adSrc: '' }),
        el(no, title, 'note', 'विश्वास पट्टी', [L, 1084, W, 52], trust, 6.4)
      ], { priority: ORDER.consult, key: 'card-11' });
      items[items.length - 1].hotspot = [90, 404 + TOP_SAFE + (items[items.length - 1].autoShift || 0), 540, 156];
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
