"""문서 파서.

발명자가 제출하는 첨부 문서(PDF)에서 텍스트를 추출해
LLM 입력 컨텍스트(reference_text)로 활용한다.
file_samples/ 의 KIPO 실제 문서로 검증한다.
"""
from __future__ import annotations

import io

import pdfplumber

MAX_CHARS = 20_000  # 컨텍스트 폭주 방지


def extract_pdf_text(data: bytes, *, max_chars: int = MAX_CHARS) -> str:
    """PDF 바이트에서 텍스트를 추출한다."""
    chunks: list[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if text.strip():
                chunks.append(text)
    joined = "\n\n".join(chunks).strip()
    if len(joined) > max_chars:
        joined = joined[:max_chars] + "\n…(이하 생략)"
    return joined


def extract_pdf_file(path: str, *, max_chars: int = MAX_CHARS) -> str:
    with open(path, "rb") as f:
        return extract_pdf_text(f.read(), max_chars=max_chars)
