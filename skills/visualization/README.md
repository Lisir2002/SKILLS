# visualization · 可视化技能

把"画个图"的需求落地为可交付的可视化产物：**图谱（diagram）**、**图表（chart）**、**表格（table）**、**可视化报告（report）**。核心方法论：先选对图，再画好图。

- 图谱：Mermaid 绘制流程图 / 时序图 / 思维导图 / 架构图 / 类图 / 状态图 / ER 图 / 甘特图 / 时间线等 11 种；
- 图表：按"问题→图型"决策树选型（趋势→折线、对比→柱状、占比→饼图、相关→散点…），遵循 Tufte 设计原则（数据墨水比、坐标诚实、颜色语义化）；
- 表格：把 JSON / CSV 数据转成对齐良好、带千分位的 Markdown / CSV / HTML 表格；
- 报告：把多图 + 表格 + 结论合成自包含、打印友好的 HTML 报告。

## 什么时候用

- 你说"画个流程图 / 时序图 / 思维导图 / 架构图 / 类图 / 状态图 / ER 图 / 甘特图 / 时间线"；
- 你给出数据说"做个图表 / 柱状图 / 折线图 / 饼图 / 散点图，把这个数据可视化"；
- 你说"把这组数据做成表格"；
- 你说"出一份可视化报告 / 周报 / 数据汇报 / Dashboard"。

## 安装

将本技能目录放入 AI 工具的 skills 目录：

```bash
mkdir -p <你的skills目录>/visualization
# 把本目录内容（SKILL.md、scripts/、references/）复制进去即可
```

## 用法

在对话中直接触发，例如：

> 根据这组数据画个图：1月 120，2月 210，3月 95，4月 340
> 画一个用户登录的时序图
> 把这份数据做成表格：华东 1200、华南 2300、华北 3400
> 出一份季度运营可视化报告，包含销量趋势、渠道占比、Top 产品表和三条结论

### 可选：脚本

技能包附带三个纯标准库脚本，离线可运行：

```bash
# 1. 选型顾问：不确定该画什么图时
python3 scripts/viz_advisor.py "把这几个月的销量画成图"

# 2. 表格生成器：数据 → Markdown/CSV/HTML
python3 scripts/table_builder.py --data '[{"月份":"1月","销量":120},{"月份":"2月","销量":210}]' \
  --title "月度销量" --thousands

# 3. 报告合成器：JSON 配置 → 自包含 HTML 报告
python3 scripts/report_builder.py report.json -o report.html
```

> 报告配置的示例见 [examples/report.example.json](examples/report.example.json)，可直接作为模板改写。

## 工作方式（四步）

1. **选型** — 判断主类型（diagram/chart/table/report）与图表子类型，一句话说明理由；
2. **生成** — 图谱用 Mermaid（仅支持 11 种已验证图种），表格/报告走脚本，精细样式手写 SVG；
3. **校验** — 语法闭合、节点合法、数据不伪造、坐标不截断、颜色语义化；
4. **输出** — 图 + 一句结论；文件类产物给出路径。

## 目录结构

```
visualization/
├── SKILL.md                     # 技能定义
├── README.md                    # 本文件
├── scripts/
│   ├── viz_advisor.py           # 可视化类型/子类型顾问（纯标准库）
│   ├── table_builder.py         # 数据 → Markdown/CSV/HTML 表格
│   └── report_builder.py        # JSON 配置 → 自包含 HTML 报告
├── references/
│   ├── mermaid-zh.md            # Mermaid 11 图种语法速查（含版本兼容注意）
│   ├── chart-zh.md              # 图表选型决策树 + Tufte 设计原则
│   └── svg-zh.md                # 手写 SVG 规范与示例
└── evals/
    └── evals.json               # 触发与质量测试用例
```

## 依赖

- `python3`（可选，仅脚本需要）；三个脚本均零第三方依赖，可离线运行；
- Mermaid 渲染预览需要支持的环境（Trae / VS Code 插件 / mermaid.live）；无渲染环境时以语法正确为验收标准；
- `xychart-beta` 需要 Mermaid ≥ 10.3，低版本自动回退为表格 + 解读。

## 示例

**输入**：`根据这组数据画个图：1月 120，2月 210，3月 95，4月 340`

**输出**：

```mermaid
xychart-beta
    title "月度访问量"
    x-axis [1月, 2月, 3月, 4月]
    y-axis "访问量" 0 --> 350
    line [120, 210, 95, 340]
```

> 结论：3 月回落、4 月创季度新高，折线图最能看出趋势。

**输入**：`把这份数据做成表格：华东 1200、华南 2300、华北 3400`

**输出**：

| 区域 | 销量 |
|------|-----:|
| 华东 | 1,200 |
| 华南 | 2,300 |
| 华北 | 3,400 |

## 许可

仅供学习与协作使用。
