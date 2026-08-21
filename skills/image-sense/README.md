# Image-Sense（无模型图像感知）

在不使用任何模型的前提下"看懂图片"的替代路径：纯 Python 标准库，零依赖、离线、确定性。
适合：没有识图能力的环境 / 需要可解释、可验证、零成本的图像事实提取。

## 安装

无需安装任何依赖。需要 `python3`（标准库自带 zlib/struct/binascii 等）。

## 用法

```bash
# 人读报告（含 ASCII 预览）
python3 scripts/image_sense.py photo.png

# 结构化 JSON（供无识图能力的 API/下游消费）
python3 scripts/image_sense.py photo.png --json

# 只要事实，不要字符画
python3 scripts/image_sense.py photo.png --no-ascii

# 生成自测 PNG（冒烟验证用）
python3 scripts/image_sense.py --make-test-png t.png
```

## 能力一览

| 能力 | 说明 | 覆盖格式 |
|------|------|----------|
| 格式/尺寸/色深/色型/透明度 | 头部解析 | PNG/JPEG/BMP/PPM/GIF |
| 像素级还原 | PNG 全格式（含调色板/透明/1~16 位深）、BMP(BI_RGB 8/24/32)、PPM | PNG/BMP/PPM |
| 主色/明暗/饱和度/细节度 | 降采样统计 | 有像素的格式 |
| 感知哈希 dHash | 相似图检索 | 有像素的格式 |
| ASCII 预览 | 亮度→字符画 | 有像素的格式 |
| EXIF 元数据 | 相机/时间/软件/ISO/GPS | PNG/JPEG |
| JPEG 头部+近似质量 | SOF 尺寸 + DQT 量化表 | JPEG |
| GIF 帧数/透明标志 | 不跑 LZW | GIF |

## 诚实边界

- **不回答语义**："这是什么场景/情绪"超出无模型能力，如实说明，禁止编造；
- **JPEG 不做像素还原**（纯标准库解码需 Huffman+IDCT，量级过大）；给头部+EXIF+近似质量；
- 无法解析则降级输出 `pixel_error`；未知格式退出码 3。

## 目录

```
image-sense/
├── SKILL.md                      # 技能入口
├── README.md                     # 本文件
├── scripts/
│   └── image_sense.py            # 纯标准库图像感知（唯一入口）
├── references/
│   └── image-understanding-zh.md # 原理、能力表、诚实边界、接线说明
└── evals/
    └── evals.json                # 触发/质量/冒烟用例
```
