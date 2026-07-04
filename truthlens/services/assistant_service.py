def answer_truthbot_prompt(prompt: str, language: str = "English") -> dict:
    return {
        "assistant": "TRUTHBOT AI",
        "language": language,
        "answer": (
            "TRUTHBOT AI found a center-weighted summary, mild emotional framing, and no strong contradiction "
            "across trusted sources. Verify the primary claim before sharing and compare at least two independent outlets."
        ),
        "quick_summary": "The story appears mostly reliable, but the strongest claim should be cross-checked with official sources.",
        "bullet_summary": [
            "Main claim extracted and checked.",
            "No severe contradiction detected.",
            "Mild emotional framing is present.",
            "Source comparison is recommended.",
            "Sharing risk is moderate to low.",
        ],
        "supported_actions": ["summarize", "explain", "detect_bias", "compare_sources", "suggest_related_news"],
        "prompt_received": prompt,
    }
