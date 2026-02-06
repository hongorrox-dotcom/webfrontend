from typing import Any
import httpx

from .config import settings


def _extract_text_from_chat_response(data: Any) -> str | None:
    if not isinstance(data, dict):
        return None

    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        choice = choices[0] or {}
        if isinstance(choice, dict):
            message = choice.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()
            text = choice.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()

    for key in ["output_text", "text", "content"]:
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()

    return None


def openai_explain_mn(prompt_mn: str) -> str:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OpenAI API key not configured (OPENAI_API_KEY).")

    base = settings.OPENAI_BASE_URL.rstrip("/")
    raw_path = settings.OPENAI_CHAT_PATH.strip()
    if not raw_path.startswith("/"):
        raw_path = "/" + raw_path

    path_candidates = [
        raw_path,
        "/chat/completions",
        "/v1/chat/completions",
    ]

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt_mn}],
        "temperature": 0.7,
    }

    timeout = httpx.Timeout(60.0)
    last_error: Exception | None = None
    with httpx.Client(timeout=timeout) as client:
        for path in path_candidates:
            url = f"{base}{path}"
            try:
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code == 429:
                    return "AI tailbar tur bolomjgui baina (OpenAI rate limit or quota). Daraa dahin oroldono uu."
                if resp.status_code in (401, 403):
                    return "AI tailbar bolomjgui baina (OpenAI auth error)."
                if resp.status_code >= 400:
                    last_error = RuntimeError(f"OpenAI API error: {resp.status_code} {resp.text}")
                    continue

                data = resp.json()
                text = _extract_text_from_chat_response(data)
                if text:
                    return text
                return str(data)
            except Exception as e:
                last_error = e
                continue

    raise RuntimeError(f"OpenAI API request failed: {last_error}")
