# Pico 2 W open case

[Download the STL](pico2w_open_case.stl) · [Preview](pico2w_open_case_preview.png)

This single-piece open cradle holds a **Raspberry Pi Pico 2 W** above a base while leaving its pin rows, on-board BOOTSEL button, and RUN reset pin accessible. The USB end has no wall or roof; the base extends 34.5 mm beyond the PCB edge so a USB plug and cable can be attached with room to handle them. One side has a broad flange with four mounting holes outside the Pico footprint. A 15 × 11 mm opening in the base sits below the wireless antenna.

## Dimensions and fasteners

All dimensions are in millimetres. Coordinate origin is the PCB centre, USB at negative Y.

| Feature | Dimension |
| --- | --- |
| Overall STL bounds | 73 × 94 × 12.5 |
| Pico PCB reference | 21 × 51 × 1 |
| Pico hole centres | X = ±5.7, Y = ±23.5 |
| Pico boss holes | 2.2 diameter, through; four underside M2 nut recesses |
| Pico underside clearance | 8 above the 4.5 thick base |
| External flange holes | 3.4 diameter for M3, at (28, −22), (45, −22), (28, 22), (45, 22) |
| USB handling area | 34.5 beyond the PCB edge, open at the end |

Use four M2 screws and nuts to attach the Pico, plus up to four M3 screws for the external flange. M2 × 12 mm is a starting screw length; check the head, washers, nut thickness, and your printed fit. The underside nut pockets are about 4.42 mm across flats and 2.1 mm deep. Avoid overtightening the printed standoffs. Print flat on the base, open side up, without supports. A test fit is recommended because printer tolerances and header solder tails vary.

The Pico 2 W has a physical **BOOTSEL** button near USB; it does not have an onboard reset button. The RUN header pin can be used with an external momentary switch to ground for hardware reset. This open design leaves both areas accessible.

## Source and regeneration

The source is [`generate_case.py`](generate_case.py). It uses `trimesh` and `manifold3d` to generate a watertight STL. Run `py generate_case.py` from this directory after installing those packages. The preview can be regenerated with `py render_preview.py` using `matplotlib`.

Board dimensions and the four 2.1 mm PCB mounting holes come from [Figure 3 in Raspberry Pi's Pico 2 W datasheet](https://datasheets.raspberrypi.com/picow/pico-2-w-datasheet.pdf). The datasheet also calls for keeping the antenna space free of nearby material. External flange dimensions, fastener clearances, and USB apron are design choices for this case.
