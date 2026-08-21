#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""concept_blend.py —— 概念融合脚手架（frame-breaker 技能 Step 2/3 补充）

作用：
  基于 Fauconnier & Turner 的概念整合网络（输入空间→类属空间→合成空间→涌现结构），
  把两个概念/领域"融合"出新东西。关键不是"把 A 和 B 的词拼起来"，而是找出
  「只在融合空间里才成立、A 和 B 单独都没有」的涌现结构——那才是创造点。

融合三类（从浅到深）：
  1) 词面杂交 —— 表层：A 的名字 + B 的包装（最弱，多半是换皮）；
  2) 结构混合 —— 用 A 的结构装 B 的内容（或反之），保持关系、换实体；
  3) 涌现结构 —— 融合空间里才出现的新关系/新约束/新问题（最强，对应变革式创造）。

用法（纯标准库，离线可运行）：
  python3 concept_blend.py --a "电梯" --b "戏剧"
  python3 concept_blend.py --a "电梯" --b "戏剧" --depth 3 --json
  python3 concept_blend.py --a "医院" --b "游戏" --json
"""
import argparse
import json
import sys

# ---------------------------------------------------------------- 融合引导模板
# (类型, 定义, 引导问题)
BLEND_LEVELS = [
    ("词面杂交",
     "表层组合：A 的名字套 B 的包装（通常是换皮，用于先扫清浅层候选）",
     "把 A 与 B 直接并列/修饰/命名后得到什么？这个结果只是换皮吗？"),
    ("结构混合",
     "结构移植：把 A 的关系结构装进 B 的内容（或反之），保持关系、换实体",
     "A 里有哪些『关系』（不只名词）可以装进 B？B 里哪些实体能替换 A 里的角色？"),
    ("涌现结构",
     "合成空间里才出现的新关系/新约束/新问题——A 和 B 单独都没有",
     "在融合空间里，什么『新关系』诞生了？它带来了什么新约束或新问题？"),
]

# 通用"压缩关系"清单：概念融合常通过压缩关键关系产生新意义
VITAL_RELATIONS = [
    "因果", "时间", "空间", "意图", "角色", "部分-整体", "类比", "反事实", "身份", "变化",
]


def build(concept_a, concept_b, depth):
    lines = []
    lines.append(f"# 概念融合脚手架 · {concept_a} × {concept_b}\n")
    lines.append("> 目标：找出『只在融合空间成立』的涌现结构，而不是把两个词拼起来。"
                 "深度越深，越接近变革式创造。\n")

    # 输入空间
    lines.append("## 输入空间 A（已有要素/关系）")
    lines.append(f"- 对象/实体：{concept_a} 的关键实体有哪些？")
    lines.append(f"- 关系/机制：{concept_a} 内部有哪些关系（因果/依赖/时序…）？")
    lines.append("")
    lines.append("## 输入空间 B（已有要素/关系）")
    lines.append(f"- 对象/实体：{concept_b} 的关键实体有哪些？")
    lines.append(f"- 关系/机制：{concept_b} 内部有哪些关系？")
    lines.append("")

    # 类属空间
    lines.append("## 类属空间（A 与 B 的共享抽象结构）")
    lines.append("- 两者有没有同构的关系骨架？（如 A 的『等待』与 B 的『幕间』共享『被管理的空档』）")
    lines.append("")

    # 逐层融合
    lines.append("## 融合候选（按深度）")
    for i, (name, desc, q) in enumerate(BLEND_LEVELS[:depth], start=1):
        lines.append(f"### 层 {i} · {name}")
        lines.append(f"- {desc}")
        lines.append(f"- 引导：{q}")
        lines.append("")

    # 涌现结构检测
    lines.append("## 涌现结构检测（最关键一步）")
    lines.append(f"- 在融合空间里，什么『新关系』是 {concept_a} 单独没有、{concept_b} 单独也没有的？")
    lines.append(f"- 这个新关系改变了什么约束 / 解锁了什么原本不可能的？")
    lines.append("")
    lines.append("## 可尝试压缩的关系")
    lines.append("- " + " / ".join(VITAL_RELATIONS))
    lines.append("")
    lines.append("## 输出模板")
    lines.append("| 层 | 融合结果 | 是换皮吗 | 涌现的新关系/新约束 |")
    lines.append("|----|----------|----------|----------------------|")
    lines.append(f"| 1 词面杂交 | {concept_a}+{concept_b} 直接拼 | 多半是 | — |")
    return "\n".join(lines)


def main(argv):
    p = argparse.ArgumentParser(description="概念融合脚手架：两概念→融合候选+涌现结构检测")
    p.add_argument("--a", required=True, help="概念/领域 A")
    p.add_argument("--b", required=True, help="概念/领域 B")
    p.add_argument("--depth", type=int, default=3, choices=[1, 2, 3],
                   help="融合深度：1=词面杂交 2=结构混合 3=涌现结构（默认 3）")
    p.add_argument("--json", action="store_true", help="输出 JSON")
    args = p.parse_args(argv)

    levels = [l[0] for l in BLEND_LEVELS[:args.depth]]
    if args.json:
        print(json.dumps({
            "概念A": args.a,
            "概念B": args.b,
            "融合深度": args.depth,
            "融合层级": levels,
            "关键关系清单": VITAL_RELATIONS,
        }, ensure_ascii=False, indent=2))
    else:
        print(build(args.a, args.b, args.depth))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
