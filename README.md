# AI Resume Screening and Candidate Evaluation System

A local Python CLI that extracts structured information from PDF resumes, compares candidates with a PDF job description, and ranks candidates using rule-based parsing, semantic similarity and configurable weighted scores.

The system uses embeddings for matching. Resume and job-description information extraction is rule-based; no LLM is used.

## Features

- Extracts selectable PDF text with PyMuPDF. Scanned PDFs requiring OCR are not supported.
- Parses skills, work experience, education and projects using Python rules, regular expressions and keyword matching.
- Generates semantic embeddings with Sentence Transformers.
- Caches embeddings by model and input text to avoid recomputing unchanged vectors.
- Scores candidates across skills, experience, education and projects.
- Supports default and job-description-specific scoring weights.
- Displays a ranked table in the terminal and optionally exports results as JSON.

## How the pipeline works

1. Read PDF resumes and one PDF job description.
2. Extract selectable text and normalize it.
3. Parse resume and job-description fields into structured data.
4. Generate or retrieve cached text embeddings.
5. Calculate category scores.
6. Apply the selected weight profile and rank candidates.
7. Display the ranking or write it to JSON.

See [docs/pipeline.md](docs/pipeline.md) for the matching and scoring details.

## Technology

| Area | Technology |
|---|---|
| Language | Python 3.10+ |
| PDF text extraction | PyMuPDF |
| Parsing | Python, regular expressions and keyword rules |
| Semantic matching | Sentence Transformers |
| Embedding model | `all-MiniLM-L6-v2` |
| Numerical operations | NumPy |
| Configuration | YAML |
| Tests | pytest |

## Setup

Use Python 3.10 or newer. From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Input files

Place PDF job descriptions in:

```text
data/job_descriptions/
```

The interactive CLI looks in this directory and lets you select a job description.

By default, the CLI reads resumes from:

```text
data/anonymized_resumes/
```

Place your resume PDFs there, or pass another directory with `--resumes`. The diagnostic parsing script defaults to `data/resumes/`.

Input PDFs are not included in the repository. The `data/` directories are ignored by Git to reduce the risk of committing candidate information.

## Run the application

Start the interactive CLI:

```bash
python3 main.py
```

Select a job description from the displayed list. The CLI uses `data/anonymized_resumes/` unless another resume directory is supplied.

Run with explicit paths and export JSON:

```bash
python3 main.py \
  --resumes data/anonymized_resumes \
  --jd "data/job_descriptions/Job Description - Python Developer.pdf" \
  --output data/outputs/python_ranking.json
```

Without `--output`, results are displayed as a terminal table. The JSON export contains candidate IDs, source filenames, category scores, final scores and ranks.

See all supported arguments:

```bash
python3 main.py --help
```

## Scoring configuration

Edit [config/weights.yaml](config/weights.yaml) to change category weights. Each profile must contain non-negative weights that sum to 1.0.

The default profile is:

| Category | Weight |
|---|---:|
| Skills | 40% |
| Experience | 25% |
| Education | 15% |
| Projects | 20% |

The repository also defines profiles for the four supplied job-description filenames:

| Job description | Skills | Experience | Education | Projects |
|---|---:|---:|---:|---:|
| Python Developer | 40% | 25% | 10% | 25% |
| Cybersecurity Specialist | 35% | 30% | 10% | 25% |
| DevOps Engineer | 35% | 30% | 10% | 25% |
| Mobile Application Developer | 40% | 20% | 10% | 30% |

The profile is selected by normalizing the job-description filename stem. If no profile matches, the default weights are used.

An alternative YAML file can be supplied with `--weights`. The `WEIGHTS_FILE` environment variable can also set the configuration path.

## Embedding cache

Embeddings are stored in:

```text
data/outputs/embedding_cache.json
```

The cache key includes the embedding model name and exact input text. Existing vectors are reused; missing vectors are generated and saved automatically. PDFs are still extracted and parsed on each run—the cache does not store parsed resumes or job descriptions.

To use a different Sentence Transformers model, set the `EMBEDDING_MODEL` environment variable before starting the application.

The example environment file is a template, not automatically loaded by the application. Export its variables in your shell or source the file with export enabled.

## Tests and diagnostic utility

Run the test suite:

```bash
python3 -m pytest -q
```

To parse a directory of resumes and export the extracted fields for inspection:

```bash
PYTHONPATH=src python3 scripts/test_all_resumes.py \
  --resumes data/anonymized_resumes \
  --output data/outputs/parsed_resumes.json
```

This diagnostic utility does not perform candidate ranking.

## Project structure

```text
.
├── config/
│   └── weights.yaml
├── data/                       # Local input PDFs and generated output
├── docs/
│   └── pipeline.md
├── scripts/
│   └── test_all_resumes.py     # Parsing diagnostic/export utility
├── src/resume_screening/
│   ├── extraction/             # PDF text extraction
│   ├── parsing/                # Text cleaning and rule-based parsing
│   ├── embeddings/             # Sentence embeddings and cache
│   ├── matching/               # Skills, experience, education, projects
│   ├── scoring/                # Weighted final score
│   ├── ranking/                # Candidate ordering
│   ├── cli.py
│   ├── config.py
│   ├── models.py
│   └── pipeline.py
├── tests/
├── main.py
├── pyproject.toml
└── requirements.txt
```

## Limitations

- Scanned or image-only PDFs are unsupported; OCR is not implemented.
- Rule-based parsing can miss information in unusual layouts or wording.
- Certification fields can be extracted from job descriptions, but certifications are not currently included in candidate scoring.
- Scores are heuristic comparisons, not validated probabilities or hiring decisions.
- The application is a local CLI; it has no web interface, database or authentication.
- Renaming a resume file does not anonymize the PDF's contents or metadata. Review documents before sharing them.

## Data handling

Resume PDFs, job descriptions, generated JSON files and the embedding cache are intended to remain local. Git ignores files under `data/`; do not force-add personal candidate documents to the repository.
