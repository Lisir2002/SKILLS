#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stereotype_scan.py —— 固化度检测器（creative-mind 技能 Step 4）

作用：
  扫描一段输出（文案/点子/标题/方案），量化它还剩多少「AI 套路 / 陈词滥调 /
  模板结构」——即固化度。模型默认输出概率最高、最安全、最套路的答案，
  本脚本把这些套路机械地抓出来，给一个 0-100 的固化度评分，供模型判断
  是否「还不够新」、要不要回炉重写。

用法（纯标准库，离线可运行）：
  python3 stereotype_scan.py --text "要检测的文本"
  python3 stereotype_scan.py --file out.md --type idea
  python3 stereotype_scan.py --text "..." --json   # 结构化输出

退出码：0 正常（固化度低=通过）；2 固化度高（≥60，建议回炉）。
"""
import argparse
import json
import re
import sys

# ---------------------------------------------------------------- 负面词库
# 词级：AI 高频套话 / 陈词滥调（中文为主，少量英文）
CLICHE_WORDS = [
    "综上所述", "总而言之", "总的来说", "值得注意的是", "需要注意的是",
    "不可否认", "毋庸置疑", "显而易见", "众所周知", "与此同时",
    "在此基础上", "由此可见", "综上所述", "一方面", "另一方面",
    "不仅", "而且", "与此同时", "除此之外",
    "随着", "的发展", "的不断深入", "的日益", "在当今", "在这个",
    "极大地", "显著地", "有效地", "极大地推动了", "助力", "赋能",
    "抓手", "闭环", "痛点", "链路", "颗粒度", "方法论", "底层逻辑",
    "顶层设计", "降维打击", "破圈", "出圈", "重构", "颠覆", "跃迁",
    "升维", "范式转移", "穿越周期", "第二曲线", "飞轮", "护城河",
    "点亮", "照亮", "唤醒", "种子", "桥梁", "灯塔",
    # 英文 AI 高频词
    "delve", "tapestry", "moreover", "furthermore", "it is important to note",
    "in conclusion", "embark on", "pivotal", "robust", "seamless",
]

# 结构级：机械句式 / 模板结构
PATTERNS = {
    "三点排比": r"(?:[，、；][^。！？]{2,12}，[^。！？]{2,12}){2}[^。！？]{2,12}[。！？]",
    "自问自答": r"[？?][^。！？]{0,8}是的|是否[^。！？]{2,20}[？?][^。！？]{2,20}答案",
    "平行否定": r"不再[^。！？]{2,15}而是|不是[^。！？]{2,15}而是|不要[^。！？]{2,15}要",
    "破折号滥用": r"—{2,}",
    "标题冒号": r"^.{2,20}[：:].{1,20}$",
    "'的'字连珠": r"[^\s。！？]{1,4}的[^\s。！？]{1,4}的[^\s。！？]{1,4}的[^\s。！？]{1,4}",
    "连接词过密": r"(因此|所以|然而|同时|其次|最后){3,}",
}

# 每种命中对评分的权重
WEIGHT = {
    "三点排比": 8, "自问自答": 6, "平行否定": 5, "破折号滥用": 4,
    "标题冒号": 3, "'的'字连珠": 3, "连接词过密": 4,
}

# 高风险模板（命中任意一个即强烈提示回炉）
HIGH_RISK = [
    "综上所述", "总而言之", "需要注意的是", "值得注意的是",
    "综上所述，", "不仅...而且", "在当今...的时代",
]


# ---------------------------------------------------------------- 检测
def scan(text, dtype="text"):
    """返回结构化检测结果。"""
    hits_words = []
    for w in CLICHE_WORDS:
        if w in text:
            hits_words.append(w)
    # 去重保序
    seen, words = set(), []
    for w in hits_words:
        if w not in seen:
            seen.add(w)
            words.append(w)

    hits_struct = {}
    for name, pat in PATTERNS.items():
        m = re.findall(pat, text, re.MULTILINE)
        if m:
            hits_struct[name] = len(m)

    # 风险模板
    high_risk = [r for r in HIGH_RISK if r in text]

    # 评分：词级 + 结构级 + 高风险
    score = min(30, len(words) * 3)
    for name, n in hits_struct.items():
        score += min(30, n * WEIGHT.get(name, 4))
    score += min(30, len(high_risk) * 12)

    # type 侧重：标题任务对「标题冒号/口号套话」更敏感
    if dtype == "title":
        if "标题冒号" in hits_struct:
            score += 5
        if any(w in text for w in ["点亮", "赋能", "破圈", "解锁"]):
            score += 8
    if dtype == "idea":
        if any(w in text for w in ["闭环", "痛点", "抓手", "底层逻辑"]):
            score += 8

    score = max(0, min(100, score))
    if score >= 60:
        verdict = "高固化（建议回炉重写）"
    elif score >= 35 or high_risk:
        verdict = "中固化（建议去套路后再交付）"
    else:
        verdict = "低固化（通过）"

    if score >= 60:
        advice = (f"命中 {len(words)} 个套话词、{len(hits_struct)} 类结构、"
                  f"{len(high_risk)} 个高风险模板，请回到发散步骤重想一轮。")
    elif high_risk:
        advice = "已命中高风险模板，建议优先替换这些句子后再交付。"
    else:
        advice = "可以交付；若想更出彩，可对剩余套路句再打磨。"

    return {
        "固化度评分": score,
        "判定": verdict,
        "词级命中": words,
        "词级命中数": len(words),
        "结构命中": hits_struct,
        "高风险模板": high_risk,
        "文本长度": len(text),
        "建议": advice,
    }


# ---------------------------------------------------------------- CLI
def main(argv):
    p = argparse.ArgumentParser(description="扫描 AI 套路/陈词滥调，输出固化度评分")
    p.add_argument("--text", help="要检测的文本")
    p.add_argument("--file", help="从文件读取文本")
    p.add_argument("--type", default="text",
                   choices=["text", "idea", "title", "plan"],
                   help="输出类型，影响侧重（默认 text）")
    p.add_argument("--json", action="store_true", help="输出 JSON")
    p.add_argument("--show-score", action="store_true",
                   help="只输出评分数字（供脚本取用）")
    p.add_argument("--fail-on-high", action="store_true",
                   help="高固化时退出码返回 2（供 CI 阻断；默认始终 0）")
    args = p.parse_args(argv)

    if args.text:
        text = args.text
    elif args.file:
        with open(args.file, encoding="utf-8") as f:
            text = f.read()
    else:
        p.error("需要 --text 或 --file")

    result = scan(text, args.type)

    if args.show_score:
        print(result["固化度评分"])
        return 2 if (args.fail_on_high and result["固化度评分"] >= 60) else 0

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"固化度评分：{result['固化度评分']} / 100 → {result['判定']}")
        print(f"词级命中（{result['词级命中数']}）：{'、'.join(result['词级命中']) or '无'}")
        print(f"结构命中：{json.dumps(result['结构命中'], ensure_ascii=False)}")
        print(f"高风险模板：{'、'.join(result['高风险模板']) or '无'}")
        print(f"建议：{result['建议']}")

    return 2 if (args.fail_on_high and result["固化度评分"] >= 60) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
