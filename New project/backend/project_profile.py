from __future__ import annotations


PROJECT_PROFILE = {
    "title": "Next Word Prediction",
    "tagline": "A deep-learning-assisted typing helper for real-time word suggestion.",
    "abstract_summary": (
        "The project uses sequence modeling to predict relevant next words from "
        "user input and exposes those predictions through a web interface."
    ),
    "main_motive": (
        "Help users type faster and more accurately by suggesting context-aware "
        "next words in real time."
    ),
    "core_features": [
        "Real-time next-word suggestions",
        "Flask API with health and reload endpoints",
        "Fallback statistical predictor for demo readiness",
        "Corrected LSTM training pipeline with validation metrics",
        "Responsive frontend for classroom demo and deployment",
    ],
    "deployment_targets": [
        "Local Python environment",
        "Docker container",
        "Single-service Flask deployment with Waitress",
    ],
}
