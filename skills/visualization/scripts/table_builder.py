#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
table_builder.py — 数据 → 表格生成器（visualization 技能）
============================================================
把 JSON / CSV 数据转成对齐良好、可读的 Markdown / CSV / HTML 表格。

用法：
    python3 table_builder.py --data '{"headers":["月份","销量"],"rows":[[1,120],[2,210]]}'
    python3 table_builder.py --data '[{"月份":"1月","销量":120},{"月份":"2月","销量":210}]'
    python3 table_builder.py --csv data.csv --format md --thousands
    python3 table_builder.py --data '<JSON>' --title "月度销量" --caption "单位：件" --align right

选项：
    --format md|csv|html   输出格式（默认 md）
    --align left|center|right|auto   列对齐（默认 auto：数值右对齐，文本左对齐）
    --thousands            数值加千分位
    --title                表格标题
    --caption              表格说明
    --sort N              按第 N 列排序（从 0 起；负数 = 降序，如 --sort -2）

依赖：仅 Python 标准库。
"""

import argparse
import csv
import io
import json
import re
import sys

NUM_RE = re.compile(r"^[-+]?\d[\d,.]*$")


def parse_data(data_json, csv_path):
    """把 JSON 字符串或 CSV 文件解析为 (headers, rows)。"""
    if csv_path:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            rows = [r for r in reader]
        if not rows:
            return [], []
        return rows[0], rows[1:]
    if not data_json:
        return [], []
    obj = json.loads(data_json)
    if isinstance(obj, dict) and "headers" in obj and "rows" in obj:
        return obj["headers"], obj["rows"]
    if isinstance(obj, list) and obj and all(isinstance(r, dict) for r in obj):
        headers = list(obj[0].keys())
        rows = [[r.get(h) for h in headers] for r in obj]
        return headers, rows
    raise ValueError("无法识别的数据格式：期望 {\"headers\":...,\"rows\":...} 或 [{\"列\":值}, ...]")


def fmt_cell(v, thousands):
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return ""
    s = str(v).strip()
    if thousands and NUM_RE.match(s):
        try:
            n = float(s)
            if n == int(n):
                return f"{int(n):,}"
            return f"{n:,}"
        except ValueError:
            return s
    return s


def detect_alignment(headers, rows, align):
    if align in ("left", "center", "right"):
        return [align] * len(headers)
    # auto：该列全为数值 → 右对齐，否则左对齐
    res = []
    for col in range(len(headers)):
        vals = [r[col] for r in rows if col < len(r)]
        numeric = bool(vals) and all(NUM_RE.match(str(v).strip()) for v in vals)
        res.append("right" if numeric else "left")
    return res


def render_markdown(headers, rows, alignments, title, caption):
    out = io.StringIO()
    if title:
        out.write(f"**{title}**\n\n")
    delim = {"left": ":---", "right": "---:", "center": ":---:"}
    out.write("| " + " | ".join(str(h) for h in headers) + " |\n")
    out.write("| " + " | ".join(delim[a] for a in alignments) + " |\n")
    for r in rows:
        cells = [fmt_cell(v, False) for v in r[: len(headers)]]
        cells += [""] * (len(headers) - len(cells))
        out.write("| " + " | ".join(cells) + " |\n")
    if caption:
        out.write(f"\n> {caption}\n")
    return out.getvalue()


def render_csv(headers, rows, thousands):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(headers)
    for r in rows:
        w.writerow([fmt_cell(v, thousands) for v in r[: len(headers)]])
    return out.getvalue()


def render_html(headers, rows, alignments, title, caption):
    out = io.StringIO()
    out.write('<table style="border-collapse:collapse;font-size:14px">\n')
    if title:
        out.write(f'<caption style="font-weight:bold;text-align:left;padding:6px">{title}</caption>\n')
    out.write("  <thead><tr>")
    for h, a in zip(headers, alignments):
        out.write(f'<th style="border:1px solid #ccc;padding:6px 10px;'
                  f'text-align:{a}">{h}</th>')
    out.write("</tr></thead>\n  <tbody>\n")
    for r in rows:
        out.write("    <tr>")
        for col, v in enumerate(r[: len(headers)]):
            a = alignments[col]
            out.write(f'<td style="border:1px solid #eee;padding:6px 10px;'
                      f'text-align:{a}">{fmt_cell(v, True)}</td>')
        out.write("</tr>\n")
    out.write("  </tbody>\n</table>\n")
    if caption:
        out.write(f'<p style="font-size:12px;color:#666">{caption}</p>\n')
    return out.getvalue()


def main():
    ap = argparse.ArgumentParser(description="数据 → 表格生成器（visualization 技能）")
    ap.add_argument("--data", help="JSON 数据：{\"headers\":...,\"rows\":...} 或 [{\"列\":值}]")
    ap.add_argument("--csv", help="CSV 文件路径（优先于 --data）")
    ap.add_argument("--format", default="md", choices=["md", "csv", "html"], dest="fmt")
    ap.add_argument("--align", default="auto", choices=["auto", "left", "center", "right"])
    ap.add_argument("--thousands", action="store_true", help="数值加千分位")
    ap.add_argument("--title", default="", help="表格标题")
    ap.add_argument("--caption", default="", help="表格说明")
    ap.add_argument("--sort", type=int, default=None, help="按第 N 列排序（负数为降序）")
    args = ap.parse_args()

    try:
        headers, rows = parse_data(args.data, args.csv)
    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)
    if not headers:
        print("错误：没有表头或数据为空", file=sys.stderr)
        sys.exit(1)

    if args.sort is not None:
        col = abs(args.sort)
        rev = args.sort < 0
        rows = sorted(rows, key=lambda r: r[col] if col < len(r) else "", reverse=rev)

    alignments = detect_alignment(headers, rows, args.align)

    if args.fmt == "csv":
        out = render_csv(headers, rows, args.thousands)
    elif args.fmt == "html":
        out = render_html(headers, rows, alignments, args.title, args.caption)
    else:
        out = render_markdown(headers, rows, alignments, args.title, args.caption)

    print(out, end="")


if __name__ == "__main__":
    main()
