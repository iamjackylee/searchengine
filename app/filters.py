from __future__ import annotations

AI_KEYWORDS = {
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


def is_ai_related(title: str, snippet: str) -> bool:
    haystack = f"{title} {snippet}".lower()
    return any(keyword in haystack for keyword in AI_KEYWORDS)
