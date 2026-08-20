#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
viz_advisor.py — 可视化类型顾问（visualization 技能选型辅助）
============================================================
输入用户的可视化需求描述，输出推荐主类型（diagram/chart/table/report）、
图表子类型、理由、置信度与备选方案（JSON）。

用法：
    python3 viz_advisor.py "<需求描述>"
    python3 viz_advisor.py --text "<需求描述>"      # 等价
    python3 viz_advisor.py "把这几个月的销量画成图" --json

依赖：仅 Python 标准库，离线可运行。
"""

import argparse
import json
import sys

# ---- 主类型关键词（命中即加权）----
# 权重：越专指的类型权重越高，避免"画个图"这类泛词抢占
CATEGORIES = {
    "diagram": {
        "weight": 1.0,
        "keywords": [
            "流程图", "流程", "时序图", "时序", "顺序图", "sequence",
            "类图", "class", "对象图", "状态图", "状态机", "state",
            "er图", "er 图", "实体关系", "关系图", "架构图", "架构", "拓扑",
            "思维导图", "脑图", "mindmap", "甘特", "gantt", "排期图",
            "时间线", "timeline", "泳道", "用户旅程", "journey",
            "决策树", "依赖图", "活动图", "用例图", "组件图", "部署图",
        ],
    },
    "chart": {
        "weight": 1.2,
        "keywords": [
            "图表", "图", "折线", "柱状", "条形", "饼图", "环形图",
            "散点", "直方图", "面积图", "热力图", "热力", "雷达图", "箱线图",
            "趋势", "占比", "构成", "分布", "对比", "排行", "排名",
            "数据可视化", "可视化数据", "chart", "plot", "graph",
            "bar", "line", "pie", "scatter", "histogram", "trend",
        ],
    },
    "table": {
        "weight": 1.0,
        "keywords": [
            "表格", "表", "对照表", "汇总表", "明细表", "清单", "目录",
            "整理成表", "做成表格", "转成表", "table", "spreadsheet",
            "excel 表格", "csv", "列表",
        ],
    },
    "report": {
        "weight": 1.1,
        "keywords": [
            "报告", "报表", "周报", "月报", "日报", "汇总报告",
            "汇报", "dashboard", "看板", "数据报告", "可视化报告",
            "report", "summary", "总结报告",
        ],
    },
}

# ---- 图表子类型（chart 内部再分级）----
CHART_SUBTYPES = [
    ("line", ["趋势", "走势", "折线", "变化", "时间", "月份", "几个月", "每月",
              "月度", "季度", "年度", "逐年", "每周", "每日", "增长",
              "trend", "line", "走势图", "曲线"]),
    ("bar", ["对比", "比较", "柱状", "条形", "排名", "排行", "同比", "环比",
             "bar", "compare", "对比图"]),
    ("pie", ["占比", "构成", "比例", "份额", "饼", "百分比",
             "pie", "proportion", "share"]),
    ("scatter", ["相关性", "相关", "散点", "关系", "correlation", "scatter"]),
    ("histogram", ["分布", "频率", "直方", "histogram", "distribution"]),
    ("area", ["面积", "累积", "累计", "area", "cumulative"]),
    ("heatmap", ["热力", "heatmap", "密度"]),
]

# ---- 图种（diagram 内部再分级）----
DIAGRAM_TYPES = [
    ("flowchart", ["流程", "算法", "决策", "步骤", "flow", "流程图"]),
    ("sequenceDiagram", ["时序", "顺序", "交互", "调用", "登录流程",
                         "sequence", "api 调用"]),
    ("classDiagram", ["类图", "面向对象", "类", "class"]),
    ("stateDiagram-v2", ["状态机", "状态图", "生命周期", "state"]),
    ("erDiagram", ["er", "实体关系", "数据库", "表结构", "建模"]),
    ("gantt", ["甘特", "排期", "项目计划", "里程碑", "gantt"]),
    ("mindmap", ["思维导图", "脑图", "发散", "mindmap"]),
    ("timeline", ["时间线", "里程碑", "timeline"]),
    ("journey", ["用户旅程", "体验", "journey"]),
]


def score(text_lower, rules, weight):
    """按关键词命中次数打分。"""
    hits = [kw for kw in rules if kw in text_lower]
    return len(hits) * weight, hits


def classify(text):
    text_lower = text.lower()
    scores = {}
    for cat, cfg in CATEGORIES.items():
        s, hits = score(text_lower, cfg["keywords"], cfg["weight"])
        scores[cat] = {"score": s, "hits": hits}

    best = max(scores, key=lambda c: scores[c]["score"])
    best_score = scores[best]["score"]
    if best_score == 0:
        return {
            "category": "unknown",
            "reason": "无法从描述判断可视化类型，建议向用户确认：是画图谱(diagram)/图表(chart)/表格(table)/报告(report)？",
            "confidence": 0.0,
            "matched": {c: scores[c]["hits"] for c in scores},
        }

    # 子类型推荐
    subtype = None
    subtype_zh = None
    if best == "chart":
        for name, kws in CHART_SUBTYPES:
            if any(k in text_lower for k in kws):
                subtype = name
                subtype_zh = {"line": "折线图", "bar": "柱状图", "pie": "饼图",
                              "scatter": "散点图", "histogram": "直方图",
                              "area": "面积图", "heatmap": "热力图"}[name]
                break
    elif best == "diagram":
        for name, kws in DIAGRAM_TYPES:
            if any(k in text_lower for k in kws):
                subtype = name
                subtype_zh = {"flowchart": "流程图", "sequenceDiagram": "时序图",
                              "classDiagram": "类图", "stateDiagram-v2": "状态图",
                              "erDiagram": "ER 图", "gantt": "甘特图",
                              "mindmap": "思维导图", "timeline": "时间线",
                              "journey": "用户旅程图"}[name]
                break

    total_hits = sum(len(scores[c]["hits"]) for c in scores)
    confidence = min(0.95, 0.4 + 0.1 * total_hits)

    reason = f"命中类型关键词：{scores[best]['hits'] or '（泛词）'}"
    if subtype_zh:
        reason += f" → 推荐子类型：{subtype_zh}"

    return {
        "category": best,
        "subtype": subtype,
        "subtype_zh": subtype_zh,
        "reason": reason,
        "confidence": round(confidence, 2),
        "matched": {c: scores[c]["hits"] for c in scores},
    }


def main():
    ap = argparse.ArgumentParser(description="可视化类型顾问（visualization 技能）")
    ap.add_argument("text", nargs="?", help="用户的可视化需求描述")
    ap.add_argument("--text", dest="text_opt", help="等价于位置参数")
    ap.add_argument("--json", action="store_true", help="仅输出 JSON（默认已输出 JSON）")
    args = ap.parse_args()

    text = args.text or args.text_opt
    if not text:
        print(json.dumps({"error": "缺少需求描述。用法：python3 viz_advisor.py '<需求描述>'"},
                         ensure_ascii=False))
        sys.exit(1)

    print(json.dumps(classify(text), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
