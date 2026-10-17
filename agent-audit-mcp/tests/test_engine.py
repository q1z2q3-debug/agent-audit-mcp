"""engine.py 编码引擎单元测试：边界、中心态、Hamming、语义。"""

import pytest

from agent_audit import engine


def test_state_space_size():
    assert engine.STATE_SPACE == 3 ** 9 == 19683
    assert engine.N_DIMS == 9


def test_center_index():
    assert engine.CENTER_INDEX == 9841
    assert engine.MIN_INDEX == 0
    assert engine.MAX_INDEX == 19682


def test_min_vector():
    # 全 ⊖ → idx 0
    assert engine.vector_to_index([-1] * 9) == 0


def test_max_vector():
    # 全 ⊕ → idx 19682
    assert engine.vector_to_index([1] * 9) == 19682


def test_center_vector():
    # 全 0 → idx 9841，bal 0
    assert engine.vector_to_index([0] * 9) == 9841
    assert engine.balance([0] * 9) == 0
    assert engine.balance(9841) == 0


def test_roundtrip_all_dim_positions():
    # 每个维度单独取三种值各验证 roundtrip
    for dim in range(9):
        for val in (-1, 0, 1):
            v = [0] * 9
            v[dim] = val
            assert engine.index_to_vector(engine.vector_to_index(v)) == v


def test_roundtrip_extremes():
    assert engine.index_to_vector(0) == [-1] * 9
    assert engine.index_to_vector(19682) == [1] * 9
    assert engine.index_to_vector(9841) == [0] * 9


def test_index_bounds():
    with pytest.raises(ValueError):
        engine.index_to_vector(-1)
    with pytest.raises(ValueError):
        engine.index_to_vector(19683)


def test_balance():
    assert engine.balance(0) == -9841
    assert engine.balance(19682) == 9841


def test_hamming():
    a = [-1] * 9
    b = [1] * 9
    assert engine.hamming(a, b) == 9
    assert engine.hamming(a, a) == 0
    assert engine.hamming([0] * 9, [0] * 9) == 0


def test_string_forms():
    # 三种字符串写法等价
    assert engine.vector_to_index("000000000") == 9841
    assert engine.vector_to_index("⊖⊖⊖⊖⊖⊖⊖⊖⊖") == 0
    assert engine.vector_to_index("⊕⊕⊕⊕⊕⊕⊕⊕⊕") == 19682
    assert engine.vector_to_index("⊖0⊖0⊕0⊕0⊖") == engine.vector_to_index(
        [-1, 0, -1, 0, 1, 0, 1, 0, -1]
    )


def test_invalid_inputs():
    with pytest.raises(ValueError):
        engine.vector_to_index([0] * 8)  # 长度不足
    with pytest.raises(ValueError):
        engine.vector_to_index([2] * 9)  # 非法三态值


def test_semantic_and_vector_str():
    assert engine.vector_str([0] * 9) == "000000000"
    sem = engine.semantic([-1, 0, 0, 0, 0, 0, 0, 0, 0])
    assert "任务结构" in sem