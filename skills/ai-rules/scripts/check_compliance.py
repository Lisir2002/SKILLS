#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai-rules · 合规自检器（check_compliance.py）
============================================
对 AI 的过程/输出做机械合规检查（Policy-as-Prompt 思路）：
命中禁止项、无证据断言、引用缺失、疑似超范围、证据缺失等。

用法：
  python3 check_compliance.py --json rules.json --text "交付说明文本..."
  python3 check_compliance.py --json rules.json --text "..." --evidence ./test_output.log
  python3 check_compliance.py --json rules.json --text "..." --scope file_a.py file_b.py

--text    : 待检查的 AI 输出/过程记录（可选，留空则只做证据/范围检查）
--evidence: 声称已完成的证据路径（文件或目录，可多个）
--scope   : 允许动用的文件/资源清单（用于超范围检查）

退出码：0=通过  1=警告(可恢复)  2=阻塞(需人裁决)
"""

import argparse
import json
import os
import re
import sys

# 无证据断言词：出现即怀疑「我把我认为当结果」（对应 R1/G5/A1）
UNVERIFIED_CLAIMS = [
    "应该能", "应该可以", "应该没问题", "大概没问题", "我觉得可以",
    "我觉得没问题", "肯定没问题", "肯定能", "绝对没问题", "放心",
    "肯定可以", "没问题了", "肯定能跑", "看起来没问题",
]

# 引用缺失检测：提到来源但没给可核验引用
CITE_MARKERS = ["根据", "来源", "引用", "参考", "研究表明", "统计显示", "官方文档", "资料显示"]
URL_RE = re.compile(r"https?://[^\s）)\]]+")

# 待办/推诿痕迹：声称完成却留下这些词 = 尚未闭环
UNFINISHED_WORDS = ["未完待续", "稍后补充", "待补", "TODO", "此处省略", "内容待填"]


def check_text(rules, text):
    """对输出文本做机械合规检查。"""
    hits = []
    text = text or ""

    # 1) 禁止项关键词扫描
    for r in rules:
        for f in r.get("forbid", []) or []:
            kw = f.strip().lstrip("不").strip()  # 去掉"不"字，命中表述即告警
            if len(kw) < 3:
                continue
            for seg in (kw[:8], kw[:12]):  # 前缀命中，容忍表述差异
                if seg and seg in text:
                    hits.append(f"[禁止项] 文本疑似违反 {r['id']}「{r['title']}」: 出现「{f}」相关表述")
                    break

    # 2) 无证据断言
    for w in UNVERIFIED_CLAIMS:
        if w in text:
            hits.append(f"[无证据断言] 出现「{w}」，缺少验证证据（G5/R1）")

    # 3) 引用缺失
    for m in CITE_MARKERS:
        if m in text and not URL_RE.search(text):
            hits.append(f"[引用缺失] 文本提到「{m}」但未给出可核验来源链接（R1/G5）")
            break

    # 4) 未完成痕迹
    for w in UNFINISHED_WORDS:
        if w in text:
            hits.append(f"[未完成痕迹] 出现「{w}」，声称完成但留有占位（R5）")

    # 5) 情绪化/模糊交付（G4 目标驱动弱化信号）
    fuzzy = ["尽力", "尽可能", "试着", "尝试完成", "尽量"]
    for w in fuzzy:
        if w in text:
            hits.append(f"[目标模糊] 出现「{w}」，建议改为可验证的成功标准（G4）")

    return hits


def check_scope(text, scope_files):
    """超范围检查：文本提到的文件若不在允许清单内则告警。"""
    hits = []
    if not scope_files or not text:
        return hits
    found = re.findall(r"[\w./-]+\.(?:py|js|ts|java|go|rs|c|cpp|md|json|yaml|yml|txt|html|css|sh|sql)", text)
    allowed = set(os.path.basename(s) for s in scope_files)
    for fname in set(found):
        if fname not in allowed:
            hits.append(f"[疑似超范围] 文本涉及未授权文件「{fname}」，不在 --scope 允许清单（R4/G3）")
    return hits


def check_evidence(evidence_paths):
    """证据核验：声称的验证产物是否存在。"""
    hits = []
    for p in evidence_paths or []:
        if not os.path.exists(p):
            hits.append(f"[证据缺失] 声明的证据路径不存在: {p}（G5）")
        else:
            if os.path.isfile(p) and os.path.getsize(p) == 0:
                hits.append(f"[证据为空] 证据文件为空: {p}（G5）")
    return hits


def main():
    ap = argparse.ArgumentParser(description="ai-rules 合规自检器")
    ap.add_argument("--json", required=True, help="规矩清单 JSON（generate_rules.py 输出）")
    ap.add_argument("--text", help="待检查的 AI 输出/过程记录文本")
    ap.add_argument("--evidence", nargs="*", default=[], help="声称的验证证据路径")
    ap.add_argument("--scope", nargs="*", default=[], help="允许动用的文件/资源清单")
    args = ap.parse_args()

    with open(args.json, encoding="utf-8") as f:
        book = json.load(f)
    rules = book.get("rules", [])

    hits = []
    hits += check_text(rules, args.text)
    hits += check_scope(args.text, args.scope)
    hits += check_evidence(args.evidence)

    # 分级：禁止项/证据缺失 -> 🚧 阻塞；无证据断言/引用缺失/超范围 -> ⚠️ 警告
    blocks = [h for h in hits if h.startswith("[禁止项]") or h.startswith("[证据缺失]")]
    warns = [h for h in hits if h not in blocks]

    print("=" * 60)
    print("ai-rules 合规自检报告")
    print("=" * 60)
    if args.text:
        print(f"检查文本 : {args.text[:60]}…" if len(args.text) > 60 else f"检查文本 : {args.text}")
    print(f"检查结果 : {len(hits)} 项（🚧 阻塞 {len(blocks)} / ⚠️ 警告 {len(warns)}）\n")

    for h in blocks:
        print(f"  🚧 {h}")
    for h in warns:
        print(f"  ⚠️ {h}")

    if not hits:
        print("  ✅ 未发现违规项。")

    if blocks:
        print("\n结论: 🚧 存在阻塞项，需要人裁决或修订后重新交付。")
        return 2
    if warns:
        print("\n结论: ⚠️ 存在可恢复警告，修正后即可交付。")
        return 1
    print("\n结论: ✅ 合规通过。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
