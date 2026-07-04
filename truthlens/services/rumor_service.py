def check_rumor(claim: str) -> dict:
    """
    Dummy implementation for checking viral rumors across different languages and platforms.
    In a real app, this would use AI to match claims against a known rumor database.
    """
    rumors_db = [
        {"claim": "synthetic speech clip claims new banking rules", "status": "Misleading"},
        {"claim": "edited storm footage reused from 2022", "status": "Fake"},
        {"claim": "celebrity deepfake endorses investment app", "status": "Fake"},
        {"claim": "local school closure message lacks source", "status": "Unverified"},
    ]
    
    claim_lower = claim.lower()
    for r in rumors_db:
        if r["claim"] in claim_lower or claim_lower in r["claim"]:
            return {"match": True, "status": r["status"]}
            
    return {"match": False, "status": "Unknown"}
