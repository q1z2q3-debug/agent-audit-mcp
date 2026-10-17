"""决策步骤信号数据模型与校验。

信号字段设计对齐 HTML 原型（agent-audit-demo.html）与设计方案：
工具调用数、语义意图、上下文命中、证据/引用、置信度、耗时比值、
授权、敏感、风险命中、迁移方向（prev_phase → step_phase）。
非法或缺失字段给出可读错误；缺失可推断字段用安全中性默认值。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

MINIMAL_FIELDS = ("tool_calls", "intent")
# 外部命名（下划线或驼峰）→ 内部键名。幂等映射：两种写法统一到同一内部键，
# 内部键与 HTML 原型一致（tool_calls/intent 保留下划线，其余推断字段用驼峰）。
_INPUT_TO_INTERNAL = {
    # v1 结构
    "tool_calls": "tool_calls",
    "toolCalls": "tool_calls",
    # v3 关系
    "context_ok": "contextOk",
    "contextOk": "contextOk",
    "strong_dep": "strongDep",
    "strongDep": "strongDep",
    # v5 时间
    "elapsed_ratio": "elapsedRatio",
    "elapsedRatio": "elapsedRatio",
    # v6 情境
    "unauthorized": "unauthorized",
    "sensitive": "sensitive",
    # v7 因果
    "citations": "citations",
    "traceable": "traceable",
    # v8 价值
    "risk_hit": "riskHit",
    "riskHit": "riskHit",
    "value_add": "valueAdd",
    "valueAdd": "valueAdd",
    # v9 演化
    "regress": "regress",
    "jump_over": "jumpOver",
    "jumpOver": "jumpOver",
    # 迁移
    "prev_phase": "prev_phase",
    "step_phase": "step_phase",
}
INFERABLE_DEFAULTS: Dict[str, Any] = {
    "contextOk": True,
    "strongDep": False,
    "evidence": 0,
    "confidence": 0.5,
    "elapsedRatio": 1.0,
    "unauthorized": False,
    "sensitive": False,
    "citations": 0,
    "traceable": True,
    "riskHit": False,
    "valueAdd": False,
    "regress": False,
    "jumpOver": False,
}


def canonicalize(raw: Dict[str, Any]) -> Dict[str, Any]:
    """把下划线/驼峰混合命名归一为内部键名（幂等，可反复调用）。"""
    if not isinstance(raw, dict):
        raise ValueError(f"signals 必须是对象，实际 {type(raw).__name__}")
    return {_INPUT_TO_INTERNAL.get(k, k): v for k, v in raw.items()}


def validate_signals(raw: Dict[str, Any], *, strict: bool = False) -> Dict[str, Any]:
    """校验并补齐信号。strict=True 时未知字段报错；默认放行（便于扩展）。"""
    raw = canonicalize(raw)

    if not isinstance(raw, dict):
        raise ValueError(f"signals 必须是对象，实际 {type(raw).__name__}")

    missing = [k for k in MINIMAL_FIELDS if k not in raw]
    if missing:
        raise ValueError(f"signals 缺少必需字段: {', '.join(missing)}")

    s: Dict[str, Any] = dict(raw)
    for k, default in INFERABLE_DEFAULTS.items():
        s.setdefault(k, default)

    tool_calls = s["tool_calls"]
    if isinstance(tool_calls, bool) or not isinstance(tool_calls, (int, float)) or tool_calls < 0:
        raise ValueError(f"tool_calls 必须是非负数值，实际 {tool_calls!r}")
    s["tool_calls"] = int(tool_calls)

    intent = str(s["intent"]).lower()
    if intent not in ("retrieve", "reason", "produce", "confirm", "execute"):
        raise ValueError(f"intent 非法: {s['intent']!r}（允许 retrieve/reason/produce/confirm/execute）")
    s["intent"] = intent

    for k in ("evidence", "citations"):
        v = s[k]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v < 0:
            raise ValueError(f"{k} 必须是非负数值，实际 {v!r}")
        s[k] = int(v)

    conf = s["confidence"]
    if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
        raise ValueError(f"confidence 必须在 [0,1]，实际 {conf!r}")

    ratio = s["elapsedRatio"]
    if not isinstance(ratio, (int, float)) or ratio <= 0:
        raise ValueError(f"elapsedRatio 必须 > 0，实际 {ratio!r}")

    for k in ("contextOk", "strongDep", "unauthorized", "sensitive", "traceable",
              "riskHit", "valueAdd", "regress", "jumpOver"):
        s[k] = bool(s[k])

    # 可选迁移字段
    if raw.get("prev_phase") is not None or raw.get("step_phase") is not None:
        s["prev_phase"] = str(raw.get("prev_phase", "start")).lower()
        s["step_phase"] = str(raw.get("step_phase", "")).lower()

    if strict:
        unknown = [k for k in s if k not in set(MINIMAL_FIELDS) | set(INFERABLE_DEFAULTS)
                   and k not in ("prev_phase", "step_phase")]
        if unknown:
            raise ValueError(f"未知信号字段: {', '.join(sorted(unknown))}")
    return s