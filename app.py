"""Local web interface for the existing five-category resume screening pipeline."""
from __future__ import annotations

import logging
import tempfile
import threading
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from src.resume_screening.pipeline import (
    evaluate_candidate,
    load_job_description,
)
from src.resume_screening.ranking.ranker import rank_candidates
from src.resume_screening.scoring.scorer import determine_weights

ROOT = Path(__file__).resolve().parent
JD_DIR = ROOT / "data" / "job_descriptions"
WEB_DIR = ROOT / "web"
MAX_RESUMES = 30
MAX_UPLOAD_BYTES = 60 * 1024 * 1024

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
logger = logging.getLogger("resume_screening.web")
_screening_lock = threading.Lock()


def _json_error(message: str, status: int = 400):
    return jsonify({"error": message}), status


@app.get("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.get("/api/setup")
def setup():
    descriptions = []
    if JD_DIR.is_dir():
        descriptions = [
            {"file": p.name, "title": p.stem}
            for p in sorted(JD_DIR.iterdir())
            if p.is_file() and p.suffix.lower() in {".pdf", ".txt"}
        ]
    return jsonify({"job_descriptions": descriptions, "max_resumes": MAX_RESUMES})


@app.post("/api/screen")
def screen():
    uploads = [f for f in request.files.getlist("resumes") if f and f.filename]
    if not uploads:
        return _json_error("Upload at least one resume PDF.")
    if len(uploads) > MAX_RESUMES:
        return _json_error(f"Upload no more than {MAX_RESUMES} resumes.")
    for item in uploads:
        if Path(item.filename or "").suffix.lower() != ".pdf":
            return _json_error(f"{item.filename} is not a PDF. Resume files must be PDFs.")

    jd_upload = request.files.get("jd_file")
    selected_jd = request.form.get("jd", "").strip()
    if not (jd_upload and jd_upload.filename) and not selected_jd:
        return _json_error("Choose or upload a job description.")

    try:
        with tempfile.TemporaryDirectory(prefix="resume-screening-") as temp:
            temp_dir = Path(temp)
            if jd_upload and jd_upload.filename:
                jd_name = secure_filename(jd_upload.filename)
                if Path(jd_name).suffix.lower() not in {".pdf", ".txt"}:
                    return _json_error("Job descriptions must be PDF or TXT files.")
                jd_path = temp_dir / jd_name
                jd_upload.save(jd_path)
            else:
                # Resolve only a filename from the known JD directory; never trust a client path.
                jd_path = (JD_DIR / Path(selected_jd).name).resolve()
                if jd_path.parent != JD_DIR.resolve() or not jd_path.is_file():
                    return _json_error("The selected job description could not be found.")

            resume_dir = temp_dir / "resumes"
            resume_dir.mkdir()
            resume_paths = []
            used_names = set()
            for index, item in enumerate(uploads, start=1):
                safe_name = secure_filename(item.filename or "") or f"resume-{index}.pdf"
                if safe_name in used_names:
                    stem, suffix = Path(safe_name).stem, Path(safe_name).suffix
                    safe_name = f"{stem}-{index}{suffix}"
                used_names.add(safe_name)
                target = resume_dir / safe_name
                item.save(target)
                resume_paths.append(target)

            jd_raw, jd = load_job_description(jd_path)
            weights = determine_weights(jd)
            candidates, rejected = [], []
            with _screening_lock:
                for path in resume_paths:
                    try:
                        candidates.append(evaluate_candidate(path, jd_raw, jd, weights))
                    except (ValueError, OSError) as exc:
                        rejected.append({"filename": path.name, "reason": str(exc)})
                ranked = rank_candidates(candidates)

            return jsonify({
                "job_description": jd_path.name,
                "weights": weights,
                "candidates": ranked,
                "rejected": rejected,
                "disclaimer": (
                    "Scores are text-matching indicators to support human review. "
                    "They are not a measure of job performance and should not be used "
                    "as the sole basis for rejecting a candidate."
                ),
            })
    except ValueError as exc:
        return _json_error(str(exc))
    except Exception:
        logger.exception("Resume screening request failed")
        return _json_error("Screening failed. Check the terminal for details.", 500)


@app.errorhandler(413)
def upload_too_large(_error):
    return _json_error("The combined upload is too large. Keep it below 60 MB.", 413)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    print("Resume screener available at http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
