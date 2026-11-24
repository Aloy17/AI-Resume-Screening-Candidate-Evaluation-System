# Resume screening pipeline

## Input
- One job description in selectable-text PDF or TXT format.
- One or more selectable-text PDF resumes.
- Scanned/image-only PDFs are rejected. OCR is deliberately not used.

## Processing
1. PyMuPDF extracts selectable PDF text.
2. Text is normalized and resumes are checked for minimum text and recognizable standard section headings.
3. Resume and JD information is parsed into structured Python dictionaries (serializable to JSON).
4. Skills are matched using normalized names and aliases.
5. Experience is assessed using parsed duration and semantic similarity between prior responsibilities and JD responsibilities.
6. Education is evaluated using degree level and field of study.
7. Project descriptions are compared semantically with JD responsibilities.
8. Certifications are matched using an explicit certification alias catalogue.
9. Five category scores are combined using a deterministic role profile. Categories that cannot be evaluated are excluded and remaining weights are renormalized.
10. Candidates are ranked by final score. Evidence and missing mandatory requirements are retained in the JSON output.

## Role profiles
Software-development roles emphasize projects and education. DevOps and cybersecurity roles emphasize experience and certifications. The profile rules are explicit in the scoring module; they are heuristics, not an AI model deciding weights.

## Run
Install dependencies with `pip install -r requirements.txt`, then run:

```bash
python -m src.resume_screening.cli --jd data/job_descriptions/role.pdf --resumes resumes/*.pdf --output data/outputs/results.json
```

Use a `.txt` JD path when preferred. Results are written as JSON.

## Limitations
- Resume section recognition is heuristic and should be validated against varied real-world resume layouts.
- Certification recognition covers the explicit aliases in the certification matcher; it is not an exhaustive global certification registry.
- The final score is a decision-support signal, not a hiring decision. Review supporting evidence and mandatory checks before shortlisting.
