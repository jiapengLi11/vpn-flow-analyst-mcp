# VPN Flow Analyst MCP

MCP tools and a Codex skill for VPN/proxy traffic triage. This repository focuses on the AI-tooling layer: flow lookup, risk explanation, knowledge retrieval, and report generation for LLM/Agent workflows.

The public version uses synthetic sample flows and a small example knowledge base. It does not include raw PCAP files, private traffic captures, model binaries, internal deployment documents, or company data.

## Features

- MCP server for VPN/proxy flow analysis.
- Codex skill for evidence-based security triage.
- RAG-ready JSONL knowledge base with protocol, feature, metric, and response notes.
- Synthetic flow samples for local testing.
- Smoke tests for tool behavior and skill structure.

## Tools

- `search_vpn_knowledge(query, limit=5)`
- `search_flows(flow_id_query, limit=10)`
- `analyze_flow(flow_id)`
- `generate_flow_report(flow_id)`
- `summarize_flows(min_risk_score=70, limit=10)`

## Quick Start

```bash
conda create -y -n vpn-flow-analyst-mcp python=3.10
conda activate vpn-flow-analyst-mcp
pip install -r requirements.txt
python tests/test_smoke.py
python src/vpn_flow_analyst_mcp/server.py
```

## MCP Client Config

```json
{
  "mcpServers": {
    "vpn-flow-analyst": {
      "command": "python",
      "args": ["C:/path/to/vpn-flow-analyst-mcp/src/vpn_flow_analyst_mcp/server.py"],
      "cwd": "C:/path/to/vpn-flow-analyst-mcp"
    }
  }
}
```

## Data Safety

This repository is intentionally sanitized:

- Flow IDs, IPs, and examples are synthetic.
- Knowledge base entries are generic public-style notes.
- No model binaries or internal documents are included.
- No PCAP files are included.

## Resume Wording

`将商用 VPN/代理流量检测结果抽象为 MCP 工具与 Codex Skill，提供 flow 查询、风险解释、知识检索和研判报告生成能力，并使用脱敏样例数据完成独立环境测试，使检测结果可被大模型/Agent 以工具调用方式复用。`

