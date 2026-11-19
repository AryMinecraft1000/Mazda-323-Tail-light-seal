# 1993 Mazda 323 BG 3-Door Hatchback — Tail Light Seal DXF Templates

Parametric 1:1 millimeter DXF cutting models and SVG blueprint for the rear combination lamp housing gaskets, cross-verified across **three independent sources**: New Old Stock (NOS) OEM **Stanley `043-1305R`** (`Mazda BS20-51-170A`) factory charcoal foam gasket, bare OEM **Stanley `043-1305R`** housing + **Amayama Mazda EPC** (`B467-51-168` / `B467-51-158`, `6× 99940-0503` M5 nuts), and a physical 1993 323 BG 3-door OEM seal measured against a metric/imperial tape measure (`0.1–1.2 mm` 6-stud agreement):
- **`B467-51-168`** (`B46751168`): Left-Hand (LH / Driver Side, Stanley `043-1305L`, housing `B467-51-161`)
- **`B467-51-158`** (`B46751158`): Right-Hand (RH / Passenger Side, Stanley `043-1305R`, housing `B467-51-151` / `BS20-51-170A`)

> **Orientation & Cutting Note:** Both DXF templates are drawn **Body-Mating Face UP** (matching the factory `L` / `R` stamp on the NOS Stanley `043-1305R` gasket). When cutting **single-sided self-adhesive EPDM**, place the sheet **adhesive-side DOWN** (protective liner facing down) so each cut gasket bonds directly onto its matching LH (`043-1305L`) or RH (`043-1305R`) lamp housing without mirroring. **Print `preview_blueprint.svg` at 100% scale on paper, verify the `100.0 mm × 20.0 mm` calibration coupon, and test-fit against your physical lamp housing before cutting foam.**

## Preview

![1993 Mazda 323 BG 3-Door Tail Light Seal Render](render_preview.png)

For 1:1 scale paper printing and dimension callouts, see [preview_blueprint.svg](preview_blueprint.svg).

## Geometry Highlights

- **Outer Contour (`CUT_OUTER`):** `335.0 mm × 149.0 mm` body with a slanted inboard (hatch-side) edge, rounded corners, and a subtle **`2.5 mm`** bottom step-down under the outboard chamber.
- **Two Asymmetric Stepped Inner Cutouts (`CUT_INNER`):**
  - **Inboard / Hatch-Side Cutout:** Stepped inward at the top-inboard boss (`H1`) and the wider double-hole bottom-inboard boss (`H2` & `H3`).
  - **Outboard / Fender-Side Cutout:** Stepped inward at the upper-bridge boss (`H4`) and along the lower-outboard boss (`H7` & `H8`), separated from the inboard cutout by the slanted (`~10°`) central bridge rib.
- **Eight Mounting Stud & Locator Holes (`CUT_HOLES`):** `6× Ø8.5 mm` M5 stud-collar clearance holes (`H1`, `H2`, `H4`, `H5`, `H6`, `H8`) + `2× Ø6.5 mm` molded plastic locating pin holes (`H3_bottom_inboard_pin`, `H7_mid_outboard_pin`).

## Generated Files

| File | Description |
| --- | --- |
| `B467-51-168_LH_tail_light_seal.dxf` | Left-Hand (LH / Stanley `043-1305L`) 2-aperture OEM gasket (AutoCAD R12 `AC1009`, mm) |
| `B467-51-158_RH_tail_light_seal.dxf` | Right-Hand (RH / Stanley `043-1305R`) 2-aperture OEM gasket (exact mirror of LH) |
| `B467-51-168_158_pair_nested.dxf` | LH + RH pair nested on a `380 mm × 400 mm` sheet with `100 mm` calibration bar |
| `B467-51-168_158_perimeter_variant.dxf` | LH + RH single-aperture perimeter ring variant (without central bridge rib) |
| `preview_blueprint.svg` | 1:1 printable visual blueprint with hole callouts, coordinate table, and `100 mm` scale bar |
| `params.json` | Editable millimeter polygon corners, fillet radii, and hole coordinates |
| `generate_seal_dxf.py` | Pure-Python generator script (standard library only) |
| `validate_dxf.py` | Structural and geometric DXF validator |

## DXF Layer Structure

| Layer | ACI Color | Contents |
| --- | --- | --- |
| `CUT_OUTER` | `7` (White) | Outer gasket perimeter incl. slanted hatch-side edge & `2.5 mm` bottom step (closed `POLYLINE`, `flag 70 = 1`) |
| `CUT_INNER` | `3` (Green) | Stepped inner chamber cutouts (closed `POLYLINE`, `flag 70 = 1`) |
| `CUT_HOLES` | `1` (Red) | `6× Ø8.5 mm` M5 stud-collar holes + `2× Ø6.5 mm` locating pin holes (`CIRCLE`) |
| `CALIBRATION` | `5` (Blue) | `100.0 mm × 20.0 mm` scale verification rectangle (nested sheets) |
| `ANNOTATIONS` | `8` (Gray) | Part numbers, crosshairs, sheet border, and material notes |

## Recommended Material & Thickness

- **Material:** **Closed-cell EPDM sponge / cellular rubber** (*Zellkautschuk* / *cauciuc spongios EPDM cu celule închise*). Closed-cell EPDM is UV-, ozone-, and weather-resistant (`-40 °C` to `+100 °C`) and does not absorb water. **Avoid open-cell foam**, which wicks water into the trunk/spare-tire well.
- **Thickness:** **`4 mm` (recommended)** — **`3 mm – 5 mm` acceptable**.
  - `4 mm`–`5 mm` compresses cleanly against the sheet-metal body lip without over-stressing the tail-light housing studs.
  - `3 mm` works well if the body flange is flat and undistorted.
- **Adhesive Backing:** Plain (no adhesive) or **single-sided self-adhesive** (applied to the plastic lamp housing side so the gasket remains removable from the painted body).
- **Minimum Sheet Size:** At least **`380 mm × 400 mm`** (e.g., `500 × 500 mm` or `500 × 1000 mm`) to cut both LH and RH seals from `B467-51-168_158_pair_nested.dxf`, or **`360 mm × 180 mm`** per single seal.

### EU Purchase Links (Verified)

| Supplier | Product | Thickness | Backing |
| --- | --- | --- | --- |
| [Diconfa (DE / EU)](https://diconfa.de/en/epdm-cellular-rubber-foam-sheet-in-various-sizes/) | EPDM Cellular Rubber Foam Sheet (custom sizes) | `1–50 mm` (select `4 mm` or `5 mm`) | Plain or self-adhesive |
| [VRTrade (NL / EU)](https://vrtrade.com/foam-rubber-sheet-epdm-4mm-width-100cm.html) | EPDM Sponge Rubber Sheet `4 mm` (`100 cm` width) | `4 mm` | Plain |
| [Fugendichtband24 (DE / EU)](https://www.fugendichtband24.de/EPDM-Zellkautschuk-Matten-4mm-Staerke-einseitig-selbstklebend-diverse-Abmessungen.htm) | EPDM Zellkautschuk Matten `4 mm` | `4 mm` | Single-sided self-adhesive |
| [Gummiprofile24 (DE / EU)](https://www.gummiprofile24.de/epdm_zellkautschuk-platte_5mm) | EPDM Zellkautschuk Platte / Matte `5 mm` | `5 mm` | Plain |

### Romanian Purchase Links (Verified In Stock)

| Supplier | Product | Thickness | Backing |
| --- | --- | --- | --- |
| [eMAG.ro (Genius / easybox)](https://www.emag.ro/cauciuc-spongios-pentru-garnituri-epdm-placa-100x100cm-grosime-5mm-rub-007/pd/D3CG6G3BM/) | Cauciuc spongios pentru garnituri EPDM, placă `100 × 100 cm` (`RUB-007`) | `5 mm` | Plain |
| [CovoareCauciuc.ro](https://www.covoarecauciuc.ro/placi-din-cauciuc-spongios/placa-cauciuc-epdm-spongios-grosime-5mm-1000x1000mm.html) | Placă cauciuc EPDM spongios (`1000 × 1000 mm`) | `5 mm` | Plain |
| [CovoareCauciuc.ro](https://www.covoarecauciuc.ro/placi-din-cauciuc-spongios/placa-cauciuc-epdm-spongios-autoadeziv-grosime-5mm-latime-1000mm.html) | Placă cauciuc EPDM spongios autoadeziv (`1000 mm` lățime) | `5 mm` | Single-sided self-adhesive |
| [CovoareCauciuc.ro](https://www.covoarecauciuc.ro/placi-din-cauciuc-spongios/placa-cauciuc-epdm-spongios-grosime-3mm-1000x1000mm.html) | Placă cauciuc EPDM spongios (`1000 × 1000 mm`) | `3 mm` | Plain |
| [CovoareCauciuc.ro](https://www.covoarecauciuc.ro/placi-din-cauciuc-spongios/placa-cauciuc-epdm-spongios-autoadeziv-grosime-3mm-latime-1000mm.html) | Placă cauciuc EPDM spongios autoadeziv (`1000 mm` lățime) | `3 mm` | Single-sided self-adhesive |

## Customizing & Regenerating

Edit any vertex `{x, y, r}` or hole coordinate (`H1`–`H8`) in `params.json`, then regenerate and validate:

```bash
python3 generate_seal_dxf.py
python3 validate_dxf.py
```
