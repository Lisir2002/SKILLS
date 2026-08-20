#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai-rules · 逐条确认器（confirm_rules.py）
==========================================
对 generate_rules.py 生成的规矩清单做「逐条自我确认」（Agent Charters 模式）：
检查歧义、自相矛盾、不可执行项，输出 ✅ / ⚠️ / 🚧 三级状态。

用法：
  python3 confirm_rules.py --json rules.json
  python3 confirm_rules.py --json rules.json --task "给管理员加批量导入" --goal "导入 1 万行 3 秒内完成"
  # --task/--goal 用于把任务目标注入检查上下文（可选）

退出码：0=全部通过  1=有警告(可修订后继续)  2=有阻塞(必须修订)
"""

import argparse
import json
import re
import sys

# 歧义词表：出现即认为该条规矩「不可精确执行」，需要量化或明确边界
AMBIGUOUS_WORDS = [
    "尽量", "适当", "尽可能", "酌情", "看情况", "大概", "差不多",
    "相关文件", "相关部分", "相关模块", "合适", "合理", "必要时",
    "优化一下", "尽快", "及时", "多次", "一段时间",
]

# 合理但需要「给默认值」的词（归为警告而非阻塞）
SOFT_WORDS = ["按需", "可以", "建议", "最好"]

# 规则自检：必须/禁止 文本中保留的「程度副词」会被标记
_DEGREE_RE = re.compile(r"(非常|极其|特别|相当|彻底|完全|务必|一定|绝对)")


def analyze_rules(book):
    """对每条规矩做四类检查，返回逐条结果与汇总。"""
    results = []
    rules = book.get("rules", [])
    seen_ids = set()
    must_texts = []
    forbid_texts = []

    for idx, r in enumerate(rules):
        rid = r.get("id", f"#{idx}")
        issues = []

        # 1) 歧义检查
        must = r.get("must", []) or []
        forbid = r.get("forbid", []) or []
        why = r.get("why", "") or ""
        verify = r.get("verify", "") or ""
        text = " ".join(must + forbid) + " " + why + " " + verify
        hit = [w for w in AMBIGUOUS_WORDS if w in text]
        soft = [w for w in SOFT_WORDS if w in text]
        if hit:
            issues.append(f"含歧义词 {hit}，无法精确执行，请量化或明确边界")
        if soft:
            issues.append(f"含模糊词 {soft}，建议给出默认值/量化口径")

        # 2) 空规则检查
        if not must and not forbid:
            issues.append("must 与 forbid 均为空，规则无实质内容")

        # 3) 无验证标准检查（对应 G4/G5：不可验证 = 不可执行）
        if not verify:
            issues.append("缺少「验证」标准，无法判断是否完成")

        # 4) 程度副词检查（易导致过度执行）
        deg = _DEGREE_RE.findall(text)
        if deg:
            issues.append(f"含程度副词 {deg}，可能被过度执行，建议改为具体标准")

        # 5) id 重复检查
        dup = rid in seen_ids
        seen_ids.add(rid)
        if dup:
            issues.append(f"id 重复: {rid}")

        # 汇总状态
        if issues:
            level = "⚠️ 需修订" if any("程度副词" in i or "模糊词" in i for i in issues) else "🚧 阻塞"
            # 空规则/无验证/歧义词 -> 阻塞；其余 -> 警告
            if any(k in i for i in issues for k in ("歧义词", "空规则", "无验证", "id 重复")):
                level = "🚧 阻塞"
        else:
            level = "✅ 通过"

        must_texts.extend(must)
        forbid_texts.extend(forbid)

        results.append({
            "id": rid,
            "title": r.get("title", ""),
            "level": level,
            "issues": issues,
            "text": text[:120],
        })

    # 6) 跨规则矛盾检查（must 与 forbid 内容互相抵消）
    conflict_hints = []
    for f in forbid_texts:
        # 找与 forbid 语义重叠的 must（简单字符串/关键词重叠启发式）
        for m in must_texts:
            if len(f) >= 4 and (f in m or m in f):
                conflict_hints.append(f"must「{m[:30]}」与 forbid「{f[:30]}」可能矛盾")
    for hint in conflict_hints[:5]:
        pass  # 记入报告

    # 汇总
    n_pass = sum(1 for r in results if r["level"] == "✅ 通过")
    n_warn = sum(1 for r in results if r["level"] == "⚠️ 需修订")
    n_block = sum(1 for r in results if r["level"] == "🚧 阻塞")

    return {
        "total": len(results),
        "pass": n_pass,
        "warn": n_warn,
        "block": n_block,
        "conflicts": conflict_hints[:5],
        "items": results,
    }


def main():
    ap = argparse.ArgumentParser(description="ai-rules 逐条确认器")
    ap.add_argument("--json", required=True, help="generate_rules.py 输出的规矩 JSON")
    ap.add_argument("--task", help="任务描述（注入检查上下文，可选）")
    ap.add_argument("--goal", help="任务成功目标（可选，用于核对可验证性）")
    args = ap.parse_args()

    with open(args.json, encoding="utf-8") as f:
        book = json.load(f)

    report = analyze_rules(book)

    print("=" * 60)
    print("ai-rules 逐条确认报告")
    print("=" * 60)
    if args.task:
        print(f"任务 : {args.task}")
    if args.goal:
        print(f"目标 : {args.goal}")
    print(f"规矩 : {report['total']} 条  "
          f"✅ {report['pass']}  ⚠️ {report['warn']}  🚧 {report['block']}\n")

    for it in report["items"]:
        print(f"{it['level']}  {it['id']} {it['title']}")
        for i in it["issues"]:
            print(f"        - {i}")

    if report["conflicts"]:
        print("\n[跨规则疑似矛盾]")
        for c in report["conflicts"]:
            print(f"  - {c}")

    if report["block"]:
        print("\n结论: 🚧 存在阻塞项，请修订后重新确认。")
        return 2
    if report["warn"]:
        print("\n结论: ⚠️ 存在可修订项，建议修订后执行；也可在用户确认下继续。")
        return 1
    print("\n结论: ✅ 规矩清单可执行，逐条确认通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
