# ai-rules · 规范 AI 做事的规矩

> 给 AI 一部"做事宪法"：分层守底线、讲道理能泛化、冲突有裁决、生效需确认、犯错会复盘、完成要证据。

## 这是什么

一个让 AI **始终守规矩地做事** 的技能包。不是单条规矩，而是一套体系：

- **默认全局生效**：AI 接任何任务都默记底线规矩（不造假/不越权/不作恶/不越界/不硬撑）与方法论规矩（先想后做/简单优先/精准改动/目标驱动/证据闭环/边界意识/自省复盘）；
- **规矩生成器**：你说"定个规矩"，它把你的需求/约束/红线合成为一份专属规矩清单；
- **逐条确认**：规矩生效前自检歧义、矛盾、可执行性，你拍板后执行；
- **合规自检**：交付前机械检查违规项，分级 `✅ ⚠️ 🚧`；
- **复盘进化**：失败后沉淀教训，规矩库随实战成长（跨会话记忆）。

## 安装与使用

技能包解压即用。目录结构：

```
ai-rules/
├── SKILL.md                     # 技能入口（模型加载）
├── README.md                    # 本文件
├── references/
│   ├── root-rules.md            # 第 1 层底线规矩详解
│   ├── general-rules.md         # 第 2 层方法论规矩详解
│   ├── rule-templates.md        # 第 3 层领域模板
│   ├── chain-of-command.md      # 冲突裁决指挥链
│   └── anti-rationalizations.md # AI 常用借口拆穿表
├── scripts/
│   ├── generate_rules.py        # 规矩生成器
│   ├── confirm_rules.py         # 逐条确认器
│   ├── check_compliance.py      # 合规自检器
│   └── retro_learn.py           # 复盘学习器
└── memory/
    └── rulebook.json            # 规矩库（含复盘沉淀）
```

## 快速上手

### 1. 直接让 AI 守规矩（最常用）

在对话中触发即可：

> "按规矩来 / 定个规矩 / 规范AI做事 / 约束一下"

AI 会自动内化默认规矩底座，并在任务中遵守。

### 2. 为新任务生成专属规矩

```bash
python3 scripts/generate_rules.py \
    --task "给管理员加批量导入用户功能" \
    --domain coding \
    --constraints "仅限 CSV" "导入失败要能回滚" \
    --redlines "不动生产数据库" \
    --output rules.md --json-out rules.json
```

生成 `rules.md`（给人读的三层规矩清单）和 `rules.json`（给脚本用）。

### 3. 逐条确认

```bash
python3 scripts/confirm_rules.py --json rules.json --task "批量导入" --goal "1 万行 3 秒内"
```

输出 `✅ 通过 / ⚠️ 需修订 / 🚧 阻塞` 三级；阻塞项必须修订。

### 4. 合规自检

```bash
python3 scripts/check_compliance.py --json rules.json \
    --text "交付说明" --evidence ./test.log --scope file_a.py
```

退出码 `0` 通过、`1` 警告、`2` 阻塞。

### 5. 复盘沉淀

```bash
python3 scripts/retro_learn.py \
    --note "导入超时：没先确认量级" \
    --violated G1 G4 \
    --rule "大数据量先确认量级与复杂度" \
    --why "O(n^2) 在 10 万行不可用" \
    --rulebook memory/rulebook.json
```

## 支持的领域模板

| domain | 领域 | 适用 |
|--------|------|------|
| `coding` | 编码开发 | 改代码、加功能、修 bug |
| `writing` | 写作润色 | 改写、报告、公众号 |
| `analysis` | 分析报告 | 数据分析、结论推断 |
| `research` | 检索调研 | 查资料、写调研 |
| `data` | 数据处理 | 清洗、转换、批处理 |
| `communication` | 消息沟通 | 回复、代拟消息 |

## 与其它技能的关系

- 与 [de-ai-flavor](../de-ai-flavor/README.md)（去 AI 味）：互补——本技能管"怎么做事"，de-ai-flavor 管"怎么写东西"；
- 通用底座：可搭配任何其它技能使用，作为默认行为约束。

## 设计依据

- Karpathy 四诫（think/simplicity/surgical/goal-driven）
- OpenAI Model Spec（Chain of Command + 决策大纲）
- Anthropic 2026 宪法（reason-based 对齐 + 四层优先级）
- Agent Charters（逐条确认机制）
- SafeHarbor / AGrail（自进化记忆护栏）
- Harness 证据闭环

## 限制

- 脚本做的是**机械检查**（关键词/结构），语义层面的合规判断仍需模型结合 [references/anti-rationalizations.md](references/anti-rationalizations.md) 自查；
- `memory/rulebook.json` 是跨会话持久化的关键，删除即丢失复盘沉淀；
- 领域模板为内置六类，新领域可自行在 `scripts/generate_rules.py` 的 `DOMAIN_TEMPLATES` 中扩展。
