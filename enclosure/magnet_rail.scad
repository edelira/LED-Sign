// Drop-in wall rail for HUB75 panels hung by their own magnetic screws.
//
// Screw the rail to the wall, then lower the sign so the magnets on the
// panels' TOP screws drop into the channel. The channel is open along its
// whole length, so the screws can be anywhere left-to-right. The panel's
// weight sits on the shaft above the front lip; to take the sign down, lift
// it a few millimetres and pull it away.
//
//   side view (wall on the left)       |=| back plate (screwed to the wall)
//                                      | |  ___ magnet
//        wall | back | magnet | lip |  | | |   |
//             |      |  ===   | ||  |  | |_|___|__ shaft -> panel
//             |______|________|_||  |  |____lip
//                    floor
//
// The panels' BOTTOM magnets get a "foot" cup so the sign hangs plumb at
// the same distance from the wall.
//
// Units: mm. Render one part at a time:
//   openscad -D 'part="rail"' -o rail.stl magnet_rail.scad
// part = "rail" | "test" | "foot" | "preview"

part = "preview";

// ---- Measure these on one of the magnetic screws --------------------------
magnet_d    = 13;     // magnet diameter
magnet_h    = 5;      // magnet thickness
shaft_d     = 6;      // thickest part of the shaft between magnet and panel
shaft_gap   = 8;      // gap between the magnet and the back of the panel

// ---- Rail -------------------------------------------------------------------
rail_len    = 192;    // one panel wide (P3 64x64 = 192 mm); print one per panel
back_t      = 4;      // back plate thickness (wall side)
floor_t     = 3;
lip_t       = 3;      // front lip thickness; must be less than shaft_gap
clear       = 1.0;    // play around the magnet
screw_d     = 4.5;    // #8 / 4 mm wood screw or anchor screw
screw_head  = 9;      // countersink diameter
screws      = 3;      // wall screws per rail
dowel_d     = 1.95;   // 1.75 mm filament pins line up neighbouring rails

pocket  = magnet_h + clear;                 // channel depth (wall to lip)
mag_bot = floor_t + clear / 2;              // magnet bottom when hanging
shaft_c = mag_bot + magnet_d / 2;           // shaft centre height
lip_top = shaft_c - shaft_d / 2 - 0.5;      // shaft rests just above the lip
rail_h  = mag_bot + magnet_d + 14;          // room for the wall screws above
depth   = back_t + pocket + lip_t;

assert(lip_t < shaft_gap, "lip_t must be thinner than the gap behind the magnet");

$fn = 48;

// Cross-section: x = out from the wall, y = up.
module profile() {
    union() {
        square([back_t, rail_h]);                         // back plate
        square([depth, floor_t]);                         // floor
        translate([back_t + pocket, 0]) square([lip_t, lip_top]);   // front lip
    }
}

module rail(len = rail_len, holes = screws) {
    difference() {
        // Extrude along the wall, then stand it up: wall side is -Y, up is +Z.
        rotate([90, 0, 90]) linear_extrude(len) profile();
        // Countersunk wall screws in the plate above the magnets.
        for (i = [0 : holes - 1]) {
            x = holes == 1 ? len / 2 : 20 + i * (len - 40) / (holes - 1);
            translate([x, 0, rail_h - 7]) rotate([-90, 0, 0]) {
                translate([0, 0, -1]) cylinder(d = screw_d, h = back_t + 2);
                translate([0, 0, back_t - (screw_head - screw_d) / 2])
                    cylinder(d1 = screw_d, d2 = screw_head, h = (screw_head - screw_d) / 2 + 0.01);
                translate([0, 0, back_t]) cylinder(d = screw_head, h = 20);
            }
        }
        // Dowel holes in both ends so neighbouring rails line up.
        for (x = [0, len], z = [floor_t + 3, rail_h - 3])
            translate([x, back_t / 2, z]) rotate([0, 90, 0]) cylinder(d = dowel_d, h = 16, center = true);
    }
}

// Cup for a bottom magnet: its base holds the panel off the wall by the same
// amount as the rail does at the top, so the sign hangs straight.
module foot() {
    base = back_t + clear;
    difference() {
        cylinder(d = magnet_d + 3.2, h = base + magnet_h - 1);
        translate([0, 0, base]) cylinder(d = magnet_d + 0.4, h = magnet_h);
    }
}

if (part == "rail") rail();
if (part == "test") rail(40, 1);
if (part == "foot") foot();
if (part == "preview") {
    color("#333") rail();
    // Magnets hanging in the channel, with their shafts.
    for (x = [40, 152]) translate([x, back_t + clear / 2, mag_bot + magnet_d / 2]) rotate([-90, 0, 0]) {
        color("#bbb") cylinder(d = magnet_d, h = magnet_h);
        color("#888") cylinder(d = shaft_d, h = magnet_h + lip_t + shaft_gap);
    }
    // Back of the panel (only the top edge is drawn).
    color("#2a6", 0.5) translate([0, back_t + clear / 2 + magnet_h + shaft_gap, -30])
        cube([rail_len, 3, 70]);
}

echo(str("Rail: ", rail_len, " x ", rail_h, " mm tall, ", depth, " mm deep; magnet capture ",
         lip_top - mag_bot, " mm"));
