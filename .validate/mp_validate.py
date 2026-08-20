#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量验证：解析链接 → 校验输出媒体 URL 可访问性与内容类型"""
import sys, json, os, subprocess, requests, random

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "skills", "media-parser", "scripts")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

def parse(text):
    r = subprocess.run([sys.executable, "parse_media.py", text],
                       cwd=SCRIPTS, capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"code": 500, "msg": "stdout 非 JSON: " + (r.stdout[-150:] + r.stderr[-150:]), "data": None, "succ": False}

def check(url, referer=None):
    if not url:
        return "EMPTY"
    h = {"User-Agent": UA}
    if referer:
        h["Referer"] = referer
    try:
        r = requests.get(url, headers=h, timeout=15, stream=True, allow_redirects=True)
        ct = r.headers.get("content-type", "?")
        cl = r.headers.get("content-length", "?")
        chunk = b""
        try:
            chunk = next(r.iter_content(512)) or b""
        except Exception:
            pass
        return f"{r.status_code} [{ct}] len={cl} first={chunk[:8].hex()}"
    except Exception as e:
        return f"ERR {type(e).__name__}: {str(e)[:60]}"

def collect_media(d):
    items = []
    if d.get("video_url"):
        items.append(("video", d["video_url"]))
    if d.get("audio_url"):
        items.append(("audio", d["audio_url"]))
    if d.get("cover_url"):
        items.append(("cover", d["cover_url"]))
    for i, img in enumerate(d.get("image_list") or []):
        url = img.get("url") if isinstance(img, dict) else img
        items.append((f"img{i}", url))
    return items

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        label, url = line.split("|", 1)
        print(f"\n{'='*70}\n[{label}] {url}")
        res = parse(url)
        if not res.get("succ") or not res.get("data"):
            print("  PARSE:", res.get("code"), res.get("msg"))
            continue
        d = res["data"]
        print(f"  platform={d.get('platform')} title={(d.get('title') or '')[:40]!r}")
        print(f"  author={(d.get('author') or {}).get('nickname')} images={len(d.get('image_list') or [])} video={'Y' if d.get('video_url') else 'N'}")
        for kind, u in collect_media(d):
            ref = None
            if d.get("platform") == "哔哩哔哩":
                ref = "https://www.bilibili.com/"
            elif d.get("platform") == "微博":
                ref = "https://weibo.com/"
            tag = f"+ref" if ref else "     "
            print(f"  [{kind:6}] {check(u, ref)}{tag}  {u[:85]}")

if __name__ == "__main__":
    main()
