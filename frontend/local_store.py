import os
import json
from datetime import datetime


_BASE = os.path.dirname(os.path.abspath(__file__))
_PATH = os.path.join(_BASE, "local_store.json")


def _load() -> dict:
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    try:
        with open(_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_cleared_at(key: str) -> str | None:
    if not key:
        return None
    data = _load()
    section = data.get("chat_clear") or {}
    return section.get(key)


def set_cleared_now(key: str) -> None:
    if not key:
        return
    data = _load()
    section = data.get("chat_clear") or {}
    section[key] = datetime.utcnow().isoformat()
    data["chat_clear"] = section
    _save(data)


# --- Read state ---
def get_last_read(key: str) -> str | None:
    if not key:
        return None
    data = _load()
    section = data.get("chat_last_read") or {}
    return section.get(key)


def set_last_read_now(key: str) -> None:
    if not key:
        return
    data = _load()
    section = data.get("chat_last_read") or {}
    section[key] = datetime.utcnow().isoformat()
    data["chat_last_read"] = section
    _save(data)


# --- Title overrides (e.g., Study Buddy Session (Course)) ---
def get_title_override(key: str) -> str | None:
    if not key:
        return None
    data = _load()
    section = data.get("chat_title_overrides") or {}
    return section.get(key)


def set_title_override(key: str, value: str) -> None:
    if not key:
        return
    data = _load()
    section = data.get("chat_title_overrides") or {}
    if value:
        section[key] = value
    else:
        section.pop(key, None)
    data["chat_title_overrides"] = section
    _save(data)
