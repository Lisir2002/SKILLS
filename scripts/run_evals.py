#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_evals.py · 技能 evals 运行器
================================
读取各技能 `skills/<name>/evals/evals.json` 并执行三类用例：
  1. trigger_evals   ：触发路由回归（模拟"用户 prompt 能否命中该技能 description"）
  2. quality_evals   ：静态质量断言（SKILL.md / README.md 内容包含性）
  3. smoke_tests     ：脚本冒烟（纯标准库脚本跑一遍，退出码 0 = 通过）

用法：
  python3 scripts/run_evals.py                 # 跑全部技能 evals
  python3 scripts/run_evals.py de-ai-flavor    # 只跑指定技能
  python3 scripts/run_evals.py --json          # JSON 输出（供 CI）

退出码：0 = 全部通过   1 = 存在失败
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKILLS_DIR = os.path.join(ROOT, "skills")
TIMEOUT = 60


def load_description(skill_dir):
    """从 SKILL.md frontmatter 提取 description（用于触发路由核验）。"""
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(skill_md):
        return ""
    text = open(skill_md, encoding="utf-8").read()
    m = __import__("re").match(r"^---\n(.*?)\n---\n", text, __import__("re").S)
    if not m:
        return ""
    for line in m.group(1).splitlines():
        kv = __import__("re").match(r'^description\s*:\s*["\']?(.*?)["\']?\s*$', line)
        if kv:
            return kv.group(1)
    return ""


def run_trigger(desc_lower, case):
    """触发路由：prompt 至少命中一个『同时存在于 description』的触发词。"""
    prompt_l = case["prompt"].lower()
    hits = [kw for kw in case.get("keywords", []) if kw in desc_lower and kw in prompt_l]
    desc_has = [kw for kw in case.get("keywords", []) if kw in desc_lower]
    if case.get("must_trigger", True):
        if hits:
            return True, f"命中触发词 {hits}"
        if desc_has and not any(k in prompt_l for k in desc_has):
            return False, f"用户 prompt 未出现触发词 {desc_has}"
        return False, "description 未覆盖声明的触发词，路由可能漏触发"
    # 反触发：不应命中
    if hits:
        return False, f"反触发用例意外命中 {hits}"
    return True, "反触发通过"


def run_quality(skill_dir, case):
    rel = case["target"]
    path = os.path.join(skill_dir, rel)
    if not os.path.exists(path):
        return False, f"目标文件不存在: {rel}"
    if case.get("kind") == "file_exists":
        return True, f"{rel} 存在"
    text = open(path, encoding="utf-8", errors="replace").read()
    needle = case["text"]
    if case.get("kind", "contains") == "not_contains":
        if needle in text:
            return False, f"{rel} 不应包含「{needle}」但命中了"
        return True, f"{rel} 未包含「{needle}」"
    if needle in text:
        return True, f"{rel} 包含「{needle}」"
    return False, f"{rel} 缺少「{needle}」"


def run_smoke(skill_dir, case):
    cmd = case["command"]
    # 支持相对 skill 目录的命令片段，如 "scripts/scan_ai_flavor.py"
    if isinstance(cmd, list) and cmd and os.path.exists(os.path.join(skill_dir, cmd[0])):
        cmd = [os.path.join(skill_dir, cmd[0])] + cmd[1:]
    try:
        r = subprocess.run(cmd, cwd=skill_dir, capture_output=True, text=True, timeout=TIMEOUT)
    except FileNotFoundError as e:
        return False, f"无法执行: {e}"
    except subprocess.TimeoutExpired:
        return False, f"超时（>{TIMEOUT}s）"
    if r.returncode == 0:
        return True, "退出码 0"
    return False, f"退出码 {r.returncode}：{r.stdout[-200:]}{r.stderr[-200:]}"


def eval_skill(name):
    skill_dir = os.path.join(SKILLS_DIR, name)
    evals_file = os.path.join(skill_dir, "evals", "evals.json")
    if not os.path.exists(evals_file):
        return [], f"缺少 {evals_file}"
    data = json.load(open(evals_file, encoding="utf-8"))
    desc_lower = load_description(skill_dir).lower()
    results = []
    for c in data.get("trigger_evals", []):
        ok, msg = run_trigger(desc_lower, c)
        results.append((name, "trigger", c["id"], ok, msg))
    for c in data.get("quality_evals", []):
        ok, msg = run_quality(skill_dir, c)
        results.append((name, "quality", c["id"], ok, msg))
    for c in data.get("smoke_tests", []):
        ok, msg = run_smoke(skill_dir, c)
        results.append((name, "smoke", c["id"], ok, msg))
    return results, None


def main():
    ap = argparse.ArgumentParser(description="技能 evals 运行器")
    ap.add_argument("skills", nargs="*", help="指定技能名；缺省跑全部")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    args = ap.parse_args()

    targets = args.skills or sorted(
        d for d in os.listdir(SKILLS_DIR)
        if os.path.isdir(os.path.join(SKILLS_DIR, d)) and not d.startswith(".")
    )

    all_results, errors = [], []
    for name in targets:
        res, err = eval_skill(name)
        if err:
            errors.append({"skill": name, "err": err})
        all_results.extend(res)

    for name, kind, cid, ok, msg in all_results:
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {name}/{kind}/{cid} — {msg}", file=sys.stderr)
    for e in errors:
        print(f"  [SKIP] {e['skill']} — {e['err']}", file=sys.stderr)

    n_fail = sum(1 for r in all_results if not r[3])
    if args.json:
        print(json.dumps({
            "total": len(all_results), "passed": len(all_results) - n_fail,
            "failed": n_fail, "errors": errors,
            "results": [{"skill": r[0], "kind": r[1], "id": r[2], "pass": r[3], "msg": r[4]} for r in all_results],
        }, ensure_ascii=False, indent=2))
    else:
        print(f"\n结果：共 {len(all_results)} 用例，通过 {len(all_results) - n_fail}，失败 {n_fail}")
        if errors:
            print(f"跳过 {len(errors)} 个技能（无 evals 文件）")

    sys.exit(1 if (n_fail or errors) else 0)


if __name__ == "__main__":
    main()
