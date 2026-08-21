#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verify_claim.py —— 创造性断言验证脚手架（frame-breaker 技能 Step 5 落地）

作用：
  创造出来的新东西必须可验证、可溯源、不冒充事实。本脚本把一条断言/新想法
  放进三层验证管线，强制回答四个问题：
    1. 断言层级：它是【事实】/【合理推断】/【假设】？（校准弃权：证据不足就降级）
    2. 证伪清单：列出至少 2 条『能推翻它』的反例/反证据方向（FVA-RAG 的证伪检索思路，
       先找"杀死查询"而不是找支持）；
    3. 验证路径：如果我要验证它，具体做什么实验/查什么数据/看什么文献（可执行步骤）；
    4. 来源方向：涉及事实的部分，给『往哪个方向能找到依据』（文献/数据集/权威源），
       给不出方向的降级为假设，禁止冒充事实。

原则：
  - 溯因引擎：对每个新断言找『缺失前提』——它依赖什么未被证实的中间假设；
  - 反溯因：生成能击败它的竞争假设，能扛住才算立得住；
  - 校准弃权（OpenAI 2025）：证据不足时明确说"这是假设"，比硬拗成事实更可信。

用法（纯标准库，离线可运行）：
  python3 verify_claim.py --claim "电梯里放镜子能显著降低乘客等待焦虑" --domain "建筑心理学"
  python3 verify_claim.py --claim "..." --json
"""
import argparse
import json
import re
import sys

# 断言层级模板
LEVELS = [
    ("事实", "有直接可查依据，可引用到具体来源；否则不标这一层"),
    ("合理推断", "由已证实前提按逻辑推出；前提必须显式列出"),
    ("假设", "证据不足或无直接来源；必须显式标注，不得冒充事实"),
]

# 证伪方向模板（先找"杀死查询"，再找支持）
FALSIFY_PROMPTS = [
    "反例：历史上/数据里有没有一个场景，这个断言不成立甚至相反？",
    "边界：在什么条件下它失效？（人群/规模/时间/语境）",
    "竞争解释：有没有更简单的替代解释（奥卡姆剃刀）？",
    "逆向证据：去搜『反对这个说法/辟谣/例外』，而不是搜支持的",
]


def build(claim, domain):
    lines = []
    lines.append(f"# 断言验证脚手架 · 「{claim}」\n")
    if domain:
        lines.append(f"> 领域：{domain}\n")
    lines.append("## 0. 先做一件事：把断言拆成原子命题")
    lines.append(f"- 「{claim}」由哪些独立的小命题组成？（每一条单独验证，别一锅炖）")
    lines.append("")

    lines.append("## 1. 断言层级（校准弃权：证据不足就降级，禁止冒充事实）")
    for name, rule in LEVELS:
        lines.append(f"- **{name}**：{rule}")
    lines.append("")

    lines.append("## 2. 证伪清单（先找能推翻它的，再找支持的）")
    for i, q in enumerate(FALSIFY_PROMPTS, 1):
        lines.append(f"{i}. {q}")
    lines.append("")

    lines.append("## 3. 验证路径（可执行步骤：做什么能确证/证伪它）")
    lines.append("- 实验/测量：做什么观测或 A/B 测试？样本与指标是什么？")
    lines.append("- 数据/资料：查哪类数据、哪份报告、哪篇文献？")
    lines.append("- 复现：别人照这个步骤做，能得到同样的结论吗？")
    lines.append("")

    lines.append("## 4. 来源方向（往哪找依据；给不出方向的降级为假设）")
    lines.append("- 每个涉及『事实』的断言，写清：作者/机构/文献/数据集/官网的『方向』")
    lines.append(f"- {domain} 领域的权威综述/教科书/标准库是哪些？")
    lines.append("- 无法指出的 → 整条降级为『假设』并在输出里显式标注。")
    lines.append("")

    lines.append("## 5. 溯因检查（它依赖什么没被证实的中间前提？）")
    lines.append("- 为了让「{claim}」成立，中间还隐藏了哪些『未证实的因果/数值/前提』？")
    lines.append("")
    return "\n".join(lines)


def main(argv):
    p = argparse.ArgumentParser(description="创造性断言验证脚手架：层级标注+证伪+验证路径+来源方向")
    p.add_argument("--claim", required=True, help="要验证的断言/新想法")
    p.add_argument("--domain", default="", help="所属领域（用于来源方向提示）")
    p.add_argument("--json", action="store_true", help="输出 JSON")
    args = p.parse_args(argv)

    if args.json:
        print(json.dumps({
            "断言": args.claim,
            "领域": args.domain,
            "断言层级": [n for n, _ in LEVELS],
            "证伪方向": FALSIFY_PROMPTS,
            "原则": ["溯因找缺失前提", "反溯因生成击败假设", "校准弃权：证据不足标假设"],
        }, ensure_ascii=False, indent=2))
    else:
        print(build(args.claim, args.domain))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
