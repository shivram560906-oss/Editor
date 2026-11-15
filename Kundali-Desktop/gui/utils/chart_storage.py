"""
gui/utils/chart_storage.py

Local chart storage — saves/loads kundali records from the desktop SQLite
database (kundali_records table).

This desktop application is intentionally single-user and local: there is no
login, account or administrator.  Every chart saved on this machine is visible
to the person using the app, and existing records (including older rows with
``user_id = NULL``) remain available.
"""
from __future__ import annotations

import datetime
import json
import os
import sys
from typing import Optional

# ── path setup ──────────────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_BACKEND = os.path.join(_ROOT, "backend")
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

# Canonical database URL + per-installation signing key, resolved by gui.paths
# before backend.config is imported.
from gui.paths import configure as _configure_desktop_environment

_DESKTOP_ENV = _configure_desktop_environment()


# ── SQLAlchemy direct access ─────────────────────────────────────────────────
_SessionMaker = None


def _get_session():
    global _SessionMaker
    if _SessionMaker is None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # Resolved by gui.paths.configure() above - one database, one engine.
        db_url = os.environ.get("DATABASE_URL") or _DESKTOP_ENV["database_path"]
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        try:
            from database.models import Base

            Base.metadata.create_all(bind=engine)
        except Exception:
            pass
        _SessionMaker = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return _SessionMaker()


# ── Public API ───────────────────────────────────────────────────────────────


def _record_values(params: dict) -> dict:
    """Normalize form params into the columns shared by insert and update."""
    gender_map = {0: "male", 1: "female", 2: "other"}
    return {
        "name": params.get("name", ""),
        "birth_date": params.get("birth_date", ""),
        "birth_time": params.get("birth_time", ""),
        "latitude": float(params.get("latitude", 0)),
        "longitude": float(params.get("longitude", 0)),
        "timezone": float(params.get("timezone", 5.75)),
        "timezone_id": params.get("timezone_id"),
        "country": params.get("country"),
        "birth_place": params.get("birth_place") or params.get("city"),
        "gender": gender_map.get(params.get("gender", 0), "male"),
        "full_name": params.get("full_name"),
        "father_name": params.get("father_name"),
        "mother_name": params.get("mother_name"),
        "gotra": params.get("gotra"),
        "surname": params.get("surname"),
        "kula": params.get("kula"),
        "kuladevata": params.get("kuladevata"),
        "spouse_name": params.get("spouse_name"),
        "marital_status": params.get("marital_status"),
        "caste": params.get("caste"),
        "religion": params.get("religion"),
        "family_details": params.get("family_details"),
        "notes": json.dumps({
            "ayanamsha_type": params.get("ayanamsha_type", "LAHIRI"),
            "node_type": params.get("node_type", "MEAN"),
            "house_system": params.get("house_system", "WHOLE_SIGN"),
            "life_events": params.get("life_events") or [],
            "comments": params.get("comments") or None,
            "region": params.get("region") or params.get("province"),
            "province": params.get("province") or params.get("region"),
            "district": params.get("district"),
        }),
    }


def save_chart(params: dict) -> int:
    """Save birth params to kundali_records and return the record ID.

    params must have: name, birth_date, birth_time, latitude, longitude, timezone
    Optional: city, gender, calculation settings, and Janmapatrika identity metadata
    """
    try:
        from database.models import KundaliRecord

        session = _get_session()
        try:
            record = KundaliRecord(
                user_id=None,
                created_at=datetime.datetime.utcnow(),
                **_record_values(params),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record.id
        finally:
            session.close()
    except Exception as e:
        raise RuntimeError(f"Failed to save chart: {e}") from e


def update_chart(record_id: int, params: dict) -> int:
    """Replace one existing record in place and return its unchanged ID."""
    try:
        from database.models import KundaliRecord

        session = _get_session()
        try:
            record = (
                session.query(KundaliRecord)
                .filter(KundaliRecord.id == record_id)
                .first()
            )
            if record is None:
                raise ValueError(f"Chart record {record_id} does not exist")
            for key, value in _record_values(params).items():
                setattr(record, key, value)
            session.commit()
            return record.id
        finally:
            session.close()
    except Exception as e:
        raise RuntimeError(f"Failed to update chart: {e}") from e


def list_charts() -> list[dict]:
    """Return every saved kundali record (newest first)."""
    try:
        from database.models import KundaliRecord

        session = _get_session()
        try:
            records = (
                session.query(KundaliRecord)
                .filter(KundaliRecord.name.isnot(None))
                .order_by(KundaliRecord.created_at.desc())
                .all()
            )
            result = []
            for r in records:
                notes = {}
                try:
                    notes = json.loads(r.notes or "{}")
                except Exception:
                    pass
                result.append({
                    "id": r.id,
                    "name": r.name,
                    "birth_date": r.birth_date,
                    "birth_time": r.birth_time,
                    "latitude": r.latitude,
                    "longitude": r.longitude,
                    "timezone": r.timezone,
                    "timezone_id": r.timezone_id,
                    "country": r.country,
                    "birth_place": r.birth_place,
                    "gender": r.gender,
                    "full_name": r.full_name,
                    "father_name": r.father_name,
                    "mother_name": r.mother_name,
                    "gotra": r.gotra,
                    "surname": r.surname,
                    "kula": r.kula,
                    "kuladevata": r.kuladevata,
                    "spouse_name": r.spouse_name,
                    "marital_status": r.marital_status,
                    "caste": r.caste,
                    "religion": r.religion,
                    "family_details": r.family_details,
                    "ayanamsha_type": notes.get("ayanamsha_type", "LAHIRI"),
                    "node_type": notes.get("node_type", "MEAN"),
                    "house_system": notes.get("house_system", "WHOLE_SIGN"),
                    "region": notes.get("region") or notes.get("province"),
                    "province": notes.get("province") or notes.get("region"),
                    "district": notes.get("district"),
                    "life_events": notes.get("life_events", []),
                    "comments": notes.get("comments"),
                    "created_at": str(r.created_at)[:16] if r.created_at else "",
                })
            return result
        finally:
            session.close()
    except Exception:
        return []


def delete_chart(record_id: int) -> bool:
    """Delete a saved kundali record. Returns True on success."""
    try:
        from database.models import KundaliRecord

        session = _get_session()
        try:
            record = (
                session.query(KundaliRecord)
                .filter(KundaliRecord.id == record_id)
                .first()
            )
            if record:
                session.delete(record)
                session.commit()
                return True
            return False
        finally:
            session.close()
    except Exception:
        return False


def get_chart_params(record_id: int) -> Optional[dict]:
    """Return the calculation params dict for a saved record."""
    try:
        from database.models import KundaliRecord

        session = _get_session()
        try:
            r = (
                session.query(KundaliRecord)
                .filter(KundaliRecord.id == record_id)
                .first()
            )
            if not r:
                return None
            notes = {}
            try:
                notes = json.loads(r.notes or "{}")
            except Exception:
                pass
            gender_map = {"male": 0, "female": 1, "other": 2}
            return {
                "record_id": r.id,
                "name": r.name,
                "birth_date": r.birth_date,
                "birth_time": r.birth_time,
                "latitude": r.latitude,
                "longitude": r.longitude,
                "timezone": r.timezone,
                "timezone_id": r.timezone_id,
                "country": r.country,
                "city": r.birth_place,
                "birth_place": r.birth_place,
                "gender": gender_map.get(r.gender or "male", 0),
                "full_name": r.full_name,
                "father_name": r.father_name,
                "mother_name": r.mother_name,
                "gotra": r.gotra,
                "surname": r.surname,
                "kula": r.kula,
                "kuladevata": r.kuladevata,
                "spouse_name": r.spouse_name,
                "marital_status": r.marital_status,
                "caste": r.caste,
                "religion": r.religion,
                "family_details": r.family_details,
                "ayanamsha_type": notes.get("ayanamsha_type", "LAHIRI"),
                "node_type": notes.get("node_type", "MEAN"),
                "house_system": notes.get("house_system", "WHOLE_SIGN"),
                "region": notes.get("region") or notes.get("province"),
                "province": notes.get("province") or notes.get("region"),
                "district": notes.get("district"),
                "life_events": notes.get("life_events", []),
                "comments": notes.get("comments"),
            }
        finally:
            session.close()
    except Exception:
        return None
