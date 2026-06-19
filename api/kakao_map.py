"""
카카오맵 REST API 클라이언트
- 주소 → 좌표 변환 (지오코딩)
- 좌표 → 행정구역명 변환 (역지오코딩)
"""

from __future__ import annotations
import httpx
from config.settings import settings

KAKAO_BASE = "https://dapi.kakao.com/v2/local"


def _headers() -> dict:
    return {"Authorization": f"KakaoAK {settings.KAKAO_REST_API_KEY}"}


async def address_to_coords(address: str) -> tuple[float, float] | None:
    """
    주소 문자열 → (위도, 경도) 변환
    변환 실패 시 None 반환
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{KAKAO_BASE}/search/address.json",
            headers=_headers(),
            params={"query": address, "analyze_type": "similar"},
        )
        resp.raise_for_status()
        data = resp.json()

    docs = data.get("documents", [])
    if not docs:
        return None

    first = docs[0]
    return float(first["y"]), float(first["x"])  # (lat, lng)


async def coords_to_region(lat: float, lng: float) -> dict:
    """
    좌표 → 행정구역 정보 반환
    Returns: { sido, sigungu, dong }
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{KAKAO_BASE}/geo/coord2regioncode.json",
            headers=_headers(),
            params={"x": lng, "y": lat},
        )
        if resp.status_code != 200:
            raise RuntimeError(f"카카오 API 오류 {resp.status_code}: {resp.text}")
        data = resp.json()

    docs = data.get("documents", [])
    region: dict = {"sido": "", "sigungu": "", "dong": ""}

    for doc in docs:
        if doc.get("region_type") == "B":  # 법정동
            region["sido"] = doc.get("region_1depth_name", "")
            region["sigungu"] = doc.get("region_2depth_name", "")
            region["dong"] = doc.get("region_3depth_name", "")
            break

    return region


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """두 좌표 간 직선 거리 (km)"""
    import math
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
