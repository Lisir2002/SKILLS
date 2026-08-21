---
name: "image-sense"
description: "Reads verifiable facts from images WITHOUT any model — pure stdlib, offline, zero dependency. Use when the user asks 识别图片/读取图片信息/图片是什么格式多大/主色调/明暗/EXIF/拍摄时间/相似图/图片内容 or provides an image path to analyze. Only outputs deterministic facts (format/size/colors/brightness/metadata/perceptual hash/ASCII preview); explicitly does NOT answer semantic 'what scene/mood' questions. Not for image generation, image editing, or OCR."
---

# Image-Sense（无模型图像感知）

## Purpose

在不使用任何模型（无视觉大模型、无 PIL/OpenCV、无 OCR 引擎、无外部命令、无网络）的前提下，
从图片里读出**可验证、可解释的结构化事实**。它"感知"但不"幻想"：只输出能从像素/字节
算出的确定性信息，绝不猜语义。当你或上层 API 没有识图能力时，这就是"看图"的替代路径。

## When to Use

- 用户提供图片路径/文件，问：这是什么格式、多大、什么颜色、明暗、有没有透明通道；
- 问：拍摄时间、相机型号、软件、GPS（EXIF 元数据）；
- 问：这张图和另一张图相似吗（感知哈希）；
- 需要把图片"翻译"成文字特征供无识图能力的下游使用；
- 需要一个人眼可读的 ASCII 预览来了解图片大致样子。

## When NOT to Use

- 问"这是什么场景 / 什么情绪 / 谁在做什么"——**语义理解超出无模型能力**，
  必须如实说明"需要识图模型"，禁止编造；
- 生成、编辑、修复图片（那是图像生成/处理）；
- 需要 OCR 识别图中文字（Tesseract 等外部工具不在零依赖范围内，见下）；
- 需要高精度物体识别/人脸识别（那是模型任务）。

## How to Use

单条命令，`python3` 直接跑（纯标准库，任意 Python3 环境）：

```bash
python3 scripts/image_sense.py <图片路径>            # 人读报告（含 ASCII 预览）
python3 scripts/image_sense.py <图片路径> --json     # 结构化 JSON（给 API/下游）
python3 scripts/image_sense.py <图片路径> --no-ascii # 只要事实不要字符画
python3 scripts/image_sense.py --make-test-png out.png  # 生成自测 PNG（冒烟验证）
```

支持格式：**PNG**（像素级全解析，含调色板/透明/1~16 位深）、**BMP**（BI_RGB 8/24/32）、
**PPM**（P3/P6）、**WebP**（VP8 有损/VP8L 无损头部+尺寸+动画帧+EXIF，像素级需 Pillow）、
**JPEG**（头部+EXIF+近似质量，像素级需 Pillow）、**GIF**（尺寸/帧数/透明标志）。

> 可选解码器（**不是模型**）：若环境装了 Pillow，WebP/JPEG 等纯标准库无法还原像素的格式
> 会自动用 Pillow 只做"位图解码"，随后所有特征/哈希/预览仍由本脚本的无模型算法计算；
> 未装 Pillow 则如实降级（给头部+EXIF，无像素特征），绝不假装。

输出哪些事实：
- `format / width / height / bit_depth / color_type / has_alpha / file_size_kb`
- EXIF：`拍摄时间 / 相机厂商 / 相机型号 / 软件 / ISO / GPS{lat,lon}`
- 像素特征：`主色(hex+占比) / 明暗 / 饱和度 / 细节度 / 透明占比`
- `dhash` 感知哈希（相似图检索用）、`ascii` ASCII 预览

## Workflow（三步：跑脚本 → 读事实 → 交输出）

1. **跑脚本**：`python3 scripts/image_sense.py <图片路径> --json`（要给人看时去掉 `--json`）。
2. **读事实**：把 `format/size/exif/features/dhash` 原样读给用户或传给下游；`exif` 空、`pixel_error`
   存在、`format=UNKNOWN` 都如实说明，不补猜测。
3. **交输出 + 边界提醒**：输出结构化事实后，若用户想要"这是什么/什么情绪"等语义，明确告知
   "本技能无模型，只能给事实；语义需要识图模型"。

## Failure Modes（失败模式与处置）

| 症状 | 含义 | 处置 |
|------|------|------|
| `format: UNKNOWN`（退出码 3） | 不支持或损坏的格式 | 告知用户支持 PNG/JPEG/BMP/PPM/GIF/WebP；损坏文件无法读 |
| `pixel_error` | 头部可读但像素无法还原（如 JPEG 无像素级、BMP 非 BI_RGB） | 仍给头部+EXIF；像素类特征（主色/哈希/预览）不输出 |
| `exif: {}` | 图片无元数据（截图/转发常见） | 如实说"无 EXIF"，不编造拍摄时间/相机 |
| 无像素特征（`pixel_error`） | 格式需解码器但环境未装 Pillow（WebP/JPEG）或格式特殊 | 给头部+EXIF；建议装 Pillow（仅解码库）以补像素特征 |
| 用户要语义/OCR/人脸识别 | 超出无模型边界 | 明确拒绝并解释；OCR 需 Tesseract（外部工具，非零依赖） |

## Output Rules（诚实边界）

1. **只给可验证事实**：每个输出都能从字节/像素算出；无法解析就降级（给头部 + `pixel_error`），
   绝不填猜测值。
2. **不回答语义**：被问"这是什么/什么情绪/什么场景"时，明确说"本技能无模型，
   只能给颜色/尺寸/元数据等事实；语义理解需要接入识图模型"。
3. **未知格式返回退出码 3**：便于上层脚本识别"这张图看不了"。
4. **交叉校验思维**：需要时把本技能的确定性特征（主色、明暗、尺寸）当作"锚"，
   用来校验任何外部识图结果的幻觉——先讲得清的事实，再谈语义。

## Files

- `scripts/image_sense.py` —— 唯一入口：纯标准库图像感知（PNG 像素解码 / EXIF / 特征统计 / dHash / ASCII）
- `references/image-understanding-zh.md` —— 无模型看图的原理、能力表、诚实边界、接线说明
