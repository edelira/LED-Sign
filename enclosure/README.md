# Enclosure: 3D-printed frame for 2× P4 64×32 panels

Parametric OpenSCAD design (`frame.scad`) for a Bambu P1S. The finished sign is
**530.5 × 146.5 × 20 mm (20.9" × 5.8" × 0.8")** plus a 33 mm wall standoff.

```
 front ──► [ PLA bezel lip ][ smoked acrylic ][ panel | panel ] ◄── tabs / hangers ── wall
```

## Before printing: measure and update `frame.scad`
The defaults come from the Waveshare spec sheet. Measure the real parts and edit
the values at the top of the file:

| Variable | Default | What to measure |
|---|---|---|
| `panel_w`, `panel_h` | 256, 128 | Outer size of one panel |
| `panel_d` | 15 | LED face to the back of the panel's plastic frame |
| `acrylic_t` | 3 | Acrylic thickness |

Re-export after changing anything (or open the file in OpenSCAD and press F6, then export):
```
for p in seg_left seg_mid seg_right tab splice hanger esp32_tray; do
  openscad -D "part=\"$p\"" -o stl/$p.stl frame.scad
done
```

## Parts (`stl/`)
| File | Qty | Notes |
|---|---|---|
| `seg_left.stl`, `seg_mid.stl`, `seg_right.stl` | 1 each | Bezel, ~177 mm each. Print **front face down** on the textured plate for a clean matte front. |
| `tab.stl` | 12 | Clamps the panels against the acrylic. Loosen one screw and swing it aside to remove the panels. |
| `splice.stl` | 4 | Spans each seam, top and bottom. One screw into each segment. |
| `hanger.stl` | 2 | Clamps the top edge, stands the sign 33 mm off the wall, and has a keyhole. |
| `esp32_tray.stl` | 1 | Holds the ESP32 DevKit on the back of a panel (VHB tape, or M3 into the panel's threaded holes). |

**Print settings:** black PLA, 0.2 mm layers, 4 walls, 15% infill, no supports.

## Hardware
- Smoked acrylic sheet, **520 × 136 × 3 mm**. A light to medium smoke tint (roughly
  30–50% light transmission) keeps the LEDs bright and hides the circuit board.
- 24× M3 × 8–10 mm self-tapping screws (or M3 screws with heat-set inserts:
  set `pilot_d = 4.0`).
- 4× 15 mm pieces of 1.75 mm filament as alignment dowels at the seams.
- Super glue (CA) for the seams (optional; the splices hold it together).
- 2 wall screws with heads up to 9 mm wide.

## Assembly
1. Push filament dowels into one side of each seam, add a drop of CA glue, and press
   the 3 segments together face down on a flat surface.
2. Lay the bezel face down. Drop in the acrylic, then both panels (the panels' input
   connectors should be on the side where the ESP32 will sit).
3. Screw on the splices over each seam, the tabs, and the two hangers on the top edge.
4. Mount the ESP32 tray on the back of a panel and wire it as in the main README.

## Hanging
- The keyholes are **300 mm (11.8") apart**, centered on the sign.
- Put two screws in the wall, level, 300 mm apart, leaving the heads 3–4 mm proud.
- Hook the sign on and slide it down. The top of the sign ends up about 6 mm (¼")
  above the screws.
