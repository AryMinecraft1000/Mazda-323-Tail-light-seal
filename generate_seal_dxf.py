#!/usr/bin/env python3
"""
Parametric DXF & SVG Cutting Template Generator for 1993 Mazda 323 BG 3-Door Hatchback
Tail Light Seals (OEM Part Numbers B467-51-168 [LH] & B467-51-158 [RH]),
modeled to Mazda OEM catalog diagram 51-164 (B467-51-168) and physical seal geometry.

Generates:
  1. B467-51-168_LH_tail_light_seal.dxf
  2. B467-51-158_RH_tail_light_seal.dxf
  3. B467-51-168_158_pair_nested.dxf
  4. B467-51-168_158_perimeter_variant.dxf
  5. preview_blueprint.svg

Pure Python standard library implementation outputting AutoCAD R12 (AC1009) ASCII DXF.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

Point = Tuple[float, float]


def dist(a: Point, b: Point) -> float:
    """Euclidean distance between two 2D points."""
    return math.hypot(b[0] - a[0], b[1] - a[1])


def normalize(vx: float, vy: float) -> Point:
    """Return unit vector for (vx, vy)."""
    mag = math.hypot(vx, vy)
    if mag < 1e-12:
        return (0.0, 0.0)
    return (vx / mag, vy / mag)


def dot2(ax: float, ay: float, bx: float, by: float) -> float:
    """2D dot product."""
    return ax * bx + ay * by


def dedupe_ring(pts: Sequence[Point], eps: float = 1e-4) -> List[Point]:
    """Remove consecutive duplicates and wrap-around duplicate in a closed vertex loop."""
    cleaned: List[Point] = []
    for p in pts:
        if not cleaned or dist(cleaned[-1], p) > eps:
            cleaned.append((round(p[0], 4), round(p[1], 4)))
    while len(cleaned) > 1 and dist(cleaned[0], cleaned[-1]) <= eps:
        cleaned.pop()
    return cleaned


def build_filleted_polygon(
    poly_spec: Sequence[Dict],
    arc_steps: int = 14,
    edge_steps: int = 10,
) -> List[Point]:
    """
    Build a smooth closed polygon from corner specs [{"x": float, "y": float, "r": float}, ...]
    with exact circular tangent fillets at both convex and concave (reflex) corners.
    """
    n = len(poly_spec)
    corners: List[Point] = [(float(p["x"]), float(p["y"])) for p in poly_spec]
    radii: List[float] = [float(p.get("r", 0.0)) for p in poly_spec]

    trim_in: List[Point] = []
    trim_out: List[Point] = []
    arc_specs: List[Tuple[float, float, float, float, float] | None] = []

    for i in range(n):
        c_prev = corners[(i - 1) % n]
        c = corners[i]
        c_next = corners[(i + 1) % n]
        r = radii[i]

        ux, uy = c_prev[0] - c[0], c_prev[1] - c[1]
        vx, vy = c_next[0] - c[0], c_next[1] - c[1]
        len_u = math.hypot(ux, uy)
        len_v = math.hypot(vx, vy)
        ux, uy = normalize(ux, uy)
        vx, vy = normalize(vx, vy)

        cos_a = max(-0.999999, min(0.999999, dot2(ux, uy, vx, vy)))
        alpha = math.acos(cos_a)
        if r <= 1e-6 or abs(alpha - math.pi) < 1e-4 or alpha < 1e-4:
            trim_in.append(c)
            trim_out.append(c)
            arc_specs.append(None)
            continue

        tan_half = math.tan(alpha / 2.0)
        sin_half = math.sin(alpha / 2.0)
        t_len = min(r / tan_half, 0.42 * min(len_u, len_v))
        r_eff = t_len * tan_half

        t_in = (c[0] + t_len * ux, c[1] + t_len * uy)
        t_out = (c[0] + t_len * vx, c[1] + t_len * vy)
        bx, by = normalize(ux + vx, uy + vy)
        dist_center = r_eff / sin_half
        ox, oy = c[0] + dist_center * bx, c[1] + dist_center * by

        a0 = math.atan2(t_in[1] - oy, t_in[0] - ox)
        a1 = math.atan2(t_out[1] - oy, t_out[0] - ox)
        da = (a1 - a0 + math.pi) % (2.0 * math.pi) - math.pi

        trim_in.append(t_in)
        trim_out.append(t_out)
        arc_specs.append((ox, oy, r_eff, a0, da))

    pts: List[Point] = []
    for i in range(n):
        spec = arc_specs[i]
        if spec is None:
            pts.append(corners[i])
        else:
            ox, oy, r_eff, a0, da = spec
            for k in range(arc_steps):
                ang = a0 + da * (k / arc_steps)
                pts.append((ox + r_eff * math.cos(ang), oy + r_eff * math.sin(ang)))

        p_start = trim_out[i]
        p_end = trim_in[(i + 1) % n]
        if dist(p_start, p_end) > 1e-4:
            for k in range(edge_steps):
                t = k / edge_steps
                pts.append((p_start[0] + t * (p_end[0] - p_start[0]), p_start[1] + t * (p_end[1] - p_start[1])))

    return dedupe_ring(pts)


def mirror_points_x(pts: Sequence[Point], ref_width: float) -> List[Point]:
    """Mirror a polygon across X = ref_width / 2, reversing order to preserve CCW orientation."""
    mirrored = [(ref_width - x, y) for x, y in reversed(pts)]
    return dedupe_ring(mirrored)


def translate_points(pts: Sequence[Point], dx: float, dy: float) -> List[Point]:
    """Translate points by (dx, dy)."""
    return [(round(x + dx, 4), round(y + dy, 4)) for x, y in pts]


def build_seal_geometry(params: Dict, side: str, style: str = "two_chamber") -> Dict:
    """
    Build complete 2D geometry dictionary for 'LH' (B467-51-168) or 'RH' (B467-51-158).
    style: 'two_chamber' (OEM 2-aperture stepped-boss) or 'perimeter' (single continuous cutout).
    """
    ref_width = float(params["reference_width_mm"])
    outer_lh = build_filleted_polygon(params["outer_polygon"], arc_steps=14, edge_steps=12)

    if style == "two_chamber":
        inners_lh = [
            build_filleted_polygon(params["left_cutout_polygon"], arc_steps=12, edge_steps=8),
            build_filleted_polygon(params["right_cutout_polygon"], arc_steps=12, edge_steps=8),
        ]
    elif style == "perimeter":
        inners_lh = [
            build_filleted_polygon(params["perimeter_cutout_polygon"], arc_steps=10, edge_steps=6),
        ]
    else:
        raise ValueError(f"Unknown seal style: {style}")

    holes_lh = [
        {
            "name": name,
            "x": float(spec["x"]),
            "y": float(spec["y"]),
            "diameter": float(spec["diameter"]),
        }
        for name, spec in params["mounting_holes"].items()
    ]

    if side == "LH":
        return {
            "side": "LH",
            "part_number": params["metadata"]["part_numbers"]["LH"],
            "outer": outer_lh,
            "inners": inners_lh,
            "holes": holes_lh,
        }
    elif side == "RH":
        holes_rh = [
            {
                "name": h["name"],
                "x": round(ref_width - h["x"], 4),
                "y": h["y"],
                "diameter": h["diameter"],
            }
            for h in holes_lh
        ]
        return {
            "side": "RH",
            "part_number": params["metadata"]["part_numbers"]["RH"],
            "outer": mirror_points_x(outer_lh, ref_width),
            "inners": [mirror_points_x(inner, ref_width) for inner in inners_lh],
            "holes": holes_rh,
        }
    else:
        raise ValueError(f"Invalid side: {side}")


def translate_seal(geom: Dict, dx: float, dy: float) -> Dict:
    """Return a translated copy of a seal geometry dictionary."""
    return {
        "side": geom["side"],
        "part_number": geom["part_number"],
        "outer": translate_points(geom["outer"], dx, dy),
        "inners": [translate_points(inner, dx, dy) for inner in geom["inners"]],
        "holes": [
            {**h, "x": round(h["x"] + dx, 4), "y": round(h["y"] + dy, 4)}
            for h in geom["holes"]
        ],
    }


def compute_bounds(geoms: Sequence[Dict], extra_pts: Sequence[Point] = ()) -> Tuple[float, float, float, float]:
    """Compute (min_x, min_y, max_x, max_y) across all geometries and extra points."""
    xs: List[float] = [p[0] for p in extra_pts]
    ys: List[float] = [p[1] for p in extra_pts]
    for g in geoms:
        for x, y in g["outer"]:
            xs.append(x)
            ys.append(y)
        for inner in g["inners"]:
            for x, y in inner:
                xs.append(x)
                ys.append(y)
        for h in g["holes"]:
            r = h["diameter"] / 2.0
            xs.extend([h["x"] - r, h["x"] + r])
            ys.extend([h["y"] - r, h["y"] + r])
    return (min(xs), min(ys), max(xs), max(ys))


class DxfR12Writer:
    """Minimal, standards-compliant AutoCAD R12 (AC1009) ASCII DXF generator."""

    def __init__(self) -> None:
        self.entities: List[str] = []

    @staticmethod
    def _pair(code: int, value: object) -> str:
        return f"{code}\n{value}\n"

    def add_polyline(self, layer: str, points: Sequence[Point], closed: bool = True) -> None:
        lines = [
            self._pair(0, "POLYLINE"),
            self._pair(8, layer),
            self._pair(66, 1),
            self._pair(10, "0.0"),
            self._pair(20, "0.0"),
            self._pair(30, "0.0"),
            self._pair(70, 1 if closed else 0),
        ]
        for x, y in points:
            lines.extend([
                self._pair(0, "VERTEX"),
                self._pair(8, layer),
                self._pair(10, f"{x:.4f}"),
                self._pair(20, f"{y:.4f}"),
                self._pair(30, "0.0"),
            ])
        lines.extend([
            self._pair(0, "SEQEND"),
            self._pair(8, layer),
        ])
        self.entities.append("".join(lines))

    def add_circle(self, layer: str, cx: float, cy: float, radius: float) -> None:
        self.entities.append("".join([
            self._pair(0, "CIRCLE"),
            self._pair(8, layer),
            self._pair(10, f"{cx:.4f}"),
            self._pair(20, f"{cy:.4f}"),
            self._pair(30, "0.0"),
            self._pair(40, f"{radius:.4f}"),
        ]))

    def add_line(self, layer: str, x1: float, y1: float, x2: float, y2: float) -> None:
        self.entities.append("".join([
            self._pair(0, "LINE"),
            self._pair(8, layer),
            self._pair(10, f"{x1:.4f}"),
            self._pair(20, f"{y1:.4f}"),
            self._pair(30, "0.0"),
            self._pair(11, f"{x2:.4f}"),
            self._pair(21, f"{y2:.4f}"),
            self._pair(31, "0.0"),
        ]))

    def add_text(self, layer: str, x: float, y: float, height: float, text: str) -> None:
        self.entities.append("".join([
            self._pair(0, "TEXT"),
            self._pair(8, layer),
            self._pair(10, f"{x:.4f}"),
            self._pair(20, f"{y:.4f}"),
            self._pair(30, "0.0"),
            self._pair(40, f"{height:.4f}"),
            self._pair(1, text),
            self._pair(7, "STANDARD"),
        ]))

    def render(self, extmin: Point, extmax: Point) -> str:
        layers = [
            ("0", 7),
            ("CUT_OUTER", 7),
            ("CUT_INNER", 3),
            ("CUT_HOLES", 1),
            ("CALIBRATION", 5),
            ("ANNOTATIONS", 8),
        ]
        p = self._pair
        out: List[str] = []

        # HEADER
        out.extend([
            p(0, "SECTION"),
            p(2, "HEADER"),
            p(9, "$ACADVER"), p(1, "AC1009"),
            p(9, "$INSUNITS"), p(70, 4),       # 4 = Millimeters
            p(9, "$MEASUREMENT"), p(70, 1),    # 1 = Metric
            p(9, "$EXTMIN"), p(10, f"{extmin[0]:.4f}"), p(20, f"{extmin[1]:.4f}"), p(30, "0.0"),
            p(9, "$EXTMAX"), p(10, f"{extmax[0]:.4f}"), p(20, f"{extmax[1]:.4f}"), p(30, "0.0"),
            p(0, "ENDSEC"),
        ])

        # TABLES
        out.extend([
            p(0, "SECTION"),
            p(2, "TABLES"),
            p(0, "TABLE"), p(2, "LTYPE"), p(70, 1),
            p(0, "LTYPE"), p(2, "CONTINUOUS"), p(70, 0), p(3, "Solid line"), p(72, 65), p(73, 0), p(40, "0.0"),
            p(0, "ENDTAB"),
            p(0, "TABLE"), p(2, "LAYER"), p(70, len(layers)),
        ])
        for name, color in layers:
            out.extend([
                p(0, "LAYER"),
                p(2, name),
                p(70, 0),
                p(62, color),
                p(6, "CONTINUOUS"),
            ])
        out.extend([
            p(0, "ENDTAB"),
            p(0, "TABLE"), p(2, "STYLE"), p(70, 1),
            p(0, "STYLE"), p(2, "STANDARD"), p(70, 0), p(40, "0.0"), p(41, "1.0"),
            p(50, "0.0"), p(71, 0), p(42, "2.5"), p(3, "txt"), p(4, ""),
            p(0, "ENDTAB"),
            p(0, "ENDSEC"),
        ])

        # BLOCKS
        out.extend([
            p(0, "SECTION"),
            p(2, "BLOCKS"),
            p(0, "ENDSEC"),
        ])

        # ENTITIES
        out.extend([p(0, "SECTION"), p(2, "ENTITIES")])
        out.extend(self.entities)
        out.extend([p(0, "ENDSEC"), p(0, "EOF")])
        return "".join(out)


def add_seal_to_dxf(dxf: DxfR12Writer, geom: Dict, label_prefix: str = "") -> None:
    """Write one seal (outer, inners, holes, and annotations) into DxfR12Writer."""
    dxf.add_polyline("CUT_OUTER", geom["outer"], closed=True)
    for inner in geom["inners"]:
        dxf.add_polyline("CUT_INNER", inner, closed=True)
    for hole in geom["holes"]:
        r = hole["diameter"] / 2.0
        dxf.add_circle("CUT_HOLES", hole["x"], hole["y"], r)
        tick = r + 2.0
        dxf.add_line("ANNOTATIONS", hole["x"] - tick, hole["y"], hole["x"] + tick, hole["y"])
        dxf.add_line("ANNOTATIONS", hole["x"], hole["y"] - tick, hole["x"], hole["y"] + tick)

    xs = [x for x, _ in geom["outer"]]
    ys = [y for _, y in geom["outer"]]
    cx = 0.5 * (min(xs) + max(xs))
    cy = 0.5 * (min(ys) + max(ys))
    label = f"{label_prefix}{geom['part_number']} ({geom['side']}) - 1993 MAZDA 323 BG 3D"
    dxf.add_text("ANNOTATIONS", cx - 105.0, cy - 3.0, 5.0, label)
    dxf.add_text("ANNOTATIONS", min(xs) + 12.0, min(ys) - 8.0, 4.0, "MAT: 3-5mm CLOSED-CELL EPDM FOAM | UNITS: MM (1:1)")


def add_calibration_bar(dxf: DxfR12Writer, x0: float, y0: float, width: float = 100.0, height: float = 20.0) -> None:
    """Add a 100.0 mm x 20.0 mm scale verification rectangle on CALIBRATION layer."""
    rect = [
        (x0, y0),
        (x0 + width, y0),
        (x0 + width, y0 + height),
        (x0, y0 + height),
    ]
    dxf.add_polyline("CALIBRATION", rect, closed=True)
    dxf.add_text("CALIBRATION", x0 + 6.0, y0 + 7.5, 4.5, f"SCALE CHECK: {width:.0f}mm x {height:.0f}mm")


def write_single_seal_dxf(path: Path, geom: Dict) -> None:
    """Write a standalone LH or RH DXF file."""
    dxf = DxfR12Writer()
    add_seal_to_dxf(dxf, geom)
    min_x, min_y, max_x, max_y = compute_bounds([geom])
    path.write_text(dxf.render((min_x - 10.0, min_y - 15.0), (max_x + 10.0, max_y + 10.0)), encoding="utf-8")


def write_nested_pair_dxf(path: Path, params: Dict, style: str, title_prefix: str = "") -> Tuple[Dict, Dict]:
    """Write a nested LH + RH DXF sheet on a 380 mm x 400 mm layout with 100 mm calibration bar."""
    nest = params["nesting"]
    sheet_w = float(nest["sheet_width_mm"])
    sheet_h = float(nest["sheet_height_mm"])
    cal_w = float(nest["calibration_bar_mm"]["width"])
    cal_h = float(nest["calibration_bar_mm"]["height"])

    lh_raw = build_seal_geometry(params, "LH", style=style)
    rh_raw = build_seal_geometry(params, "RH", style=style)

    lh_min_x, lh_min_y, lh_max_x, lh_max_y = compute_bounds([lh_raw])
    rh_min_x, rh_min_y, rh_max_x, rh_max_y = compute_bounds([rh_raw])

    lh_w = lh_max_x - lh_min_x
    lh_h = lh_max_y - lh_min_y
    rh_w = rh_max_x - rh_min_x
    rh_h = rh_max_y - rh_min_y

    margin_y = 6.0
    lh_dx = 0.5 * (sheet_w - lh_w) - lh_min_x
    lh_dy = margin_y - lh_min_y
    rh_dx = 0.5 * (sheet_w - rh_w) - rh_min_x
    rh_dy = (sheet_h - margin_y - rh_h) - rh_min_y

    lh = translate_seal(lh_raw, lh_dx, lh_dy)
    rh = translate_seal(rh_raw, rh_dx, rh_dy)

    cal_x = 0.5 * (sheet_w - cal_w)
    cal_y = 0.5 * ((margin_y + lh_h) + (sheet_h - margin_y - rh_h) - cal_h)

    dxf = DxfR12Writer()
    add_seal_to_dxf(dxf, lh, label_prefix=title_prefix)
    add_seal_to_dxf(dxf, rh, label_prefix=title_prefix)
    add_calibration_bar(dxf, cal_x, cal_y, cal_w, cal_h)

    dxf.add_polyline("ANNOTATIONS", [(0.0, 0.0), (sheet_w, 0.0), (sheet_w, sheet_h), (0.0, sheet_h)], closed=True)
    dxf.add_text("ANNOTATIONS", 10.0, sheet_h + 4.0, 5.0, f"SHEET LAYOUT: {sheet_w:.0f}mm x {sheet_h:.0f}mm")

    path.write_text(dxf.render((0.0, -12.0), (sheet_w, sheet_h + 12.0)), encoding="utf-8")
    return lh, rh


def svg_path_from_ring(pts: Sequence[Point]) -> str:
    """Convert a closed 2D ring into an SVG path string (flipping Y inside transform)."""
    if not pts:
        return ""
    parts = [f"M {pts[0][0]:.2f} {-pts[0][1]:.2f}"]
    for x, y in pts[1:]:
        parts.append(f"L {x:.2f} {-y:.2f}")
    parts.append("Z")
    return " ".join(parts)


def generate_svg_blueprint(path: Path, params: Dict, lh: Dict, rh: Dict) -> None:
    """Generate a dimensioned 1:1 millimeter SVG technical blueprint for both LH and RH seals."""
    w_mm = 420.0
    h_mm = 540.0

    lh_xs = [x for x, _ in lh["outer"]]
    lh_ys = [y for _, y in lh["outer"]]
    span_w = max(lh_xs) - min(lh_xs)
    span_h = max(lh_ys) - min(lh_ys)

    lh_tx, lh_ty = 32.0, 216.0
    rh_tx, rh_ty = 32.0, 422.0

    def render_seal_group(g: Dict, tx: float, ty: float, title: str) -> str:
        inner_paths = " ".join(svg_path_from_ring(inn) for inn in g["inners"])
        compound_d = f"{svg_path_from_ring(g['outer'])} {inner_paths}"
        holes_svg = []
        for h in g["holes"]:
            cx, cy, r = h["x"], -h["y"], h["diameter"] / 2.0
            if cx > 260.0:
                tx_pos, anchor = cx - r - 2.0, "end"
            else:
                tx_pos, anchor = cx + r + 2.0, "start"
            holes_svg.append(
                f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r:.2f}" fill="#ffffff" stroke="#d32f2f" stroke-width="0.45"/>'
                f'<line x1="{cx-r-1.5:.2f}" y1="{cy:.2f}" x2="{cx+r+1.5:.2f}" y2="{cy:.2f}" stroke="#d32f2f" stroke-width="0.25"/>'
                f'<line x1="{cx:.2f}" y1="{cy-r-1.5:.2f}" x2="{cx:.2f}" y2="{cy+r+1.5:.2f}" stroke="#d32f2f" stroke-width="0.25"/>'
                f'<text x="{tx_pos:.2f}" y="{cy+1.1:.2f}" text-anchor="{anchor}" font-size="3.2" fill="#b71c1c" font-family="monospace">{h["name"].split("_")[0]} Ø{h["diameter"]:.1f}</text>'
            )

        return f"""
  <g transform="translate({tx:.1f}, {ty:.1f})">
    <text x="175" y="-172" text-anchor="middle" font-size="5.2" font-weight="bold" fill="#111111" font-family="sans-serif">{title}</text>
    <path d="{compound_d}" fill="#2e7d32" fill-opacity="0.14" fill-rule="evenodd" stroke="#111111" stroke-width="0.55"/>
    {"".join(holes_svg)}
  </g>"""

    rows_svg = []
    for idx, (name, spec) in enumerate(params["mounting_holes"].items()):
        ry = 482.0 + idx * 6.5
        rows_svg.append(
            f'<text x="22" y="{ry:.1f}" font-size="3.9" font-family="monospace" fill="#222">{name:<22} X={spec["x"]:6.1f} mm   Y={spec["y"]:6.1f} mm   Ø{spec["diameter"]:.1f} mm</text>'
        )

    x_left_dim = lh_tx + min(lh_xs)
    x_right_dim = lh_tx + max(lh_xs)
    y_top_dim = lh_ty - max(lh_ys)
    y_bot_dim = lh_ty - min(lh_ys)

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w_mm:.0f}mm" height="{h_mm:.0f}mm" viewBox="0 0 {w_mm:.0f} {h_mm:.0f}">
  <rect x="0" y="0" width="{w_mm:.0f}" height="{h_mm:.0f}" fill="#fafafa"/>
  <rect x="8" y="8" width="{w_mm-16:.0f}" height="{h_mm-16:.0f}" fill="none" stroke="#333333" stroke-width="0.6"/>

  <!-- Header Block -->
  <text x="18" y="21" font-size="7.2" font-weight="bold" font-family="sans-serif" fill="#111">1993 MAZDA 323 BG 3-DOOR HATCHBACK — TAIL LIGHT SEAL CUTTING BLUEPRINT (1:1)</text>
  <text x="18" y="28" font-size="4.4" font-family="sans-serif" fill="#444">Part Numbers: B467-51-168 (LH / 51-164) &amp; B467-51-158 (RH)  |  Material: 3–5 mm Closed-Cell EPDM Foam  |  Units: mm</text>
  <line x1="18" y1="32" x2="402" y2="32" stroke="#888" stroke-width="0.4"/>

  <!-- Overall Dimensions Callout for LH -->
  <line x1="{x_left_dim:.2f}" y1="232" x2="{x_right_dim:.2f}" y2="232" stroke="#1565c0" stroke-width="0.4" stroke-dasharray="2,1"/>
  <text x="{0.5*(x_left_dim+x_right_dim):.2f}" y="238" text-anchor="middle" font-size="4.2" font-family="monospace" fill="#1565c0">Overall Width = {span_w:.1f} mm</text>

  <line x1="398" y1="{y_top_dim:.2f}" x2="398" y2="{y_bot_dim:.2f}" stroke="#1565c0" stroke-width="0.4" stroke-dasharray="2,1"/>
  <text x="403" y="{0.5*(y_top_dim+y_bot_dim):.2f}" font-size="4.2" font-family="monospace" fill="#1565c0" transform="rotate(-90 403 {0.5*(y_top_dim+y_bot_dim):.2f})" text-anchor="middle">Overall Height = {span_h:.1f} mm (incl. 9 mm bottom tab)</text>

  {render_seal_group(lh, lh_tx, lh_ty, "B467-51-168 (LH — Left / Driver Side, per Mazda Diagram 51-164)")}
  {render_seal_group(rh, rh_tx, rh_ty, "B467-51-158 (RH — Right / Passenger Side, Mirrored)")}

  <!-- 100 mm Scale Calibration Bar -->
  <g transform="translate(22, 442)">
    <rect x="0" y="0" width="100" height="20" fill="none" stroke="#1565c0" stroke-width="0.6"/>
    <line x1="50" y1="0" x2="50" y2="20" stroke="#1565c0" stroke-width="0.3" stroke-dasharray="1.5,1"/>
    <text x="50" y="11.5" text-anchor="middle" font-size="4.5" font-weight="bold" font-family="monospace" fill="#1565c0">100.0 mm x 20.0 mm CALIBRATION COUPON</text>
  </g>

  <text x="135" y="450" font-size="4.3" font-family="sans-serif" fill="#333">1. Print at 100% scale (no fit-to-page) and verify the blue rectangle measures exactly 100.0 mm.</text>
  <text x="135" y="457" font-size="4.3" font-family="sans-serif" fill="#333">2. Test-fit paper template on physical B467-51-161 / -151 tail lamp housing before cutting foam.</text>

  <!-- Coordinate Table -->
  <text x="22" y="474" font-size="4.8" font-weight="bold" font-family="sans-serif" fill="#111">LH (B467-51-168) HOLE COORDINATES (relative to bottom-outer body corner X=0, Y=0):</text>
  {"".join(rows_svg)}

  <text x="22" y="524" font-size="4.0" font-family="sans-serif" fill="#555">DXF Layers: CUT_OUTER (White/7) | CUT_INNER (Green/3) | CUT_HOLES (Red/1) | CALIBRATION (Blue/5) | ANNOTATIONS (Gray/8)</text>
  <text x="22" y="530" font-size="4.0" font-family="sans-serif" fill="#555">Adjust any parameter in params.json and run: python3 generate_seal_dxf.py</text>
</svg>
"""
    path.write_text(svg, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate DXF & SVG cutting models for 1993 Mazda 323 BG tail light seals.")
    parser.add_argument("--params", type=Path, default=Path(__file__).parent / "params.json", help="Path to params.json")
    parser.add_argument("--outdir", type=Path, default=Path(__file__).parent, help="Output directory")
    args = parser.parse_args()

    params = json.loads(args.params.read_text(encoding="utf-8"))
    outdir: Path = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    lh_2ch = build_seal_geometry(params, "LH", style="two_chamber")
    rh_2ch = build_seal_geometry(params, "RH", style="two_chamber")

    write_single_seal_dxf(outdir / "B467-51-168_LH_tail_light_seal.dxf", lh_2ch)
    write_single_seal_dxf(outdir / "B467-51-158_RH_tail_light_seal.dxf", rh_2ch)
    write_nested_pair_dxf(outdir / "B467-51-168_158_pair_nested.dxf", params, style="two_chamber")
    write_nested_pair_dxf(
        outdir / "B467-51-168_158_perimeter_variant.dxf",
        params,
        style="perimeter",
        title_prefix="PERIMETER RING: ",
    )
    generate_svg_blueprint(outdir / "preview_blueprint.svg", params, lh_2ch, rh_2ch)

    print(f"Generated 4 DXF files and preview_blueprint.svg in {outdir}")


if __name__ == "__main__":
    main()
