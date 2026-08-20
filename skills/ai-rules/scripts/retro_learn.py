#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai-rules · 复盘学习器（retro_learn.py）
========================================
任务结束后（尤其失败/返工）沉淀教训：新增实战规矩、统计违规、记录复盘日志，
让规矩库随实战进化（SafeHarbor/AGrail 的自进化记忆 + aashari retro 思路）。

用法：
  python3 retro_learn.py \
      --note "导入功能超时：没先确认数据量级就用了 O(n^2) 方案" \
      --violated G1 G4 \
      --rule "涉及大数据量先确认量级与时间复杂度" \
      --why "O(n^2) 在 10 万行时不可用" \
      --rulebook ../memory/rulebook.json

退出码：0=成功
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone


def load_rulebook(path):
    """加载规矩库；不存在则初始化。"""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {
        "skill": "ai-rules",
        "version": 1,
        "updated_at": None,
        "rules": [],       # 实战沉淀规矩（第 2 层通用风格）
        "retro_log": [],   # 复盘日志
    }


def save_rulebook(path, book):
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    book["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(book, f, ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser(description="ai-rules 复盘学习器：沉淀实战规矩")
    ap.add_argument("--note", required=True, help="复盘记录（一句话描述发生了什么、教训是什么）")
    ap.add_argument("--violated", nargs="*", default=[], help="本次被违反的规矩 id（如 G1 G4 R1）")
    ap.add_argument("--rule", help="建议新增的实战规矩文本（可选）")
    ap.add_argument("--why", help="新增规矩的「为什么」（可选，reason-based 必备）")
    ap.add_argument("--rulebook", default="memory/rulebook.json",
                    help="规矩库 JSON 路径（默认 ./memory/rulebook.json）")
    args = ap.parse_args()

    book = load_rulebook(args.rulebook)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1) 违规计数
    for rid in args.violated:
        for r in book["rules"]:
            if r["id"] == rid:
                r["violation_count"] = r.get("violation_count", 0) + 1

    # 2) 沉淀新规矩（自动编号 L<n>，标记 source=retro）
    if args.rule and args.why:
        n = len(book["rules"]) + 1
        new_rule = {
            "id": f"L{n}",
            "layer": 2,
            "type": "lesson",
            "title": f"实战教训 {n}",
            "must": [args.rule],
            "why": args.why or "(来自复盘，未记录原因——建议补上「为什么」)",
            "verify": "在本规则适用场景下按此执行，并在交付中说明。",
            "source": "retro",
            "violation_count": 0,
        }
        # 去重：同 must 文本已存在则不重复添加
        if not any(r.get("must") == new_rule["must"] for r in book["rules"]):
            book["rules"].append(new_rule)
            print(f"[retro_learn] 已新增实战规矩 {new_rule['id']}: {args.rule}")

    # 3) 复盘日志
    book["retro_log"].append({
        "time": now,
        "note": args.note,
        "violated": args.violated,
        "new_rule": args.rule,
        "why": args.why,
    })

    save_rulebook(args.rulebook, book)

    print(f"[retro_learn] 复盘已记录: {args.note}")
    if args.violated:
        print(f"[retro_learn] 违规统计: {', '.join(args.violated)} 计数 +1")
    print(f"[retro_learn] 规矩库已更新: {os.path.abspath(args.rulebook)}")
    print(f"[retro_learn] 当前实战规矩 {len(book['rules'])} 条, 复盘记录 {len(book['retro_log'])} 条")
    return 0


if __name__ == "__main__":
    sys.exit(main())
