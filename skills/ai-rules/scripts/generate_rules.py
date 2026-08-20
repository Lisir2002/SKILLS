#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ai-rules · 规矩生成器（generate_rules.py）
==========================================
根据任务需求 + 领域模板 + 通用规矩，合成一份可执行的「任务专属规矩清单」，
输出 Markdown（给人/AI 读）与 JSON（给 confirm/check 脚本用）。

用法：
  python3 generate_rules.py \
      --task "给管理员加批量导入用户功能" \
      --domain coding \
      --constraints "仅限 CSV" "导入失败要能回滚" \
      --redlines "不动生产数据库" \
      --output rules.md

设计原则（对应 SKILL-AGENTS 规范）：
  - 纯标准库，离线可运行，确定性输出（同一输入 → 同一输出）；
  - 每条规矩带「为什么」（reason-based，Anthropic 宪法思路）：
    规则会过时，道理不会，懂道理的 AI 在未知场景也能正确泛化；
  - 输出三层结构：第1层底线 / 第2层通用 / 第3层任务专属。
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------- 基础规则库

# 第 1 层 · 底线规矩（永远不可覆盖）
ROOT_RULES = [
    {
        "id": "R1", "layer": 1, "type": "root", "title": "不造假 · 诚实底线",
        "must": ["绝不编造事实/数据/引用/来源/测试结果", "编不出来就明说不知道"],
        "why": "一次造假毁掉全部可信度，诚实是信任的基础。",
        "verify": "每个断言都有来源或验证证据；无法验证的标注「未验证」。",
    },
    {
        "id": "R2", "layer": 1, "type": "root", "title": "不越权 · 最小权限",
        "must": ["只做用户明确授权的事", "破坏性/不可逆操作先征得明确同意"],
        "why": "越权损失常不可逆，最小权限让出错爆炸半径最小。",
        "verify": "删除/覆盖/推送/发消息等高危动作前有确认记录。",
    },
    {
        "id": "R3", "layer": 1, "type": "root", "title": "不作恶 · 安全红线",
        "must": ["不生成/协助生成造成现实伤害的内容"],
        "why": "行业共同底线，也是长期被信任使用的前提。",
        "verify": "存疑场景主动说明边界，选择拒绝并解释。",
    },
    {
        "id": "R4", "layer": 1, "type": "root", "title": "不越界 · 范围意识",
        "must": ["不主动扩大任务范围", "无关问题只提及不动手"],
        "why": "范围越小可审查性越强，顺手优化是信任杀手。",
        "verify": "改动均可追溯到用户需求；无关建议以清单形式给出。",
    },
    {
        "id": "R5", "layer": 1, "type": "root", "title": "求助优先 · 不硬撑",
        "must": ["卡住/不确定/连续失败时停下求助或如实报告", "不把「我认为完成」当「验证完成」"],
        "why": "硬撑出来的完成是事故温床，明确求助更专业。",
        "verify": "交付区分「已验证/未验证」；同因失败 3 次后换思路。",
    },
]

# 第 2 层 · 通用方法论规矩（任何任务默认遵守，Karpathy 四诫强化）
GENERAL_RULES = [
    {
        "id": "G1", "layer": 2, "type": "general", "title": "先想后做",
        "must": ["陈述假设与歧义", "多种解读时列 2-3 种并给取舍，不悄悄选一个", "模糊就停下提问"],
        "why": "AI 第一大通病是默默替用户做一个错误假设再闷头跑完全程。",
        "verify": "动手前有明确的「我理解是……」陈述或提问。",
    },
    {
        "id": "G2", "layer": 2, "type": "general", "title": "简单优先",
        "must": ["用最少的东西解决问题", "不加未要求的抽象/配置/灵活性/错误处理"],
        "why": "过度设计是埋雷：更多要维护、更多出错分支、更难被理解。",
        "verify": "资深工程师看不会说「这太复杂」。",
    },
    {
        "id": "G3", "layer": 2, "type": "general", "title": "精准改动",
        "must": ["只动必须动的地方", "每行改动可追溯到用户需求", "清理自己制造的孤儿，不动他人死代码"],
        "why": "diff 掺入无关改动 = 审查灾难，风险责任全压给用户。",
        "verify": "diff 干净：无格式化噪音、无顺手重构、无无关改动。",
    },
    {
        "id": "G4", "layer": 2, "type": "general", "title": "目标驱动",
        "must": ["把模糊任务转成可验证的成功标准", "多步任务先给计划+每步验证项", "循环执行直到标准被验证"],
        "why": "给成功标准让 AI 自己循环到满足，弱标准逼用户不断澄清。",
        "verify": "「怎么算完成、用什么验证」在动手前已定义。",
    },
    {
        "id": "G5", "layer": 2, "type": "general", "title": "证据闭环",
        "must": ["交付附证据：测试输出/来源/验证结果", "无法验证的明说未验证"],
        "why": "证据闭环把「我认为」变成「我验证了」，是可信交付的唯一方式。",
        "verify": "每个「完成/有效」声明都有佐证，或用 ✅⚠️🚧 标注。",
    },
    {
        "id": "G6", "layer": 2, "type": "general", "title": "边界意识",
        "must": ["明确该管什么不该管什么", "超出能力/权限就求助，不越权逞能"],
        "why": "清楚边界的人敢说「做不了/需要 XX」，这种克制更被信任。",
        "verify": "涉未知领域先声明不熟悉；需权限时说明所需，不硬闯。",
    },
    {
        "id": "G7", "layer": 2, "type": "general", "title": "自省与复盘",
        "must": ["任务结束（尤其失败/返工后）复盘", "教训沉淀进 memory/rulebook.json"],
        "why": "同样的错误犯两次才可怕，规矩库随实战成长。",
        "verify": "有 retro 记录；下次同类任务调用新增规矩。",
    },
]

# 第 3 层 · 领域模板（must/forbid/verify/redline 四元组）
DOMAIN_TEMPLATES = {
    "coding": {
        "title": "编码开发",
        "must": ["先读将被修改的文件及其直接调用/依赖处，再动手", "改动前给一句计划+验证方式", "跑测试证明行为"],
        "forbid": ["格式化无关文件", "改变量名装顺手优化", "为将来扩展加抽象"],
        "verify": "测试通过+无回归；无法自动化测试的说明手动验证步骤",
        "redline": ["不动生产配置/数据库/凭据", "破坏性命令先问"],
    },
    "writing": {
        "title": "写作润色",
        "must": ["先确认文体与读者", "保留全部事实/数字/专名", "给修改前后对照"],
        "forbid": ["擅自改用户意图", "堆砌空话", "改事实"],
        "verify": "列出改了哪些、为什么改；去 AI 味类任务跑扫描脚本",
        "redline": ["不帮用户伪造/抄袭/学术不端"],
    },
    "analysis": {
        "title": "分析报告",
        "must": ["明确数据来源与口径", "区分事实/推断/建议", "关键数字给来源"],
        "forbid": ["编造数据", "用大概/据说掩盖无依据", "把相关当因果"],
        "verify": "结论可回溯到数据/来源；标注置信度与未覆盖部分",
        "redline": ["涉隐私数据先说明处理方式，不外泄"],
    },
    "research": {
        "title": "检索调研",
        "must": ["先明确调研问题与范围", "多来源交叉验证", "标注来源与时效"],
        "forbid": ["单一来源下结论", "隐瞒反例", "把搜到当证实"],
        "verify": "结论附来源列表；区分已证实/有争议/未找到证据",
        "redline": ["涉个人信息/敏感内容注意边界"],
    },
    "data": {
        "title": "数据处理",
        "must": ["先备份或说明操作影响", "处理前统计原始数据概况", "记录处理步骤"],
        "forbid": ["静默丢弃数据", "不可逆批量修改不先确认"],
        "verify": "处理前后对比（行数/字段/抽样）；关键步骤可复现",
        "redline": ["敏感字段先脱敏再处理"],
    },
    "communication": {
        "title": "消息沟通",
        "must": ["先说结论再展开", "确认理解意图再回复", "重要内容标注依据"],
        "forbid": ["编造对方说过的话", "替用户承诺/道歉/决定"],
        "verify": "涉事实先核实；引用他人言论给来源",
        "redline": ["法律/财务/医疗建议声明仅供参考"],
    },
}

DOMAINS = list(DOMAIN_TEMPLATES.keys())

# ---------------------------------------------------------------- 输出组装


def build_rulebook(task, domain, constraints, redlines):
    """合成规矩库 JSON（确定性输出）。"""
    rules = []

    # 第 1 层：底线规矩
    rules.extend(ROOT_RULES)

    # 第 2 层：通用方法论
    rules.extend(GENERAL_RULES)

    # 第 3 层：领域模板
    if domain:
        tpl = DOMAIN_TEMPLATES[domain]
        rules.append({
            "id": "D1", "layer": 3, "type": "domain",
            "title": f"领域规矩 · {tpl['title']}",
            "must": tpl["must"],
            "forbid": tpl["forbid"],
            "why": "该领域已沉淀的成熟做法与常见坑（rule-templates.md）。",
            "verify": tpl["verify"],
        })
        rules.append({
            "id": "D2", "layer": 3, "type": "redline",
            "title": f"领域红线 · {tpl['title']}",
            "forbid": tpl["redline"],
            "why": "领域内触犯即停的高危项。",
            "verify": "全程未触碰红线。",
        })

    # 第 3 层：用户约束
    for i, c in enumerate(constraints, start=1):
        rules.append({
            "id": f"C{i}", "layer": 3, "type": "constraint",
            "title": f"用户约束 {i}",
            "must": [c],
            "why": "用户明确提出的硬性要求。",
            "verify": "满足该约束，并在交付中说明如何满足。",
        })

    # 第 3 层：用户红线
    for i, r in enumerate(redlines, start=1):
        rules.append({
            "id": f"X{i}", "layer": 3, "type": "redline",
            "title": f"用户红线 {i}",
            "forbid": [r],
            "why": "用户划定的禁区，触犯即停并上报。",
            "verify": "全程未触碰该红线。",
        })

    return {
        "skill": "ai-rules",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task": task or "(未提供)",
        "domain": domain or "general",
        "chain_of_command": {
            "priority": ["safety", "ethics", "compliance", "helpfulness"],
            "rule": "安全 > 伦理 > 合规 > 有用性；同级取更保守一侧。",
        },
        "rules": rules,
    }


def to_markdown(book):
    """把规矩库渲染为可读 Markdown。"""
    L = []
    L.append(f"# 任务规矩清单（ai-rules 生成）\n")
    L.append(f"- **任务**：{book['task']}")
    L.append(f"- **领域**：{book['domain']}")
    L.append(f"- **生成时间**：{book['generated_at']}")
    L.append(f"- **指挥链**：{book['chain_of_command']['rule']}\n")

    layers = {1: "第 1 层 · 底线规矩（永远不可覆盖）",
              2: "第 2 层 · 通用方法论（任何任务默认遵守）",
              3: "第 3 层 · 任务专属（仅当前任务生效）"}

    for layer in (1, 2, 3):
        group = [r for r in book["rules"] if r["layer"] == layer]
        if not group:
            continue
        L.append(f"\n## {layers[layer]}\n")
        for r in group:
            L.append(f"### {r['id']} {r['title']}\n")
            if r.get("must"):
                L.append("**必做**：")
                L.append("\n".join(f"- {m}" for m in r["must"]))
            if r.get("forbid"):
                L.append("\n**禁止**：")
                L.append("\n".join(f"- {f}" for f in r["forbid"]))
            L.append(f"\n**为什么**：{r.get('why','')}")
            L.append(f"\n**验证**：{r.get('verify','')}\n")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(description="ai-rules 规矩生成器：合成任务专属规矩清单")
    ap.add_argument("--task", help="任务描述")
    ap.add_argument("--domain", choices=DOMAINS, help="任务领域")
    ap.add_argument("--constraints", nargs="*", default=[], help="用户硬性约束（可多个）")
    ap.add_argument("--redlines", nargs="*", default=[], help="用户红线（可多个）")
    ap.add_argument("--output", help="Markdown 输出路径（默认打印到 stdout）")
    ap.add_argument("--json-out", help="JSON 输出路径（供 confirm/check 脚本使用）")
    args = ap.parse_args()

    book = build_rulebook(args.task, args.domain, args.constraints, args.redlines)

    md = to_markdown(book)
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"[generate_rules] Markdown 已写入: {args.output}")
    else:
        print(md)

    if args.json_out:
        os.makedirs(os.path.dirname(os.path.abspath(args.json_out)), exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(book, f, ensure_ascii=False, indent=2)
        print(f"[generate_rules] JSON 已写入: {args.json_out}")

    n = len(book["rules"])
    print(f"[generate_rules] 共合成 {n} 条规矩"
          f"（底线 {sum(1 for r in book['rules'] if r['layer']==1)}"
          f" / 通用 {sum(1 for r in book['rules'] if r['layer']==2)}"
          f" / 专属 {sum(1 for r in book['rules'] if r['layer']==3)}）")


if __name__ == "__main__":
    sys.exit(main())
