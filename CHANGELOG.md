# CHANGELOG

本文件记录仓库与各技能包的变更历史。
遵循 Keep a Changelog 约定（新增/变更/弃用/移除/修复/安全）。

## [0.7.0] - 2026-08-20

### 新增
- 第五个技能包 **`visualization`（可视化）**：把"画个图"需求落地为图谱 / 图表 / 表格 / 可视化报告
  - 源码 `skills/visualization/`，压缩包 `packages/visualization.zip`
  - 四步工作流：选型（`viz_advisor.py` 判型 + chart-zh 决策树）→ 生成（Mermaid/SVG/表格/报告）→ 校验（语法+数据+设计）→ 输出（图 + 结论句）
  - 图谱支持 11 种已验证 Mermaid 图种（flowchart/sequenceDiagram/classDiagram/stateDiagram-v2/erDiagram/gantt/pie/xychart-beta/journey/mindmap/timeline），标注 `xychart-beta` 需 Mermaid ≥10.3 并给出降级方案
  - 图表选型遵循 Tufte 原则（数据墨水比、坐标诚实、颜色语义化、一图一结论），references 三文档：`mermaid-zh.md` / `chart-zh.md` / `svg-zh.md`
  - 三脚本纯标准库离线：`viz_advisor.py` 类型/子类型顾问（多级关键词打分+置信度）、`table_builder.py` 数据→Markdown/CSV/HTML（自动对齐/千分位/排序）、`report_builder.py` JSON 配置→自包含打印友好 HTML（含 mermaid 渲染与离线降级）
  - `examples/report.example.json` 报告配置模板；evals 15 用例（触发 7 + 质量 5 + 冒烟 3）全通过
- 仓库 evals 用例数由 38 增至 53，全部通过；`validate_skills.py` 对 visualization 校验 0 错误 0 警告

## [0.6.0] - 2026-08-20

### 新增
- **技能项目体系强化**（全网调研 skill 开发最佳实践后落地）：
  - 仓库级校验器 `scripts/validate_skills.py`：把 SKILL-AGENTS.md §7 清单自动化（frontmatter/name kebab-case/description 单行与触发词/正文结构/敏感信息扫描/references 一层深/evals 存在性/体积提示），退出码 0/1 供 CI 阻断
  - evals 回归体系：4 个技能全部补齐 `evals/evals.json`（触发正/反用例 + 质量断言 + 纯标准库脚本冒烟），新增运行器 `scripts/run_evals.py`（`--json` 供 CI），共 38 用例全通过
  - GitHub Actions CI `.github/workflows/validate.yml`：push/PR 到 main 自动跑校验器 + evals
  - README 技能索引升级为分类导航表（写作/媒体/行为治理/工具四类），新增「质量保障」章节

### 变更
- `docs/SKILL-AGENTS.md` 强化：
  - 新增 §4.5 技能链与组合（输出契约/共享状态层/四模式/协作分工与安全）
  - §5 重构为「内容与安全规范」：新增 §5.2 注入与输出安全（不信任外部内容为指令/输出注入防护/凭据防窃取，依据 Snyk ToxicSkills 与 RationalEyes 安全手册）、§5.3 最小权限
  - §7 清单新增安全、evals、输出契约检查项；§2 结构图补充仓库级 scripts/ 与 CI
  - §11 参考来源补充技能链、安全、审计实践来源
- `skills/ai-rules/SKILL.md` / `skills/media-parser/SKILL.md`：description 触发词前载（符合 §4.2.5「触发点前载」，首 120 字符内含触发短语）

## [0.5.0] - 2026-08-20

### 新增
- 第三个技能包 **`ai-rules`（规范 AI 做事的规矩）**：给 AI 一套"做事宪法"体系
  - 源码 `skills/ai-rules/`，压缩包 `packages/ai-rules.zip`
  - 三层宪法结构：第 1 层底线（R1 不造假/R2 不越权/R3 不作恶/R4 不越界/R5 不硬撑）+ 第 2 层方法论（G1 先想后做/G2 简单优先/G3 精准改动/G4 目标驱动/G5 证据闭环/G6 边界意识/G7 自省复盘）+ 第 3 层任务专属（按需生成）
  - 设计借鉴：Karpathy 四诫、OpenAI Model Spec（指挥链）、Anthropic 2026 宪法（reason-based + 四层优先级）、Agent Charters（逐条确认）、SafeHarbor/AGrail（自进化记忆）、Harness 证据闭环
  - 四脚本（纯标准库离线）：`generate_rules.py` 规矩生成器 / `confirm_rules.py` 逐条确认器 / `check_compliance.py` 合规自检器 / `retro_learn.py` 复盘学习器
  - `memory/rulebook.json` 跨会话规矩库（基线 R1-R5+G1-G7，复盘可进化、违规计数、去重）
  - references 五文档：root/general 规则详解（含"为什么"）、六类领域模板、指挥链裁决示例、反合理化表
  - 全链路实测：生成 17 条规矩、confirm 抓出歧义并修复（🚧 0）、自检三级判定与退出码正确、复盘新增/去重/违规计数正常

## [0.4.0] - 2026-08-20

### 新增
- 第二个技能包 **`media-parser`（多平台媒体解析）**：解析 20+ 平台分享链接 → 无水印视频/图集/封面/标题/作者/音频
  - 源码 `skills/media-parser/`，基于开源 [media-parser](https://github.com/ucmao/media-parser)（MIT）封装，逻辑本地运行
  - 支持抖音 `a_bogus` 签名、从整段分享文案提取链接、可选 `--download` 本地下载
  - 实测优化：抖音 CDN 节点探测（规避 403）、B站返回 CDN 直链（替代本地路径）、微博修复游客登录页劫持
- 实测验证脚本 `/.validate/`：`mp_validate.py`（解析+URL 可访问性）+ `mp_deep_validate.py`（下载媒体字节校验 MP4/MP3/图片容器结构）+ 自搜真实链接集 `test_links.txt`

### 变更
- `skills/media-parser/SKILL.md` / `README.md`：按 2026-08 补充测试更新"实测可用性"矩阵（抖音 4/4、快手 4/5、B站 3/4、微博部分、小红书需 Cookie、知乎 403 等如实标注）
- **失败案例全网借鉴调研**：检索并借鉴 yby6-crawling-short-video-mcp（20+平台）、wwwzhouhui/video-parser、KuaishouParser、vedio2blog 等开源方案，逐项复测失败链接并归因：
  - 快手 fXqlD6：作品级风控（转发 Cookie 至 `/fw/photo/` 方案同样失败）
  - 微博 status2：纯转发/文本微博（`page_info` 为空），失败为正确行为
  - B站 BV1pBXMYeEkU：`view` API 返回 `-404`，视频已删除，非 412 反爬
  - 西瓜/皮皮虾：旧链接已下架/失效；2026 有效西瓜链接连主流方案也拿不到 `videoInfoRes`
  - 结论：无脚本可修复缺陷，全部为内容失效/平台限制，已写入 Failure Modes 与可用性矩阵
- **微视分享域名补全**：原仅支持 `video.weishi.qq.com` / `isee.weishi.qq.com`，补注册微视 APP 默认分享格式 `h5.weishi.qq.com`（302 至 `m.weishi.qq.com/vise/share/`）及其目标域名；现有 `Vise.initState` 解析逻辑完全适配，实测 200 解析成功、视频为有效 MP4（`video/mp4` ftyp 结构）、封面为 JPEG

## [0.3.0] - 2026-08-20

### 新增
- 首个技能包 **`de-ai-flavor`（去 AI 味）**：将 AI 生成的中文文本改写得像真人
  - 源码 `skills/de-ai-flavor/`，压缩包 `packages/de-ai-flavor.zip`
  - Voice→Tells→Audit 三遍式工作流（先注入人味，再清除标志，最后自审+量化验证）
  - 四层标志检测：结构级（平行否定/三点排比/自问自答/破折号滥用）、语法级（翻译腔/名物化/"的"字连珠/介词框架/连接词过密）、标点级（分号/冒号/一逗到底/语气标点缺失）、词级（套话/模板腔）
  - 脚本 `scripts/scan_ai_flavor.py`：纯标准库，输出 JSON（词级+结构级+语法级+标点级检测、评分 0-100）
  - 规则源 `references/ai-tells-zh.md`：AI 可执行指令集（A-E 五类规则 + 交付前自查清单 + 场景档位）
  - 含 Responsible Use 合规声明（拒绝用于 AI 代写伪装/隐瞒披露）

## [0.2.0] - 2026-08-20

### 新增
- 联网调研各类标准文档规范，新增 `docs/DOC-WRITING-GUIDE.md`（各类型文档写法：skill README / 仓库 README / CHANGELOG / Conventional Commits / ADR / 设计文档 / AGENTS.md）

### 变更
- 重构 `docs/SKILL-AGENTS.md`：基于 Agent Skills 开放标准与 Anthropic 最佳实践，修正并强化
  - `description`：由"≤200 字符"修正为"单行、≤1024 字符、前 ~120 字含触发词、第三人称、含做什么+何时用+反触发"
  - `name`：明确 kebab-case 正则、≤64 字符、= 目录名、不含 claude/anthropic
  - 补充渐进式披露原则、正文结构（When NOT to Use / Output Spec / Failure Modes）、可选 frontmatter 字段、脚本 vs 散文、校验工具、参考依据
- 更新 `docs/SKILL-TEMPLATE.md` 与 `README.md`、`CHANGELOG.md` 以匹配新规范

## [0.1.0] - 2026-08-20

### 新增
- 项目初始化，搭建仓库规范骨架：
  - `docs/SKILL-AGENTS.md` — 技能设计与打包规范
  - `docs/SKILL-TEMPLATE.md` — SKILL.md 推荐模板
  - `README.md` — 仓库说明文档