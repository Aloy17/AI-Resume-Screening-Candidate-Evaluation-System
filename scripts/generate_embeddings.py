
import json
import argparse
from pathlib import Path

from resume_screening.models import (
    ResumeData,
    ExperienceEntry,
    EducationEntry,
    ProjectEntry,
)
from resume_screening.embeddings.embedder import Embedder


def load_resume(data: dict) -> ResumeData:
    """Convert a JSON dictionary into a ResumeData object."""

    return ResumeData(
        candidate_id=data["candidate_id"],
        source_file=data.get("source_file", ""),
        skills=data.get("skills", []),
        experience=[
            ExperienceEntry(**entry)
            for entry in data.get("experience", [])
        ],
        education=[
            EducationEntry(**entry)
            for entry in data.get("education", [])
        ],
        projects=[
            ProjectEntry(**entry)
            for entry in data.get("projects", [])
        ],
        total_experience_years=data.get(
            "total_experience_years", 0.0
        ),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Generate embeddings for parsed resumes."
    )

    parser.add_argument(
        "--input",
        default="data/outputs/parsed_resumes.json",
        help="Path to parsed resume JSON.",
    )

    parser.add_argument(
        "--output",
        default="data/outputs/resume_embeddings.json",
        help="Path to save generated embeddings.",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return

    with input_path.open("r", encoding="utf-8") as file:
        input_data = json.load(file)

    resumes_data = input_data.get("resumes", [])

    if not resumes_data:
        print("No parsed resumes found in the input JSON.")
        return

    embedder = Embedder()
    embedded_resumes = []

    print(f"\nGenerating embeddings for {len(resumes_data)} resumes.\n")

    for resume_data in resumes_data:
        try:
            resume = load_resume(resume_data)

            section_embeddings = embedder.embed_resume_sections(resume)

            embedded_resumes.append({
                "candidate_id": resume.candidate_id,
                "source_file": resume.source_file,
                "embeddings": {
                    section: vector.tolist()
                    for section, vector in section_embeddings.items()
                },
            })

            print(f"[SUCCESS] {resume.source_file}")

        except Exception as error:
            print(
                f"[FAILED] {resume_data.get('source_file', 'Unknown')}: "
                f"{error}"
            )

    output = {
        "summary": {
            "total_resumes": len(resumes_data),
            "successfully_embedded": len(embedded_resumes),
            "failed": len(resumes_data) - len(embedded_resumes),
            "embedding_model": embedder.model_name,
        },
        "resumes": embedded_resumes,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(output, indent=4),
        encoding="utf-8",
    )

    print("\n========== EMBEDDING SUMMARY ==========")
    print(f"Total resumes:        {len(resumes_data)}")
    print(f"Successfully embedded: {len(embedded_resumes)}")
    print(f"Failed:               {len(resumes_data) - len(embedded_resumes)}")
    print(f"\nJSON saved to: {output_path}")
    print("=======================================")


if __name__ == "__main__":
    main()
