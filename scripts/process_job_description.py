
import json
from dataclasses import asdict
from pathlib import Path

from resume_screening.extraction import extract_text
from resume_screening.parsing.cleaner import clean_text
from resume_screening.parsing.info_extractor import parse_job_description
from resume_screening.embeddings.embedder import Embedder


INPUT_DIR = Path("data/job_descriptions")
OUTPUT_DIR = Path("data/outputs/job_descriptions")


def main():
    pdf_files = sorted(INPUT_DIR.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF job descriptions found in {INPUT_DIR}")
        return

    print(f"Found {len(pdf_files)} job descriptions.\n")

    embedder = Embedder()

    successful = 0
    failed = 0

    for pdf_path in pdf_files:
        try:
            # Step 1: Extract text from PDF.
            raw_text = extract_text(pdf_path)

            # Step 2: Clean extracted text.
            cleaned_text = clean_text(raw_text)

            # Step 3: Parse structured JD data.
            job = parse_job_description(cleaned_text)

            # Step 4: Generate embeddings for semantic fields.
            section_texts = {
                "required_skills": " ".join(job.required_skills),
                "preferred_skills": " ".join(job.preferred_skills),
                "responsibilities": " ".join(job.responsibilities),
                "project_requirements": " ".join(
                    job.project_requirements
                ),
            }

            embeddings = {}

            for section, text in section_texts.items():
                if text.strip():
                    embeddings[section] = (
                        embedder.embed([text])[0].tolist()
                    )
                else:
                    embeddings[section] = None

            # Step 5: Serialize every JobDescription field.
            job_data = asdict(job)
            job_data["source_file"] = pdf_path.name

            output = {
                "job_description": job_data,
                "embeddings": embeddings,
                "embedding_model": embedder.model_name,
            }

            # Step 6: Save JSON.
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

            output_path = OUTPUT_DIR / f"{pdf_path.stem}.json"

            output_path.write_text(
                json.dumps(
                    output,
                    indent=4,
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            successful += 1

            print(f"[SUCCESS] {pdf_path.name}")
            print(f"          Title: {job.title}")
            print(f"          Required skills: {len(job.required_skills)}")
            print(f"          Preferred skills: {len(job.preferred_skills)}")
            print(
                f"          Experience: "
                f"{job.min_experience_years}–"
                f"{job.max_experience_years} years"
            )
            print(
                f"          Responsibilities: "
                f"{len(job.responsibilities)}"
            )
            print(
                f"          Project requirements: "
                f"{len(job.project_requirements)}"
            )
            print(
                f"          Preferred certifications: "
                f"{len(job.preferred_certifications)}"
            )
            print(f"          JSON: {output_path}\n")

        except Exception as error:
            failed += 1
            print(f"[FAILED] {pdf_path.name}")
            print(f"         Reason: {error}\n")

    print("========== PROCESSING SUMMARY ==========")
    print(f"Total PDFs: {len(pdf_files)}")
    print(f"Successfully processed: {successful}")
    print(f"Failed: {failed}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("========================================")


if __name__ == "__main__":
    main()
