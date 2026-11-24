from src.resume_screening.matching.certifications import evaluate_certification_match, extract_certifications

def test_extracts_known_certification_aliases():
    assert "CISSP" in extract_certifications("Certified Information Systems Security Professional (CISSP)")
    assert "Certified Kubernetes Administrator" in extract_certifications("CKA certified")

def test_matches_required_certifications():
    result = evaluate_certification_match("Holder of CompTIA Security+ and CISSP", "Required: CISSP and CEH")
    assert result["matched"] == ["CISSP"]
    assert result["missing"] == ["CEH"]
    assert result["score"] == 50

def test_no_certification_requirement_is_not_scored():
    assert evaluate_certification_match("AWS experience", "No certificate required")["score"] is None
