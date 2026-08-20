#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
report_builder.py — 可视化报告合成器（visualization 技能）
============================================================
把 JSON 配置（标题/章节/文字/表格/Mermaid/SVG/要点）合成为自包含、打印友好的 HTML 报告。

用法：
    python3 report_builder.py report.json > report.html
    python3 report_builder.py report.json -o report.html

report.json 结构：
{
  "title": "2026 Q3 运营数据报告",
  "subtitle": "内部资料 · 数据团队",
  "date": "2026-08-20",
  "sections": [
    {"type": "text",   "heading": "概述",   "body": "一段正文，支持 **Markdown 加粗**。"},
    {"type": "mermaid","heading": "架构",   "code": "graph TD; A[用户]-->B[服务]"},
    {"type": "table",  "heading": "对比",   "table": {"headers": ["指标","Q2","Q3"], "rows": [[...]]}},
    {"type": "svg",    "heading": "自绘",   "code": "<svg ...>...</svg>"},
    {"type": "list",   "heading": "结论",   "items": ["要点一", "要点二"]},
    {"type": "callout","heading": "注意",   "body": "...", "tone": "warn|info|danger|ok"}
  ]
}

Mermaid 渲染需要网络（CDN）；离线时图表以代码块展示，报告其余内容不受影响。
依赖：仅 Python 标准库。
"""

import argparse
import html
import json
import re
import sys

# ---- 极简 Markdown 加粗/行内代码渲染（够用即可，不引第三方库）----
def inline_md(s):
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def table_to_html(tbl):
    headers = tbl.get("headers", [])
    rows = tbl.get("rows", [])
    out = ['<table class="data">']
    if headers:
        out.append("<thead><tr>" + "".join(f"<th>{html.escape(str(h))}</th>" for h in headers) + "</tr></thead>")
    out.append("<tbody>")
    for r in rows:
        cells = [html.escape(str(v)) for v in r]
        cells += [""] * (len(headers) - len(cells))
        out.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


CALL_TONE = {
    "info":  ("#E8F1FB", "#1F4E8C"),
    "warn":  ("#FDF3E7", "#8A5B00"),
    "danger":("#FBE9E9", "#8C1D1D"),
    "ok":    ("#E9F6EC", "#1E6B34"),
}


def build_report(data):
    title = data.get("title", "可视化报告")
    subtitle = data.get("subtitle", "")
    date = data.get("date", "")

    parts = []
    for sec in data.get("sections", []):
        stype = sec.get("type", "text")
        heading = sec.get("heading")
        if heading:
            parts.append(f'<h2>{html.escape(heading)}</h2>')
        if stype == "text":
            body = sec.get("body", "")
            parts.append('<div class="text">' + "".join(
                f"<p>{inline_md(b)}</p>" for b in body.split("\n\n") if b.strip()
            ) + "</div>")
        elif stype == "list":
            items = "".join(f"<li>{inline_md(i)}</li>" for i in sec.get("items", []))
            parts.append(f"<ul>{items}</ul>")
        elif stype == "table":
            parts.append(table_to_html(sec.get("table", {})))
        elif stype == "mermaid":
            code = sec.get("code", "")
            parts.append('<pre class="mermaid">' + html.escape(code) + "</pre>")
        elif stype == "svg":
            parts.append('<div class="svg-block">' + sec.get("code", "") + "</div>")
        elif stype == "callout":
            bg, fg = CALL_TONE.get(sec.get("tone", "info"), CALL_TONE["info"])
            parts.append(
                f'<div class="callout" style="background:{bg};border-left:4px solid {fg};color:{fg}">'
                f"{inline_md(sec.get('body', ''))}</div>"
            )
        else:
            parts.append(f'<p>[未知章节类型：{html.escape(stype)}]</p>')

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{html.escape(title)}</title>
<style>
  body {{ font-family: system-ui, 'PingFang SC', 'Microsoft YaHei', sans-serif;
         max-width: 900px; margin: 0 auto; padding: 32px 24px; color: #222; line-height: 1.7; }}
  h1 {{ font-size: 26px; margin-bottom: 4px; }}
  .meta {{ color: #888; font-size: 13px; margin-bottom: 24px; }}
  h2 {{ font-size: 19px; border-bottom: 1px solid #eee; padding-bottom: 6px; margin-top: 32px; }}
  table.data {{ border-collapse: collapse; width: 100%; margin: 8px 0; font-size: 14px; }}
  table.data th, table.data td {{ border: 1px solid #ddd; padding: 6px 10px; text-align: right; }}
  table.data th {{ background: #f5f5f5; text-align: center; }}
  table.data td:first-child {{ text-align: left; }}
  pre.mermaid {{ background: #fafafa; border: 1px dashed #bbb; border-radius: 6px;
                padding: 12px; overflow-x: auto; font-size: 13px; }}
  .callout {{ padding: 12px 16px; border-radius: 6px; margin: 12px 0; }}
  .svg-block svg {{ max-width: 100%; height: auto; }}
  code {{ background: #f0f0f0; padding: 1px 5px; border-radius: 4px; font-size: 13px; }}
  @media print {{ body {{ padding: 0; }} h2 {{ page-break-after: avoid; }} }}
</style>
</head>
<body>
<h1>{html.escape(title)}</h1>
{(f'<div class="meta">{html.escape(subtitle)}' + (' · ' + html.escape(date) if date else '') + '</div>') if subtitle or date else ''}
{''.join(parts)}
<script>
  /* Mermaid 渲染（需网络）。离线时上方代码块原样展示，报告其余内容不受影响。 */
  (function(){{
    var c = document.createElement('script');
    c.src = 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js';
    c.onload = function(){{ mermaid.initialize({{startOnLoad:true, theme:'default'}}); }};
    document.head.appendChild(c);
  }})();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="可视化报告合成器（visualization 技能）")
    ap.add_argument("config", help="report.json 配置文件路径")
    ap.add_argument("-o", "--output", help="输出 HTML 文件路径（缺省打印到 stdout）")
    args = ap.parse_args()

    try:
        with open(args.config, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"错误：无法读取配置文件 {args.config}：{e}", file=sys.stderr)
        sys.exit(1)

    out = build_report(data)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"已生成报告：{args.output}", file=sys.stderr)
    else:
        sys.stdout.write(out)


if __name__ == "__main__":
    main()
