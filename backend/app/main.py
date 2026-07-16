"""특허 명세서 초안 자동 작성 — MVP 백엔드 (FastAPI).

폐쇄형: 외부 API를 호출하지 않고 로컬 LLM(Ollama)만 사용한다.
"""
from __future__ import annotations

import io

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from . import llm
from .export import to_docx, to_markdown
from .parser import extract_pdf_text
from .prompts import build_prompt
from .schema import SECTIONS, get_section

app = FastAPI(title="특허 명세서 초안 생성기", version="0.1.0")

# MVP: 로컬 프론트(React dev 서버)에서의 접근 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- 모델 ----

class Invention(BaseModel):
    title_hint: str | None = Field(None, description="발명 제목/주제 힌트")
    description: str | None = Field(None, description="발명 설명 (핵심 입력)")
    problem: str | None = None
    key_features: str | None = None
    background: str | None = None
    reference_text: str | None = Field(None, description="첨부문서에서 추출한 텍스트")


class GenerateRequest(BaseModel):
    invention: Invention
    sections: list[str] | None = Field(
        None, description="생성할 섹션 key 목록. 미지정 시 전체."
    )


class RegenerateRequest(BaseModel):
    invention: Invention
    section: str
    generated: dict[str, str] = Field(default_factory=dict)
    extra_instruction: str | None = None


class ExportRequest(BaseModel):
    generated: dict[str, str]


# ---- 엔드포인트 ----

@app.get("/api/health")
async def health():
    return {"service": "ok", "llm": await llm.health()}


@app.get("/api/sections")
async def list_sections():
    return [
        {"key": s.key, "title": s.title, "guide": s.guide, "depends_on": s.depends_on}
        for s in SECTIONS
    ]


@app.post("/api/parse")
async def parse_document(file: UploadFile = File(...)):
    """첨부 PDF에서 텍스트 추출."""
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "현재 MVP는 PDF만 지원합니다.")
    data = await file.read()
    try:
        text = extract_pdf_text(data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"PDF 파싱 실패: {exc}") from exc
    return {"filename": file.filename, "chars": len(text), "text": text}


@app.post("/api/generate")
async def generate(req: GenerateRequest):
    """명세서 섹션들을 순차 생성. 앞 섹션 결과가 뒤 섹션 컨텍스트가 된다."""
    invention = req.invention.model_dump()
    target_keys = req.sections or [s.key for s in SECTIONS]

    generated: dict[str, str] = {}
    for section in SECTIONS:  # 스키마 순서 유지 (의존성 보장)
        if section.key not in target_keys:
            continue
        system, user = build_prompt(section, invention, generated)
        try:
            text = await llm.chat(system, user)
        except llm.LLMError as exc:
            raise HTTPException(502, str(exc)) from exc
        generated[section.key] = text

    return {"generated": generated}


@app.post("/api/regenerate")
async def regenerate(req: RegenerateRequest):
    """단일 섹션 재생성 (추가 지시 반영 가능)."""
    section = get_section(req.section)
    if section is None:
        raise HTTPException(404, f"알 수 없는 섹션: {req.section}")
    invention = req.invention.model_dump()
    system, user = build_prompt(
        section, invention, req.generated, extra_instruction=req.extra_instruction
    )
    try:
        text = await llm.chat(system, user)
    except llm.LLMError as exc:
        raise HTTPException(502, str(exc)) from exc
    return {"section": req.section, "text": text}


@app.post("/api/export/markdown")
async def export_markdown(req: ExportRequest):
    md = to_markdown(req.generated)
    return StreamingResponse(
        io.BytesIO(md.encode("utf-8")),
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=specification.md"},
    )


@app.post("/api/export/docx")
async def export_docx(req: ExportRequest):
    data = to_docx(req.generated)
    return StreamingResponse(
        io.BytesIO(data),
        media_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        headers={"Content-Disposition": "attachment; filename=specification.docx"},
    )
