"""Memory-efficient financial sentiment inference through ONNX."""

import json
import os
import subprocess
import threading
from pathlib import Path
from typing import Iterable, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCRIPT = Path(__file__).with_suffix(".mjs")
NODE_DEPENDENCY = PROJECT_ROOT / "node_modules" / "@huggingface" / "transformers"
_runtime_install_lock = threading.Lock()


def _ensure_node_runtime() -> None:
    """Install inference dependencies when a legacy deploy skipped npm ci."""

    if NODE_DEPENDENCY.is_dir():
        return

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
