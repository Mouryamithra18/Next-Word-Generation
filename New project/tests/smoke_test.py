from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app import app


def main() -> None:
    client = app.test_client()

    routes = [
        ("/", client.get("/")),
        ("/api/health", client.get("/api/health")),
        ("/api/project-info", client.get("/api/project-info")),
        (
            "/api/predict",
            client.post("/api/predict", json={"text": "machine learning", "top_n": 3}),
        ),
    ]

    for route, response in routes:
        if response.status_code != 200:
            raise SystemExit(f"{route} failed with status {response.status_code}")
        print(f"{route}: OK")


if __name__ == "__main__":
    main()
