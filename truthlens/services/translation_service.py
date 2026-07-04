from truthlens.services.ai_client import generate_ai_text


def translate_text(text: str, target_language: str) -> str:
    """
    Translates text into the target language. Relies on AI text generation.
    """
    if not text:
        return ""
    
    if target_language == "English":
        return text

    prompt = f"Translate the following news text into the language '{target_language}'. Only return the translated text without commentary: \"{text}\""
    return generate_ai_text(prompt)
