# Resume Screening and Ranking Process

## 1. Resume Upload

The recruiter uploads multiple PDF resumes along with a Job Description (JD).

## 2. Text Extraction

Text is extracted from each PDF using PyMuPDF. If a resume is scanned or contains images instead of selectable text, OCR (Tesseract) is used.

## 3. Information Extraction

The extracted text is cleaned and processed to identify:

- Technical skills
- Work experience
- Educational qualifications
- Projects
- Previous job roles and responsibilities

The result is a structured JSON document that is easy to process and compare.

## 4. Resume Embedding

A pretrained Sentence Transformer model (all-MiniLM-L6-v2) converts text sections into embeddings. Separate embeddings are generated for skills, experience descriptions and projects, rather than one embedding for the whole resume.

## 5. Comparison with Job Description

- Skills: checks whether the candidate has the required skills, including variations and related terminology.
- Experience: checks years of experience using numerical rules and compares previous responsibilities with the JD.
- Education: checks whether the qualification matches the required qualification.
- Projects: compares project descriptions with the JD responsibilities and requirements using cosine similarity.

## 6. Score Calculation

Each category gets an individual score. Scores are combined with predefined weights into an overall suitability score.

| Category | Initial weight |
| --- | --- |
| Technical Skills | 40% |
| Work Experience | 25% |
| Education | 15% |
| Projects | 20% |

These weights are initial examples and can be adjusted in `config/weights.yaml`.

## 7. Candidate Ranking

Candidates are sorted from highest to lowest final score. The recruiter sees the ranked list with each category score to understand the ranking.

## Conventions in this codebase

- Category scores and the final score are on a 0 to 100 scale.
- Weights must be non negative and sum to 1.0.
- Ties in final score are broken by skills score, then by candidate id, so output is deterministic.
