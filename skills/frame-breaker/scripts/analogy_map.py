#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""analogy_map.py —— 类比映射脚手架（frame-breaker 技能 Step 3 补充）

作用：
  基于 Gentner 的结构映射理论（SMT）：类比的价值在『关系结构』对齐，而不在表面相似。
  给出源域（无关领域）与目标域（本题），本脚本产出：
    1) 源域的关系结构（把『名词』换成『关系谓词』）；
    2) 目标域的对应物候选（保持关系、换实体）；
    3) 可移植关系清单（Step 3 域外移植的原料）；
    4) 表面差异提示（防止被『看着像』误导，只做名词级搬运=换皮）。

用法（纯标准库，离线可运行）：
  python3 analogy_map.py --source "气象锋面" --target "两个僵持的部门"
  python3 analogy_map.py --source "戏剧的悬念" --target "电梯等待" --json
"""
import argparse
import json
import sys

# ---------------------------------------------------------------- 结构映射引导
# 常见的关系谓词骨架：类比时优先找『关系』而不是『对象』
RELATION_SKELETONS = [
    ("支配/控制", "谁控制谁？A 支配 B，还是互相制约？"),
    ("依赖/因果", "谁依赖谁？原因在哪个实体身上？"),
    ("竞争/对抗", "两股力量是否在对立？交汇处发生了什么？"),
    ("交换/传递", "信息/资源/能量怎么流动？有没有中转站？"),
    ("反馈/循环", "有没有自我强化的回路？延迟在哪里？"),
    ("边界/隔断", "内外怎么划界？边界被打破会怎样？"),
    ("时序/等待", "先后顺序是什么？等待在哪一环？"),
    ("角色/职能", "每个实体扮演什么职能？职能可以互换吗？"),
]

# 表面差异提示词（SMT：表面相似是陷阱）
SURFACE_TRAP_WORDS = [
    "形状像", "名字像", "颜色像", "尺寸像", "同类物品",
]


def build(source, target):
    lines = []
    lines.append(f"# 类比映射脚手架 · {source} → {target}\n")
    lines.append("> 原则（结构映射理论）：对齐『关系结构』，不是对齐表面特征。"
                 "只因为『名字像』而移植 = 换皮。\n")

    lines.append("## 1. 源域关系结构（把名词翻译成关系谓词）")
    lines.append(f"- 列出 {source} 里的关键实体；")
    lines.append(f"- 把它们之间的『关系』写成谓词（谁支配谁/谁依赖谁/什么在循环…），不要只写名词。")
    lines.append("")
    lines.append("## 2. 目标域对应物候选（保持关系、换实体）")
    lines.append(f"- 在 {target} 里找出能扮演同一种『关系角色』的实体；")
    lines.append(f"- 验证：把源域的关系骨架套上去后，{target} 里哪些『原本不可能』的关系出现了？")
    lines.append("")
    lines.append("## 3. 可移植关系清单（Step 3 移植的原料）")
    lines.append(f"- 从 {source} 抽出 1-3 条『关系规则』（不是点子），")
    lines.append(f"- 用它重定义 {target} 的问题表述。")
    lines.append("")
    lines.append("## 4. 表面差异检查（防止换皮）")
    lines.append(f"- {source} 与 {target} 表面哪里不同？（实体/尺度过完全不一样，才说明真的是结构移植，不是抄名词）")
    lines.append("")
    lines.append("## 关系谓词骨架（可对齐的候选）")
    for name, q in RELATION_SKELETONS:
        lines.append(f"- **{name}**：{q}")
    lines.append("")
    lines.append("## 输出模板")
    lines.append("| 源域关系（谓词） | 目标域对应物 | 移植后产生的新框架 |")
    lines.append("|------------------|--------------|--------------------|")
    lines.append(f"| {source} 的『支配关系』 | {target} 的『____』 | 问题从『____』变成『____』 |")
    return "\n".join(lines)


def main(argv):
    p = argparse.ArgumentParser(description="类比映射脚手架：源域关系结构→目标域移植")
    p.add_argument("--source", required=True, help="源域（无关领域）")
    p.add_argument("--target", required=True, help="目标域（本题）")
    p.add_argument("--json", action="store_true", help="输出 JSON")
    args = p.parse_args(argv)

    if args.json:
        print(json.dumps({
            "源域": args.source,
            "目标域": args.target,
            "关系骨架": [n for n, _ in RELATION_SKELETONS],
            "原则": "对齐关系结构，不对齐表面特征（SMT）",
        }, ensure_ascii=False, indent=2))
    else:
        print(build(args.source, args.target))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
