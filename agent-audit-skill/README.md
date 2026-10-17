# Agent 审计层 · 九维认知空间（agent-audit-mcp）

> 给 AI Agent 的每一步决策，装一个**可枚举、可审计、可回溯**的"认知黑匣子"。

当你把 RAG + LLM + 工具交给 Agent 自动运行时，最怕的不是它慢，而是它**悄悄越权、
拍脑袋下高风险结论、引用无法溯源、状态跳变逃逸**——事后说不清每一步为什么这么做。

`agent-audit-mcp` 把 Agent 的每一步决策映射为**九位平衡三进制认知状态序列**
（3⁹ = 19683 态，中心态 idx=9841），对整个会话给出四档结论：

| 结论 | 含义 | 处置 |
| --- | --- | --- |
| 🟢 **OK** | 全步骤无红线，迁移平稳 | 继续执行 |
| 🟡 **WATCH** | 相邻步 Hamming 距离 > 4（状态跳变） | 人工复核跳变点 |
| 🟠 **ALERT** | 命中高风险 / 依据缺失 | 停止自动执行，转合规复核 |
| 🔴 **BLOCK** | 命中越权红线 | 阻断执行，回退并补授权 |

九维维度：**结构 · 功能 · 关系 · 属性 · 时间 · 情境 · 因果 · 价值 · 演化**；
红线维度：v6 越权(BLOCK)、v7 依据缺失 / v8 高风险(ALERT)。
来自东方易理三态思维（⊖/0/⊕）× 现代 AI 工程，判定规则透明、阈值全部可调。

---

## ✨ 为什么是它

- **纯本地 / 零外部依赖**：编码引擎是纯数学（零依赖），审计全程本地跑，决策轨迹不出你的机器。
- **确定性可复现**：同样输入必得同样九维状态与结论，可写进合规审计报告。
- **标准 MCP**：接入后 WorkBuddy 对话里直接说"审计这一步决策…"即可调用，三个工具开箱即用。
- **可嵌入流水线**：`audit_agent_session` 可对整段 Agent 日志批量审计，天然适配 Agent 编排层的"日志钩子"。

## 🚀 三分钟接入（本地 stdio）

```bash
# 1) 安装（Python ≥ 3.10；PyPI 一键装，自动带上 MCP SDK ≥ 2.0）
python -m pip install agent-audit-mcp
#    源码开发装法： cd agent-audit-mcp && python -m pip install -e .

# 2) 一键注册为 WorkBuddy 连接器（安全合并，不覆盖现有配置）
python ../agent-audit-skill/install.py
# 然后到 WorkBuddy「连接器」页找到 agent-audit，点「Trust」启用

# 3) 直接对话调用
#    「审计这一步决策：tool_calls=2, intent=produce, evidence=4, citations=3」
#    「审计这个会话轨迹…」→ 返回 OK/WATCH/ALERT/BLOCK 报告
```

远程 HTTP（团队共享）：`python -m agent_audit.server --transport http --host 0.0.0.0 --port 9527`，
WorkBuddy 连 `http://<主机>:9527/mcp`。

## 🎬 看真实效果

见 [`demo/DEMO.md`](demo/DEMO.md)：四个预设场景（正常建议 / 高风险全仓 / 越权荐股 / 状态跳变逃逸）
由本地引擎真实跑出 **OK / ALERT / BLOCK / WATCH**，含每步九维向量、红线、跳变与处置建议。

## 🎯 适用人群

- 搭建 **AI Agent / 多智能体编排**的团队（给自动决策加一道合规闸）
- 需要 **AI 决策可解释、可溯源**的合规/风控场景
- 研究 **九维认知空间 / HexQ** 的教学与产品团队

## 💰 商业化路径

- **开源引流**：MIT 开源 + 技术文引流，建立"Agent 审计 = 九维认知空间"的心智占位。
- **企业版**：私有化部署、阈值定制、审计报表、与现有日志系统对接。
- **顾问/内训**：把九维认知审计方法论带入企业 AI 治理流程。

> 详见 `发布与上架指南.md`（上架步骤 + 变现分层）。

## 🔧 目录结构

```
agent-audit-mcp/            MCP Server 源码（engine/audit/rules/signals/server）
agent-audit-skill/          ← 本目录（可上架的技能包）
  SKILL.md                  技能清单（触发条件/能力/部署）
  README.md                 市场版说明（本文件）
  发布与上架指南.md         上架与变现
  引流技术文提纲.md          技术引流文大纲
  install.py                一键注册连接器
  demo/DEMO.md              真实运行演示
  gen_demo.py               演示生成器
```

## 📜 合规声明

本工具提供的是**决策审计编码与判定**，不构成任何投资建议或证券咨询服务。

## License

MIT © 润泽 · 灵助（三元九维）
