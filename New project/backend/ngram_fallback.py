from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from backend.text_utils import sentence_chunks, tokenize_words


class NGramFallbackPredictor:
    def __init__(self, corpus_text: str) -> None:
        self.unigrams: Counter[str] = Counter()
        self.bigrams: defaultdict[tuple[str], Counter[str]] = defaultdict(Counter)
        self.trigrams: defaultdict[tuple[str, str], Counter[str]] = defaultdict(Counter)
        self.fit(corpus_text)

    @classmethod
    def from_path(cls, path: Path) -> "NGramFallbackPredictor":
        return cls(path.read_text(encoding="utf-8"))

    def fit(self, corpus_text: str) -> None:
        self.unigrams.clear()
        self.bigrams.clear()
        self.trigrams.clear()

        for sentence in sentence_chunks(corpus_text):
            words = tokenize_words(sentence)
            if len(words) < 2:
                continue

            tokens = ["<s>", "<s>", *words]
            for index in range(2, len(tokens)):
                current = tokens[index]
                previous = tokens[index - 1]
                previous_pair = (tokens[index - 2], previous)
                self.unigrams[current] += 1
                self.bigrams[(previous,)][current] += 1
                self.trigrams[previous_pair][current] += 1

    def predict(self, text: str, top_n: int = 3) -> list[dict[str, float | str]]:
        words = tokenize_words(text)
        counters: list[Counter[str]] = []

        if len(words) >= 2:
            trigram_counter = self.trigrams.get((words[-2], words[-1]))
            if trigram_counter:
                counters.append(trigram_counter)

        if words:
            bigram_counter = self.bigrams.get((words[-1],))
            if bigram_counter:
                counters.append(bigram_counter)

        counters.append(self.unigrams)

        results: list[dict[str, float | str]] = []
        seen: set[str] = set()

        for counter in counters:
            total = float(sum(counter.values())) or 1.0
            for word, count in counter.most_common(top_n * 3):
                if word in seen or word == "<s>":
                    continue
                results.append(
                    {
                        "word": word,
                        "score": round(count / total, 4),
                        "source": "fallback",
                    }
                )
                seen.add(word)
                if len(results) == top_n:
                    return results

        return results
