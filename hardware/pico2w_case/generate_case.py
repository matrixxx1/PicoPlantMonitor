"""Generate a two-piece Pico 2 W case (millimetres).

Requires trimesh and manifold3d: py -m pip install trimesh manifold3d
The board outline and hole centres follow Figure 3 of the official
Pico 2 W datasheet. Inspect a printed test fit before final installation.
"""

from pathlib import Path

import trimesh


BASE_OUT = Path(__file__).resolve().parent / 'pico2w_open_case.stl'
LID_OUT = Path(__file__).resolve().parent / 'pico2w_lid.stl'
FLOOR = 4.5
STANDOFF_TOP = 12.5  # 8 mm gap above the floor for soldered header tails
LID_ROOF = 2.4
LID_POST = 12.25  # half-length posts; lid underside is 16.75 mm above base bottom
LID_WALL = 2.4
USB_WALL_OPENING = 50.0
BOARD_HOLES_X = (-5.7, 5.7)       # 11.4 mm between columns
BOARD_HOLES_Y = (-23.5, 23.5)     # 2 mm from each end of 51 mm PCB
EXTERNAL_HOLES = ((-24, -30), (45, -30), (-24, 30), (45, 30))
OLED_CENTRE = (34, -8)
OLED_HOLE_HALF_SPACING = 11.85  # adjustable around common 23–24 mm patterns


def box(size, centre):
    mesh = trimesh.creation.box(extents=size)
    mesh.apply_translation(centre)
    return mesh


def cylinder(radius, height, centre, sections=64):
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    mesh.apply_translation(centre)
    return mesh


def horizontal_slot(length, diameter, height, centre):
    """Rounded slot used for tolerance-sensitive OLED mounting holes."""
    x, y, z = centre
    straight = length - diameter
    pieces = [box((straight, diameter, height), centre)]
    for offset in (-straight / 2, straight / 2):
        pieces.append(cylinder(diameter / 2, height, (x + offset, y, z)))
    return trimesh.boolean.union(pieces, engine='manifold')


def build_base():
    # USB apron runs 38.5 mm beyond the PCB. The right-hand wing is wider
    # than the left ledge, while the four external holes surround the board.
    main = box((49, 103, FLOOR), (-6.5, -12.5, FLOOR / 2))  # -31..18, -64..39
    wing = box((37, 78, FLOOR), (36.5, 0, FLOOR / 2))  # 18..55, -39..39
    solids = [main, wing]
    for x in BOARD_HOLES_X:
        for y in BOARD_HOLES_Y:
            solids.append(cylinder(2.5, STANDOFF_TOP - FLOOR,
                                   (x, y, (STANDOFF_TOP + FLOOR) / 2)))
    cradle = trimesh.boolean.union(solids, engine='manifold')

    cuts = []
    # M2 clearance through each 2.1 mm board-hole centre. The underside has
    # a 4.42 mm across-flats hex recess for an M2 nut (measure your hardware).
    for x in BOARD_HOLES_X:
        for y in BOARD_HOLES_Y:
            cuts.append(cylinder(1.1, STANDOFF_TOP + 1, (x, y, STANDOFF_TOP / 2)))
            cuts.append(cylinder(2.55, 2.2, (x, y, 1.0), sections=6))

    # Four M3 holes span both sides and both ends of the Pico footprint.
    for x, y in EXTERNAL_HOLES:
        cuts.append(cylinder(1.7, FLOOR + 1, (x, y, FLOOR / 2)))

    # Window below the wireless antenna; no cover or lip surrounds it.
    cuts.append(box((15, 11, FLOOR + 1), (0, 12.5, FLOOR / 2)))
    cradle = trimesh.boolean.difference([cradle, *cuts], engine='manifold')
    if not cradle.is_watertight or cradle.body_count != 1:
        raise RuntimeError('Generated case is not one watertight solid')
    return cradle


def build_lid():
    # Print the lid upside-down: roof on the bed, four posts growing upward.
    # After flipping onto the base, the roof underside is 16.75 mm above its
    # bottom, leaving 3.25 mm over the Pico PCB top and open pin rows.
    solids = [box((86, 78, LID_ROOF), (12, 0, LID_ROOF / 2))]
    wall_z = LID_ROOF + LID_POST / 2
    # Full-height perimeter walls meet the base. The USB end deliberately has
    # an oversized 50 mm opening for bulky plugs and easy cable handling.
    solids.extend([
        box((LID_WALL, 78, LID_POST), (-31 + LID_WALL / 2, 0, wall_z)),
        box((LID_WALL, 78, LID_POST), (55 - LID_WALL / 2, 0, wall_z)),
        box((86, LID_WALL, LID_POST), (12, 39 - LID_WALL / 2, wall_z)),
        box(((86 - USB_WALL_OPENING) / 2, LID_WALL, LID_POST),
            (-31 + (86 - USB_WALL_OPENING) / 4, -39 + LID_WALL / 2, wall_z)),
        box(((86 - USB_WALL_OPENING) / 2, LID_WALL, LID_POST),
            (55 - (86 - USB_WALL_OPENING) / 4, -39 + LID_WALL / 2, wall_z)),
    ])
    for x, y in EXTERNAL_HOLES:
        solids.append(cylinder(5.2, LID_POST,
                               (x, y, LID_ROOF + LID_POST / 2)))
    # Reinforce the roof around the four OLED screw slots on the inside of the
    # lid. The OLED itself sits on the outside on M2 spacers.
    for x_sign in (-1, 1):
        for y_sign in (-1, 1):
            x = OLED_CENTRE[0] + x_sign * OLED_HOLE_HALF_SPACING
            y = OLED_CENTRE[1] + y_sign * OLED_HOLE_HALF_SPACING
            solids.append(box((7, 6, 2.0), (x, y, LID_ROOF + 1.0)))
    lid = trimesh.boolean.union(solids, engine='manifold')
    cuts = []
    for x, y in EXTERNAL_HOLES:
        cuts.append(cylinder(1.7, LID_POST + LID_ROOF + 1,
                             (x, y, (LID_POST + LID_ROOF) / 2)))
    # Long slots expose both pin banks. A short crossbar between pin positions
    # braces the centre of the roof without contacting the board beneath.
    for x in (-11.75, 11.75):
        cuts.append(box((12.5, 33, LID_ROOF + 1), (x, -9.5, LID_ROOF / 2)))
        cuts.append(box((12.5, 17, LID_ROOF + 1), (x, 17.5, LID_ROOF / 2)))
    # Full-height, open-front USB / BOOTSEL access; RF window at the rear.
    cuts.append(box((25, 29, LID_ROOF + 1), (0, -24.5, LID_ROOF / 2)))
    cuts.append(box((15, 16, LID_ROOF + 1), (0, 18, LID_ROOF / 2)))
    # Four M2 slots mount a common 0.96-inch SSD1306 on the exterior. The
    # breakout's four-pin header sits between the lower pair of OLED bolt holes,
    # so the wire opening is directly beneath that header and wholly between
    # those two M2 slots.
    for x_sign in (-1, 1):
        for y_sign in (-1, 1):
            x = OLED_CENTRE[0] + x_sign * OLED_HOLE_HALF_SPACING
            y = OLED_CENTRE[1] + y_sign * OLED_HOLE_HALF_SPACING
            cuts.append(horizontal_slot(4.5, 2.5, LID_ROOF + 3,
                                        (x, y, (LID_ROOF + 2) / 2)))
    cuts.append(box((14, 6, LID_ROOF + 3),
                    (OLED_CENTRE[0], OLED_CENTRE[1] + OLED_HOLE_HALF_SPACING,
                     (LID_ROOF + 2) / 2)))
    lid = trimesh.boolean.difference([lid, *cuts], engine='manifold')
    if not lid.is_watertight or lid.body_count != 1:
        raise RuntimeError('Generated lid is not one watertight solid')
    return lid


if __name__ == '__main__':
    for destination, mesh in ((BASE_OUT, build_base()), (LID_OUT, build_lid())):
        mesh.export(destination)
        print('Saved:', destination)
        print('Bounds (mm):', mesh.bounds.tolist())
        print('Volume (mm^3):', round(mesh.volume, 1))
