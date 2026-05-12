from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from mcp.server.fastmcp import FastMCP


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
FLOW_PATH = DATA_DIR / "sample_flows.csv"
KNOWLEDGE_PATH = DATA_DIR / "vpn_knowledge.jsonl"

mcp = FastMCP("vpn-flow-analyst")


def load_flows() -> pd.DataFrame:
    return pd.read_csv(FLOW_PATH)


def load_knowledge() -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    for line in KNOWLEDGE_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            docs.append(json.loads(line))
    return docs


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def risk_hits(row: Dict[str, Any]) -> List[str]:
    hits: List[str] = []
    port = int(row.get("responder_port", 0))
    if port not in {80, 443, 8080, 8443, 22, 53}:
        hits.append("non_standard_port")
    if float(row.get("has_tls_sni", 0)) == 0 and float(row.get("suspicion_score", 0)) >= 60:
        hits.append("encrypted_like_without_sni")
    if float(row.get("duration_sec", 0)) >= 60:
        hits.append("long_lived_session")
    if float(row.get("packet_balance", 0)) >= 0.80:
        hits.append("balanced_bidirectional_exchange")
    if float(row.get("max_packet_size", 0)) >= 1400:
        hits.append("large_packet_pattern")
    return hits


def risk_score(row: Dict[str, Any]) -> int:
    base = int(float(row.get("suspicion_score", 0)))
    score = base
    hits = risk_hits(row)
    if "non_standard_port" in hits:
        score += 5
    if "encrypted_like_without_sni" in hits:
        score += 10
    if "long_lived_session" in hits:
        score += 5
    return min(score, 100)


def risk_level(score: int) -> str:
    if score >= 80:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


@mcp.tool()
def search_vpn_knowledge(query: str, limit: int = 5) -> Dict[str, Any]:
    """Search VPN/proxy protocol, feature, metric, and response knowledge."""
    terms = [term.lower() for term in query.split() if term.strip()]
    ranked = []
    for doc in load_knowledge():
        haystack = " ".join(
            str(doc.get(field, "")) for field in ["title", "tags", "content"]
        ).lower()
        score = sum(1 for term in terms if term in haystack)
        if not terms or score > 0:
            ranked.append((score, doc))
    ranked.sort(key=lambda item: item[0], reverse=True)
    return {
        "query": query,
        "matches": [json_safe(doc) for _, doc in ranked[: max(1, limit)]],
    }


@mcp.tool()
def search_flows(flow_id_query: str, limit: int = 10) -> Dict[str, Any]:
    """Search sample flows by partial flow_id."""
    flows = load_flows()
    matched = flows[
        flows["flow_id"].str.contains(flow_id_query, case=False, regex=False, na=False)
    ].head(max(1, limit))
    return {
        "query": flow_id_query,
        "count": int(len(matched)),
        "flows": json_safe(matched.to_dict(orient="records")),
    }


@mcp.tool()
def analyze_flow(flow_id: str) -> Dict[str, Any]:
    """Analyze one flow and return risk score, level, evidence, and next action."""
    flows = load_flows()
    matched = flows[flows["flow_id"] == flow_id]
    if matched.empty:
        return {"flow_id": flow_id, "found": False, "message": "flow_id not found"}
    row = matched.iloc[0].to_dict()
    score = risk_score(row)
    hits = risk_hits(row)
    return {
        "flow_id": flow_id,
        "found": True,
        "label_hint": row.get("label", "unknown"),
        "risk_score": score,
        "risk_level": risk_level(score),
        "hit_features": hits,
        "evidence": {
            "protocol": row.get("protocol"),
            "responder_port": int(row.get("responder_port", 0)),
            "duration_sec": float(row.get("duration_sec", 0)),
            "bytes_per_second": float(row.get("bytes_per_second", 0)),
            "packet_balance": float(row.get("packet_balance", 0)),
            "has_tls_sni": int(row.get("has_tls_sni", 0)),
        },
        "next_action": "Review endpoint context, SNI/domain evidence, and similar false-positive cases.",
    }


@mcp.tool()
def generate_flow_report(flow_id: str) -> Dict[str, Any]:
    """Generate a concise markdown triage report for one flow."""
    analysis = analyze_flow(flow_id)
    if not analysis.get("found"):
        return analysis
    query = " ".join(analysis.get("hit_features", [])) or "vpn flow triage"
    knowledge = search_vpn_knowledge(query, limit=3)
    markdown = [
        f"# Flow Triage Report: {flow_id}",
        "",
        f"- Risk level: {analysis['risk_level']}",
        f"- Risk score: {analysis['risk_score']}",
        f"- Label hint: {analysis['label_hint']}",
        f"- Hit features: {', '.join(analysis['hit_features']) or 'none'}",
        "",
        "## Evidence",
    ]
    for key, value in analysis["evidence"].items():
        markdown.append(f"- {key}: {value}")
    markdown.extend(["", "## Related knowledge"])
    for doc in knowledge["matches"]:
        markdown.append(f"- {doc['title']}: {doc['content']}")
    markdown.extend(["", "## Next action", f"- {analysis['next_action']}"])
    return {
        "flow_id": flow_id,
        "analysis": analysis,
        "knowledge_matches": knowledge["matches"],
        "markdown": "\n".join(markdown),
    }


@mcp.tool()
def summarize_flows(min_risk_score: int = 70, limit: int = 10) -> Dict[str, Any]:
    """Summarize sample flows above a risk threshold."""
    flows = load_flows()
    rows = []
    for _, item in flows.iterrows():
        row = item.to_dict()
        score = risk_score(row)
        if score >= min_risk_score:
            rows.append(
                {
                    "flow_id": row["flow_id"],
                    "risk_score": score,
                    "risk_level": risk_level(score),
                    "label_hint": row.get("label"),
                    "hit_features": risk_hits(row),
                }
            )
    rows = sorted(rows, key=lambda item: item["risk_score"], reverse=True)[:limit]
    return {
        "min_risk_score": min_risk_score,
        "count": len(rows),
        "flows": json_safe(rows),
    }


if __name__ == "__main__":
    mcp.run()

