---
name: "creative-mind"
description: "Use whenever the user asks for 创新, 新想法, 脑洞, 点子, 灵感, 创意, 想个新方案, 跳出思维定式, 打破常规, 不要套路, 别模板化, 要原创, 与众不同, 重新发明, or wants the model to break out of fixed thinking, generate its own new ideas, and create something novel instead of regurgitating the obvious answer. Runs a four-step creative engine: detach from the default/typical answer, diverge with techniques (SCAMPER, cross-domain fusion, counterfactual, first principles, reversal), converge by combining and selecting, then verify novelty with stereotype scanning. Produces multiple original candidates plus a structured idea sheet. Not for routine execution, factual Q&A, or tool usage."
---

# Creative Mind（通用创新引擎）

## Purpose / 用途

让模型**在自己的知识储备上造出属于自己的新东西**，而不是把训练数据里的"最常见答案"再吐一遍。本技能解决"AI 输出千篇一律、没有新思想"的痛点：用一套可执行的**发散-收敛引擎**，强制模型先跳出典型答案、再构造多个原创候选、最后自批判去套路，产出真正有自己想法的结果。

## 核心原理：先破典型性陷阱

> 详细解释见 [references/creative-workflow-zh.md](references/creative-workflow-zh.md)

模型直接回答 = 取分布里概率最高的那个"典型答案"（安全、熟悉、千篇一律）。破解口诀：

```
不要直接问"答案是什么"，先问"有哪些可能的答案" → 列出候选池 → 再选/组合/改造
```

本技能的工作流就是把这个口诀变成强制步骤。

## When to Use

- 用户要"新想法 / 脑洞 / 点子 / 灵感 / 创意 / 创新 / 想出个不一样的"；
- 用户说"跳出思维定式 / 打破常规 / 别按套路来 / 不要模板化 / 要原创 / 与众不同 / 重新发明";
- 任何需要**原创产出**的任务：标题、文案、产品方案、架构设计、故事、活动策划、商业模式……；
- 用户抱怨输出"太套路 / 太模板 / 像 AI 写的 / 没新意"时，用本技能重做。

## When NOT to Use

- 常规执行任务（改个 bug、跑个流程、查资料）——不需要发散；
- 事实问答（"法国的首都是哪"）——发散反而有害；
- 用户已明确给出方案、只要照做；
- 工具用法说明。

## Workflow（四步）

### Step 1 · 破固化（Detach）

动手前**先说出"典型答案"**，然后主动绕开它：

- 明确该任务大多数人/大多数模型会给出的"默认答案"是什么；
- 写下它的特征（主题、结构、套路）并标为"禁止直抄的模板"；
- 换一个初始视角或约束，让默认路径不可行。

> 提示：把"典型答案"写在草稿里，当作对照物，不直接产出它。

### Step 2 · 发散（Diverge）

生成**至少 3 个互不相同的候选**，而不是 1 个"最好的"答案。用技法库强制岔路：

```bash
python3 scripts/idea_scaffold.py --topic "<问题/主题>" --domain <domain> --techniques all
```

- 输出一组"发散脚手架"：跨域种子、SCAMPER 提问、反事实分支、第一性原理拆解、随机刺激；
- 不要用脚手架本身当答案，把它当**岔路口**，在每条岔路上继续想象；
- 候选之间必须**结构/角度不同**，而不是同一观点的三种措辞。

技法库速查（详见 [references/techniques-zh.md](references/techniques-zh.md)）：

| 技法 | 一句话 |
|------|--------|
| SCAMPER | 对现有物逐项替换/合并/改造/换用/删减/反转 |
| 跨域融合 | 把两个不相关领域强行组合 |
| 反事实 | 假设历史/条件改变，推演涟漪效应 |
| 第一性原理 | 丢弃假设，从底层重新搭建 |
| 反转/极端化 | 把某个属性反转或推到极端 |
| 类比迁移 | 借用冷门领域机制映射到本领域 |
| 随机刺激 | 随机词/图像作为种子强扭成方案 |

### Step 3 · 收敛（Converge）

从候选池里**选择 + 组合 + 打磨**：

- 挑 2 个最不相干的候选，强行杂交（往往产出最意外的组合）；
- 用三维度筛：**新颖度**（是否真的少见）/ **可行性**（能否落地）/ **价值**（是否值得）；
- 明确"为了谁、解决什么、凭什么不同"；
- 给最终方案一个具体的名字（命名强制聚焦）。

### Step 4 · 验新（Verify）

交付前做两层去套路：

1. **自批判 red-team**：以挑剔读者身份列出本方案"哪里还是套路/陈词滥调/无新意"，至少找 3 处，逐处改写；
2. **机械检测**：跑固化度扫描，量化剩余套路：

```bash
python3 scripts/stereotype_scan.py --text "<交付内容>" --type <text|idea|title|plan>
```

- 输出固化度评分（0-100）与命中清单；
- 评分偏高（≥60）或命中"高风险模板"→ 回到 Step 2 重发一轮；
- 不达标不交付。

## Output Spec

- **创意方案**：结构化 Markdown，含 `核心点子` / `为什么新` / `如何落地` / `风险与盲点`；
- **多候选**：Step 2 产出 ≥3 个候选时，用编号列表，每个候选一句话 + 一个独特角度；
- **验收句**：交付末尾固定一句"本方案与典型答案的差异是：______"；
- 可选 JSON 契约（供下游消费）：
```json
{ "idea": "…", "novelty": "…", "how": "…", "risk": "…", "technique": "…" }
```

## Failure Modes

- **发散不足**：3 个候选其实是同一观点的换皮——用技法库强制"角度必须不同"，并在候选旁标注所用技法；
- **直接输出脚手架**：把 idea_scaffold 的启发词当答案交差——脚手架只是岔路，必须继续想象；
- **收敛太早**：第一个"还行"的候选就定稿——Step 2 先凑满 ≥3 个候选再收敛；
- **自批判走形式**：red-team 列了 3 处但没真改写——要求"改写前后对比"；
- **把"新"当"怪"**：为创新而怪、脱离可行性——三维度里可行性与价值必须达标，不达标说明还需打磨而非放弃；
- **套路文风残留**：内容新但文风套（"综上所述""值得注意的是"）——stereotype_scan 会抓到，回去重写。

## Dependencies

- `python3`（仅标准库，离线可运行）；
- 两个脚本：`idea_scaffold.py`（发散脚手架）/ `stereotype_scan.py`（固化度检测）。

## References

- 四步工作流原理与"为什么"：[references/creative-workflow-zh.md](references/creative-workflow-zh.md)
- 创新技法库（12+ 技法 + 示例）：[references/techniques-zh.md](references/techniques-zh.md)
- AI 套路/陈词滥调负面清单：[references/anti-cliche-zh.md](references/anti-cliche-zh.md)

## Examples

**用户**：给智能水杯想 3 个不一样的卖点文案。

**Step 1 破固化**：典型答案 = "智能温控 / 喝水提醒 / APP 连接"，全部标记为不直抄。

**Step 2 发散**（`--techniques cross_domain,counterfactual,extreme`）：
- 候选 A（跨域：植物学）——像植物感知水分那样，"口渴度"可视化在杯身上；
- 候选 B（反事实：如果杯会聊天）——杯子在"你忙了一小时没喝水"时用不同角色语气提醒；
- 候选 C（极端化：杯子的另一半拿来干嘛）——杯盖变迷你盆栽/香薰座，喝水变成仪式。

**Step 3 收敛**：杂交 A+B → "会感知口渴、会提醒的杯子"，命名「渴感杯」。

**Step 4 验新**：stereotype_scan 命中 0 高风险模板，固化度 22；red-team 改写"智能"一词为"感知"后交付。
