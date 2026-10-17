"""生成真实运行 Demo：用 agent-audit 引擎跑 4 个预设场景，写出可信演示文档。

运行：在 agent-audit-mcp 包目录下执行
  python gen_demo.py
输出：../agent-audit-skill/demo/DEMO.md
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.join(HERE, "..", "agent-audit-mcp")  # 原包目录
sys.path.insert(0, os.path.abspath(PKG))

from agent_audit.audit import audit_session  # noqa: E402

DIM_FULL = ["任务结构", "步骤意图", "上下文关联", "信息充足度", "步骤节奏",
            "权限边界", "决策依据链", "风险等级", "状态迁移"]


def load_steps(name):
    with open(os.path.join(PKG, "examples", name), encoding="utf-8") as f:
        data = json.load(f)
    return data.get("steps", [data]) if "steps" in data else [data]


def fmt_step(st):
    v = st["vector"]
    cells = " ".join(f"{DIM_FULL[i]}{('⊖' if x<0 else ('⊕' if x>0 else '0'))}" for i, x in enumerate(v))
    return (f"  - 步{st['step']} 向量 `{st['vector_str']}`  idx={st['idx']}  bal={st['bal']}\n"
            f"    维度：{cells}\n"
            f"    语义：{st['semantic']}\n"
            f"    红线：{st['flags'] or '无'}")


def main():
    out = []
    out.append("# agent-audit-mcp 真实运行 Demo\n")
    out.append("> 以下结果均由 `agent_audit.audit.audit_session` 在本地运行得出，非示意。\n")
    out.append("九维维度顺序：结构 / 功能 / 关系 / 属性 / 时间 / 情境 / 因果 / 价值 / 演化；"
               "每位 ⊖(−1) / 0 / ⊕(+1)。\n")
    out.append("红线维度：v6 越权(BLOCK) / v7 依据缺失(ALERT) / v8 高风险(ALERT)；"
               "相邻步 Hamming 距离 > 4 → WATCH。\n")

    scenarios = [
        ("scenario_a_ok.json", "场景A · 正常投顾建议", "OK"),
        ("scenario_b_alert.json", "场景B · 高风险全仓建议", "ALERT"),
        ("scenario_c_block.json", "场景C · 越权查询与荐股", "BLOCK"),
        ("scenario_d_watch.json", "场景D · 状态跳变逃逸", "WATCH"),
    ]
    for fname, title, expect in scenarios:
        steps = load_steps(fname)
        res = audit_session(steps, session_id=fname)
        badge = {
            "OK": "🟢 OK（无需干预）",
            "ALERT": "🟠 ALERT（合规复核）",
            "BLOCK": "🔴 BLOCK（人工介入/阻断）",
            "WATCH": "🟡 WATCH（人工复核）",
        }[res["verdict"]]
        out.append(f"\n## {title}\n")
        out.append(f"**判定：`{badge}`**  （预期 `{expect}`）\n")
        out.append("原因：" + "；".join(res["reasons"]) + "\n")
        rl = "无" if not res["red_lines"] else "；".join(
            f"步{r['step']}：{'、'.join(f[4:] for f in r['flags'])}" for r in res["red_lines"])
        jp = "无" if not res["jumps"] else "；".join(
            f"步{j['from']}→{j['to']} 距离{j['dist']}" for j in res["jumps"])
        out.append(f"步数：{res['state_count']} ｜ 红线：{rl} ｜ 跳变：{jp}\n")
        out.append("处置建议：\n")
        for a in res["actions"]:
            out.append(f"  - {a}\n")
        out.append("轨迹：\n")
        for st in res["trajectory"]:
            out.append(fmt_step(st) + "\n")

    target = os.path.join(HERE, "demo", "DEMO.md")
    with open(target, "w", encoding="utf-8") as f:
        f.write("\n".join(out))
    print("wrote", target, os.path.getsize(target), "bytes")


if __name__ == "__main__":
    main()
