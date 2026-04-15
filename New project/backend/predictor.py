from __future__ import annotations

import importlib.util
import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np

from backend.ngram_fallback import NGramFallbackPredictor
from backend.text_utils import normalize_text


class PredictorService:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        self.artifacts_dir = self.base_dir / "artifacts"
        self.data_dir = self.base_dir / "data"
        self.corpus_path = self.data_dir / "sample_corpus.txt"
        self.model_path = self.artifacts_dir / "next_word_model.keras"
        self.tokenizer_path = self.artifacts_dir / "tokenizer.pkl"
        self.metadata_path = self.artifacts_dir / "metadata.json"
        self.metrics_path = self.artifacts_dir / "metrics.json"

        self.model: Any | None = None
        self.tokenizer: Any | None = None
        self.sequence_length: int | None = None
        self.metadata: dict[str, Any] = {}
        self.metrics: dict[str, Any] = {}
        self.fallback = NGramFallbackPredictor.from_path(self.corpus_path)
        self.mode = "fallback"
        self.status_message = "Using the built-in statistical fallback predictor."
        self.load_error: str | None = None
        self.reload()

    def reload(self) -> None:
        self.model = None
        self.tokenizer = None
        self.sequence_length = None
        self.metadata = {}
        self.metrics = {}
        self.mode = "fallback"
        self.load_error = None
        self.status_message = "Using the built-in statistical fallback predictor."
        self.fallback = NGramFallbackPredictor.from_path(self.corpus_path)

        if not self.tensorflow_available:
            self.load_error = "TensorFlow is not installed in the current environment."
            return

        if not self.has_lstm_artifacts:
            self.load_error = "No trained LSTM artifacts were found in the artifacts folder."
            return

        try:
            self._load_lstm_predictor()
            self.mode = "lstm"
            self.status_message = "Using the trained LSTM model from the artifacts folder."
        except Exception as exc:  # pragma: no cover - runtime safeguard
            self.load_error = str(exc)

    @property
    def tensorflow_available(self) -> bool:
        return importlib.util.find_spec("tensorflow") is not None

    @property
    def has_lstm_artifacts(self) -> bool:
        return (
            self.model_path.exists()
            and self.tokenizer_path.exists()
            and self.metadata_path.exists()
        )

    def _load_lstm_predictor(self) -> None:
        from tensorflow.keras.models import load_model

        with self.metadata_path.open("r", encoding="utf-8") as handle:
            self.metadata = json.load(handle)

        if self.metrics_path.exists():
            with self.metrics_path.open("r", encoding="utf-8") as handle:
                self.metrics = json.load(handle)

        with self.tokenizer_path.open("rb") as handle:
            self.tokenizer = pickle.load(handle)

        self.model = load_model(self.model_path)
        self.sequence_length = int(self.metadata["sequence_length"])

    def health(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "status_message": self.status_message,
            "tensorflow_available": self.tensorflow_available,
            "has_lstm_artifacts": self.has_lstm_artifacts,
            "load_error": self.load_error,
            "artifacts_dir": str(self.artifacts_dir),
            "corpus_path": str(self.corpus_path),
            "metadata": self.metadata,
            "metrics": self.metrics,
        }

    def predict(self, text: str, top_n: int = 3) -> list[dict[str, Any]]:
        normalized = normalize_text(text)
        if not normalized:
            return []

        if self.mode == "lstm" and self.model is not None and self.tokenizer is not None:
            predictions = self._predict_with_lstm(normalized, top_n=top_n)
            if predictions:
                return predictions

        return self.fallback.predict(normalized, top_n=top_n)

    def _predict_with_lstm(
        self,
        text: str,
        top_n: int,
    ) -> list[dict[str, Any]]:
        from tensorflow.keras.preprocessing.sequence import pad_sequences

        token_list = self.tokenizer.texts_to_sequences([text])[0]
        if not token_list:
            return []

        padded = pad_sequences(
            [token_list],
            maxlen=self.sequence_length,
            padding="pre",
            truncating="pre",
        )
        probabilities = self.model.predict(padded, verbose=0)[0]
        top_indices = np.argsort(probabilities)[-(top_n * 4) :][::-1]

        index_to_word = getattr(self.tokenizer, "index_word", None)
        if index_to_word is None:
            index_to_word = {
                index: word for word, index in self.tokenizer.word_index.items()
            }

        results: list[dict[str, Any]] = []
        for index in top_indices:
            word = index_to_word.get(int(index), "")
            if not word or word == "<OOV>" or any(item["word"] == word for item in results):
                continue
            results.append(
                {
                    "word": word,
                    "score": round(float(probabilities[index]), 4),
                    "source": "lstm",
                }
            )
            if len(results) == top_n:
                break

        return results
