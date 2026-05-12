---
name: vpn-flow-analyst
description: Use this skill to analyze VPN/proxy flow evidence, call MCP tools for flow lookup and knowledge retrieval, explain risk signals, and draft concise security triage reports.
---

# VPN Flow Analyst

Use this skill when the user asks for VPN/proxy traffic triage, encrypted-tunnel risk explanation, suspicious flow review, MCP tool use, or a report based on flow-level detection signals.

## Workflow

1. Identify the target:
   - Single flow: `flow_id`
   - Flow search: partial flow identifier
   - Batch summary: risk threshold or top suspicious flows
   - Knowledge question: protocol, feature, false positive, or response playbook
2. Gather evidence:
   - `search_flows` for candidate flows
   - `analyze_flow` for one flow
   - `search_vpn_knowledge` for protocol and response context
   - `generate_flow_report` for a markdown triage draft
   - `summarize_flows` for high-risk flow overview
3. Answer with:
   - Risk level
   - Evidence
   - Possible false-positive explanation
   - Recommended next action
   - Uncertainty or missing context

## Safety Notes

Do not claim payload decryption or exact VPN attribution unless evidence explicitly supports it. Prefer wording such as "suspected encrypted tunnel" or "VPN-like behavior" when the signal is derived from statistical flow features.

When discussing model improvement, prefer exact before-and-after values and state whether the number is an absolute percentage-point improvement or a relative improvement.

