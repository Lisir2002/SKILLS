# <skill-name>

Concise summary of what this skill does and the problem it solves in 1–2 sentences.

---

## frontmatter（将上方占位替换为以下内容）

```markdown
---
name: "<skill-name>"        # kebab-case, = 目录名, ≤64 字符, 不含 claude/anthropic
description: "Does X. Use when <scenario> or user asks for <literal trigger>. Not for <anti-trigger>."
                            # 英文、单行、≤1024 字符、前 ~120 字符含触发词、
                            # 第三人称、含"做什么+何时用+反触发"、避免冒号与块标量符
---
```

---

## 推荐正文结构（强小标题 + 短段落）

# <Skill Title>

## Purpose（一段说明解决的痛点）
一句话/一小段。

## When to Use（触发场景）
- 场景 A …
- 关键词 B …

## When NOT to Use（反触发，勿省略）
- 相近技能才做的…

## Workflow（带具体命令的编号步骤）
1. …
2. …（需要精确时用 `scripts/` 脚本，不要用长文字复述机器能确定执行的步骤）

## Output Spec（"完成"长什么样）
输出结构、验收标准。

## Failure Modes（常见坑）
- 已踩过的坑…

## Dependencies
- 环境/工具/权限，如 `Python >= 3.10`、`scripts/run.py`

## References / Scripts
指向 `references/`（一层深）与 `scripts/`。

## Examples
干净、可直接复用的示例（不含密钥/真实数据）。

---

> 完整规范见 [SKILL-AGENTS.md](SKILL-AGENTS.md)；各类文档写法见 [DOC-WRITING-GUIDE.md](DOC-WRITING-GUIDE.md)。