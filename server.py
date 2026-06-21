"""
보호수 MCP 서버
카카오 PlayMCP 등록용 — 공공데이터 기반 전국 보호수 조회 도구 모음
"""

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
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
    # KC 리버스 프록시 통과 시 Host 헤더가 localhost가 아니므로 DNS rebinding 보호 비활성화
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

mcp.tool(
    title="Search Protected Trees",
    description=(
        "Search for protected trees (보호수) and natural monument trees (천연기념물) "
        "in the 보호수 MCP database by location name or species. "
        "Supports abbreviations like '전남', '경북'. "
        "Returns a merged list of 보호수 (산림청) and 천연기념물 수목 (국가유산청) results."
    ),
    annotations=ToolAnnotations(
        title="Search Protected Trees",
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=True,
        idempotentHint=True,
    ),
)(search_protected_trees)

mcp.tool(
    title="Find Nearby Protected Trees",
    description=(
        "Find protected trees (보호수) near a given GPS coordinate in the 보호수 MCP database. "
        "Returns trees sorted by distance within the specified radius. "
        "Input latitude/longitude in decimal degrees (WGS84)."
    ),
    annotations=ToolAnnotations(
        title="Find Nearby Protected Trees",
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=True,
        idempotentHint=True,
    ),
)(find_nearby_protected_trees)

mcp.tool(
    title="Get Protected Tree Detail",
    description=(
        "Retrieve detailed information for a single protected tree (보호수) "
        "by its designation number (지정번호) from the 보호수 MCP database. "
        "Includes species, age, address, and a Kakao Map link."
    ),
    annotations=ToolAnnotations(
        title="Get Protected Tree Detail",
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=True,
        idempotentHint=True,
    ),
)(get_protected_tree_detail)

mcp.tool(
    title="Get Protected Tree Stats",
    description=(
        "Get aggregated statistics for protected trees (보호수) in the 보호수 MCP database. "
        "Supports grouping by species (수종별), region (시도별), or age range (수령대별). "
        "Optionally filter by a specific district (시군구)."
    ),
    annotations=ToolAnnotations(
        title="Get Protected Tree Stats",
        readOnlyHint=True,
        destructiveHint=False,
        openWorldHint=True,
        idempotentHint=True,
    ),
)(get_protected_tree_stats)


if __name__ == "__main__":
    import os
    if "PORT" in os.environ:
        os.environ.setdefault("FASTMCP_PORT", os.environ["PORT"])
    os.environ.setdefault("FASTMCP_HOST", "0.0.0.0")

    transport = os.getenv("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)
