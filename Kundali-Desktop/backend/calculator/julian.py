def datetime_to_jd(year: int, month: int, day: int, hour: int, minute: int, second: float, timezone_offset: float) -> float:
    """
    Converts local datetime to Julian Date (UT).
    timezone_offset is in hours (e.g., +5.75 for Nepal, +5.5 for India, -5.0 for EST).
    """
    # 1. Convert local time to UTC
    # Since: Local Time = UTC + Offset => UTC = Local Time - Offset
    decimal_hours = hour + minute / 60.0 + second / 3600.0
    utc_decimal_hours = decimal_hours - timezone_offset
    
    # Adjust day if UTC hours cross day boundaries
    utc_day = day
    utc_month = month
    utc_year = year
    
    if utc_decimal_hours >= 24.0:
        utc_decimal_hours -= 24.0
        utc_day += 1
    elif utc_decimal_hours < 0.0:
        utc_decimal_hours += 24.0
        utc_day -= 1
        
    # Handle month/year rollover (simple Gregorian logic)
    # A standard way is to construct a datetime object in python to handle roll-overs cleanly
    import datetime
    try:
        # We create a local datetime, subtract timezone offset, and get UTC datetime
        local_dt = datetime.datetime(year, month, day, hour, minute, int(second), int((second - int(second)) * 1000000))
        utc_dt = local_dt - datetime.timedelta(hours=timezone_offset)
        
        y = utc_dt.year
        m = utc_dt.month
        d = utc_dt.day + (utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0 + utc_dt.microsecond / 3600000000.0) / 24.0
    except Exception:
        # Fallback if outside standard datetime range (e.g. historical dates before year 1)
        y = utc_year
        m = utc_month
        d = utc_day + utc_decimal_hours / 24.0

    # 2. Compute Julian Date
    if m <= 2:
        y -= 1
        m += 12
    
    # Gregorian calendar check (introduced Oct 15, 1582)
    is_gregorian = True
    if year < 1582 or (year == 1582 and (month < 10 or (month == 10 and day <= 4))):
        is_gregorian = False

    if is_gregorian:
        A = int(y / 100)
        B = 2 - A + int(A / 4)
    else:
        B = 0

    jd = int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5
    return jd

def jd_to_julian_centuries(jd: float) -> float:
    """
    Converts Julian Date to Julian Centuries since J2000.0 (JD 2451545.0).
    """
    return (jd - 2451545.0) / 36525.0
