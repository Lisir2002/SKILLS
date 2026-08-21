#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""image_sense.py —— 无模型图像感知（纯标准库，离线，零依赖）

作用：
  在不使用任何模型（无视觉大模型、无 PIL/OpenCV、无 OCR 引擎、无外部命令）的前提下，
  用纯 Python 标准库从图片里"读出"可验证、可解释的结构化信息：
    格式 / 尺寸 / 色深 / 色型 / 透明度 / 文件大小
    EXIF 元数据（拍摄时间 / 相机 / GPS / 软件）
    主色 / 明暗 / 色彩饱和度 / 细节复杂度
    感知哈希（dHash，用于相似图检索）
    ASCII 预览（人眼可直接看像素长什么样）

  它"感知"但不"幻想"：只输出能从像素/字节里算出来的事实，绝不猜语义。
  "这张图是什么场景 / 什么情绪"这类语义问题，本脚本明确拒绝回答（没有模型就诚实说不懂）。

原理（全部纯标准库）：
  - PNG：解析 chunk（IHDR/PLTE/IDAT/eXIf）→ zlib 解压 → 按行 unfilter（None/Sub/Up/Average/Paeth）
        还原像素，支持位深 1/2/4/8/16、色型 gray/rgb/palette/gray+alpha/rgba。
  - JPEG：解析 marker 头部（SOF 得尺寸）+ APP1 EXIF + DQT 量化表近似质量；不做 DCT 像素还原
        （JPEG 像素级解码需几十倍代码量，超出"零依赖"目标，由头部/元数据给出全部可算信息）。
  - BMP / PPM：直接还原像素。
  - GIF：解析头部尺寸 + 帧数 + 透明度标志（不跑 LZW）。
  - EXIF：解析 TIFF IFD0 + GPS IFD。

用法：
  python3 image_sense.py <图片路径>
  python3 image_sense.py <图片路径> --json        # 结构化输出（供上层/API 消费）
  python3 image_sense.py <图片路径> --no-ascii     # 关掉 ASCII 预览
  python3 image_sense.py --make-test-png out.png   # 生成一张自测 PNG（冒烟用）
"""
import argparse
import binascii
import json
import struct
import sys
import zlib

# ---------------------------------------------------------------- 基础工具

def _num(v, digits=1):
    """数值格式化，None 安全。"""
    if v is None:
        return None
    return round(float(v), digits)


# ---------------------------------------------------------------- PNG

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
_CT_NAMES = {0: "灰度 gray", 2: "真彩 rgb", 3: "索引调色板 palette", 4: "灰度+alpha", 6: "真彩+alpha rgba"}
_FILTERS = 5


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _unfilter_scanline(line, prev, bpp):
    """对单行做逆滤波（返回可用的 RGB 字节流）。line 已去掉行首滤波类型字节。"""
    f = line[0]
    raw = bytearray(line[1:])
    n = len(raw)
    if f == 0:
        pass
    elif f == 1:  # Sub
        for i in range(bpp, n):
            raw[i] = (raw[i] + raw[i - bpp]) & 0xFF
    elif f == 2:  # Up
        for i in range(n):
            raw[i] = (raw[i] + prev[i]) & 0xFF
    elif f == 3:  # Average
        for i in range(n):
            left = raw[i - bpp] if i >= bpp else 0
            raw[i] = (raw[i] + ((left + prev[i]) >> 1)) & 0xFF
    elif f == 4:  # Paeth
        for i in range(n):
            left = raw[i - bpp] if i >= bpp else 0
            up = prev[i]
            upleft = prev[i - bpp] if i >= bpp else 0
            raw[i] = (raw[i] + _paeth(left, up, upleft)) & 0xFF
    return bytes(raw)


def parse_png(data):
    """返回 dict；pixels 为 (r,g,b,a) 列表（或 None 表示无法还原）。"""
    if data[:8] != _PNG_MAGIC:
        raise ValueError("不是 PNG")
    pos, w, h, bit_depth, color_type = 8, None, None, None, None
    idat, palette, exif = b"", b"", b""
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        cdata = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            w, h, bit_depth, color_type = struct.unpack(">IIBB", cdata[:10])
        elif ctype == b"PLTE":
            palette = cdata
        elif ctype == b"IDAT":
            idat += cdata
        elif ctype == b"eXIf":
            exif = cdata
        pos += 12 + length

    info = {
        "format": "PNG", "width": w, "height": h, "bit_depth": bit_depth,
        "color_type": color_type, "color_type_name": _CT_NAMES.get(color_type),
        "has_alpha": color_type in (4, 6),
        "exif": parse_exif(exif) if exif else {},
    }
    pixels = None
    try:
        raw = zlib.decompress(idat)
        channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color_type]
        bytes_per_px = (bit_depth + 7) // 8
        bpp = channels * bytes_per_px
        stride = w * bpp
        rows_raw, prev = [], bytes(stride)
        p = 0
        for _ in range(h):
            if p + 1 + stride > len(raw):
                raise ValueError("IDAT 数据不完整")
            rows_raw.append(_unfilter_scanline(raw[p:p + 1 + stride], prev, bpp))
            prev = rows_raw[-1]
            p += 1 + stride
        pixels = _decode_png_pixels(rows_raw, w, h, bit_depth, color_type, palette)
    except Exception as exc:  # 像素级失败不影响头部/元数据输出
        info["pixel_error"] = str(exc)
    info["pixels"] = pixels
    return info


def _decode_png_pixels(rows, w, h, bit_depth, color_type, palette):
    """把 unfilter 后的字节行解码成 (r,g,b,a) 列表。"""
    pix = []
    bytes_per_px = (bit_depth + 7) // 8
    if color_type == 2:  # rgb
        for row in rows:
            for i in range(w):
                r, g, b = row[i * 3], row[i * 3 + 1], row[i * 3 + 2]
                pix.append((r, g, b, 255))
    elif color_type == 6:  # rgba
        for row in rows:
            for i in range(w):
                r, g, b, a = row[i * 4], row[i * 4 + 1], row[i * 4 + 2], row[i * 4 + 3]
                pix.append((r, g, b, a))
    elif color_type == 0:  # gray
        for row in rows:
            for i in range(w):
                v = row[i * bytes_per_px] if bytes_per_px == 1 else row[i * 2]
                pix.append((v, v, v, 255))
    elif color_type == 4:  # gray+alpha
        for row in rows:
            for i in range(w):
                v = row[i * 2] if bytes_per_px == 1 else row[i * 4]
                a = row[i * 2 + 1] if bytes_per_px == 1 else row[i * 4 + 2]
                pix.append((v, v, v, a))
    elif color_type == 3:  # palette
        plen = len(palette) // 3
        for row in rows:
            idxs = _unpack_indexes(row, w, bit_depth)
            for idx in idxs:
                i = idx * 3
                if idx < plen:
                    pix.append((palette[i], palette[i + 1], palette[i + 2], 255))
                else:
                    pix.append((0, 0, 0, 255))
    return pix


def _unpack_indexes(row_bytes, count, bit_depth):
    """把低位数像素解成索引序列。"""
    if bit_depth == 8:
        return list(row_bytes[:count])
    if bit_depth == 16:
        return [row_bytes[i * 2] for i in range(count)]
    bits = bit_depth
    idxs = []
    mask = (1 << bits) - 1
    for i in range(count):
        bitpos = i * bits
        bytepos, offset = divmod(bitpos, 8)
        val = row_bytes[bytepos] >> (8 - bits - offset) if offset + bits <= 8 else 0
        idxs.append(val & mask)
    return idxs


# ---------------------------------------------------------------- JPEG

_JPEG_MAGIC = b"\xff\xd8"


def parse_jpeg(data):
    """JPEG：头部尺寸 + EXIF + DQT 近似质量；不做像素还原。"""
    if data[:2] != _JPEG_MAGIC:
        raise ValueError("不是 JPEG")
    info = {"format": "JPEG", "width": None, "height": None,
            "bit_depth": 8, "color_type_name": "YCbCr（可含 alpha 分量）",
            "has_alpha": False, "exif": {}, "pixels": None, "quality_approx": None}
    pos, size, quant_sum, n_quant = 2, 0, 0, 0
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            pos += 1
            continue
        marker = data[pos + 1]
        if marker in (0xD8, 0x01, 0xD9):
            pos += 2
            continue
        length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        seg = data[pos + 4:pos + 2 + length]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB):
            info["height"], info["width"] = struct.unpack(">HH", seg[1:5])
            info["bit_depth"] = seg[0]
        elif marker == 0xE1 and seg[:6] == b"Exif\x00\x00":
            info["exif"] = parse_exif(seg[6:]) or {}
        elif marker == 0xDB:  # 量化表
            p = 0
            while p < len(seg):
                pq = seg[p] >> 4
                n_quant += 1
                quant_sum += sum(seg[p + 1:p + 65])
                p += 1 + 64
        pos += 2 + length
    if n_quant:
        avg = quant_sum / n_quant / 64.0
        # 经验映射：平均量化步长越大质量越低（近似值，仅供参考）
        info["quality_approx"] = max(1, min(100, int(round(100 - (avg - 1) / 16.0 * 100))))
    return info


# ---------------------------------------------------------------- BMP

def parse_bmp(data):
    if data[:2] != b"BM":
        raise ValueError("不是 BMP")
    offset = struct.unpack("<I", data[10:14])[0]
    dib_size = struct.unpack("<I", data[14:18])[0]
    w = struct.unpack("<i", data[18:22])[0]
    h = struct.unpack("<i", data[22:26])[0]
    bpp = struct.unpack("<H", data[28:30])[0]
    comp = struct.unpack("<I", data[30:34])[0]
    top_down = h < 0
    h = abs(h)
    info = {
        "format": "BMP", "width": w, "height": h, "bit_depth": bpp,
        "color_type_name": f"{bpp}bpp", "has_alpha": bpp in (32,),
        "exif": {}, "pixels": None, "compression": comp,
    }
    if comp not in (0,) or bpp not in (24, 32, 8):
        info["pixel_error"] = f"压缩/位深 {comp}/{bpp} 非零依赖目标（BI_RGB 8/24/32 才还原像素）"
        return info
    pal = []
    if bpp == 8:
        pal = [tuple(data[i:i + 4][:3]) for i in range(14 + dib_size, 14 + dib_size + 256 * 4)]
    stride = ((w * bpp + 31) // 32) * 4
    pix = []
    for row in range(h):
        src_row = row if top_down else h - 1 - row
        base = offset + src_row * stride
        for x in range(w):
            if bpp == 24:
                b, g, r = data[base + x * 3], data[base + x * 3 + 1], data[base + x * 3 + 2]
                pix.append((r, g, b, 255))
            elif bpp == 32:
                b, g, r, a = data[base + x * 4], data[base + x * 4 + 1], data[base + x * 4 + 2], data[base + x * 4 + 3]
                pix.append((r, g, b, a))
            else:
                pix.append((*pal[data[base + x]], 255))
    info["pixels"] = pix
    return info


# ---------------------------------------------------------------- PPM

def parse_ppm(data):
    if data[:2] not in (b"P3", b"P6"):
        raise ValueError("不是 PPM")
    mode = data[:2]
    parts, p = [], 2
    while len(parts) < 4:
        while p < len(data) and data[p:p + 1].isspace():
            p += 1
        if data[p:p + 1] == b"#":
            while p < len(data) and data[p:p + 1] != b"\n":
                p += 1
            continue
        start = p
        while p < len(data) and not data[p:p + 1].isspace():
            p += 1
        parts.append(data[start:p])
        if p < len(data) and data[p:p + 1].isspace():
            p += 1
    w, h, maxv = int(parts[0]), int(parts[1]), int(parts[2])
    info = {"format": "PPM", "width": w, "height": h, "bit_depth": maxv,
            "color_type_name": "P6 二进制 RGB" if mode == b"P6" else "P3 ASCII RGB",
            "has_alpha": False, "exif": {}, "pixels": None}
    pix = []
    if mode == b"P6":
        body = data[p:]
        for i in range(w * h):
            r, g, b = body[i * 3], body[i * 3 + 1], body[i * 3 + 2]
            pix.append((r, g, b, 255))
    else:
        nums = []
        while p < len(data):
            tok = []
            while p < len(data) and data[p:p + 1].isspace():
                p += 1
            if data[p:p + 1] == b"#":
                while p < len(data) and data[p:p + 1] != b"\n":
                    p += 1
                continue
            while p < len(data) and not data[p:p + 1].isspace():
                tok.append(chr(data[p]))
                p += 1
            if tok:
                nums.append(int("".join(tok)))
        for i in range(0, len(nums) - 2, 3):
            pix.append((nums[i], nums[i + 1], nums[i + 2], 255))
    info["pixels"] = pix
    return info


# ---------------------------------------------------------------- GIF

def parse_gif(data):
    if data[:6] not in (b"GIF87a", b"GIF89a"):
        raise ValueError("不是 GIF")
    w, h = struct.unpack("<HH", data[6:10])
    packed = data[10]
    has_global = bool(packed & 0x80)
    gct_size = 2 << (packed & 0x07) if has_global else 0
    frames = 0
    has_transparent = False
    pos = 13
    if has_global:
        pos += 3 * gct_size
    while pos + 1 < len(data):
        b = data[pos]
        if b == 0x3B:  # 结束
            break
        if b == 0x2C:  # 图像描述符
            frames += 1
            pos += 10
            lzw_min = data[pos] if pos < len(data) else 0
            pos += 1
            if pos < len(data):
                sub_len = data[pos]
                pos += 1 + sub_len
                # 跳到后续子块（LZW 数据，不解码）
                while pos < len(data) and data[pos]:
                    pos += 1 + data[pos]
                pos += 1
        elif b == 0x21:  # 扩展块
            label = data[pos + 1]
            if label == 0xF9:  # 图形控制扩展
                block_len = data[pos + 2] if pos + 2 < len(data) else 0
                if block_len >= 4:
                    flags = data[pos + 3]
                    if flags & 0x01:
                        has_transparent = True
                pos += 2 + 1 + block_len
            else:
                pos += 2
                while pos < len(data) and data[pos]:
                    pos += 1 + data[pos]
                pos += 1
        else:
            break
    return {
        "format": "GIF", "width": w, "height": h, "bit_depth": 8,
        "color_type_name": "索引色（LZW 压缩）", "has_alpha": False,
        "has_transparency_flag": has_transparent, "frames": max(frames, 1),
        "exif": {}, "pixels": None,
    }


# ---------------------------------------------------------------- EXIF (TIFF)

_TAG_NAMES = {
    0x010E: "描述", 0x010F: "相机厂商", 0x0110: "相机型号", 0x0112: "方向",
    0x0131: "软件", 0x0132: "修改时间", 0x829A: "曝光时间", 0x829D: "光圈",
    0x8827: "ISO", 0x9003: "拍摄时间", 0x920A: "焦距",
}
_TYPE_SIZES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 9: 4, 10: 8}


def _exif_value(bo, tiff, typ, cnt, val_bytes):
    size = _TYPE_SIZES.get(typ, 1) * cnt
    if size > 4:
        off = struct.unpack(bo + "I", val_bytes)[0]
        raw = tiff[off:off + size]
    else:
        raw = val_bytes[:size]
    if typ == 2:  # ASCII
        return raw.split(b"\x00")[0].decode("utf-8", "replace")
    if typ in (3, 4, 9):
        fmt = bo + {3: "H", 4: "I", 9: "i"}[typ]
        vals = struct.unpack(fmt * cnt, raw[:size])
        return vals[0] if cnt == 1 else list(vals)
    if typ in (5, 10):  # 有理数
        fmt = bo + {5: "I", 10: "i"}[typ]
        vals = struct.unpack(fmt * cnt * 2, raw[:size])
        out = []
        for i in range(0, len(vals), 2):
            out.append(vals[i] / vals[i + 1] if vals[i + 1] else None)
        return out[0] if cnt == 1 else out
    return None


def _read_ifd(bo, tiff, off):
    if off + 2 > len(tiff):
        return {}, None
    n = struct.unpack(bo + "H", tiff[off:off + 2])[0]
    entries = {}
    for i in range(n):
        e = off + 2 + 12 * i
        if e + 12 > len(tiff):
            break
        tag, typ, cnt = struct.unpack(bo + "HHI", tiff[e:e + 8])
        val = tiff[e + 8:e + 12]
        entries[tag] = _exif_value(bo, tiff, typ, cnt, val)
    next_off_off = off + 2 + 12 * n
    nxt = struct.unpack(bo + "I", tiff[next_off_off:next_off_off + 4])[0] if next_off_off + 4 <= len(tiff) else None
    return entries, nxt


def _gps_dms(bo, tiff, val):
    """把 GPS 坐标（三元有理数）转十进制度。"""
    if not val or not isinstance(val, list) or len(val) < 3:
        return None
    try:
        deg, mn, sec = val[0], val[1], val[2]
        d = float(deg or 0) + float(mn or 0) / 60 + float(sec or 0) / 3600
        return round(d, 6)
    except (TypeError, ValueError):
        return None


def parse_exif(tiff):
    """解析 TIFF 块为可读 dict；失败返回 {}（EXIF 缺失很常见，不报错）。"""
    if len(tiff) < 8 or tiff[:2] not in (b"II", b"MM"):
        return {}
    bo = "<" if tiff[:2] == b"II" else ">"
    try:
        ifd0, _ = _read_ifd(bo, tiff, struct.unpack(bo + "I", tiff[4:8])[0])
    except Exception:
        return {}
    out = {}
    for tag, name in _TAG_NAMES.items():
        if tag in ifd0 and ifd0[tag] is not None:
            out[name] = ifd0[tag]
    if 0x8825 in ifd0 and isinstance(ifd0[0x8825], int):
        try:
            gps, _ = _read_ifd(bo, tiff, ifd0[0x8825])
            latref = gps.get(1, "")
            lonref = gps.get(3, "")
            lat = _gps_dms(bo, tiff, gps.get(2))
            lon = _gps_dms(bo, tiff, gps.get(4))
            if lat is not None and lon is not None:
                if latref == "S":
                    lat = -lat
                if lonref == "W":
                    lon = -lon
                out["GPS"] = {"lat": lat, "lon": lon}
        except Exception:
            pass
    return out


# ---------------------------------------------------------------- 分析器

def _downsample(pix, w, h, max_dim=128):
    """盒子降采样，控制计算量。返回 (pw, ph, 降采样像素) 与 alpha 掩码。"""
    if max(w, h) <= max_dim:
        return w, h, pix
    scale = max_dim / max(w, h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    xs = [int(x / nw * w) for x in range(nw)]
    ys = [int(y / nh * h) for y in range(nh)]
    out = []
    for y in ys:
        for x in xs:
            out.append(pix[y * w + x])
    return nw, nh, out


def analyze_pixels(pix, w, h):
    """从像素列表算结构化特征。pix 为 (r,g,b,a) 列表。"""
    if not pix:
        return None
    nw, nh, p = _downsample(pix, w, h)
    n = len(p)
    opaque = [q for q in p if q[3] > 128] or p
    # 明暗
    lum_total = 0.0
    # 主色（量化到 5^3 桶）
    buckets = {}
    for (r, g, b, a) in opaque:
        lum_total += 0.299 * r + 0.587 * g + 0.114 * b
        key = (r // 51, g // 51, b // 51)
        if key not in buckets:
            buckets[key] = [0, 0, 0, 0]  # sum r,g,b,count
        bkt = buckets[key]
        bkt[0] += r
        bkt[1] += g
        bkt[2] += b
        bkt[3] += 1
    avg_lum = lum_total / len(opaque)
    top = sorted(buckets.items(), key=lambda kv: -kv[1][3])[:3]
    colors = []
    for key, (sr, sg, sb, cnt) in top:
        r, g, b = sr // cnt, sg // cnt, sb // cnt
        colors.append({"rgb": [r, g, b], "hex": "#%02X%02X%02X" % (r, g, b),
                       "ratio": round(cnt / len(opaque), 3)})
    # 色彩饱和度（平均 max-min）
    sat = 0.0
    for (r, g, b, _a) in opaque:
        sat += (max(r, g, b) - min(r, g, b)) / 255.0
    sat /= len(opaque)
    # 细节度（相邻像素亮度差占比）
    diffs = 0
    for i in range(1, len(opaque)):
        r0 = 0.299 * opaque[i][0] + 0.587 * opaque[i][1] + 0.114 * opaque[i][2]
        r1 = 0.299 * opaque[i - 1][0] + 0.587 * opaque[i - 1][1] + 0.114 * opaque[i - 1][2]
        if abs(r0 - r1) > 24:
            diffs += 1
    detail = diffs / max(1, len(opaque) - 1)
    # 透明度占比
    alpha_ratio = sum(1 for q in p if q[3] < 128) / n
    return {
        "dominant_colors": colors,
        "brightness": _num(avg_lum, 0),
        "brightness_label": "暗" if avg_lum < 85 else ("亮" if avg_lum > 170 else "中等"),
        "saturation": _num(sat, 2),
        "saturation_label": "灰" if sat < 0.1 else ("淡" if sat < 0.3 else "彩"),
        "detail": _num(detail, 3),
        "detail_label": "简" if detail < 0.05 else ("中" if detail < 0.2 else "繁"),
        "transparent_ratio": _num(alpha_ratio, 3),
    }


def dhash(pix, w, h, size=8):
    """dHash：9x8 灰度相邻比较 → 64 位十六进制。用于相似图检索。"""
    if not pix:
        return None
    import statistics
    gw, gh = size + 1, size
    xs = [int(x / gw * w) for x in range(gw)]
    ys = [int(y / gh * h) for y in range(gh)]
    grays = []
    for y in ys:
        row = []
        for x in xs:
            r, g, b, _a = pix[y * w + x]
            row.append(0.299 * r + 0.587 * g + 0.114 * b)
        grays.append(row)
    bits = []
    for y in range(gh):
        for x in range(gw - 1):
            bits.append(1 if grays[y][x] > grays[y][x + 1] else 0)
    return "{:016x}".format(int("".join("1" if b else "0" for b in bits), 2))


def ascii_preview(pix, w, h, cols=64, rows=16):
    if not pix:
        return None
    chars = " .:-=+*#%@"
    gw, gh = cols, rows
    xs = [int(x / gw * w) for x in range(gw)]
    ys = [int(y / gh * h) for y in range(gh)]
    out = []
    for y in ys:
        line = []
        for x in xs:
            r, g, b, _a = pix[y * w + x]
            v = 0.299 * r + 0.587 * g + 0.114 * b
            line.append(chars[int(v / 256 * len(chars))])
        out.append("".join(line))
    return out


# ---------------------------------------------------------------- 主流程

def detect(data):
    if data[:8] == _PNG_MAGIC:
        return parse_png(data)
    if data[:2] == _JPEG_MAGIC:
        return parse_jpeg(data)
    if data[:2] == b"BM":
        return parse_bmp(data)
    if data[:2] in (b"P3", b"P6"):
        return parse_ppm(data)
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return parse_gif(data)
    return {"format": "UNKNOWN", "error": "无法识别的图片格式（支持 PNG/JPEG/BMP/PPM/GIF）"}


def make_test_png(path, w=64, h=32):
    """生成一张自测 PNG：横向渐变 + 红色方块 + 暗色底，便于冒烟验证。"""
    rows = bytearray()
    for y in range(h):
        rows.append(0)  # filter None
        for x in range(w):
            r = int(x / w * 255)
            g = int(y / h * 255)
            b = 40
            if 12 <= x < 30 and 6 <= y < 22:  # 红色方块
                r, g, b = 255, 0, 0
            elif x < 6 or x >= w - 6:  # 两侧深色
                r, g, b = 10, 10, 10
            rows += bytes((r, g, b))

    def chunk(typ, cdata):
        return (struct.pack(">I", len(cdata)) + typ + cdata +
                struct.pack(">I", binascii.crc32(typ + cdata) & 0xFFFFFFFF))

    png = _PNG_MAGIC
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(rows)))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return w, h


def render(info, show_ascii=True):
    lines = []
    w, h = info.get("width"), info.get("height")
    lines.append("== 图像感知（无模型 · 纯标准库） ==")
    if w and h:
        lines.append(f"格式      : {info.get('format')}   尺寸 {w}x{h} "
                     f"({round(w / h, 2)} : 1)")
    else:
        lines.append(f"格式      : {info.get('format')}   尺寸：未知（无法解析头部）")
    if info.get("bit_depth"):
        lines.append(f"位深/色型 : {info.get('bit_depth')} bit / {info.get('color_type_name')}")
    if info.get("frames"):
        lines.append(f"帧数      : {info.get('frames')}")
    if info.get("has_transparency_flag") is not None:
        lines.append(f"透明标志  : {'有' if info.get('has_transparency_flag') else '无'}")
    if info.get("quality_approx"):
        lines.append(f"质量(近似): {info['quality_approx']}（JPEG DQT 量化表估算）")
    exif = info.get("exif") or {}
    if exif:
        lines.append("-- EXIF 元数据 --")
        for k, v in exif.items():
            if k == "GPS":
                lines.append(f"  GPS : {v['lat']}, {v['lon']}")
            else:
                lines.append(f"  {k} : {v}")
    else:
        lines.append("-- EXIF 元数据 -- 无")
    if info.get("pixel_error"):
        lines.append(f"-- 像素级 -- 无法还原（{info['pixel_error']}）")
    feats = info.get("features")
    if feats:
        lines.append("-- 像素特征 --")
        for c in feats["dominant_colors"]:
            lines.append(f"  主色 {c['hex']}  RGB{c['rgb']}  占比 {c['ratio']:.0%}")
        lines.append(f"  明暗 : {feats['brightness_label']} ({feats['brightness']})")
        lines.append(f"  色彩 : {feats['saturation_label']} (饱和度 {feats['saturation']})")
        lines.append(f"  细节 : {feats['detail_label']} (差异率 {feats['detail']})")
        lines.append(f"  透明 : {feats['transparent_ratio']:.0%}")
        if info.get("dhash"):
            lines.append(f"  感知哈希 : {info['dhash']}")
    if show_ascii and info.get("ascii"):
        lines.append("-- ASCII 预览（亮度映射） --")
        for row in info["ascii"]:
            lines.append("  " + row)
    lines.append("-- 语义提醒 --")
    lines.append("  本脚本只输出可从像素/字节算出的确定性事实；不含任何模型，")
    lines.append("  无法回答'这是什么场景/什么情绪'等语义问题。需要语义请另接识图模型。")
    return "\n".join(lines)


def main(argv):
    p = argparse.ArgumentParser(description="无模型图像感知（纯标准库）")
    p.add_argument("path", nargs="?", help="图片路径")
    p.add_argument("--json", action="store_true", help="JSON 输出")
    p.add_argument("--no-ascii", action="store_true", help="关闭 ASCII 预览")
    p.add_argument("--make-test-png", metavar="OUT", help="生成自测 PNG")
    args = p.parse_args(argv)

    if args.make_test_png:
        w, h = make_test_png(args.make_test_png)
        print(json.dumps({"made": args.make_test_png, "width": w, "height": h}))
        return 0
    if not args.path:
        p.error("需要一个图片路径（或 --make-test-png）")
        return 2

    try:
        with open(args.path, "rb") as f:
            data = f.read()
    except OSError as exc:
        print(json.dumps({"error": f"读取失败: {exc}"}))
        return 2

    info = detect(data)
    if info.get("format") == "UNKNOWN":
        print(render(info))
        return 3
    info["file_size"] = len(data)
    info["file_size_kb"] = round(len(data) / 1024, 1)
    feats = analyze_pixels(info.get("pixels"), info.get("width") or 0, info.get("height") or 0)
    if feats:
        info["features"] = feats
        info["dhash"] = dhash(info["pixels"], info["width"], info["height"])
        if not args.no_ascii:
            info["ascii"] = ascii_preview(info["pixels"], info["width"], info["height"])
    info.pop("pixels", None)  # 不把原始像素塞进输出

    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
    else:
        print(render(info))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
