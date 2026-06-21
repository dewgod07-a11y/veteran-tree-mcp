"""
tools/search.py
보호수 검색 도구 2개

  - search_protected_trees      : 지역명·수종으로 보호수 목록 검색
  - find_nearby_protected_trees : 좌표 기반 반경 내 보호수 탐색
"""

from __future__ import annotations
import asyncio
from api.public_data import fetch_all_protected_trees, normalize_tree
from api.heritage import fetch_heritage_trees, normalize_heritage_tree
from api.kakao_map import haversine_km

# 시도 약칭 → 공식명 매핑
_SIDO_ALIAS: dict[str, str] = {
    "서울": "서울특별시",
    "부산": "부산광역시",
    "대구": "대구광역시",
    "인천": "인천광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별자치시",
    "경기": "경기도",
    "강원": "강원특별자치도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전북특별자치도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도",
}

_SIDO_NAMES = set(_SIDO_ALIAS.values())


def _classify_location(loc: str) -> tuple[str, str]:
    """(sigungu, sido) 분류 — 시도명이면 sido에, 그 외는 sigungu에 배치"""
    if not loc:
        return "", ""
    expanded = _SIDO_ALIAS.get(loc, loc)
    if expanded in _SIDO_NAMES:
        return "", expanded
    return loc, ""


async def search_protected_trees(
    location: str = "",
    species: str = "",
    min_age: int = 0,
    max_results: int = 20,
) -> dict:
    """
    지역명 또는 수종으로 보호수 목록을 검색합니다.

    Args:
        location:    시군구명 또는 시도명 (예: 광명시, 강남구, 경기도). 비워두면 전국
        species:     수종 필터 (예: 느티나무, 은행나무). 비워두면 전체
        min_age:     최소 수령 필터 (년). 0이면 전체
        max_results: 반환할 최대 건수 (기본 20, 최대 100)
    """
    max_results = min(max_results, 500)
    loc = location.strip()

    sigungu_q, sido_q = _classify_location(loc)

    # 보호수 + 천연기념물 병렬 조회
    async def _fetch_protected() -> list[dict]:
        try:
            result = await fetch_all_protected_trees(sigungu=sigungu_q, sido=sido_q)
            trees = [normalize_tree(raw) for raw in result.get("items", [])]
            for t in trees:
                t.setdefault("source", "보호수")
            return trees
        except Exception:
            return []

    heritage_error: str = ""

    async def _fetch_heritage() -> list[dict]:
        nonlocal heritage_error
        try:
            # 시도 필터 없이 전체 조회 후 클라이언트 필터
            result = await fetch_heritage_trees(num_of_rows=600)
            trees = [normalize_heritage_tree(raw) for raw in result.get("items", [])]
            if loc:
                trees = [
                    t for t in trees
                    if loc in t.get("sido", "") or loc in t.get("sigungu", "") or loc in t.get("address", "")
                ]
            return trees
        except Exception as e:
            heritage_error = str(e)
            return []

    protected_trees, heritage_trees = await asyncio.gather(
        _fetch_protected(), _fetch_heritage()
    )
    # 천연기념물을 먼저 표시 (더 중요도 높음)
    all_trees = heritage_trees + protected_trees

    # 수종 필터 (클라이언트)
    if species:
        all_trees = [t for t in all_trees if species in t.get("species", "")]

    # 수령 필터 (클라이언트, 천연기념물은 age=0이므로 보호수만 필터링됨)
    if min_age > 0:
        all_trees = [t for t in all_trees if t["age"] >= min_age]

    result = {
        "query": {"location": location, "species": species, "min_age": min_age},
        "total_count": len(all_trees),
        "returned": len(all_trees[:max_results]),
        "trees": all_trees[:max_results],
    }
    if heritage_error:
        result["heritage_error"] = heritage_error
    return result


async def find_nearby_protected_trees(
    lat: float,
    lng: float,
    sigungu: str = "",
    radius_km: float = 3.0,
    max_results: int = 10,
) -> dict:
    """
    위도·경도 좌표 기준 반경 내 보호수를 거리순으로 반환합니다.

    Args:
        lat:         위도 (예: 37.4621)
        lng:         경도 (예: 126.8535)
        sigungu:     시군구명 힌트 (예: 광명시, 강남구). 알고 있으면 입력하면 더 정확합니다
        radius_km:   탐색 반경 km (기본 3km, 최대 20km)
        max_results: 반환할 최대 건수 (기본 10)
    """
    radius_km = min(radius_km, 20.0)
    max_results = min(max_results, 50)

    try:
        result = await fetch_all_protected_trees(sigungu=sigungu)
    except Exception as e:
        return {"error": f"공공 API 호출 실패: {str(e)}", "trees": []}

    trees = [normalize_tree(raw) for raw in result.get("items", [])]

    nearby = []
    for tree in trees:
        if not (tree["lat"] and tree["lng"]):
            continue
        dist = haversine_km(lat, lng, tree["lat"], tree["lng"])
        if dist <= radius_km:
            nearby.append({**tree, "distance_km": round(dist, 2)})

    nearby.sort(key=lambda t: t["distance_km"])

    return {
        "query": {"lat": lat, "lng": lng, "sigungu": sigungu, "radius_km": radius_km},
        "total_found": len(nearby),
        "trees": nearby[:max_results],
    }
