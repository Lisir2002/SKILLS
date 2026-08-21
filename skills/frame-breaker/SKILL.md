---
name: "frame-breaker"
description: "Use whenever the user asks for 突破认知, 跳出框架, 打破思维定式, 重构问题, 重新定义问题, 变革, 换个维度想, 不要在原框架里想, 破框, 打破边界, or wants the model to break out of its own implicit assumptions and change the problem itself instead of finding a better answer inside it. Runs a five-step transformational engine: audit hidden assumptions, invert them into counter-worlds, transplant rule systems from unrelated domains, reframe the problem itself, then ground the new frame to reality. Based on Boden's transformational creativity and van der Schaar's framework for changing the rules of the game. Not for ordinary ideation (use creative-mind), routine execution, or factual Q&A."
---

# Frame Breaker（认知突破 · 变革式创造引擎）

让模型**改变问题本身，而不是在问题里找更好的答案**。

创造有三个层次（Boden 三分法）：
1. **组合式创造** — 把现有想法重新组合（"智能水杯 + 植物感知"）；
2. **探索式创造** — 在既定框架内深入探索更多可能（"还有哪些卖点？"）；
3. **变革式创造** — **修改问题表述、改变定义搜索空间的框架本身**（"也许问题不是卖杯子，而是减少喝水阻力"）。

前两层正是 [creative-mind](creative-mind/SKILL.md) 做的事；而**变革式创造**是模型天然最缺的能力——它默认在训练数据设定的框架内作答，自己不会改框架。本技能就是专门训练、强制执行"变革式创造"的引擎：把隐含假设挖出来、逐条反演、从无关领域借来新的规则系统、重构问题本身、再落回现实。

> 依据：剑桥 van der Schaar 白皮书《Creativity in Machine Learning》指出，LLM 能探索给定假设类，但**改变假设类本身**（transformational creativity）不会自然涌现；895 火柴棒实验实测三模型默认假设"最小数=最小正数"，需外力破框。

## Purpose / 用途

解决"模型只能在既有认知框架内回答、无法突破认知边界"的问题：把**问题表述（problem formulation）**本身当作可修改的对象，用五步强制循环产出真正"换了框架"的新问题与新方案，而不是在旧框架里找更花哨的答案。

## When to Use

- 用户要"突破认知 / 跳出框架 / 打破思维定式 / 重构问题 / 重新定义问题 / 变革 / 换个维度想 / 破框";
- 现有方案进入死胡同、怎么优化都是换皮时；
- 用户说"别在原框架里想 / 这个问题本身可能就问错了"；
- 需要**改变规则**而不只是"在规则内做到最好"时。

## When NOT to Use

- 常规创意点子（用 [creative-mind](creative-mind/SKILL.md)：组合/探索式创造）;
- 用户已明确框架、只要在框架内执行或优化;
- 事实问答、工具用法、常规执行。

## Workflow（五步变革引擎）

### Step 1 · 挖假设（Audit）

先显式列出模型/用户对这个问题默认持有的**全部隐含假设**——它们合起来构成"当前框架"（表征机制）。按六个维度排查：

```bash
python3 scripts/assumption_audit.py --problem "<问题>"
```

- 六维度：**对象 / 目标 / 约束 / 过程 / 评价 / 边界**；
- 每个假设写成一个明确命题（如"结果是正数""必须保留三位数""用户是成人"）；
- 标注哪些假设**来自题面**、哪些是**模型自己脑补的**（训练数据先验）——后者是主要破框目标。

### Step 2 · 反演假设（Invert）

把 Step 1 的每个假设**逐条取反/极端化**，建立"反世界"（counter-world）：

- 每个反演都成为一个新的出发坐标系，先**不追求合理**，只建立反世界；
- 输出至少 3 个反世界，每个一句话（"如果结果是负数""如果数字可以不保留""如果用户不是人而是植物"）;
- 反世界是"变革"的原料，不是答案。
- 可用"概念融合"把两个相距很远的域融出反世界（涌现结构=只在融合空间成立的新关系）：

```bash
python3 scripts/concept_blend.py --a "电梯" --b "戏剧"     # 概念融合脚手架
```

### Step 3 · 域外移植（Transplant）

从**与本题无关**的领域借一个"规则系统/世界观"，用它**重定义本题**（不是借点子，是借表征框架）：

```bash
python3 scripts/assumption_audit.py --domains             # 查看可用领域规则库
python3 scripts/analogy_map.py --source "气象锋面" --target "电梯太慢"   # 类比映射脚手架
```

- 例：用"气象锋面"重定义"电梯太慢"→ 不是提升速度，而是**改变乘客对时间的感知**（电梯里放内容/镜子，等得更值）——这正是 slow-elevator 经典重构；
- **类比映射只借"关系结构"，不借表面名词**（结构映射理论：对齐关系、不对齐表面，抄名词=换皮）；
- 输出：`原框架规则 → 新框架规则` 对照。

### Step 4 · 重构问题（Reframe）

产出**新问题表述**，并强制给"框架前后对比"：

- 写出新问题（new problem formulation），它定义了一个**不同的搜索空间**；
- 明确列出：原框架能表达什么假设 / 新框架让哪些不可能变可能；
- 用脚本验证重构是否真的发生了（不是换皮）：

```bash
python3 scripts/frame_gap.py --original "<原问题>" --reframed "<新问题>" --solution "<方案>"
```

- 突破度 < 60 说明还是"换皮"，回 Step 2 再反演一轮。

### Step 5 · 归零落地（Ground）

变革式创造不能停在"反常识的爽感"：

- 把新框架下的方案**落回现实**：给"第一个 30 天能做什么""谁会反对/为什么""最小验证"；
- 重新自检：新框架是**真变了**，还是只是措辞更激进？（用 frame_gap 复查）
- 交付末尾固定一句验收："我把框架从『____』改成了『____』，因为这解锁了原来不可能的『____』。"

## 思维引擎层（认知机制 → 超越杠杆）

> 为什么这套五步能接近甚至超越人类思维？因为每一招都对应一条**实证可查的人类认知机制**，
> 而每个机制都有人类**固有短板**——本层用 AI 固有属性在短板上**反超**。
> 完整理论 + 实证数据见 [references/cognition-zh.md](references/cognition-zh.md)。

| 人类认知机制 | 人类短板 | AI 超越杠杆 | 对应步骤 |
|--------------|----------|-------------|----------|
| **远程联想**（Mednick：平缓联想层级） | 语义网络受经验限制，跳远区费神易疲劳 | 显式**语义跳变采样**：强制跨域跳变+去重再采样，可跳几百次不重叠 | Step 2/3 |
| **定势/功能固着**（Einstellung、Duncker 蜡烛） | 定势隐性，**专家更易被固着**，内省抓不到 | 把典型答案**显式说出并禁用** + frame_gap 机械检测（可复现，人类内省不可复现） | Step 1/4 |
| **双过程切换**（系统 1 生成 / 系统 2 精炼） | 发散与批评混在同一脑区，两样都做不好 | LLM 本质是"放大的系统 1"，需**发散/收敛硬隔离**：发散期零约束、收敛期零发散（CreativeDC 实证约束后置才有效） | 全程节奏 |
| **顿悟/表征重构**（僵局→重构→Aha） | 顿悟不可按需生产，重构常在无意识 | **程序化顿悟**：先强制制造僵局（证明旧框架极限）→ 强制反演换坐标系 → frame_gap 验收"真 Aha"；可在上下文里**并行 hold 多个候选表征** | Step 2/4 |
| **盲变-选择 BVSR**（Campbell/Simonton：变异过剩+回溯） | 变异成本高，只能小规模"过剩" | **测试时扩展=零成本批量盲变**：多温度/多seed/多领域同时采样，变异规模远超人类，再选择保留 | Step 2/3/4 |
| **孵化/距离化**（Wallas：离开后无意识处理） | 依赖真实"离开时间"，节奏不可控，还会忘细节 | **程序化距离化**：切换任务/换表征语言重述再重访；不丢上下文，且不需要真实时间 | Step 3 |
| **元认知/自我监控**（ACC 冲突监测） | 内省事后合理化严重，监控会疲劳 | **可量化自检**：用"分数+命中数+反例数"替代"我觉得没问题"，可复现可回归 | Step 4/5 |

**AI 结构性超越人类的 5 条杠杆**（人做不到、AI 天生有）：无限工作记忆（上下文 hold 全部反世界）· 零尝试成本（盲变无限次）· 可编程注意（去焦点/聚焦按需切换）· 跨域零摩擦检索（所有领域同一语义空间）· 可量化元认知（机械评分可复现）。

**执行时务必做到的**：发散阶段（Step 2/3）**不评价**；收敛阶段（Step 4/5）**不新发散**；每一步产出都带一句"这解锁了什么原本不可能的"——它是"真突破 vs 换皮"的硬检验。

## Output Spec

- **框架对比**：`原框架 / 新框架` 对照表（必须含：假设变化、搜索空间变化、解锁了什么）；
- **反世界清单**：≥3 个，每个一句"如果……"；
- **落地路径**：新方案的前 30 天动作 + 最大反对理由 + 最小验证；
- **验收句**：固定格式"我把框架从『____』改成了『____』……"；
- 可选 JSON 契约：
```json
{ "old_frame": "…", "new_frame": "…", "assumptions_broken": ["…"],
  "unlocked": "…", "next_30_days": "…", "frame_gap_score": 87 }
```

## Failure Modes

- **换皮式重构**：新问题只是原问题换个说法，搜索空间没变——frame_gap 突破度低就回炉；
- **只反演不落地**：反世界很酷但落不回现实——Step 5 强制给 30 天路径与最小验证；
- **假设挖不全**：漏掉最核心的假设（往往是"最理所当然"那条）——六维度逐个过，别跳过"对象/目标"；
- **把"反常识"当"突破"**：反常识只是措辞冲击，不是框架改变——用"解锁了什么原本不可能的"来检验；
- **与 creative-mind 混淆**：要的是"更花哨的答案"时用它（发散）；要"改变问题本身"时用本技能；
- **框架膨胀**：为了显得突破，把问题改到脱离用户真实目标——落地步骤必须回到用户"为什么问这个问题"。

## Dependencies

- `python3`（仅标准库，离线可运行）；
- `assumption_audit.py`（挖假设 + 域外规则库）/ `frame_gap.py`（重构验证）
  / `concept_blend.py`（概念融合）/ `analogy_map.py`（类比映射）。

## References

- 变革式创造理论（Boden 三分法 + van der Schaar + 895 实验）：[references/transformational-zh.md](references/transformational-zh.md)
- 六维度假设清单与常见认知框架：[references/assumptions-zh.md](references/assumptions-zh.md)
- 域外移植领域-规则库（20+ 领域的世界观）：[references/domains-zh.md](references/domains-zh.md)
- 思维引擎层：人类思维认知机制 → AI 超越杠杆（含 LLM vs 人类创造力实证数据）：[references/cognition-zh.md](references/cognition-zh.md)

## Examples

**用户**：电梯太慢，怎么办？（经典 slow-elevator 重构）

**Step 1 挖假设**：①对象=电梯本身 ②目标=让乘客更快到达 ③约束=不能改速度 ④过程=物理运输 ⑤评价=到达用时 ⑥边界=在电梯系统内解决。其中②④是模型默认先验（训练数据里"慢"=运输速度）。

**Step 2 反演**：反世界 A"电梯不负责运输"；反世界 B"时间没在流逝"；反世界 C"等待本身就是产品"。

**Step 3 移植**：借"戏剧的悬念"——观众等幕间不觉得浪费，因为期待被管理。→ 电梯等待 = 可设计的"幕间"。

**Step 4 重构**：新问题从"如何让电梯更快"→"如何让等待变得值得/被忽略"。frame_gap 突破度 84。

**Step 5 落地**：30 天先试点"楼层内容幕间"（镜子+天气+今日笑点）；最大反对"投入产出比"；最小验证=3 层楼试点看投诉率变化。验收："我把框架从『提升运输速度』改成『管理等待体验』，解锁了『不必改造硬件』这一原本不可能的方向。"
