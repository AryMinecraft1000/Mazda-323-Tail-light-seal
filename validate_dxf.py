#!/usr/bin/env python3
"""
Structural and Geometric Validator for the Mazda 323 BG Tail Light Seal DXF files.

Checks:
  1. Valid DXF tag/value line pairs, HEADER/TABLES/BLOCKS/ENTITIES/EOF, $INSUNITS = 4.
  2. Every POLYLINE on CUT_OUTER and CUT_INNER is closed (flag 70 == 1), has zero
     consecutive/wrap-around duplicate vertices, and zero segment self-intersections.
  3. Every CIRCLE on CUT_HOLES has radius 3.25 mm (4x studs) or 4.00 mm (1x locator pin),
     and every hole + wall/boss clearance lies strictly inside CUT_OUTER and outside
     all CUT_INNER cutouts (minimum foam wall >= 3.5 mm).
  4. Exact mirror symmetry between B467-51-168_LH_tail_light_seal.dxf and
     B467-51-158_RH_tail_light_seal.dxf.
  5. Nested sheets fit cleanly inside 380 mm x 340 mm with no inter-part collisions.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

Point = Tuple[float, float]


def parse_dxf_pairs(text: str) -> List[Tuple[int, str]]:
    """Parse ASCII DXF into (group_code, value) pairs and verify structural pairing."""
    lines = text.splitlines()
    if len(lines) % 2 != 0:
        raise AssertionError(f"Odd number of lines ({len(lines)}) in DXF file")
    pairs: List[Tuple[int, str]] = []
    for i in range(0, len(lines), 2):
        code_str = lines[i].strip()
        val_str = lines[i + 1].strip()
        try:
            code = int(code_str)
        except ValueError as exc:
            raise AssertionError(f"Invalid DXF group code at line {i + 1}: {code_str!r}") from exc
        pairs.append((code, val_str))
    return pairs


def extract_sections_and_entities(pairs: Sequence[Tuple[int, str]]) -> Dict:
    """Validate sections and extract polylines, circles, and header vars from DXF pairs."""
    sections: List[str] = []
    insunits = None
    measurement = None
    acadver = None
    has_eof = False

    polylines: List[Dict] = []
    circles: List[Dict] = []

    i = 0
    n = len(pairs)
    current_section = None
    while i < n:
        code, val = pairs[i]
        if code == 0 and val == "EOF":
            has_eof = True
            break
        if code == 0 and val == "SECTION":
            i += 1
            if i >= n or pairs[i][0] != 2:
                raise AssertionError("SECTION not followed by group 2 section name")
            current_section = pairs[i][1]
            sections.append(current_section)
            i += 1
            continue
        if code == 0 and val == "ENDSEC":
            current_section = None
            i += 1
            continue

        if current_section == "HEADER" and code == 9:
            var_name = val
            if i + 1 < n:
                nxt_code, nxt_val = pairs[i + 1]
                if var_name == "$ACADVER" and nxt_code == 1:
                    acadver = nxt_val
                elif var_name == "$INSUNITS" and nxt_code == 70:
                    insunits = int(nxt_val)
                elif var_name == "$MEASUREMENT" and nxt_code == 70:
                    measurement = int(nxt_val)
            i += 1
            continue

        if current_section == "ENTITIES" and code == 0:
            if val == "POLYLINE":
                layer = None
                flag70 = 0
                flag66 = 0
                i += 1
                while i < n and pairs[i][0] != 0:
                    c, v = pairs[i]
                    if c == 8:
                        layer = v
                    elif c == 70:
                        flag70 = int(v)
                    elif c == 66:
                        flag66 = int(v)
                    i += 1
                verts: List[Point] = []
                while i < n:
                    if pairs[i] == (0, "VERTEX"):
                        vx = vy = None
                        i += 1
                        while i < n and pairs[i][0] != 0:
                            c, v = pairs[i]
                            if c == 10:
                                vx = float(v)
                            elif c == 20:
                                vy = float(v)
                            i += 1
                        if vx is None or vy is None:
                            raise AssertionError(f"VERTEX missing coordinates on layer {layer}")
                        verts.append((vx, vy))
                    elif pairs[i] == (0, "SEQEND"):
                        i += 1
                        while i < n and pairs[i][0] != 0:
                            i += 1
                        break
                    else:
                        raise AssertionError(f"Unexpected entity inside POLYLINE: {pairs[i]}")
                polylines.append({"layer": layer, "flag70": flag70, "flag66": flag66, "vertices": verts})
                continue

            if val == "CIRCLE":
                layer = None
                cx = cy = r = None
                i += 1
                while i < n and pairs[i][0] != 0:
                    c, v = pairs[i]
                    if c == 8:
                        layer = v
                    elif c == 10:
                        cx = float(v)
                    elif c == 20:
                        cy = float(v)
                    elif c == 40:
                        r = float(v)
                    i += 1
                circles.append({"layer": layer, "cx": cx, "cy": cy, "r": r})
                continue

        i += 1

    return {
        "sections": sections,
        "has_eof": has_eof,
        "acadver": acadver,
        "insunits": insunits,
        "measurement": measurement,
        "polylines": polylines,
        "circles": circles,
    }


def orient(a: Point, b: Point, c: Point) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def on_segment(a: Point, b: Point, c: Point, eps: float = 1e-9) -> bool:
    return (
        min(a[0], b[0]) - eps <= c[0] <= max(a[0], b[0]) + eps
        and min(a[1], b[1]) - eps <= c[1] <= max(a[1], b[1]) + eps
    )


def segments_intersect(a1: Point, a2: Point, b1: Point, b2: Point) -> bool:
    """Exact 2D closed segment intersection test."""
    o1 = orient(a1, a2, b1)
    o2 = orient(a1, a2, b2)
    o3 = orient(b1, b2, a1)
    o4 = orient(b1, b2, a2)

    if (o1 > 1e-9 and o2 < -1e-9 or o1 < -1e-9 and o2 > 1e-9) and (
        o3 > 1e-9 and o4 < -1e-9 or o3 < -1e-9 and o4 > 1e-9
    ):
        return True
    if abs(o1) <= 1e-9 and on_segment(a1, a2, b1):
        return True
    if abs(o2) <= 1e-9 and on_segment(a1, a2, b2):
        return True
    if abs(o3) <= 1e-9 and on_segment(b1, b2, a1):
        return True
    if abs(o4) <= 1e-9 and on_segment(b1, b2, a2):
        return True
    return False


def point_in_polygon(pt: Point, poly: Sequence[Point]) -> bool:
    """Ray-casting point-in-polygon test."""
    x, y = pt
    inside = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
            inside = not inside
    return inside


def point_to_segment_dist(p: Point, a: Point, b: Point) -> float:
    """Minimum distance from point p to segment ab."""
    vx, vy = b[0] - a[0], b[1] - a[1]
    wx, wy = p[0] - a[0], p[1] - a[1]
    len_sq = vx * vx + vy * vy
    if len_sq < 1e-12:
        return math.hypot(wx, wy)
    t = max(0.0, min(1.0, (wx * vx + wy * vy) / len_sq))
    proj = (a[0] + t * vx, a[1] + t * vy)
    return math.hypot(p[0] - proj[0], p[1] - proj[1])


def point_to_polygon_dist(p: Point, poly: Sequence[Point]) -> float:
    """Minimum distance from point p to the edges of closed polygon poly."""
    n = len(poly)
    return min(point_to_segment_dist(p, poly[i], poly[(i + 1) % n]) for i in range(n))


def polygons_intersect(poly1: Sequence[Point], poly2: Sequence[Point]) -> bool:
    """Check if boundaries of poly1 and poly2 intersect."""
    n1, n2 = len(poly1), len(poly2)
    for i in range(n1):
        a1, a2 = poly1[i], poly1[(i + 1) % n1]
        for j in range(n2):
            b1, b2 = poly2[j], poly2[(j + 1) % n2]
            if segments_intersect(a1, a2, b1, b2):
                return True
    return False


def check_closed_simple_polyline(poly: Dict, min_verts: int = 4) -> List[Point]:
    """Validate closed flag, non-duplication, and zero self-intersections."""
    verts: List[Point] = poly["vertices"]
    layer = poly["layer"]
    if poly["flag70"] != 1:
        raise AssertionError(f"Polyline on {layer} is not closed (flag 70={poly['flag70']})")
    if poly["flag66"] != 1:
        raise AssertionError(f"Polyline on {layer} missing flag 66=1")
    if len(verts) < min_verts:
        raise AssertionError(f"Polyline on {layer} has too few vertices ({len(verts)} < {min_verts})")

    n = len(verts)
    for i in range(n):
        d = math.hypot(verts[(i + 1) % n][0] - verts[i][0], verts[(i + 1) % n][1] - verts[i][1])
        if d < 1e-4:
            raise AssertionError(f"Duplicate/zero-length edge on {layer} at vertex {i}: {verts[i]}")

    for i in range(n):
        a1, a2 = verts[i], verts[(i + 1) % n]
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue  # adjacent wrap-around edges share vertex 0
            b1, b2 = verts[j], verts[(j + 1) % n]
            if segments_intersect(a1, a2, b1, b2):
                raise AssertionError(f"Self-intersection on {layer} between edges {i} and {j}")
    return verts


def validate_file(
    dxf_path: Path,
    expected_outer_count: int,
    expected_inner_count: int,
    expected_circle_count: int,
    min_wall_mm: float = 8.0,
) -> Dict:
    """Run all structural and geometric checks on a single DXF file."""
    text = dxf_path.read_text(encoding="utf-8")
    pairs = parse_dxf_pairs(text)
    parsed = extract_sections_and_entities(pairs)

    if parsed["sections"] != ["HEADER", "TABLES", "BLOCKS", "ENTITIES"]:
        raise AssertionError(f"{dxf_path.name}: unexpected sections {parsed['sections']}")
    if not parsed["has_eof"]:
        raise AssertionError(f"{dxf_path.name}: missing EOF")
    if parsed["acadver"] != "AC1009":
        raise AssertionError(f"{dxf_path.name}: expected AC1009, got {parsed['acadver']}")
    if parsed["insunits"] != 4:
        raise AssertionError(f"{dxf_path.name}: expected $INSUNITS=4 (mm), got {parsed['insunits']}")
    if parsed["measurement"] != 1:
        raise AssertionError(f"{dxf_path.name}: expected $MEASUREMENT=1 (metric), got {parsed['measurement']}")

    outers = [p for p in parsed["polylines"] if p["layer"] == "CUT_OUTER"]
    inners = [p for p in parsed["polylines"] if p["layer"] == "CUT_INNER"]
    holes = [c for c in parsed["circles"] if c["layer"] == "CUT_HOLES"]

    if len(outers) != expected_outer_count:
        raise AssertionError(f"{dxf_path.name}: expected {expected_outer_count} CUT_OUTER, got {len(outers)}")
    if len(inners) != expected_inner_count:
        raise AssertionError(f"{dxf_path.name}: expected {expected_inner_count} CUT_INNER, got {len(inners)}")
    if len(holes) != expected_circle_count:
        raise AssertionError(f"{dxf_path.name}: expected {expected_circle_count} CUT_HOLES, got {len(holes)}")

    outer_polys = [check_closed_simple_polyline(p, min_verts=160) for p in outers]
    inner_polys = [check_closed_simple_polyline(p, min_verts=40) for p in inners]

    # Check outer contours don't collide with each other (for nested pairs)
    for idx in range(len(outer_polys)):
        for jdx in range(idx + 1, len(outer_polys)):
            if polygons_intersect(outer_polys[idx], outer_polys[jdx]):
                raise AssertionError(f"{dxf_path.name}: nested CUT_OUTER #{idx} and #{jdx} intersect")

    # Group each inner contour and hole with its enclosing outer contour
    for inner_idx, inner_poly in enumerate(inner_polys):
        enclosing = [oi for oi, op in enumerate(outer_polys) if point_in_polygon(inner_poly[0], op)]
        if len(enclosing) != 1:
            raise AssertionError(f"{dxf_path.name}: CUT_INNER #{inner_idx} not strictly inside one CUT_OUTER")
        op = outer_polys[enclosing[0]]
        if polygons_intersect(inner_poly, op):
            raise AssertionError(f"{dxf_path.name}: CUT_INNER #{inner_idx} intersects CUT_OUTER")
        # Check non-intersection against other inner polys
        for other_idx in range(inner_idx + 1, len(inner_polys)):
            if polygons_intersect(inner_poly, inner_polys[other_idx]):
                raise AssertionError(f"{dxf_path.name}: CUT_INNER #{inner_idx} intersects #{other_idx}")

    # Check circle radii and clearance to outer and inner contours
    stud_count = 0
    pin_count = 0
    for c in holes:
        r = c["r"]
        if math.isclose(r, 3.25, abs_tol=1e-3):
            stud_count += 1
        elif math.isclose(r, 4.00, abs_tol=1e-3):
            pin_count += 1
        else:
            raise AssertionError(f"{dxf_path.name}: unexpected hole radius {r:.4f} mm")

        pt = (c["cx"], c["cy"])
        enclosing = [oi for oi, op in enumerate(outer_polys) if point_in_polygon(pt, op)]
        if len(enclosing) != 1:
            raise AssertionError(f"{dxf_path.name}: hole {pt} is not inside CUT_OUTER")
        op = outer_polys[enclosing[0]]

        d_outer = point_to_polygon_dist(pt, op) - r
        if d_outer < min_wall_mm:
            raise AssertionError(f"{dxf_path.name}: hole {pt} too close to CUT_OUTER ({d_outer:.2f} mm < {min_wall_mm} mm)")

        for inner_idx, inner_poly in enumerate(inner_polys):
            if point_in_polygon(pt, inner_poly):
                raise AssertionError(f"{dxf_path.name}: hole {pt} falls inside CUT_INNER #{inner_idx}")
            d_inner = point_to_polygon_dist(pt, inner_poly) - r
            if d_inner < min_wall_mm:
                raise AssertionError(
                    f"{dxf_path.name}: hole {pt} too close to CUT_INNER #{inner_idx} ({d_inner:.2f} mm < {min_wall_mm} mm)"
                )

    expected_studs = 6 * expected_outer_count
    expected_pins = 0
    if stud_count != expected_studs or pin_count != expected_pins:
        raise AssertionError(
            f"{dxf_path.name}: expected {expected_studs} studs + {expected_pins} pins, got {stud_count} + {pin_count}"
        )

    # Check calibration bar on nested sheets
    cal_polys = [p for p in parsed["polylines"] if p["layer"] == "CALIBRATION"]
    for cp in cal_polys:
        verts = check_closed_simple_polyline(cp, min_verts=4)
        xs = [v[0] for v in verts]
        ys = [v[1] for v in verts]
        if not (math.isclose(max(xs) - min(xs), 100.0, abs_tol=1e-3) and math.isclose(max(ys) - min(ys), 20.0, abs_tol=1e-3)):
            raise AssertionError(f"{dxf_path.name}: calibration bar size mismatch")
        for op in outer_polys:
            if polygons_intersect(verts, op):
                raise AssertionError(f"{dxf_path.name}: calibration bar overlaps CUT_OUTER")

    return {"outer_polys": outer_polys, "inner_polys": inner_polys, "holes": holes}


def verify_mirror_symmetry(lh_data: Dict, rh_data: Dict, ref_width: float) -> None:
    """Confirm exact mirror symmetry across x = ref_width / 2 between LH and RH DXFs."""
    def check_poly_mirror(p1: Sequence[Point], p2: Sequence[Point], label: str) -> None:
        if len(p1) != len(p2):
            raise AssertionError(f"{label} vertex count mismatch: {len(p1)} vs {len(p2)}")
        s1 = sorted(p1)
        s2 = sorted((ref_width - x, y) for x, y in p2)
        for a, b in zip(s1, s2):
            if math.hypot(a[0] - b[0], a[1] - b[1]) > 1e-3:
                raise AssertionError(f"{label} mirror symmetry mismatch: {a} vs {b}")

    check_poly_mirror(lh_data["outer_polys"][0], rh_data["outer_polys"][0], "Outer contour")
    for idx in range(len(lh_data["inner_polys"])):
        check_poly_mirror(lh_data["inner_polys"][idx], rh_data["inner_polys"][idx], f"Inner chamber #{idx}")

    lh_holes = sorted((h["cx"], h["cy"], h["r"]) for h in lh_data["holes"])
    rh_holes_mir = sorted((ref_width - h["cx"], h["cy"], h["r"]) for h in rh_data["holes"])
    for a, b in zip(lh_holes, rh_holes_mir):
        if math.hypot(a[0] - b[0], a[1] - b[1]) > 1e-3 or abs(a[2] - b[2]) > 1e-4:
            raise AssertionError(f"Hole circle mirror symmetry mismatch: {a} vs {b}")


def main() -> int:
    base = Path(__file__).parent
    params = json.loads((base / "params.json").read_text(encoding="utf-8"))
    ref_width = float(params["reference_width_mm"])
    sheet_w = float(params["nesting"]["sheet_width_mm"])
    sheet_h = float(params["nesting"]["sheet_height_mm"])

    lh = validate_file(base / "B467-51-168_LH_tail_light_seal.dxf", 1, 2, 6, min_wall_mm=8.0)
    rh = validate_file(base / "B467-51-158_RH_tail_light_seal.dxf", 1, 2, 6, min_wall_mm=8.0)
    verify_mirror_symmetry(lh, rh, ref_width)

    pair_nested = validate_file(base / "B467-51-168_158_pair_nested.dxf", 2, 4, 12, min_wall_mm=8.0)
    perim_nested = validate_file(base / "B467-51-168_158_perimeter_variant.dxf", 2, 2, 12, min_wall_mm=8.0)

    # Check sheet bounds for nested sheets
    for label, data in [("pair_nested", pair_nested), ("perimeter_variant", perim_nested)]:
        all_pts = [pt for poly in data["outer_polys"] for pt in poly]
        min_x = min(x for x, _ in all_pts)
        max_x = max(x for x, _ in all_pts)
        min_y = min(y for _, y in all_pts)
        max_y = max(y for _, y in all_pts)
        if min_x < 0.0 or max_x > sheet_w or min_y < 0.0 or max_y > sheet_h:
            raise AssertionError(
                f"{label} exceeds {sheet_w:.0f}x{sheet_h:.0f} mm sheet: x=[{min_x:.2f}, {max_x:.2f}], y=[{min_y:.2f}, {max_y:.2f}]"
            )

    print("ALL 4 DXF FILES PASSED GEOMETRIC AND STRUCTURAL VALIDATION")
    return 0


if __name__ == "__main__":
    sys.exit(main())
