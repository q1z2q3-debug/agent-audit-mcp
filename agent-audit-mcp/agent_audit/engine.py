"""平衡三进制编码引擎（纯数学，零依赖）。

九维认知空间基本结构单元：9 个认知观察角度，每位 ∈ {-1, 0, +1}，
状态空间大小 3^9 = 19683，枚举键 idx ∈ [0, 19682]，中心态 idx = 9841。

与中药材九维认知指纹库 v1-v4 使用同一套编码/键/距离数学。
"""

from __future__ import annotations

from typing import Iterable, List, Sequence, Union

N_DIMS = 9
STATE_SPACE = 3 ** N_DIMS  # 19683
CENTER_INDEX = (STATE_SPACE - 1) // 2  # 9841
MIN_INDEX = 0
MAX_INDEX = STATE_SPACE - 1  # 19682
SYMBOLS = {-1: "\u2296", 0: "0", 1: "\u2295"}  # ⊖ / 0 / ⊕
DIM_NAMES = ["结构", "功能", "关系", "属性", "时间", "情境", "因果", "价值", "演化"]
DIM_FULL_NAMES = [
    "任务结构", "步骤意图", "上下文关联", "信息充足度", "步骤节奏",
    "权限边界", "决策依据链", "风险等级", "状态迁移",
]

Vector = Union[Sequence[int], str]


def _normalize(v: Vector) -> List[int]:
    """把 tuple/list/str('⊖0⊕' 或 '-101' 或 '012') 归一为 [-1,0,1] 列表。"""
    if isinstance(v, str):
        v = v.strip()
        if len(v) != N_DIMS:
            raise ValueError(f"状态串长度必须为 {N_DIMS}，实际 {len(v)}: {v!r}")
        out = []
        for ch in v:
            if ch in "-1":
                out.append(-1)
            elif ch in "0":
                out.append(0)
            elif ch in "+1":
                out.append(1)
            elif ch == "\u2296":
                out.append(-1)
            elif ch == "\u2295":
                out.append(1)
            else:
                raise ValueError(f"非法三态字符 {ch!r}")
        return out
    out = []
    for x in v:
        x = int(x)
        if x not in (-1, 0, 1):
            raise ValueError(f"三态值必须 ∈ {{-1,0,1}}，实际 {x}")
        out.append(x)
    if len(out) != N_DIMS:
        raise ValueError(f"状态向量长度必须为 {N_DIMS}，实际 {len(out)}")
    return out


def vector_to_index(v: Vector) -> int:
    """idx = Σ(v_i + 1) * 3^(9-i)，∈ [0, 19682]。"""
    vec = _normalize(v)
    idx = 0
    for i, x in enumerate(vec):
        idx += (x + 1) * (3 ** (N_DIMS - 1 - i))
    return idx


def index_to_vector(idx: int) -> List[int]:
    """逆运算：idx → 九维三态向量。校验 0 ≤ idx ≤ 19682。"""
    idx = int(idx)
    if not (MIN_INDEX <= idx <= MAX_INDEX):
        raise ValueError(f"idx 必须 ∈ [{MIN_INDEX}, {MAX_INDEX}]，实际 {idx}")
    vec = []
    for i in range(N_DIMS):
        p = 3 ** (N_DIMS - 1 - i)
        t = idx // p
        vec.append(t - 1)
        idx -= t * p
    return vec


def balance(idx_or_vector) -> int:
    """平衡值 bal = idx - 9841 ∈ [-9841, +9841]，全零中心态 bal = 0。"""
    idx = vector_to_index(idx_or_vector) if not isinstance(idx_or_vector, int) else int(idx_or_vector)
    return idx - CENTER_INDEX


def vector_str(v: Vector) -> str:
    """渲染为符号串，如 '00⊖0⊖⊖⊖00'。"""
    return "".join(SYMBOLS[x] for x in _normalize(v))


def hamming(a: Vector, b: Vector) -> int:
    """两状态逐位不相等计数（决策轨迹中'跳变幅度'）。"""
    va, vb = _normalize(a), _normalize(b)
    return sum(1 for x, y in zip(va, vb) if x != y)


def semantic(v: Vector) -> str:
    """一句话语义：把 ⊖ 维度的名称列出来。"""
    vec = _normalize(v)
    minus = [DIM_FULL_NAMES[i] for i, x in enumerate(vec) if x == -1]
    plus = [DIM_FULL_NAMES[i] for i, x in enumerate(vec) if x == 1]
    parts = []
    if minus:
        parts.append("偏弱/不足：" + "、".join(minus))
    if plus:
        parts.append("偏强/超常：" + "、".join(plus))
    return "；".join(parts) if parts else "全部中和（转化中）"