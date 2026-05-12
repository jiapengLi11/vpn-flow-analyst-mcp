# 将 VPN / 代理流量研判能力封装成 MCP 工具与 Codex Skill：一次 AI 应用工具化实践

## 前言

最近在做一个安全方向的 AI 应用实践，场景是商用 VPN / 代理流量的检测与研判。项目早期更多关注流量侧工作，比如 PCAP 抓取、会话聚合、特征提取、基线检测和误判分析。但如果只停留在“模型输出一个标签”这一层，离真正可用的安全分析工具还有一段距离。

安全分析师实际需要的是：

- 这条流为什么可疑？
- 命中了哪些特征？
- 有没有可能是正常业务误报？
- 类似协议或历史案例怎么解释？
- 下一步应该怎么复核？

所以我尝试把检测结果进一步封装成 AI 可调用能力：一部分做成 MCP 工具，负责 flow 查询、风险解释、知识检索和报告生成；另一部分做成 Codex Skill，沉淀安全研判流程，让大模型在分析时有固定的工作方式。

项目已脱敏开源：

GitHub：<https://github.com/jiapengLi11/vpn-flow-analyst-mcp>

## 一、为什么要做 MCP 和 Skill

在安全流量分析场景中，大模型直接看原始数据并不现实。

一方面，原始 PCAP 或真实 flow 里可能包含敏感信息，不适合直接暴露给模型；另一方面，流量研判不是单轮问答，而是一个多步骤过程：

1. 先查 flow 基础信息
2. 再看风险分数和命中特征
3. 再检索协议知识和误判案例
4. 最后生成研判结论和处置建议

如果把这些逻辑全部写进一个 prompt，不仅难维护，也不利于复用。

因此我把项目拆成两层：

- MCP：把查询、分析、检索、报告生成封装成标准工具
- Skill：告诉 AI 面对 VPN / 代理流量研判任务时应该怎么分析

这样模型不再只是“自由生成”，而是可以围绕工具结果和知识库证据做推理。

## 二、项目定位

这个开源仓库不是完整的流量检测平台，也不包含真实流量样本和训练模型。

它聚焦的是 AI 应用工具化这一层：

- 如何把检测结果抽象成 MCP tools
- 如何给 AI Agent 提供安全研判工作流
- 如何用脱敏样例数据完成可复现测试
- 如何让项目既能展示能力，又避免泄露真实数据

项目结构如下：

```text
vpn-flow-analyst-mcp/
├── data/
│   ├── sample_flows.csv          # 脱敏合成 flow 样例
│   └── vpn_knowledge.jsonl       # VPN / 代理研判知识库样例
├── skills/
│   └── vpn-flow-analyst/
│       ├── SKILL.md              # Codex Skill
│       └── agents/openai.yaml
├── src/
│   └── vpn_flow_analyst_mcp/
│       └── server.py             # MCP Server
├── tests/
│   └── test_smoke.py             # 烟测脚本
├── README.md
├── OPEN_SOURCE_CHECKLIST.md
└── requirements.txt
```

## 三、MCP 工具设计

当前 MCP server 提供了 5 个工具：

```text
search_vpn_knowledge(query, limit=5)
search_flows(flow_id_query, limit=10)
analyze_flow(flow_id)
generate_flow_report(flow_id)
summarize_flows(min_risk_score=70, limit=10)
```

### 1. search_vpn_knowledge

用于检索 VPN / 代理相关知识，比如协议特征、误判原因、指标说明和处置建议。

知识库采用 JSONL 格式，方便后续替换成向量库或 Hybrid RAG。

示例知识：

```json
{
  "id": "proto-wireguard-001",
  "title": "WireGuard traffic clues",
  "tags": ["wireguard", "vpn", "udp"],
  "content": "WireGuard is UDP based. Typical clues include stable peer endpoints, compact handshake packets, periodic keepalive behavior, and long-lived bidirectional encrypted payload exchange."
}
```

### 2. search_flows

用于按 flow_id 模糊搜索样例流量。

在真实项目中，这个工具可以对接检测平台或数据库；在开源版本中，为了脱敏，只使用合成样例 CSV。

### 3. analyze_flow

用于分析单条 flow，输出：

- 风险分数
- 风险等级
- 命中特征
- 关键证据
- 下一步建议

这里没有直接暴露原始 PCAP，而是基于会话级结构化特征做解释。

### 4. generate_flow_report

用于生成单条 flow 的 Markdown 研判报告。

它会先调用 flow 分析逻辑，再根据命中特征检索知识库，最后组合成一个结构化报告。

### 5. summarize_flows

用于按风险阈值汇总高风险 flow，适合批量任务后的初筛。

## 四、Skill 设计

Skill 的作用不是写业务代码，而是给 AI 一个稳定的工作流程。

我在 `SKILL.md` 中约束了分析步骤：

```text
1. Identify the target
2. Gather evidence
3. Answer with risk level, evidence, false-positive possibility, next action, and uncertainty
```

同时也加了安全说明：

- 不要声称解密了 payload
- 不要在证据不足时断言具体 VPN 类型
- 对统计特征推断出的结果，优先使用 “suspected encrypted tunnel” 或 “VPN-like behavior”
- 指标提升要说明基线和计算方式

这部分对面试也很重要，因为安全场景里的大模型应用不能只追求“会生成”，还要关注可控性和可解释性。

## 五、脱敏开源策略

这个项目在开源时做了专门的范围收敛。

没有开源：

- 原始 PCAP
- 真实 flow_id
- 真实 IP / 域名
- 模型权重
- 内部部署文档
- 实验输出报告

开源仓库只保留：

- MCP 工具代码
- Codex Skill
- 合成 flow 样例
- 通用知识库样例
- 测试脚本
- 开源检查清单

这也是我觉得安全项目开源时很重要的一点：不是把所有东西都传上去，而是把可复用的工程能力抽象出来。

## 六、本地运行与测试

创建环境：

```bash
conda create -y -n vpn-flow-analyst-mcp python=3.10
conda activate vpn-flow-analyst-mcp
pip install -r requirements.txt
```

运行测试：

```bash
python tests/test_smoke.py
```

测试通过时会输出：

```text
smoke tests passed
```

启动 MCP server：

```bash
python src/vpn_flow_analyst_mcp/server.py
```

MCP 客户端配置示例：

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

## 七、测试结果

我在独立 Anaconda 环境中做了烟测，验证内容包括：

- Skill 文件结构
- Skill frontmatter
- Skill UI 元数据
- 知识库检索
- flow 搜索
- 单流分析
- 研判报告生成
- MCP 工具注册

结果：

```text
smoke tests passed
```

其中 MCP 工具注册能发现以下 tools：

```text
search_vpn_knowledge
search_flows
analyze_flow
generate_flow_report
summarize_flows
```

## 八、项目中的一个工程细节

在原始实验项目中，模型资产曾经由 `scikit-learn 1.6.1` 保存。如果新环境默认安装更高版本，可能会出现 joblib 反序列化失败。

这提醒我，AI 应用项目不只是“模型能跑一次”就够了，还需要关注：

- 依赖版本固定
- 环境复现
- 数据脱敏
- 工具接口稳定
- 测试脚本可复用

所以在开源的 MCP / Skill 版本中，我没有直接依赖真实模型资产，而是改用合成样例和可解释规则完成工具演示。这样仓库更轻，也更适合公开展示。

## 九、面试中可以怎么讲

如果面试官问这个项目，我会这样介绍：

> 我把商用 VPN / 代理流量检测结果抽象成了 MCP 工具和 Codex Skill。MCP 负责提供 flow 查询、风险解释、知识检索和报告生成能力；Skill 负责沉淀安全研判流程，让大模型在分析时按照“查证据、看命中特征、检索知识、给出处置建议”的方式工作。开源版本只保留脱敏样例和工具层代码，不包含真实流量和模型资产。

如果继续追问为什么要做 MCP：

> 因为流量研判是多步骤任务，不适合只靠一个 prompt 完成。MCP 可以把可复用能力标准化暴露给 Agent，比如查询 flow、检索知识、生成报告。这样模型的回答可以基于工具结果，而不是完全自由生成。

如果问 Skill 的价值：

> Skill 更像是给 AI 的任务说明书。它约束了安全场景下的分析流程和措辞边界，比如不能声称解密 payload，不能在证据不足时断言具体 VPN 类型，要输出风险等级、证据、不确定性和下一步建议。

## 十、总结

这个项目的重点不是做一个完整的商业安全平台，而是把已有的流量检测思路进一步抽象成 AI 应用可复用能力。

我觉得这类工作很适合 AI 应用开发岗位，因为它不只是在调用大模型 API，而是在思考：

- 业务数据怎么结构化
- 模型应该调用哪些工具
- 知识库怎么提供证据
- 输出如何可解释
- 开源时如何脱敏

这也是我后续继续完善的方向：把 MCP 工具和 RAG 检索结合得更深，再补一个更完整的 Agent workflow，让安全研判从“模型输出标签”走向“可解释、可复核、可复用的智能分析流程”。

