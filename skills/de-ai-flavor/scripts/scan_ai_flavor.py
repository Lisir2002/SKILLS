#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scan_ai_flavor.py — 中文文本"AI味"扫描器（词级 + 结构级）
============================================================
扫描两类 AI 标志：
  1. 词级（ai_markers）    ：套话、模板腔、机械过渡词
  2. 结构级（structural）  ：平行否定、三点排比、自问自答、破折号滥用、短句结尾
并给出句式节奏指标（句子长度方差 = 突发度的代理指标）与总体评分。

用途：de-ai-flavor 技能的量化验证工具，改写前后各跑一次对比效果。

用法：
    python3 scan_ai_flavor.py <file.txt|->   # 从文件或 stdin 读取
    python3 scan_ai_flavor.py --text "正文..."

输出：JSON（便于 AI 解析）。
依赖：仅 Python 标准库，可离线运行。
"""

import argparse
import json
import re
import sys

# ---- 词级：AI 味高频词/套话（按强度分级）----
# strength 1 = 轻度（上下文相关），2 = 中度，3 = 强标志
AI_MARKERS = [
    ("综上所述", 3), ("总而言之", 3), ("总的来说", 2), ("总之", 2),
    ("值得注意的是", 3), ("值得一提的是", 3), ("不难发现", 3),
    ("毋庸置疑", 3), ("不言而喻", 3), ("众所周知", 3), ("显而易见", 3),
    ("让我们深入探讨", 3), ("让我们来看看", 3), ("让我们来", 3),
    ("正如我们所见", 3), ("从某种意义上说", 3),
    ("在当今时代", 3), ("在当今社会", 3), ("在这个数字化时代", 3),
    ("随着科技的不断发展", 3), ("随着……的发展", 3),
    ("扮演着至关重要的角色", 3), ("发挥着重要作用", 3), ("起着关键作用", 3),
    ("具有重要意义", 3), ("不容忽视", 2), ("不可忽视", 2),
    ("举足轻重", 2), ("至关重要", 2),
    ("首先，", 2), ("其次，", 2), ("第三，", 2), ("最后，", 2),
    ("与此同时", 2), ("由此可见", 2), ("通过以上分析", 2),
    ("一方面", 2), ("另一方面", 2), ("不仅", 1), ("而且", 1),
    ("提升", 1), ("促进", 1), ("加强", 1), ("优化", 1),
    ("赋能", 2), ("助力", 1), ("打造", 1), ("构建", 1),
    ("深耕", 2), ("生态", 1), ("抓手", 2), ("闭环", 2),
    ("底层逻辑", 2), ("方法论", 1), ("颗粒度", 2), ("对齐", 1),
    ("范式", 2), ("维度", 1), ("破局", 2), ("痛点", 1), ("壁垒", 2),
    ("有利于", 1), ("有助于", 1),
]

# ---- 结构级：正则模式 ----
STRUCTURAL_PATTERNS = {
    "parallel_negation": {          # 平行否定 "不是X而是Y" / "并非X而是Y"
        "pattern": re.compile(r"(不是[^。；!?！？]{1,30}而是|并非[^。；!?！？]{1,30}而是|并非[^。；!?！？]{1,30}而)"),
        "label": "平行否定（不是X而是Y）",
    },
    "rhetorical_qa": {              # 自问自答 "？答案" / "答案是"
        "pattern": re.compile(r"[？?][^。！!？?]{0,12}(答案是|答案就是|原因很简单|问题在于[^。]*答案)"),
        "label": "自问自答（？答案是）",
    },
    "dash_overuse": {               # 破折号滥用（全文 ≥2 处 "——" 才算）
        "pattern": re.compile(r"——"),
        "label": "破折号滥用（——）",
    },
    "enumerative_three": {          # 三点式排比：顿号分隔的恰好3项
        "pattern": re.compile(r"[^，。；！？!?、]{1,10}[、][^，。；！？!?、]{1,10}[、][^，。；！？!?、]{1,10}(?![、])"),
        "label": "三点式排比（A、B、C）",
    },
    "summary_ending": {             # 总结腔结尾："由此可见/综上/总的来说" 引导
        "pattern": re.compile(r"(由此可见|综上|总的来说|总而言之|一言以蔽之)"),
        "label": "总结腔结尾",
    },
    "mirror_structure": {           # 镜像结构：相邻重复句式（"一是…二是…"型）
        "pattern": re.compile(r"(一是[^。；]{2,20}二是|要[^，。]{1,15}，要[^，。]{1,15}，要)"),
        "label": "镜像/重复排比（一是…二是…）",
    },
}

# ---- 语法级：中文特有的 AI 味语法（翻译腔/名物化/过度连接）----
# 名物化/虚化动词："进行/加以/予以/开展" + 名词短语（"对X进行研究"）
NOMINALIZATION_RE = re.compile(r"(进行|加以|予以|开展了|开展了|实施)[^。，；！？!?]{0,8}(研究|分析|处理|优化|调整|改进|调查|评估)")
# "的"字连珠：连续 3+ 个"X的"定语链（"……的……的……"）
DE_CHAIN_RE = re.compile(r"[^。，；！？!?、]{1,8}的[^。，；！？!?、]{1,8}的[^。，；！？!?、]{1,8}的")
# 介词框架滥用："在…方面/对于…来说/通过…的方式/随着…的发展"
PREP_FRAMES_RE = re.compile(r"(对于[^，。；]{1,20}来说|在[^，。；]{1,20}方面|通过[^，。；]{1,20}的方式|随着[^，。；]{1,20}的发展|在[^，。；]{1,20}的背景下)")

# 连接词（机械连接，过密即 AI 味）
CONNECTIVES = ["因此", "所以", "然而", "但是", "与此同时", "此外", "而且", "总之", "由此可见", "同时", "进而", "从而"]

# ---- 标点级：频率统计 ----
# RUC 实测：AI 更爱冒号/分号；真人更爱引号；破折号差异不显著（滥用才算问题）


def count_sentences(text: str) -> tuple[int, float, list[int]]:
    """粗切句子，返回 (句数, 平均长度, 各句长度列表)。"""
    parts = re.split(r"[。！？!?；;\n]", text)
    sentences = [p.strip() for p in parts if len(p.strip()) >= 2]
    if not sentences:
        return 0, 0.0, []
    lens = [len(s) for s in sentences]
    avg = sum(lens) / len(lens)
    return len(sentences), avg, lens


def sentence_variance(lens: list[int]) -> float:
    """句子长度方差：衡量节奏是否太均匀（AI 味：方差偏低）。"""
    if len(lens) < 2:
        return 0.0
    avg = sum(lens) / len(lens)
    return sum((x - avg) ** 2 for x in lens) / len(lens)


def scan(text: str) -> dict:
    text_lower = text.lower()

    # 1) 词级
    found: dict[str, int] = {}
    for marker, strength in AI_MARKERS:
        if marker in text_lower:
            found[marker] = max(found.get(marker, 0), strength)

    # 2) 结构级
    structural: dict[str, int] = {}
    for key, spec in STRUCTURAL_PATTERNS.items():
        if key == "dash_overuse":
            continue  # 破折号由下方 "≥2 才算滥用" 逻辑统一处理
        n = len(spec["pattern"].findall(text))
        if n > 0:
            structural[key] = n

    # 破折号滥用：仅当 ≥2 处才算滥用（1 处是正常使用）
    dash_total = len(STRUCTURAL_PATTERNS["dash_overuse"]["pattern"].findall(text))
    if dash_total >= 2:
        structural["dash_overuse"] = dash_total

    # 3) 语法级
    syntax: dict[str, int] = {}
    n_nominal = len(NOMINALIZATION_RE.findall(text))
    if n_nominal:
        syntax["nominalization"] = n_nominal            # 名物化/虚化动词
    n_dechain = len(DE_CHAIN_RE.findall(text))
    if n_dechain:
        syntax["de_chain"] = n_dechain                  # "的"字连珠
    n_prep = len(PREP_FRAMES_RE.findall(text))
    if n_prep:
        syntax["prep_frames"] = n_prep                  # 介词框架
    connective_total = sum(text.count(c) for c in CONNECTIVES)
    if connective_total:
        syntax["connective_overuse"] = connective_total  # 连接词总数（过密才扣分）

    # 4) 标点级
    punct: dict[str, int] = {}
    n_semicolon = text.count("；")
    if n_semicolon >= 2:
        punct["semicolon_overuse"] = n_semicolon        # 分号滥用（AI 爱用分号列排比）
    n_colon = text.count("：")
    if n_colon >= 3:
        punct["colon_heavy"] = n_colon                  # 冒号过多
    n_q = text.count("？") + text.count("?")
    n_ex = text.count("！") + text.count("!")
    if len(text) >= 150 and n_q == 0 and n_ex == 0:
        punct["no_tone_punct"] = 1                      # 语气标点缺失（长文本无问号/感叹号）
    ellipsis = text.count("……") + text.count("...")
    if ellipsis:
        punct["ellipsis"] = ellipsis                    # 省略号（中性统计，不扣分）
    # 一逗到底：单句内含 ≥4 个逗号
    run_on = 0
    for clause in re.split(r"[。！？!?；;\n]", text):
        if clause.count("，") + clause.count(",") >= 4:
            run_on += 1
    if run_on:
        punct["run_on_comma"] = run_on                  # 一逗到底（长句逗号过多）

    # 段落统计
    paras = [p.strip() for p in text.split("\n") if len(p.strip()) > 0]
    para_lens = [len(p) for p in paras] if paras else []

    # 短句结尾统计：以 ≤8 字句子结尾的段落数
    short_end_count = 0
    for p in paras:
        ends = [s.strip() for s in re.split(r"[。！？!?；;\n]", p) if s.strip()]
        if ends and len(ends[-1]) <= 8:
            short_end_count += 1

    # 句式节奏
    n_sent, avg_len, lens = count_sentences(text)
    variance = sentence_variance(lens)

    # 评分：0-100，越高 AI 味越重
    score = 0
    score += min(35, len(found) * 3.5)                      # 词级数量
    score += min(10, sum(v for v in found.values()))        # 词级强度
    score += min(20, len(structural) * 5)                   # 结构级（比词级更实锤）
    score += min(10, len(syntax) * 2.5)                     # 语法级（翻译腔/名物化等）
    score += min(10, len(punct) * 2.5)                      # 标点级（分号/冒号/一逗到底等）
    if n_sent >= 5:
        if variance < 60:                                   # 节奏太均匀
            score += 8
        elif variance < 120:
            score += 4
        if avg_len > 40:
            score += 6
        elif avg_len > 30:
            score += 3
    if para_lens and len(para_lens) >= 3:
        pvar = sentence_variance(para_lens)
        if pvar < 200:
            score += 2
    if paras and short_end_count > 1:
        score += 4                                          # 多段以短句结尾
    score = min(100, round(score))

    return {
        "text_length": len(text),
        "sentence_count": n_sent,
        "avg_sentence_len": round(avg_len, 1),
        "sentence_len_variance": round(variance, 1),
        "paragraph_count": len(paras),
        "short_ending_paragraphs": short_end_count,
        "ai_markers": found,
        "ai_marker_count": len(found),
        "structural_markers": structural,
        "syntax_markers": syntax,
        "punctuation_markers": punct,
        "ai_flavor_score": score,
        "verdict": _verdict(score),
    }


def _verdict(score: int) -> str:
    if score >= 60:
        return "AI味很重，按流程重写（Voice→Tells→Audit）"
    if score >= 35:
        return "有一定AI味，重点清理结构与标志词"
    if score >= 15:
        return "轻微AI味，微调即可"
    return "基本无AI味"


def main():
    ap = argparse.ArgumentParser(description="扫描中文文本的AI味标志（词级+结构级）")
    ap.add_argument("file", nargs="?", help="输入文件路径，或 - 读取 stdin")
    ap.add_argument("--text", help="直接传入文本")
    args = ap.parse_args()

    if args.text:
        text = args.text
    elif args.file == "-" or args.file is None and not sys.stdin.isatty():
        text = sys.stdin.read()
    elif args.file:
        with open(args.file, encoding="utf-8") as f:
            text = f.read()
    else:
        ap.print_help()
        sys.exit(1)

    result = scan(text)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
