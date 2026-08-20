# <skill-name>

Concise summary of what this skill does and the problem it solves in 1–2 sentences.

## When to Use
Describe the trigger scenarios explicitly.

## Workflow
Step-by-step instructions the AI should follow.

## Constraints
Boundaries, prohibitions, and hard requirements.

## Dependencies
External tools, environments, or permissions required.

## Examples
Clean, reusable examples.

---

# Template

Frontmatter:

```markdown
---
name: "<skill-name>"
description: "Does X. Invoke when <scenario> happens or user asks for <keyword>."
---

# <Skill Title>

## Overview
One line: what problem this skill solves.

## When to Use
- Scenario A ...
- Keyword B ...

## Workflow
1. Step one ...
2. Step two ...

## Constraints
- Do not ...
- Must ...

## Dependencies
- Python >= 3.10, scripts/run.py

## Examples
```
... safe example ...
```
```

For the full standard, see [SKILL-AGENTS.md](SKILL-AGENTS.md).