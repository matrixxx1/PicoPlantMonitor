"""Generate an open Pico 2 W mounting cradle (millimetres).

Requires trimesh and manifold3d: py -m pip install trimesh manifold3d
The board outline and hole centres follow Figure 3 of the official
Pico 2 W datasheet. Inspect a printed test fit before final installation.
"""

from pathlib import Path

import trimesh


OUT = Path(__file__).resolve().parent / 'pico2w_open_case.stl'
FLOOR = 4.5
STANDOFF_TOP = 12.5  # 8 mm gap above the floor for soldered header tails
BOARD_HOLES_X = (-5.7, 5.7)       # 11.4 mm between columns
BOARD_HOLES_Y = (-23.5, 23.5)     # 2 mm from each end of 51 mm PCB
FLANGE_HOLES = ((28, -22), (45, -22), (28, 22), (45, 22))


def box(size, centre):
    mesh = trimesh.creation.box(extents=size)
    mesh.apply_translation(centre)
    return mesh


def cylinder(radius, height, centre, sections=64):
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    mesh.apply_translation(centre)
    return mesh


def build():
    # The 34.5 mm open apron in front of the PCB leaves room for a USB plug
    # and strain relief. The right-hand wing is entirely beyond the board.
    main = box((36, 94, FLOOR), (0, -13, FLOOR / 2))  # x -18..18, y -60..34
    wing = box((37, 62, FLOOR), (36.5, 0, FLOOR / 2))  # x 18..55
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

    # Four M3 clearance holes on the broad flange, all outside the PCB outline.
    for x, y in FLANGE_HOLES:
        cuts.append(cylinder(1.7, FLOOR + 1, (x, y, FLOOR / 2)))

    # Window below the wireless antenna; no cover or lip surrounds it.
    cuts.append(box((15, 11, FLOOR + 1), (0, 12.5, FLOOR / 2)))
    cradle = trimesh.boolean.difference([cradle, *cuts], engine='manifold')
    if not cradle.is_watertight or cradle.body_count != 1:
        raise RuntimeError('Generated case is not one watertight solid')
    return cradle


if __name__ == '__main__':
    mesh = build()
    mesh.export(OUT)
    print('Saved:', OUT)
    print('Bounds (mm):', mesh.bounds.tolist())
    print('Volume (mm^3):', round(mesh.volume, 1))
