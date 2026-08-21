# CHANGELOG

本文件记录仓库与各技能包的变更历史。
遵循 Keep a Changelog 约定（新增/变更/弃用/移除/修复/安全）。

## [0.12.0] - 2026-08-21

### 新增
- 第八个技能包 **`image-sense`（无模型图像感知）**：在**完全不依赖任何模型**的前提下"看图"，接无识图能力 API 时可用
  - 源码 `skills/image-sense/`，压缩包 `packages/image-sense.zip`
  - 纯 Python 标准库、零依赖、离线、确定性（用户要求"只保留无模型路径"，已剔除 VLM/Pillow 等一切其他方案）
  - `scripts/image_sense.py` 单入口：PNG 像素级全解析（zlib 解压 + None/Sub/Up/Average/Paeth 逆滤波，位深 1/2/4/8/16、色型 gray/rgb/palette/gray+alpha/rgba）、BMP(BI_RGB 8/24/32)、PPM(P3/P6)、JPEG 头部+EXIF+DQT 近似质量、GIF 尺寸/帧数/透明标志；EXIF TIFF IFD0+GPS 解析（相机/时间/软件/ISO/经纬度）；特征统计（主色/明暗/饱和度/细节/透明占比）+ dHash 感知哈希 + ASCII 预览；`--json` 结构化输出、`--make-test-png` 自测
  - 诚实边界：只给可从像素/字节算出的确定性事实，明确拒绝回答"这是什么/什么情绪"等语义问题（无模型就说不懂），未知格式退出码 3
  - references 一文档：`image-understanding-zh.md`（可行性结论：感知层可无模型、语义层不可；能力表/边界/接线说明 + 来源方向）
  - evals 24 用例（触发 5 正 + 2 反 + 质量 14 + 冒烟 3）全通过
- 仓库 evals 用例数由 120 增至 144，全部通过；`validate_skills.py` 对 image-sense 校验 0 错误 0 警告

## [0.11.0] - 2026-08-21

### 变更
- **frame-breaker 增强：新增「创造保真与可验证」三条硬纪律 + 突破训练先验杠杆**（用户要求：重构不脱离大意、不捏造、新东西可验证可溯源；第二轮认知科学 + AI 前沿深度调研）
  - SKILL.md 新增 `创造保真与可验证` 纪律层：①**意图保留锚**（重构前写下大意/硬约束，重构后回读对照，防"为变而变"）②**断言分级**（事实/合理推断/假设，证据不足显式降级，校准弃权不冒充事实）③**证伪优先**（新想法必须能答"什么能推翻它+怎么验证它+往哪找依据"，先找"杀死查询"再找支持）
  - 思维引擎层新增第 8 条机制：**突破训练先验**（对齐坍缩）→ 稀有性选择杠杆（DivPO 准则：选"稀有但高质"、拒"常见但平庸"，禁用对齐后最典型答案）
  - `frame_gap.py` 新增 `--intent`：双指标判定（框架突破度 + 意图保真度），识别"跑题式重构"，输出真破框且不跑题/跑题/换皮三级判定
  - 新增脚本 `verify_claim.py` 断言验证脚手架（断言层级标注 + 证伪清单 + 可执行验证路径 + 来源方向，含溯因/反溯因/校准弃权原则）
  - references `cognition-zh.md` 新增三章：§10 意图保真（Aalto 重构不助益实证、上下文漂移有界可控 arXiv:2510.07777、轨迹几何全局/局部相似度）、§11 创造性验证（FVA-RAG 证伪检索、OpenAI 校准弃权、溯因缺失前提+反溯因、可执行反事实）、§12 突破训练先验（DivPO/Diversified-DPO/ReDiPO 反对齐坍缩）；来源增至 25+ 条并分组
  - evals 用例 30→42（新增质量 8 + 冒烟 4，含 --intent 真/跑题对比、verify_claim 冒烟）
  - README 同步；`packages/frame-breaker.zip` 重新打包
- 仓库 evals 用例数由 108 增至 120，全部通过；`validate_skills.py` 对 frame-breaker 校验 0 错误 0 警告

## [0.10.0] - 2026-08-21

### 变更
- **frame-breaker 增强：新增「思维引擎层」**（基于认知科学 + AI 创造力前沿深度调研，目标：接近→并驾齐驱→超越人类思维）
  - SKILL.md 新增 `思维引擎层` 章节：把人类创造性思维拆成 7 条实证机制（远程联想/定势与功能固着/双过程切换/顿悟与表征重构/盲变-选择 BVSR/孵化与距离化/元认知监控），每条配「人类短板 → AI 超越杠杆 → 对应步骤」
  - 明确 AI 结构性超越人类的 5 条杠杆：无限工作记忆、零尝试成本、可编程注意、跨域零摩擦检索、可量化元认知
  - 执行纪律：发散期（Step2/3）不评价、收敛期（Step4/5）不新发散（CreativeDC 实证约束后置才有效）；每步必答「解锁了什么原本不可能的」
  - 新增脚本 `concept_blend.py` 概念融合脚手架（Fauconnier & Turner 四空间：词面杂交/结构混合/涌现结构三层融合 + 关键关系压缩清单）
  - 新增脚本 `analogy_map.py` 类比映射脚手架（Gentner 结构映射理论：只借关系结构、不借表面名词，附 8 类关系谓词骨架）
  - 新增 references `cognition-zh.md`：7 条机制完整理论 + LLM vs 人类创造力实证数据（Nature Sci Rep 2025 发散/收敛均超人类、Nature Hum Behav 2026 人类右尾极值优势与天才人设阈限、LLM 输出同质化 arXiv:2501.19361、创造力见顶 arXiv:2504.12320、CreativeDC 约束后置、UoT 变革推理工程化等 15+ 来源）
  - README 同步；`packages/frame-breaker.zip` 重新打包
- 仓库 evals 用例数由 98 增至 108，全部通过（frame-breaker 30/30 含新增质量 6 + 冒烟 4）；`validate_skills.py` 对 frame-breaker 校验 0 错误 0 警告

## [0.9.0] - 2026-08-21

### 新增
- 第七个技能包 **`frame-breaker`（认知突破 · 变革式创造引擎）**：让模型**改变问题本身**而非在问题里找更好的答案，补齐模型天然缺失的"变革式创造"能力
  - 源码 `skills/frame-breaker/`，压缩包 `packages/frame-breaker.zip`
  - 理论依据 Boden 三分法 + 剑桥 van der Schaar《Creativity in Machine Learning》：LLM 天然擅长组合式/探索式创造，但"修改问题表述、改变定义搜索空间的表征机制"（变革式创造）不会自然涌现；895 火柴棒实验实证三模型默认"最小数=最小正数"无法自破框
  - 五步变革引擎：挖假设（六维度显式化隐含假设）→ 反演假设（逐条取反建反世界）→ 域外移植（借无关领域规则系统重定义问题）→ 重构问题（产出新表述+框架前后对比）→ 归零落地（30 天路径+最小验证）
  - 两脚本纯标准库离线：`assumption_audit.py` 隐含假设审计（六维挖掘脚手架 + 框架残留信号扫描 + 20+ 领域规则库）、`frame_gap.py` 框架突破度检测（bigram 结构相似度 + 新颖实词占比 → 0-100，识别"换皮式重构"）
  - references 三文档：`transformational-zh.md` 变革式创造理论、`assumptions-zh.md` 六维假设清单与常见认知框架、`domains-zh.md` 域外移植领域规则库
  - 与 creative-mind 互补：creative-mind 做组合式/探索式（在框架内更好），frame-breaker 做变革式（改变框架本身）
  - evals 20 用例（触发 6 + 质量 10 + 冒烟 4，含真重构/换皮对比）全通过
- 仓库 evals 用例数由 78 增至 98，全部通过；`validate_skills.py` 对 frame-breaker 校验 0 错误 0 警告

## [0.8.0] - 2026-08-21

### 新增
- 第六个技能包 **`creative-mind`（通用创新引擎）**：让模型基于自身知识储备造出属于自己的新东西，破解"AI 输出千篇一律、固化思想"问题
  - 源码 `skills/creative-mind/`，压缩包 `packages/creative-mind.zip`
  - 核心依据"模式坍缩"研究：LLM 默认输出概率最高/最安全/最套路的答案（典型性偏见所致），破解口诀"先列候选池再选择"（口述采样 Verbalized Sampling）
  - 四步引擎：破固化 Detach（先说出典型答案并禁用）→ 发散 Diverge（12+ 技法产出 ≥3 个角度不同候选）→ 收敛 Converge（跨候选杂交 + 新颖/可行/价值三维筛选 + 命名）→ 验新 Verify（red-team 自批判 + 固化度机械检测）
  - 两脚本纯标准库离线：`idea_scaffold.py` 发散脚手架（SCAMPER/跨域融合/反事实/第一性原理/反转/极端化/类比/随机刺激/口述采样，9 技法随机种子可复现）、`stereotype_scan.py` 固化度检测（负面词库 + 结构模式 → 0-100 评分，`--fail-on-high` 供 CI）
  - references 三文档：`creative-workflow-zh.md` 原理（模式坍缩为什么发生）、`techniques-zh.md` 技法库（13 技法+示例）、`anti-cliche-zh.md` AI 套路负面清单
  - evals 18 用例（触发 5 + 质量 10 + 冒烟 3）全通过
- 仓库 evals 用例数由 60 增至 78，全部通过；`validate_skills.py` 对 creative-mind 校验 0 错误 0 警告



### 新增
- 第五个技能包 **`visualization`（可视化）**：把"画个图"需求落地为图谱 / 图表 / 表格 / 可视化报告
  - 源码 `skills/visualization/`，压缩包 `packages/visualization.zip`
  - 四步工作流：选型（`viz_advisor.py` 判型 + chart-zh 决策树）→ 生成（Mermaid/SVG/表格/报告）→ 校验（语法+数据+设计）→ 输出（图 + 结论句）
  - 图谱支持 11 种已验证 Mermaid 图种（flowchart/sequenceDiagram/classDiagram/stateDiagram-v2/erDiagram/gantt/pie/xychart-beta/journey/mindmap/timeline），标注 `xychart-beta` 需 Mermaid ≥10.3 并给出降级方案
  - 图表选型遵循 Tufte 原则（数据墨水比、坐标诚实、颜色语义化、一图一结论），references 四文档：`mermaid-zh.md` / `chart-zh.md` / `svg-zh.md` / `palette-zh.md`
  - 四脚本纯标准库离线：`viz_advisor.py` 类型/子类型顾问（多级关键词打分+置信度）、`svg_chart.py` 离线 SVG 图表生成器、`table_builder.py` 数据→Markdown/CSV/HTML（自动对齐/千分位/排序）、`report_builder.py` JSON 配置→自包含打印友好 HTML（含 mermaid 渲染与离线降级）
  - `examples/report.example.json` 报告配置模板；evals 15 用例（触发 7 + 质量 5 + 冒烟 3）全通过

### 变更
- **visualization 扩展强化（离线图表 + 无障碍配色 + 看板布局）**：
  - 新增 `scripts/svg_chart.py`：8 种图型（bar/hbar/line/area/pie/donut/scatter/histogram）纯 SVG 离线渲染，零依赖，规避 Mermaid `xychart-beta` 版本限制；支持 `--palette`（okabe/tableau/antv）、`--show-values`、`-o` 输出
  - `report_builder.py` 支持 `chart` 章节（内联调用 svg_chart 渲染离线图表）与 `columns` 章节（多列看板布局，`widths` 控列宽、子标题降级 h3、窄屏单列自适应）
  - 新增 `references/palette-zh.md` 配色与无障碍规范：Okabe-Ito/Tableau/AntV 三色板、WCAG 对比度速查（正文 ≥4.5:1）、形状+颜色双重编码、语义色惯例、SVG 无障碍结构
  - `SKILL.md` / `README.md` 更新：svg_chart 用法、chart/columns 章节示例、配色规范引用
  - evals 用例由 15 增至 22（新增质量 4 + 冒烟 3）；`run_evals.py` 支持 `file_exists` 质量断言；仓库 evals 总数由 53 增至 60，全部通过
- 仓库 evals 用例数增至 60，全部通过；`validate_skills.py` 对 visualization 校验 0 错误（3 条 pre-existing 环境路径警告）

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