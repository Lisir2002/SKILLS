#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""idea_scaffold.py —— 发散脚手架生成器（creative-mind 技能 Step 2）

作用：
  给定问题/主题，用多种创新技法生成一组「岔路口」式启发（跨域种子、
  SCAMPER 提问、反事实分支、第一性原理拆解、反转、极端化、随机刺激、
  口述采样等）。脚手架本身不是答案，而是让模型跳出默认路径、继续想象
  出真正原创候选的起点。

用法（纯标准库，离线可运行）：
  python3 idea_scaffold.py --topic "智能水杯卖点" --domain product --techniques all
  python3 idea_scaffold.py --topic "周末团建活动" --domain event --techniques cross_domain,reversal --seed 42 --json

依赖：仅 Python 标准库。无网络、无第三方包。
"""
import argparse
import json
import random
import sys

# ---------------------------------------------------------------- 词库
# 跨域融合：随机抽取的两个「无关领域」及其机制提示
DOMAINS = [
    ("植物学", "植物感知缺水、向光性、根系网络"),
    ("蜂群", "分布式决策、信息素路径、集体智慧"),
    ("气象学", "气压差、锋面相遇、蝴蝶效应"),
    ("音乐", "节奏、和声冲突与解决、留白休止"),
    ("考古学", "地层分层、文物修复、断代"),
    ("游戏", "关卡难度曲线、奖励反馈环、成就系统"),
    ("军事", "侦察-决策-执行回路、佯攻、情报不对称"),
    ("宗教仪式", "仪式感、禁忌、敬畏与重复"),
    ("农业", "轮作、嫁接、温室控制、土壤菌群"),
    ("太空工程", "冗余设计、轨道转移、资源循环"),
    ("金融", "对冲、期权、复利、风险定价"),
    ("医学", "免疫记忆、对症下药、预防优于治疗"),
    ("戏剧", "三幕结构、戏剧冲突、悬念钩子"),
    ("侦探推理", "不在场证明、反转真凶、线索埋设"),
    ("生态学", "共生、天敌制衡、生态位错开"),
    ("语言学", "词源演化、方言变体、新词造词法"),
    ("烹饪", "火候层次、味觉平衡、时令食材"),
    ("体育竞技", "攻防转换、战术板、体能分配"),
    ("心理学", "心流、锚定效应、损失厌恶"),
    ("科幻设定", "时间循环、平行宇宙、意识上传"),
]

# 随机刺激种子：供 cross-domain 之外单独使用的「无意义但可强扭」的词
STIMULI = [
    "回声", "仙人掌", "潮汐", "钥匙", "折纸", "钟摆", "苔藓", "蒸汽",
    "回声定位", "沙漏", "磁铁", "榫卯", "风筝", "水滴石穿", "候鸟", "灯塔",
]

# 第一性原理拆解：把问题还原到本质的提问
FIRST_PRINCIPLES = [
    "剥掉所有包装与约定后，用户/受众真正想要的那个核心价值是什么？",
    "这件事最底层的物理/逻辑约束是什么？哪些「必须」其实可以推翻？",
    "如果从零开始、不用现有任何方案，你会先造哪一块？",
    "这件事的「目标」再往上跳一层，是什么更大的目标？",
]

# SCAMPER 七个操作
SCAMPER = [
    ("S 替换 Substitute", "把核心组成部分换成另一个东西，换成什么最出人意料？"),
    ("C 组合 Combine", "把主题与某个看似无关的东西合并，合并成什么？"),
    ("A 调整 Adapt", "调整哪一个环节的形态、顺序或节奏？"),
    ("M 放大/缩小 Magnify/Minify", "哪一部分放大到极端？哪一部分删到最小？"),
    ("P 换用 Put to another use", "换个用户、换个场景、换个用途，用在谁身上？"),
    ("E 消除 Eliminate", "去掉哪个「必备项」？去掉之后世界会怎样？"),
    ("R 反转 Reverse", "把流程、视角或逻辑倒过来，倒过来是什么样？"),
]

# 反转目标维度
REVERSALS = [
    "把「目标」反转：本来要快，反过来追求慢/久；本来要多，反过来追求少。",
    "把「关系」反转：用户与产品互换角色、主体与客体互换。",
    "把「流程」反转：从终点倒着走到起点，先给结论再推导原因。",
    "把「评价」反转：把缺点当卖点、把限制当特色。",
]

# 极端化维度
EXTREMES = [
    ("成本→0", "如果成本几乎为零，方案会变成什么样？"),
    ("速度→无限", "如果结果瞬间可得，体验会如何改变？"),
    ("尺寸→极小/极大", "如果尺寸缩小到 1% 或放大到 100 倍呢？"),
    ("用户→所有人/一个人", "如果只服务一个人，或所有人，会怎么设计？"),
    ("次数→一次/无数", "如果只能用一次，或能用无数次，会怎么设计？"),
]

# 口述采样（Verbalized Sampling）：先列候选分布，再从中挑，避免直接给最安全答案
VERBALIZED = [
    "列出 5 个「可能的候选方向」及它们各自的『被选中概率』，不要只给一个答案。",
    "挑 2 个方向组合成一个杂交方向，说明为什么杂交后比任一方都新。",
]


# ---------------------------------------------------------------- 技法渲染
def render(topic, domain):
    """返回 {技法名: [启发句...]}。每项启发都是让模型继续想象的「岔路口」。"""
    rnd = random.Random(_SEED if _SEED is not None else None)
    out = {}

    def block(name, lines):
        out[name] = lines

    # SCAMPER
    block("SCAMPER", [f"{k}：{q}（围绕『{topic}』）" for k, q in SCAMPER])

    # 跨域融合：抽 2 个无关领域（含随机刺激兜底）
    picked = rnd.sample(DOMAINS, 2)
    block("跨域融合", [
        f"把「{topic}」与「{a[0]}」结合：{a[1]} 的机制能否迁移到本主题？" for a in picked
    ])

    # 反事实
    block("反事实", [
        f"假设「{topic}」最依赖的那个前提被拿走/改变，世界会怎么演化？",
        f"如果历史在某一点分岔（某个关键产品/技术从未出现），现在的「{topic}」会如何不同？",
    ])

    # 第一性原理
    block("第一性原理", [q for q in FIRST_PRINCIPLES])

    # 反转
    block("反转", REVERSALS)

    # 极端化
    block("极端化", [f"{tag}：{q}（围绕『{topic}』）" for tag, q in EXTREMES])

    # 类比迁移
    analog = rnd.choice(DOMAINS)
    block("类比迁移", [
        f"借用一个冷门领域——{analog[0]}（{analog[1]}）——的机制，映射到「{topic}」上会产生什么？"
    ])

    # 随机刺激
    stim = rnd.sample(STIMULI, 3)
    block("随机刺激", [
        f"用随机种子『{s}』强扭成与「{topic}」相关的点子（先接受荒谬，再找逻辑）。" for s in stim
    ])

    # 口述采样
    block("口述采样", VERBALIZED)

    return out


# ---------------------------------------------------------------- CLI
def parse_args(argv):
    p = argparse.ArgumentParser(
        description="生成发散脚手架（岔路口式启发），供模型继续想象原创方案")
    p.add_argument("--topic", required=True, help="问题/主题，如：智能水杯卖点")
    p.add_argument("--domain", default="general",
                   help="领域（general/product/writing/event/plan），影响领域词缀，仅提示用")
    p.add_argument("--techniques", default="all",
                   help="技法列表，逗号分隔；all=全部。可选：scamper,cross_domain,"
                        "counterfactual,first_principles,reversal,extreme,analogy,"
                        "random_stimuli,verbalized")
    p.add_argument("--seed", type=int, default=None, help="随机种子，用于复现")
    p.add_argument("--json", action="store_true", help="输出 JSON（供下游解析）")
    return p.parse_args(argv)


def main(argv):
    global _SEED
    args = parse_args(argv)
    _SEED = args.seed

    ALL = ["scamper", "cross_domain", "counterfactual", "first_principles",
           "reversal", "extreme", "analogy", "random_stimuli", "verbalized"]
    chosen = ALL if args.techniques.strip().lower() == "all" else [
        t.strip().lower() for t in args.techniques.split(",") if t.strip()]

    raw = render(args.topic, args.domain)
    # 技法名 → 脚本内 key 映射
    keymap = {
        "scamper": "SCAMPER", "cross_domain": "跨域融合",
        "counterfactual": "反事实", "first_principles": "第一性原理",
        "reversal": "反转", "extreme": "极端化", "analogy": "类比迁移",
        "random_stimuli": "随机刺激", "verbalized": "口述采样",
    }
    selected = {keymap[k]: raw[keymap[k]] for k in chosen if k in keymap}

    result = {
        "topic": args.topic,
        "domain": args.domain,
        "techniques": chosen,
        "note": "脚手架不是答案，请把它当作岔路口继续想象，产出至少 3 个角度不同的候选。",
        "scaffolds": selected,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(f"# 发散脚手架 · {args.topic}（领域：{args.domain}）\n")
    print(f"> {result['note']}\n")
    for name, lines in selected.items():
        print(f"## {name}")
        for ln in lines:
            print(f"- {ln}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
