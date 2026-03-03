from __future__ import annotations

import yaml

from app.config import settings


def load_sources(file_path: str | None = None) -> dict:
    path = file_path or settings.sources_file
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    data.setdefault("rss_sources", [])
    data.setdefault("gdelt_sources", [])
    return data
