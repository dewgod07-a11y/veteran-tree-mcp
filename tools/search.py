"""
tools/search.py
보호수 검색 도구 2개

  - search_protected_trees      : 지역명·수종으로 보호수 목록 검색
  - find_nearby_protected_trees : 좌표 기반 반경 내 보호수 탐색
"""

from __future__ import annotations
from api.public_data import fetch_protected_trees, normalize_tree
from api.kakao_map import haversine_km


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
    max_results = min(max_results, 100)
    loc = location.strip()

    # 1차: 시군구명(SGG_NM) API 필터로 조회
    try:
        result = await fetch_protected_trees(sigungu=loc, num_of_rows=100)
    except Exception as e:
        return {"error": f"공공 API 호출 실패: {str(e)}", "trees": []}

    trees = [normalize_tree(raw) for raw in result.get("items", [])]

    # 2차: 결과 없으면 시도명(CTPV_NM) 클라이언트 필터로 재조회
    if not trees and loc:
        try:
            result2 = await fetch_protected_trees(num_of_rows=100)
            trees = [
                normalize_tree(raw) for raw in result2.get("items", [])
                if loc in normalize_tree(raw).get("sido", "")
            ]
        except Exception:
            pass

    # 수종 필터 (클라이언트)
    if species:
        trees = [t for t in trees if species in t.get("species", "")]

    # 수령 필터 (클라이언트)
    if min_age > 0:
        trees = [t for t in trees if t["age"] >= min_age]

    return {
        "query": {"location": location, "species": species, "min_age": min_age},
        "total_count": result.get("totalCount", 0),
        "returned": len(trees[:max_results]),
        "trees": trees[:max_results],
    }


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
        result = await fetch_protected_trees(
            sigungu=sigungu,
            num_of_rows=100,
        )
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
