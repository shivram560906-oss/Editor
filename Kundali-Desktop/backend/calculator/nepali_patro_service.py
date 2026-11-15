"""
backend/calculator/nepali_patro_service.py

Official Nepali Patro synchronization and caching service.
Fetches, decrypts, and caches official daily Panchang from Nepali Patro API
(https://api.nepalipatro.com.np/fetch/panchanga) using AES-CBC decryption.
Maintains a local SQLite cache for instant, zero-latency offline access.
"""
from __future__ import annotations

import base64
import datetime
import json
import os
import pathlib
import re
import sqlite3
from typing import Any, Dict, Optional

import requests
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# ── AES Decryption Key for Nepali Patro API ─────────────────────────────────
# The public web client uses this shared key.  It can be overridden for a
# deployment that has been issued a different key, but it is not a secret that
# protects user data, so it is kept as a working default.
_KEY_B64 = (
    os.environ.get("NEPALI_PATRO_API_KEY")
    or "9E4mk3Woz7tN8Ic9LRZYG5ipy7971B62egK199a0d+c="
).strip()
_KEY_BYTES = base64.b64decode(_KEY_B64)
_API_URL = os.environ.get(
    "NEPALI_PATRO_API_URL", "https://api.nepalipatro.com.np/fetch/panchanga"
)

# ── Cache Database Path ─────────────────────────────────────────────────────
_appdata = pathlib.Path(os.environ.get("LOCALAPPDATA", pathlib.Path.home())) / "ShivramJyotish"
_appdata.mkdir(parents=True, exist_ok=True)
_DB_PATH = str((_appdata / "nepali_patro_cache.db").resolve())

DEV_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
ASCII_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")


def _to_ascii_digits(s: str) -> str:
    return str(s or "").translate(DEV_DIGITS)


def _to_devanagari_digits(s: str) -> str:
    return str(s or "").translate(ASCII_DIGITS)


def _init_db():
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS patro_cache (
                    ad_date TEXT PRIMARY KEY,
                    bs_date TEXT,
                    raw_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
    except Exception:
        pass


_init_db()


def _decrypt_payload(enc_data: str) -> Optional[Dict[str, Any]]:
    """Decrypt the AES-CBC encrypted response from Nepali Patro API."""
    try:
        if isinstance(enc_data, str):
            try:
                raw_json = base64.b64decode(enc_data).decode("utf-8")
                s = json.loads(raw_json)
            except Exception:
                s = json.loads(enc_data)
        else:
            s = enc_data

        iv = base64.b64decode(s["iv"])
        ciphertext = base64.b64decode(s["value"])

        cipher = Cipher(algorithms.AES(_KEY_BYTES), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()

        dec_bytes = bytes([b for b in padded if b != 0])
        if dec_bytes and dec_bytes[-1] <= 16:
            pad_len = dec_bytes[-1]
            if all(b == pad_len for b in dec_bytes[-pad_len:]):
                dec_bytes = dec_bytes[:-pad_len]

        text = dec_bytes.decode("utf-8", errors="ignore")
        text = re.sub(r'[\x00-\x19]+', '', text)
        return json.loads(text)
    except Exception:
        return None


def fetch_from_api(ad_date: datetime.date, timeout: float = 3.0) -> Optional[Dict[str, Any]]:
    """Fetch and decrypt live panchang for the given Gregorian date."""
    try:
        fields = {
            "year": str(ad_date.year),
            "month": f"{ad_date.month:02d}",
            "day": f"{ad_date.day:02d}",
            "time": "12:00:00",
        }
        headers = {
            # Identify the application honestly instead of spoofing a browser.
            "User-Agent": "ShivramJyotish/2.0",
            "Accept": "application/json, text/plain, */*",
        }
        resp = requests.post(_API_URL, data=fields, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            return _decrypt_payload(resp.text)
    except Exception:
        pass
    return None


def get_cached(date_str: str) -> Optional[Dict[str, Any]]:
    """Retrieve raw json from local SQLite cache."""
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT raw_json FROM patro_cache WHERE ad_date = ?", (date_str,))
            row = cur.fetchone()
            if row and row[0]:
                return json.loads(row[0])
    except Exception:
        pass
    return None


def save_to_cache(date_str: str, bs_date_str: str, data: Dict[str, Any]):
    """Persist panchang into local SQLite cache."""
    try:
        with sqlite3.connect(_DB_PATH) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO patro_cache (ad_date, bs_date, raw_json) VALUES (?, ?, ?)",
                (date_str, bs_date_str, json.dumps(data, ensure_ascii=False)),
            )
            conn.commit()
    except Exception:
        pass


def seed_cache_from_dataset(dataset_path: str):
    """Seed the SQLite cache from an existing dataset JSON file."""
    if not os.path.exists(dataset_path):
        return
    try:
        with open(dataset_path, "r", encoding="utf-8") as f:
            records = json.load(f)
        if isinstance(records, list):
            for r in records:
                ad = r.get("ad_date")
                bs = r.get("bs_date", "")
                if ad and "tithi_name" in r:
                    save_to_cache(ad, bs, r)
        elif isinstance(records, dict):
            for k, r in records.items():
                if isinstance(r, dict):
                    ad = r.get("ad_date") or k
                    bs = r.get("bs_date", "")
                    if "tithi_name" in r:
                        save_to_cache(ad, bs, r)
    except Exception:
        pass


# Seed local cache from existing project scratch datasets if present
_root_dir = pathlib.Path(__file__).parent.parent.parent
_scratch_5yr = _root_dir / "scratch" / "nepali_patro_5yr_dataset.json"
_scratch_sep = _root_dir / "scratch" / "patro_sep_17_23.json"
if _scratch_5yr.exists():
    seed_cache_from_dataset(str(_scratch_5yr))
if _scratch_sep.exists():
    seed_cache_from_dataset(str(_scratch_sep))


def _parse_time_from_str(s: str) -> Optional[str]:
    """Extract 'HH:MM:00' from a string like 'अष्टमी, १४:१७ बजेपछि नवमी'."""
    if not s:
        return None
    s_en = _to_ascii_digits(s)
    m = re.search(r'(\d{1,2}):(\d{2})', s_en)
    if m:
        h = int(m.group(1))
        mi = int(m.group(2))
        return f"{h:02d}:{mi:02d}:00"
    return None


def _format_planet_from_patro(val: str, use_devanagari: bool = True) -> Dict[str, Any]:
    """Convert Patro format '5|1|13|3' to structured planet dict."""
    if not val or not isinstance(val, str):
        return {}
    val_en = _to_ascii_digits(val.strip().replace(":", "|").replace("/", "|"))
    parts = val_en.split("|")
    if len(parts) < 2:
        return {}
    try:
        r = int(parts[0])
        d = int(parts[1])
        m = int(parts[2]) if len(parts) > 2 else 0
        s = int(parts[3]) if len(parts) > 3 else 0
        dec_deg = r * 30.0 + d + m / 60.0 + s / 3600.0
        fmt_ne = f"{_to_devanagari_digits(str(r))}|{_to_devanagari_digits(str(d))}|{_to_devanagari_digits(str(m))}|{_to_devanagari_digits(str(s))}"
        fmt_en = f"{r}|{d}|{m}|{s}"
        return {
            "longitude": dec_deg,
            "rashi_index": r,
            "degrees": d,
            "minutes": m,
            "seconds": s,
            "formatted": fmt_ne if use_devanagari else fmt_en,
            "formatted_en": fmt_en,
        }
    except Exception:
        return {}


def get_nepali_patro_panchang(ad_date: datetime.date) -> Optional[Dict[str, Any]]:
    """Retrieve official Nepali Patro panchang for the given date (from cache or API)."""
    date_str = ad_date.isoformat()
    raw = get_cached(date_str)
    if not raw:
        raw = fetch_from_api(ad_date)
        if raw:
            save_to_cache(date_str, raw.get("bs", ""), raw)

    if not raw:
        return None

    # Parse and structure fields
    tithi_raw = raw.get("tithi_name", "")
    nak_raw = raw.get("nakshatra", "")
    yog_raw = raw.get("yog", "")
    kar_raw = raw.get("karan", "")

    # Tithi
    t_end = _parse_time_from_str(tithi_raw)
    t_parts = tithi_raw.split(",") if "," in tithi_raw else [tithi_raw]
    t_cur = t_parts[0].strip()
    t_next = ""
    if len(t_parts) > 1:
        nm = re.search(r'बजे(?:पछि|उप्रान्त)\s*([^\s]+)', t_parts[1])
        if nm:
            t_next = nm.group(1).strip()

    # Nakshatra
    n_end = _parse_time_from_str(nak_raw)
    n_parts = nak_raw.split(",") if "," in nak_raw else [nak_raw]
    n_cur = n_parts[0].strip()
    n_next = ""
    if len(n_parts) > 1:
        nm = re.search(r'बजे(?:पछि|उप्रान्त)\s*([^\s]+)', n_parts[1])
        if nm:
            n_next = nm.group(1).strip()

    # Yoga
    y_end = _parse_time_from_str(yog_raw)
    y_parts = yog_raw.split(",") if "," in yog_raw else [yog_raw]
    y_cur = y_parts[0].strip()
    y_next = ""
    if len(y_parts) > 1:
        nm = re.search(r'बजे(?:पछि|उप्रान्त)\s*([^\s]+)', y_parts[1])
        if nm:
            y_next = nm.group(1).strip()

    # Karana root name from sunrise
    # Format e.g. "तैतिल, ०५:२१ बजेपछि कौलव, १६:२२ बजेउप्रान्त वणिज"
    k_parts = [p.strip() for p in kar_raw.split(",") if p.strip()]
    k_cur = k_parts[1] if len(k_parts) >= 2 else (k_parts[0] if k_parts else "")
    # extract clean karana name
    km = re.search(r'(?:बजे(?:पछि|उप्रान्त)\s*)?([^\s,]+)', k_cur)
    if km:
        k_cur = km.group(1).strip()

    # Planets
    planets_map = {
        "Sun": _format_planet_from_patro(raw.get("surya", "")),
        "Moon": _format_planet_from_patro(raw.get("chandra", "")),
        "Mars": _format_planet_from_patro(raw.get("mangal", "")),
        "Mercury": _format_planet_from_patro(raw.get("budha", "")),
        "Jupiter": _format_planet_from_patro(raw.get("brihaspati", "")),
        "Venus": _format_planet_from_patro(raw.get("sukra", "")),
        "Saturn": _format_planet_from_patro(raw.get("sani", "")),
        "Rahu": _format_planet_from_patro(raw.get("rahu", "")),
    }
    # Ketu is opposite Rahu (+6 signs = 180°)
    if planets_map["Rahu"] and "longitude" in planets_map["Rahu"]:
        r_lon = planets_map["Rahu"]["longitude"]
        k_lon = (r_lon + 180.0) % 360.0
        kr = int(k_lon // 30)
        kd = int(k_lon % 30)
        km = int(((k_lon % 30) - kd) * 60)
        ks = int(round(((((k_lon % 30) - kd) * 60) - km) * 60))
        fmt_ne = f"{_to_devanagari_digits(str(kr))}|{_to_devanagari_digits(str(kd))}|{_to_devanagari_digits(str(km))}|{_to_devanagari_digits(str(ks))}"
        fmt_en = f"{kr}|{kd}|{km}|{ks}"
        planets_map["Ketu"] = {
            "longitude": k_lon,
            "rashi_index": kr,
            "degrees": kd,
            "minutes": km,
            "seconds": ks,
            "formatted": fmt_ne,
            "formatted_en": fmt_en,
        }

    # Dinman & Sun
    sr_time = raw.get("sunrise", "०५:५१").replace("AM", "").replace("PM", "").strip()
    ss_time = raw.get("sunset", "१८:०१").replace("AM", "").replace("PM", "").strip()
    dinman_ghati = raw.get("dinman", "")
    dinman_diff = raw.get("dinman_diff", "")
    
    # Belantar & Kranti
    kranti_str = raw.get("kranti", "")
    belantar_str = raw.get("belantar", "")

    return {
        "source": "NEPALI_PATRO_OFFICIAL",
        "tithi_nepali": t_cur,
        "tithi_end_time": t_end,
        "next_tithi_nepali": t_next,
        "nakshatra_nepali": n_cur,
        "nakshatra_end_time": n_end,
        "next_nakshatra_nepali": n_next,
        "yoga_nepali": y_cur,
        "yoga_end_time": y_end,
        "next_yoga_nepali": y_next,
        "karana_nepali": k_cur,
        "karana_full_nepali": kar_raw,
        "sunrise": sr_time,
        "sunset": ss_time,
        "dinman": dinman_diff or dinman_ghati,
        "dinman_ghati": dinman_ghati,
        "dinman_ghati_nepali": _to_devanagari_digits(dinman_ghati),
        "kranti": kranti_str,
        "belantar": belantar_str,
        "velantara": belantar_str,
        "chandrarashi": raw.get("chandrarashi", ""),
        "anandadi_yoga": raw.get("anandiyog", ""),
        "din_vishesh": raw.get("parba", "") or raw.get("brataparva", ""),
        "planetary_positions": planets_map,
        "samvatsara": raw.get("sambatsar", ""),
        "nepal_samvat": {
            "year": raw.get("nsyear", ""),
            "era": raw.get("nsmonth", ""),
        },
        "raw": raw,
    }
