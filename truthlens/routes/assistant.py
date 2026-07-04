from flask import Blueprint, jsonify, request

from truthlens.services.assistant_service import answer_truthbot_prompt


assistant_bp = Blueprint("assistant", __name__)


@assistant_bp.post("/truthbot")
def truthbot():
    payload = request.get_json(silent=True) or {}
    prompt = str(payload.get("prompt", "")).strip() or "Can I trust this article?"
    language = str(payload.get("language", "English"))
    return jsonify(answer_truthbot_prompt(prompt, language))
