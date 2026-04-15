from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from backend.predictor import PredictorService
from backend.project_profile import PROJECT_PROFILE


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
predictor = PredictorService(BASE_DIR)


@app.get("/")
def index() -> object:
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.get("/api/health")
def health() -> object:
    return jsonify(predictor.health())


@app.get("/api/project-info")
def project_info() -> object:
    return jsonify(
        {
            **PROJECT_PROFILE,
            "health": predictor.health(),
        }
    )


@app.post("/api/predict")
def predict() -> object:
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    top_n = max(1, min(int(payload.get("top_n", 3)), 5))

    if not text:
        return jsonify(
            {
                "mode": predictor.mode,
                "predictions": [],
                "message": "Type at least one word to receive suggestions.",
            }
        )

    return jsonify(
        {
            "mode": predictor.mode,
            "predictions": predictor.predict(text, top_n=top_n),
            "message": predictor.status_message,
        }
    )


@app.post("/api/reload")
def reload_predictor() -> object:
    predictor.reload()
    return jsonify(predictor.health())


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
