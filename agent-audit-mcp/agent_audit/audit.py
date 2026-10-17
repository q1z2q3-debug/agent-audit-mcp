"""九维状态判定 + 状态序列审计报告生成。

流程：signals → 九维状态（含 idx/bal/语义/标记） → 轨迹审计
（红线、跳变、总结论 OK/WATCH/ALERT/BLOCK） → 审计报告。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from . import engine
from . import signals as sig
from .rules import RULES_VERSION, RuleConfig, default_config


def state_from_signals(raw: Dict[str, Any], config: Optional[RuleConfig] = None) -> Dict[str, Any]:
    """单个决策步骤信号 → 九维状态。与 HTML 原型 stateFromSignals 语义一致。"""
    cfg = config or default_config()
    s = sig.validate_signals(raw)

    # v1 任务结构
    v1 = -1 if s["tool_calls"] <= 0 else (1 if s["tool_calls"] >= cfg.toolHi else 0)
    # v2 步骤意图
    v2 = -1 if s["intent"] == "retrieve" else (1 if s["intent"] in ("produce", "execute", "confirm") else 0)
    # v3 上下文关联
    v3 = -1 if not s["contextOk"] else (1 if s["strongDep"] else 0)
    # v4 信息充足度
    v4 = -1 if s["evidence"] < cfg.eviLo else (1 if (s["evidence"] >= cfg.eviHi or s["confidence"] >= cfg.highConf) else 0)
    # v5 步骤节奏
    ratio = float(s["elapsedRatio"])
    v5 = -1 if ratio > cfg.tSlow else (1 if ratio < cfg.tFast else 0)
    # v6 权限边界
    v6 = -1 if s["unauthorized"] else (1 if s["sensitive"] else 0)
    # v7 决策依据链
    v7 = -1 if s["citations"] <= 0 else (1 if (s["citations"] >= cfg.citeHi and s["traceable"]) else 0)
    # v8 风险等级
    v8 = -1 if s["riskHit"] else (1 if s["valueAdd"] else 0)
    # v9 状态迁移
    v9 = -1 if s["regress"] else (1 if s["jumpOver"] else 0)

    vector = [v1, v2, v3, v4, v5, v6, v7, v8, v9]
    idx = engine.vector_to_index(vector)
    bal = engine.balance(idx)
    flags = _flags_for(vector, cfg)

    return {
        "vector": vector,
        "vector_str": engine.vector_str(vector),
        "idx": idx,
        "bal": bal,
        "semantic": engine.semantic(vector),
        "flags": flags,
        "signals_snapshot": s,
    }


def _flags_for(vector: List[int], cfg: RuleConfig) -> List[str]:
    flags = []
    for dim, name in cfg.redFlags.items():
        if vector[dim] == -1:
            flags.append(f"RED:v{dim + 1}{name}")
    return flags


def audit_session(
    steps: Sequence[Dict[str, Any]],
    *,
    session_id: Optional[str] = None,
    config: Optional[RuleConfig] = None,
) -> Dict[str, Any]:
    """整个会话的决策轨迹 → 审计报告。steps 为 signals 列表。"""
    cfg = config or default_config()
    states = [state_from_signals(st, cfg) for st in steps]

    red_lines = []
    for i, st in enumerate(states):
        if st["flags"]:
            red_lines.append({
                "step": i + 1,
                "flags": st["flags"],
                "vector_str": st["vector_str"],
                "idx": st["idx"],
                "why": f"步骤 {i + 1} 触发红线维度：{'、'.join(st['flags'])}",
            })

    jumps = []
    for j in range(1, len(states)):
        dist = engine.hamming(states[j - 1]["vector"], states[j]["vector"])
        if dist > cfg.jump:
            jumps.append({"from": j, "to": j + 1, "dist": dist})

    has_block = any("越权" in f for r in red_lines for f in r["flags"])
    has_alert = any(("高风险" in f or "依据缺失" in f) for r in red_lines for f in r["flags"])
    has_watch = len(jumps) > 0
    verdict = "OK"
    reasons = []
    if has_block:
        verdict = "BLOCK"
        reasons.append("存在越权红线（BLOCK 需人工介入并阻断）")
    elif has_alert:
        verdict = "ALERT"
        reasons.append("存在高风险或依据缺失（ALERT 需合规复核）")
    elif has_watch:
        verdict = "WATCH"
        reasons.append("相邻步骤跳变（WATCH 需人工复核）")
    else:
        reasons.append("全部步骤未触发红线，状态迁移平稳")

    actions = _actions_for(verdict, red_lines, jumps)

    return {
        "session_id": session_id or "",
        "rules_version": RULES_VERSION,
        "verdict": verdict,
        "reasons": reasons,
        "trajectory": [
            {k: st[k] for k in ("step", "text", "vector", "vector_str", "idx", "bal", "semantic", "flags") if k in st}
            for st in _with_step_numbers(states)
        ],
        "red_lines": red_lines,
        "jumps": jumps,
        "actions": actions,
        "state_count": len(states),
    }


def _with_step_numbers(states: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for i, st in enumerate(states, start=1):
        st = dict(st)
        st["step"] = i
        out.append(st)
    return out


def _actions_for(verdict: str, red_lines: List[Dict[str, Any]], jumps: List[Dict[str, Any]]) -> List[str]:
    if verdict == "BLOCK":
        actions = ["阻断执行", "回退到越权发生前一步", "补充授权/权限审批后重试"]
    elif verdict == "ALERT":
        actions = ["停止自动执行，转人工合规复核", "补充证据与可溯源引用", "重新生成高置信输出"]
    elif verdict == "WATCH":
        actions = [f"复核跳变位置（步骤 {j['from']}→{j['to']}，距离 {j['dist']}）" for j in jumps] or ["人工复核状态跳变"]
    else:
        actions = ["无需干预，继续执行"]
    return actions