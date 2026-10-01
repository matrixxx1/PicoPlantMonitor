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
LID_POST = 24.5  # lid underside is 29 mm above the bottom of the assembled base
BOARD_HOLES_X = (-5.7, 5.7)       # 11.4 mm between columns
BOARD_HOLES_Y = (-23.5, 23.5)     # 2 mm from each end of 51 mm PCB
EXTERNAL_HOLES = ((-24, -30), (45, -30), (-24, 30), (45, 30))


def box(size, centre):
    mesh = trimesh.creation.box(extents=size)
    mesh.apply_translation(centre)
    return mesh


def cylinder(radius, height, centre, sections=64):
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    mesh.apply_translation(centre)
    return mesh


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
    # After flipping onto the base, the roof underside is 29 mm above its
    # bottom, leaving 15.5 mm over the Pico PCB top and open pin rows.
    solids = [box((86, 78, LID_ROOF), (12, 0, LID_ROOF / 2))]
    for x, y in EXTERNAL_HOLES:
        solids.append(cylinder(5.2, LID_POST,
                               (x, y, LID_ROOF + LID_POST / 2)))
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
