"""Conservative certification extraction and exact/alias matching."""
import re

CERTIFICATION_PATTERNS = {
    "AWS Certified Solutions Architect": [r"AWS Certified Solutions Architect", r"AWS SAA"],
    "AWS Certified Developer": [r"AWS Certified Developer"],
    "AWS Certified SysOps Administrator": [r"AWS Certified SysOps Administrator"],
    "Microsoft Azure Administrator": [r"Azure Administrator Associate", r"AZ-104"],
    "Microsoft Azure Fundamentals": [r"Azure Fundamentals", r"AZ-900"],
    "Google Professional Cloud Architect": [r"Google Professional Cloud Architect"],
    "Certified Kubernetes Administrator": [r"Certified Kubernetes Administrator", r"\bCKA\b"],
    "Certified Kubernetes Application Developer": [r"Certified Kubernetes Application Developer", r"\bCKAD\b"],
    "CompTIA Security+": [r"CompTIA Security\+"],
    "CISSP": [r"\bCISSP\b", r"Certified Information Systems Security Professional"],
    "CEH": [r"\bCEH\b", r"Certified Ethical Hacker"],
    "OSCP": [r"\bOSCP\b", r"Offensive Security Certified Professional"],
    "CCNA": [r"\bCCNA\b", r"Cisco Certified Network Associate"],
    "PMP": [r"\bPMP\b", r"Project Management Professional"],
    "Scrum Master": [r"Certified ScrumMaster", r"Professional Scrum Master"],
}

def extract_certifications(text: str) -> list[str]:
    found = []
    for name, patterns in CERTIFICATION_PATTERNS.items():
        if any(re.search(pattern, text or "", re.IGNORECASE) for pattern in patterns):
            found.append(name)
    return found

def evaluate_certification_match(resume_text: str, jd_text: str) -> dict:
    candidate = extract_certifications(resume_text)
    required = extract_certifications(jd_text)
    if not required:
        return {"score": None, "status": "not_required", "matched": [], "missing": [],
                "candidate_certifications": candidate}
    matched = [name for name in required if name in candidate]
    missing = [name for name in required if name not in candidate]
    return {"score": round(len(matched) / len(required) * 100, 2), "status": "scored",
            "matched": matched, "missing": missing, "candidate_certifications": candidate}
