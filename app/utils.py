from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_PREFIXES = ("utm_", "fbclid", "gclid", "mc_cid", "mc_eid")


def canonicalize_url(url: str) -> str:
    split = urlsplit(url.strip())
    query_items = [
        (k, v)
        for k, v in parse_qsl(split.query, keep_blank_values=True)
        if not any(k.lower().startswith(prefix) for prefix in TRACKING_PREFIXES)
    ]
    cleaned_query = urlencode(query_items)
    clean_path = split.path or "/"
    normalized = urlunsplit((split.scheme.lower(), split.netloc.lower(), clean_path.rstrip("/"), cleaned_query, ""))
    return normalized
