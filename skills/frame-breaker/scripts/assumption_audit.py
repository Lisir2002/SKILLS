#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""assumption_audit.py —— 隐含假设审计器（frame-breaker 技能 Step 1 & 3）

作用：
  1) --problem：输出「六维度假设挖掘脚手架」，把模型/用户对问题默认持有的
     隐含假设显式挖出来（对象/目标/约束/过程/评价/边界）。模型据此逐维度
     列出假设命题，并区分「题面给的」与「模型自己脑补的」（后者是破框目标）。
  2) --text：机械扫描一段方案文本里的「框架残留信号」——未审计假设的痕迹
     （必须/应该/通常/显然/唯一…等安全限定词），提示还有没被挖出的假设。
  3) --domains：列出域外移植可用的领域-规则库清单（详见 references/domains-zh.md）。

用法（纯标准库，离线可运行）：
  python3 assumption_audit.py --problem "电梯太慢怎么办"
  python3 assumption_audit.py --text "方案必须保持三位数，通常用户只看首页"
  python3 assumption_audit.py --domains
  python3 assumption_audit.py --problem "..." --json
"""
import argparse
import json
import re
import sys

# ---------------------------------------------------------------- 六维度
SIX_DIMS = [
    ("对象", "这个问题默认的『对象/主体/用户』是谁？假设了它是什么类型？",
     "对象换成别的物种/形态/尺度会怎样？"),
    ("目标", "默认的目标是什么？（更快/更多/更省…）这个目标本身合理吗？",
     "目标的相反面是什么？'最不'要什么？"),
    ("约束", "默认的约束是什么？哪些约束其实从未被题面声明？",
     "把约束取反/删除/极端化会怎样？"),
    ("过程", "默认的解决过程是什么？（运输/计算/传递…）有没有另一种过程能达到同一目的？",
     "如果过程完全不经过它，结果会如何？"),
    ("评价", "默认用什么标准评价成功？（时间/数量/成本…）换评价标准会改变什么？",
     "如果成功的新定义是失败，旧方案还成立吗？"),
    ("边界", "默认的解决范围边界在哪？（在这个系统内/这个公司内/这个学科内…）",
     "把边界扩大/缩小到极限会怎样？"),
]

# ---------------------------------------------------------------- 域外规则库
# 领域 -> (领域规则系统/世界观, 可用于重定义的示例)
DOMAINS = {
    "戏剧": ("悬念-期待管理：等待被设计成体验的一部分", "电梯等待→幕间"),
    "气象学": ("锋面相遇：两股力量交汇处产生新天气", "合并两个僵持的系统"),
    "蜂群": ("分布式决策：无中心，个体规则涌现整体行为", "去掉中心调度"),
    "植物学": ("向光性/感知缺水的主动适应", "从'被动响应'改'主动感知'"),
    "经济学": ("外部性：成本/收益不由交易双方承担", "把代价转给本来不承担者"),
    "语言学": ("词义随使用演化，旧词装新义", "给旧概念重新命名以解锁联想"),
    "医学": ("免疫记忆：先小剂量暴露再建立抵抗", "先小步试错再规模化"),
    "游戏设计": ("奖励反馈环：行为被即时反馈塑造", "改变反馈对象而非行为本身"),
    "军事侦察": ("情报不对称：信息差即战力", "把'猜'变成'直接显示'"),
    "生态学": ("生态位错开：竞争双方避开同一资源", "不抢同一批用户"),
    "宗教仪式": ("仪式感：重复动作承载意义", "把无意义操作变仪式"),
    "太空工程": ("冗余设计：关键部件必须有备份", "让最关键的环节可失败"),
    "侦探推理": ("不在场证明：怀疑'理所当然在场'的一方", "质疑默认在场的参与者"),
    "金融期权": ("对冲：用相反头寸锁住风险", "不消除风险而是对冲"),
    "烹饪": ("火候层次：外层与内层不同熟度", "同一产品分层次给不同人群"),
    "心理学": ("锚定效应：先给参照再被参照绑架", "重置参照系本身"),
    "科幻设定": ("时间循环/平行宇宙：改变因果结构", "不改变事件，改变时间结构"),
    "考古学": ("断代：从碎片重推完整系统", "从碎片推断原框架"),
    "体育战术": ("攻防转换：防守即进攻的起点", "把'补短板'改'用短板'"),
    "音乐": ("和声解决：不和谐后回到和谐才动人", "先制造不适再解决"),
}

# 框架残留信号词（未审计假设的痕迹）
ASSUMPTION_WORDS = [
    "必须", "应该", "只能", "唯一", "通常", "显然", "自然", "正常", "当然",
    "理所当然", "不言而喻", "无非", "就是", "本来", "一般", "常见", "标准",
    "需要保证", "必须保持", "通常认为", "理所当然地",
]


# ---------------------------------------------------------------- 功能
def audit_problem(problem):
    lines = []
    lines.append(f"# 假设审计脚手架 · {problem}\n")
    lines.append("> 对每个维度：写成一个明确的假设命题，并标注【题面】还是【模型脑补】。"
                 "『脑补』项是主要破框目标。\n")
    for dim, q, inv in SIX_DIMS:
        lines.append(f"## {dim}")
        lines.append(f"- 挖：{q}")
        lines.append(f"- 反：{inv}")
        lines.append("")
    lines.append("## 输出模板")
    lines.append("| 维度 | 隐含假设（命题） | 来源 | 取反后的反世界 |")
    lines.append("|------|------------------|------|----------------|")
    lines.append("| 对象 | 例：结果是正数 | 模型脑补 | 负数也允许 |")
    return "\n".join(lines)


def scan_text(text):
    hits = []
    for w in ASSUMPTION_WORDS:
        if w in text:
            hits.append(w)
    # 去重保序
    seen, words = set(), []
    for w in hits:
        if w not in seen:
            seen.add(w)
            words.append(w)
    return words


def list_domains():
    lines = ["# 域外移植 · 领域规则库（20+）", ""]
    lines.append("> 从无关领域借『规则系统/世界观』来重定义本题（不是借点子，是借表征框架）。"
                 "详细版见 references/domains-zh.md。\n")
    lines.append("| 领域 | 规则系统/世界观 | 可参考用法 |")
    lines.append("|------|------------------|------------|")
    for name, (rule, use) in DOMAINS.items():
        lines.append(f"| {name} | {rule} | {use} |")
    return "\n".join(lines)


# ---------------------------------------------------------------- CLI
def main(argv):
    p = argparse.ArgumentParser(description="隐含假设审计：挖六维假设/扫框架残留/列域外规则库")
    p.add_argument("--problem", help="要挖掘隐含假设的问题")
    p.add_argument("--text", help="扫描文本里的框架残留信号（未审计假设的痕迹）")
    p.add_argument("--domains", action="store_true", help="列出域外移植领域规则库")
    p.add_argument("--json", action="store_true", help="输出 JSON")
    args = p.parse_args(argv)

    if args.domains:
        if args.json:
            print(json.dumps({"domains": list(DOMAINS.keys())}, ensure_ascii=False, indent=2))
        else:
            print(list_domains())
        return 0

    if args.problem:
        if args.json:
            print(json.dumps({"problem": args.problem, "dims": SIX_DIMS}, ensure_ascii=False, indent=2))
        else:
            print(audit_problem(args.problem))
        return 0

    if args.text:
        words = scan_text(args.text)
        result = {
            "框架残留信号": words,
            "命中数": len(words),
            "提示": (f"文本里仍含 {len(words)} 个假设性措辞，说明可能有未审计的隐含假设，"
                     f"请先用 --problem 把假设挖干净。" if words else "未发现明显框架残留。"),
        }
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"框架残留信号（{len(words)}）：{'、'.join(words) or '无'}")
            print(result["提示"])
        return 0

    p.error("需要 --problem / --text / --domains 之一")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
