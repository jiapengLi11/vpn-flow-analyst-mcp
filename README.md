# VPN Flow Analyst MCP

![Python](https://img.shields.io/badge/Python-3.10-blue)
![MCP](https://img.shields.io/badge/Protocol-MCP-black)
![Security](https://img.shields.io/badge/Domain-Traffic%20Analysis-red)
![Agent](https://img.shields.io/badge/Use%20Case-LLM%20Tooling-green)

## Overview

This repository provides MCP tools and a Codex skill for VPN / proxy traffic triage. It focuses on the AI-tooling layer: flow lookup, risk explanation, knowledge retrieval, and report generation for LLM or agent workflows.

The public version uses synthetic sample flows and a small example knowledge base. It does not include raw PCAP files, private traffic captures, model binaries, internal deployment documents, or company data.

## Highlights

- MCP server for VPN and proxy flow analysis
- Codex skill for evidence-based traffic triage
- RAG-ready knowledge base in JSONL format
- synthetic flow samples for local testing
- smoke tests for tool behavior and skill structure

## Core Tools

- `search_vpn_knowledge(query, limit=5)`
- `search_flows(flow_id_query, limit=10)`
- `analyze_flow(flow_id)`
- `generate_flow_report(flow_id)`
- `summarize_flows(min_risk_score=70, limit=10)`

## Project Structure

- `src/vpn_flow_analyst_mcp/server.py`: MCP server implementation
- `skills/vpn-flow-analyst/`: Codex skill definition
- `data/sample_flows.csv`: synthetic sample flows
- `data/vpn_knowledge.jsonl`: lightweight knowledge base
- `tests/test_smoke.py`: smoke tests
- `mcp_client_config.example.json`: client configuration example

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

- flow IDs, IPs, and examples are synthetic
- knowledge base entries are generic public-style notes
- no model binaries or internal documents are included
- no PCAP files are included

## Resume Wording

`将商用 VPN/代理流量检测结果抽象为 MCP 工具与 Codex Skill，提供 flow 查询、风险解释、知识检索和研判报告生成能力，并使用脱敏样例数据完成独立环境测试，使检测结果可被大模型/Agent 以工具调用方式复用。`
