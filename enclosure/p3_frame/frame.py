#!/usr/bin/env python3
"""Rear frame for the 3x 64x64 P3 sign (576 x 192 mm). CadQuery; run:
    pip install cadquery && python3 frame.py        -> stl/*.stl

Nothing sits in front of the LEDs: the panels drop in from the front onto a
ledge and are held by M3 screws into their own threaded holes, driven from
the back. A thin wall wraps the panel edges, flush with the LED face.

Axes as printed: x = left/right seen from the FRONT, y = up, z = 0 at the
wall (print bed) rising towards the LED face. Every part prints as modelled,
without supports.

Hole pattern per panel (from the centre of a 192 mm panel) is taken from the
"Waveshare LED Matrix" housing STL the owner supplied:
  M3 top/bottom: (-78.5, 0, +78.5 ; +-86.8)    M3 sides: (+-86.8 ; +-7.5)
  4 mm side holes: (+-87 ; +-62)
Print test_jig.stl first to check it against a real panel.
"""
import cadquery as cq

# ---- measure these on the real sign -------------------------------------
PANEL      = 192.0   # one panel, edge to edge
N          = 3       # panels side by side
PANEL_D    = 13.0    # LED face to the flat back rim of the panel's plastic frame
REAR       = 27.0    # room behind the ledge for wiring (+3 mm ledge = 30 mm behind the panels)
CLR        = 0.4     # gap between panel edge and wall, each side
# Matrix Portal bump (set BAY_SIDE = None for no bump)
BAY_SIDE   = "left"  # side it sticks out of, seen from the FRONT
BAY_OUT    = 12.0    # room past the frame's side wall
BAY_H      = 40.0    # opening height (the board is ~26 mm wide)
BAY_Y      = 0.0     # centre of the board above (+) / below (-) the panel's mid-height
USB_W      = 13.0    # cable slot in the end of the bump
# ---- frame --------------------------------------------------------------
WALL  = 2.4          # 6 lines with a 0.4 nozzle
LEDGE = 20.0         # ledge width under the panel rim (the sample uses 19)
LEDGE_T = 3.0
HEAD  = 1.6          # plastic left under each screw head (M3x6 screws)
JOINT = 120.0        # frame is cut at x = +-JOINT (240 mm middle rails)
STUD  = 406.4 / 2    # keyholes 16" apart
HOLES_TB = [(-78.5, 86.8), (0, 86.8), (78.5, 86.8)]
HOLES_SIDE = [(86.8, 7.5)]
PINS_SIDE = [(87.0, 62.0)]

Xi, Yi = N * PANEL / 2 + CLR, PANEL / 2 + CLR      # inside of the wall
Xo, Yo = Xi + WALL, Yi + WALL
G = LEDGE + CLR
SEAT = REAR + LEDGE_T                              # panel back rim sits here
H = SEAT + PANEL_D
E = 0.01


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl(x, y, d, z0, z1):
    return cq.Workplane("XY").circle(d / 2).extrude(z1 - z0).translate((x, y, z0))


def cyl_x(x0, x1, y, z, d):
    return cq.Workplane("YZ").circle(d / 2).extrude(x1 - x0).translate((x0, y, z))


def frame():
    f = box(-Xo, Xo, -Yo, Yo, 0, H).edges("|Z").fillet(2.0)
    # inside: panel pocket, ledge opening, 45 degree underside, open back
    f = f.cut(box(-Xi, Xi, -Yi, Yi, SEAT, H + E))
    f = f.cut(box(-Xi + G, Xi - G, -Yi + G, Yi - G, REAR - E, SEAT + E))
    taper = (cq.Workplane("XY").workplane(offset=REAR - G).rect(2 * Xi, 2 * Yi)
             .workplane(offset=G).rect(2 * (Xi - G), 2 * (Yi - G)).loft(combine=True))
    f = f.cut(taper).cut(box(-Xi, Xi, -Yi, Yi, -E, REAR - G + E))

    cuts = []
    def screw(x, y):
        cuts.append(cyl(x, y, 3.4, -E, H))
        cuts.append(cyl(x, y, 6.5, -E, SEAT - HEAD))
    for i in range(N):
        cx = (i - (N - 1) / 2) * PANEL
        for dx, dy in HOLES_TB:
            for s in (1, -1):
                screw(cx + dx, s * dy)
        for k in (-80, -40, 0, 40, 80):                # vent slots, top and bottom
            x = cx + k
            for s in (1, -1):
                if s == 1 and abs(abs(x) - STUD) < 22: continue
                if s == -1 and abs(x) < 22: continue
                if abs(abs(x) - JOINT) < 14: continue
                cuts.append(box(x - 9, x + 9, s * Yi - 1 if s > 0 else -Yo - 1, s * Yo + 1 if s > 0 else -Yi + 1, 2.5, 6.0))
    for sx in (1, -1):
        cx = sx * (N - 1) / 2 * PANEL
        for dx, dy in HOLES_SIDE:
            for s in (1, -1): screw(cx + sx * dx, s * dy)
        for dx, dy in PINS_SIDE:
            for s in (1, -1): cuts.append(cyl(cx + sx * dx, s * dy, 4.4, -E, H))
        for s in (1, -1):                               # filament dowels across the joints
            cuts.append(cyl_x(sx * JOINT - 7, sx * JOINT + 7, s * (Yi - 3.5), 22, 2.0))
    cuts.append(box(-9, 9, -Yo - 1, -Yi + 1, -E, 6.5))  # power cable, bottom centre

    for sx in (1, -1):                                  # keyhole tabs (top, against the wall)
        x = sx * STUD
        f = f.union(box(x - 11, x + 11, Yi - 26, Yi + E, 0, 3))
        cuts.append(cyl(x, Yi - 18, 9.5, -E, 3 + E))
        cuts.append(cyl(x, Yi - 8, 4.6, -E, 3 + E))
        cuts.append(box(x - 2.3, x + 2.3, Yi - 18, Yi - 8, -E, 3 + E))

    if BAY_SIDE:
        m = -1 if BAY_SIDE == "left" else 1
        y0, y1 = BAY_Y - BAY_H / 2, BAY_Y + BAY_H / 2
        def bx(a, b, *r):                               # a, b = distance out from the centre
            return box(min(m * a, m * b), max(m * a, m * b), *r)
        f = f.union(bx(Xo - E, Xo + BAY_OUT + 2, y0 - 2, y1 + 2, 0, SEAT))
        cuts.append(bx(Xi - G - E, Xo + BAY_OUT, y0, y1, -E, SEAT - 1.2))   # through wall + ledge
        cuts.append(bx(Xi - G - E, Xi, y0, y1, SEAT - 1.3, SEAT + E))       # no ledge under the board
        cuts.append(bx(Xo + BAY_OUT - E, Xo + BAY_OUT + 3, BAY_Y - USB_W / 2, BAY_Y + USB_W / 2, -E, SEAT - 5))
    for c in cuts:
        f = f.cut(c)
    return f


def tie_plate():
    """Joins two panels across a seam using their side holes."""
    p = box(-17, 17, -15, 15, 0, LEDGE_T).edges("|Z").fillet(3)
    for sx in (1, -1):
        for sy in (1, -1):
            x, y = sx * (PANEL / 2 - HOLES_SIDE[0][0]), sy * HOLES_SIDE[0][1]
            p = p.cut(cyl(x, y, 3.4, -E, 4)).cut(cyl(x, y, 6.5, HEAD, 4))
    return p


def test_jig():
    """1.2 mm outline of one panel's back with every hole: check before printing the frame."""
    j = box(-96, 96, -96, 96, 0, 1.2).cut(box(-76, 76, -76, 76, -E, 2))
    for s in (1, -1):
        for dx, dy in HOLES_TB: j = j.cut(cyl(dx, s * dy, 3.4, -E, 2))
        for t in (1, -1):
            j = j.cut(cyl(s * HOLES_SIDE[0][0], t * HOLES_SIDE[0][1], 3.4, -E, 2))
            j = j.cut(cyl(s * PINS_SIDE[0][0], t * PINS_SIDE[0][1], 4.4, -E, 2))
    return j


if __name__ == "__main__":
    import os
    os.makedirs("stl", exist_ok=True)
    f = frame()
    big = 400
    parts = {
        "side_left": f.intersect(box(-big, -JOINT, -big, big, -1, 99)),
        "side_right": f.intersect(box(JOINT, big, -big, big, -1, 99)),
        "mid_top": f.intersect(box(-JOINT, JOINT, 0, big, -1, 99)),
        "mid_bottom": f.intersect(box(-JOINT, JOINT, -big, 0, -1, 99)),
        "tie_plate": tie_plate(),
        "test_jig": test_jig(),
        "_assembled": f,
    }
    for name, p in parts.items():
        cq.exporters.export(p, f"stl/{name}.stl", tolerance=0.02, angularTolerance=0.2)
        bb = p.val().BoundingBox()
        print(f"{name:12s} {bb.xlen:6.1f} x {bb.ylen:6.1f} x {bb.zlen:5.1f} mm  {p.val().Volume() / 1000:6.1f} cm3  solids={p.solids().size()}")
