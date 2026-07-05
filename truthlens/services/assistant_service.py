from truthlens.services.ai_client import generate_ai_text


def answer_truthbot_prompt(prompt: str, language: str = "English") -> dict:
    ai_result = generate_ai_text(prompt)
    answer = ai_result["text"]
    return {
        "assistant": "TRUTHBOT AI",
        "language": language,
        "provider": ai_result["provider"],
        "answer": answer,
        "quick_summary": answer[:260],
        "bullet_summary": [
            "Main claim extracted.",
            "Trust and bias signals reviewed.",
            "AI-generated text risk considered.",
            "Cross-source verification recommended.",
            "Share only after checking primary sources.",
        ],
        "supported_actions": ["summarize", "explain", "detect_bias", "compare_sources", "suggest_related_news"],
        "prompt_received": prompt,
    }
