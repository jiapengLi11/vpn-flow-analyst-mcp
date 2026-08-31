from __future__ import annotations

import argparse
import json
from typing import Any

from vpn_flow_analyst_mcp import server


def emit(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vpn-flow-analyst",
        description="Inspect synthetic VPN/proxy-like flow evidence through the same functions exposed by MCP.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze one exact flow ID.")
    analyze.add_argument("flow_id")

    report = subparsers.add_parser("report", help="Generate a Markdown triage report.")
    report.add_argument("flow_id")

    summary = subparsers.add_parser("summary", help="List flows above a risk threshold.")
    summary.add_argument("--min-risk-score", type=int, default=70)
    summary.add_argument("--limit", type=int, default=10)

    knowledge = subparsers.add_parser("knowledge", help="Search the local triage knowledge base.")
    knowledge.add_argument("query")
    knowledge.add_argument("--limit", type=int, default=5)

    subparsers.add_parser("serve", help="Start the FastMCP server over stdio.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "analyze":
        emit(server.analyze_flow(args.flow_id))
    elif args.command == "report":
        result = server.generate_flow_report(args.flow_id)
        print(result.get("markdown", json.dumps(result, ensure_ascii=False, indent=2)))
    elif args.command == "summary":
        emit(server.summarize_flows(args.min_risk_score, args.limit))
    elif args.command == "knowledge":
        emit(server.search_vpn_knowledge(args.query, args.limit))
    else:
        server.mcp.run()


if __name__ == "__main__":
    main()
