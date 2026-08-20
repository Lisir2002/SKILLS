#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_skills.py · 技能包自动化校验器
=========================================
把 docs/SKILL-AGENTS.md 第 7 节《校验与质量检查清单》变成可执行脚本：
对 skills/ 下每个技能做静态检查（frontmatter / 结构 / 敏感信息 / 引用深度）。

用法：
  python3 scripts/validate_skills.py            # 校验全部技能
  python3 scripts/validate_skills.py de-ai-flavor   # 只校验指定技能
  python3 scripts/validate_skills.py --json     # JSON 输出（供 CI 消费）

退出码：0 = 全部通过（仅警告可忽略）  1 = 存在错误（阻断打包/CI）
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKILLS_DIR = os.path.join(ROOT, "skills")

# ── 常量：来自 SKILL-AGENTS.md 的硬性规则 ──────────────────────────────
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NAME_MAX = 64
DESC_MAX = 1024
DESC_LEAD = 120            # 触发词应落在前 120 字符内
RESERVED = ("claude", "anthropic")
BLOCK_SCALARS = re.compile(r"^\s*(?:description\s*:\s*)(?:>|-|\||[>|][+-])", re.M)

# 必含正文段落（正文标题可能是"Purpose / 用途"等双语形式，按关键词模糊匹配）
REQUIRED_SECTIONS = {
    "Purpose":        r"purpose",
    "When to Use":    r"when\s+to\s+use",
    "When NOT to Use": r"when\s+not\s+to\s+use",
    "Workflow":       r"workflow|工作流",
    "Output Spec":    r"output\s+spec|输出规范|output",
    "Failure Modes":  r"failure\s+modes|失败模式",
    "Dependencies":   r"dependenc",
}

# 敏感信息模式（扫描技能内所有文本文件）：(正则, 说明, 是否硬错误)
# 硬错误 = 泄露令牌/用户身份/口令；警告 = 通用项目根路径（如 ~/workspace 属环境约定，允许）
SENSITIVE_PATTERNS = [
    (re.compile(r"(?i)\bghp_[A-Za-z0-9]{20,}\b"), "GitHub token (ghp_…)", True),
    (re.compile(r"(?i)\bsk[-_][A-Za-z0-9]{16,}\b"), "OpenAI 风格密钥 (sk_…)", True),
    (re.compile(r"(?i)\b[a-z0-9._-]+:[A-Za-z0-9._-]{16,}\b@"), "含口令的连接串", True),
    (re.compile(r"(?i)api[_-]?key\s*[=:]\s*['\"]?[A-Za-z0-9]{16,}"), "明文 API Key", True),
    (re.compile(r"(?i)password\s*[=:]\s*['\"]?[^'\"]{6,}"), "明文密码", True),
    (re.compile(r"\bcookie\s*[=:]\s*['\"][^'\"]{20,}"), "明文 Cookie", True),
    (re.compile(r"/home/[a-z0-9_]+/"), "用户专属绝对路径 /home/<user>/", True),
    (re.compile(r"/workspace(?:/|$)"), "项目根绝对路径 /workspace（多为环境约定，确认非内部状态泄露）", False),
]

# 技能内文本文件扩展名（做敏感信息扫描）
TEXT_EXTS = {".md", ".py", ".js", ".json", ".txt", ".sh", ".yaml", ".yml", ".toml"}

RESULTS = []


def report(skill, level, msg):
    RESULTS.append({"skill": skill, "level": level, "msg": msg})
    # 人类可读进度走 stderr，保证 --json 时 stdout 只有纯 JSON
    if level == "ERROR":
        print(f"  ✗ [{skill}] ERROR  {msg}", file=sys.stderr)
    else:
        print(f"  ! [{skill}] warn   {msg}", file=sys.stderr)


def walk_text_files(skill_dir):
    for root, _dirs, files in os.walk(skill_dir):
        for fn in files:
            ext = os.path.splitext(fn)[1]
            if ext in TEXT_EXTS and fn not in ("busybox_lint.py",):
                yield os.path.join(root, fn)


def check_skill(name):
    skill_dir = os.path.join(SKILLS_DIR, name)
    skill_md = os.path.join(skill_dir, "SKILL.md")
    readme = os.path.join(skill_dir, "README.md")

    # 1. 目录结构：SKILL.md 必需，README.md 必需
    if not os.path.exists(skill_md):
        report(name, "ERROR", f"缺少 SKILL.md（期望 {skill_md}）")
        return
    if not os.path.exists(readme):
        report(name, "warn", "缺少 README.md（用户向说明，规范要求必需）")

    with open(skill_md, encoding="utf-8") as f:
        content = f.read()

    # 2. frontmatter 解析
    fm = {}
    m = re.match(r"^---\n(.*?)\n---\n", content, re.S)
    if not m:
        report(name, "ERROR", "SKILL.md 首行不是 YAML frontmatter（^--- ... ---）")
        return
    try:
        # 用最小 YAML 子集解析：仅 name / description 等简单键值
        for line in m.group(1).splitlines():
            kv = re.match(r'^([A-Za-z0-9_-]+)\s*:\s*["\']?(.*?)["\']?\s*$', line)
            if kv:
                fm[kv.group(1)] = kv.group(2)
    except Exception as e:  # pragma: no cover
        report(name, "ERROR", f"frontmatter 解析失败: {e}")
        return

    # 3. name 规则
    nm = fm.get("name", "")
    if not nm:
        report(name, "ERROR", "frontmatter 缺少 name")
    else:
        if not NAME_RE.match(nm):
            report(name, "ERROR", f"name '{nm}' 不符合 kebab-case（{NAME_RE.pattern}）")
        if len(nm) > NAME_MAX:
            report(name, "ERROR", f"name 超长（{len(nm)} > {NAME_MAX}）")
        if nm != name:
            report(name, "ERROR", f"name '{nm}' 与目录名 '{name}' 不一致")
        low = nm.lower()
        for r in RESERVED:
            if r in low:
                report(name, "ERROR", f"name 含保留词 '{r}'")

    # 4. description 规则
    desc = fm.get("description", "")
    if not desc:
        report(name, "ERROR", "frontmatter 缺少 description")
    else:
        if len(desc) > DESC_MAX:
            report(name, "ERROR", f"description 超长（{len(desc)} > {DESC_MAX} 字符）")
        if "\n" in desc:
            report(name, "ERROR", "description 含换行（必须是单物理行）")
        lead = desc[:DESC_LEAD].lower()
        if not any(k in lead for k in ("use when", "use whenever", "when the user", "when user")):
            report(name, "warn", f"description 前 {DESC_LEAD} 字符未出现 'use when/when the user' 等触发短语")
        if re.search(r"\bI can\b|\bYou can use\b|\bi will\b", desc):
            report(name, "warn", "description 疑似第一/第二人称（应第三人称）")
        if "Not for" not in desc and "not for " not in desc.lower():
            report(name, "warn", "description 缺少反触发 'Not for …'")
    if BLOCK_SCALARS.search(content):
        report(name, "warn", "frontmatter 疑似使用 YAML 块标量符（> / | / >- / |-）")

    # 5. 正文必含段落（Purpose 允许由标题下的引言段承担，不必显式写 "## Purpose"）
    for label, pat in REQUIRED_SECTIONS.items():
        if label == "Purpose":
            has_intro = bool(re.search(r"#\s+.+\n\n[^\n#]+\n\n## ", content)) or bool(re.search(r"##\s*purpose\b", content, re.I))
            if not has_intro:
                report(name, "warn", "正文缺少 Purpose：建议加 '## Purpose' 标题，或在标题下用引言段说明用途")
            continue
        if not re.search(pat, content, re.I):
            report(name, "warn", f"正文缺少段落 '{label}'（建议补充）")

    # 6. 敏感信息扫描
    for fp in walk_text_files(skill_dir):
        try:
            text = open(fp, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        rel = os.path.relpath(fp, ROOT)
        for pat, desc, is_error in SENSITIVE_PATTERNS:
            if pat.search(text):
                report(name, is_error and "ERROR" or "warn", f"命中敏感信息 [{desc}] → {rel}")

    # 7. references/ 一层深引用
    ref_dir = os.path.join(skill_dir, "references")
    if os.path.isdir(ref_dir):
        for root, _d, files in os.walk(ref_dir):
            for fn in files:
                rel_ref = os.path.join(os.path.relpath(root, skill_dir), fn)
                if rel_ref not in content:
                    report(name, "warn", f"references 文件未被 SKILL.md 引用: {rel_ref}")

    # 8. evals/evals.json（推荐项）
    evals_file = os.path.join(skill_dir, "evals", "evals.json")
    if os.path.exists(evals_file):
        try:
            json.load(open(evals_file, encoding="utf-8"))
        except Exception as e:
            report(name, "ERROR", f"evals/evals.json 不是合法 JSON: {e}")
    else:
        report(name, "warn", "缺少 evals/evals.json（推荐：触发与质量测试用例）")

    # 9. 体积提示（建议 <500 行）
    nlines = content.count("\n") + 1
    if nlines > 500:
        report(name, "warn", f"SKILL.md 达 {nlines} 行，超过建议上限 500 行，考虑拆分到 references/")
    elif nlines > 300:
        report(name, "warn", f"SKILL.md 达 {nlines} 行，接近建议上限，可评估拆分")


def main():
    ap = argparse.ArgumentParser(description="技能包自动化校验器（依据 SKILL-AGENTS.md §7）")
    ap.add_argument("skills", nargs="*", help="指定技能名；缺省校验全部")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    args = ap.parse_args()

    targets = args.skills or sorted(
        d for d in os.listdir(SKILLS_DIR)
        if os.path.isdir(os.path.join(SKILLS_DIR, d)) and not d.startswith(".")
    )
    if not targets:
        print("未发现任何技能目录", file=sys.stderr)
        sys.exit(1)

    print(f"校验 {len(targets)} 个技能：{', '.join(targets)}\n", file=sys.stderr)
    for name in targets:
        check_skill(name)

    errors = [r for r in RESULTS if r["level"] == "ERROR"]
    warns = [r for r in RESULTS if r["level"] == "warn"]

    if args.json:
        print(json.dumps({"total": len(targets), "errors": errors, "warnings": warns,
                          "pass": not errors}, ensure_ascii=False, indent=2))
    else:
        print(f"\n{'=' * 50}")
        print(f"结果：错误 {len(errors)}，警告 {len(warns)}")
        if not errors:
            print("通过：可进入打包/发布流程")
        else:
            print("失败：存在阻断性错误，请修复后重试")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
