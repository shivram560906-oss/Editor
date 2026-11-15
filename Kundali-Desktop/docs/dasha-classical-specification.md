# Dasha Classical Specification Boundary

This document defines what the unified dasha report may claim as calculated. It is a guard against presenting an implementation assumption as a classical result.

## Shared Contract

All enabled systems use a five-level tree:

`Mahadasha -> Antardasha -> Pratyantardasha -> Sookshmadasha -> Pranadasha`

Each calculated node must contain:

- `level` from 1 through 5
- `start` and `end` as ISO AD dates
- exact `start_bs` and `end_bs`, or an empty value when the calendar library cannot convert the date
- `is_partial` when the visible interval begins at birth rather than at the astronomical period boundary
- `is_active` derived from one injected reference date
- `children` when the next level is calculated

Required invariants:

- sibling intervals are contiguous
- every child is inside its parent
- the final child ends exactly at the parent end
- at most one active node exists per level on an active path
- repeated calculation with the same inputs and reference date is deterministic

The transport status is one of `ready`, `empty`, `unavailable`, `error`, or `no_chart`. An unavailable level or system must never receive fabricated dates, scores, or prediction text.

## Vimshottari

The existing Vimshottari calculator remains the compatibility baseline. Its legacy `dasha` field and current node shape must remain unchanged. Deep-level expansion may be improved only through an additive normalized field or an explicitly versioned mode.

The classical sequence and proportional subdivision rules are already represented by the current engine. Any full-tree change requires the existing regression guard and structural invariant tests to pass.

The Janmapatrika antardasha grid additionally consumes an additive `antardashas` list on every Vimshottari Mahadasha. It always contains the complete nine-lord cycle, including antardashas completed before birth (`is_before_birth: true`). The legacy `children` list continues to expose only the visible post-birth chain.

The printed grid is one continuous table with a single shared header row and one data row per Mahadasha:

- Vimshottari always renders ten independent columns (`दशा` plus the nine planets in fixed order); Yogini always renders nine (`दशा` plus the eight Yoginis in fixed order). No cell uses `colspan` or `rowspan`.
- The first column contains only row labels (`दशा` in the header, `बाँकी उमेर` in the data rows). A planet or Yogini name never appears in it.
- In the birth Mahadasha row, antardashas completed before birth are shown as `—`; the birth-time antardasha's actual remaining duration occupies its own lord's column. Every later Mahadasha row places each antardasha's cumulative value under that same lord's column.
- Values are cumulative from the native's birth and never reset at a Mahadasha or cycle boundary. They are the exact calendar difference between the birth date and each antardasha's calculated end date, so display rounding cannot accumulate.
- A period shorter than one complete month prints its remaining days (for example `१२ दिन`); all other values print whole years and months.
- The grid never prints “जन्म अघि”.
- Three Mahadasha rows are visible initially. A small `+` link in the last cell of the final visible row, and the `+` control below the table, reveal three more rows each. Vimshottari keeps every Mahadasha returned by the engine; Yogini keeps all three 36-year cycles (24 Mahadashas).

The same layout, cumulative-from-birth rule, and expansion behavior apply to the Yogini antardasha grid.

## Yogini

The legacy `yogini_dasha` field is preserved exactly for existing consumers. The additive normalized `yogini_dasha_five_level` field follows the supplied eight-Yogini, five-level rules.

- The Yogini order is Mangala, Pingala, Dhanya, Bhramari, Bhadrika, Ulka, Siddha, and Sankata.
- Their Mahadasha weights are 1, 2, 3, 4, 5, 6, 7, and 8 years, totaling a 36-year cycle.
- For nakshatra number `N` from Ashwini=1 through Revati=27, birth Yogini index is `((N + 3 - 1) mod 8) + 1`; zero-based implementation uses the equivalent offset.
- Birth balance is calculated from the Moon's elapsed arc-minutes within the 800-arc-minute nakshatra: elapsed is `D * elapsed / 800`, and remaining is `D * (800 - elapsed) / 800`.
- Mahadashas begin with the birth Yogini and continue cyclically through the eight-Yogini order.
- Each nested level begins from its parent Yogini and advances cyclically through the same order.
- Antardasha, Pratyantardasha, Sookshmadasha, and Pranadasha use the recursive formula `child = parent * child_weight / 36`.
- When birth falls inside a Mahadasha or child period, the conceptual period start is retained for the proportional calculation. Every child keeps its full `parent * child_weight / 36` duration; only the period that is active at birth is truncated at the birth date. Periods that ended before birth are omitted from the visible tree.
- The normalized tree exposes both the Yogini identity (`lord`/`yogini`) and the planetary interpretation identity (`planet_lord`). Sankata uses canonical planetary lord `Rahu` in the normalized field; the legacy `Rahu/Ketu` representation is unchanged.
- All five levels use contiguous date-only intervals, exact AD-to-BS conversion where supported, and deterministic cumulative boundaries. Very short date-only intervals may omit children when positive subdivision cannot be represented.

The normalized Yogini report is `ready` only when this calculated five-level tree is available. Its interpretation uses the shared chart-backed Dasha Phal presentation; no additional Yogini-specific timing formula is claimed beyond these supplied rules.

## Ashtottari

The Ashtottari engine follows BPHS 32.23-27 and uses eight lords; Ketu is excluded.

- The Mahadasha years are Sun 6, Moon 15, Mars 8, Mercury 17, Saturn 10, Jupiter 19, Rahu 12, and Venus 21, totaling a 108-year cycle.
- Counting starts from Ardra (Shivadi) when a graha occupies the Lagna and from Krittika (Krittikadi) otherwise.
- The nakshatra groups assigned to the eight lords are 4, 2, 4, 2, 4, 3, 4, and 4; every nakshatra in a group carries an equal share `lord_years / group_count`.
- The birth balance is the unelapsed fraction of the birth nakshatra plus every later nakshatra in the same lord's group. The conceptual period start is obtained by subtracting that elapsed share from the birth date.
- Mahadashas continue in the eight-lord order from the birth lord. The birth Mahadasha is truncated at birth; later Mahadashas are full periods.
- Antardashas and deeper levels use the same eight-lord order, proportional to the parent's full conceptual interval. The visible child chain starts at birth and omits periods completed earlier.

## Tribhagi

The enabled Tribhagi engine follows the Parashari rule set supplied for this
application. It is an additive scaled Vimshottari calculation and does not
modify the legacy Vimshottari field or calculator.

- The source Vimshottari cycle is 120 years; Tribhagi divides it into three,
  giving a 40-year cycle.
- The planetary order remains Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter,
  Saturn, Mercury, then repeats.
- Each planetary Mahadasha duration is the Vimshottari duration divided by
  three: 7/3, 20/3, 6/3, 10/3, 7/3, 18/3, 16/3, 19/3, and 17/3 years.
- The first lord is determined by the Moon's birth nakshatra using the same
  nine-lord nakshatra sequence as Vimshottari.
- Birth balance uses the elapsed fraction within the 13°20′ nakshatra:
  elapsed Tribhagi period equals planetary Tribhagi duration multiplied by
  elapsed nakshatra fraction; balance is the period minus elapsed time.
- Three successive 40-year cycles are generated continuously from the birth
  cycle, giving 27 Mahadashas. Mahadashas completed before birth are omitted
  from the first cycle and the birth-active Mahadasha is truncated at birth;
  the engine never skips forward to today's cycle.
- Antardasha through Pranadasha use recursive proportional subdivision in the
  same planetary order. Each child uses its lord's Vimshottari proportion of
  the parent interval, so the one-third scaling is applied at the Mahadasha
  cycle and retained proportionally at every nested level.
- All five levels are generated for every visible Tribhagi branch. Dates use
  the existing 365.25-day compatibility convention and exact AD-to-BS
  conversion when the calendar library supports the date.

The normalized Tribhagi report is `ready` only when this calculated tree is
available. Its interpretation uses the shared chart-backed Parashari dasha
phal presentation; no additional Tribhagi-specific prediction rule is claimed
beyond the supplied timing rules.

## Rollout Gates

1. Contract and tree invariants pass independently of any system formula.
2. Legacy Vimshottari/Yogini regression snapshots remain unchanged.
3. Each new system has at least one authoritative reference case and deterministic repeatability test.
4. API integration is additive and isolates new-engine failures from chart calculation.
5. Desktop controls expose only levels whose status is `ready`; unavailable states remain visible and explicit.
6. Prediction and score modules consume calculated nodes and chart-backed factors only. No default score is emitted for an unavailable calculation.
