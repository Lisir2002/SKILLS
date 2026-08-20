# SKILL 技能包设计与规范标准（SKILL Design & Packaging Standard）

> 本文档是本仓库所有技能包统一遵循的**规范性设计文档**。
> 它定义了从需求、设计、实现、审核到打包发布的完整流程与硬性规范。
> 规范化依据：Agent Skills 开放标准（agentskills.io / Anthropic skills）、主流 AI 工具技能约定、行业文档规范（Keep a Changelog、Conventional Commits 等）。
> 配套文档：[SKILL-TEMPLATE.md](SKILL-TEMPLATE.md)（模板）、[DOC-WRITING-GUIDE.md](DOC-WRITING-GUIDE.md)（各类型文档写法）。
> 凡与本规范冲突的内容，以本文档为准。

---

## 1. 目标与范围

本规范约束仓库内**每一个 AI Skill 技能包**的组成、格式、质量与发布方式，保证：

- 结构统一、可被主流 AI 工具（Trae / Claude Code / Cursor / Codex 等）正确识别与加载；
- 技能触发准确（description 是唯一的路由/触发机制）；
- 行为稳定、可复用、不泄露敏感信息；
- 依赖与脚本可复现、可离线运行；
- 审核、迭代、版本管理清晰可追溯。

适用对象：`skills/<skill-name>/` 源码目录、`packages/*.zip` 打包产物及配套文档。

---

## 2. 仓库结构

```
SKILLS/
├── README.md                          # 说明文档（仓库总览 + 技能索引）
├── docs/
│   ├── SKILL-AGENTS.md                # 本文档（技能设计与打包规范）
│   ├── SKILL-TEMPLATE.md              # SKILL.md 推荐模板
│   └── DOC-WRITING-GUIDE.md           # 各类型文档规范写法（README/CHANGELOG/提交等）
├── skills/
│   └── <skill-name>/                  # 技能源码目录（规范见第 3 节）
│       ├── SKILL.md                   # 技能定义（必需）
│       ├── evals/evals.json           # 触发与质量用例（推荐）
│       ├── references/                # 可选：按需加载的长文档
│       ├── scripts/                   # 可选：可执行脚本
│       ├── assets/                    # 可选：输出用模板/资源
│       └── README.md                  # 技能说明（用户向）
├── packages/                          # 打包产物存放目录
│   └── <skill-name>.zip               # 每个技能一个压缩包
└── CHANGELOG.md                       # 变更记录（Keep a Changelog 约定）
```

---

## 3. 技能源码结构规范

技能是一个**目录**（而非单个 md 文件），目录名与 `name` 完全一致。仅创建实际需要的目录，不保留空脚手架。

| 路径 | 必需 | 说明 |
|------|------|------|
| `SKILL.md` | ✅ | 技能入口：frontmatter + 指令正文，见第 4 节 |
| `README.md` | ✅ | 用户向说明：用途、安装、用法、示例，见 DOC-WRITING-GUIDE |
| `scripts/` | ⬜ | 确定性代码（校验/脚手架/解析）。步骤必须精确时优先脚本 |
| `references/` | ⬜ | 按需加载的长文档、模式、领域知识（仅当 SKILL.md 引用它时载入） |
| `assets/` | ⬜ | 用于**输出**的模板/图标/字体，不读入上下文 |
| `evals/evals.json` | ⬜ | 触发与质量测试用例 |

**加载纪律（渐进式披露，Progressive Disclosure）**：会话开始时模型**只看到** `name` + `description`；正文仅在技能被触发后才加载。因此：
- 长参考材料放 `references/`，正文里只需**一层深**链接指向它；
- `description` 之外的文件不进触发判断，`description` 承载全部"何时用"信息。

---

## 4. `SKILL.md` 规范

### 4.1 命名（`name`）

`name` 必须满足 Agent Skills 校验规则：

- `kebab-case`：正则 `^[a-z0-9]+(-[a-z0-9]+)*$`，≤ 64 字符；
- **必须与目录名/文件夹名完全一致**；
- 禁止前后连字符、禁止连续连字符 `--`；
- 不得包含 `claude` / `anthropic`（避免生态保留字）；
- 见名知义，不与通用命令/工具冲突。

### 4.2 frontmatter

`SKILL.md` 第 1 行起即为 YAML 块，**只含必需的 `name` 和 `description`**，可加少量可选字段。

```markdown
---
name: "my-skill-name"
description: "Does X. Use when the user asks for Y or mentions Z. Not for W."
---
```

**`description` —— 全文最重要的字段。** 它是技能的路由 API：触发判断时模型只读它（约 30–100 token）。规则：

1. **英文**书写（跨工具可识别、匹配稳定）；
2. **单物理行**：不要用 YAML 块标量符（`>-`、`|-`、`>`、`|`）；长度上限 **1024 字符**，触发关键词尽量落在**前 120 字符**内（过长会被路由截断），**150–400 字符为最佳区间**；
3. **第三人称**撰写（语句会被注入系统提示）；不要用 "I can…" / "You can use…"；
4. 结构公式 = **做什么 + 何时用（含用户真实会说的触发词）+ 不做什么（反向排除）**：

> Generates unit tests for the active file. Use when the user asks to "write tests", "add coverage", or "make a test file". Not for fixing failing tests or reviewing existing ones.

5. **触发点前载**：具体触发信号（文件类型、命令、动词同义词）放前面，越具体越靠前；
6. **稍微主动**：模型默认偏"少触发"，可用 "Use whenever…" 等指令式措辞对抗漏触发；**避免**空泛词（scalable/flexible）、避免副词 "explicitly"（不同模型解析不一致）；
7. **保留负面触发**：当存在相近姊妹技能时，用 "Not for …" + 2–3 个短名词短语排除；若需 5+ 条排除，说明范围过宽，应拆分技能；
8. **只编码模型会做错的部分**：不要编写与模型原生能力重复的技能（如泛泛的提交信息、泛泛 code review），否则约一半概率不触发。编码"它不知道/会做错"的领域知识才有效。

### 4.3 可选 frontmatter 字段

仅 `name` / `description` 为必需；按需添加（保持 frontmatter ≤ ~20 行）：

| 字段 | 用途 |
|------|------|
| `argument-hint` | `/skill` 自动补全提示，如 `[file] [format]` |
| `license` | 使用许可，如 `Apache-2.0` |
| `disable-model-invocation: true` | 仅允许 `/skill` 手动触发（副作用类技能：部署/发布） |
| `user-invocable: false` | 后台知识技能，从 `/` 菜单隐藏 |
| `allowed-tools` | 最小权限工具白名单（尽力而为，非安全边界） |
| `context: fork` + `agent` | 在子代理中隔离运行 |

### 4.4 正文结构

推荐**强 H2/H3 结构 + 短段落**，避免长文本墙：

```markdown
# <Skill 标题>

## Purpose / 用途             # 一段说明解决的痛点
## When to Use / 何时使用      # 触发场景
## When NOT to Use / 反触发     # 最重要且作者最常省略的段落
## Workflow / 工作流程          # 带具体命令的编号步骤
## Output Spec / 输出规范       # "完成"长什么样（产出结构）
## Failure Modes / 失败模式     # 常见坑与已踩过的坑（高价值内容）
## Dependencies / 依赖          # 外部工具/环境/权限
## References / Scripts        # 指向 references/ 与 scripts/ 的指针（一层深）
## Examples / 示例             # 干净可复用示例
```

要求：

- 指令**具体、可执行**，落实为可执行命令，而非空泛描述；
- 每步明确输入/输出与验收标准，减少 AI 自由发挥；
- **脚本 vs 散文**：需要精确时用脚本，不要用冗长文字描述一个脚本就能确定执行的步骤；脚本代码不进入上下文，只有输出进入。

---

## 5. 内容安全与隐私规范（强制）

任何技能内容**不得包含**：

- 用户私密信息、凭据、令牌、 Cookie、内部 URL、示例密钥（含 `sk_test_…`）；
- 原始用户数据 / 数据集样本 / 日志 / 查询结果；
- 一次性任务进度、临时文件路径、个别分析结论。

一律使用干净的示例与泛化占位符。技能只承载**可复用的工作流指令与约定**。

---

## 6. 脚本规范

### 6.1 存放与入口
- 放 `scripts/`；
- 提供清晰入口（如 `scripts/run.sh`、`main.py`），并在 `SKILL.md` / `README.md` 说明调用方式与参数。

### 6.2 语言与环境
- 明确标注依赖（Python/Node 版本、系统工具）；
- 提供 `requirements.txt` / `package.json` 等依赖声明；
- 优先**离线可复现**。

### 6.3 健壮性
- 使用非交互模式（`CI=true`、`-y`、`--no-input`）；
- 显式校验输入参数并输出友好错误；
- 输出结构稳定（JSON/表格/固定目录），便于 AI 解析；
- 涉及网络优先走 `HTTP_PROXY`/`HTTPS_PROXY` 代理环境变量（沙箱直连 TCP 可能失败）。

---

## 7. 校验与质量检查清单（打包前必查）

可使用社区校验工具辅助（`skilllint`、Agent Skills 的 `skills-ref validate`），但不能替代人工检查。

- [ ] `name` 为 kebab-case、≤64 字符、与目录名一致、无保留词；
- [ ] `description`：英文、单行、≤1024 字符、前 120 字含触发词、第三人称、含"做什么+何时用+反触发"、无冒号引发 YAML 引号、无块标量符；
- [ ] `SKILL.md` 具备 Purpose / When to Use / When NOT to Use / Workflow / Output Spec / Failure Modes / Dependencies / Examples；
- [ ] 无敏感信息、无绝对内部路径、无真实/示例密钥；
- [ ] 脚本含入口说明与依赖声明，能非交互运行；
- [ ] `README.md` 说明用途、安装、用法、示例；
- [ ] 干净环境本地自测跑通核心路径；
- [ ] 目录结构符合第 2 / 3 节；
- [ ] 若含 `references/`，确认正文仅一层深引用。

---

## 8. 打包与发布规范

- 每个技能对应**一个 `zip`**，命名 `<skill-name>.zip`；
- zip 内**根目录为 `skills/<skill-name>/`**（保持相对路径一致，解压即用）；
- 生成命令：

```bash
cd /path/to/SKILLS
zip -r packages/<skill-name>.zip skills/<skill-name>
```

- 发布到 `packages/`，并在 `README.md` 技能索引登记；变更同步更新 `CHANGELOG.md`。

---

## 9. 审核与提交流程

1. **需求**：用户提出技能需求；
2. **调研**：联网检索同类技能/最佳实践，形成强化设计；
3. **实现**：按本规范编写完整技能包（SKILL.md、脚本、说明、资源、可选 evals）；
4. **评审**：交用户拍板确认，必要时迭代修改；
5. **打包**：`zip` 打包至 `packages/`；
6. **发布**：推送 commit 到 `main` 分支。

> 未经用户确认，不得推送最终技能包。

---

## 10. 版本与变更

- 使用 `git` 追踪变更；重要改动记录于 `CHANGELOG.md`（Keep a Changelog 约定：Added / Changed / Deprecated / Removed / Fixed / Security）；
- 提交信息遵循 Conventional Commits（`feat:` / `fix:` / `docs:` / `chore:` 等），见 [DOC-WRITING-GUIDE.md](DOC-WRITING-GUIDE.md)。

---

## 11. 参考来源（Best Practices 依据）

- Agent Skills 开放标准：agentskills.io / github.com/agentskills/agentskills
- Anthropic 技能作者最佳实践（docs.anthropic.com / anthropics/skills）
- Anthropic Claude Code Skills 文档（frontmatter 参考）
- Keep a Changelog、Conventional Commits、Standard Readme、makeareadme
- 设计文档 / ADR 社区模板（Google / Stripe / Nygard）