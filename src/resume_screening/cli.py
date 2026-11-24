"""Command line entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_weights
from .pipeline import run_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="resume-screening",
        description="Rank PDF resumes against a job description.",
    )
    parser.add_argument("--resumes", required=True, help="Directory containing PDF resumes")
    parser.add_argument("--jd", required=True, help="Path to the job description text file")
    parser.add_argument("--weights", default=None, help="Path to a weights YAML file")
    parser.add_argument("--output", default=None, help="Write ranked results as JSON to this path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results = run_pipeline(args.resumes, args.jd, weights=load_weights(args.weights))
    payload = [r.to_dict() for r in results]

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(payload, indent=2))
    else:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
