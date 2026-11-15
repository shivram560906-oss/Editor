# कुण्डली निर्माण — Janmapatrika Data Mapping

## Scope and invariants

This document is the implementation contract for the new, isolated **कुण्डली निर्माण** module. Existing planetary, Panchanga, Varga, Dasha, Yoga, and report calculations are consumed read-only and are not modified. The supplied references are reproduced as one continuous traditional composition on a single 148 mm-wide sheet whose height grows to contain all prose without a page break.

Fallback policy for every displayed value:

1. Use an existing calculated/current-Kundali value.
2. Derive a deterministic calendar or presentation value from the birth metadata.
3. Use a persisted Additional Janmapatrika Details value where calculation is impossible.
4. Render `उपलब्ध छैन` rather than an empty cell if a legacy/open chart lacks the required value.

## Data mapping

| संस्कृत शीर्षक | Database Field Name | Data Source | Calculation Method | Required / New Field | Validation Rule |
|---|---|---|---|---|---|
| श्रीशालिवाहनीय शकः | derived `shaka_year` | Current Kundali `metadata.birth_date` | Gregorian year − 78; year-boundary presentation fallback | Derived, not persisted | Integer, four digits |
| श्रीविक्रमादित्य संवत् | derived `vikram_samvat` | Current Kundali birth date / BS converter | Existing AD→BS conversion; use BS year | Derived, not persisted | Integer in supported BS calendar range |
| ईसवीय सन् | derived `gregorian_year` | `metadata.birth_date` | Parse Gregorian year | Derived, not persisted | ISO `YYYY-MM-DD` |
| संवत्सर | derived `samvatsara` | `panchang.samvatsara` | Existing 60-year Samvatsara calculation | Existing calculation | Non-empty Unicode text |
| उत्तरायण / दक्षिणायन | derived `ayana` | `metadata.birth_date` | Tropical seasonal boundary approximation: Uttarayana Jan 14–Jul 15, otherwise Dakshinayana | Derived | Valid birth date |
| ऋतु | derived `ritu` | `metadata.birth_date` | Six traditional two-month seasonal bands from Gregorian month | Derived | One of वसन्त, ग्रीष्म, वर्षा, शरद्, हेमन्त, शिशिर |
| मास | derived `lunar_month` | Current Panchanga + birth date | Existing Panchanga month status when available; deterministic Nepali month-name fallback from birth month | Derived | Non-empty Unicode text |
| पक्ष | derived `paksha` | `panchang.tithi.paksha_nepali` | Existing birth Panchanga | Existing calculation | शुक्लपक्ष or कृष्णपक्ष |
| वार | derived `vara` | `panchang.vara.nepali` | Existing local civil weekday calculation | Existing calculation | Valid weekday name |
| तिथि | derived `tithi` | `panchang.tithi.birth_nepali`, fallback `panchang.tithi.nepali` | Existing birth-instant Tithi takes priority | Existing calculation | Non-empty Unicode text |
| नक्षत्र | derived `nakshatra` | `panchang.nakshatra.nepali` / `avakahada_chakra.nakshatra` | Existing birth-time Moon position | Existing calculation | One of 27 Nakshatras |
| चरण | derived `pada` | `panchang.nakshatra.pada` / `avakahada_chakra.pada` | Existing Nakshatra quarter calculation | Existing calculation | Integer 1–4 |
| योग | derived `yoga` | `panchang.yoga.birth_nepali`, fallback `panchang.yoga.nepali` | Existing birth-instant Yoga | Existing calculation | One of 27 Yogas |
| करण | derived `karana` | `panchang.karana.birth_nepali`, fallback `panchang.karana.nepali` | Existing birth-instant Karana | Existing calculation | Valid Karana name |
| लग्न | derived `lagna` | `lagna.sign_number`, `lagna.longitude_in_sign` | Existing sidereal Ascendant calculation | Existing calculation | Sign 1–12, longitude 0–30° |
| राशि | derived `moon_sign` | Moon entry in `planets` | Existing sidereal Moon sign | Existing calculation | Sign 1–12 |
| नवांश | derived `navamsha` | `vargas.D9` Lagna / first Lagna placement | Existing D9 Varga output | Existing calculation | Sign 1–12 or `उपलब्ध छैन` for legacy charts |
| देश | `country` | Birth Information input / city selection | Selected city country; persisted with chart details | New persisted column | Trimmed Unicode text, max 100 chars |
| जन्मस्थान | derived/persisted `birth_place` | `metadata.city`; record city | Existing selected city/current chart metadata | Additive persisted column | Trimmed Unicode text, max 200 chars |
| अक्षांश | `latitude` | `metadata.latitude` / `kundali_records.latitude` | Existing birth input | Existing field | −90 through +90 |
| देशान्तर | `longitude` | `metadata.longitude` / `kundali_records.longitude` | Existing birth input | Existing field | −180 through +180 |
| मानक समय | `timezone`, `timezone_id` | `metadata.timezone`, `metadata.timezone_id` | Existing historical timezone resolver | Existing numeric; additive ID persistence | UTC −12 through +14; IANA string max 100 |
| स्थानीय जन्म समय | `birth_time` | `metadata.birth_time` | Existing normalized local birth time | Existing field | `HH:MM` or `HH:MM:SS` |
| सूर्योदय | derived `sunrise` | `panchang.sunrise.time` | Existing location-aware sunrise calculation | Existing calculation | `HH:MM` |
| सूर्यास्त | derived `sunset` | `panchang.sunset.time` | Existing location-aware sunset calculation | Existing calculation | `HH:MM` |
| नामाक्षर | derived `name_akshara` | `avakahada_chakra.name_akshara` | Existing Nakshatra/Pada Avakahada lookup | Existing calculation | Unicode syllable or explicit unavailable text |
| गण | derived `gana` | `avakahada_chakra.gana` | Existing Avakahada lookup | Existing calculation | देव, मनुष्य, राक्षस or source spelling |
| योनि | derived `yoni` | `avakahada_chakra.yoni` | Existing Avakahada lookup | Existing calculation | Non-empty Unicode text |
| नाडी | derived `nadi` | `avakahada_chakra.nadi` | Existing Avakahada lookup | Existing calculation | आदि, मध्य, अन्त्य |
| वर्ण | derived `varna` | `avakahada_chakra.varna` | Existing Avakahada lookup | Existing calculation | Non-empty Unicode text |
| वश्य | derived `vashya` | `avakahada_chakra.vashya` | Existing Avakahada lookup | Existing calculation | Non-empty Unicode text |
| जातकको पूरा नाम | `full_name` | Additional Janmapatrika Details / existing `name` default | User input; defaults from current chart name | New persisted column | Required for new input; trimmed, 1–200 chars |
| बाबुको नाम | `father_name` | Additional Janmapatrika Details | User input | New persisted column | Trimmed Unicode text, max 200 chars; explicit unavailable fallback for legacy data |
| आमाको नाम | `mother_name` | Additional Janmapatrika Details | User input | New persisted column | Trimmed Unicode text, max 200 chars; explicit unavailable fallback for legacy data |
| गोत्र | `gotra` | Additional Janmapatrika Details | User input | New persisted column | Trimmed Unicode text, max 100 chars |
| थर | `surname` | Additional Janmapatrika Details | User input | New persisted column | Trimmed Unicode text, max 100 chars |
| कुल | `kula` | Additional Janmapatrika Details | User input | New persisted column | Trimmed Unicode text, max 100 chars |
| कुलदेवता | `kuladevata` | Additional Janmapatrika Details | User input | New persisted column | Trimmed Unicode text, max 200 chars |
| पति / पत्नीको नाम | `spouse_name` | Additional Janmapatrika Details | User input | New persisted column | Trimmed Unicode text, max 200 chars; conditionally applicable |
| वैवाहिक अवस्था | `marital_status` | Additional Janmapatrika Details | User selection | New persisted column | अविवाहित, विवाहित, विधवा/विधुर, सम्बन्धविच्छेद, अन्य |
| जात | `caste` | Additional Janmapatrika Details | User input | New persisted column | Trimmed Unicode text, max 100 chars |
| धर्म | `religion` | Additional Janmapatrika Details | User input | New persisted column | Trimmed Unicode text, max 100 chars |
| परिवारको विवरण | `family_details` | Additional Janmapatrika Details | User multiline input | New persisted text column | Trimmed Unicode text, max 2000 chars |

## Reference-line mapping and de-duplication

The single continuous sheet contains the Ganesh panel, invocation, Shaka/Vikram/Gregorian/Samvatsara opening, Panchanga prose, Lagna and Navamsha, location/time, family, Avakahada, sunrise/sunset, naming blessing, and the closing घात section. The module expresses these as ordered inline prose with dark-red calculated values, black Sanskrit prose, and gray dotted underlines, matching the supplied pale-green reference rather than a modern card/grid layout.

The latest user-supplied Unicode header supersedes the earlier transcription and is preserved exactly once:

> श्रीमङ्गलमूर्तये नमः
> आदित्याद्या ग्रहासर्वे सनक्षत्राः सराशयः ॥
> कुर्वन्तुमङ्गल तस्य यस्यैषा जन्मपत्रिका॥

## Persistence and API contract

The new columns are additive nullable columns on `kundali_records`, preserving all existing records. Record create/response schemas accept and return these fields. Current-chart calculation requests accept the presentation metadata only so it can travel with the open chart; no planetary or report formula receives or depends on it.

Migration `0003_janmapatrika_details` adds all 15 location and identity columns after the existing legacy schema. The configured workspace-root SQLite database was reconciled to revision `0002_auth_admin`, upgraded to `0003_janmapatrika_details`, and verified without changing the existing Kundali record count.

Persistence behavior follows the existing application boundary:

- Offline saves retain every Janmapatrika key in frontend `localStorage` records.
- `POST /api/records` calls create or update the same fields in `kundali_records`; no login or account is required.
- Duplicate matching uses the existing birth identity tuple and updates provided detail fields instead of creating another record.
- Reads and writes are single-user/local: every chart saved on the machine is visible and editable.
- The desktop app talks to the calculation engine in-process, so these API rules apply whether the optional local server is running or not.

## Delivered module boundaries

- `Janmapatrika.jsx` is a standalone, read-only, continuous-sheet renderer of the current `chartData` calculation result.
- `Janmapatrika.css` owns the pale-green A4 paper, double green frame, repeated four-sided maroon Swastik rails, traditional colors, dotted underlines, preview mode, responsive overflow, and print isolation.
- `App.jsx` copies submitted identity metadata into the open chart and restores it when a local saved record is loaded.
- Institutional sidebar and legacy chart menu actions both route `kundali_nirman` to the same renderer.
- Planetary, Panchanga, Avakahada, Varga, Dasha, Yoga, and report engines were not changed for this module.

## Output contract

- Typesetting: body prose is grouped into semantic passages ending at `॥`; browser wrapping, rather than artificial JSX line breaks, determines individual visual lines.
- Body measure: centered 112 mm text column inside the 148 mm sheet, providing approximately 18 mm of equal left/right whitespace and targeting 6–11 Devanagari words per automatically wrapped line while preserving dynamic-value integrity.
- Typography: one 12 pt Devanagari body size, 150% line height, and uniform 8 px paragraph margins; no minimum row height or artificial final-line stretching.
- Alignment: invocation verses are centered; all main Sanskrit/Nepali prose is justified with the final line left natural.
- Screen: desktop, laptop, and tablet preview of one continuous 148 mm-wide sheet; narrow viewports use contained horizontal scrolling so document proportions remain stable.
- Print: one continuous content-height sheet without an explicit page break, with print-only isolation and exact paper colors enabled. A physical printer may paginate long content according to its hardware and driver limits.
- PDF: client-side single-page export using a 148 mm width and a height calculated from the rendered document, with `html2canvas` scale `3`. This targets high-quality output, but physical 300 DPI cannot be guaranteed by a browser renderer or printer driver.
- Word: Word-compatible Unicode HTML exported with a `.doc` filename and embedded styles. It opens in Microsoft Word but is not a native Office Open XML `.docx` package.
- Empty legacy values: `उपलब्ध छैन`, never visually blank.

## Verification contract

Focused tests cover text trimming, blank normalization, maximum lengths, create/update behavior, single-user record visibility, and nullable legacy records. Validation also includes the Panchanga and Avakahada regression suites, frontend production build, touched-file ESLint checks, Python compilation, Alembic revision/schema inspection, and whitespace checks.
