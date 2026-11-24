# Pipeline and Scoring Details

## 1. Inputs and execution

The application processes multiple resume PDFs from one directory and one PDF job description.

- The interactive CLI searches for job descriptions in `data/job_descriptions/`.
- Its default resume directory is `data/anonymized_resumes/`.
- The resume directory can be overridden with `--resumes`.
- A job description can be selected interactively or supplied with `--jd`.

The application runs locally through `python3 main.py` or the installed `resume-screening` command.

## 2. PDF text extraction

PyMuPDF extracts selectable text from each PDF. The extractor raises an error when a PDF is missing, is not a PDF, or contains no extractable text.

OCR is not implemented. Scanned/image-only PDFs are therefore unsupported.

## 3. Text cleaning

Extracted text is normalized before parsing. Cleaning includes Unicode normalization, line-ending normalization, joining words split by line-break hyphens, removing control and invisible formatting characters, and normalizing whitespace.

## 4. Rule-based information extraction

The parser uses Python code, regular expressions, section headings and keyword aliases. It does not use an LLM.

### Resume fields

- Candidate ID and source filename.
- Skills.
- Work experience: title, company, duration and responsibilities.
- Education: degree, field of study, institution and year.
- Projects: name, description and detected technologies.
- Total estimated experience in years.

### Job-description fields

- Job title.
- Required and preferred skills.
- Minimum and maximum experience.
- Required and preferred education.
- Responsibilities and explicit project requirements.
- Required and preferred certifications.
- Evaluation emphasis.

Extracting a field does not necessarily mean it participates in scoring. Certifications and evaluation emphasis are currently parsed but are not scoring categories.

## 5. Embeddings and cache

The default Sentence Transformers model is `all-MiniLM-L6-v2`.

The embedding cache is stored at:

`data/outputs/embedding_cache.json`

Each cache key is derived from the model name and exact input text. Cached vectors are reused when both match; missing vectors are generated, normalized and persisted.

The cache stores embeddings only. PDF extraction and parsing still happen on each pipeline run.

## 6. Category matching

Every candidate receives four category scores from 0 to 100.

### Skills

- Exact normalized matches are assigned first.
- Remaining skills are compared by cosine similarity.
- Semantic matches must meet a threshold of 0.75.
- Matching is one-to-one: a candidate skill cannot satisfy multiple target skills within the same group.
- When both required and preferred skills exist, their scores are combined 80:20. If only one group exists, that group supplies the score.
- If the job description contains no required or preferred skills, the score is 0.

### Experience

The years component compares the candidate's total estimated experience with the JD's minimum requirement.

- If the candidate is below the minimum, the score is proportional to candidate years divided by required minimum years.
- Meeting or exceeding the minimum produces 100; exceeding the maximum is not penalized.
- If both minimum and maximum are absent, the years score is 100.
- A minimum of zero does not impose a positive experience threshold.

When both candidate responsibilities and JD responsibilities are available, they are semantically compared with one-to-one assignment. The years and responsibility components are combined 70:30. If either side has no responsibility evidence, only the years score is used.

### Education

Education is compared using rule-based degree levels and field-of-study aliases. Required and preferred qualification scores are combined 80:20 when both are present. If only one is present, only that requirement is scored. If the JD specifies neither, the education score is 100.

### Projects

Project descriptions are compared only with explicit JD project requirements—not the general responsibilities section.

- Description similarity uses cosine similarity and a threshold of 0.65.
- Each project and each project requirement can be used in at most one description match.
- Technology overlap is an exact normalized comparison between detected project technologies and the JD's required and preferred skills.
- Description and technology scores are combined 70:30 when both are available. If only one component has usable evidence, the available component is used.
- A resume with no parsed projects receives 0.

## 7. Weighted final score

The four category scores are combined using a weight profile from `config/weights.yaml`. Weights must be non-negative and sum to 1.0.

### Default weights

| Category | Weight |
|---|---:|
| Skills | 40% |
| Experience | 25% |
| Education | 15% |
| Projects | 20% |

### Job-specific profiles

| Profile | Skills | Experience | Education | Projects |
|---|---:|---:|---:|---:|
| Python Developer | 40% | 25% | 10% | 25% |
| Cybersecurity Specialist | 35% | 30% | 10% | 25% |
| DevOps Engineer | 35% | 30% | 10% | 25% |
| Mobile Application Developer | 40% | 20% | 10% | 30% |

A profile is selected by normalizing the job-description filename stem and matching it to a profile key. If no profile matches, default weights are used.

The final score is the weighted sum of skills, experience, education and project scores.

## 8. Ranking

Candidates are ordered by:

1. Final score, descending.
2. Skills score, descending, to break final-score ties.
3. Candidate ID, ascending, to break remaining ties.

Ranks are assigned sequentially after sorting.

## 9. Output

By default, the CLI displays a terminal table with rank, candidate ID, final score and all four category scores.

When `--output` is supplied, the same ranked results are written as JSON. The JSON includes candidate ID, source filename, category scores, final score and rank.

## 10. Parsing diagnostic utility

`scripts/test_all_resumes.py` extracts and parses every PDF in a selected resume directory and writes structured JSON for inspection. It does not run matching, scoring or ranking.

## 11. Limitations and interpretation

- OCR is not available; PDFs need selectable text.
- Rule-based parsing is sensitive to resume and JD wording and layout.
- Parsed certifications are not currently scored.
- Scoring weights and thresholds are heuristic and have not been empirically validated against hiring outcomes.
- A high suitability score is not a probability of being hired and must not be treated as an automated hiring decision.
- Renaming PDF files does not remove names or other personal information from document contents or metadata.
