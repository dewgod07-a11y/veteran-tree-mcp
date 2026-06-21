"""
tools/detail.py
보호수 상세 조회 도구

  - get_protected_tree_detail : 지정번호로 보호수 상세 정보 반환
  - get_protected_tree_stats  : 지역·수종별 보호수 통계
"""

from __future__ import annotations
from api.public_data import fetch_all_protected_trees, normalize_tree


async def get_protected_tree_detail(tree_id: str) -> dict:
    """
    보호수 지정번호로 상세 정보를 조회합니다.

    Args:
        tree_id: 보호수 지정번호 (예: 11-1-7, 서울-강남-1 등)
    """
    try:
        result = await fetch_all_protected_trees()
    except Exception as e:
        return {"error": f"공공 API 호출 실패: {str(e)}", "tree_id": tree_id}

    for raw in result.get("items", []):
        tree = normalize_tree(raw)
        if tree.get("tree_id") == tree_id:
            if tree["lat"] and tree["lng"]:
                label = tree["designation"] or tree["species"] or "보호수"
                tree["map_url"] = (
                    f"https://map.kakao.com/link/map/{label},{tree['lat']},{tree['lng']}"
                )
            return tree

    return {"error": f"보호수 '{tree_id}'를 찾을 수 없습니다.", "tree_id": tree_id}


async def get_protected_tree_stats(
    region: str = "",
    group_by: str = "species",
) -> dict:
    """
    전국 또는 특정 지역의 보호수 통계를 반환합니다.

    Args:
        region:   집계할 시군구명 (예: 강남구, 수원시). 비워두면 전국
        group_by: 집계 기준 — "species"(수종별) | "region"(시도별) | "age_range"(수령대별)
    """
    if group_by not in ("species", "region", "age_range"):
        group_by = "species"

    try:
        result = await fetch_all_protected_trees(sigungu=region)
    except Exception as e:
        return {"error": f"공공 API 호출 실패: {str(e)}"}

    trees = [normalize_tree(raw) for raw in result.get("items", [])]
    total = result.get("totalCount", len(trees))

    if not trees:
        return {"region": region or "전국", "total_count": 0, "groups": []}

    counts: dict[str, int] = {}
    ages: list[int] = []

    for tree in trees:
        age = tree.get("age", 0)
        if age:
            ages.append(age)

        if group_by == "species":
            key = tree.get("species") or "미상"
        elif group_by == "region":
            key = tree.get("sido") or "미상"
        else:
            if age == 0:
                key = "미상"
            elif age < 100:
                key = "100년 미만"
            elif age < 200:
                key = "100~199년"
            elif age < 300:
                key = "200~299년"
            elif age < 500:
                key = "300~499년"
            else:
                key = "500년 이상"

        counts[key] = counts.get(key, 0) + 1

    groups = sorted(
        [{"label": k, "count": v} for k, v in counts.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    result_dict: dict = {
        "region": region or "전국",
        "total_count": total,
        "sample_size": len(trees),
        "group_by": group_by,
        "groups": groups,
    }

    if ages:
        result_dict["age_stats"] = {
            "avg": round(sum(ages) / len(ages)),
            "max": max(ages),
            "min": min(ages),
        }

    return result_dict
