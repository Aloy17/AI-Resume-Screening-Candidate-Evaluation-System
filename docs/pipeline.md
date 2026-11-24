
# Resume Screening and Candidate Evaluation Pipeline

## 1. Input

The system accepts:

- Multiple PDF resumes from a directory.
- One PDF job description.

The CLI validates the input paths and processes PDF files.

## 2. Text Extraction

PyMuPDF extracts selectable text from each PDF.

The current implementation does not perform OCR. Scanned PDFs or PDFs without extractable text are unsupported and produce an extraction error.

## 3. Text Cleaning

Extracted text is normalized before parsing. Cleaning includes:

- Normalizing Unicode characters.
- Standardizing line endings.
- Rejoining words split across lines by hyphens.
- Removing control characters.
- Normalizing whitespace and blank lines.

## 4. Information Extraction

The rule-based parser converts the cleaned text into structured data.

### Resume information

- Candidate identifier and source filename.
- Technical skills.
- Work experience, including job titles, companies, durations and responsibilities.
- Education, including degrees, fields of study, institutions and years.
- Projects, including names, descriptions and technologies.
- Total estimated experience in years.

### Job description information

- Job title.
- Required and preferred skills.
- Minimum and maximum experience.
- Required and preferred education.
- Responsibilities.
- Project requirements.
- Required and preferred certifications.
- Evaluation emphasis.

The parser uses Python rules, regular expressions and keyword matching. It does not use an LLM.

## 5. Embedding Generation and Caching

The system uses the Sentence Transformers model `all-MiniLM-L6-v2` to convert text into numerical embeddings.

Embeddings are generated for the text used by the matching components, such as skills, responsibilities and project descriptions.

### Cache behaviour

The embedding cache is stored at:

`data/outputs/embedding_cache.json`

Each cache key is calculated using the embedding model name and input text. This means:

1. The system checks whether an embedding for the exact text and model already exists.
2. If it exists, the cached vector is reused.
3. If it does not exist, the model generates the embedding.
4. The new embedding is normalized and saved to the cache.

The cache is persistent across ranking runs. Changing the input text or embedding model results in a different cache key.

**Important:** The cache stores embeddings, not parsed resume or job description data. PDFs are still extracted and parsed whenever the ranking pipeline runs.

## 6. Candidate Matching

Each candidate is evaluated across four categories.

### Skills

Required and preferred skills are compared using exact matching and semantic similarity.

The best candidate skill match is considered for each target skill. Semantic similarity uses cosine similarity, with a threshold of 0.75.

Required and preferred skill scores are combined using an 80:20 weighting.

### Experience

Experience evaluation combines:

- A numerical comparison of the candidate's total experience against the job's minimum requirement.
- Semantic similarity between the candidate's responsibilities and the job description's responsibilities.

The two components use a 70:30 weighting.

### Education

Education is evaluated using rule-based comparisons of degree levels and fields of study against the required and preferred qualifications.

Required and preferred education scores use an 80:20 weighting.

### Projects

Project descriptions and technologies are compared against the job description's project requirements or responsibilities.

The project score combines semantic description similarity and technology overlap using a 70:30 weighting.

## 7. Weighted Scoring

Each matching category produces a score between 0 and 100.

The final suitability score is calculated using configurable weights.

| Category | Default Weight |
|---|---:|
| Skills | 40% |
| Experience | 25% |
| Education | 15% |
| Projects | 20% |

Weights are configured in `config/weights.yaml`. They must be non-negative and sum to 1.0.

The final score is the weighted sum of the four category scores.

## 8. Candidate Ranking

Candidates are sorted by:

1. Final suitability score, descending.
2. Skills score, descending, when final scores are tied.
3. Candidate ID, ascending, when both scores are tied.

Each candidate receives a sequential rank.

## 9. Output

The CLI exports the ranked candidates as JSON.

The output includes:

- Candidate identifier.
- Original resume filename.
- Individual category scores.
- Final suitability score.
- Candidate rank.

## 10. Diagnostic Utility

`scripts/test_all_resumes.py` can process all resume PDFs and export structured parsing results for inspection.

This utility is intended for diagnosing extraction and parsing quality. It is separate from the main ranking pipeline.

## Implementation Limitations

- Scanned or image-only PDFs are not supported because OCR is not implemented.
- Rule-based extraction may miss information in unusual resume formats.
- Embedding caching avoids regenerating unchanged vectors, but does not eliminate PDF extraction or parsing on subsequent runs.
- Scores are heuristic indicators of candidate suitability and should not be treated as automated hiring decisions.
