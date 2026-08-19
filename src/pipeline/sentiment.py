"""Memory-efficient financial sentiment inference through ONNX."""

import json
import logging
import os
import re
import subprocess
import threading
from pathlib import Path
from typing import Iterable, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCRIPT = Path(__file__).with_suffix(".mjs")
NODE_DEPENDENCY = PROJECT_ROOT / "node_modules" / "@huggingface" / "transformers"
_runtime_install_lock = threading.Lock()
logger = logging.getLogger(__name__)

POSITIVE_TERMS = frozenset(
    {
        "beat", "beats", "bullish", "buy", "growth", "gain", "gains",
        "outperform", "profit", "profits", "rally", "record", "strong",
        "surge", "upside", "upgrade",
    }
)
NEGATIVE_TERMS = frozenset(
    {
        "bearish", "cut", "decline", "downgrade", "drop", "falls", "fraud",
        "loss", "losses", "miss", "misses", "risk", "sell", "slump",
        "weak", "warning",
    }
)
TOKEN_PATTERN = re.compile(r"[A-Za-z]+")


def _enabled(name: str, default: str = "true") -> bool:
    return os.getenv(name, default).lower() in {"1", "true", "yes"}


def _heuristic_scores(texts: list[str]) -> list[list[float]]:
    """Return deterministic financial sentiment when ONNX is unavailable."""

    results = []
    for text in texts:
        tokens = [token.lower() for token in TOKEN_PATTERN.findall(text)]
        positive = sum(token in POSITIVE_TERMS for token in tokens)
        negative = sum(token in NEGATIVE_TERMS for token in tokens)
        evidence = positive + negative
        if evidence == 0:
            results.append([0.1, 0.1, 0.8])
            continue

        positive_ratio = (positive + 1) / (evidence + 2)
        directional_weight = 0.85
        results.append(
            [
                positive_ratio * directional_weight,
                (1 - positive_ratio) * directional_weight,
                1 - directional_weight,
            ]
        )
    return results


def _ensure_node_runtime() -> None:
    """Install inference dependencies when a legacy deploy skipped npm ci."""

    if NODE_DEPENDENCY.is_dir():
        return

    if not _enabled("SENTIMENT_RUNTIME_INSTALL_ENABLED", "false"):
        raise RuntimeError("Sentiment ONNX runtime is not installed")

    with _runtime_install_lock:
        if NODE_DEPENDENCY.is_dir():
            return

        try:
            result = subprocess.run(
                [
                    os.getenv("NPM_BINARY", "npm"),
                    "ci",
                    "--omit=dev",
                    "--no-audit",
                    "--no-fund",
                ],
                cwd=PROJECT_ROOT,
                env={**os.environ, "ONNXRUNTIME_NODE_INSTALL_CUDA": "skip"},
                text=True,
                capture_output=True,
                check=False,
                timeout=300,
            )
        except FileNotFoundError as error:
            raise RuntimeError("npm is required for sentiment inference") from error
        except subprocess.TimeoutExpired as error:
            raise RuntimeError("Installing sentiment dependencies timed out") from error

        if result.returncode != 0:
            detail = result.stderr.strip().splitlines()
            message = detail[-1] if detail else "unknown npm error"
            raise RuntimeError(f"Unable to install sentiment dependencies: {message}")
        if not NODE_DEPENDENCY.is_dir():
            raise RuntimeError("Sentiment dependencies were not installed correctly")


class SentimentPipeline:
    """Run a compact financial classifier without loading PyTorch."""

    def __init__(self, script_path: Optional[Path] = None, timeout: int = 300):
        self.script_path = Path(script_path or DEFAULT_SCRIPT)
        self.timeout = timeout
        if not self.script_path.is_file():
            raise RuntimeError(f"Sentiment runner not found: {self.script_path}")

    def analyze_batch(self, texts: Iterable[str], batch_size: int = 16) -> list[list[float]]:
        items = [str(text) for text in texts]
        if not items:
            return []

        try:
            return self._analyze_with_node(items, batch_size)
        except RuntimeError as error:
            if not _enabled("SENTIMENT_FALLBACK_ENABLED"):
                raise
            logger.warning("Using heuristic sentiment fallback: %s", error)
            return _heuristic_scores(items)

    def _analyze_with_node(
        self, items: list[str], batch_size: int
    ) -> list[list[float]]:
        _ensure_node_runtime()
        payload = json.dumps({"texts": items, "batchSize": batch_size})
        try:
            result = subprocess.run(
                [os.getenv("NODE_BINARY", "node"), str(self.script_path)],
                input=payload,
                text=True,
                capture_output=True,
                check=False,
                timeout=self.timeout,
            )
        except FileNotFoundError as error:
            raise RuntimeError("Node.js is required for FinBERT inference") from error
        except subprocess.TimeoutExpired as error:
            raise RuntimeError("Sentiment inference timed out") from error

        if result.returncode != 0:
            detail = result.stderr.strip().splitlines()
            message = detail[-1] if detail else "unknown inference error"
            raise RuntimeError(f"Sentiment inference failed: {message}")

        try:
            response = json.loads(result.stdout)
            scores = response["scores"]
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            raise RuntimeError("Sentiment model returned an invalid response") from error

        if len(scores) != len(items):
            raise RuntimeError("Sentiment model returned the wrong number of results")

        normalized = []
        for score in scores:
            values = [
                float(score.get("positive", 0)),
                float(score.get("negative", 0)),
                float(score.get("neutral", 0)),
            ]
            if any(value < 0 or value > 1 for value in values):
                raise RuntimeError("Sentiment model returned an invalid probability")
            normalized.append(values)
        return normalized

    def analyze(self, text: str) -> list[list[float]]:
        return self.analyze_batch([text])
