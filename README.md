# 1993 Mazda 323 BG 3-Door Hatchback — Tail Light Seal DXF Templates

Parametric 1:1 millimeter DXF cutting models and SVG blueprint for the rear combination lamp housing gaskets:
- **`B467-51-168`** (`B46751168`): Left-Hand (LH / Driver Side)
- **`B467-51-158`** (`B46751158`): Right-Hand (RH / Passenger Side)

> **Important Fitment Note:** Mazda never published standalone engineering blueprints for `B467-51-168` / `B467-51-158` (they were die-cut closed-cell foam gaskets supplied with the `B467-51-161` / `B467-51-151` lamp housings). These DXF files provide a 1:1 millimeter parametric starting model based on the 323 BG 3-door hatchback wrap-around lamp geometry. **Print `preview_blueprint.svg` at 100% scale on paper, verify the `100.0 mm × 20.0 mm` calibration coupon, and test-fit against your physical lamp housing before cutting foam.**

## Generated Files

| File | Description |
| --- | --- |
| `B467-51-168_LH_tail_light_seal.dxf` | Left-Hand (LH) 2-aperture OEM-style gasket (AutoCAD R12 `AC1009`, mm) |
| `B467-51-158_RH_tail_light_seal.dxf` | Right-Hand (RH) 2-aperture OEM-style gasket (exact mirror of LH) |
| `B467-51-168_158_pair_nested.dxf` | LH + RH 2-aperture pair nested on a `380 mm × 340 mm` sheet with `100 mm` calibration bar |
| `B467-51-168_158_perimeter_variant.dxf` | LH + RH single-aperture perimeter ring variant (no central bridge rib) |
| `preview_blueprint.svg` | 1:1 printable visual blueprint with hole callouts, coordinate table, and `100 mm` scale bar |
| `params.json` | Editable millimeter dimensions, stud coordinates, corner radii, and chamber bounds |
| `generate_seal_dxf.py` | Pure-Python generator script (standard library only) |
| `validate_dxf.py` | Structural and geometric DXF validator |

## DXF Layer Structure

| Layer | ACI Color | Contents |
| --- | --- | --- |
| `CUT_OUTER` | `7` (White) | Outer gasket perimeter (closed `POLYLINE`, `flag 70 = 1`) |
| `CUT_INNER` | `3` (Green) | Inner chamber cutouts (closed `POLYLINE`, `flag 70 = 1`) |
| `CUT_HOLES` | `1` (Red) | 3× mounting stud holes (`Ø6.5 mm` `CIRCLE`) |
| `CUT_DRAIN_RELIEF` | `4` (Cyan) | Optional `6.0 mm × 4.0 mm` bottom weep relief notch |
| `CALIBRATION` | `5` (Blue) | `100.0 mm × 20.0 mm` scale verification rectangle (nested sheets) |
| `ANNOTATIONS` | `8` (Gray) | Part numbers, crosshairs, sheet border, and material notes |

## Material Recommendation

- **3 mm – 5 mm closed-cell EPDM sponge foam rubber** (single-sided pressure-sensitive adhesive backing optional on the housing side). Avoid open-cell foam, which absorbs water and causes trunk leaks.

## Customizing & Regenerating

Edit any value in `params.json` (such as stud coordinates `S1`–`S4`, alignment pin `P1`, outer dimensions, or chamber cutouts), then regenerate and validate:

```bash
python3 generate_seal_dxf.py
python3 validate_dxf.py
```
