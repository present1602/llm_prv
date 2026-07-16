"""KIPO 특허 명세서 항목 스키마.

특허 명세서는 한국 특허청(KIPO) 서식에 따라 정해진 항목들로 구성된다.
각 섹션을 독립적으로 생성/재생성할 수 있도록 스키마로 정의한다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SectionSpec:
    """명세서 한 섹션의 정의."""

    key: str  # 내부 식별자
    title: str  # 화면/문서에 표시되는 항목명
    guide: str  # LLM 생성 지침 (무엇을, 어떻게 써야 하는지)
    depends_on: list[str] = field(default_factory=list)  # 먼저 생성돼야 하는 섹션


# 생성 순서대로 나열 (앞 섹션 결과가 뒤 섹션의 컨텍스트가 됨)
SECTIONS: list[SectionSpec] = [
    SectionSpec(
        key="title",
        title="발명의 명칭",
        guide=(
            "발명의 대상을 간결하고 명확하게 나타내는 명칭을 작성한다. "
            "지나치게 광범위하거나 상표·모델명은 피하고, 기술적 대상을 드러낸다. "
            "20자 내외의 한 줄로 작성한다."
        ),
    ),
    SectionSpec(
        key="technical_field",
        title="기술분야",
        guide=(
            "본 발명이 속하는 기술분야를 1~2문장으로 기술한다. "
            "'본 발명은 ~에 관한 것으로, 보다 상세하게는 ~에 관한 것이다' 형식을 사용한다."
        ),
        depends_on=["title"],
    ),
    SectionSpec(
        key="background",
        title="배경기술",
        guide=(
            "종래기술의 구성과 그 문제점을 설명한다. "
            "발명자가 제공한 배경 정보 범위 내에서만 기술하고, "
            "존재하지 않는 특정 선행문헌 번호나 인용을 지어내지 않는다. "
            "3~5문장으로 작성한다."
        ),
        depends_on=["technical_field"],
    ),
    SectionSpec(
        key="problem",
        title="해결하려는 과제",
        guide=(
            "배경기술의 문제점을 바탕으로, 본 발명이 해결하고자 하는 기술적 과제를 "
            "명확한 항목으로 정리한다. '본 발명은 ~를 목적으로 한다' 형식을 사용한다."
        ),
        depends_on=["background"],
    ),
    SectionSpec(
        key="solution",
        title="과제의 해결 수단",
        guide=(
            "과제를 해결하기 위한 발명의 핵심 구성(수단)을 기술한다. "
            "구성요소와 그 결합 관계를 중심으로, 발명자가 설명한 내용에 근거해 작성한다. "
            "청구항의 기초가 되는 핵심 특징을 포함한다."
        ),
        depends_on=["problem"],
    ),
    SectionSpec(
        key="effect",
        title="발명의 효과",
        guide=(
            "해결 수단으로 인해 얻어지는 효과(이점)를 기술한다. "
            "해결 과제와 대응되도록 작성하며, 과장하지 않는다. 2~4문장."
        ),
        depends_on=["solution"],
    ),
    SectionSpec(
        key="embodiment",
        title="발명을 실시하기 위한 구체적인 내용",
        guide=(
            "발명의 구체적인 실시예를 상세히 기술한다. 구성요소들의 동작, 상호작용, "
            "구체적 수치·재료·순서 등을 발명자 입력에 근거해 서술한다. "
            "당업자가 재현할 수 있을 만큼 구체적으로 작성한다."
        ),
        depends_on=["solution"],
    ),
    SectionSpec(
        key="claims",
        title="청구범위",
        guide=(
            "특허청구범위를 작성한다. 독립항 1개와 필요한 종속항으로 구성한다. "
            "각 청구항은 '청구항 N' 으로 시작하고, 독립항은 발명의 핵심 구성을 "
            "포괄적으로, 종속항은 '제 N 항에 있어서,' 로 시작해 한정한다. "
            "해결 수단·실시예에 기재된 구성만 청구한다(기재불비 방지)."
        ),
        depends_on=["solution", "embodiment"],
    ),
    SectionSpec(
        key="abstract",
        title="요약서",
        guide=(
            "발명의 요지를 한 문단(3~5문장)으로 요약한다. "
            "기술분야, 해결 과제, 핵심 해결 수단, 효과가 드러나게 작성한다."
        ),
        depends_on=["solution", "effect"],
    ),
]

SECTION_BY_KEY: dict[str, SectionSpec] = {s.key: s for s in SECTIONS}


def get_section(key: str) -> Optional[SectionSpec]:
    return SECTION_BY_KEY.get(key)
