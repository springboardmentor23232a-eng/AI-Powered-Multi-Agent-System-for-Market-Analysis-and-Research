"""LLM access. The LLM writes words only: it never computes, retrieves or decides.

TemplateLLM is deterministic and offline (default, used in tests and when no key is set).
AnthropicLLM is an optional adapter; its output is rejected if it contains any number that
was not in the facts it was given, in which case the template text is used instead.
"""
import json
import re
from typing import Protocol

import httpx

from app.core.config import settings

POSITIVE = ("surge", "jump", "gain", "beat", "record", "growth", "upgrade", "win", "strong", "rise", "profit up", "outperform")
NEGATIVE = ("fall", "drop", "loss", "probe", "penalty", "downgrade", "fraud", "slump", "decline", "cut", "weak",
            "plunge", "ban", "fine", "miss", "slide", "investigation")


class LLMClient(Protocol):
    tokens_used: int

    def summarize(self, agent: str, facts: dict[str, str]) -> str: ...

    def classify_sentiment(self, headlines: list[str]) -> list[str]: ...


class TemplateLLM:
    tokens_used = 0

    def summarize(self, agent: str, facts: dict[str, str]) -> str:
        if not facts:
            return f"No {agent} figures were available."
        parts = "; ".join(f"{k.replace('_', ' ')}: {v}" for k, v in facts.items())
        return f"{agent.capitalize()} findings. {parts}."

    def classify_sentiment(self, headlines: list[str]) -> list[str]:
        out = []
        for h in headlines:
            low = h.lower()
            pos = sum(w in low for w in POSITIVE)
            neg = sum(w in low for w in NEGATIVE)
            out.append("positive" if pos > neg else "negative" if neg > pos else "neutral")
        return out


_NUM = re.compile(r"\d+(?:[.,]\d+)*")


def numbers_grounded(text: str, facts: dict[str, str]) -> bool:
    """True if every number in `text` appears in the formatted facts."""
    allowed = set(_NUM.findall(" ".join(facts.values())))
    return all(n in allowed for n in _NUM.findall(text))


class AnthropicLLM:
    """Unverified against the live API in this repo; failures fall back to TemplateLLM output."""

    def __init__(self, api_key: str, model: str | None = None, fallback: TemplateLLM | None = None):
        self.api_key, self.model = api_key, model or settings.llm_model
        self.fallback = fallback or TemplateLLM()
        self.tokens_used = 0

    def _call(self, system: str, prompt: str, max_tokens: int = 400) -> str:
        r = httpx.post(
            "https://api.anthropic.com/v1/messages", timeout=60,
            headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": self.model, "max_tokens": max_tokens, "system": system,
                  "messages": [{"role": "user", "content": prompt}]})
        r.raise_for_status()
        body = r.json()
        usage = body.get("usage", {})
        self.tokens_used += usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
        return "".join(b.get("text", "") for b in body["content"] if b.get("type") == "text").strip()

    def summarize(self, agent: str, facts: dict[str, str]) -> str:
        try:
            text = self._call(
                "You write 2-3 sentence equity research summaries. Use ONLY the figures provided. "
                "Do not introduce any other number, date, fact, forecast or advice.",
                f"Agent: {agent}\nFacts: {json.dumps(facts)}")
            if text and numbers_grounded(text, facts):
                return text
        except (httpx.HTTPError, KeyError, ValueError):
            pass
        return self.fallback.summarize(agent, facts)

    def classify_sentiment(self, headlines: list[str]) -> list[str]:
        try:
            raw = self._call(
                "Classify each headline's sentiment for the named company's investors. "
                'Reply with only a JSON array of "positive", "negative" or "neutral", one per headline, in order.',
                json.dumps(headlines))
            labels = json.loads(raw)
            if (isinstance(labels, list) and len(labels) == len(headlines)
                    and all(x in ("positive", "negative", "neutral") for x in labels)):
                return labels
        except (httpx.HTTPError, KeyError, ValueError):
            pass
        return self.fallback.classify_sentiment(headlines)


def build_llm() -> LLMClient:
    return AnthropicLLM(settings.llm_api_key) if settings.llm_api_key else TemplateLLM()
