
# AI Resume Screening and Candidate Evaluation System

A Python-based system that extracts information from PDF resumes, evaluates candidates against a job description, and produces a ranked list with category-wise scores.

## Features

- Extracts selectable text from PDF resumes and job descriptions using PyMuPDF.
- Parses skills, experience, education and projects using rule-based extraction.
- Generates semantic embeddings using Sentence Transformers.
- Automatically caches embeddings and reuses them across ranking runs.
- Scores candidates across four categories.
- Calculates weighted suitability scores.
- Ranks candidates deterministically.

## Pipeline

PDF Resumes + PDF Job Description
→ Text Extraction
→ Text Cleaning
→ Information Extraction
→ Embedding Generation and Cache Lookup
→ Category-wise Matching
→ Weighted Scoring
→ Candidate Ranking
→ JSON Output

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.13 |
| PDF extraction | PyMuPDF |
| Information extraction | Python regex and rule-based parsing |
| Embeddings | Sentence Transformers |
| Embedding model | all-MiniLM-L6-v2 |
| Numerical operations | NumPy |
| Configuration | YAML |
| Testing | pytest |

## Evaluation Categories

| Category | Default Weight |
|---|---:|
| Skills | 40% |
| Experience | 25% |
| Education | 15% |
| Projects | 20% |

Weights are configurable in `config/weights.yaml`. All weights must be non-negative and sum to 1.0.

## Embedding Cache

The system stores individual text embeddings in:

`data/outputs/embedding_cache.json`

When the ranking pipeline runs:

1. It checks the cache for each requested text and embedding model.
2. Existing embeddings are reused.
3. Missing embeddings are generated and saved.
4. Changed text or a different model produces a new cache entry.

The cache is generated automatically. No separate embedding-generation command is required.

## Project Structure

```text
.
├── config/
│   └── weights.yaml
├── data/
│   ├── resumes/
│   ├── job_descriptions/
│   └── outputs/
├── docs/
│   └── pipeline.md
├── scripts/
│   └── test_all_resumes.py
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
└── requirements.txt
```

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the project dependencies:

```bash
pip install -e ".[dev]"
```

Run the test suite:

```bash
PYTHONPATH=src python3 -m pytest -v
```

## Usage

Place PDF resumes in `data/resumes/` and PDF job descriptions in `data/job_descriptions/`.

Run the ranking pipeline:

```bash
PYTHONPATH=src python3 -m resume_screening.cli \
  --resumes data/resumes \
  --jd "data/job_descriptions/JD_Python_Dev.pdf" \
  --output data/outputs/ranking.json
```

The output contains candidate rankings, final suitability scores and individual category scores.

## Additional Utility

To export all resumes as structured JSON for inspection:

```bash
PYTHONPATH=src python3 scripts/test_all_resumes.py
```

## Current Limitations

- Scanned/image-only PDFs are not supported.
- Information extraction is rule-based and may miss information in unusual resume formats.
- Suitability scores are heuristic estimates, not hiring decisions.
- The system is currently a local CLI application.

## Data Privacy

Resume PDFs, job descriptions, generated outputs and embedding caches are stored locally. Files under `data/` are excluded from Git to avoid committing candidate information.
```

After saving, tell me. Then we'll update `docs/pipeline.md` to match this README and verify both documents against the actual implementation.