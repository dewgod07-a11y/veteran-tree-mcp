"""
보호수 MCP 서버
카카오 PlayMCP 등록용 — 공공데이터 기반 전국 보호수 조회 도구 모음

실행 방법:
  pip install -r requirements.txt
  python server.py
"""

from mcp.server.fastmcp import FastMCP
from tools.search import (
    search_protected_trees,
    find_nearby_protected_trees,
)
from tools.detail import (
    get_protected_tree_detail,
    get_protected_tree_stats,
)

mcp = FastMCP(
    name="보호수 MCP",
    instructions=(
        "전국 보호수(保護樹)에 대한 공공데이터 기반 조회 도구 모음입니다. "
        "지역명·수종으로 보호수를 검색하고, 지정번호로 상세 정보를 조회하며, "
        "현재 위치 주변의 보호수를 거리순으로 찾아드립니다."
    ),
)

# 🔍 검색 (2개)
mcp.tool()(search_protected_trees)
mcp.tool()(find_nearby_protected_trees)

# 📋 상세 조회 · 통계 (2개)
mcp.tool()(get_protected_tree_detail)
mcp.tool()(get_protected_tree_stats)


if __name__ == "__main__":
    import os
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)
