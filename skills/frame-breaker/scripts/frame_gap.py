#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""frame_gap.py —— 框架突破度检测器（frame-breaker 技能 Step 4 验证）

作用：
  验证「重构问题」是否真的发生了，而不是换皮。比较原问题与新问题/方案在
  词面结构与概念上的差异，输出 0-100 的「框架突破度」：低于 60 说明新问题
  只是原问题的换皮，搜索空间没变，需要回 Step 2 再反演一轮。

原理：
  - 换皮式重构与原问题共享大量字符结构 → bigram 相似度高 → 突破度低；
  - 真重构会在「重构后的问题」里引入原问题没有的新实词 → 新颖词占比高 → 突破度高。
  - 新颖度刻意只看问题本身、不含方案：方案里的新词常是原目标域的换词
    （如"电机转速"之于"速度"），会污染"问题是否真的重构"的判断。

用法（纯标准库，离线可运行）：
  python3 frame_gap.py --original "如何让电梯更快" --reframed "如何让等待变得值得" \
      --solution "电梯里做内容幕间，管理乘客对时间的感知"
  python3 frame_gap.py --original "..." --reframed "..." --solution "..." --json
"""
import argparse
import json
import re
import sys

# 停用字/标点：不参与结构相似度计算。
# 停用词覆盖虚词、程度词与常见"操作/动作"词——过滤后剩下的是"实词"。
# 若重构只是换动词没换目标，过滤后新旧问题会只剩共享的对象实词，相似度就高。
STOP = set(
    "如何让的与和为在什么怎么办一个这样使把将对都更要用是吗呢？，。！、；：\"' "
    "怎样怎么把做搞弄跑走提升优化加快加速实现达到变得能够可以需要应该 "
    "给被从到向于之及或又再只还也都就才很最太挺快慢")
CN_RE = re.compile(r"[\u4e00-\u9fff]")


def clean_grams(s, n=2):
    """去掉非中文字符与停用字，返回连续 n-gram 集合。"""
    chars = [c for c in CN_RE.findall(s) if c not in STOP]
    if len(chars) < n:
        return set(chars) if chars else set()
    return {"".join(chars[i:i + n]) for i in range(len(chars) - n + 1)}


def jaccard(a, b):
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def main(argv):
    p = argparse.ArgumentParser(description="检测重构问题是否真的发生（框架突破度 0-100）")
    p.add_argument("--original", required=True, help="原问题")
    p.add_argument("--reframed", required=True, help="新问题（重构后）")
    p.add_argument("--solution", default="", help="新框架下的方案（仅供结果里展示，不参与评分）")
    p.add_argument("--json", action="store_true", help="输出 JSON")
    args = p.parse_args(argv)

    # 结构相似度（bigram Jaccard）
    g_orig = clean_grams(args.original)
    g_ref = clean_grams(args.reframed)
    sim = jaccard(g_orig, g_ref)

    # 新颖概念占比：只看「重构后的问题」本身相对原问题引入的实词。
    # 刻意不含方案——方案里的新词（如"电机转速"）可能仍是原目标域的换词，
    # 会污染"问题是否真的重构"的判断。
    novel = len(g_ref - g_orig) / len(g_ref) if g_ref else 0.0

    # 突破度：结构差异贡献 55%，新颖概念贡献 45%
    score = max(0, min(100, round(100 * (1 - sim) * 0.55 + 100 * novel * 0.45)))

    if score >= 60:
        verdict = "真重构（突破度达标）"
        advice = "框架确实变了：搜索空间已被扩展。进入落地步骤，并明确「解锁了什么原本不可能的」。"
    elif score >= 35:
        verdict = "边缘（可能还是换皮）"
        advice = ("新问题与旧框架结构相似度过高。挑 1-2 个未取反的核心假设再反演一轮，"
                  "并尝试引入一个真正无关的领域规则。")
    else:
        verdict = "换皮（未突破）"
        advice = ("新问题基本是原问题的同义改写，搜索空间没变。回到 Step 2：把最『理所当然』"
                  "的假设（通常是对象或目标维度）取反，建立反世界后再重构。")

    result = {
        "原问题": args.original,
        "新问题": args.reframed,
        "结构相似度": round(sim, 2),
        "新颖概念占比": round(novel, 2),
        "框架突破度": score,
        "判定": verdict,
        "建议": advice,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"框架突破度：{score} / 100 → {verdict}")
        print(f"结构相似度：{result['结构相似度']}（越高越像换皮）")
        print(f"新颖概念占比：{result['新颖概念占比']}")
        print(f"建议：{advice}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
