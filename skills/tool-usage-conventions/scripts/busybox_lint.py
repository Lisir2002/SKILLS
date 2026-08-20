#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
busybox_lint.py · BusyBox 命令兼容性自检器
==========================================
静态检查将要执行的 shell 命令（或脚本文件）是否含 GNU 专属语法与无界循环，
避免在 Alpine/BusyBox 环境下"解析即报错、重试又失败"。

用法：
  python3 busybox_lint.py --cmd 'grep -P "\\d+" file'
  python3 busybox_lint.py --file build.sh
  cat script.sh | python3 busybox_lint.py
  python3 busybox_lint.py --cmd '...' --json      # JSON 输出

退出码：0=无问题  1=发现兼容性问题
"""

import argparse
import json
import re
import sys

# (检查名, 匹配模式, 修正建议)
# 模式均为"命中即告警"——宁可多报提醒修正，不可漏报导致运行时报错。
CHECKS = [
    (
        "gnu-netcat-q",
        re.compile(r"\bnc\s+-q\s+\d+"),
        "nc -q N 是 GNU netcat「EOF 后等待」扩展，BusyBox 不支持；"
        "改用 nc -w N host port，或 wget -T 2 -O /dev/null URL / curl --connect-timeout 2 -s",
    ),
    (
        "grep-perl-regex",
        re.compile(r"\bgrep\b[^|;]*\s-P(?:\s|$)"),
        "grep -P 是 GNU 扩展，BusyBox 无 -P；改用 grep -E 与 POSIX 类",
    ),
    (
        "grep-backslash-d-s",
        re.compile(r"\bgrep\b[^\n|;]*\\[ds](?![a-zA-Z])"),
        "grep 不认 \\d / \\s；改用 [0-9] / [[:space:]]，"
        "或 LC_ALL=C grep '[^ -~]' 做字节级非 ASCII 检测",
    ),
    (
        "awk-unicode-hex",
        re.compile(r"\bawk\b[^\n]*\\x\{[0-9a-fA-F]+\}"),
        "awk \\x{...} 是 gawk Unicode 语法，busybox awk 不支持；改用 LC_ALL=C 字节判断",
    ),
    (
        "date-gnu-d",
        re.compile(r"\bdate\s+-d\b"),
        "date -d '...' 是 GNU 解析（-d @epoch 部分支持）；跨平台优先 date +%s / date -u +%FT%TZ",
    ),
    (
        "head-neg-n",
        re.compile(r"\bhead\s+-n\s+-\d+"),
        "head -n -N 负数写法 BusyBox 部分版本不支持；改用 awk/sed 替代",
    ),
    (
        "tail-neg-n",
        re.compile(r"\btail\s+-n\s+\+\d+"),
        "tail -n +N 负数写法 BusyBox 部分版本不支持；改用 awk/sed 替代",
    ),
    (
        "unbounded-while",
        re.compile(r"(?:\bwhile\s+(?:true|1|\[[^\]]*\])\b|\bwhile\s*:)"),
        "无界循环 while true / while : / while [ 1 ] 禁止：会无限刷屏空耗 CPU；"
        "改用有限次数（for i in 1 2 3 4 5 / seq）+ sleep + 明确退出条件",
    ),
    (
        "unbounded-until",
        re.compile(r"\buntil\s+false\b"),
        "无界循环 until false 禁止；改用有限次数 + 明确退出条件，并在超时前结束",
    ),
    (
        "unbounded-for-c",
        re.compile(r"\bfor\s*\(\s*\("),
        "无界循环 for ((;;)) 禁止；改用 for i in 1 2 3 4 5 / seq",
    ),
]


def lint_line(line):
    """对一行命令做全部检查，返回命中列表 [(check_name, advice)]。"""
    hits = []
    for name, pattern, advice in CHECKS:
        if pattern.search(line):
            hits.append((name, advice))
    return hits


def main():
    ap = argparse.ArgumentParser(description="busybox_lint：静态检查 shell 命令的 BusyBox 兼容性")
    src = ap.add_mutually_exclusive_group(required=False)
    src.add_argument("--cmd", help="单条命令字符串")
    src.add_argument("--file", help="脚本文件路径（逐行检查）")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    args = ap.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    elif args.cmd:
        lines = [args.cmd]
    else:
        lines = sys.stdin.readlines()

    problems = []
    for idx, line in enumerate(lines, 1):
        for name, advice in lint_line(line):
            problems.append({
                "line": idx,
                "check": name,
                "advice": advice,
                "text": line.strip()[:120],
            })

    if args.json:
        print(json.dumps({"ok": not problems, "problems": problems},
                         ensure_ascii=False, indent=2))
    else:
        if problems:
            print(f"发现 {len(problems)} 个 BusyBox 兼容性问题：")
            for p in problems:
                print(f"  第 {p['line']} 行 [{p['check']}]: {p['text']}")
                print(f"      → {p['advice']}")
            print("\n结论: 需修正后再执行（对照 container-compat.md 的 GNU→BusyBox 表）")
        else:
            print("未发现 BusyBox 兼容性问题（无 GNU 专属语法、无无界循环）。")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
