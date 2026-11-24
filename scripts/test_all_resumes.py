
import argparse
import json
from pathlib import Path

from resume_screening.extraction import extract_text
from resume_screening.parsing.cleaner import clean_text
from resume_screening.parsing.info_extractor import parse_resume


def main():
    parser = argparse.ArgumentParser(
        description="Extract and export all PDF resumes as structured JSON."
    )

    parser.add_argument(
        "--resumes",
        default="data/resumes",
        help="Directory containing PDF resumes.",
    )

    parser.add_argument(
        "--output",
        default="data/outputs/parsed_resumes.json",
        help="Path for the generated JSON file.",
    )

    args = parser.parse_args()

    resume_dir = Path(args.resumes)
    output_path = Path(args.output)

    if not resume_dir.exists() or not resume_dir.is_dir():
        print(f"Resume directory not found: {resume_dir}")
        return

    pdf_files = sorted(resume_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF resumes found in {resume_dir}")
        return

    parsed_resumes = []
    failed_resumes = []

    print(f"\nFound {len(pdf_files)} resumes.\n")

    for pdf_path in pdf_files:
        try:
            raw_text = extract_text(pdf_path)
            cleaned_text = clean_text(raw_text)

            resume = parse_resume(
                clean_text=cleaned_text,
                candidate_id=pdf_path.stem,
                source_file=pdf_path.name,
            )

            parsed_resumes.append(resume.to_dict())

            print(f"[SUCCESS] {pdf_path.name}")

        except Exception as error:
            failed_resumes.append({
                "source_file": pdf_path.name,
                "error": str(error),
            })

            print(f"[FAILED] {pdf_path.name}: {error}")

    output = {
        "summary": {
            "total_resumes": len(pdf_files),
            "successfully_parsed": len(parsed_resumes),
            "failed": len(failed_resumes),
        },
        "resumes": parsed_resumes,
        "failed_resumes": failed_resumes,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(output, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )

    print("\n========== EXPORT SUMMARY ==========")
    print(f"Total resumes:       {len(pdf_files)}")
    print(f"Successfully parsed: {len(parsed_resumes)}")
    print(f"Failed:              {len(failed_resumes)}")
    print(f"\nJSON saved to: {output_path}")
    print("====================================")


if __name__ == "__main__":
    main()
