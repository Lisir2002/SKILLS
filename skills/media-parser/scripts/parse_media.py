#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
parse_media.py — 多平台媒体解析 CLI（media-parser 技能入口）
================================================================
从抖音/B站/快手/小红书/微博/YouTube 等 20+ 平台分享链接中，
解析出标题、作者、无水印视频/图集地址、封面、音频等元数据，输出 JSON。

用法：
    python3 parse_media.py "<链接 或 包含链接的文本>"     # 解析并输出 JSON
    python3 parse_media.py "<链接>" --download <目录>     # 解析并下载视频/封面到目录
    python3 parse_media.py --deps                          # 检查/提示依赖是否齐全

依赖（首次使用前安装）：
    pip install -r requirements.txt
    # 即 requests, beautifulsoup4, lxml, mini-racer, python-dotenv

输出：JSON（结构与原 media-parser API 一致，方便 AI 解析反馈）。
"""

import argparse
import json
import os
import sys

# 将本目录加入 sys.path，保证 src/utils/configs 等绝对导入可用
_HERE = os.path.dirname(os.path.abspath(__file__))
_MP = os.path.join(_HERE, "mp")
if _MP not in sys.path:
    sys.path.insert(0, _MP)

try:
    from utils.web_fetcher import WebFetcher, UrlParser
    from configs.general_constants import DOMAIN_TO_NAME
    from src.parser_factory import ParserFactory
except ImportError as e:
    print(json.dumps({
        "code": 500,
        "msg": f"依赖缺失：{e}。请先运行：pip install -r requirements.txt",
        "data": None,
        "succ": False,
    }, ensure_ascii=False, indent=2))
    sys.exit(2)


def safe_execute(func, default=None):
    """安全执行，解析器单字段失败不影响整体。"""
    try:
        return func()
    except Exception:
        return default


def fetch_with_retry(parser, platform):
    """抓取媒体内容，小红书特殊重试。"""
    max_attempts = 3 if platform == "小红书" else 1
    res = None
    for i in range(max_attempts):
        res = {
            "title": safe_execute(parser.get_title_content),
            "video_url": safe_execute(parser.get_real_video_url),
            "cover_url": safe_execute(parser.get_cover_photo_url),
            "author": safe_execute(parser.get_author_info),
            "image_list": safe_execute(parser.get_image_list, default=[]),
            "audio_url": safe_execute(parser.get_audio_url),
        }
        if res["video_url"] or res["image_list"]:
            return res
        if i < max_attempts - 1:
            # 清理可能失效的缓存后重试
            import src.parsers.douyin_parser as _dp
            if hasattr(_dp, "DouyinParser"):
                _dp.DouyinParser._TTWID_CACHE = None
    return res or {}


def parse_text(text, download_dir=None):
    """核心解析流程，返回 (dict, exit_code)。"""
    # 1. 从文本提取 URL
    url = UrlParser.get_url(text)
    if not url:
        return {
            "code": 400,
            "msg": "未在输入中找到可识别的 http(s) 链接，请提供视频/图集分享链接或包含链接的文本",
            "data": None,
            "succ": False,
        }, 1

    # 2. 跟随重定向，识别平台
    redirect_url = WebFetcher.fetch_redirect_url(url)
    if not redirect_url:
        # 增强：原始链接本身即属支持平台（如 m.weibo.cn/status/<id> 会被 302 到游客登录页）
        # 此时回退到原始 URL，由其解析器内部 API 提取数据。
        domain = UrlParser.get_domain(url)
        if DOMAIN_TO_NAME.get(domain):
            redirect_url = UrlParser.extract_video_address(url)
    if not redirect_url:
        return {
            "code": 400,
            "msg": "链接解析失败：无法跟随重定向或目标不在支持平台列表",
            "data": None,
            "succ": False,
        }, 1

    platform = DOMAIN_TO_NAME.get(UrlParser.get_domain(redirect_url))
    real_url = UrlParser.extract_video_address(redirect_url)

    if not platform:
        return {
            "code": 400,
            "msg": f"该链接尚未支持提取：{real_url}",
            "data": None,
            "succ": False,
        }, 1

    # 3. 分发解析器并抓取
    parser = ParserFactory.create_parser(platform, real_url)
    content = fetch_with_retry(parser, platform)

    if not content.get("video_url") and not content.get("image_list"):
        hint = "该链接需要小红书登录 Cookie 校验，请在配置中提供有效 Cookie 后重试" if platform == "小红书" else "提取媒体内容失败，请检查链接或稍后重试"
        return {
            "code": 400,
            "msg": f"解析失败：{hint}",
            "data": None,
            "succ": False,
        }, 1

    # 4. 统一 HTTPS
    processed_images = []
    for img in content.get("image_list", []):
        if isinstance(img, dict):
            processed_images.append({
                "url": UrlParser.convert_to_https(img.get("url")),
                "live_photo_url": UrlParser.convert_to_https(img.get("live_photo_url")),
            })
        else:
            processed_images.append(UrlParser.convert_to_https(img))

    data = {
        "video_id": UrlParser.get_video_id(redirect_url),
        "platform": platform,
        "title": content.get("title"),
        "video_url": UrlParser.convert_to_https(content.get("video_url")),
        "audio_url": UrlParser.convert_to_https(content.get("audio_url")),
        "cover_url": UrlParser.convert_to_https(content.get("cover_url")),
        "author": content.get("author"),
        "image_list": processed_images,
    }

    # 5. 可选下载
    downloaded = None
    if download_dir:
        downloaded = _download(parser, data, download_dir)

    if downloaded:
        data["downloads"] = downloaded

    return {
        "code": 200,
        "msg": "成功",
        "data": data,
        "succ": True,
    }, 0


def _download(parser, data, download_dir):
    """下载视频/封面到指定目录，返回本地文件路径。"""
    os.makedirs(download_dir, exist_ok=True)
    result = {}
    if data.get("video_url"):
        try:
            p = parser.download_and_save(download_dir, data["video_url"], "mp4")
            result["video_file"] = p
        except Exception:
            result["video_file"] = None
    if data.get("cover_url") and not data.get("image_list"):
        try:
            p = parser.download_and_save(download_dir, data["cover_url"], "jpg")
            result["cover_file"] = p
        except Exception:
            result["cover_file"] = None
    if not result:
        return None
    return result


def main():
    ap = argparse.ArgumentParser(description="多平台媒体解析（无水印地址提取）")
    ap.add_argument("text", nargs="?", help="视频/图集分享链接，或包含链接的文本")
    ap.add_argument("--download", metavar="DIR", help="解析后同时下载视频/封面到指定目录")
    ap.add_argument("--deps", action="store_true", help="仅检查依赖是否齐全")
    args = ap.parse_args()

    if args.deps:
        missing = []
        for mod in ["requests", "bs4", "lxml", "py_mini_racer"]:
            try:
                __import__(mod)
            except ImportError:
                missing.append(mod)
        print(json.dumps({
            "code": 200 if not missing else 400,
            "msg": "依赖齐全" if not missing else f"缺少依赖：{missing}，请运行 pip install -r requirements.txt",
            "data": {"missing": missing},
            "succ": not missing,
        }, ensure_ascii=False, indent=2))
        sys.exit(0 if not missing else 1)

    if not args.text:
        ap.print_help()
        sys.exit(1)

    result, code = parse_text(args.text, args.download)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(code)


if __name__ == "__main__":
    main()
