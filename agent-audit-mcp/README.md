# Agent 审计层 MCP 插件（agent-audit-mcp）

把 AI Agent 的**每一步决策**映射为九位平衡三进制认知状态序列（3⁹ = 19683，
中心态 9841），形成可枚举、可审计、可回溯的**决策认知轨迹**，并通过
**MCP（Model Context Protocol）** 暴露为腾讯 WorkBuddy 可直接调用的工具。

```
用户请求 ──▶ Agent 编排层（RAG + LLM + 工具）
                │            │
                │ 日志钩子    │ 九维审计（本插件）
                ▼            ▼
           信号(signals) ──▶ 九维状态 → 轨迹审计 → 审计报告(OK/WATCH/ALERT/BLOCK)
```

## 能力

| 工具 | 说明 |
| --- | --- |
| `audit_agent_step` | 审计单个决策步骤，返回九维状态编码（idx / bal / 三态串）与红线标记 |
| `audit_agent_session` | 审计整个会话决策轨迹，返回状态序列 + 总结论 + 处置建议 |
| `encode_state` | 九维三态向量 ⇄ 枚举键/平衡值换算；可选计算 Hamming 距离（教学/工具） |

九维维度：v1 结构 | v2 功能 | v3 关系 | v4 属性 | v5 时间 | v6 情境 | v7 因果 | v8 价值 | v9 演化，
每位三态 ⊖(−1)/0/⊕(+1)；红线维度 v6 越权（BLOCK）、v7 依据缺失 / v8 高风险（ALERT）、
相邻步 Hamming > 4 状态跳变（WATCH）。

## 安装

```bash
cd agent-audit-mcp
python -m pip install -e .
```

要求 Python ≥ 3.10，MCP SDK ≥ 2.0（`pip install -e .` 会自动安装）。

## 在 WorkBuddy 中接入

WorkBuddy 是 MCP **客户端（宿主）**，通过「连接器」接入外部 MCP Server。本插件支持两种连接器：

### 方式一：本地 stdio 连接器（个人工具，推荐）

1. 安装依赖后启动命令行：`python -m agent_audit.server`
2. 在 WorkBuddy「连接器」页新建 **本地 stdio** 类型连接器：
   - 命令：`python -m agent_audit.server`
   - 工作目录：本插件所在路径
3. 保存后 WorkBuddy 自动发现 `audit_agent_step` / `audit_agent_session` / `encode_state` 三个工具，
   对话中直接说「审计这一步决策…」即可调用。

### 方式二：远程 HTTP 连接器（跨机器 / 多人共享）

1. 启动 HTTP 服务（默认 9527 端口，与灵助生态习惯一致）：

   ```bash
   python -m agent_audit.server --transport http --host 0.0.0.0 --port 9527
   ```

2. 在 WorkBuddy「连接器」页新建 **HTTP / SSE** 类型连接器：
   - URL：`http://<主机地址>:9527/mcp`
   - 如服务部署在公网，建议置于网关后并配置 API Key。

## 阈值配置（可选）

通过环境变量覆盖默认阈值（示例值，接入真实日志后需校准）：

```bash
export NINE_AUDIT_TOOL_HI=3      # v1 工具调用数 ≥3 → ⊕
export NINE_AUDIT_EVI_LO=2       # v4 证据数 <2 → ⊖
export NINE_AUDIT_EVI_HI=5       # v4 证据数 ≥5 → ⊕
export NINE_AUDIT_T_SLOW=3.0     # v5 耗时 >3x → ⊖
export NINE_AUDIT_T_FAST=0.5     # v5 耗时 <0.5x → ⊕
export NINE_AUDIT_CITE_HI=3      # v7 引用数 ≥3 → ⊕
export NINE_AUDIT_JUMP=4         # 相邻步 Hamming >4 → WATCH
```

## 信号字段（audit_agent_step / audit_agent_session 入参）

工具入参为**嵌套结构**（与 MCP 工具签名一致）：

**`audit_agent_step`** → `{ "signals": { ...信号字段... } }`

**`audit_agent_session`** → `{ "steps": [ { ...信号字段... }, ... ], "session_id": "可选" }`

每个步骤的信号字段如下（`tool_calls` / `intent` 必需，其余可省略取安全默认值）：

```jsonc
{
  "tool_calls": 2,           // 工具调用数（必需）
  "intent": "reason",        // retrieve/reason/produce/execute/confirm（必需）
  "context_ok": true,        // 上下文是否对齐
  "strong_dep": false,       // 是否强依赖外部角色/工具
  "evidence": 3,             // 证据数
  "confidence": 0.85,        // 置信度 0..1
  "elapsed_ratio": 1.2,      // 耗时/基准耗时比值
  "unauthorized": false,     // 是否越权
  "sensitive": false,        // 是否敏感操作
  "citations": 2,            // 可溯源引用数
  "traceable": true,         // 引用是否可溯源
  "risk_hit": false,         // 是否命中高风险规则
  "value_add": false,        // 是否合规增值输出
  "regress": false,          // 是否状态回退
  "jump_over": false         // 是否跳过多步直达
}
```

兼容 HTML 演示原型的驼峰命名（`toolCalls` / `contextOk` / `riskHit` 等）与下划线命名，二者等价。

## 预设场景示例

`examples/` 含四个可直接代入 `audit_agent_session.steps` 的示例（对应设计四场景）：

| 文件 | 场景 | 预期结论 |
| --- | --- | --- |
| `scenario_a_ok.json` | 正常投顾建议 | OK |
| `scenario_b_alert.json` | 高风险全仓建议 | ALERT |
| `scenario_c_block.json` | 越权查询与荐股 | BLOCK |
| `scenario_d_watch.json` | 状态跳变逃逸 | WATCH |

## 测试

```bash
python -m pytest tests/ -v
```

覆盖：编码边界（idx 0 / 19682 / 9841、bal 0）、Hamming、四场景判定
（A OK / B ALERT / C BLOCK / D WATCH）、HTTP 握手与工具列表。

## 相关文档

- `../Agent审计层落地设计方案.md`：审计层方法论与判定规则
- `../Agent审计MCP插件-设计方案.md`：本插件设计文档
- `../实例大全-九维认知空间拓展.md`：九维认知空间与 10 实例档案