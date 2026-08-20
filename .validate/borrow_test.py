#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""借鉴 yby6-crawling-short-video-mcp 方案，实测我们失败的链接"""
import json, re, requests, warnings
warnings.filterwarnings("ignore")
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"

def weibo_h5(video_id):
    """yby6 方案：h5.video.weibo.com 播放 API"""
    req_url = f"https://h5.video.weibo.com/api/component?page=/show/{video_id}"
    headers = {
        "Referer": f"https://h5.video.weibo.com/show/{video_id}",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": UA,
    }
    body = f'data={{"Component_Play_Playinfo":{{"oid":"{video_id}"}}}}'
    r = requests.post(req_url, headers=headers, data=body, timeout=15)
    j = r.json()
    data = j.get("data", {}).get("Component_Play_Playinfo", {})
    if not data:
        return f"code={j.get('code')} msg={j.get('msg')}"
    urls = data.get("urls", {})
    v = "https:" + next(iter(urls.values())) if urls else data.get("stream_url")
    return {"title": data.get("title"), "author": data.get("author"),
            "video_url": v, "cover": "https:" + data["cover_image"]}

def xigua_share(video_id):
    """yby6 方案：m.ixigua.com/douyin/share/video 页面 _ROUTER_DATA"""
    url = (f"https://m.ixigua.com/douyin/share/video/{video_id}"
           f"?aweme_type=107&schema_type=1&utm_source=copy&utm_campaign=client_share&utm_medium=android&app=aweme")
    r = requests.get(url, headers={"User-Agent": UA}, timeout=15)
    m = re.search(r"window\._ROUTER_DATA\s*=\s*(.*?)</script>", r.text, re.S)
    if not m:
        return f"status={r.status_code} 无 _ROUTER_DATA，len={len(r.text)}"
    j = json.loads(m.group(1).strip())
    try:
        info = j["loaderData"]["video_(id)/page"]["videoInfoRes"]["item_list"][0]
        v = info["video"]["play_addr"]["url_list"][0].replace("playwm", "play")
        return {"title": info["desc"], "author": info["author"]["nickname"], "video_url": v,
                "cover": info["video"]["cover"]["url_list"][0]}
    except Exception as e:
        return f"解析 _ROUTER_DATA 失败: {type(e).__name__}: {e}"

def kuaishou_with_cookie(share_url):
    """yby6 方案：转发 share 的 headers/cookie 到 location"""
    s = requests.Session()
    r0 = s.get(share_url, headers={"User-Agent": UA, "Referer": "https://v.kuaishou.com/"}, allow_redirects=False, timeout=15)
    loc = r0.headers.get("location", "")
    if not loc:
        return f"无 location, status={r0.status_code}"
    loc = loc.replace("/fw/long-video/", "/fw/photo/")
    r1 = s.get(loc, headers={"User-Agent": UA}, timeout=15)
    m = re.search(r"window\.INIT_STATE\s*=\s*(.*?)</script>", r1.text, re.S)
    if not m:
        return f"status={r1.status_code} 无 INIT_STATE, len={len(r1.text)}"
    j = json.loads(m.group(1).strip())
    photo = None
    for item in j.values():
        if isinstance(item, dict) and "result" in item and "photo" in item:
            photo = item; break
    if not photo:
        return "无 photo 数据"
    if photo["result"] != 1:
        return f"result={photo['result']}"
    d = photo["photo"]
    v = ""
    if "mainMvUrls" in d and d["mainMvUrls"]:
        v = d["mainMvUrls"][0]["url"]
    return {"title": d.get("caption"), "author": d.get("userName"), "video_url": v,
            "cover": d["coverUrls"][0]["url"]}

print("=== 1. 微博 h5.video.weibo.com API 方案 ===")
for label, vid in [("status2-5321729474035871", "5321729474035871"),
                   ("旧链-4502762094452171", "4502762094452171"),
                   ("status1-5334109490250213", "5334109490250213")]:
    try:
        res = weibo_h5(vid)
        print(f"[{label}] {json.dumps(res, ensure_ascii=False)[:160]}")
    except Exception as e:
        print(f"[{label}] ERR {type(e).__name__}: {str(e)[:60]}")

print("\n=== 2. 西瓜 m.ixigua.com 方案 ===")
for label, vid in [("i6702747579374895629", "6702747579374895629"),
                   ("i6813566850056585736", "6813566850056585736")]:
    try:
        res = xigua_share(vid)
        print(f"[{label}] {json.dumps(res, ensure_ascii=False)[:160]}")
    except Exception as e:
        print(f"[{label}] ERR {type(e).__name__}: {str(e)[:60]}")

print("\n=== 3. 快手转发 cookie 方案 ===")
for label, url in [("fXqlD6", "https://v.kuaishou.com/fXqlD6"),
                   ("K63pZGkI", "https://v.kuaishou.com/K63pZGkI")]:
    try:
        res = kuaishou_with_cookie(url)
        print(f"[{label}] {json.dumps(res, ensure_ascii=False)[:160]}")
    except Exception as e:
        print(f"[{label}] ERR {type(e).__name__}: {str(e)[:60]}")
