#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
svg_chart.py — 离线 SVG 图表生成器（visualization 技能）
============================================================
把结构化数据渲染成**纯 SVG** 图表（柱状/条形/折线/面积/饼/环形/散点/直方图），
零第三方依赖、可离线运行、可内嵌 Markdown/HTML/报告/网页。

用法：
  python3 svg_chart.py --type bar  --data '{"labels":["1月","2月","3月"],"values":[120,210,95]}'
  python3 svg_chart.py --type line --data '{"labels":["1月","2月"],"series":[{"name":"销量","values":[120,210]},{"name":"成本","values":[80,90]}]}' -o chart.svg
  python3 svg_chart.py --type pie  --data '{"labels":["搜索引擎","直接访问"],"values":[45,30]}' --title "流量占比"
  python3 svg_chart.py --type histogram --data '{"values":[1,2,2,3,3,3,4,5,5,6]}' --bins 5
  python3 svg_chart.py --type bar --data '<file.json>' --palette tableau --show-values

数据格式（随 --type 不同）：
  bar/hbar/line/area : {"labels": [...], "values": [...]}
                       或 {"labels": [...], "series": [{"name":..,"values":[...]}, ...]}
  scatter            : {"points": [{"x":..,"y":..,"label":..}, ...]}
  pie/donut          : {"labels": [...], "values": [...]}
  histogram          : {"values": [原始数值...]}

输出：SVG 到 stdout 或 -o 文件。默认 Okabe-Ito 色盲安全配色，含 <title>/<desc>（无障碍）。
依赖：仅 Python 标准库，离线可运行。
"""

import argparse
import json
import math
import os
import sys
import xml.sax.saxutils as sax

FONT = "system-ui, 'PingFang SC', 'Microsoft YaHei', sans-serif"
GRID = "#E5E5E5"      # 浅灰网格（数据墨水比）
AXIS = "#888888"
TEXT = "#333333"

# 色板：默认 Okabe-Ito（经科学验证的色盲安全）；tableau/antv 为备选
PALETTES = {
    "okabe": ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2",
              "#D55E00", "#CC79A7", "#999999"],
    "tableau": ["#4E79A7", "#F28E2B", "#E15759", "#76B7B2", "#59A14F",
                "#EDC948", "#B07AA1", "#FF9DA7", "#9C755F", "#BAB0AC"],
    "antv": ["#5B8FF9", "#5AD8A6", "#5D7092", "#F6BD16", "#E8684A",
             "#6DC8EC", "#9270CA", "#FF9D4D", "#269A99", "#FF99C3"],
}


def esc(s):
    return sax.escape(str(s))


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ── 刻度与缩放 ──────────────────────────────────────────────
def nice_step(raw):
    """把任意步长规整到 1/2/5×10^n 序列。"""
    if raw <= 0:
        return 1.0
    mag = 10 ** math.floor(math.log10(raw))
    norm = raw / mag
    for m in (1, 2, 5, 10):
        if norm <= m:
            return m * mag
    return 10 * mag


def make_ticks(vmin, vmax, target=5):
    """生成整洁刻度列表 [(value, label)]。"""
    if vmax <= vmin:
        vmax = vmin + 1
    span = vmax - vmin
    step = nice_step(span / max(1, target - 1))
    lo = math.floor(vmin / step) * step
    ticks = []
    v = lo
    while v <= vmax + 1e-9:
        ticks.append((v, _fmt_tick(v)))
        v += step
    return ticks


def _fmt_tick(v):
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return ("%.1f" % v).rstrip("0").rstrip(".")


def linear(v, vmin, vmax, omin, omax):
    if vmax <= vmin:
        return omin
    return omin + (v - vmin) / (vmax - vmin) * (omax - omin)


def series_of(data):
    """统一成 (labels, [{name, values}])。"""
    labels = data.get("labels", [])
    if "series" in data and data["series"]:
        return labels, data["series"]
    values = data.get("values", [])
    return labels, [{"name": None, "values": values}]


def all_values(series):
    return [v for s in series for v in s["values"] if v is not None]


# ── 公共外壳 ────────────────────────────────────────────────
def shell(inner, title, desc, w, h):
    tid, did = "t", "d"
    return (
        f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-labelledby="{tid} {did}">\n'
        f'  <title id="{tid}">{esc(title)}</title>\n'
        f'  <desc id="{did}">{esc(desc)}</desc>\n'
        f'  <style>text{{font-family:{FONT};}} .tick{{font-size:12px;fill:{TEXT};}} '
        f'.axis{{stroke:{AXIS};stroke-width:1;}} .grid{{stroke:{GRID};stroke-width:1;}} '
        f'.title{{font-size:17px;font-weight:bold;fill:#111;}} '
        f'.sub{{font-size:12px;fill:#666;}} .legend{{font-size:12px;fill:{TEXT};}}</style>\n'
        + inner +
        f"</svg>\n"
    )


# ── 坐标轴类图表（bar/hbar/line/area/scatter 共用）──────────
def base_plot(spec, labels, series, draw_fn, is_hbar=False):
    w = int(spec.get("width", 720))
    h = int(spec.get("height", 420))
    title = spec.get("title", "")
    caption = spec.get("caption", "")
    show_values = spec.get("show_values", False)
    colors = spec.get("_colors")
    top = 46
    left, right, bottom = (110, 24, 58) if is_hbar else (74, 24, 58)
    pw, ph = w - left - right, h - top - bottom

    if is_hbar:
        # 横向：x 轴为数值，y 轴为类别
        ymin, ymax = 0, max(0, max(all_values(series)) * 1.08 or 1)
        yticks = make_ticks(ymin, ymax, target=6)
        n = len(labels) or 1
        slot = pw / n
        cx = left + slot / 2
        def X(v): return left + (v - ymin) / (ymax - ymin) * pw
        def Y(i): return top + (i + 0.5) * (ph / n)
        bar_w = min(28.0, slot * 0.5)
    else:
        ymin, ymax = 0, max(0, max(all_values(series)) * 1.08 or 1)
        yticks = make_ticks(ymin, ymax, target=6)
        xmin, xmax = 0, max(1, len(labels) - 1)
        def Y(v): return top + ph - (v - ymin) / (ymax - ymin) * ph
        def X(i): return left + (i / xmax) * pw
        n = len(labels) or 1
        slot = pw / n
        bar_w = min(46.0, slot * 0.62)

    parts = []
    parts.append(f'<text x="{left + pw / 2}" y="26" text-anchor="middle" class="title">{esc(title)}</text>')
    if caption:
        parts.append(f'<text x="{left}" y="{h - 14}" class="sub">{esc(caption)}</text>')

    # 网格 + 数值轴刻度
    if is_hbar:
        for v, lbl in yticks:
            gx = X(v)
            parts.append(f'<line class="grid" x1="{gx:.1f}" y1="{top}" x2="{gx:.1f}" y2="{top + ph}"/>')
            parts.append(f'<text class="tick" x="{gx:.1f}" y="{top + ph + 18}" text-anchor="middle">{esc(lbl)}</text>')
        # 类别标签（左）
        for i, lb in enumerate(labels):
            parts.append(f'<text class="tick" x="{left - 8:.1f}" y="{Y(i) + 4:.1f}" text-anchor="end">{esc(lb)}</text>')
        ax1 = f'<line class="axis" x1="{left:.1f}" y1="{top}" x2="{left:.1f}" y2="{top + ph}"/>'
        ax2 = f'<line class="axis" x1="{left:.1f}" y1="{top + ph}" x2="{left + pw:.1f}" y2="{top + ph}"/>'
        parts.append(ax1); parts.append(ax2)
    else:
        for v, lbl in yticks:
            gy = Y(v)
            parts.append(f'<line class="grid" x1="{left:.1f}" y1="{gy:.1f}" x2="{left + pw:.1f}" y2="{gy:.1f}"/>')
            parts.append(f'<text class="tick" x="{left - 8:.1f}" y="{gy + 4:.1f}" text-anchor="end">{esc(lbl)}</text>')
        for i, lb in enumerate(labels):
            parts.append(f'<text class="tick" x="{X(i):.1f}" y="{top + ph + 20}" text-anchor="middle">{esc(lb)}</text>')
        ax1 = f'<line class="axis" x1="{left:.1f}" y1="{top:.1f}" x2="{left:.1f}" y2="{top + ph:.1f}"/>'
        ax2 = f'<line class="axis" x1="{left:.1f}" y1="{top + ph:.1f}" x2="{left + pw:.1f}" y2="{top + ph:.1f}"/>'
        parts.append(ax1); parts.append(ax2)

    # 图例（多系列）
    if len(series) > 1:
        lx = left + pw
        for k, s in enumerate(series):
            if not s.get("name"):
                continue
            ly = top + 2 + k * 20
            parts.append(f'<rect x="{lx - 14}" y="{ly - 9}" width="10" height="10" rx="1.5" fill="{colors[k % len(colors)]}"/>')
            parts.append(f'<text class="legend" x="{lx}" y="{ly}">{esc(s["name"])}</text>')
        right = max(right, 24 + max((len(esc(s.get("name",""))) for s in series if s.get("name")), default=0) * 6.5)

    parts.append(draw_fn(series, labels, X, Y, colors, bar_w, left, top, ph, pw, is_hbar, show_values))
    return "".join(parts)


def draw_bars(series, labels, X, Y, colors, bar_w, left, top, ph, pw, is_hbar, show_values):
    parts = []
    ns = len(series)
    group = bar_w / ns if ns else bar_w
    for si, s in enumerate(series):
        c = colors[si % len(colors)]
        for i, v in enumerate(s["values"]):
            if v is None:
                continue
            if is_hbar:
                y = top + (i + 0.5) * (ph / len(labels)) - group / 2 + si * group
                hh = max(1.5, group * 0.7)
                bw = max(1.5, X(v) - left)
                parts.append(f'<rect x="{left:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{hh:.1f}" fill="{c}" rx="1.5"/>')
                if show_values:
                    parts.append(f'<text class="tick" x="{left + bw + 4:.1f}" y="{y + hh / 2 + 4:.1f}">{esc(_fmt_tick(v))}</text>')
            else:
                x = left + (i + 0.5) * (pw / len(labels)) - group / 2 + si * group
                yv = Y(v)
                bh = max(1.5, top + ph - yv)
                parts.append(f'<rect x="{x:.1f}" y="{yv:.1f}" width="{group * 0.8:.1f}" height="{bh:.1f}" fill="{c}" rx="1.5"/>')
                if show_values:
                    parts.append(f'<text class="tick" x="{x + group * 0.4:.1f}" y="{yv - 5:.1f}" text-anchor="middle">{esc(_fmt_tick(v))}</text>')
    return "".join(parts)


def draw_lines(series, labels, X, Y, colors, bar_w, left, top, ph, pw, is_hbar, show_values, area=False):
    parts = []
    for si, s in enumerate(series):
        c = colors[si % len(colors)]
        pts = [(X(i), Y(v)) for i, v in enumerate(s["values"]) if v is not None]
        if len(pts) < 2:
            continue
        poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        if area:
            base = Y(0)
            poly_area = f"{pts[0][0]:.1f},{base:.1f} " + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + f" {pts[-1][0]:.1f},{base:.1f}"
            parts.append(f'<polygon points="{poly_area}" fill="{c}" opacity="0.22"/>')
        parts.append(f'<polyline points="{poly}" fill="none" stroke="{c}" stroke-width="2.5"/>')
        for x, y in pts:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#fff" stroke="{c}" stroke-width="2"/>')
            if show_values:
                parts.append(f'<text class="tick" x="{x:.1f}" y="{y - 8:.1f}" text-anchor="middle">{esc(_fmt_tick(s["values"][pts.index((x, y))]))}</text>')
    return "".join(parts)


def render_cartesian(spec, area=False, hbar=False):
    labels, series = series_of(spec["data"])
    ctype = spec.get("type")
    if ctype in ("line", "area") and not hbar:
        draw_fn = lambda *a: draw_lines(*a, area=area)
    else:
        draw_fn = draw_bars
    return shell(
        base_plot(spec, labels, series, draw_fn, is_hbar=hbar),
        spec.get("title", spec.get("type", "chart")),
        spec.get("caption", "") or f"{spec.get('type')} 图，共 {len(labels)} 个类别",
        int(spec.get("width", 720)), int(spec.get("height", 420)),
    )


# ── 饼 / 环形 ───────────────────────────────────────────────
def polar(cx, cy, r, ang_deg):
    a = math.radians(ang_deg - 90)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def render_pie(spec, donut=False):
    w, h = int(spec.get("width", 640)), int(spec.get("height", 420))
    data = spec["data"]
    labels = data.get("labels", [])
    values = data.get("values", [])
    colors = spec.get("_colors")
    total = sum(values) or 1
    title = spec.get("title", "")
    cx, cy, r = 210, 190, 130
    ir = r * 0.58 if donut else 0

    parts = []
    parts.append(f'<text x="{w / 2}" y="26" text-anchor="middle" class="title">{esc(title)}</text>')
    angle = 0.0
    for i, v in enumerate(values):
        if v <= 0:
            continue
        sweep = 360.0 * v / total
        a1, a2 = angle, angle + sweep
        x1, y1 = polar(cx, cy, r, a1)
        x2, y2 = polar(cx, cy, r, a2)
        large = 1 if sweep > 180 else 0
        c = colors[i % len(colors)]
        if donut:
            x1o, y1o = polar(cx, cy, ir, a1)
            x2o, y2o = polar(cx, cy, ir, a2)
            d = (f"M {x1:.1f} {y1:.1f} A {r} {r} 0 {large} 1 {x2:.1f} {y2:.1f} "
                 f"L {x2o:.1f} {y2o:.1f} A {ir} {ir} 0 {large} 0 {x1o:.1f} {y1o:.1f} Z")
        else:
            d = f"M {cx} {cy} L {x1:.1f} {y1:.1f} A {r} {r} 0 {large} 1 {x2:.1f} {y2:.1f} Z"
        parts.append(f'<path d="{d}" fill="{c}" stroke="#fff" stroke-width="1.5"/>')
        if v / total >= 0.08:
            mid = angle + sweep / 2
            mx, my = polar(cx, cy, r * (0.62 if donut else 0.66), mid)
            parts.append(f'<text x="{mx:.1f}" y="{my + 4:.1f}" text-anchor="middle" fill="#fff" font-size="12px" font-weight="bold">{esc(f"{v / total * 100:.0f}%")}</text>')
        angle += sweep

    # 图例（右）
    lx, ly = w - 230, 70
    for i, lb in enumerate(labels):
        y = ly + i * 26
        pct = values[i] / total * 100 if total else 0
        parts.append(f'<rect x="{lx}" y="{y - 10}" width="12" height="12" rx="2" fill="{colors[i % len(colors)]}"/>')
        parts.append(f'<text class="legend" x="{lx + 20}" y="{y}">{esc(lb)} — {esc(f"{pct:.1f}%")}</text>')

    desc = f"{title or '占比'}：" + "、".join(f"{lb} {v / total * 100:.1f}%" for lb, v in zip(labels, values) if total)
    return shell("".join(parts), title or "占比图", desc, w, h)


# ── 散点 ───────────────────────────────────────────────────
def render_scatter(spec):
    w, h = int(spec.get("width", 720)), int(spec.get("height", 420))
    data = spec["data"]
    pts = data.get("points", [])
    colors = spec.get("_colors")
    top, left, bottom, right = 46, 64, 56, 24
    pw, ph = w - left - right, h - top - bottom
    xs = [p.get("x", 0) for p in pts]
    ys = [p.get("y", 0) for p in pts]
    xmin, xmax = min(xs + [0]), max(xs + [1])
    ymin, ymax = 0, max(ys + [1]) * 1.08 or 1
    xticks = make_ticks(xmin, xmax, target=6)
    yticks = make_ticks(ymin, ymax, target=6)

    def X(v): return left + (v - xmin) / (xmax - xmin) * pw
    def Y(v): return top + ph - (v - ymin) / (ymax - ymin) * ph

    parts = [f'<text x="{left + pw / 2}" y="26" text-anchor="middle" class="title">{esc(spec.get("title", ""))}</text>']
    for v, lbl in yticks:
        gy = Y(v)
        parts.append(f'<line class="grid" x1="{left:.1f}" y1="{gy:.1f}" x2="{left + pw:.1f}" y2="{gy:.1f}"/>')
        parts.append(f'<text class="tick" x="{left - 8:.1f}" y="{gy + 4:.1f}" text-anchor="end">{esc(lbl)}</text>')
    for v, lbl in xticks:
        gx = X(v)
        parts.append(f'<text class="tick" x="{gx:.1f}" y="{top + ph + 20}" text-anchor="middle">{esc(lbl)}</text>')
    parts.append(f'<line class="axis" x1="{left:.1f}" y1="{top}" x2="{left:.1f}" y2="{top + ph}"/>')
    parts.append(f'<line class="axis" x1="{left:.1f}" y1="{top + ph}" x2="{left + pw}" y2="{top + ph}"/>')
    for i, p in enumerate(pts):
        c = colors[i % len(colors)]
        px, py = X(p.get("x", 0)), Y(p.get("y", 0))
        parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5" fill="{c}" opacity="0.75"/>')
        if p.get("label"):
            parts.append(f'<text class="tick" x="{px:.1f}" y="{py - 8:.1f}" text-anchor="middle">{esc(p["label"])}</text>')
    return shell("".join(parts), spec.get("title", "散点图"),
                 spec.get("caption", f"散点图，共 {len(pts)} 个点"), w, h)


# ── 直方图 ─────────────────────────────────────────────────
def render_histogram(spec):
    w, h = int(spec.get("width", 720)), int(spec.get("height", 420))
    data = spec["data"]
    vals = [v for v in data.get("values", []) if v is not None]
    colors = spec.get("_colors")
    bins = int(spec.get("bins", 8))
    if not vals:
        return shell("", spec.get("title", "直方图"), "无数据", w, h)
    vmin, vmax = min(vals), max(vals)
    if vmax == vmin:
        vmax = vmin + 1
    step = nice_step((vmax - vmin) / bins)
    edges = []
    e = math.floor(vmin / step) * step
    while e <= vmax:
        edges.append(e)
        e += step
    counts = [0] * (len(edges) - 1)
    for v in vals:
        idx = min(len(counts) - 1, max(0, int((v - edges[0]) / step)))
        counts[idx] += 1
    top, left, bottom, right = 46, 64, 56, 24
    pw, ph = w - left - right, h - top - bottom
    ymax = max(counts + [1])
    yticks = make_ticks(0, ymax, target=5)
    slot = pw / len(counts)

    def Y(v): return top + ph - v / ymax * ph
    parts = [f'<text x="{left + pw / 2}" y="26" text-anchor="middle" class="title">{esc(spec.get("title", "直方图"))}</text>']
    for v, lbl in yticks:
        gy = Y(v)
        parts.append(f'<line class="grid" x1="{left:.1f}" y1="{gy:.1f}" x2="{left + pw:.1f}" y2="{gy:.1f}"/>')
        parts.append(f'<text class="tick" x="{left - 8:.1f}" y="{gy + 4:.1f}" text-anchor="end">{esc(lbl)}</text>')
    parts.append(f'<line class="axis" x1="{left:.1f}" y1="{top}" x2="{left:.1f}" y2="{top + ph}"/>')
    parts.append(f'<line class="axis" x1="{left:.1f}" y1="{top + ph}" x2="{left + pw}" y2="{top + ph}"/>')
    for i, c in enumerate(counts):
        x = left + i * slot + 2
        bw = slot - 4
        yv = Y(c)
        parts.append(f'<rect x="{x:.1f}" y="{yv:.1f}" width="{bw:.1f}" height="{top + ph - yv:.1f}" fill="{colors[0]}" opacity="0.85"/>')
        if i == len(counts) - 1 or i % 2 == 0:
            lbl = f"{edges[i]:g}-{edges[i + 1]:g}"
            parts.append(f'<text class="tick" x="{x + bw / 2:.1f}" y="{top + ph + 20}" text-anchor="middle" font-size="10px">{esc(lbl)}</text>')
    desc = f"直方图：{len(vals)} 个样本，{len(counts)} 个区间"
    return shell("".join(parts), spec.get("title", "直方图"), desc, w, h)


# ── 统一入口 ───────────────────────────────────────────────
def render_svg(spec):
    """把图表配置渲染为 SVG 字符串。spec 结构见文件头。"""
    ctype = spec.get("type", "bar")
    colors = spec.get("colors") or PALETTES.get(spec.get("palette", "okabe"), PALETTES["okabe"])
    spec["_colors"] = colors
    if ctype in ("bar",):
        return render_cartesian(spec, hbar=False)
    if ctype in ("hbar", "barh"):
        return render_cartesian(spec, hbar=True)
    if ctype in ("line",):
        return render_cartesian(spec, area=False)
    if ctype in ("area",):
        return render_cartesian(spec, area=True)
    if ctype == "pie":
        return render_pie(spec, donut=False)
    if ctype == "donut":
        return render_pie(spec, donut=True)
    if ctype == "scatter":
        return render_scatter(spec)
    if ctype == "histogram":
        return render_histogram(spec)
    raise ValueError(f"未知图表类型：{ctype}（支持 bar/hbar/line/area/pie/donut/scatter/histogram）")


def _load_data(arg):
    if arg and os.path.isfile(arg):
        with open(arg, encoding="utf-8") as f:
            return json.load(f)
    return json.loads(arg)


def main():
    ap = argparse.ArgumentParser(description="离线 SVG 图表生成器（visualization 技能）")
    ap.add_argument("--type", default="bar", choices=["bar", "hbar", "line", "area", "pie", "donut", "scatter", "histogram"])
    ap.add_argument("--data", required=True, help="JSON 数据（或数据文件路径）")
    ap.add_argument("--title", default="")
    ap.add_argument("--caption", default="", help="图注/说明（同时作为 <desc>）")
    ap.add_argument("--palette", default="okabe", choices=["okabe", "tableau", "antv"])
    ap.add_argument("--colors", default="", help="自定义色板，逗号分隔的 hex，如 #f00,#0f0")
    ap.add_argument("--width", type=int, default=720)
    ap.add_argument("--height", type=int, default=420)
    ap.add_argument("--show-values", action="store_true", help="在柱/线上标注数值")
    ap.add_argument("--bins", type=int, default=8, help="histogram 的区间数")
    ap.add_argument("-o", "--output", help="输出 SVG 文件路径（缺省打印到 stdout）")
    args = ap.parse_args()

    try:
        data = _load_data(args.data)
    except Exception as e:
        print(f"错误：无法解析 --data：{e}", file=sys.stderr)
        sys.exit(1)

    spec = {
        "type": args.type, "data": data, "title": args.title,
        "caption": args.caption, "palette": args.palette,
        "width": args.width, "height": args.height,
        "show_values": args.show_values, "bins": args.bins,
    }
    if args.colors:
        spec["colors"] = [c.strip() for c in args.colors.split(",") if c.strip()]

    try:
        svg = render_svg(spec)
    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"已生成图表：{args.output}（{len(svg)} 字符）", file=sys.stderr)
    else:
        sys.stdout.write(svg)


if __name__ == "__main__":
    main()
