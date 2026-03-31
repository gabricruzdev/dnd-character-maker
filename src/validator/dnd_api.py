"""
Cliente para dnd5eapi.co — verificações de existência no SRD.
"""

from __future__ import annotations

import requests

BASE = "https://www.dnd5eapi.co/api/2014"
_TIMEOUT = 8

# Known official source abbreviations — content from these is trusted
OFFICIAL_SOURCES = {
    "PHB", "DMG", "XGtE", "TCoE", "FToD", "VGtM", "MToF", "MotM",
    "SCAG", "ERLW", "EGtW", "MOoT", "SaCoC", "VRGtR", "SjAiS", "DSotDQ",
    "GGtR", "AI", "BPGotG", "TBoMT", "PAitM",
    "VSoS",  # Valda's Spire of Secrets
}


def _slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace("'", "").replace(",", "")


def _exists(endpoint: str, name: str) -> bool | None:
    """Check if a resource exists in the SRD API. Returns True/False/None (on error)."""
    slug = _slugify(name)
    try:
        r = requests.get(f"{BASE}/{endpoint}/{slug}", timeout=_TIMEOUT)
        return r.status_code == 200
    except Exception:
        return None


def race_exists(name: str) -> bool | None:
    return _exists("races", name)


def class_exists(name: str) -> bool | None:
    return _exists("classes", name)


def spell_exists(name: str) -> bool | None:
    return _exists("spells", name)


def subclass_exists(name: str) -> bool | None:
    return _exists("subclasses", name)


def background_exists(name: str) -> bool | None:
    return _exists("backgrounds", name)


def equipment_exists(name: str) -> bool | None:
    return _exists("equipment", name)


def is_official_source(source: str) -> bool:
    return source.upper().strip() in OFFICIAL_SOURCES
