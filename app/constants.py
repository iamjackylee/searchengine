"""Shared constants used by both the FastAPI app and the ingestion scripts."""
from __future__ import annotations

# ── GDELT ────────────────────────────────────────────────────
GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"

# ── AI keyword filter ────────────────────────────────────────
AI_KEYWORDS: set[str] = {
    "ai",
    "artificial intelligence",
    "machine learning",
    "ml",
    "deep learning",
    "llm",
    "large language model",
    "generative",
    "neural network",
    "chatgpt",
    "openai",
    "anthropic",
    "gemini",
    "copilot",
}

# ── URL tracking parameters to strip during canonicalization ─
TRACKING_PREFIXES: tuple[str, ...] = (
    "utm_",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
)
