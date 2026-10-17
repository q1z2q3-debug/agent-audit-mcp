"""MCP Server：把九维 Agent 审计层暴露为可被 WorkBuddy 调用的工具。

支持两种 WorkBuddy 连接器：
- 本地 stdio：  python -m agent_audit.server
- 远程 HTTP：   python -m agent_audit.server --transport http --host 0.0.0.0 --port 9527
                （WorkBuddy URL 填 http://<host>:9527/mcp）

工具：
- audit_agent_step    审计单个决策步骤 → 九维状态
- audit_agent_session 审计整个会话 → 轨迹 + 总结论 + 处置建议
- encode_state        九维三态串 ⇄ idx/bal（工具/教学）
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Any, Dict, List, Optional, Sequence, Union

try:
    from mcp.server.mcpserver import MCPServer
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "缺少 MCP SDK，请先安装：python -m pip install 'mcp>=2.0'"
    ) from exc

from . import __version__
from . import signals as sig
from .audit import audit_session, state_from_signals
from .rules import RuleConfig, default_config

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9527
# 允许通过环境变量覆盖阈值，便于 WorkBuddy 侧按需调整
_ENV_PREFIX = "NINE_AUDIT_"


def _load_config_from_env() -> RuleConfig:
    cfg = default_config()
    mapping = {
        "TOOL_HI": "toolHi",
        "EVI_LO": "eviLo",
        "EVI_HI": "eviHi",
        "T_SLOW": "tSlow",
        "T_FAST": "tFast",
        "CITE_HI": "citeHi",
        "JUMP": "jump",
        "HIGH_CONF": "highConf",
    }
    for env_key, attr in mapping.items():
        val = os.environ.get(_ENV_PREFIX + env_key)
        if val is None:
            continue
        try:
            current = getattr(cfg, attr)
            if isinstance(current, bool):
                cast = _to_bool
            elif isinstance(current, float):
                cast = _to_float
            else:
                cast = _to_int
            setattr(cfg, attr, cast(val))
        except ValueError:
            sys.stderr.write(f"[agent-audit] 忽略非法阈值 {_ENV_PREFIX}{env_key}={val!r}\n")
    return cfg


def _to_bool(v: str) -> bool:
    return v.strip().lower() in ("1", "true", "yes", "on")


def _to_int(v: str) -> int:
    return int(v)


def _to_float(v: str) -> float:
    return float(v)


# ---------------------------------------------------------------------------
# 工具实现（确定性计算，返回可 JSON 序列化对象）
# ---------------------------------------------------------------------------

def _tool_audit_step(signals: Dict[str, Any]) -> Dict[str, Any]:
    """审计单个决策步骤，返回九维状态编码与红线标记。

    入参 signals 字段（均兼容小写/下划线或驼峰）：
      tool_calls 工具调用数(int, 必需)
      intent     语义意图: retrieve/reason/produce/execute/confirm(必需)
      context_ok 上下文是否对齐(bool, 默认 true)
      strong_dep 是否强依赖外部角色/工具(bool, 默认 false)
      evidence   证据数(int, 默认 0)
      confidence 置信度 0..1(float, 默认 0.5)
      elapsed_ratio 耗时/基准耗时比值(float, 默认 1.0)
      unauthorized 是否越权请求(bool, 默认 false)
      sensitive    是否敏感操作(bool, 默认 false)
      citations    回复中可溯源引用数(int, 默认 0)
      traceable    引用是否可溯源(bool, 默认 true)
      risk_hit     是否命中高风险规则(bool, 默认 false)
      value_add    是否合规增值输出(bool, 默认 false)
      regress      是否状态回退(bool, 默认 false)
      jump_over    是否跳过多步直达(bool, 默认 false)

    返回：{vector, vector_str, idx, bal, semantic, flags, signals_snapshot}
    """
    cfg = _load_config_from_env()
    return state_from_signals(_canonical(signals), cfg)


def _tool_audit_session(
    steps: List[Dict[str, Any]],
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """审计整个会话的决策轨迹。

    入参：
      steps     决策步骤 signals 列表（每项同上 audit_agent_step）
      session_id 会话标识(可选)

    返回：审计报告 {session_id, rules_version, verdict(OK/WATCH/ALERT/BLOCK),
                    reasons, trajectory, red_lines, jumps, actions, state_count}
    """
    cfg = _load_config_from_env()
    return audit_session([_canonical(s) for s in steps], session_id=session_id, config=cfg)


def _tool_encode_state(
    vector: Optional[str] = None,
    idx: Optional[int] = None,
    other_vector: Optional[str] = None,
) -> Dict[str, Any]:
    """九维三态向量 ⇄ 枚举键/平衡值；可计算与另一状态的 Hamming 距离。

    入参（二选一）：
      vector 九位三态串，如 "00⊖0⊖000⊖" 或 "-10-101010-1" 或 "012000102"
      idx     枚举键 0..19682
    可选：
      other_vector 另一个九位三态串，用于计算 Hamming 距离

    返回：{vector, vector_str, idx, bal, center?, hamming?}
    """
    from . import engine

    if vector is None and idx is None:
        raise ValueError("必须提供 vector 或 idx 之一")
    if vector is not None:
        vec = engine.index_to_vector(engine.vector_to_index(vector))
        idx_out = engine.vector_to_index(vector)
    else:
        idx_out = int(idx)
        vec = engine.index_to_vector(idx_out)
    result: Dict[str, Any] = {
        "vector": vec,
        "vector_str": engine.vector_str(vec),
        "idx": idx_out,
        "bal": engine.balance(idx_out),
        "is_center": idx_out == engine.CENTER_INDEX,
    }
    if other_vector is not None:
        result["hamming"] = engine.hamming(vec, other_vector)
    return result


def _canonical(signals: Dict[str, Any]) -> Dict[str, Any]:
    """把下划线/驼峰命名统一归一（委托 signals.canonicalize，幂等）。"""
    return sig.canonicalize(signals)


# ---------------------------------------------------------------------------
# MCP Server 组装
# ---------------------------------------------------------------------------

def build_server() -> MCPServer:
    server = MCPServer(
        name="agent-audit",
        title="Agent 审计层（九维认知空间）",
        description=(
            "九维认知空间 Agent 审计工具：把 Agent 决策步骤映射为九位平衡三进制"
            "（3^9=19683，中心态 9841）认知状态序列，输出枚举键/平衡值/红线标记，"
            "并对整个会话生成 OK/WATCH/ALERT/BLOCK 审计报告。"
            "Audit AI agent decisions with balanced ternary cognitive states."
        ),
        version=__version__,
    )
    server.add_tool(_tool_audit_step, name="audit_agent_step",
                    description="审计单个 Agent 决策步骤，返回九维状态编码(idx/bal/三态串)与红线标记")
    server.add_tool(_tool_audit_session, name="audit_agent_session",
                    description="审计整个会话决策轨迹，返回状态序列与 OK/WATCH/ALERT/BLOCK 总结论及处置建议")
    server.add_tool(_tool_encode_state, name="encode_state",
                    description="九维三态向量⇄枚举键/平衡值换算，可选计算与另一状态的 Hamming 距离（教学/工具）")
    return server


async def _run_stdio() -> None:
    server = build_server()
    await server.run_stdio_async()


async def _run_http(host: str, port: int) -> None:
    server = build_server()
    await server.run_streamable_http_async(
        host=host,
        port=port,
        streamable_http_path="/mcp",
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="九维 Agent 审计层 MCP Server")
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio",
                        help="传输方式：stdio（WorkBuddy 本地连接器）或 http（远程连接器）")
    parser.add_argument("--host", default=os.environ.get("NINE_AUDIT_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=int(os.environ.get("NINE_AUDIT_PORT", str(DEFAULT_PORT))))
    args = parser.parse_args(argv)

    if args.transport == "http":
        print(f"[agent-audit] HTTP MCP Server: http://{args.host}:{args.port}/mcp  (rules={_load_config_from_env()})", file=sys.stderr)
        asyncio.run(_run_http(args.host, args.port))
    else:
        asyncio.run(_run_stdio())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())