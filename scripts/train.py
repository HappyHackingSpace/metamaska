#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas", "scikit-learn", "joblib"]
# ///
"""Automated model training for metamaska.

Run with: uv run scripts/train.py

Reads data/processed/dataset.json, trains a TfidfVectorizer + SVC pipeline,
evaluates on a held-out test set, and saves the model to
metamaska/models/payload_clf.joblib.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.svm import SVC

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = REPO_ROOT / "data" / "processed" / "dataset.json"
MODEL_DIR = REPO_ROOT / "metamaska" / "models"
MODEL_PATH = MODEL_DIR / "payload_clf.joblib"

# Hyperparameters (tuned via GridSearchCV in notebooks/model/modeling.ipynb)
TFIDF_PARAMS = {
    "input": "content",
    "lowercase": True,
    "analyzer": "char",
    "max_features": 1024,
    "ngram_range": (1, 4),
}
SVC_PARAMS = {
    "C": 10,
    "kernel": "rbf",
    "probability": True,
}
TEST_SIZE = 0.25
RANDOM_STATE = 42
MIN_ACCURACY = 0.98


def main() -> None:
    if not DATASET_PATH.exists():
        log.error("Dataset not found at %s", DATASET_PATH)
        log.error("Run 'make collect-data' first.")
        sys.exit(1)

    log.info("Loading dataset from %s", DATASET_PATH)
    df = pd.read_json(DATASET_PATH, orient="records")
    log.info("  %d records, types: %s", len(df), sorted(df["type"].unique()))

    X = df["pattern"].to_numpy().astype(str)
    y = df["type"].to_numpy().astype(str)

    log.info("Splitting %d records (test_size=%.0f%%)", len(X), TEST_SIZE * 100)
    train_x, test_x, train_y, test_y = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y,
    )

    log.info("Training pipeline: TfidfVectorizer(char 1-4) → SVC(C=10, rbf)")
    pipe = make_pipeline(
        TfidfVectorizer(**TFIDF_PARAMS),
        SVC(**SVC_PARAMS),
    )
    pipe.fit(train_x, train_y)

    train_acc = pipe.score(train_x, train_y)
    test_acc = pipe.score(test_x, test_y)
    log.info("  Train accuracy: %.4f", train_acc)
    log.info("  Test accuracy:  %.4f", test_acc)

    preds = pipe.predict(test_x)
    log.info("\n%s", classification_report(test_y, preds))

    if test_acc < MIN_ACCURACY:
        log.error(
            "Test accuracy %.4f is below minimum threshold %.4f — aborting.",
            test_acc, MIN_ACCURACY,
        )
        sys.exit(1)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, MODEL_PATH, protocol=2, compress=3)
    log.info("Model saved to %s", MODEL_PATH)


if __name__ == "__main__":
    main()
