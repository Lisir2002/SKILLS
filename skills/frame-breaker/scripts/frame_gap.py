#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""frame_gap.py —— 框架突破度 + 意图保真度 检测器（frame-breaker 技能 Step 4 验证）

作用（双指标，缺一不可）：
  1. 「框架突破度」0-100：验证重构问题是否真的发生（不是换皮）。
     低于 60 说明新问题只是原问题的换皮，搜索空间没变，回 Step 2 再反演一轮。
  2. 「意图保真度」0-100（传入 --intent 时启用）：验证重构**没有脱离大意**。
     突破 ≠ 跑题：改路径可以，目的地（要解的大问题/不可违背的硬约束）不能丢。
     低于 60 说明为了"变"而丢掉了原问题真正要解决的意图，需要回 Step 1 重审大意。

原理：
  - 换皮式重构与原问题共享大量字符结构 → bigram 相似度高 → 突破度低；
  - 真重构会在「重构后的问题」里引入原问题没有的新实词 → 新颖词占比高 → 突破度高；
  - 保真度 = 重构后的问题里仍覆盖的「意图实词」占比（意图=大意/目标/硬约束，用 --intent 给出）。
  - 新颖度刻意只看问题本身、不含方案：方案里的新词常是原目标域的换词
    （如"电机转速"之于"速度"），会污染"问题是否真的重构"的判断。

用法（纯标准库，离线可运行）：
  python3 frame_gap.py --original "如何让电梯更快" --reframed "如何让等待变得值得" \
      --solution "电梯里做内容幕间，管理乘客对时间的感知"
  python3 frame_gap.py --original "如何让电梯更快" --reframed "如何让等待变得值得" \
      --intent "解决用户对电梯慢的抱怨" --solution "..." --json
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
    p.add_argument("--intent", default="",
                   help="原问题的『大意/目标/硬约束』（要解的大问题、不可违背的前提）。"
                        "传入后额外输出『意图保真度』，验证重构没跑题")
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

    # 意图保真度：重构后的问题里仍覆盖多少『意图实词』（--intent 给出的目标/硬约束）
    # 突破 ≠ 跑题：改路径可以，目的地不能丢。这是"重构不脱离大意"的机械检查。
    g_intent = clean_grams(args.intent) if args.intent else set()
    faithful = round(100 * len(g_intent & g_ref) / len(g_intent)) if g_intent else None

    if not args.intent:
        if score >= 60:
            verdict = "真重构（突破度达标）"
            advice = ("框架确实变了：搜索空间已被扩展。"
                      "建议再传 --intent 给『大意/目标/硬约束』，确认没跑题。")
        elif score >= 35:
            verdict = "边缘（可能还是换皮）"
            advice = ("新问题与旧框架结构相似度过高。挑 1-2 个未取反的核心假设再反演一轮，"
                      "并尝试引入一个真正无关的领域规则。")
        else:
            verdict = "换皮（未突破）"
            advice = ("新问题基本是原问题的同义改写，搜索空间没变。回到 Step 2：把最『理所当然』"
                      "的假设（通常是对象或目标维度）取反，建立反世界后再重构。")
    else:
        if faithful < 60:
            verdict = "跑题（离题重构）"
            advice = ("突破度虽然达标，但新问题丢掉了原问题的大意/硬约束——为『变』而变。"
                      "回到 Step 1 重审：原问题真正要解决的是什么？把意图锚回新问题再重构。")
        elif score >= 60:
            verdict = "真破框且不跑题（保真）"
            advice = ("框架真变了，且没有脱离大意：换的是路径，目的地还在。"
                      "进入落地步骤，并明确『解锁了什么原本不可能的』。")
        elif score >= 35:
            verdict = "破框不足（可能换皮）"
            advice = ("没有跑题，但突破度不够——新问题还是太贴着旧框架。挑核心假设再反演一轮，"
                      "或换一个真正无关的领域移植。")
        else:
            verdict = "换皮（未突破）"
            advice = "没有跑题，但新问题基本是原问题的同义改写。回 Step 2 建立反世界后再重构。"

    result = {
        "原问题": args.original,
        "新问题": args.reframed,
        "结构相似度": round(sim, 2),
        "新颖概念占比": round(novel, 2),
        "框架突破度": score,
        "判定": verdict,
        "建议": advice,
    }
    if faithful is not None:
        result["意图保真度"] = faithful

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"框架突破度：{score} / 100 → {verdict}")
        print(f"结构相似度：{result['结构相似度']}（越高越像换皮）")
        print(f"新颖概念占比：{result['新颖概念占比']}")
        if faithful is not None:
            print(f"意图保真度：{faithful} / 100（越低越跑题）")
        print(f"建议：{advice}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
