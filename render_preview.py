#!/usr/bin/env python3
"""Pure-Python PNG preview renderer for the Mazda 323 BG tail light seal geometry."""

from __future__ import annotations

import json
import math
import struct
import zlib
from pathlib import Path
from typing import List, Sequence, Tuple

from generate_seal_dxf import build_seal_geometry

Point = Tuple[float, float]
Color = Tuple[int, int, int]


def write_png(path: Path, width: int, height: int, rgb_buf: bytearray) -> None:
    """Write an RGB888 bytearray to a PNG file."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    raw_rows = bytearray()
    stride = width * 3
    for y in range(height):
        raw_rows.append(0)
        raw_rows.extend(rgb_buf[y * stride : (y + 1) * stride])

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw_rows), 6)) + chunk(b"IEND", b"")
    path.write_bytes(png)


def scanline_fill_mask(w: int, h: int, polys_and_sign: Sequence[Tuple[Sequence[Point], bool]]) -> bytearray:
    """Fast scanline rasterizer returning a 1-byte mask (1 = inside, 0 = outside)."""
    mask = bytearray(w * h)
    for poly, fill_val in polys_and_sign:
        ys = [p[1] for p in poly]
        y_start = max(0, int(math.floor(min(ys))))
        y_end = min(h - 1, int(math.ceil(max(ys))))
        n = len(poly)
        val = 1 if fill_val else 0
        for py in range(y_start, y_end + 1):
            y = py + 0.5
            xs: List[float] = []
            for i in range(n):
                x1, y1 = poly[i]
                x2, y2 = poly[(i + 1) % n]
                if (y1 <= y < y2) or (y2 <= y < y1):
                    xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            row_off = py * w
            for k in range(0, len(xs) - 1, 2):
                x_a = max(0, int(math.ceil(xs[k])))
                x_b = min(w - 1, int(math.floor(xs[k + 1])))
                for px in range(x_a, x_b + 1):
                    mask[row_off + px] = val
    return mask


def draw_thick_segment(
    buf: bytearray, w: int, h: int, p0: Point, p1: Point, radius: float, color: Color
) -> None:
    x0, y0 = p0
    x1, y1 = p1
    min_x = max(0, int(math.floor(min(x0, x1) - radius - 1)))
    max_x = min(w - 1, int(math.ceil(max(x0, x1) + radius + 1)))
    min_y = max(0, int(math.floor(min(y0, y1) - radius - 1)))
    max_y = min(h - 1, int(math.ceil(max(y0, y1) + radius + 1)))
    dx, dy = x1 - x0, y1 - y0
    len_sq = dx * dx + dy * dy
    r2 = radius * radius
    r, g, b = color
    for py in range(min_y, max_y + 1):
        for px in range(min_x, max_x + 1):
            t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / len_sq)) if len_sq > 1e-9 else 0.0
            dist2 = (px - (x0 + t * dx)) ** 2 + (py - (y0 + t * dy)) ** 2
            if dist2 <= r2:
                idx = (py * w + px) * 3
                buf[idx], buf[idx + 1], buf[idx + 2] = r, g, b


def draw_seal(
    buf: bytearray,
    w: int,
    h: int,
    geom: dict,
    scale: float,
    ox: float,
    oy_bottom: float,
) -> None:
    def to_px(pt: Point) -> Point:
        return (ox + pt[0] * scale, oy_bottom - pt[1] * scale)

    outer_px = [to_px(p) for p in geom["outer"]]
    inners_px = [[to_px(p) for p in inn] for inn in geom["inners"]]
    holes_px = [(ox + hole["x"] * scale, oy_bottom - hole["y"] * scale, (hole["diameter"] / 2.0) * scale) for hole in geom["holes"]]

    ops: List[Tuple[Sequence[Point], bool]] = [(outer_px, True)] + [(inn, False) for inn in inners_px]
    mask = scanline_fill_mask(w, h, ops)
    for hx, hy, hr in holes_px:
        hr2 = hr * hr
        for py in range(max(0, int(hy - hr - 1)), min(h, int(hy + hr + 2))):
            row_off = py * w
            for px in range(max(0, int(hx - hr - 1)), min(w, int(hx + hr + 2))):
                if (px - hx) ** 2 + (py - hy) ** 2 <= hr2:
                    mask[row_off + px] = 0

    for idx_px, m in enumerate(mask):
        if m:
            idx = idx_px * 3
            buf[idx], buf[idx + 1], buf[idx + 2] = 43, 48, 54

    # Crisp cut outlines: outer = black, inner = emerald green, holes = crimson red
    for i in range(len(outer_px)):
        draw_thick_segment(buf, w, h, outer_px[i], outer_px[(i + 1) % len(outer_px)], 1.3, (15, 15, 18))
    for inn in inners_px:
        for i in range(len(inn)):
            draw_thick_segment(buf, w, h, inn[i], inn[(i + 1) % len(inn)], 1.2, (46, 160, 67))
    for hx, hy, hr in holes_px:
        steps = 48
        pts = [(hx + hr * math.cos(2 * math.pi * k / steps), hy + hr * math.sin(2 * math.pi * k / steps)) for k in range(steps)]
        for i in range(steps):
            draw_thick_segment(buf, w, h, pts[i], pts[(i + 1) % steps], 1.2, (211, 47, 47))


def main() -> None:
    base = Path(__file__).parent
    params = json.loads((base / "params.json").read_text(encoding="utf-8"))
    lh = build_seal_geometry(params, "LH", style="two_chamber")
    rh = build_seal_geometry(params, "RH", style="two_chamber")

    w, h = 1100, 1080
    # Light blueprint grid background (#f7f9fc)
    buf = bytearray([247, 249, 252] * (w * h))

    # Draw subtle 25 mm grid (scale = 2.6 px/mm -> 65 px per 25 mm)
    scale = 2.6
    step = int(round(25.0 * scale))
    for gx in range(0, w, step):
        for py in range(h):
            idx = (py * w + gx) * 3
            buf[idx], buf[idx + 1], buf[idx + 2] = 228, 234, 242
    for gy in range(0, h, step):
        for px in range(w):
            idx = (gy * w + px) * 3
            buf[idx], buf[idx + 1], buf[idx + 2] = 228, 234, 242

    ref_w = float(params["reference_width_mm"])
    ox = (w - ref_w * scale) / 2.0
    draw_seal(buf, w, h, lh, scale, ox, 470.0)
    draw_seal(buf, w, h, rh, scale, ox, 980.0)

    out_path = base / "render_preview.png"
    write_png(out_path, w, h, buf)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
