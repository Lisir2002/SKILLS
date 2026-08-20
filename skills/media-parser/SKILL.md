---
name: "media-parser"
description: "Use when the user sends a 抖音/快手/小红书/B站/微博/YouTube short-video share link or paste 分享文案 and asks to 解析/去水印/下载/提取视频/查看详情. Parses 20+ platforms (Douyin/TikTok/Bilibili/Kuaishou/Xiaohongshu/Weibo/YouTube) into structured metadata: no-watermark video, images, cover, title, author, audio. Not for uploading content or operating on non-media links."
---

# Media Parser（多平台媒体解析）

从抖音、B站、快手、小红书、微博、YouTube 等 **20+ 平台**的分享链接中，解析出结构化元数据：无水印视频地址、图集、封面、标题、作者、音频。基于开源项目 [media-parser](https://github.com/ucmao/media-parser)（MIT）封装，解析逻辑全部在本地脚本中完成，不依赖第三方解析服务。

## When to Use

- 用户发来抖音/快手/小红书/B站/微博等平台的**视频或图集分享链接**，希望：
  - 解析（"解析一下这个链接"）
  - 去水印（"帮我下载无水印的"）
  - 提取视频/图集（"提取这个视频"）
  - 查看详情（"这个视频的信息"）
- 用户粘贴整段**分享文案**（含链接和乱码），从中提取并解析链接。
- 用户想下载视频/封面到本地。

## When NOT to Use

- 非媒体链接（普通网页、文档、代码仓库链接）——本技能只处理视频/图集分享链接；
- 用户要"上传视频/发布内容"——本技能只读解析，不发布；
- 纯图片链接（非图集分享页）。

## Workflow

1. **确认输入**：获取用户提供的链接或包含链接的分享文案。若无链接，先向用户索要。

2. **检查依赖**（首次使用）：
   ```bash
   python3 parse_media.py --deps
   ```
   若提示缺少依赖，先安装（脚本目录下的 `requirements.txt`）：
   ```bash
   pip install -r requirements.txt
   ```

3. **执行解析**：
   ```bash
   python3 parse_media.py "<链接 或 分享文案>"
   ```
   输出为 JSON，结构：
   - `data.platform` — 平台（抖音/哔哩哔哩/快手/小红书/微博/YouTube 等）
   - `data.title` — 标题
   - `data.video_url` — 无水印视频地址（图集作品为 null）
   - `data.cover_url` — 封面地址
   - `data.author` — `{nickname, author_id, avatar}`
   - `data.image_list` — 图集无水印图片列表（视频作品为 []）
   - `data.audio_url` — 背景音乐地址

4. **反馈结果**：把解析出的元数据**结构化反馈给用户**：
   - 平台 + 标题 + 作者；
   - 无水印视频地址（用 markdown 链接呈现，方便点击/复制）；
   - 若有图集：给出图片数量与图片链接；
   - 若有封面/音频：一并给出。

5. **可选下载**（用户要求"下载"时）：
   ```bash
   python3 parse_media.py "<链接>" --download <目录>
   ```
   结果中会多出 `data.downloads`（`video_file` / `cover_file` 本地路径）。

## Output Spec

- 默认只输出解析结果，用**简洁的 markdown 反馈**：平台、标题、作者、无水印链接（可点击）、图集数量、封面/音频。
- 链接以可点击 markdown 形式给出；不要省略任何有效地址。
- 解析失败时如实反馈脚本返回的 `msg`（如"该链接尚未支持提取""提取媒体内容失败""需要小红书登录 Cookie"），并说明可能原因（平台反爬/签名失效/需要 Cookie），不要编造结果。

## Failure Modes

> 以下"失败"均经 2026-08 复测归因（含借鉴主流开源方案对比验证），确认绝大多数是**内容本身/平台限制**，而非脚本缺陷。

- **平台反爬**（实测）：知乎（403）、西瓜/皮皮虾历史旧链接（内容已下架或 JS 渲染）无 cookie 时难以提取；如实告知用户。
- **部分快手作品被 API 拦截**：个别作品页面浏览器可打开，但服务端解析被平台 block（返回"不完整视频状态"）。已用主流开源方案（转发分享 Cookie 至 `/fw/photo/` 页）对比验证，同样失败，属作品级风控，非脚本问题；换链接或重试。
- **部分微博为无视频内容**：`m.weibo.cn/statuses/show` 返回 `page_info` 为空时，说明该微博是纯文本/转发微博，本身不含视频，报"提取媒体内容失败"是**正确行为**（已用 h5.video.weibo.com 播放 API 交叉验证，该 API 需视频 oid、对文本微博同样返回空）。
- **B站视频已删除**：部分 B 站 BV 号在 `view` API 返回 `code=-404`（"啥都木有"），即视频已删除/不存在，与 UA/Referer/Cookie 无关；其余链接正常解析。
- **抖音签名/接口变更**：`a_bogus` 签名由上游维护，若抖音改风控可能暂时失效；重试或提示用户。注意抖音有约 100 次/接口的请求硬性上限，高频调用触发限流（status 2863）。
- **小红书高级链接需要 Cookie**：推荐流链接（`xsec_source=pc_feed`）需配置登录 Cookie（见 README 的 `.env` 配置）；部分短链在未配置 Cookie 时也会提示需要校验，配置后即可。
- **西瓜视频服务端解析门槛高**：当前有效链接经 `m.ixigua.com` 分享页与主流开源方案（yby6）对比均拿不到 `videoInfoRes`，需登录态/签名环境，暂列为不可用。
- **YouTube/沙箱网络**：部分网络出口（如 CI 沙箱）会阻断 YouTube 等境外站点，属环境限制而非脚本缺陷。
- **图文 vs 视频**：图文作品 `video_url` 为 null、有 `image_list`；视频作品相反。按字段实际值反馈，不要臆断。
- **链接过期/失效**：跟随重定向失败时明确报错。

## Responsible Use

- 本技能仅用于解析**用户自己获得的、有权保存的**分享链接，用于个人素材管理、学习研究。
- **禁止**用于：批量爬取侵权内容、规避版权保护、传播他人未授权作品、任何商业盗用。
- 若用户意图明显违规（如要求爬取他人私有/付费内容），拒绝执行并说明。

## Dependencies

- Python 3.8+；`requests`、`beautifulsoup4`、`lxml`、`mini-racer`（执行抖音签名 JS）、`python-dotenv`（可选 .env 配置）。
- 安装：`pip install -r requirements.txt`。
- 抖音解析需要联网访问抖音接口；部分平台受反爬限制，属上游现状。

## References

- 解析器源码（基于 media-parser MIT）：`scripts/mp/`（含 `src/parsers/`、`utils/`、`configs/`）
- 依赖清单：`scripts/requirements.txt`
- 原项目与许可：`LICENSE-MEDIA-PARSER.txt`

## Examples

**输入**
> 帮我解析一下：8.88 复制打开抖音，看看【阿泽的作品】福州的作业本上有非常美丽的地标 https://www.douyin.com/note/7616399587141737704  l@c.At qEh:/ 06/18

**输出（markdown 反馈）**
> **解析结果 · 抖音图文**
> - 标题：福州的作业本上有非常美丽的地标
> - 作者：阿泽
> - 图集：共 2 张无水印图片
> - 音频：[背景音乐](https://...mp3)
> - 图片 1：[无水印原图](https://p3-pc-sign.douyinpic.com/...)
> - 图片 2：[无水印原图](https://p3-pc-sign.douyinpic.com/...)
>
> （如需下载到本地，告诉我目录即可，我会用 --download 保存）
