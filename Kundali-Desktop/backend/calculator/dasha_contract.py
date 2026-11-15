"""Shared, additive contracts for multi-system dasha reports.

This module deliberately contains no astronomical or classical dasha formula. It
only defines the transport/status shape and safe tree helpers used by later
system-specific calculators and native presentation code.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Iterable

DASHA_CONTRACT_VERSION = "1.0"
DASHA_LEVELS = {
    1: {"key": "mahadasha", "label_en": "Mahadasha", "label_ne": "महादशा"},
    2: {"key": "antardasha", "label_en": "Antardasha", "label_ne": "अन्तर्दशा"},
    3: {"key": "pratyantardasha", "label_en": "Pratyantardasha", "label_ne": "प्रत्यन्तरदशा"},
    4: {"key": "sookshmadasha", "label_en": "Sookshmadasha", "label_ne": "सूक्ष्मदशा"},
    5: {"key": "pranadasha", "label_en": "Pranadasha", "label_ne": "प्राणदशा"},
}

STATUS_READY = "ready"
STATUS_EMPTY = "empty"
STATUS_UNAVAILABLE = "unavailable"
STATUS_ERROR = "error"
STATUS_NO_CHART = "no_chart"


def unavailable_report(system: str, reason: str, *, error: bool = False) -> dict[str, Any]:
    """Return an explicit report state; never substitute fabricated periods."""
    return {
        "contract_version": DASHA_CONTRACT_VERSION,
        "system": system,
        "status": STATUS_ERROR if error else STATUS_UNAVAILABLE,
        "message": reason,
        "levels": [],
        "active_path": [],
        "periods": [],
    }


def report_from_tree(system: str, nodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Wrap an already-calculated tree in the additive normalized contract."""
    return {
        "contract_version": DASHA_CONTRACT_VERSION,
        "system": system,
        "status": STATUS_READY if nodes else STATUS_EMPTY,
        "message": "",
        "levels": sorted({int(node.get("level", 1)) for node in walk_periods(nodes)}),
        "active_path": active_path(nodes),
        "periods": nodes,
    }


def walk_periods(nodes: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
    """Yield every node without changing the source payload."""
    for node in nodes:
        yield node
        yield from walk_periods(node.get("children") or [])


def active_path(nodes: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return the active chain, or an empty list when no node is active."""
    for node in nodes:
        if node.get("is_active"):
            child_path = active_path(node.get("children") or [])
            return [node, *child_path]
    return []


def validate_tree(nodes: list[dict[str, Any]]) -> list[str]:
    """Validate structural invariants for a calculated period tree."""
    errors: list[str] = []

    def validate_siblings(items: list[dict[str, Any]], parent: dict[str, Any] | None = None) -> None:
        previous_end: date | None = None
        for index, node in enumerate(items):
            start_raw, end_raw = node.get("start"), node.get("end")
            try:
                start = date.fromisoformat(start_raw)
                end = date.fromisoformat(end_raw)
            except (TypeError, ValueError):
                errors.append(f"invalid interval at index {index}")
                continue
            if end <= start:
                errors.append(f"non-positive interval at index {index}")
            if previous_end is not None and start != previous_end:
                errors.append(f"non-contiguous siblings at index {index}")
            if parent and (start < date.fromisoformat(parent["start"]) or end > date.fromisoformat(parent["end"])):
                errors.append(f"child outside parent at index {index}")
            previous_end = end
            children = node.get("children") or []
            if children:
                validate_siblings(children, node)
                if children[-1].get("end") != node.get("end"):
                    errors.append(f"children do not end with parent at index {index}")

    validate_siblings(nodes)
    return errors


__all__ = [
    "DASHA_CONTRACT_VERSION",
    "DASHA_LEVELS",
    "STATUS_READY",
    "STATUS_EMPTY",
    "STATUS_UNAVAILABLE",
    "STATUS_ERROR",
    "STATUS_NO_CHART",
    "unavailable_report",
    "report_from_tree",
    "walk_periods",
    "active_path",
    "validate_tree",
]
