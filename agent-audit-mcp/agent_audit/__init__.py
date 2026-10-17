"""agent_audit —— 九维认知空间 Agent 审计层 MCP 插件核心包。

把 AI Agent 的"每一步决策"映射为九位平衡三进制认知状态序列，
形成可枚举、可审计、可回溯的决策认知轨迹。

- engine: 平衡三进制编码引擎（3^9=19683，中心态 9841，Hamming 距离）
- rules:  九维判定规则与阈值配置
- signals: 决策步骤信号模型
- audit:  九维状态判定 + 审计报告
- server: MCP Server（stdio / Streamable HTTP），供 WorkBuddy 接入
"""

__version__ = "1.0.0"
__all__ = [
    "__version__",
    "engine",
    "rules",
    "signals",
    "audit",
    "server",
]