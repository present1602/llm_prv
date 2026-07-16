"""섹션별 프롬프트 오케스트레이터.

발명자 입력 + 이미 생성된 섹션들을 컨텍스트로 묶어,
각 섹션에 대한 system/user 프롬프트를 구성한다.
"""
from __future__ import annotations

from .schema import SectionSpec

SYSTEM_PROMPT = (
    "당신은 대한민국 특허청(KIPO) 서식에 따라 특허 명세서를 작성하는 "
    "숙련된 변리사 보조자입니다. 다음 원칙을 반드시 지키십시오.\n"
    "1. 발명자가 제공한 정보와 이미 작성된 다른 섹션의 내용에만 근거해 작성합니다.\n"
    "2. 존재하지 않는 선행문헌 번호, 논문, 특허번호를 지어내지 않습니다.\n"
    "3. 특허 명세서의 격식 있는 문어체(개조식이 아닌 서술체)를 사용합니다.\n"
    "4. 요청된 '해당 섹션의 본문'만 출력하고, 항목 제목·머리말·설명·군더더기를 붙이지 않습니다.\n"
    "5. 초안이며 변리사의 검토·수정을 전제로 함을 인지하고, 과장하거나 단정하지 않습니다."
)


def _invention_block(invention: dict) -> str:
    """발명자 입력을 프롬프트용 텍스트 블록으로."""
    lines = ["## 발명자 제공 정보"]
    fields = [
        ("발명의 제목/주제", invention.get("title_hint")),
        ("발명 설명", invention.get("description")),
        ("해결하려는 문제", invention.get("problem")),
        ("핵심 아이디어/특징", invention.get("key_features")),
        ("배경/종래기술", invention.get("background")),
        ("참고 자료(첨부문서에서 추출)", invention.get("reference_text")),
    ]
    for label, value in fields:
        if value and str(value).strip():
            lines.append(f"### {label}\n{str(value).strip()}")
    return "\n\n".join(lines)


def _context_block(generated: dict[str, str], depends_on: list[str]) -> str:
    """앞서 생성된 의존 섹션들을 컨텍스트로."""
    if not depends_on:
        return ""
    parts = ["## 이미 작성된 관련 섹션"]
    for key in depends_on:
        text = generated.get(key)
        if text:
            parts.append(f"### [{key}]\n{text}")
    return "\n\n".join(parts) if len(parts) > 1 else ""


def build_prompt(
    section: SectionSpec,
    invention: dict,
    generated: dict[str, str],
    *,
    extra_instruction: str | None = None,
) -> tuple[str, str]:
    """(system, user) 프롬프트를 반환."""
    blocks = [_invention_block(invention)]
    ctx = _context_block(generated, section.depends_on)
    if ctx:
        blocks.append(ctx)

    task = [
        f"## 작성할 섹션: 「{section.title}」",
        f"작성 지침: {section.guide}",
    ]
    if extra_instruction and extra_instruction.strip():
        task.append(f"추가 요청사항: {extra_instruction.strip()}")
    task.append(
        f"위 정보를 바탕으로 「{section.title}」 섹션의 본문만 작성하십시오. "
        "제목이나 설명 없이 본문 텍스트만 출력합니다."
    )
    blocks.append("\n".join(task))

    return SYSTEM_PROMPT, "\n\n".join(blocks)
