---
name: agent-audit-mcp
version: 1.0.0
title: Agent 审计层（九维认知空间）
description: 把 AI Agent 的每一步决策映射为九位平衡三进制认知状态序列（3^9=19683，中心态 9841），对单个步骤或整个会话生成 OK / WATCH / ALERT / BLOCK 审计报告（越权/依据缺失/高风险/状态跳变）。当用户要求审计 AI Agent 的决策步骤或会话轨迹、判断 Agent 是否越权/高风险/缺乏证据、或把决策编码为九维三态认知状态时使用本技能。
author: 润泽 · 灵助（三元九维）
license: MIT
---

# Agent 审计层 MCP（agent-audit-mcp）

把 AI Agent 的**每一步决策**映射为九位平衡三进制认知状态序列（3⁹ = 19683 态，
中心态 idx=9841），形成**可枚举、可审计、可回溯**的决策认知轨迹，并通过
**MCP（Model Context Protocol）** 暴露为 WorkBuddy 可直接调用的工具。

```
用户请求 ──▶ Agent 编排层（RAG + LLM + 工具）
                │            │
                │ 日志钩子    │ 九维审计（本技能）
                ▼            ▼
           信号(signals) ──▶ 九维状态 → 轨迹审计 → 审计报告(OK/WATCH/ALERT/BLOCK)
```

## 能力（3 个 MCP 工具）

| 工具 | 用途 | 返回 |
| --- | --- | --- |
| `audit_agent_step` | 审计单个决策步骤 | 九维状态编码（idx / bal / 三态串）+ 红线标记 |
| `audit_agent_session` | 审计整个会话决策轨迹 | 状态序列 + OK/WATCH/ALERT/BLOCK 总结论 + 处置建议 |
| `encode_state` | 九维三态向量 ⇄ 枚举键/平衡值 | 可算两状态 Hamming 距离（教学/工具） |

九维维度：结构 · 功能 · 关系 · 属性 · 时间 · 情境 · 因果 · 价值 · 演化，
每位三态 ⊖(−1)/0/⊕(+1)。

**判定规则**（阈值可用环境变量覆盖，见下）：
- v6 情境 `越权` → BLOCK
- v7 因果 `依据缺失` / v8 价值 `高风险` → ALERT
- 相邻步 Hamming 距离 > 4 → WATCH
- 以上皆无 → OK

## 何时使用（触发条件）

用户出现以下意图时调用本技能：
- 「审计这一步 Agent 决策…」「审计这个会话的决策轨迹…」
- 「Agent 是否越权 / 高风险 / 缺乏证据？给出审计结论」
- 「把这段决策编码成九维认知状态 / 算枚举键 / 算 Hamming 距离」

## 部署方式

本技能是一个 **MCP Server**，需要注册为 WorkBuddy 连接器后，对话中即可调用。

### 方式一：本地 stdio 连接器（推荐，单人使用）

1. 安装（二选一）：
   ```bash
   # 从 PyPI 一键安装（推荐）：https://pypi.org/project/agent-audit-mcp/
   python -m pip install agent-audit-mcp
   # 或源码开发安装：
   cd agent-audit-mcp && python -m pip install -e .
   ```
2. 在 WorkBuddy「连接器」页新建 **本地 stdio** 连接器：
   - 命令：`<你的python> -m agent_audit.server`
   - 工作目录：`agent-audit-mcp` 包所在路径
3. 保存后自动发现三个工具，对话中直接说「审计这一步决策…」即可。

> 一键安装器：运行本目录 `install.py`（自动把连接器写进 `~/.workbuddy/mcp.json`，安全合并不覆盖）。

### 方式二：远程 HTTP 连接器（跨机器 / 团队共享）

```bash
python -m agent_audit.server --transport http --host 0.0.0.0 --port 9527
```
WorkBuddy 新建 HTTP/SSE 连接器，URL 填 `http://<主机>:9527/mcp`（公网建议网关 + API Key）。

## 工具入参（signals）

`audit_agent_step` → `{ "signals": { ... } }`
`audit_agent_session` → `{ "steps": [ { ... }, ... ], "session_id": "可选" }`

每个步骤字段（`tool_calls` / `intent` 必需，其余可省略取安全默认；下划线或驼峰命名皆可）：

```jsonc
{
  "tool_calls": 2,            // 工具调用数（必需）
  "intent": "reason",         // retrieve/reason/produce/execute/confirm（必需）
  "context_ok": true,         // 上下文是否对齐
  "strong_dep": false,        // 是否强依赖外部角色/工具
  "evidence": 3,              // 证据数
  "confidence": 0.85,         // 置信度 0..1
  "elapsed_ratio": 1.2,       // 耗时/基准耗时比值
  "unauthorized": false,      // 是否越权
  "sensitive": false,         // 是否敏感操作
  "citations": 2,             // 可溯源引用数
  "traceable": true,          // 引用是否可溯源
  "risk_hit": false,          // 是否命中高风险规则
  "value_add": false,         // 是否合规增值输出
  "regress": false,           // 是否状态回退
  "jump_over": false          // 是否跳过多步直达
}
```

## 阈值配置（可选，环境变量覆盖）

```bash
export NINE_AUDIT_TOOL_HI=3      # v1 工具调用数 ≥3 → ⊕
export NINE_AUDIT_EVI_LO=2       # v4 证据数 <2 → ⊖
export NINE_AUDIT_EVI_HI=5       # v4 证据数 ≥5 → ⊕
export NINE_AUDIT_T_SLOW=3.0     # v5 耗时 >3x → ⊖
export NINE_AUDIT_T_FAST=0.5     # v5 耗时 <0.5x → ⊕
export NINE_AUDIT_CITE_HI=3      # v7 引用数 ≥3 → ⊕
export NINE_AUDIT_JUMP=4         # 相邻步 Hamming >4 → WATCH
export NINE_AUDIT_HIGH_CONF=0.8  # v4 高置信阈值
```

## 相关文件

- `../agent-audit-mcp/` —— MCP Server 源码（engine / audit / rules / signals / server）
- `demo/DEMO.md` —— 四场景真实运行演示（OK / ALERT / BLOCK / WATCH）
- `README.md` —— 市场版说明（价值主张、安装、变现）
- `发布与上架指南.md` —— 如何上架到市场并变现
