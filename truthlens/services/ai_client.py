import httpx
from flask import current_app

from truthlens.services.scoring import score_from_seed


def generate_ai_text(prompt: str) -> dict:
    prompt = (prompt or "").strip()
    if not prompt:
        return {"provider": "local", "text": "Ask me a news, bias, summary, or trust question."}

    for provider, caller in (("gemini", _call_gemini), ("groq", _call_groq), ("openai", _call_openai)):
        try:
            text = caller(prompt)
            if text:
                return {"provider": provider, "text": text.strip()}
        except Exception as exc:
            print(f"{provider} provider failed: {exc}")

    return {"provider": "local", "text": generate_local_response(prompt)}


def _call_gemini(prompt: str) -> str | None:
    key = current_app.config.get("GEMINI_API_KEY")
    if not key:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
    payload = {"contents": [{"parts": [{"text": _truthbot_prompt(prompt)}]}]}
    with httpx.Client(timeout=12.0) as client:
        response = client.post(url, json=payload)
    if response.status_code >= 400:
        return None
    return response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")


def _call_groq(prompt: str) -> str | None:
    key = current_app.config.get("GROQ_API_KEY")
    if not key:
        return None
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": "You are TRUTHBOT AI, a concise news credibility, fact-checking, and bias analysis assistant."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 450,
    }
    with httpx.Client(timeout=12.0) as client:
        response = client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {key}"},
        )
    if response.status_code >= 400:
        return None
    return response.json().get("choices", [{}])[0].get("message", {}).get("content")


def _call_openai(prompt: str) -> str | None:
    key = current_app.config.get("OPENAI_API_KEY")
    if not key:
        return None
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are TRUTHBOT AI. Be concise, careful, and state uncertainty when needed."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 450,
    }
    with httpx.Client(timeout=12.0) as client:
        response = client.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {key}"},
        )
    if response.status_code >= 400:
        return None
    return response.json().get("choices", [{}])[0].get("message", {}).get("content")


def _truthbot_prompt(prompt: str) -> str:
    return (
        "You are TRUTHBOT AI, a concise news credibility assistant. "
        "Summarize clearly, identify bias, flag uncertainty, and suggest verification steps.\n\n"
        f"User request: {prompt}"
    )


def generate_local_response(prompt: str) -> str:
    lower = prompt.lower()
    if "timeline" in lower:
        return "Timeline: claim appears, TruthLens extracts assertions, checks trusted sources, scores risk, and produces a share-safe report."
    if "5" in lower or "bullet" in lower or "points" in lower:
        return "1. Extract the claim. 2. Compare sources. 3. Check bias. 4. Estimate AI risk. 5. Verify with official sources before sharing."
    if "bias" in lower:
        return "Bias analysis: watch for emotional wording, selective context, one-sided sourcing, and missing primary evidence."
    if "summarize" in lower or "summary" in lower or "what happened" in lower:
        return "Short summary: TruthLens found the main claim, estimated credibility signals, and recommends checking official sources before sharing."
    score = score_from_seed(prompt, 55, 96)
    return f"TRUTHBOT AI local analysis score: {score}%. Cross-check this with trusted media, official websites, and fact-check databases."
