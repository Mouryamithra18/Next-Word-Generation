from __future__ import annotations

import html
import re
from typing import Iterable


WORD_PATTERN = re.compile(r"[a-z]+(?:'[a-z]+)?")
SENTENCE_SPLIT = re.compile(r"[.!?\n]+")


def normalize_text(text: str) -> str:
    cleaned = html.unescape(text or "").lower()
    cleaned = cleaned.replace("’", "'")
    cleaned = re.sub(r"[^a-z0-9'?!.,\s-]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def tokenize_words(text: str) -> list[str]:
    return WORD_PATTERN.findall(normalize_text(text))


def sentence_chunks(text: str) -> Iterable[str]:
    normalized = normalize_text(text)
    for chunk in SENTENCE_SPLIT.split(normalized):
        chunk = chunk.strip()
        if chunk:
            yield chunk
