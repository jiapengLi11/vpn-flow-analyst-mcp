from __future__ import annotations

import asyncio
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vpn_flow_analyst_mcp import server  # noqa: E402


def test_direct_tools() -> None:
    knowledge = server.search_vpn_knowledge("OpenVPN false positive", limit=2)
    assert len(knowledge["matches"]) >= 1

    flows = server.search_flows("flow-demo", limit=3)
    assert flows["count"] == 3

    analysis = server.analyze_flow("flow-demo-002")
    assert analysis["found"] is True
    assert analysis["risk_level"] in {"medium", "high"}

    report = server.generate_flow_report("flow-demo-002")
    assert "Flow Triage Report" in report["markdown"]

    summary = server.summarize_flows(min_risk_score=70)
    assert summary["count"] >= 1


async def test_fastmcp_tool_registry() -> None:
    tools = await server.mcp.list_tools()
    tool_names = {tool.name for tool in tools}
    assert {
        "search_vpn_knowledge",
        "search_flows",
        "analyze_flow",
        "generate_flow_report",
        "summarize_flows",
    }.issubset(tool_names)


def test_skill_files() -> None:
    skill_path = ROOT / "skills" / "vpn-flow-analyst" / "SKILL.md"
    meta_path = ROOT / "skills" / "vpn-flow-analyst" / "agents" / "openai.yaml"
    text = skill_path.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "Workflow" in text
    assert meta_path.exists()


if __name__ == "__main__":
    test_direct_tools()
    asyncio.run(test_fastmcp_tool_registry())
    test_skill_files()
    print("smoke tests passed")

