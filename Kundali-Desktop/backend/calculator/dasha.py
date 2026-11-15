import datetime
import nepali_datetime
from typing import List, Dict, Any

# Order of planets in Vimshottari Dasha
DASHA_ORDER = [
    {"name": "Ketu", "nepali": "केतु", "years": 7},
    {"name": "Venus", "nepali": "शुक्र", "years": 20},
    {"name": "Sun", "nepali": "सूर्य", "years": 6},
    {"name": "Moon", "nepali": "चन्द्र", "years": 10},
    {"name": "Mars", "nepali": "मङ्गल", "years": 7},
    {"name": "Rahu", "nepali": "राहु", "years": 18},
    {"name": "Jupiter", "nepali": "गुरु", "years": 16},
    {"name": "Saturn", "nepali": "शनि", "years": 19},
    {"name": "Mercury", "nepali": "बुध", "years": 17}
]

ASHTOTTARI_ORDER = [
    # BPHS 32.23-27: Ashtottari uses eight lords (Ketu is excluded).
    # The commentary lists the years as 6, 15, 8, 17, 10, 19, 12 and 21
    # (the OCR "29" is a corrupted "21"); the total is 108 years.
    {"name": "Sun", "nepali": "सूर्य", "years": 6},
    {"name": "Moon", "nepali": "चन्द्र", "years": 15},
    {"name": "Mars", "nepali": "मङ्गल", "years": 8},
    {"name": "Mercury", "nepali": "बुध", "years": 17},
    {"name": "Saturn", "nepali": "शनि", "years": 10},
    {"name": "Jupiter", "nepali": "गुरु", "years": 19},
    {"name": "Rahu", "nepali": "राहु", "years": 12},
    {"name": "Venus", "nepali": "शुक्र", "years": 21},
]

# BPHS 32.26: counting from Ardra (Shivadi) or Krittika (Krittikadi), the
# nakshatra groups assigned to the eight lords are 4, 2, 4, 2, 4, 3, 4, 4.
ASHTOTTARI_NAKSHATRA_GROUPS = [4, 2, 4, 2, 4, 3, 4, 4]
ASHTOTTARI_TOTAL_YEARS = 108
ARDRA_NAKSHATRA_INDEX = 5       # 0-based: Ashwini=0 ... Ardra=5
KRITTIKA_NAKSHATRA_INDEX = 2    # 0-based: Ashwini=0 ... Krittika=2


def ad_to_bs_str(ad_date: datetime.date) -> str:
    """Return an exact BS date, or an empty value when conversion is unavailable.

    A fixed AD-to-BS year offset is not a calendar conversion: BS month/day
    boundaries vary by year.  In particular, ``nepali_datetime`` has a finite
    supported range, so dates outside it must not be presented as fabricated
    or approximate BS dates.
    """
    try:
        bs_date = nepali_datetime.date.from_datetime_date(ad_date)
    except Exception:
        # Calendar library range/validation failures are an unavailable state.
        return ""
    return f"{bs_date.year}-{bs_date.month:02d}-{bs_date.day:02d}"

def calculate_sub_dashas(
    parent_lord_idx: int,
    parent_start: datetime.date,
    parent_end: datetime.date,
    parent_years: float,
    level: int,
    birth_date: datetime.date,
    current_date: datetime.date
) -> List[Dict[str, Any]]:
    sub_periods = []
    current_start = parent_start
    
    for i in range(9):
        lord_idx = (parent_lord_idx + i) % 9
        lord_info = DASHA_ORDER[lord_idx]
        
        parent_duration_days = (parent_end - parent_start).days
        sub_days = int(parent_duration_days * (lord_info["years"] / 120.0))
        
        if i == 8:
            sub_end = parent_end
        else:
            sub_end = current_start + datetime.timedelta(days=sub_days)
            if sub_end > parent_end:
                sub_end = parent_end
                
        if sub_end <= birth_date:
            current_start = sub_end
            continue
            
        display_start = current_start
        is_partial = False
        if current_start < birth_date:
            display_start = birth_date
            is_partial = True
            
        is_active = (display_start <= current_date < sub_end)
        
        start_bs = ad_to_bs_str(display_start)
        end_bs = ad_to_bs_str(sub_end)
        node = {
            "lord": lord_info["name"],
            "lord_nepali": lord_info["nepali"],
            "start": display_start.isoformat(),
            "end": sub_end.isoformat(),
            "start_bs": start_bs,
            "end_bs": end_bs,
            "start_bs_available": bool(start_bs),
            "end_bs_available": bool(end_bs),
            "is_partial": is_partial,
            "is_active": is_active,
            "level": level
        }
        
        if level < 3 or (level < 5 and is_active):
            node["children"] = calculate_sub_dashas(
                lord_idx,
                current_start,
                sub_end,
                lord_info["years"],
                level + 1,
                birth_date,
                current_date
            )
            
        sub_periods.append(node)
        current_start = sub_end
        
    return sub_periods


def _calculate_complete_antardashas(
    parent_lord_idx: int,
    parent_start: datetime.date,
    parent_end: datetime.date,
    birth_date: datetime.date,
    current_date: datetime.date,
) -> List[Dict[str, Any]]:
    """Return the complete nine-antardasha cycle for a mahadasha.

    ``calculate_sub_dashas`` intentionally drops periods that ended before
    birth because the legacy ``children`` list describes the visible life
    timeline.  The Janmapatrika antardasha grid, however, has one column per
    lord, so a partial birth mahadasha must still expose its pre-birth
    antardashas.  This additive list keeps the true astronomical boundaries
    and marks periods completed before birth instead of fabricating or
    duplicating a neighbouring lord.
    """
    periods: List[Dict[str, Any]] = []
    cursor = parent_start
    parent_duration_days = (parent_end - parent_start).days

    for offset in range(len(DASHA_ORDER)):
        lord_idx = (parent_lord_idx + offset) % len(DASHA_ORDER)
        lord_info = DASHA_ORDER[lord_idx]

        if offset == len(DASHA_ORDER) - 1:
            sub_end = parent_end
        else:
            sub_days = int(parent_duration_days * (lord_info["years"] / 120.0))
            sub_end = cursor + datetime.timedelta(days=sub_days)
            if sub_end > parent_end:
                sub_end = parent_end

        start_bs = ad_to_bs_str(cursor)
        end_bs = ad_to_bs_str(sub_end)
        periods.append({
            "lord": lord_info["name"],
            "lord_nepali": lord_info["nepali"],
            "start": cursor.isoformat(),
            "end": sub_end.isoformat(),
            "start_bs": start_bs,
            "end_bs": end_bs,
            "start_bs_available": bool(start_bs),
            "end_bs_available": bool(end_bs),
            "is_before_birth": sub_end <= birth_date,
            "is_partial": cursor < birth_date < sub_end,
            "is_active": cursor <= current_date < sub_end,
            "level": 2,
        })
        cursor = sub_end

    return periods


def calculate_vimshottari_dasha(
    moon_sidereal_long: float,
    birth_date_str: str,
    birth_time_str: str = "12:00:00",
    balance_at_birth: float = None
) -> List[Dict[str, Any]]:
    try:
        birth_dt = datetime.datetime.strptime(f"{birth_date_str} {birth_time_str}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            birth_dt = datetime.datetime.strptime(birth_date_str, "%Y-%m-%d")
        except ValueError:
            birth_dt = datetime.datetime.now()
        
    birth_date = birth_dt.date()
    current_date = datetime.date.today()
    
    # Normalize longitude to 0..360
    moon_sidereal_long = float(moon_sidereal_long % 360.0)
    if moon_sidereal_long < 0:
        moon_sidereal_long += 360.0

    nakshatra_size = 360.0 / 27.0  # 13.333333333333334 degrees
    nak_idx = int(moon_sidereal_long / nakshatra_size) % 27
    
    start_planet_idx = nak_idx % 9
    first_lord = DASHA_ORDER[start_planet_idx]

    if balance_at_birth is not None and balance_at_birth > 0:
        # Use provided balance_at_birth (remaining years of first dasha)
        balance_years = min(float(balance_at_birth), float(first_lord["years"]))
        elapsed_years = first_lord["years"] - balance_years
    else:
        # Calculate from nakshatra degree
        nak_long = moon_sidereal_long % nakshatra_size
        fraction_elapsed = nak_long / nakshatra_size
        elapsed_years = fraction_elapsed * first_lord["years"]

    elapsed_days = round(elapsed_years * 365.25)
    conceptional_start = birth_date - datetime.timedelta(days=elapsed_days)
    
    timeline = []
    current_start_date = conceptional_start
    current_planet_idx = start_planet_idx
    
    for cycle in range(9):
        lord = DASHA_ORDER[current_planet_idx]
        dasha_days = int(lord["years"] * 365.25)
        end_date = current_start_date + datetime.timedelta(days=dasha_days)
        
        if end_date <= birth_date:
            current_start_date = end_date
            current_planet_idx = (current_planet_idx + 1) % 9
            continue
            
        display_start = current_start_date
        is_partial = False
        if current_start_date < birth_date:
            display_start = birth_date
            is_partial = True
            
        is_active = (display_start <= current_date < end_date)
        
        start_bs = ad_to_bs_str(display_start)
        end_bs = ad_to_bs_str(end_date)
        node = {
            "lord": lord["name"],
            "lord_nepali": lord["nepali"],
            "total_years": lord["years"],
            "start": display_start.isoformat(),
            "end": end_date.isoformat(),
            "start_bs": start_bs,
            "end_bs": end_bs,
            "start_bs_available": bool(start_bs),
            "end_bs_available": bool(end_bs),
            "is_partial": is_partial,
            "is_active": is_active,
            "level": 1
        }
        
        # Calculate sub-dashas (Level 2 = Antardasha)
        node["children"] = calculate_sub_dashas(
            current_planet_idx,
            current_start_date,
            end_date,
            lord["years"],
            2,
            birth_date,
            current_date
        )
        # Additive complete cycle for the Janmapatrika antardasha grid. The
        # legacy ``children`` list above remains the visible post-birth chain.
        node["antardashas"] = _calculate_complete_antardashas(
            current_planet_idx,
            current_start_date,
            end_date,
            birth_date,
            current_date,
        )
        
        timeline.append(node)
        current_start_date = end_date
        current_planet_idx = (current_planet_idx + 1) % 9
        
    return timeline


def _parse_birth_date(birth_date_str: str, birth_time_str: str = "12:00:00") -> datetime.date:
    """Parse the birth date using the same compatibility rules as Vimshottari."""
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


def _calculate_scaled_sub_dashas(
    parent_lord_idx: int,
    parent_start: datetime.date,
    parent_end: datetime.date,
    level: int,
    birth_date: datetime.date,
    current_date: datetime.date,
) -> List[Dict[str, Any]]:
    """Build every nested Tribhagi level using proportional Vimshottari order."""
    periods: List[Dict[str, Any]] = []
    cursor = parent_start
    parent_duration_days = (parent_end - parent_start).days
    # Date-only output cannot represent nine positive children in a shorter
    # parent interval. Stop before rounding can create repeated zero-length
    # descendants.
    if parent_duration_days < len(DASHA_ORDER):
        return periods

    total_years = sum(info["years"] for info in DASHA_ORDER)
    for offset in range(len(DASHA_ORDER)):
        lord_idx = (parent_lord_idx + offset) % len(DASHA_ORDER)
        lord_info = DASHA_ORDER[lord_idx]
        cumulative_years = sum(
            DASHA_ORDER[(parent_lord_idx + index) % len(DASHA_ORDER)]["years"]
            for index in range(offset + 1)
        )
        boundary_days = round(parent_duration_days * cumulative_years / total_years)
        end = parent_end if offset == len(DASHA_ORDER) - 1 else (
            parent_start + datetime.timedelta(days=boundary_days)
        )
        if end <= cursor:
            continue
        if end <= birth_date:
            cursor = end
            continue

        display_start = max(cursor, birth_date)
        node = {
            "lord": lord_info["name"],
            "lord_nepali": lord_info["nepali"],
            "start": display_start.isoformat(),
            "end": end.isoformat(),
            "start_bs": ad_to_bs_str(display_start),
            "end_bs": ad_to_bs_str(end),
            "start_bs_available": bool(ad_to_bs_str(display_start)),
            "end_bs_available": bool(ad_to_bs_str(end)),
            "is_partial": cursor < birth_date,
            "is_active": display_start <= current_date < end,
            "level": level,
        }
        if level < 5:
            children = _calculate_scaled_sub_dashas(
                lord_idx, cursor, end, level + 1, birth_date, current_date
            )
            if children:
                node["children"] = children
        periods.append(node)
        cursor = end

    return periods


def calculate_tribhagi_dasha(
    moon_sidereal_long: float,
    birth_date_str: str,
    birth_time_str: str = "12:00:00",
    balance_at_birth: float = None,
) -> List[Dict[str, Any]]:
    """Calculate Parashari Tribhagi Dasha through Pranadasha.

    Tribhagi uses the Vimshottari sequence and nakshatra balance, with every
    planetary period divided by three.  Its complete cycle is therefore 40
    years.  Three successive cycles are generated continuously from the birth
    cycle so the report retains the elapsed periods instead of silently
    jumping forward to today's cycle.
    """
    birth_date = _parse_birth_date(birth_date_str, birth_time_str)
    current_date = datetime.date.today()
    longitude = float(moon_sidereal_long) % 360.0
    nakshatra_size = 360.0 / 27.0
    nakshatra_index = int(longitude / nakshatra_size) % 27
    start_index = nakshatra_index % len(DASHA_ORDER)
    first_lord = DASHA_ORDER[start_index]
    tribhagi_years = first_lord["years"] / 3.0

    if balance_at_birth is not None and balance_at_birth > 0:
        balance_years = min(float(balance_at_birth), tribhagi_years)
        elapsed_years = tribhagi_years - balance_years
    else:
        fraction_elapsed = (longitude % nakshatra_size) / nakshatra_size
        elapsed_years = tribhagi_years * fraction_elapsed

    cursor = birth_date - datetime.timedelta(days=int(elapsed_years * 365.25))

    periods: List[Dict[str, Any]] = []
    # Three 40-year cycles are the exact analogue of the nine Vimshottari
    # Mahadashas (one 120-year cycle).  Each cycle repeats the same order.
    for _cycle in range(3):
        for offset in range(len(DASHA_ORDER)):
            lord_idx = (start_index + offset) % len(DASHA_ORDER)
            lord_info = DASHA_ORDER[lord_idx]
            duration_days = int(lord_info["years"] / 3.0 * 365.25)
            end = cursor + datetime.timedelta(days=duration_days)
            if end <= birth_date:
                cursor = end
                continue

            display_start = max(cursor, birth_date)
            start_bs = ad_to_bs_str(display_start)
            end_bs = ad_to_bs_str(end)
            node = {
                "lord": lord_info["name"],
                "lord_nepali": lord_info["nepali"],
                "total_years": lord_info["years"] / 3.0,
                "start": display_start.isoformat(),
                "end": end.isoformat(),
                "start_bs": start_bs,
                "end_bs": end_bs,
                "start_bs_available": bool(start_bs),
                "end_bs_available": bool(end_bs),
                "is_partial": cursor < birth_date,
                "is_active": display_start <= current_date < end,
                "level": 1,
            }
            node["children"] = _calculate_scaled_sub_dashas(
                lord_idx, cursor, end, 2, birth_date, current_date
            )
            periods.append(node)
            cursor = end

    return periods


def _calculate_ashtottari_sub_dashas(
    parent_lord_idx: int,
    parent_start: datetime.date,
    parent_end: datetime.date,
    level: int,
    birth_date: datetime.date,
    current_date: datetime.date,
) -> List[Dict[str, Any]]:
    """Recursively build Ashtottari antardasha/pratyantardasha using ASHTOTTARI_ORDER.

    Each sub-period's duration is proportional to the sub-lord's total years
    within the parent period — identical logic to Vimshottari sub-dashas but
    applied to the 108-year Ashtottari sequence.
    """
    periods: List[Dict[str, Any]] = []
    parent_duration_days = (parent_end - parent_start).days
    if parent_duration_days < len(ASHTOTTARI_ORDER):
        return periods

    total_years = ASHTOTTARI_TOTAL_YEARS
    cursor = parent_start
    for offset in range(len(ASHTOTTARI_ORDER)):
        lord_idx = (parent_lord_idx + offset) % len(ASHTOTTARI_ORDER)
        lord_info = ASHTOTTARI_ORDER[lord_idx]
        # Proportional duration: (sub_lord_years / 108) * parent_duration
        sub_days = round(parent_duration_days * lord_info["years"] / total_years)
        end = parent_end if offset == len(ASHTOTTARI_ORDER) - 1 else (
            cursor + datetime.timedelta(days=sub_days)
        )
        if end <= cursor:
            continue
        if end <= birth_date:
            cursor = end
            continue

        display_start = max(cursor, birth_date)
        start_bs = ad_to_bs_str(display_start)
        end_bs = ad_to_bs_str(end)
        node: Dict[str, Any] = {
            "lord": lord_info["name"],
            "lord_nepali": lord_info["nepali"],
            "total_years": lord_info["years"],
            "start": display_start.isoformat(),
            "end": end.isoformat(),
            "start_bs": start_bs,
            "end_bs": end_bs,
            "start_bs_available": bool(start_bs),
            "end_bs_available": bool(end_bs),
            "is_partial": cursor < birth_date,
            "is_active": display_start <= current_date < end,
            "level": level,
        }
        # Generate Pratyantardasha (level 3) when the period is active
        if level < 3 or (level < 5 and node["is_active"]):
            children = _calculate_ashtottari_sub_dashas(
                lord_idx, cursor, end, level + 1, birth_date, current_date
            )
            if children:
                node["children"] = children
        periods.append(node)
        cursor = end
    return periods


def _ashtottari_birth_period(
    longitude: float,
    lagna_occupied: bool,
) -> tuple[int, float, float]:
    """Return the birth Ashtottari lord and its elapsed/balance years.

    BPHS 32.26-27: when a graha occupies the Lagna, count from Ardra
    (Shivadi); otherwise count from Krittika (Krittikadi).  The eight
    nakshatra groups are 4, 2, 4, 2, 4, 3, 4, 4 and every nakshatra in a
    group carries an equal share of that lord's period.  The balance is the
    unelapsed part of the birth nakshatra plus every later nakshatra in the
    same group.
    """
    nakshatra_size = 360.0 / 27.0
    nakshatra_index = int(longitude / nakshatra_size) % 27
    start_index = (
        ARDRA_NAKSHATRA_INDEX if lagna_occupied else KRITTIKA_NAKSHATRA_INDEX
    )
    offset = (nakshatra_index - start_index) % 27
    cumulative = 0
    for lord_idx, group_count in enumerate(ASHTOTTARI_NAKSHATRA_GROUPS):
        cumulative += group_count
        if offset < cumulative:
            position = offset - (cumulative - group_count)
            fraction_elapsed = (longitude % nakshatra_size) / nakshatra_size
            per_nakshatra_years = ASHTOTTARI_ORDER[lord_idx]["years"] / group_count
            elapsed_years = (position + fraction_elapsed) * per_nakshatra_years
            balance_years = ASHTOTTARI_ORDER[lord_idx]["years"] - elapsed_years
            return lord_idx, elapsed_years, balance_years

    # A normalized longitude always falls in one of the 27 groups.  Keep the
    # fallback deterministic for malformed inputs.
    return 0, 0.0, float(ASHTOTTARI_ORDER[0]["years"])


def calculate_ashtottari_dasha(
    moon_sidereal_long: float,
    birth_date_str: str,
    birth_time_str: str = "12:00:00",
    *,
    lagna_occupied: bool = False,
) -> List[Dict[str, Any]]:
    """Calculate Ashtottari Dasha (108-year cycle) with nested sub-periods.

    BPHS 32.23-27 defines eight lords (Ketu is excluded) with periods
    6, 15, 8, 17, 10, 19, 12 and 21 years.  The nakshatra groups counted from
    Ardra (Lagna occupied) or Krittika (Lagna empty) are 4, 2, 4, 2, 4, 3, 4
    and 4.  A nakshatra's share of its lord's period is therefore the lord's
    years divided by the group size, not by eight.

    Each Mahadasha generates antardasha children in the same eight-lord order,
    proportional to the parent interval; deeper levels follow the same rule.
    """
    birth_date = _parse_birth_date(birth_date_str, birth_time_str)
    current_date = datetime.date.today()
    longitude = float(moon_sidereal_long) % 360.0
    start_index, elapsed_years, _balance_years = _ashtottari_birth_period(
        longitude, lagna_occupied
    )
    cursor = birth_date - datetime.timedelta(days=int(elapsed_years * 365.25))

    periods: List[Dict[str, Any]] = []
    for offset in range(len(ASHTOTTARI_ORDER)):
        lord_idx = (start_index + offset) % len(ASHTOTTARI_ORDER)
        lord_info = ASHTOTTARI_ORDER[lord_idx]
        end = cursor + datetime.timedelta(days=int(lord_info["years"] * 365.25))
        if end <= birth_date:
            cursor = end
            continue

        display_start = max(cursor, birth_date)
        is_partial = cursor < birth_date
        is_active = display_start <= current_date < end
        start_bs = ad_to_bs_str(display_start)
        end_bs = ad_to_bs_str(end)

        node: Dict[str, Any] = {
            "lord": lord_info["name"],
            "lord_nepali": lord_info["nepali"],
            "total_years": lord_info["years"],
            "start": display_start.isoformat(),
            "end": end.isoformat(),
            "start_bs": start_bs,
            "end_bs": end_bs,
            "start_bs_available": bool(start_bs),
            "end_bs_available": bool(end_bs),
            "is_partial": is_partial,
            "is_active": is_active,
            "level": 1,
        }
        # Always generate antardasha (level 2); deeper levels follow the active
        # chain so the 108-year tree stays transportable.
        node["children"] = _calculate_ashtottari_sub_dashas(
            lord_idx, cursor, end, 2, birth_date, current_date
        )
        periods.append(node)
        cursor = end

    return periods
