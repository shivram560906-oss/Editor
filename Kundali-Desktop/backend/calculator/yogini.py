import datetime
from typing import List, Dict, Any

from calculator.dasha import ad_to_bs_str

# Order of Yoginis in Yogini Dasha
YOGINI_ORDER = [
    {"index": 1, "name": "Mangala", "nepali": "मङ्गला", "years": 1, "lord": "Moon"},
    {"index": 2, "name": "Pingala", "nepali": "पिङ्गला", "years": 2, "lord": "Sun"},
    {"index": 3, "name": "Dhanya", "nepali": "धान्या", "years": 3, "lord": "Jupiter"},
    {"index": 4, "name": "Bhramari", "nepali": "भ्रामरी", "years": 4, "lord": "Mars"},
    {"index": 5, "name": "Bhadrika", "nepali": "भद्रिका", "years": 5, "lord": "Mercury"},
    {"index": 6, "name": "Ulka", "nepali": "उल्का", "years": 6, "lord": "Saturn"},
    {"index": 7, "name": "Siddha", "nepali": "सिद्धा", "years": 7, "lord": "Venus"},
    {"index": 8, "name": "Sankata", "nepali": "संकटा", "years": 8, "lord": "Rahu/Ketu"},
]

YOGINI_CYCLE_YEARS = sum(item["years"] for item in YOGINI_ORDER)  # 36

PLANET_NEPALI = {
    "Sun": "सूर्य",
    "Moon": "चन्द्र",
    "Mars": "मङ्गल",
    "Mercury": "बुध",
    "Jupiter": "गुरु",
    "Venus": "शुक्र",
    "Saturn": "शनि",
    "Rahu": "राहु",
    "Ketu": "केतु",
}


def add_years(start_date: datetime.date, years: float) -> datetime.date:
    """Adds a decimal number of years to a date."""
    days_to_add = int(years * 365.25)
    return start_date + datetime.timedelta(days=days_to_add)


def _parse_birth_date(birth_date_str: str, birth_time_str: str = "12:00:00") -> datetime.date:
    try:
        birth_dt = datetime.datetime.strptime(
            f"{birth_date_str} {birth_time_str}", "%Y-%m-%d %H:%M:%S"
        )
    except ValueError:
        try:
            birth_dt = datetime.datetime.strptime(birth_date_str, "%Y-%m-%d")
        except ValueError:
            birth_dt = datetime.datetime.now()
    return birth_dt.date()


def _yogini_start(longitude: float) -> tuple[int, float]:
    """Return the birth Yogini index and the elapsed fraction of its nakshatra.

    BPHS: nakshatra number ``N`` (Ashwini=1 ... Revati=27) maps to Yogini
    ``((N + 3 - 1) mod 8) + 1``.  The balance is the unelapsed fraction of that
    nakshatra's yogini period.
    """
    nakshatra_size = 360.0 / 27.0
    nakshatra_number = int(longitude / nakshatra_size) % 27 + 1
    val = (nakshatra_number + 3) % 8
    start_idx = (val - 1) if val != 0 else 7  # 0 remainder = Sankata
    fraction_elapsed = (longitude % nakshatra_size) / nakshatra_size
    return start_idx, fraction_elapsed


def _yogini_node(
    info: Dict[str, Any],
    start: datetime.date,
    end: datetime.date,
    level: int,
    current_date: datetime.date,
    *,
    is_partial: bool,
    children: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Build one normalized Yogini period node.

    ``start``/``end`` are the visible boundaries.  For a birth-active period
    ``start`` is the birth date, while its conceptual (astronomical) start is
    earlier; ``is_partial`` records that truncation.
    """
    start_bs = ad_to_bs_str(start)
    end_bs = ad_to_bs_str(end)
    planet_lord = "Rahu" if info["name"] == "Sankata" else info["lord"]
    node = {
        "lord": info["name"],
        "lord_nepali": info["nepali"],
        "yogini": info["name"],
        "yogini_nepali": info["nepali"],
        "planet_lord": planet_lord,
        "planet_lord_nepali": PLANET_NEPALI.get(planet_lord, planet_lord),
        "level": level,
        "total_years": info["years"],
        "start": start.isoformat(),
        "end": end.isoformat(),
        "start_bs": start_bs,
        "end_bs": end_bs,
        "start_bs_available": bool(start_bs),
        "end_bs_available": bool(end_bs),
        "is_partial": bool(is_partial),
        "is_active": start <= current_date < end,
    }
    if children:
        node["children"] = children
    return node


def _child_boundaries(
    parent_start: datetime.date,
    parent_end: datetime.date,
    parent_idx: int,
) -> List[tuple[int, Dict[str, Any], datetime.date, datetime.date]]:
    """Return the eight full Yogini child periods of ``parent_start``..``parent_end``.

    The child duration is ``parent_years * child_weight / 36`` (BPHS).  For a
    partial birth Mahadasha the parent interval passed here is the *conceptual*
    full interval, so children are never compressed into the remaining portion.
    """
    duration_days = (parent_end - parent_start).days
    if duration_days < len(YOGINI_ORDER):
        return []

    boundaries: List[tuple[int, Dict[str, Any], datetime.date, datetime.date]] = []
    cursor = parent_start
    cumulative = 0
    previous_boundary = 0
    for offset in range(len(YOGINI_ORDER)):
        idx = (parent_idx + offset) % len(YOGINI_ORDER)
        info = YOGINI_ORDER[idx]
        cumulative += info["years"]
        raw_boundary = round(duration_days * cumulative / YOGINI_CYCLE_YEARS)
        # Deep levels can round a one-day slice down to zero.  Reserve at least
        # one day for every sibling so the date-only tree stays positive.
        minimum = previous_boundary + 1
        maximum = duration_days - (len(YOGINI_ORDER) - 1 - offset)
        boundary_days = min(max(raw_boundary, minimum), maximum)
        end = (
            parent_end
            if offset == len(YOGINI_ORDER) - 1
            else parent_start + datetime.timedelta(days=boundary_days)
        )
        boundaries.append((idx, info, cursor, end))
        cursor = end
        previous_boundary = boundary_days
    return boundaries


def _calculate_yogini_children(
    parent_idx: int,
    parent_start: datetime.date,
    parent_end: datetime.date,
    level: int,
    birth_date: datetime.date,
    current_date: datetime.date,
) -> List[Dict[str, Any]]:
    """Recursively divide a Yogini period by the 1..8 / 36 rule.

    ``parent_start``/``parent_end`` are conceptual boundaries.  Children that
    end before birth are omitted; the child active at birth is truncated to the
    birth date.  Every emitted child therefore satisfies ``end > start`` and
    sibling intervals stay contiguous from the visible parent start.
    """
    if (parent_end - parent_start).days < len(YOGINI_ORDER):
        return []

    children: List[Dict[str, Any]] = []
    for idx, info, child_start, child_end in _child_boundaries(
        parent_start, parent_end, parent_idx
    ):
        if child_end <= birth_date:
            continue
        visible_start = max(child_start, birth_date)
        nested = (
            _calculate_yogini_children(
                idx, child_start, child_end, level + 1, birth_date, current_date
            )
            if level < 5
            else []
        )
        children.append(
            _yogini_node(
                info,
                visible_start,
                child_end,
                level,
                current_date,
                is_partial=child_start < birth_date,
                children=nested,
            )
        )
    return children


def _complete_yogini_antardashas(
    parent_idx: int,
    parent_start: datetime.date,
    parent_end: datetime.date,
    birth_date: datetime.date,
    current_date: datetime.date,
) -> List[Dict[str, Any]]:
    """Return the complete eight-Yogini antardasha cycle with true boundaries.

    Janmapatrika renders only the post-birth part of this list, but keeping the
    complete cycle preserves correct durations.  A period compressed to the
    birth balance would show wrong values in every later cell.
    """
    periods: List[Dict[str, Any]] = []
    for idx, info, child_start, child_end in _child_boundaries(
        parent_start, parent_end, parent_idx
    ):
        start_bs = ad_to_bs_str(child_start)
        end_bs = ad_to_bs_str(child_end)
        periods.append(
            {
                "name": info["name"],
                "nepali": info["nepali"],
                "total_years": info["years"],
                "start": child_start.isoformat(),
                "end": child_end.isoformat(),
                "start_bs": start_bs,
                "end_bs": end_bs,
                "start_bs_available": bool(start_bs),
                "end_bs_available": bool(end_bs),
                "is_before_birth": child_end <= birth_date,
                "is_partial": child_start < birth_date < child_end,
                "is_active": max(child_start, birth_date) <= current_date < child_end,
                "level": 2,
            }
        )
    return periods


def _conceptual_birth_period(
    birth_date: datetime.date,
    start_idx: int,
    fraction_elapsed: float,
) -> tuple[datetime.date, datetime.date]:
    """Return the full conceptual birth Mahadasha interval and its visible end."""
    first = YOGINI_ORDER[start_idx]
    elapsed_days = int(first["years"] * fraction_elapsed * 365.25)
    conceptual_start = birth_date - datetime.timedelta(days=elapsed_days)
    conceptual_end = conceptual_start + datetime.timedelta(days=int(first["years"] * 365.25))
    return conceptual_start, conceptual_end


def calculate_yogini_dasha(
    moon_sidereal_long: float,
    birth_date_str: str,
    birth_time_str: str,
) -> List[Dict[str, Any]]:
    """Calculate the legacy Yogini Mahadasha timeline for three 36-year cycles.

    The first Mahadasha starts at birth (``is_partial``) and ends at the true
    boundary of the birth Yogini period.  Its ``antardashas`` field contains the
    complete eight-Yogini cycle with true boundaries and ``is_before_birth``
    flags, which the Janmapatrika grid uses to render correct, increasing
    remaining-age values.
    """
    birth_date = _parse_birth_date(birth_date_str, birth_time_str)
    longitude = float(moon_sidereal_long) % 360.0
    start_idx, fraction_elapsed = _yogini_start(longitude)
    current_date = datetime.date.today()
    conceptual_start, _ = _conceptual_birth_period(
        birth_date, start_idx, fraction_elapsed
    )

    timeline: List[Dict[str, Any]] = []
    cursor = conceptual_start
    current_idx = start_idx
    for offset in range(len(YOGINI_ORDER) * 3):
        info = YOGINI_ORDER[current_idx]
        end = cursor + datetime.timedelta(days=int(info["years"] * 365.25))
        visible_start = max(cursor, birth_date)
        if end <= birth_date:
            cursor = end
            current_idx = (current_idx + 1) % len(YOGINI_ORDER)
            continue

        timeline.append(
            {
                "name": info["name"],
                "nepali": info["nepali"],
                "lord": info["lord"],
                "total_years": info["years"],
                "start": visible_start.isoformat(),
                "end": end.isoformat(),
                "is_partial": cursor < birth_date,
                "remaining_years": (
                    end - visible_start
                ).days / 365.25,
                "antardashas": _complete_yogini_antardashas(
                    current_idx, cursor, end, birth_date, current_date
                ),
            }
        )
        cursor = end
        current_idx = (current_idx + 1) % len(YOGINI_ORDER)

    return timeline


def calculate_yogini_dasha_five_level(
    moon_sidereal_long: float,
    birth_date_str: str,
    birth_time_str: str = "12:00:00",
    current_date: datetime.date = None,
) -> List[Dict[str, Any]]:
    """Calculate normalized Yogini Dasha through Pranadasha.

    The first Mahadasha is truncated to birth; its children are generated from
    the conceptual full Mahadasha start so their durations follow the classical
    ``parent * child_weight / 36`` rule instead of being compressed into the
    remaining balance.
    """
    birth_date = _parse_birth_date(birth_date_str, birth_time_str)
    if current_date is None:
        current_date = datetime.date.today()
    longitude = float(moon_sidereal_long) % 360.0
    start_idx, fraction_elapsed = _yogini_start(longitude)
    conceptual_start, first_end = _conceptual_birth_period(
        birth_date, start_idx, fraction_elapsed
    )

    periods: List[Dict[str, Any]] = []
    cursor = conceptual_start
    for offset in range(len(YOGINI_ORDER) * 3):
        idx = (start_idx + offset) % len(YOGINI_ORDER)
        info = YOGINI_ORDER[idx]
        end = (
            first_end
            if offset == 0
            else cursor + datetime.timedelta(days=int(info["years"] * 365.25))
        )
        visible_start = max(cursor, birth_date)
        if end <= birth_date:
            cursor = end
            continue
        children = _calculate_yogini_children(
            idx, cursor, end, 2, birth_date, current_date
        )
        periods.append(
            _yogini_node(
                info,
                visible_start,
                end,
                1,
                current_date,
                is_partial=cursor < birth_date,
                children=children,
            )
        )
        cursor = end
    return periods
