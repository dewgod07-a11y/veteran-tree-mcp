"""도구 통합 테스트 — 실제 API 호출"""
import asyncio, json, sys

sys.path.insert(0, ".")
from tools.search import search_protected_trees, find_nearby_protected_trees
from tools.detail import get_protected_tree_detail, get_protected_tree_stats


def _pp(label: str, data: dict) -> None:
    print(f"\n{'='*60}")
    print(f"[{label}]")
    print(json.dumps(data, ensure_ascii=False, indent=2))


async def main() -> None:
    # 1) 지역 검색 — 강남구 느티나무
    r1 = await search_protected_trees(location="강남구", species="느티나무", max_results=3)
    _pp("search: 강남구 느티나무", {
        "total": r1["total_count"],
        "returned": r1["returned"],
        "first": r1["trees"][0] if r1["trees"] else None,
    })

    # 2) 전국 은행나무 (수령 200년 이상)
    r2 = await search_protected_trees(species="은행나무", min_age=200, max_results=3)
    _pp("search: 은행나무 200년+", {
        "total": r2["total_count"],
        "first": r2["trees"][0] if r2["trees"] else None,
    })

    # 3) 주변 보호수 — 광화문 좌표
    r3 = await find_nearby_protected_trees(lat=37.5759, lng=126.9769, radius_km=5.0, max_results=3)
    _pp("nearby: 광화문 5km", {
        "total_found": r3["total_found"],
        "trees": [{"name": t.get("designation") or t.get("species"), "dist": t.get("distance_km")} for t in r3["trees"]],
    })

    # 4) 상세 조회 — 첫 번째 검색 결과의 tree_id 사용
    all_trees = r1["trees"] + r2["trees"]
    if all_trees:
        tid = all_trees[0]["tree_id"]
        r4 = await get_protected_tree_detail(tid)
        _pp(f"detail: {tid}", r4)
    else:
        print("\n[detail] 검색 결과 없음 — 건너뜀")

    # 5) 통계 — 수종별 전국
    r5 = await get_protected_tree_stats(group_by="species")
    _pp("stats: 수종별 전국 (상위 5)", {
        "region": r5.get("region"),
        "total_count": r5.get("total_count"),
        "top5": r5.get("groups", [])[:5],
        "age_stats": r5.get("age_stats"),
    })

    # 6) 통계 — 시도별 전국
    r6 = await get_protected_tree_stats(group_by="region")
    _pp("stats: 시도별 전국 (상위 5)", {
        "top5": r6.get("groups", [])[:5],
    })

    # 7) 천연기념물 포함 검색
    r7 = await search_protected_trees(location="전남", max_results=5)
    sources = {t.get("source", "?") for t in r7["trees"]}
    _pp("search: 전남 (보호수+천연기념물 혼합 확인)", {
        "total": r7["total_count"],
        "sources": list(sources),
        "trees": [{"name": t.get("designation") or t.get("species"), "source": t.get("source")} for t in r7["trees"][:5]],
    })

    print("\n" + "="*60)
    print("테스트 완료")


asyncio.run(main())
