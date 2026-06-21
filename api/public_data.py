"""
공공데이터포털 보호수 현황 API 클라이언트
서비스: 행정안전부_보호수정보 조회서비스
Endpoint: GET https://apis.data.go.kr/1741000/protected_tree_info/info
"""

from __future__ import annotations
import httpx
import urllib.parse
import time
from typing import Any
from config.settings import settings

ENDPOINT = "https://apis.data.go.kr/1741000/protected_tree_info/info"

_cache: dict[str, tuple[Any, float]] = {}
CACHE_TTL = 3600  # 1시간


def _cache_get(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry and time.time() < entry[1]:
        return entry[0]
    return None


def _cache_set(key: str, data: Any) -> None:
    _cache[key] = (data, time.time() + CACHE_TTL)


async def fetch_protected_trees(
    sigungu: str = "",
    sido: str = "",
    page_no: int = 1,
    num_of_rows: int = 100,
) -> dict:
    """
    보호수 목록 조회

    Returns:
        { "totalCount": int, "items": [ {...}, ... ] }
    """
    cache_key = f"list:{sigungu}:{sido}:{page_no}:{num_of_rows}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    # cond[...] 파라미터 대괄호가 httpx에서 인코딩되지 않도록 URL 직접 구성
    qs = urllib.parse.urlencode({
        "serviceKey": settings.PUBLIC_DATA_API_KEY,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "returnType": "json",
    })
    if sigungu:
        qs += f"&cond[SGG_NM::LIKE]={urllib.parse.quote(sigungu)}"
    if sido:
        qs += f"&cond[CTPV_NM::LIKE]={urllib.parse.quote(sido)}"

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(f"{ENDPOINT}?{qs}")
        resp.raise_for_status()
        data = resp.json()

    body = data.get("response", {}).get("body", {})
    total = body.get("totalCount", 0)
    items_raw = body.get("items", [])

    if isinstance(items_raw, dict):
        items = items_raw.get("item", [])
        if isinstance(items, dict):
            items = [items]
    elif isinstance(items_raw, list):
        items = items_raw
    else:
        items = []

    result = {"totalCount": total, "items": items}
    _cache_set(cache_key, result)
    return result


async def fetch_all_protected_trees(
    sigungu: str = "",
    sido: str = "",
    max_items: int = 3000,
) -> dict:
    """
    보호수 전체 목록 페이지네이션 조회 (최대 max_items건)

    Returns:
        { "totalCount": int, "items": [ {...}, ... ] }
    """
    cache_key = f"all:{sigungu}:{sido}:{max_items}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    PAGE_SIZE = 1000
    first = await fetch_protected_trees(
        sigungu=sigungu, sido=sido, page_no=1, num_of_rows=PAGE_SIZE
    )
    total = first["totalCount"]
    items: list = list(first["items"])

    page = 2
    while len(items) < min(total, max_items):
        more = await fetch_protected_trees(
            sigungu=sigungu, sido=sido, page_no=page, num_of_rows=PAGE_SIZE
        )
        batch = more["items"]
        if not batch:
            break
        items.extend(batch)
        page += 1

    result = {"totalCount": total, "items": items[:max_items]}
    _cache_set(cache_key, result)
    return result


async def fetch_raw_sample(sigungu: str = "") -> dict:
    """디버그용 — 실제 요청 URL과 원본 응답 반환"""
    qs = urllib.parse.urlencode({
        "serviceKey": settings.PUBLIC_DATA_API_KEY,
        "pageNo": 1,
        "numOfRows": 3,
        "returnType": "json",
    })
    if sigungu:
        qs += f"&cond[SGG_NM::LIKE]={urllib.parse.quote(sigungu)}"

    url = f"{ENDPOINT}?{qs}"

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    body = data.get("response", {}).get("body", {})
    return {
        "request_url": url,
        "totalCount": body.get("totalCount", 0),
        "numOfRows": body.get("numOfRows", 0),
        "raw_items_type": type(body.get("items", None)).__name__,
        "raw_body_keys": list(body.keys()),
        "items_preview": str(body.get("items", ""))[:500],
    }


def normalize_tree(raw: dict) -> dict:
    """API 응답 원본 필드 → 표준 필드 변환 (행정안전부_보호수정보 조회서비스 기준)"""
    return {
        "tree_id":        raw.get("DSGN_NO", ""),           # 지정번호
        "designation":    raw.get("DIGN_NM", ""),           # 지정명 (시·군나무 등)
        "type":           raw.get("PRTCTDTR_TYPE_NM", ""),  # 보호수유형 (노목/희귀목 등)
        "species":        raw.get("TREE_KND", ""),          # 수종 (은행나무 등)
        "scientific_name":raw.get("STDY_NM", ""),           # 학명
        "family":         raw.get("DEPTM_NM", ""),          # 과명
        "age":            _safe_int(raw.get("TREE_AG", 0)), # 수령 (년)
        "height_m":       raw.get("TREE_HGT", ""),          # 수고 (m)
        "trunk_circ_m":   raw.get("CHST_HGT_CIRC", ""),    # 흉고둘레 (m)
        "trunk_count":    raw.get("TRUN_CNT", ""),          # 그루수
        "address":        raw.get("LCTN_LOTNO_ADDR", ""),   # 지번주소
        "road_address":   raw.get("LCTN_ROAD_NM_ADDR", ""),# 도로명주소
        "land_category":  raw.get("LDCG_NM", ""),          # 지목
        "sido":           raw.get("CTPV_NM", ""),           # 시도명
        "sigungu":        raw.get("SGG_NM", ""),            # 시군구명
        "lat":            _safe_float(raw.get("WGS84_LAT", 0)),
        "lng":            _safe_float(raw.get("WGS84_LOT", 0)),
        "designated_at":  raw.get("PRTCTDTR_DSGN_YMD", ""),# 지정일
        "cancelled_at":   raw.get("PRTCTDTR_CNCLTN_YMD", ""),# 지정해제일
        "managing_org":   raw.get("MNG_INST_NM", ""),      # 관리기관
        "owner_type":     raw.get("OWNR_SE", ""),           # 소유구분
        "manage_no":      raw.get("MNG_NO", ""),            # 관리번호
        "updated_at":     raw.get("DAT_UPDT_PNT", ""),     # 갱신시점
    }


def _safe_int(val) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def _safe_float(val) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0
