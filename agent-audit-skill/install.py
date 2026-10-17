"""一键把 agent-audit MCP 连接器注册进 WorkBuddy 的 ~/.workbuddy/mcp.json。

安全合并：不覆盖已有的其它连接器；写入前自动备份原文件。
用法：
    python install.py            # 注册（默认）
    python install.py --check    # 只体检环境与当前配置，不写入

跨平台：Windows / macOS / Linux 均可。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.abspath(os.path.join(HERE, "..", "agent-audit-mcp"))
MCP_JSON = os.path.expanduser(os.path.join("~", ".workbuddy", "mcp.json"))
SERVER_NAME = "agent-audit"


def mcp_version() -> str:
    """取 mcp 版本：优先 importlib.metadata，其次模块属性。"""
    try:
        from importlib.metadata import version
        return version("mcp")
    except Exception:
        import mcp
        return getattr(mcp, "__version__", "unknown")


def ensure_mcp() -> bool:
    """确认当前解释器能用 mcp；缺则尝试安装（best-effort）。"""
    try:
        import mcp  # noqa: F401
        print(f"[ok] mcp 已安装：{mcp_version()}")
        return True
    except Exception:
        print("[..] 未检测到 mcp，尝试安装 mcp>=2.0 ...")
        cmd = [sys.executable, "-m", "pip", "install", "mcp>=2.0"]
        try:
            subprocess.check_call(cmd)
            print("[ok] mcp 安装完成")
            return True
        except Exception as e:
            print(f"[warn] 自动安装失败：{e}")
            print("       请手动执行：python -m pip install 'mcp>=2.0'")
            return False


def build_entry() -> dict:
    return {
        "command": sys.executable,
        "args": ["-m", "agent_audit.server"],
        "cwd": PKG,
        "env": {"PYTHONIOENCODING": "utf-8"},
        "disabled": False,
    }


def load_config() -> dict:
    if not os.path.exists(MCP_JSON):
        return {"mcpServers": {}}
    with open(MCP_JSON, encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("mcpServers", {})
    return data


def check_only() -> None:
    print("== 环境体检 ==")
    print("python :", sys.executable)
    print("包目录 :", PKG, "(存在)" if os.path.isdir(PKG) else "(缺失!)")
    print("server :", os.path.join(PKG, "agent_audit", "server.py"),
          "(存在)" if os.path.isfile(os.path.join(PKG, "agent_audit", "server.py")) else "(缺失!)")
    try:
        import mcp  # noqa: F401
        print("mcp    : 已装", mcp_version())
    except Exception:
        print("mcp    : 未安装（将尝试安装）")
    cfg = load_config()
    print("mcp.json:", MCP_JSON, "(存在)" if os.path.exists(MCP_JSON) else "(将创建)")
    print("已有连接器:", list(cfg.get("mcpServers", {}).keys()))
    print("agent-audit 已注册:", SERVER_NAME in cfg.get("mcpServers", {}))


def register() -> None:
    ensure_mcp()
    cfg = load_config()
    if os.path.exists(MCP_JSON):
        bak = MCP_JSON + f".bak-{time.strftime('%Y%m%d-%H%M%S')}"
        shutil.copy2(MCP_JSON, bak)
        print(f"[ok] 已备份原配置 -> {bak}")
    cfg["mcpServers"][SERVER_NAME] = build_entry()
    os.makedirs(os.path.dirname(MCP_JSON), exist_ok=True)
    with open(MCP_JSON, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    print(f"[ok] 已写入连接器 '{SERVER_NAME}' -> {MCP_JSON}")
    print("\n下一步：打开 WorkBuddy「连接器」页，找到 agent-audit，点「Trust」启用。")
    print("然后对话中即可说：「审计这一步决策…」「审计这个会话轨迹…」")


def main() -> int:
    parser = argparse.ArgumentParser(description="注册 agent-audit MCP 连接器")
    parser.add_argument("--check", action="store_true", help="只体检，不写入")
    args = parser.parse_args()
    if args.check:
        check_only()
    else:
        register()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
