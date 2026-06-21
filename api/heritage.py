"""
국가유산청 오픈API - 천연기념물 수목 조회
Endpoint: https://www.cha.go.kr/cha/SearchKindOpenapiList.do
API 키 불필요 (국가유산청 공개 API)
ccbaKdcd=15: 천연기념물
"""

from __future__ import annotations
import httpx
import time
import xml.etree.ElementTree as ET
from typing import Any

ENDPOINT = "https://www.cha.go.kr/cha/SearchKindOpenapiList.do"
CCBA_KDCD_NATURAL = "16"  # 천연기념물

# 수목 판별 키워드
TREE_KEYWORDS = [
    "나무", "숲", "소나무", "은행나무", "느티나무", "팽나무",
    "왕버들", "참나무", "잣나무", "향나무", "전나무", "주목", "측백",
    "회화나무", "벚나무", "동백나무", "후박나무", "비자나무", "모감주나무",
    "이팝나무", "대나무", "노거수", "곰솔", "금강송", "송림", "백송",
]

_cache: dict[str, tuple[Any, float]] = {}
CACHE_TTL = 3600


def _cache_get(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry and time.time() < entry[1]:
        return entry[0]
    return None


def _cache_set(key: str, data: Any) -> None:
    _cache[key] = (data, time.time() + CACHE_TTL)


async def fetch_heritage_trees(
    sido: str = "",
    page_no: int = 1,
    num_of_rows: int = 100,
) -> dict:
    """
    천연기념물 수목 목록 조회

    Returns:
        { "totalCount": int, "items": [ {...}, ... ] }
    """
    cache_key = f"heritage:{sido}:{page_no}:{num_of_rows}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    params: dict[str, Any] = {
        "ccbaKdcd": CCBA_KDCD_NATURAL,
        "pageUnit": num_of_rows,
        "pageIndex": page_no,
    }
    if sido:
        params["ccsiName"] = sido

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(ENDPOINT, params=params)
        resp.raise_for_status()
        xml_text = resp.text

    items, total = _parse_xml(xml_text)
    tree_items = [
        item for item in items
        if _is_tree(item) and item.get("ccbaCncl", "N") != "Y"
    ]

    result = {"totalCount": total, "items": tree_items}
    _cache_set(cache_key, result)
    return result


async def fetch_heritage_raw_sample() -> dict:
    """디버그용 — 원본 XML 파싱 결과 반환"""
    params = {
        "ccbaKdcd": CCBA_KDCD_NATURAL,
        "pageUnit": 3,
        "pageIndex": 1,
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(ENDPOINT, params=params)
        xml_text = resp.text

    items, total = _parse_xml(xml_text)
    return {
        "totalCount": total,
        "sample_item": items[:1],
        "sample_keys": list(items[0].keys()) if items else [],
        "raw_xml_preview": xml_text[:500],
    }


def _parse_xml(xml_text: str) -> tuple[list[dict], int]:
    """XML 응답 파싱 → (items, totalCount)"""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return [], 0

    total_el = root.find(".//totalCnt")
    total = int(total_el.text or 0) if total_el is not None and total_el.text else 0

    items = []
    for item_el in root.findall(".//item"):
        item: dict[str, str] = {}
        for child in item_el:
            item[child.tag] = (child.text or "").strip()
        items.append(item)

    return items, total


def _is_tree(item: dict) -> bool:
    """천연기념물 항목이 수목인지 판별 (실제 이름은 ccbaMnm1에 있음)"""
    name = item.get("ccbaMnm1", "")
    return any(kw in name for kw in TREE_KEYWORDS)


def normalize_heritage_tree(raw: dict) -> dict:
    """국가유산청 API 응답 → 보호수 표준 필드로 변환"""
    name = raw.get("ccbaMnm1", "")
    sido = raw.get("ccbaCtcdNm", "")   # 예: "대구", "강원"
    sigungu = raw.get("ccsiName", "")  # 예: "동구", "강릉시"
    cpno = raw.get("ccbaCpno", "")
    address = f"{sido} {sigungu}".strip()

    return {
        "source":         "천연기념물",
        "tree_id":        cpno,
        "designation":    name,
        "type":           "천연기념물",
        "species":        _extract_species(name),
        "scientific_name": raw.get("ccbaMnm2", ""),
        "family":         "",
        "age":            0,
        "height_m":       "",
        "trunk_circ_m":   "",
        "trunk_count":    "",
        "address":        address,
        "road_address":   address,
        "land_category":  "",
        "sido":           sido,
        "sigungu":        sigungu,
        "lat":            _safe_float(raw.get("latitude", 0)),
        "lng":            _safe_float(raw.get("longitude", 0)),
        "designated_at":  "",
        "cancelled_at":   "",
        "managing_org":   raw.get("ccbaAdmin", "국가유산청"),
        "owner_type":     "",
        "manage_no":      cpno,
        "updated_at":     raw.get("regDt", ""),
        "heritage_url":   (
            f"https://www.heritage.go.kr/heri/cul/culSelectDetail.do?ccbaCpno={cpno}"
            if cpno else ""
        ),
    }


def _extract_species(name: str) -> str:
    # 긴 키워드 우선 매칭 (은행나무 > 나무)
    for kw in sorted(TREE_KEYWORDS, key=len, reverse=True):
        if kw in name:
            return kw
    return ""


def _safe_float(val) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0
