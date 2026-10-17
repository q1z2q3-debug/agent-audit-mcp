"""audit.py 四场景判定测试：A OK / B ALERT / C BLOCK / D WATCH。"""

import json
from pathlib import Path

import pytest

from agent_audit import audit, engine

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def _load(name: str) -> dict:
    with open(EXAMPLES / name, encoding="utf-8") as f:
        return json.load(f)


def test_scenario_a_ok():
    data = _load("scenario_a_ok.json")
    report = audit.audit_session(data["steps"], session_id=data["session_id"])
    assert report["verdict"] == "OK"
    assert report["red_lines"] == []
    assert report["jumps"] == []
    assert report["state_count"] == 2


def test_scenario_b_alert():
    data = _load("scenario_b_alert.json")
    report = audit.audit_session(data["steps"], session_id=data["session_id"])
    assert report["verdict"] == "ALERT"
    # 步骤 2 无依据(v7 ⊖) + 高风险(v8 ⊖)
    assert any("依据缺失" in f for st in report["red_lines"] for f in st["flags"])
    assert any("高风险" in f for st in report["red_lines"] for f in st["flags"])


def test_scenario_c_block():
    data = _load("scenario_c_block.json")
    report = audit.audit_session(data["steps"], session_id=data["session_id"])
    # 越权红线优先 → BLOCK
    assert report["verdict"] == "BLOCK"
    assert any("越权" in f for st in report["red_lines"] for f in st["flags"])
    assert report["actions"][0] == "阻断执行"


def test_scenario_d_watch():
    data = _load("scenario_d_watch.json")
    report = audit.audit_session(data["steps"], session_id=data["session_id"])
    # 无红线、有跳变 → WATCH
    assert report["verdict"] == "WATCH"
    assert report["red_lines"] == []
    assert len(report["jumps"]) >= 1
    assert report["jumps"][0]["dist"] > 4


def test_verdict_priority():
    # 同时具备 BLOCK 与 ALERT 时 BLOCK 优先
    report = audit.audit_session(
        [
            {"tool_calls": 1, "intent": "retrieve", "unauthorized": True, "citations": 0},
            {"tool_calls": 1, "intent": "produce", "riskHit": True, "citations": 0},
        ]
    )
    assert report["verdict"] == "BLOCK"


def test_step_numbering_and_red_line_detail():
    data = _load("scenario_c_block.json")
    report = audit.audit_session(data["steps"])
    assert [t["step"] for t in report["trajectory"]] == [1, 2]
    assert report["red_lines"][0]["step"] == 1
    assert "越权" in report["red_lines"][0]["why"]


def test_signals_camel_case_compat():
    # 驼峰字段在 server._canonical 归一，这里验证 audit 层对下划线兼容
    st = audit.state_from_signals(
        {"tool_calls": 1, "intent": "produce", "citations": 4, "traceable": True}
    )
    assert st["vector"][6] == 1


def test_single_step_is_state():
    st = audit.state_from_signals(
        {"tool_calls": 2, "intent": "reason", "evidence": 3, "confidence": 0.85,
         "elapsedRatio": 1.0, "citations": 2, "traceable": True}
    )
    assert isinstance(st["idx"], int)
    assert engine.index_to_vector(st["idx"]) == st["vector"]