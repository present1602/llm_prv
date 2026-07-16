"""LLM 클라이언트.

Ollama의 OpenAI 호환 엔드포인트(/v1)를 사용한다.
백엔드 전체가 이 얇은 래퍼만 통해 LLM을 호출하므로,
나중에 vLLM 등 다른 OpenAI 호환 서버로 base_url/model만 바꿔 교체할 수 있다.
"""
from __future__ import annotations

import os

import httpx

# 환경변수로 런타임 교체 (Ollama → vLLM 등)
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "exaone3.5:7.8b")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "ollama")  # Ollama는 아무 값이나 허용
LLM_TIMEOUT = float(os.environ.get("LLM_TIMEOUT", "180"))


class LLMError(RuntimeError):
    pass


async def chat(
    system: str,
    user: str,
    *,
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> str:
    """OpenAI 호환 chat completion 호출. 생성된 텍스트를 반환한다."""
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    url = f"{LLM_BASE_URL.rstrip('/')}/chat/completions"
    headers = {"Authorization": f"Bearer {LLM_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        raise LLMError(
            f"LLM 서버에 연결할 수 없습니다 ({url}). "
            f"Ollama가 실행 중인지 확인하세요. 원인: {exc}"
        ) from exc

    if resp.status_code != 200:
        raise LLMError(f"LLM 오류 {resp.status_code}: {resp.text[:500]}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as exc:
        raise LLMError(f"예상치 못한 LLM 응답 형식: {data}") from exc


async def health() -> dict:
    """LLM 서버 및 모델 가용성 점검."""
    url = f"{LLM_BASE_URL.rstrip('/')}/models"
    headers = {"Authorization": f"Bearer {LLM_API_KEY}"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=headers)
        resp.raise_for_status()
        models = [m.get("id") for m in resp.json().get("data", [])]
        return {
            "ok": True,
            "base_url": LLM_BASE_URL,
            "configured_model": LLM_MODEL,
            "available_models": models,
            "model_ready": LLM_MODEL in models,
        }
    except httpx.HTTPError as exc:
        return {
            "ok": False,
            "base_url": LLM_BASE_URL,
            "configured_model": LLM_MODEL,
            "error": str(exc),
        }
