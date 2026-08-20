# 手写 SVG 规范与示例（中文）

> visualization 技能在需要"精细样式图表"或"自定义图形"时的手写 SVG 依据。
> 默认优先用 Mermaid / 表格；只有需要精确控制样式时才手写 SVG。

---

## 1. 结构基线（每个 SVG 必须满足）

```svg
<svg viewBox="0 0 800 500" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t d">
  <title id="t">2026 年各季度营收（万元）</title>
  <desc id="d">Q1 120，Q2 210，Q3 95，Q4 340，Q4 为全年最高。</desc>
  <!-- 图形内容 -->
</svg>
```

- **必须**：`viewBox`（可缩放）、`xmlns`、`<title>` 与 `<desc>`（无障碍 / 屏幕阅读器）；
- 建议：`role="img"` + `aria-labelledby`；
- 不写 `width`/`height` 固定像素时默认 100% 自适应；写死尺寸请同时给 `viewBox`。

---

## 2. 基础元素速查

| 元素 | 作用 | 示例 |
|------|------|------|
| `<rect>` | 矩形 | `<rect x="10" y="20" width="100" height="40" rx="4"/>` |
| `<circle>` | 圆 | `<circle cx="50" cy="50" r="20"/>` |
| `<ellipse>` | 椭圆 | `<ellipse cx="50" cy="50" rx="30" ry="15"/>` |
| `<line>` | 直线 | `<line x1="0" y1="0" x2="100" y2="100"/>` |
| `<path>` | 任意路径 | `<path d="M10 80 Q 95 10 180 80"/>`（曲线） |
| `<polygon>` | 多边形 | `<polygon points="10,10 110,10 60,60"/>` |
| `<text>` | 文字 | `<text x="50" y="50" text-anchor="middle">标题</text>` |
| `<g>` | 分组 | `<g fill="none" stroke="#333">…</g>` |

常用样式属性（作为 `fill`/`stroke`/`opacity` 等直接写在元素上，或放 `<style>`）：

```svg
<text x="400" y="30" text-anchor="middle" font-size="22" font-weight="bold">季度营收</text>
```

- `text-anchor`：`start`（默认左对齐）/ `middle`（居中）/ `end`（右对齐）；
- 字体：`font-family="system-ui, 'PingFang SC', 'Microsoft YaHei', sans-serif"`（保证中文渲染）。

---

## 3. 一个完整的柱状图示例

```svg
<svg viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="t d">
  <title id="t">2026 年月度销量（件）</title>
  <desc id="d">1 到 4 月销量为 120、210、95、340，4 月最高。</desc>
  <style>
    .axis { stroke:#888; stroke-width:1; }
    .grid { stroke:#eee; stroke-width:1; }
    .bar { fill:#4C78A8; }
    .bar.high { fill:#E45756; }
    .label { font-size:14px; fill:#333; }
  </style>

  <g>
    <line class="axis" x1="80" y1="340" x2="720" y2="340"/>
    <line class="axis" x1="80" y1="340" x2="80" y2="40"/>

    <line class="grid" x1="80" y1="340" x2="720" y2="340"/>
    <line class="grid" x1="80" y1="240" x2="720" y2="240"/>
    <line class="grid" x1="80" y1="140" x2="720" y2="140"/>
    <line class="grid" x1="80" y1="40"  x2="720" y2="40"/>

    <rect class="bar" x="100"  y="237" width="80" height="103"/>
    <rect class="bar" x="260"  y="165" width="80" height="175"/>
    <rect class="bar" x="420"  y="273" width="80" height="67"/>
    <rect class="bar high" x="580" y="40"  width="80" height="300"/>

    <text class="label" x="140" y="360" text-anchor="middle">1月</text>
    <text class="label" x="300" y="360" text-anchor="middle">2月</text>
    <text class="label" x="460" y="360" text-anchor="middle">3月</text>
    <text class="label" x="620" y="360" text-anchor="middle">4月</text>

    <text class="label" x="140" y="228" text-anchor="middle">120</text>
    <text class="label" x="300" y="156" text-anchor="middle">210</text>
    <text class="label" x="460" y="264" text-anchor="middle">95</text>
    <text class="label" x="620" y="31"  text-anchor="middle">340</text>
  </g>
</svg>
```

要点：
- 坐标换算：数值 `v`，范围 `[min,max]`，映射到 `[y_bottom, y_top]`：`y = y_bottom - (v - min) / (max - min) * (y_bottom - y_top)`；
- 从 0 起画（本例 max=350，换算时用真实上下界并**不截断**）；
- 网格线用浅色（数据墨水比），数据本体用深色 / 语义色；
- 数值标签放柱顶，方便精确读取。

---

## 4. 折线 / 散点要点

```svg
<!-- 折线：path + 数据点圆 -->
<polyline points="100,280 260,180 420,320 580,60" fill="none" stroke="#4C78A8" stroke-width="3"/>
<circle cx="100" cy="280" r="4" fill="#4C78A8"/>
<circle cx="260" cy="180" r="4" fill="#4C78A8"/>
<circle cx="420" cy="320" r="4" fill="#4C78A8"/>
<circle cx="580" cy="60"  r="4" fill="#4C78A8"/>
```

- 折线：`<polyline>` 连点 + 每点一个 `<circle>` 标注；
- 散点：仅 `<circle>`（可加透明度处理重叠，`opacity="0.7"`）。

---

## 5. 无障碍与可维护

- 颜色对比度：文字与背景对比 ≥ 4.5:1；不止用颜色区分（同时用形状 / 标签 / 图案）；
- 图表可缩放：靠 `viewBox`，不要用固定像素写死；
- 可维护：数据点 ≤20 手写；更多数据用脚本生成（`table_builder.py` 等），不要手工堆 `rect`；
- 动画（可选，用 SMIL）：`<animate attributeName="opacity" from="0" to="1" dur="0.6s"/>`，仅用于汇报强调，不用于日常文档。

---

## 6. 产出前自检

- [ ] 有 `viewBox` + `xmlns` + `<title>` + `<desc>`
- [ ] 坐标从 0 开始（或显式标注截断）
- [ ] 有单位、有数值标签、有图例（多系列时）
- [ ] 颜色 ≤7 种、语义一致、对比度达标
- [ ] 数据无伪造，坐标未夸大
