# 各类型文档规范写法指南（Documentation Writing Guide）

> 依据全网主流规范（Keep a Changelog、Conventional Commits、Standard Readme、makeareadme、ADR 模板等）整理，作为本仓库各类文档的统一写法约定。技能格式规范另见 [SKILL-AGENTS.md](SKILL-AGENTS.md)。

---

## 1. 通用写作原则（适用所有文档）

- **写给读者，不写给作者**：描述行为与影响，不堆内部实现细节、变量名、补丁过程；
- **主动语态 + 祈使句**：`Add X` / `Fix crash when …`，少用被动；
- **撰写视角**：多数文档面向"次新手"，用最少的步骤讲清一件事；
- **同一版本/发布**：新到旧、最新在上；
- **具体 > 抽象**：能用 `Python 3.12, pnpm 9.x` 就说具体版本，不用"较新版本"；
- **干净示例**：不出现真实/示例密钥（含 `sk_test_…`）、内部 URL、个人数据。

---

## 2. `SKILL.md`（技能定义）

完整规范见 [SKILL-AGENTS.md](SKILL-AGENTS.md)。要点回顾：

- frontmatter：仅 `name`（kebab-case、= 目录名、≤64 字符）+ `description`（英文、单行、≤1024 字符、前 120 字含触发词、第三人称、含"做什么+何时用+反触发"）；
- 正文：强小标题 + 短段落：Purpose / When to Use / **When NOT to Use** / Workflow / Output Spec / Failure Modes / Dependencies / References / Examples。

---

## 3. 技能 `README.md`（每个技能目录内）

面向使用该技能的人（即下载并安装它的人），建议结构：

| 区块 | 说明 |
|------|------|
| 标题 + 一句话简介 | 该技能做什么、解决什么问题 |
| 何时使用 / 不用于 | 触发场景与反触发，与 SKILL.md 一致 |
| 安装 | 放到哪里（如 `.trae/skills/<name>/`）或导入流程 |
| 用法 | 最小可运行示例 + 常用命令/触发语 |
| 依赖 | 所需环境/工具/权限，含版本 |
| 示例 | 干净、可直接复用的输入输出示例 |
| 许可 | 如适用 |

---

## 4. 仓库根 `README.md`（总览）

作为仓库"名片"，采用**认知漏斗**：先宽后窄，让人能快速判断是否需要深入。参考 structure：

1. 标题 + 一句话定位；
2. **你最想让人看到的核心**（本项目：技能库规范、技能索引）；
3. 目录结构；
4. 安装/使用（本库：如何装某个技能）；
5. 技能索引表；
6. 贡献/流程；
7. 许可。

要点：任何次新手只看 README 也能上手；不写未完成的大段技术文档；链接可跳转到 `docs/` 深化。

---

## 5. `CHANGELOG.md`（Keep a Changelog）

- 一个版本一个区块，**最新在上**，标题：`## [x.y.z] - YYYY-MM-DD`（ISO 8601 日期）；
- 顶部保留 `## [Unreleased]` 跟踪未发布改动；
- 每条改动归入六个类别之一，**空类别省略**：

| 类别 | 含义 |
|------|------|
| **Added** | 新功能 |
| **Changed** | 既有功能的变更 |
| **Deprecated** | 即将移除的功能 |
| **Removed** | 已移除的功能 |
| **Fixed** | 缺陷修复 |
| **Security** | 漏洞/安全修复（优先写 CVE ID） |

- **禁止**直接 dump `git log`（噪音大）；按用户可感知的粒度合并相近改动；
- 每条从读者视角描述："Add dark mode" 而非 "implement ThemeProvider"。

示例：

```markdown
## [Unreleased]

### Added
- 仓库 skill 包验收脚本

## [0.1.0] - 2026-08-20

### Added
- 项目初始化，技能库规范骨架（SKILL-AGENTS.md / SKILL-TEMPLATE.md / README.md）
```

---

## 6. 提交信息（Conventional Commits）

格式：`<type>(<scope>): <description>`

主要类型：

| 类型 | 用途 |
|------|------|
| `feat:` | 新功能 |
| `fix:` | 缺陷修复 |
| `docs:` | 文档变更 |
| `refactor:` | 重构，不改行为 |
| `perf:` | 性能优化 |
| `test:` | 测试 |
| `build:` / `ci:` | 构建 / CI |
| `chore:` | 其他（依赖、工具） |

规则：

- `type` 必写，`scope` 可选（如 `feat(skill-x):`）；
- 描述一行、祈使句、小写开头、结尾不加句号；
- 破坏性变更：`feat!: …` 并在脚注写 `BREAKING CHANGE: …`。

示例：

```text
feat(skill-x): add validate script
docs: document README conventions
fix: prevent empty-output crash in generator
```

---

## 7. ADR（架构决策记录，可选）

当仓库出现**影响面较大**的约定/决策时，用 ADR 记录"为什么"，避免未来再次争论。参考 Nygard 模板，每份 ADR 一个文件、编号命名：

```markdown
# ADR-0001: <简短标题，以决策而非主题命名>

- 状态: Proposed | Accepted | Deprecated | Superseded by ADR-0002
- 日期: YYYY-MM-DD
- 决策人: <names>

## 背景 Context
驱动该决策的问题与冲突因素（价值中立）。

## 决定 Decision
用什么方案解决，主动语态一句。

## 后果 Consequences
变得更容易/更困难/新增的风险，正面负面并列。

## 备选方案 Alternatives
看过的其他方案及为何否决（每条一句即可）。
```

---

## 8. 设计文档（Design Doc，可选）

当某项改动存在多种合理方案、或影响跨模块/跨团队时，用设计文档在实现前对齐。**它是决策文档，不是实现手册**。核心三段式：

1. **问题层**：问题描述、目标（Goals）、非目标（Non-goals）、需求；
2. **功能层**：外部可观察的行为（与实现无关）；
3. **技术层**：架构、数据流、接口、存储。

必备区块参考：Context & Scope → Goals / Non-goals → Proposed Solution → Alternatives Considered → Cross-cutting concerns（安全/隐私/可观测）→ Rollout & Rollback。

---

## 9. `AGENTS.md`（面向 AI 代理的仓库指令，可选）

若仓库要给 AI 编码代理提供项目约定，可在根目录建 `AGENTS.md`（"写给机器的 README"），常见区块：

- Project Overview（2–3 句）；
- Tech Stack（精确定版）；
- Setup / Build / Test 命令（给精确命令，不靠猜）；
- Code Style、Testing、Architecture Notes；
- PR / Commit 约定（Conventional Commits）；
- Security、Things to Avoid（反模式）。

要点：**短、具体、非推理可得**；保留人类可见的 `README.md` 做总览，机器指令进 `AGENTS.md`，关注点分离；作为"活性文档"随项目持续迭代。