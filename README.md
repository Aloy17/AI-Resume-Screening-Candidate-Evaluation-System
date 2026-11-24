# AI Resume Screening and Candidate Evaluation System

Ranks multiple PDF resumes against a Job Description (JD) and shows a per category score breakdown for each candidate, so a recruiter can see why a candidate ranked where they did.

## Pipeline

PDF Resume → Text Extraction → Information Extraction → Structured JSON → Embeddings → Comparison with JD → Score Calculation → Candidate Ranking

| Stage | Module | Tooling |
| --- | --- | --- |
| Resume upload | `resume_screening.cli`, `resume_screening.pipeline` | CLI for now |
| Text extraction | `resume_screening.extraction` | PyMuPDF, Tesseract OCR fallback for scanned PDFs |
| Information extraction | `resume_screening.parsing` | Cleaning plus section parsing into structured JSON |
| Embeddings | `resume_screening.embeddings` | Sentence Transformers, all-MiniLM-L6-v2, per section |
| Comparison with JD | `resume_screening.matching` | Skills, experience, education, projects |
| Score calculation | `resume_screening.scoring` | Weighted sum of category scores |
| Candidate ranking | `resume_screening.ranking` | Sort high to low, keep category scores |

Default weights live in `config/weights.yaml`: skills 40%, experience 25%, education 15%, projects 20%. They are initial values and can be adjusted.

Full detail is in `docs/pipeline.md`.

## Project layout

```
.
├── config/
│   └── weights.yaml
├── data/
│   ├── resumes/
│   ├── job_descriptions/
│   └── outputs/
├── docs/
│   └── pipeline.md
├── src/
│   └── resume_screening/
│       ├── cli.py
│       ├── config.py
│       ├── models.py
│       ├── pipeline.py
│       ├── extraction/
│       ├── parsing/
│       ├── embeddings/
│       ├── matching/
│       ├── scoring/
│       └── ranking/
├── tests/
├── pyproject.toml
├── requirements.txt
└── .env.example
```

## Setup

Tesseract must be installed on the system for the OCR fallback.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
pytest
```

## Usage

```bash
resume-screening --resumes data/resumes --jd data/job_descriptions/jd.txt --output data/outputs/ranking.json
```

## Status

The structure, data models, config loading, score combination and ranking are implemented and tested. The extraction, parsing, embedding and matching stages are skeletons that raise `NotImplementedError` and are the next things to build.

Resumes contain personal information. Everything under `data/` is git ignored except the `.gitkeep` files.
