# Pico 2 W two-piece case

[Base STL](pico2w_open_case.stl) · [SSD1306-ready lid STL](pico2w_lid.stl) · [Dimensioned preview](pico2w_case_with_oled_preview.png)

This ventilated case holds a **Raspberry Pi Pico 2 W** on four raised standoffs. Four external mounting holes surround the entire Pico: two left of the board and two on the extra-wide right side. The lid is a separate print with four matching corner posts and full-height outer perimeter walls. Openings give access to both pin rows, USB, BOOTSEL, and the antenna area. A deliberately oversized 50 mm opening in the USB-end wall leaves room to connect and handle bulky cables.

## Dimensions and fasteners

All dimensions are in millimetres. The coordinate origin is the PCB centre, with USB at negative Y.

| Feature | Dimension |
| --- | --- |
| Base bounds | 86 × 103 × 12.5 |
| Lid print bounds | 86 × 78 × 14.65, printed roof down |
| Assembled maximum height | 19.15 above base bottom |
| Pico PCB reference | 21 × 51 × 1 |
| Pico hole centres | X = ±5.7, Y = ±23.5 |
| Pico standoff holes | 2.2 diameter, through; underside M2 nut recesses |
| Pico underside clearance | 8 above the 4.5 thick base |
| Four shared external holes | 3.4 diameter for M3; X = −24 or 45, Y = −30 or 30 |
| USB handling area | 38.5 beyond the PCB edge, open at the end |
| Clearance above PCB | 3.25 to underside of lid roof |
| Lid perimeter wall | 2.4 thick × 12.25 tall |
| USB-end wall opening | 50 wide |

Print the base flat with standoffs up. Print the separate lid with its roof on the bed and posts up. Both pieces are designed to print without supports. Fasten the Pico to its four base standoffs using M2 screws and nuts; M2 × 12 mm is a starting length. The underside nut pockets are about 4.42 mm across flats and 2.1 mm deep. Then flip the lid onto the base so its posts meet the four external holes. Four M3 bolts with nuts can hold the lid and base together and also attach the case to a mounting surface. Choose bolt length for the mounting surface, washers, and nut; approximately M3 × 22 mm is a starting point for the shortened case alone. Check fit before tightening, and avoid overtightening printed parts.

The Pico 2 W has a physical **BOOTSEL** button near USB; it does not have an onboard reset button. The RUN header pin can be used with an external momentary switch to ground for hardware reset. The lid hatch leaves the USB and BOOTSEL area open; pin slots leave the RUN pin reachable. The base and lid have openings near the Pico wireless antenna. Keep added hardware and metal clear of that area.

This design has been checked digitally, but has not yet been physically test printed or fitted to a board. Verify printer tolerances, USB plug size, header solder tails, attached wiring, and your chosen fasteners on a test print.

## Integrated SSD1306 lid mounting

The lid's wide side now includes four reinforced 4.5 × 2.5 mm horizontal M2 slots centred on a 23.7 × 23.7 mm pattern. They accommodate common 0.96-inch SSD1306 boards with approximately 23–24 mm hole spacing. Mount the OLED above the outside face of the lid using four M2 screws, washers, nuts, and 3–5 mm spacers so its rear solder joints cannot touch the plastic.

A 14 × 6 mm pass-through sits directly beneath the OLED's four-pin header, completely between the corresponding pair of M2 display-mounting slots. Orient the OLED so its header aligns with this opening, then route the red, black, blue, and yellow jumper wires through the back of the lid to the Pico. Add a small grommet or protect the wire bundle with heat-shrink if the printed slot edge is rough.

The assumed breakout PCB envelope is approximately 27.3 × 27.8 mm. Generic SSD1306 boards vary, so measure the actual PCB and hole centres before printing or first print only the roof layers as a fit gauge. Do not overtighten the OLED PCB.

## Source and regeneration

The case source is [`generate_case.py`](generate_case.py). It uses `trimesh` and `manifold3d` to generate watertight STL files. Run `py generate_case.py` from this directory after installing those packages. Regenerate the preview with `py render_preview.py` using `matplotlib`.

Board dimensions and the four 2.1 mm PCB mounting holes come from [Figure 3 in Raspberry Pi's Pico 2 W datasheet](https://datasheets.raspberrypi.com/picow/pico-2-w-datasheet.pdf). The datasheet also calls for keeping the antenna space free of nearby material. External hole positions, fastener clearances, lid, and USB apron are design choices for this case.
