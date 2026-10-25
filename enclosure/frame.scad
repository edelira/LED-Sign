// LED-Sign frame: 2x Waveshare P4 64x32 panels (128x32) behind smoked acrylic.
// Units: mm. Z = 0 is the front face; parts print front-face-down on the bed.
// Sized for a Bambu P1S (256 x 256 bed): the bezel prints as 3 segments.
//
// Render one part at a time:  openscad -D 'part="seg_left"' -o seg_left.stl frame.scad
// part = "assembly" | "seg_left" | "seg_mid" | "seg_right" | "tab" | "splice" | "hanger" | "esp32_tray"

part = "assembly";

// ---- Measure these when the panels / acrylic arrive -------------------------
panel_w     = 256;    // one panel, outer width  (spec: 256)
panel_h     = 128;    // one panel, outer height (spec: 128)
panel_d     = 15;     // panel depth, LED face to back of its plastic frame
panels      = 2;
acrylic_t   = 3;      // smoked acrylic thickness
acrylic_m   = 4;      // acrylic extends this far past the panels on every side

// ---- Design ----------------------------------------------------------------
fit         = 0.5;    // total clearance per pocket dimension
lip         = 2;      // front bezel thickness
wall        = 5;      // wall outside the acrylic pocket
corner_r    = 2;
segments    = 3;      // 531 mm overall / 3 = 177 mm per piece
pilot_d     = 2.6;    // M3 self-tapping screw pilot (use 4.0 for M3 heat-set inserts)
pilot_depth = 10;
dowel_d     = 1.95;   // 1.75 mm filament offcuts as alignment pins
dowel_len   = 8;      // per side
standoff    = 30;     // hanger depth: room behind the panels for the ESP32 + wires

PW = panel_w * panels;
PH = panel_h;
AW = PW + 2 * acrylic_m;
AH = PH + 2 * acrylic_m;
OW = AW + fit + 2 * wall;
OH = AH + fit + 2 * wall;
D  = lip + acrylic_t + panel_d;          // rear edge is flush with the panel backs
rim_y = (OH / 2 + (PH + fit) / 2) / 2;    // centreline of top/bottom wall at the back
rim_x = (OW / 2 + (PW + fit) / 2) / 2;    // centreline of the end walls at the back
seam_x = [for (i = [1 : segments - 1]) -OW / 2 + i * OW / segments];

top_holes    = [-220, -172, -128, seam_x[0] - 8, seam_x[0] + 8, 0,
                seam_x[1] - 8, seam_x[1] + 8, 128, 172, 220];
bottom_holes = [-220, -150, seam_x[0] - 8, seam_x[0] + 8, 0,
                seam_x[1] - 8, seam_x[1] + 8, 150, 220];
end_holes    = [-35, 35];

$fn = 40;
eps = 0.01;

module rrect(w, h, r) { offset(r) square([w - 2 * r, h - 2 * r], center = true); }

module bezel() {
    difference() {
        linear_extrude(D) rrect(OW, OH, corner_r);
        // window: exactly the LED area
        translate([0, 0, -1]) linear_extrude(lip + 2) square([PW + fit, PH + fit], center = true);
        // acrylic pocket
        translate([0, 0, lip]) linear_extrude(acrylic_t + eps) square([AW + fit, AH + fit], center = true);
        // 45-degree step down to the panel pocket (no unsupported ledge when printing)
        hull() {
            translate([0, 0, lip + acrylic_t]) linear_extrude(eps) square([AW + fit, AH + fit], center = true);
            translate([0, 0, lip + acrylic_t + acrylic_m]) linear_extrude(eps) square([PW + fit, PH + fit], center = true);
        }
        translate([0, 0, lip + acrylic_t]) linear_extrude(D) square([PW + fit, PH + fit], center = true);
        // screw pilots in the rear edge
        for (x = top_holes)    translate([x,  rim_y, D - pilot_depth]) cylinder(d = pilot_d, h = pilot_depth + 1);
        for (x = bottom_holes) translate([x, -rim_y, D - pilot_depth]) cylinder(d = pilot_d, h = pilot_depth + 1);
        for (s = [-1, 1], y = end_holes) translate([s * rim_x, y, D - pilot_depth]) cylinder(d = pilot_d, h = pilot_depth + 1);
        // dowel holes across each seam, top and bottom walls
        for (x = seam_x, s = [-1, 1])
            translate([x, s * (OH / 2 - wall / 2 - 0.5), lip + acrylic_t + 2])
                rotate([0, 90, 0]) cylinder(d = dowel_d, h = 2 * dowel_len, center = true);
    }
}

module segment(i) {
    x0 = -OW / 2 + i * OW / segments;
    intersection() {
        bezel();
        translate([x0, -OH, -1]) cube([OW / segments, 2 * OH, D + 2]);
    }
}

// Flat clamp that screws to the rear edge and holds the panel against the acrylic.
// Loosen and swing it aside to remove the panels.
module tab(w = 16, holes = [0]) {
    reach = (OH / 2 - rim_y) + 10;        // covers the wall, overlaps the panel ~6 mm
    difference() {
        translate([-w / 2, 0, 0]) linear_extrude(3) offset(1) offset(-1) square([w, reach]);
        for (x = holes) translate([x, OH / 2 - rim_y, -1]) cylinder(d = 3.4, h = 5);
    }
}

module splice() { tab(32, [-8, 8]); }      // spans a seam: one screw into each segment

// Wall hanger: clamps like a tab, stands the sign off the wall, keyhole for a screw head.
module hanger() {
    plate_w = 60; plate_h = 22; block_w = 30;
    hole_y = OH / 2 - rim_y;              // from the outer (top) edge of the frame
    difference() {
        union() {
            translate([-plate_w / 2, 0, 0]) cube([plate_w, plate_h, 3]);
            translate([-block_w / 2, 0, 0]) cube([block_w, plate_h, 3 + standoff]);
        }
        for (x = [-22, 22]) translate([x, hole_y, -1]) cylinder(d = 3.4, h = 5);
        // keyhole on the wall-facing face: drop in at the big hole, slide toward the top edge
        top = 3 + standoff;
        translate([0, 16, top - 4]) cylinder(d = 9.5, h = 5);                 // entry
        hull() for (y = [6, 16]) translate([0, y, top - 3 - 4]) cylinder(d = 9.5, h = 4);  // head pocket
        hull() for (y = [6, 16]) translate([0, y, top - 4]) cylinder(d = 4.6, h = 5);      // shank slot
    }
}

// Tray for a 30/38-pin ESP32 DevKit (pins up). Fix to the panel back with VHB tape
// or with M3 screws through the slots into the panel's threaded mounting holes.
module esp32_tray() {
    iw = 57; ih = 30.5; t = 2;
    difference() {
        union() {
            translate([-iw / 2 - t, -ih / 2 - t, 0]) cube([iw + 2 * t, ih + 2 * t, t + 4]);
            translate([-iw / 2 - t - 14, -8, 0]) cube([iw + 2 * t + 28, 16, t]);
        }
        translate([-iw / 2, -ih / 2, t]) cube([iw, ih, 10]);
        translate([-iw / 2 + 8, -ih / 2 - t - 1, t]) cube([iw - 16, ih + 2 * t + 2, 10]);  // USB / wire exits
        for (s = [-1, 1]) hull() for (dx = [0, 7]) translate([s * (iw / 2 + t + 3.5 + dx), 0, -1]) cylinder(d = 3.4, h = t + 2);
    }
}

if (part == "seg_left")   segment(0);
if (part == "seg_mid")    segment(1);
if (part == "seg_right")  segment(2);
if (part == "tab")        tab();
if (part == "splice")     splice();
if (part == "hanger")     hanger();
if (part == "esp32_tray") esp32_tray();
if (part == "assembly") {
    color("#1a1a1a") for (i = [0 : segments - 1]) translate([(i - 1) * 6, 0, 0]) segment(i);
    color("#55555580") translate([0, 0, lip]) linear_extrude(acrylic_t) square([AW, AH], center = true);
    color("#2a6") translate([0, 0, lip + acrylic_t]) linear_extrude(panel_d) square([PW, PH], center = true);
}
echo(str("Overall: ", OW, " x ", OH, " x ", D, " mm  (", OW / 25.4, " x ", OH / 25.4, " in)"));
echo(str("Segment length: ", OW / segments, " mm"));
echo(str("Acrylic to order: ", AW, " x ", AH, " x ", acrylic_t, " mm"));
echo(str("Seams at x = ", seam_x));
