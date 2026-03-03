from __future__ import annotations

from app.constants import AI_KEYWORDS


def is_ai_related(title: str, snippet: str) -> bool:
    haystack = f"{title} {snippet}".lower()
    return any(keyword in haystack for keyword in AI_KEYWORDS)
