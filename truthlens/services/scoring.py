from hashlib import sha256


def score_from_seed(seed: str, minimum: int = 35, maximum: int = 98) -> int:
    digest = sha256(seed.encode("utf-8", errors="ignore")).hexdigest()
    value = int(digest[:8], 16)
    return minimum + value % (maximum - minimum + 1)


def score_label(score: int) -> str:
    if score >= 95:
        return "Verified"
    if score >= 75:
        return "Reliable"
    if score >= 50:
        return "Needs Verification"
    return "Potentially Misleading"


def build_truthlens_factors(seed: str) -> dict:
    return {
        "source_credibility": score_from_seed(seed + "source", 45, 99),
        "fact_consistency": score_from_seed(seed + "facts", 45, 99),
        "ai_detection_results": score_from_seed(seed + "ai", 45, 99),
        "cross_source_verification": score_from_seed(seed + "cross", 45, 99),
        "community_reports": score_from_seed(seed + "community", 45, 99),
        "historical_reliability": score_from_seed(seed + "history", 45, 99),
    }
