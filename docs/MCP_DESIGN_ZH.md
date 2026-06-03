# VPN Flow Analyst MCP 中文设计说明

## 1. 文档目标

本文用于说明 `vpn-flow-analyst-mcp` 项目中 MCP 部分的设计思路、实现方式、工具能力、调用流程和测试方法。

这个 MCP 项目的核心目标不是做完整的流量检测平台，而是把网络流量研判过程中的固定能力抽象成大模型 / Agent 可以调用的工具，包括：

- flow 查询
- 单流风险分析
- VPN / 代理 / 加密隧道知识检索
- 单流研判报告生成
- 可疑 flow 批量汇总

开源版本使用脱敏合成数据，不包含真实 PCAP、真实 IP、内部模型、公司资料或实验输出。

项目仓库：

```text
https://github.com/jiapengLi11/vpn-flow-analyst-mcp
```

## 2. 为什么要做 MCP

在安全流量研判场景中，大模型不能直接只靠 prompt 回答问题。

原因主要有三点：

### 2.1 流量研判是多步骤任务

一次完整研判通常不是一句话能完成的，而是类似下面的流程：

```text
用户提出问题
  -> 查询 flow 基础信息
  -> 分析风险分数和命中特征
  -> 检索协议知识或误报案例
  -> 组织证据
  -> 输出风险等级、判断依据和复核建议
```

如果把这些逻辑全部塞进一个 prompt，系统会难以维护，也不方便复用。

### 2.2 安全场景需要证据约束

安全分析不能让模型自由发挥。比如模型不能随便声称：

- 已经解密 payload
- 确认某条流一定是某种 VPN
- 某个正常业务一定是攻击或违规流量

MCP 的价值是把可验证的数据查询和知识检索变成工具，让模型基于工具结果回答，而不是凭空生成。

### 2.3 工具能力可以复用

`flow 查询`、`风险分析`、`知识检索`、`报告生成` 这些能力不仅可以给一个 Agent 使用，也可以给其他客户端或工作流复用。

因此，MCP 更像是把安全研判能力标准化暴露出来。

## 3. MCP 和 Skill 的关系

本项目中同时设计了 MCP 和 Skill。

两者分工不同：

| 模块 | 作用 | 类比 |
| --- | --- | --- |
| MCP | 提供可调用工具 | 工具箱 |
| Skill | 规定分析流程和输出边界 | 操作手册 |

MCP 负责具体能力：

- 查 flow
- 查知识库
- 分析风险
- 生成报告
- 汇总高风险样例

Skill 负责告诉 AI：

- 什么时候应该调用哪个工具
- 结果应该怎么组织
- 哪些结论不能过度断言
- 指标提升应该怎么规范表达

因此整体关系可以理解为：

```text
Skill 规定流程，MCP 提供工具。
```

## 4. 项目目录结构

MCP 相关核心文件如下：

```text
vpn-flow-analyst-mcp/
├── data/
│   ├── sample_flows.csv
│   └── vpn_knowledge.jsonl
├── src/
│   └── vpn_flow_analyst_mcp/
│       ├── __init__.py
│       └── server.py
├── skills/
│   └── vpn-flow-analyst/
│       ├── SKILL.md
│       ├── SKILL.zh-CN.md
│       └── agents/
│           └── openai.yaml
├── tests/
│   └── test_smoke.py
├── README.md
├── requirements.txt
└── mcp_client_config.example.json
```

其中：

- `server.py` 是 MCP server 的核心实现
- `sample_flows.csv` 是脱敏合成 flow 样例
- `vpn_knowledge.jsonl` 是轻量知识库样例
- `test_smoke.py` 是本地烟测脚本
- `SKILL.zh-CN.md` 是中文 Skill 说明

## 5. MCP Server 实现方式

MCP server 使用 Python 的 `FastMCP` 实现。

核心初始化代码：

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("vpn-flow-analyst")
```

每个工具通过 `@mcp.tool()` 装饰器注册：

```python
@mcp.tool()
def analyze_flow(flow_id: str) -> Dict[str, Any]:
    ...
```

最后通过下面代码启动：

```python
if __name__ == "__main__":
    mcp.run()
```

这样 MCP 客户端就可以发现并调用这些工具。

## 6. 数据设计

### 6.1 sample_flows.csv

`sample_flows.csv` 是脱敏合成 flow 样例，用来演示 MCP 工具的输入和输出。

它不包含真实 IP、真实域名、真实用户、真实企业流量。

主要字段包括：

| 字段 | 含义 |
| --- | --- |
| flow_id | 合成 flow 标识 |
| protocol | 传输层协议 |
| responder_port | 响应端口 |
| packet_count | 包数量 |
| total_bytes | 总字节数 |
| duration_sec | 会话持续时间 |
| bytes_per_second | 每秒字节数 |
| packets_per_second | 每秒包数 |
| upstream_byte_ratio | 上行字节占比 |
| packet_balance | 上下行包数量平衡度 |
| avg_packet_size | 平均包长 |
| std_packet_size | 包长标准差 |
| max_packet_size | 最大包长 |
| avg_inter_arrival | 平均包间隔 |
| std_inter_arrival | 包间隔标准差 |
| has_tls_sni | 是否存在 TLS SNI |
| suspicion_score | 可疑分数 |
| label | 样例标签提示 |

这些字段模拟真实项目中 `pcap -> flow -> 特征` 后得到的结构化结果。

### 6.2 vpn_knowledge.jsonl

`vpn_knowledge.jsonl` 是轻量知识库样例。

每一行是一条 JSON 文档：

```json
{
  "id": "proto-wireguard-001",
  "title": "WireGuard traffic clues",
  "tags": ["wireguard", "vpn", "udp"],
  "content": "WireGuard is UDP based. Typical clues include stable peer endpoints, compact handshake packets, periodic keepalive behavior, and long-lived bidirectional encrypted payload exchange."
}
```

当前知识库包含几类内容：

- 协议特征
- flow 级特征说明
- 指标表述规范
- 误报分析
- 高风险 flow 复核建议

后续可以替换成真正的 RAG 检索模块，比如：

- BM25
- 向量检索
- Hybrid Retrieval
- 图谱增强检索

## 7. MCP 工具清单

当前共实现 5 个 MCP tools：

```text
search_vpn_knowledge
search_flows
analyze_flow
generate_flow_report
summarize_flows
```

下面逐个说明。

## 8. 工具一：search_vpn_knowledge

### 8.1 功能

根据用户 query 检索 VPN / 代理 / 加密隧道相关知识。

### 8.2 输入

```text
query: str
limit: int = 5
```

### 8.3 输出

返回匹配的知识条目：

```json
{
  "query": "OpenVPN false positive",
  "matches": [
    {
      "id": "proto-openvpn-001",
      "title": "OpenVPN traffic clues",
      "tags": ["openvpn", "vpn", "protocol"],
      "content": "..."
    }
  ]
}
```

### 8.4 设计意义

这个工具让大模型在回答时可以先检索知识，再结合 flow 证据生成结论。

它解决的是：

```text
模型不能只靠记忆回答安全分析问题。
```

## 9. 工具二：search_flows

### 9.1 功能

根据部分 flow_id 搜索候选 flow。

### 9.2 输入

```text
flow_id_query: str
limit: int = 10
```

### 9.3 输出

返回匹配 flow 列表：

```json
{
  "query": "flow-demo",
  "count": 3,
  "flows": [
    {
      "flow_id": "flow-demo-001",
      "protocol": "TCP",
      "responder_port": 443,
      "duration_sec": 42.5,
      "suspicion_score": 78
    }
  ]
}
```

### 9.4 设计意义

真实业务中，分析师可能只知道部分 flow 标识，或者需要先检索候选会话。

这个工具对应的是：

```text
先找到分析对象，再做深入研判。
```

## 10. 工具三：analyze_flow

### 10.1 功能

分析单条 flow，输出风险等级、风险分数、命中特征和关键证据。

### 10.2 输入

```text
flow_id: str
```

### 10.3 输出

```json
{
  "flow_id": "flow-demo-002",
  "found": true,
  "label_hint": "encrypted_tunnel",
  "risk_score": 100,
  "risk_level": "high",
  "hit_features": [
    "non_standard_port",
    "encrypted_like_without_sni",
    "long_lived_session",
    "balanced_bidirectional_exchange"
  ],
  "evidence": {
    "protocol": "UDP",
    "responder_port": 51820,
    "duration_sec": 180.0,
    "bytes_per_second": 212.28,
    "packet_balance": 0.88,
    "has_tls_sni": 0
  },
  "next_action": "Review endpoint context, SNI/domain evidence, and similar false-positive cases."
}
```

### 10.4 风险规则

当前开源版使用可解释规则完成风险解释。

命中特征包括：

| 命中特征 | 含义 |
| --- | --- |
| non_standard_port | 响应端口不在常见服务端口集合内 |
| encrypted_like_without_sni | 可疑分较高且没有 TLS SNI |
| long_lived_session | 会话持续时间较长 |
| balanced_bidirectional_exchange | 上下行交互较均衡 |
| large_packet_pattern | 出现较大包长模式 |

风险分数基于 `suspicion_score` 和命中特征加权得到。

### 10.5 设计意义

这个工具是 MCP 中最核心的工具。

它把原本模型或规则输出的结果整理成大模型易于使用的结构化证据。

## 11. 工具四：generate_flow_report

### 11.1 功能

生成单条 flow 的 Markdown 研判报告。

### 11.2 输入

```text
flow_id: str
```

### 11.3 内部流程

```text
generate_flow_report
  -> analyze_flow
  -> search_vpn_knowledge
  -> 组合 Markdown 报告
```

### 11.4 输出内容

报告包含：

- Risk level
- Risk score
- Label hint
- Hit features
- Evidence
- Related knowledge
- Next action

### 11.5 设计意义

这个工具把 flow 分析结果和知识库内容组合起来，直接生成分析师可读的报告初稿。

它体现了 AI 应用中常见的模式：

```text
结构化工具结果 + 检索知识 + 模板化生成
```

## 12. 工具五：summarize_flows

### 12.1 功能

按风险阈值汇总可疑 flow。

### 12.2 输入

```text
min_risk_score: int = 70
limit: int = 10
```

### 12.3 输出

```json
{
  "min_risk_score": 70,
  "count": 3,
  "flows": [
    {
      "flow_id": "flow-demo-002",
      "risk_score": 100,
      "risk_level": "high",
      "label_hint": "encrypted_tunnel",
      "hit_features": ["non_standard_port", "long_lived_session"]
    }
  ]
}
```

### 12.4 设计意义

这个工具适合批量分析场景。

比如用户可以问：

```text
找出风险分大于 70 的可疑 flow。
```

Agent 就可以调用该工具进行初筛。

## 13. 典型调用链路

### 13.1 单条 flow 分析

```text
用户：分析 flow-demo-002
  -> analyze_flow("flow-demo-002")
  -> search_vpn_knowledge("命中特征 / 协议线索")
  -> 输出风险等级、证据、误报可能和复核建议
```

### 13.2 单条报告生成

```text
用户：给 flow-demo-002 生成研判报告
  -> generate_flow_report("flow-demo-002")
  -> 返回 Markdown 报告
```

### 13.3 批量高风险汇总

```text
用户：查看风险分大于 70 的 flow
  -> summarize_flows(min_risk_score=70)
  -> 返回高风险 flow 列表
```

### 13.4 知识问答

```text
用户：为什么正常下载可能被误判为隧道流量？
  -> search_vpn_knowledge("false positive download traffic")
  -> 基于知识库内容回答
```

## 14. 本地运行方式

### 14.1 创建环境

```bash
conda create -y -n vpn-flow-analyst-mcp python=3.10
conda activate vpn-flow-analyst-mcp
pip install -r requirements.txt
```

### 14.2 运行烟测

```bash
python tests/test_smoke.py
```

通过时输出：

```text
smoke tests passed
```

### 14.3 启动 MCP Server

```bash
python src/vpn_flow_analyst_mcp/server.py
```

### 14.4 MCP 客户端配置

示例配置：

```json
{
  "mcpServers": {
    "vpn-flow-analyst": {
      "command": "python",
      "args": [
        "C:/path/to/vpn-flow-analyst-mcp/src/vpn_flow_analyst_mcp/server.py"
      ],
      "cwd": "C:/path/to/vpn-flow-analyst-mcp"
    }
  }
}
```

## 15. 测试内容

烟测脚本位于：

```text
tests/test_smoke.py
```

测试内容包括：

- 知识库检索是否有结果
- flow 搜索是否正常
- 单流分析是否返回风险等级
- 单流报告是否生成 Markdown
- 高风险 flow 汇总是否正常
- MCP tool registry 是否能发现工具
- Skill 文件是否存在
- Skill frontmatter 是否规范

这保证了开源仓库在没有真实数据和模型的情况下也能独立运行。

## 16. 脱敏设计

开源版本刻意不包含：

- 原始 PCAP
- 真实 IP
- 真实域名
- 真实用户数据
- 内部部署路径
- 模型二进制
- 实验输出报告

只保留：

- 合成 flow 样例
- 通用知识库样例
- MCP server 代码
- Skill 说明
- 测试脚本

这样做的目的是：

```text
展示 AI 工具化设计能力，同时避免泄露真实安全数据。
```

## 17. 当前版本边界

当前版本是一个脱敏开源演示项目，不是完整生产系统。

主要边界：

- flow 数据来自合成样例
- 风险分析使用可解释规则，不包含真实训练模型
- 知识检索使用简单关键词匹配，不是完整向量检索
- 没有接入真实检测平台或数据库
- 没有公开内部实验报告和模型资产

这些边界是刻意设计的，因为当前开源目标是展示 MCP / Skill 能力封装，而不是公开完整检测系统。

## 18. 后续可扩展方向

后续可以继续扩展：

- 接入真实检测平台 API
- 将 CSV flow 样例替换为数据库查询
- 将 JSONL 知识库替换为向量库
- 增加 Hybrid RAG
- 增加 Agent Workflow
- 增加批量任务接口
- 增加报告导出
- 增加误报案例库
- 增加端到端 MCP client 测试

## 19. 面试解释口径

如果面试官问“MCP 是怎么做的”，可以这样回答：

```text
我把流量研判中的几个固定动作抽象成了 MCP tools，包括 flow 搜索、单流风险分析、知识库检索、报告生成和高风险 flow 汇总。

实现上使用 Python FastMCP，每个工具通过 @mcp.tool() 注册。开源版本为了脱敏，底层读取合成 flow CSV 和 JSONL 知识库，不包含真实流量和模型资产。

这样大模型或 Agent 在分析时不需要直接接触原始流量，而是通过 MCP 工具获取结构化证据，再结合 Skill 中定义的研判流程，输出风险等级、命中特征、误报可能和复核建议。
```

如果继续问“为什么要做 MCP”，可以这样回答：

```text
因为流量研判不是一次 prompt 能稳定完成的任务，它需要查 flow、看特征、检索协议知识、判断误报可能，再生成报告。

MCP 可以把这些步骤标准化成工具，方便不同 Agent 或客户端复用，也能减少大模型凭空生成的风险。
```

如果问“和 RAG 有什么关系”，可以这样回答：

```text
当前版本的 search_vpn_knowledge 是一个轻量知识检索工具，使用 JSONL 知识库做演示。它可以看成 RAG 的最小形态。

后续可以把这个工具替换成 BM25、向量检索或 Hybrid RAG，但 MCP 工具接口可以保持不变。这样 Agent 调用方式不变，只需要升级底层检索实现。
```

## 20. 总结

这个 MCP 项目的价值在于：

- 把安全流量研判动作工具化
- 把检测结果变成大模型可调用的结构化证据
- 把知识检索和报告生成纳入 Agent 工作流
- 用脱敏样例保证项目可公开展示
- 给后续 RAG、Agent、Skill 扩展留下接口

一句话概括：

```text
这是一个面向 VPN / 代理流量研判场景的 MCP 工具化原型，用来连接检测结果、知识库和大模型 Agent。
```

