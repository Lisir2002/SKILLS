# SKILL 技能包设计与规范标准（SKILL Design & Packaging Standard）

> 本文档是本仓库所有技能包统一遵循的**规范性设计文档**。
> 它定义了从需求、设计、实现、审核到打包发布的完整流程与硬性规范。
> 凡与本规范冲突的内容，以本文档为准。

---

## 1. 目标与范围

本规范用于约束仓库内**每一个 AI Skill 技能包**的组成、格式、质量与发布方式，保证：

- 结构统一、可被主流 AI 工具（Trae / Claude / Cursor 等）正确识别与加载；
- 技能行为稳定、可复用、不泄露敏感信息；
- 依赖与脚本可复现、可离线运行；
- 审核、迭代、版本管理清晰可追溯。

适用对象：本仓库下的所有 `skills/<skill-name>/` 源码目录、`packages/*.zip` 打包产物及配套文档。

---

## 2. 仓库结构

```
SKILLS/
├── README.md                        # 说明文档（仓库总览 + 技能索引）
├── docs/
│   ├── SKILL-DESIGN-STANDARD.md     # 本文档（规范性设计标准）
│   └── SKILL-TEMPLATE.md            # SKILL.md 推荐模板
├── skills/
│   └── <skill-name>/                # 技能源码目录（规范见第 3 节）
│       ├── SKILL.md                 # 技能定义（必需）
│       ├── README.md                # 技能说明（必需）
│       ├── scripts/                 # 可选：可执行脚本
│       ├── assets/                  # 可选：资源文件（示例/模板/图标等）
│       └── ...其他文件
├── packages/                        # 打包产物存放目录
│   └── <skill-name>.zip             # 每个技能一个压缩包
└── CHANGELOG.md                     # 仓库/技能变更记录
```

---

## 3. 技能源码结构规范

每个技能以独立目录 `skills/<skill-name>/` 管理，**发布即 `zip` 打包**。

| 路径 | 必需 | 说明 |
|------|------|------|
| `SKILL.md` | ✅ | 技能核心定义文件，见第 4 节 |
| `README.md` | ✅ | 用户向说明：用途、安装、用法、示例 |
| `scripts/` | ⬜ | 技能运行时所需脚本（见第 6 节） |
| `assets/` | ⬜ | 静态资源：示例输入、字典、规则文件、配色、模板等 |

---

## 4. `SKILL.md` 规范

### 4.1 命名（`<skill-name>`）

- 使用 `kebab-case`（小写字母 + 连字符），如 `code-reviewer`、`voice-to-text`；
- 名称需**见名知义**，能反映其核心能力；
- 不与通用命令/工具名冲突。

### 4.2 frontmatter

```markdown
---
name: "<skill-name>"
description: "<one-liner description>"
---
```

`description` 强制要求：

1. 用 **英文** 编写（便于 AI 工具识别与触发匹配）；
2. 必须同时包含两点：
   - **功能**：技能做什么；
   - **触发条件**：何时调用（when to invoke）。
3. 建议 ≤ 200 字符，太长会被截断影响匹配。

推荐句式：

> "Does X. Invoke when <scenario> happens or user asks for <keyword>."

### 4.3 正文结构

```markdown
# <Skill 标题>

## 简介 / Overview           # 一句话说明该技能解决什么问题
## 使用场景 / When to Use    # 明确指出触发时机
## 工作流程 / Workflow       # 分步指令，AI 执行逻辑
## 规则与约束 / Constraints  # 边界、禁忌、硬性要求
## 依赖 / Dependencies       # 需要的外部工具/环境/权限
## 示例 / Examples           # 可复用的安全示例
```

要求：

- 指令需**具体、可执行**，而非空泛描述；
- 关键判断给出一致标准，减少 AI 的自由发挥空间；
- 涉及脚本时，正文明确调用入口与参数。

---

## 5. 内容安全与隐私规范（强制）

任何技能内容 **不得包含**：

- 用户私密信息、凭据、令牌、Cookie、内部 URL；
- 原始用户数据 / 数据集样本 / 日志 / 查询结果；
- 一次性任务进度、临时文件路径、个别分析结论。

一律使用干净的示例与泛化占位符。技能应只承载**可复用的工作流指令与约定**。

---

## 6. 脚本规范

### 6.1 存放与入口
- 一律放 `scripts/` 目录；
- 提供清晰入口（如 `scripts/run.sh`、`main.py`），并在 `SKILL.md` 与 `README.md` 中说明调用方式。

### 6.2 语言与环境
- 明确标注依赖环境（Python 版本、Node 版本、系统工具）；
- 提供 `requirements.txt` / `package.json` / `Dockerfile` 等依赖声明（如适用）；
- 优先保证 **离线可复现**。

### 6.3 健壮性
- 使用非交互模式（`CI=true`、`-y`、`--no-input`）以适配远程沙箱；
- 显式校验输入参数并给出友好错误；
- 输出结构稳定（JSON/表格/固定目录），便于 AI 解析；
- 涉及网络优先走 `HTTP_PROXY`/`HTTPS_PROXY` 代理环境变量（沙箱直连 TCP 可能失败）。

---

## 7. 质量检查清单（打包前必查）

- [ ] `description` 为英文，含功能 + 触发条件，≤200 字符；
- [ ] `SKILL.md` 具备 Overview / When to Use / Workflow / Constraints / Dependencies / Examples；
- [ ] 无敏感信息、无绝对内部路径、无真实凭据；
- [ ] 脚本含入口说明与依赖声明，能非交互运行；
- [ ] `README.md` 说明用途、安装、用法、示例；
- [ ] 在干净环境本地自测一次（能跑通核心路径）；
- [ ] 目录符合第 2 / 3 节结构。

---

## 8. 打包与发布规范

- 每个技能对应**一个 `zip`**，命名 `<skill-name>.zip`；
- zip 内**根目录为 `skills/<skill-name>/`**（保持相对路径一致，便于解压即用）；
- 生成命令：

```bash
cd /path/to/SKILLS
zip -r packages/<skill-name>.zip skills/<skill-name>
```

- 发布到 `packages/` 目录，并在 `README.md` 的技能索引表登记；变更同步更新 `CHANGELOG.md`。

---

## 9. 审核与提交流程

1. **需求**：用户提出某个技能需求；
2. **调研**：联网检索同类技能/最佳实践，形成强化设计；
3. **实现**：按本规范编写完整技能包；
4. **评审**：交用户拍板确认，必要时迭代修改；
5. **打包**：`zip` 打包至 `packages/`；
6. **发布**：推送 commit 到 `main` 分支。

> 未经用户确认，不得推送最终包。

---

## 10. 版本与变更

- 使用 `git` 追踪变更；重要改动在 `CHANGELOG.md` 记录；
- 语义化简要标注（新增 / 修复 / 增强）。