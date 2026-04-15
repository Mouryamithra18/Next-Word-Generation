from __future__ import annotations

import argparse
import json
import math
import pickle
import sys
from datetime import datetime, timezone
from pathlib import Path

from sklearn.model_selection import train_test_split

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.text_utils import sentence_chunks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train an LSTM next-word prediction model."
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path("data/sample_corpus.txt"),
        help="Path to the training corpus text file.",
    )
    parser.add_argument(
        "--artifacts-dir",
        type=Path,
        default=Path("artifacts"),
        help="Directory where the trained model and tokenizer will be saved.",
    )
    parser.add_argument("--epochs", type=int, default=18)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--embedding-dim", type=int, default=128)
    parser.add_argument("--lstm-units", type=int, default=192)
    parser.add_argument("--max-words", type=int, default=12000)
    parser.add_argument(
        "--max-sequences",
        type=int,
        default=25000,
        help="Cap the number of generated training sequences for faster experiments.",
    )
    parser.add_argument("--validation-size", type=float, default=0.15)
    return parser.parse_args()


def load_corpus(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"Corpus file is empty: {path}")
    return text


def build_sequences(text: str, tokenizer: object) -> list[list[int]]:
    sequences: list[list[int]] = []
    for sentence in sentence_chunks(text):
        encoded = tokenizer.texts_to_sequences([sentence])[0]
        if len(encoded) < 2:
            continue
        for stop in range(2, len(encoded) + 1):
            sequences.append(encoded[:stop])
    return sequences


def predict_top_words(
    model: object,
    tokenizer: object,
    text: str,
    sequence_length: int,
) -> list[str]:
    from tensorflow.keras.preprocessing.sequence import pad_sequences

    encoded = tokenizer.texts_to_sequences([text])[0]
    if not encoded:
        return []

    padded = pad_sequences(
        [encoded],
        maxlen=sequence_length,
        padding="pre",
        truncating="pre",
    )
    probabilities = model.predict(padded, verbose=0)[0]
    top_indices = probabilities.argsort()[-3:][::-1]
    index_to_word = getattr(tokenizer, "index_word", None) or {
        index: word for word, index in tokenizer.word_index.items()
    }
    return [
        index_to_word.get(int(index), "")
        for index in top_indices
        if index_to_word.get(int(index), "")
    ]


def main() -> None:
    args = parse_args()

    try:
        import numpy as np
        import tensorflow as tf
        from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
        from tensorflow.keras.layers import Dense, Embedding, LSTM
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.optimizers import Adam
        from tensorflow.keras.preprocessing.sequence import pad_sequences
        from tensorflow.keras.preprocessing.text import Tokenizer
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "TensorFlow is required for training. Use a Python 3.9-3.12 environment, "
            "then install it with `pip install -r requirements-lstm.txt`."
        ) from exc

    corpus_text = load_corpus(args.corpus)
    tokenizer = Tokenizer(
        num_words=args.max_words,
        oov_token="<OOV>",
        filters='!"#$%&()*+,-./:;=?@[\\]^_`{|}~\t\n',
        lower=True,
    )
    tokenizer.fit_on_texts([corpus_text])

    sequences = build_sequences(corpus_text, tokenizer)
    if not sequences:
        raise SystemExit("No training sequences were generated. Check the corpus content.")

    if args.max_sequences and len(sequences) > args.max_sequences:
        sequences = sequences[: args.max_sequences]

    max_sequence_length = max(len(sequence) for sequence in sequences)
    padded_sequences = pad_sequences(
        sequences,
        maxlen=max_sequence_length,
        padding="pre",
    )

    X = np.array(padded_sequences[:, :-1])
    y = np.array(padded_sequences[:, -1])

    X_train, X_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=args.validation_size,
        random_state=42,
        shuffle=True,
    )

    vocab_size = min(args.max_words, len(tokenizer.word_index) + 1)

    model = Sequential(
        [
            Embedding(vocab_size, args.embedding_dim, input_length=max_sequence_length - 1),
            LSTM(args.lstm_units, dropout=0.2),
            Dense(vocab_size, activation="softmax"),
        ]
    )
    model.compile(
        loss="sparse_categorical_crossentropy",
        optimizer=Adam(learning_rate=0.001),
        metrics=[
            "accuracy",
            tf.keras.metrics.SparseTopKCategoricalAccuracy(
                k=3,
                name="top3_accuracy",
            ),
        ],
    )

    callbacks = [
        EarlyStopping(
            monitor="val_top3_accuracy",
            mode="max",
            patience=3,
            restore_best_weights=True,
        ),
        ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=2,
            min_lr=1e-5,
        ),
    ]

    history = model.fit(
        X_train,
        y_train,
        validation_data=(X_val, y_val),
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
        verbose=1,
    )

    metrics = model.evaluate(X_val, y_val, return_dict=True, verbose=0)
    metrics = {key: float(value) for key, value in metrics.items()}
    metrics["perplexity"] = round(math.exp(min(metrics["loss"], 12)), 4)

    sample_prompts = [
        "machine learning",
        "next word",
        "the model",
        "users can",
    ]
    preview_predictions = {
        prompt: predict_top_words(
            model,
            tokenizer,
            prompt,
            sequence_length=max_sequence_length - 1,
        )
        for prompt in sample_prompts
    }

    args.artifacts_dir.mkdir(parents=True, exist_ok=True)
    model.save(args.artifacts_dir / "next_word_model.keras")
    with (args.artifacts_dir / "tokenizer.pkl").open("wb") as handle:
        pickle.dump(tokenizer, handle)

    metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "corpus_path": str(args.corpus),
        "sequence_length": max_sequence_length - 1,
        "vocab_size": vocab_size,
        "train_samples": int(len(X_train)),
        "validation_samples": int(len(X_val)),
        "epochs_completed": len(history.history["loss"]),
        "preview_predictions": preview_predictions,
    }
    with (args.artifacts_dir / "metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    with (args.artifacts_dir / "metrics.json").open("w", encoding="utf-8") as handle:
        json.dump(metrics, handle, indent=2)

    with (args.artifacts_dir / "history.json").open("w", encoding="utf-8") as handle:
        json.dump(
            {
                key: [float(item) for item in values]
                for key, values in history.history.items()
            },
            handle,
            indent=2,
        )

    print("Training complete.")
    print(json.dumps(metrics, indent=2))
    print(json.dumps(preview_predictions, indent=2))


if __name__ == "__main__":
    main()
