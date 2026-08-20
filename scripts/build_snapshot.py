#!/usr/bin/env python3
"""Refresh the static MarketSent dataset."""

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.snapshot import build_snapshot  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "frontend" / "public" / "data" / "marketsent.json",
    )
    parser.add_argument(
        "--model",
        action="store_true",
        help="Use the ONNX financial-language model instead of the deterministic fallback.",
    )
    args = parser.parse_args()
    snapshot = build_snapshot(args.output, use_model=args.model)
    status = ", ".join(
        f"{source['name']}: {source['item_count']} ({source['status']})"
        for source in snapshot["sources"]
    )
    print(f"Wrote {snapshot['count']} posts to {args.output} — {status}")


if __name__ == "__main__":
    main()
