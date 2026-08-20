# CHANGELOG

本文件记录仓库与各技能包的变更历史。
遵循 Keep a Changelog 约定（新增/变更/弃用/移除/修复/安全）。

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