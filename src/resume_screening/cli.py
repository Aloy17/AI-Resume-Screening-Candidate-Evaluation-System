
"""Command line entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_weights
from .pipeline import run_pipeline


DEFAULT_RESUMES = "data/anonymized_resumes"
DEFAULT_JD_DIR = "data/job_descriptions"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="resume-screening",
        description="Rank PDF resumes against a PDF job description.",
    )

    parser.add_argument(
        "--resumes",
        default=DEFAULT_RESUMES,
        help="Directory containing PDF resumes.",
    )

    parser.add_argument(
        "--jd",
        default=None,
        help="Path to a PDF job description.",
    )

    parser.add_argument(
        "--weights",
        default=None,
        help="Path to a weights YAML file.",
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Optional path to save ranked results as JSON.",
    )

    return parser


def select_job_description(jd_dir: str) -> Path | None:
    """Display available job descriptions and let the user select one."""

    directory = Path(jd_dir)

    if not directory.is_dir():
        raise NotADirectoryError(
            f"Job description directory not found: {directory}"
        )

    job_descriptions = sorted(directory.glob("*.pdf"))

    if not job_descriptions:
        raise FileNotFoundError(
            f"No PDF job descriptions found in: {directory}"
        )

    print("\n" + "=" * 65)
    print("                 RESUME SCREENING SYSTEM")
    print("=" * 65)
    print("\nSelect a job description:\n")

    for index, jd_path in enumerate(job_descriptions, start=1):
        print(f"  {index}. {jd_path.stem}")

    print("\n  q. Quit")
    print()

    while True:
        try:
            choice = input("Enter your choice: ").strip().lower()

            if choice == "q":
                print("\nExiting Resume Screening System.")
                return None

            if not choice.isdigit():
                print("Invalid choice. Enter a number or 'q'.\n")
                continue

            choice = int(choice)

            if 1 <= choice <= len(job_descriptions):
                selected = job_descriptions[choice - 1]
                print(f"\nSelected: {selected.stem}\n")
                return selected

            print(
                f"Please choose a number between "
                f"1 and {len(job_descriptions)}, or 'q'.\n"
            )

        except (KeyboardInterrupt, EOFError):
            print("\n\nExiting Resume Screening System.")
            return None


def display_ranking(results: list) -> None:
    """Display candidate rankings in a formatted terminal table."""

    if not results:
        print("\nNo candidates were found.\n")
        return

    headers = [
        "Rank",
        "Candidate",
        "Final Score",
        "Skills",
        "Experience",
        "Education",
        "Projects",
    ]

    rows = []

    for result in results:
        scores = result.scores.to_dict()

        rows.append([
            str(result.rank),
            result.candidate_id,
            f"{result.final_score:.2f}",
            f"{scores['skills']:.2f}",
            f"{scores['experience']:.2f}",
            f"{scores['education']:.2f}",
            f"{scores['projects']:.2f}",
        ])

    widths = [
        max(
            len(headers[i]),
            max(len(row[i]) for row in rows),
        )
        for i in range(len(headers))
    ]

    def format_row(row: list[str]) -> str:
        return (
            "| "
            + " | ".join(
                value.ljust(widths[index])
                for index, value in enumerate(row)
            )
            + " |"
        )

    separator = (
        "+"
        + "+".join("-" * (width + 2) for width in widths)
        + "+"
    )

    print("\n")
    print("=" * len(separator))
    print("                    CANDIDATE RANKING")
    print("=" * len(separator))
    print()
    print(separator)
    print(format_row(headers))
    print(separator)

    for row in rows:
        print(format_row(row))

    print(separator)
    print(f"\nTotal candidates evaluated: {len(results)}")
    print()


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        jd_path = (
            Path(args.jd)
            if args.jd
            else select_job_description(DEFAULT_JD_DIR)
        )

        if jd_path is None:
            return 0

        print("Processing resumes. Please wait...\n")

        results = run_pipeline(
            args.resumes,
            str(jd_path),
            weights=(
                load_weights(args.weights, jd_path)
                if args.weights
                else None
            ),
        )

        if args.output:
            payload = [
                result.to_dict()
                for result in results
            ]

            output_json = json.dumps(
                payload,
                indent=4,
                ensure_ascii=False,
            )

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
            display_ranking(results)

        return 0

    except (
        FileNotFoundError,
        NotADirectoryError,
        ValueError,
    ) as error:
        print(f"\nError: {error}")
        return 1

    except (KeyboardInterrupt, EOFError):
        print("\n\nOperation cancelled.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
