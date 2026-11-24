# AI Resume Screening & Candidate Evaluation System

A local resume-screening application that compares multiple ATS-readable PDF resumes against one job description and ranks candidates using five transparent categories:

- Technical skills
- Work experience
- Education
- Projects
- Certifications

The application uses the existing `src/resume_screening` pipeline and its role-based weight profiles. It displays each candidate's final score, category scores, applied weights, mandatory requirement checks and matching evidence. Resumes that fail PDF extraction or ATS-format validation are listed separately with a reason.

## Run the web application

Python 3.10 or newer is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

## Screen candidates

1. Select a job description from `data/job_descriptions/`, or upload a PDF/TXT job description.
2. Upload one or more candidate resume PDFs (up to 30 per run).
3. Select **Screen and rank candidates**.
4. Review the ranked shortlist and expand a candidate to inspect category scores, weights, mandatory checks and detailed evidence.

You can also add reusable job descriptions to `data/job_descriptions/`; they will appear in the selector when the page is refreshed.

## Input handling

- Job descriptions: PDF or TXT.
- Resumes: text-based, ATS-readable PDFs.
- Scanned/image-only resumes are not OCR-processed; they are rejected when usable text cannot be extracted.
- Uploaded files are processed in a temporary directory and removed after the request completes.
- The web server binds to `127.0.0.1`, so it is intended for local use.

## Automated tests

```bash
python -m pytest -v
```

## Important limitation

Scores are text-matching indicators to support human review. They are not a measure of job performance and should not be used as the sole basis for rejecting a candidate.
