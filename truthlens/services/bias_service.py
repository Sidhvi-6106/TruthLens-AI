from truthlens.services.scoring import score_from_seed


def analyze_linguistic_bias(text: str) -> dict:
    """
    Performs text parsing to check for political, emotional, and propaganda markers.
    """
    if not text:
        return {"political_bias": "Center", "emotional_manipulation": 0, "propaganda_risk": 0}

    t_lower = text.lower()

    # 1. Political Bias Check
    left_words = ["progressive", "liberal", "socialist", "democrat", "welfare", "inequality", "green new deal", "regulation"]
    right_words = ["conservative", "republican", "libertarian", "market", "deregulation", "capitalism", "traditional", "taxes"]
    
    left_hits = sum(1 for w in left_words if w in t_lower)
    right_hits = sum(1 for w in right_words if w in t_lower)
    
    if left_hits > right_hits:
        political = "Left"
    elif right_hits > left_hits:
        political = "Right"
    else:
        political = "Center"

    # 2. Emotional Manipulation Check
    emotional_triggers = ["shocking", "horrifying", "miracle", "catastrophe", "outrageous", "panic", "crisis", "warning", "absolutely", "terrifying", "amazing"]
    emotional_hits = sum(1 for w in emotional_triggers if w in t_lower)
    # Scale score
    emotional_score = min(95, 10 + emotional_hits * 15 + (score_from_seed(text + "emo") % 15))

    # 3. Propaganda Risk Check
    propaganda_indicators = ["conspiracy", "agenda", "elite", "secret", "hidden truth", "censored", "mainstream media", "brainwash", "they don't want you to know"]
    propaganda_hits = sum(1 for w in propaganda_indicators if w in t_lower)
    propaganda_score = min(95, 5 + propaganda_hits * 20 + (score_from_seed(text + "prop") % 15))

    return {
        "political_bias": political,
        "emotional_manipulation": emotional_score,
        "propaganda_risk": propaganda_score
    }
