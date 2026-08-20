# CHANGELOG

本文件记录仓库与各技能包的变更历史。
遵循 Keep a Changelog 约定（新增/变更/弃用/移除/修复/安全）。

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