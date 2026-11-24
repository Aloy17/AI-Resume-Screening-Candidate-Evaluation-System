"""End-to-end PDF resume screening pipeline."""
from pathlib import Path
import json
import re

from src.resume_screening.extraction.text_extractor import extract_text_from_pdf
from src.resume_screening.parsing.cleaner import clean_text
from src.resume_screening.parsing.info_extractor import extract_resume_information
from src.resume_screening.parsing.jd_extractor import extract_job_description_information
from src.resume_screening.matching.skills import evaluate_skill_match
from src.resume_screening.matching.experience import evaluate_experience_match
from src.resume_screening.matching.education import evaluate_education_match
from src.resume_screening.matching.semantic import evaluate_semantic_match
from src.resume_screening.matching.projects import evaluate_project_match
from src.resume_screening.matching.certifications import evaluate_certification_match
from src.resume_screening.scoring.scorer import determine_weights, calculate_final_score
from src.resume_screening.ranking.ranker import rank_candidates

ATS_HEADINGS={"education","experience","work experience","professional experience","skills","technical skills","projects","certifications","summary","profile","objective","internship experience"}

def validate_resume_text(text):
    if len(text.strip()) < 120:
        raise ValueError("Resume text is too short to be valid.")
    headings=set()
    for line in text.splitlines():
        heading=re.sub(r"[^a-z ]","",line.lower()).strip()
        if heading in ATS_HEADINGS: headings.add(heading)
    if len(headings)<2:
        raise ValueError("Resume lacks recognizable standard sections; upload an ATS-readable text PDF.")

def load_job_description(path):
    path=Path(path)
    if path.suffix.lower()==".pdf": raw=extract_text_from_pdf(path)
    elif path.suffix.lower()==".txt": raw=path.read_text(encoding="utf-8")
    else: raise ValueError("Job descriptions must be .pdf or .txt files.")
    raw=clean_text(raw)
    if len(raw)<40: raise ValueError("Job description is empty or too short.")
    return raw,extract_job_description_information(raw)

def _experience_score(resume,jd,semantic):
    duration=evaluate_experience_match(resume,jd)
    numeric=duration.get("experience_match_percentage")
    semantic_score=semantic.get("experience_semantic_score") if semantic else None
    if numeric is None and semantic_score is None: return None,duration
    if numeric is None: score=semantic_score
    elif semantic_score is None: score=numeric
    else: score=.5*numeric+.5*semantic_score
    duration["responsibility_semantic_score"]=semantic_score
    duration["experience_category_score"]=round(score,2)
    return round(score,2),duration

def evaluate_candidate(pdf_path,jd_raw,jd,weights=None):
    path=Path(pdf_path)
    raw=extract_text_from_pdf(path)
    validate_resume_text(raw)
    resume=extract_resume_information(clean_text(raw))
    skills=evaluate_skill_match(resume,jd)
    education=evaluate_education_match(resume,jd)
    try: semantic=evaluate_semantic_match(resume,jd)
    except ValueError: semantic=None
    projects=evaluate_project_match(resume,jd)
    certifications=evaluate_certification_match(raw,jd_raw)
    experience_score,experience=_experience_score(resume,jd,semantic)
    scores={
      "skills":skills["overall_skill_match_percentage"] if jd.get("required_skills") or jd.get("preferred_skills") else None,
      "experience":experience_score,
      "education":education["overall_education_match_percentage"] if jd.get("education_required") else None,
      "projects":projects["score"],
      "certifications":certifications["score"],
    }
    scoring=calculate_final_score(scores,weights or determine_weights(jd))
    return {"filename":path.name,"final_score":scoring["final_score"],"category_scores":scores,
      "weights_configured":scoring["weights_configured"],"weights_applied":scoring["weights_applied"],
      "excluded_categories":scoring["excluded_categories"],
      "mandatory_checks":{"minimum_experience_met":experience.get("meets_minimum_requirement"),
        "missing_required_skills":skills["required_skill_match"]["missing_skills"]},
      "details":{"skills":skills,"experience":experience,"education":education,
        "projects":projects,"certifications":certifications,"semantic_evidence":semantic}}

def screen_resumes(resume_paths,jd_path,weights=None):
    if not resume_paths: raise ValueError("Provide at least one resume PDF.")
    jd_raw,jd=load_job_description(jd_path)
    results=[]; rejected=[]
    for path in resume_paths:
        try: results.append(evaluate_candidate(path,jd_raw,jd,weights))
        except (ValueError,FileNotFoundError,OSError) as exc: rejected.append({"filename":Path(path).name,"reason":str(exc)})
    ranked=rank_candidates(results)
    for item in ranked: item["rejected_candidates"]=rejected
    return ranked

def save_results(results,output_path):
    output=Path(output_path); output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding="utf-8")
