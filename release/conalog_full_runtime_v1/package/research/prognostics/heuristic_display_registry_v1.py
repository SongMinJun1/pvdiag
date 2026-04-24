#!/usr/bin/env python3
from __future__ import annotations

import math


# `_ko` fields are Korean display labels. Keep them operator/engineer-readable,
# and prefer precise field-facing terminology over overly softened wording.
# This registry intentionally covers only remapped heuristic-family labels and
# their short glossary notes. Longer report/README prose stays outside.
DISPLAY_HEURISTIC_NAME_MAP = {
    "다이오드·서브스트링형": "다이오드·서브스트링 이상형",
    "접속·부분개방형": "접속 불량·부분 개방형",
    "센서·피드백형": "센서·계측 피드백 이상형",
    "제어응답형": "제어 응답 이상형",
    "전력변환부형": "전력변환부 이상형",
    "외부계통교란형": "외부 계통 교란형",
}

HEURISTIC_DISPLAY_NOTE_MAP = {
    "다이오드·서브스트링 이상형": "서브스트링 단위 전류 불균형이나 바이패스 다이오드 이상처럼 국소 회로 문제를 우선 의심하는 라벨",
    "접속 불량·부분 개방형": "커넥터, 접속부, 배선 일부 개방처럼 접촉 저항 증가나 단속성 단선을 우선 의심하는 라벨",
    "센서·계측 피드백 이상형": "센서값, 계측 피드백, 측정 체인 이상 때문에 전기적 이상처럼 보일 수 있는 경우를 가리키는 라벨",
    "제어 응답 이상형": "MLPE나 제어기가 패널 상태 변화에 비정상적으로 응답하거나 추종이 흔들리는 경우를 가리키는 라벨",
    "전력변환부 이상형": "인버터, 전력변환부, 내부 전력 전자 회로 영향 가능성을 우선 두는 라벨",
    "외부 계통 교란형": "계통 전압 변동, 외부 전원 품질 저하, 공통 외란처럼 패널 외부 요인 가능성을 우선 두는 라벨",
}

LEGACY_HEURISTIC_DISPLAY_NAME_MAP = {
    "다이오드·국소 회로 이상형": "다이오드·서브스트링 이상형",
    "접촉 끊김 형": "접속 불량·부분 개방형",
    "장치 측정 이상형": "센서·계측 피드백 이상형",
    "장치 응답 이상형": "제어 응답 이상형",
    "외부 전원 흔들림형": "외부 계통 교란형",
}

LEGACY_HEURISTIC_DISPLAY_NAMES = frozenset(LEGACY_HEURISTIC_DISPLAY_NAME_MAP)


def normalize_display_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def display_heuristic_name(raw_label: object) -> str:
    normalized = normalize_display_text(raw_label)
    if not normalized:
        return ""
    if normalized in DISPLAY_HEURISTIC_NAME_MAP:
        return DISPLAY_HEURISTIC_NAME_MAP[normalized]
    if normalized in HEURISTIC_DISPLAY_NOTE_MAP:
        return normalized
    if normalized in LEGACY_HEURISTIC_DISPLAY_NAME_MAP:
        return LEGACY_HEURISTIC_DISPLAY_NAME_MAP[normalized]
    return normalized


def display_heuristic_note(raw_label: object) -> str:
    normalized = display_heuristic_name(raw_label)
    return HEURISTIC_DISPLAY_NOTE_MAP.get(normalized, "")


def contains_legacy_heuristic_display_name(value: object) -> bool:
    return normalize_display_text(value) in LEGACY_HEURISTIC_DISPLAY_NAMES
