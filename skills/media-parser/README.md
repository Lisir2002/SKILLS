# media-parser · 多平台媒体解析技能

从抖音、B站、快手、小红书、微博、YouTube 等 **20+ 平台**分享链接中，解析出**无水印视频/图集地址**、标题、作者、封面、音频等元数据。

解析逻辑全部**本地运行**（不依赖第三方解析服务），基于开源项目 [media-parser](https://github.com/ucmao/media-parser)（MIT 许可）封装。

## 它能做什么

- ✅ 抖音 / TikTok / 快手 / 小红书 / B站 / 微博 / 西瓜 / AcFun / 好看视频 / 微视 / 梨视频 / 皮皮搞笑 / 皮皮虾 / 全民小视频 / 全民K歌 / 六间房 / 新片场 / 最右 / 逗拍 / 虎牙 / 绿洲 / 美拍 / 知乎 / YouTube
- ✅ 视频、图文图集、实况图、背景音乐
- ✅ 支持抖音 `a_bogus` 签名（本地生成，无需额外服务）
- ✅ 支持从整段"分享文案"中自动提取链接

## 安装

把本技能目录放入 AI 工具的 skills 目录（如 `.trae/skills/media-parser/`）。

### 脚本依赖（首次使用前）

```bash
pip install -r scripts/requirements.txt
# 即 requests / beautifulsoup4 / lxml / mini-racer / python-dotenv
```

检查依赖：`python3 scripts/parse_media.py --deps`

### 小红书高级解析（可选）

推荐流链接（`xsec_source=pc_feed`）需要登录 Cookie。复制 `scripts/.env.example` 为 `scripts/.env`，填入你的小红书 Cookie（含 `a1` 字段）即可。普通分享链接无需配置。

## 用法

在对话中触发，例如：

> 解析这个链接：`<抖音/B站/快手等分享链接>`
> 帮我去水印：`<链接>`
> 下载这个视频到本地：`<链接>`

AI 会自动运行脚本并把结果结构化反馈给你（平台/标题/作者/无水印链接/图集等）。

### 命令行直接使用

```bash
# 解析链接（或整段分享文案），输出 JSON
python3 scripts/parse_media.py "https://v.douyin.com/xxxx/"

# 解析并下载视频/封面到指定目录
python3 scripts/parse_media.py "<链接>" --download ./downloads

# 检查依赖
python3 scripts/parse_media.py --deps
```

## 目录结构

```
media-parser/
├── SKILL.md                        # 技能定义
├── README.md                       # 本文件
├── LICENSE-MEDIA-PARSER.txt        # 原项目 MIT 许可（含第三方代码，保留声明）
└── scripts/
    ├── parse_media.py              # 主入口：解析链接 → JSON（可选手动下载）
    ├── requirements.txt            # 依赖清单
    ├── .env.example                # 小红书 Cookie 可选配置示例
    └── mp/                         # media-parser 核心代码（src/utils/configs）
```

## 输出字段

| 字段 | 说明 |
|------|------|
| `platform` | 平台（抖音/哔哩哔哩/快手/小红书/微博/YouTube…） |
| `title` | 标题 |
| `video_url` | 无水印视频地址（图文作品为 null） |
| `cover_url` | 封面地址 |
| `author` | 作者 `{nickname, author_id, avatar}` |
| `image_list` | 图集无水印图片（视频作品为 []） |
| `audio_url` | 背景音乐地址 |

## 已知限制（如实说明）

### 实测可用性（2026-08 真实链接验证）

> 含补充测试：随机/自搜真实链接 + 深度内容校验（下载媒体字节验证 MP4/MP3/图片容器结构，并交叉核对标题/作者与源页面一致）。

| 平台 | 状态 | 说明 |
|------|------|------|
| 抖音 | ✅ 完全可用 | 4/4 通过（含自搜链接）；走 `aweme/detail` API + `a_bogus` 签名，**不受 2026-08 分享页改版影响**；解析出的视频均为有效 MP4（ftyp+moov+mdat），标题/作者与源页面一致 |
| 快手 | ⚠️ 基本可用 | 4/5 通过；`v.kuaishou.com` 短链与 `www.kuaishou.com/short-video/<id>` 直链均支持；个别作品被平台 API 拦截（页面可打开但服务端解析返回"不完整视频状态"）——已用主流开源方案（转发分享 Cookie 至 `/fw/photo/` 页）对比验证，同样失败，属作品级风控 |
| 小红书 | ⚠️ 需 Cookie | 本次测试的 `xhslink.com` 短链要求登录 Cookie 校验；配置 Cookie 后可用（推荐流链接必配） |
| 微博 | ✅ 可用（已验证） | 解析失败的样本经核实是**纯转发/文本微博（`page_info` 为空）**，非脚本缺陷；有视频的微博均成功。已用 `h5.video.weibo.com` 播放 API（需视频 oid）交叉验证结论一致 |
| 哔哩哔哩 | ✅ 可用（已验证） | 3/4 通过；失败样本 `BV1pBXMYeEkU` 经 `view` API 核实为 **`-404` 视频已删除**（与 UA/Referer/Cookie 无关）；解析出的视频/音频为有效 MP4 |
| 微视 | ✅ 可用（已验证） | 支持全部 4 类分享链接：`video.weishi.qq.com/<短码>`、`isee.weishi.qq.com`、`h5.weishi.qq.com/weishi/feed/<id>`（APP 默认复制格式，302 至 `m.weishi.qq.com`）、`m.weishi.qq.com`；实测视频为有效 MP4、封面为 JPEG |
| 西瓜视频 | ❌ 本次不可用 | 历史链接已下架；2026 有效链接经 `m.ixigua.com` 分享页与主流开源方案（yby6）对比均拿不到 `videoInfoRes`，需登录态/签名环境，服务端解析门槛高 |
| 皮皮虾 | ❌ 本次不可用 | 历史链接已失效，无法获取作品 ID |
| 知乎 | ❌ 暂不可用 | 无 cookie 请求被 403 反爬拦截（需 `z_c0`） |
| YouTube | ⚠️ 未验证 | 沙箱出口被 SSL 阻断；真实环境可能可用 |
| 其他平台 | 未逐一验证 | 依赖上游 media-parser 实现，可能受反爬影响 |

> 深度内容校验说明：对所有成功解析的视频下载前 2MB 字节，确认 MP4 容器（`ftyp=isom` + `moov` + `mdat`）、MP3（`ID3` 头）、图片（JPEG/PNG/WEBP 魔数）均正确，排除"返回错误页/占位文件"的情况。

### 其他说明

- **平台反爬**：部分平台（如知乎、部分 B站链接）会拦截无 cookie 的脚本请求，此时明确报错，属上游 media-parser 现状；
- **抖音风控变更**：`a_bogus` 签名算法由上游维护，抖音调整风控时可能暂时失效，重试即可（实测当前可用）；**注意抖音存在约 100 次/接口的请求硬性上限**，高频调用会触发限流（status 2863）；
- **小红书推荐流**：需要配置登录 Cookie（普通分享链接不受影响）。

## 合规声明

仅用于解析**你有权保存**的分享链接（个人素材管理、学习研究）。禁止用于爬取侵权内容、规避版权、传播未授权作品。原项目同样强调：仅用于学习交流和技术研究，严禁非法用途。

## 许可

技能封装部分遵循本仓库规范；内嵌解析代码遵循 [MIT 许可](LICENSE-MEDIA-PARSER.txt)（Copyright (c) 2025 ucmao）。