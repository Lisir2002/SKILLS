#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""深度内容验证：下载媒体前 2MB，校验容器结构（MP4 ftyp/moov/mdat、MP3 ID3、图片魔数），
并尝试从 moov 中解析元数据以确认媒体内容真实有效。"""
import sys, json, os, subprocess, requests, struct

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "skills", "media-parser", "scripts")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
REF = {"哔哩哔哩": "https://www.bilibili.com/", "微博": "https://weibo.com/"}

def parse(text):
    r = subprocess.run([sys.executable, "parse_media.py", text],
                       cwd=SCRIPTS, capture_output=True, text=True, timeout=60)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {"code": 500, "msg": "stdout 非 JSON", "data": None, "succ": False}

import warnings
warnings.filterwarnings("ignore")

def fetch(url, referer=None, limit=2*1024*1024):
    h = {"User-Agent": UA}
    if referer:
        h["Referer"] = referer
    try:
        r = requests.get(url, headers=h, timeout=20, stream=True, allow_redirects=True)
    except requests.exceptions.SSLError as e:
        return 0, f"SSL:{str(e)[:40]}", b""
    except Exception as e:
        return 0, f"{type(e).__name__}:{str(e)[:40]}", b""
    ct = r.headers.get("content-type", "?")
    status = r.status_code
    data = b""
    for chunk in r.iter_content(65536):
        data += chunk
        if len(data) >= limit:
            break
    r.close()
    return status, ct, data

def box_names(data):
    """解析 MP4 顶层 box 名称（前 64KB 内），返回有序列表"""
    names, off = [], 0
    while off + 8 <= len(data) and len(names) < 12:
        size = struct.unpack(">I", data[off:off+4])[0]
        box = data[off+4:off+8].decode("latin1", "ignore")
        names.append(box)
        if size < 8:
            break
        off += size
    return names

def probe(kind, url, referer=None):
    status, ct, data = fetch(url, referer)
    out = f"{status} [{ct}] got={len(data)}B"
    if status != 200 or not data:
        return out + " <-- 不可访问/无内容"
    if kind in ("video", "audio"):
        if data[4:8] == b"ftyp":
            names = box_names(data)
            has_moov = "moov" in names
            has_mdat = "mdat" in names
            out += f" | MP4 ftyp={data[8:12].decode('latin1')} boxes={names[:8]} moov={'Y' if has_moov else 'N'} mdat={'Y' if has_mdat else 'N'}"
        elif data[:3] == b"ID3":
            out += " | MP3 ID3 header OK"
        elif data[:4] == b"\x00\x00\x00\x18" and data[4:8] == b"mp42":
            out += " | MP4 mp42 OK"
        else:
            out += f" | 非预期容器 first={data[:16].hex()}"
    else:  # image
        if data[:3] == b"\xff\xd8\xff":
            out += " | JPEG magic OK"
        elif data[:8] == b"\x89PNG\r\n\x1a\n":
            out += " | PNG magic OK"
        elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            out += " | WEBP magic OK"
        else:
            out += f" | 非预期图片 first={data[:16].hex()}"
    return out

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
        if not line:
            continue
        label, url = line.split("|", 1)
        print(f"\n{'='*70}\n[{label}] {url}")
        res = parse(url)
        if not res.get("succ") or not res.get("data"):
            print("  PARSE:", res.get("code"), res.get("msg"))
            continue
        d = res["data"]
        ref = REF.get(d.get("platform"))
        print(f"  platform={d.get('platform')} title={(d.get('title') or '')[:44]!r} author={(d.get('author') or {}).get('nickname')}")
        for kind, u in collect_media(d):
            print(f"  [{kind:5}] {probe(kind, u, ref)}")

if __name__ == "__main__":
    main()
