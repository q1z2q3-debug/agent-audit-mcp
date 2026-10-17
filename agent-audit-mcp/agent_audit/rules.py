"""九维判定规则与阈值配置（全部可配置；示例阈值，接入真实日志后需校准）。

与 HTML 原型 / 设计方案保持同一套规则语义：
- v1 结构：tool_calls==0 → ⊖；1~2 → 0；>= toolHi → ⊕
- v2 功能：retrieve → ⊖；reason → 0；produce/confirm → ⊕
- v3 关系：!contextOk → ⊖；strongDep → ⊕；否则 0
- v4 属性：evidence < eviLo → ⊖；>= eviHi 或高置信 → ⊕；否则 0
- v5 时间：ratio > tSlow → ⊖；< tFast → ⊕；否则 0
- v6 情境：unauthorized → ⊖；sensitive → ⊕；否则 0
- v7 因果：citations <= 0 → ⊖；>= citeHi 且可溯源 → ⊕；否则 0
- v8 价值：riskHit → ⊖；valueAdd → ⊕；否则 0
- v9 演化：regress → ⊖；jumpOver → ⊕；否则 0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

RULES_VERSION = "1.0.0"


@dataclass
class RuleConfig:
    """阈值配置，可通过 JSON 覆盖。"""
    toolLo: int = 1          # v1 工具调用数下限（<=0 缺）
    toolHi: int = 3          # v1 工具调用数上限（>=3 多/并行）
    eviLo: int = 2           # v4 证据数下限（<2 缺）
    eviHi: int = 5           # v4 证据数上限（>=5 足）
    tSlow: float = 3.0       # v5 耗时比值慢阈值（>3x 慢）
    tFast: float = 0.5       # v5 耗时比值快阈值（<0.5x 快）
    citeLo: int = 1          # v7 引用数下限（0 缺）
    citeHi: int = 3          # v7 引用数上限（>=3 且可溯源 足）
    jump: int = 4            # 相邻步 Hamming 距离 > 4 → 状态跳变
    highConf: float = 0.8    # v4 置信度高阈值
    redDims: List[int] = field(default_factory=lambda: [5, 6, 7])  # 红线维度（0-based v6/v7/v8）
    redFlags: Dict[int, str] = field(default_factory=lambda: {5: "越权", 6: "依据缺失", 7: "高风险"})

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "RuleConfig":
        known = {
            k: v for k, v in d.items()
            if k in cls.__dataclass_fields__  # type: ignore[attr-defined]
        }
        return cls(**known)


def default_config() -> RuleConfig:
    return RuleConfig()