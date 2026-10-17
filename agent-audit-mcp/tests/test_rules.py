"""rules.py 配置与阈值映射测试。"""

import pytest

from agent_audit import audit, engine
from agent_audit.rules import RuleConfig, default_config


def test_default_config_values():
    cfg = default_config()
    assert cfg.toolHi == 3
    assert cfg.eviLo == 2
    assert cfg.eviHi == 5
    assert cfg.tSlow == 3.0
    assert cfg.tFast == 0.5
    assert cfg.citeHi == 3
    assert cfg.jump == 4
    assert cfg.highConf == 0.8
    assert cfg.redDims == [5, 6, 7]


def test_config_from_dict_filters_unknown():
    cfg = RuleConfig.from_dict({"toolHi": 5, "not_a_field": 123})
    assert cfg.toolHi == 5
    assert not hasattr(cfg, "not_a_field")


def test_v1_structure_thresholds():
    assert audit.state_from_signals({"tool_calls": 0, "intent": "reason"})["vector"][0] == -1
    assert audit.state_from_signals({"tool_calls": 1, "intent": "reason"})["vector"][0] == 0
    assert audit.state_from_signals({"tool_calls": 3, "intent": "reason"})["vector"][0] == 1


def test_v2_intent_mapping():
    assert audit.state_from_signals({"tool_calls": 1, "intent": "retrieve"})["vector"][1] == -1
    assert audit.state_from_signals({"tool_calls": 1, "intent": "reason"})["vector"][1] == 0
    assert audit.state_from_signals({"tool_calls": 1, "intent": "produce"})["vector"][1] == 1


def test_v4_evidence_thresholds():
    base = {"tool_calls": 1, "intent": "reason"}
    assert audit.state_from_signals({**base, "evidence": 1})["vector"][3] == -1
    assert audit.state_from_signals({**base, "evidence": 3})["vector"][3] == 0
    assert audit.state_from_signals({**base, "evidence": 5})["vector"][3] == 1
    # 证据达标（2~4）且高置信 → ⊕（高置信不能抵消证据不足）
    assert audit.state_from_signals({**base, "evidence": 3, "confidence": 0.95})["vector"][3] == 1
    assert audit.state_from_signals({**base, "evidence": 1, "confidence": 0.95})["vector"][3] == -1


def test_v5_time_thresholds():
    base = {"tool_calls": 1, "intent": "reason"}
    assert audit.state_from_signals({**base, "elapsedRatio": 4.0})["vector"][4] == -1
    assert audit.state_from_signals({**base, "elapsedRatio": 1.0})["vector"][4] == 0
    assert audit.state_from_signals({**base, "elapsedRatio": 0.4})["vector"][4] == 1


def test_v6_auth_thresholds():
    base = {"tool_calls": 1, "intent": "reason"}
    assert audit.state_from_signals({**base, "unauthorized": True})["vector"][5] == -1
    assert audit.state_from_signals({**base, "sensitive": True})["vector"][5] == 1


def test_v7_citation_thresholds():
    base = {"tool_calls": 1, "intent": "reason"}
    assert audit.state_from_signals({**base, "citations": 0})["vector"][6] == -1
    assert audit.state_from_signals({**base, "citations": 2})["vector"][6] == 0
    assert audit.state_from_signals({**base, "citations": 4})["vector"][6] == 1


def test_v8_v9():
    base = {"tool_calls": 1, "intent": "reason"}
    assert audit.state_from_signals({**base, "riskHit": True})["vector"][7] == -1
    assert audit.state_from_signals({**base, "valueAdd": True})["vector"][7] == 1
    assert audit.state_from_signals({**base, "regress": True})["vector"][8] == -1
    assert audit.state_from_signals({**base, "jumpOver": True})["vector"][8] == 1


def test_encode_center_via_rules_is_9841():
    # 全部中性信号 → 中心态
    st = audit.state_from_signals(
        {"tool_calls": 1, "intent": "reason", "evidence": 3, "confidence": 0.5,
         "elapsedRatio": 1.0, "citations": 2}
    )
    assert st["idx"] == engine.CENTER_INDEX
    assert st["bal"] == 0