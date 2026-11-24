
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
        description="Rank PDF resumes against a PDF job description.",
    )

    parser.add_argument(
        "--resumes",
        required=True,
        help="Directory containing PDF resumes.",
    )

    parser.add_argument(
        "--jd",
        required=True,
        help="Path to the PDF job description.",
    )

    parser.add_argument(
        "--weights",
        default=None,
        help="Path to a weights YAML file.",
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Write ranked results as JSON to this path.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        results = run_pipeline(
            args.resumes,
            args.jd,
            weights=load_weights(args.weights),
        )

        payload = [result.to_dict() for result in results]

        output_json = json.dumps(
            payload,
            indent=4,
            ensure_ascii=False,
        )

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            output_path.write_text(
                output_json,
                encoding="utf-8",
            )

            print(f"Ranked results saved to: {output_path}")

        else:
            print(output_json)

        return 0

    except (FileNotFoundError, NotADirectoryError, ValueError) as error:
        print(f"Error: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
