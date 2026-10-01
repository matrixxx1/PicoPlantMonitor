"""Draw dimensioned top and side views for the Pico 2 W case STL."""

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
import trimesh

HERE = Path(__file__).resolve().parent
mesh = trimesh.load(HERE / 'pico2w_open_case.stl', force='mesh')
assert mesh.is_watertight and mesh.body_count == 1

fig, (top, side) = plt.subplots(1, 2, figsize=(13, 8),
                                gridspec_kw={'width_ratios': [1, 1.1]})
fig.patch.set_facecolor('#f4f7f3')
for ax in (top, side):
    ax.set_facecolor('#fff')

top.set_title('Top view · orange dashed Pico 2 W outline')
top.add_patch(Rectangle((-18, -60), 36, 94, facecolor='#28765a'))
top.add_patch(Rectangle((18, -31), 37, 62, facecolor='#28765a'))
top.add_patch(Rectangle((-7.5, 7), 15, 11, facecolor='#fff'))
top.add_patch(Rectangle((-10.5, -25.5), 21, 51, fill=False,
                        edgecolor='#f5a623', linewidth=2, linestyle='--'))
for x in (-5.7, 5.7):
    for y in (-23.5, 23.5):
        top.add_patch(Circle((x, y), 2.5, facecolor='#12513c'))
        top.add_patch(Circle((x, y), 1.1, facecolor='#fff'))
for x in (28, 45):
    for y in (-22, 22):
        top.add_patch(Circle((x, y), 1.7, facecolor='#fff'))
top.text(0, -43, 'OPEN USB\nCABLE AREA', ha='center', va='center', fontsize=10)
top.text(36.5, 0, 'WIDE\nMOUNTING\nFLANGE', ha='center', va='center',
         fontsize=10, color='white')
top.text(0, 12.5, 'ANTENNA\nWINDOW', ha='center', va='center', fontsize=7)
top.set_xlim(-23, 60)
top.set_ylim(39, -65)
top.set_aspect('equal')
top.set_xlabel('mm')
top.set_ylabel('mm')
top.grid(alpha=.12)

side.set_title('Side profile · 8 mm clearance below board')
side.add_patch(Rectangle((-60, 0), 94, 4.5, facecolor='#28765a'))
for y in (-23.5, 23.5):
    side.add_patch(Rectangle((y - 2.5, 4.5), 5, 8, facecolor='#12513c'))
side.add_patch(Rectangle((-25.5, 12.5), 51, 1, facecolor='#f5a623'))
side.text(0, 14.5, 'Pico 2 W PCB', ha='center', fontsize=10)
side.annotate('Micro USB and plug\nopen on this end', xy=(-31, 13.5),
              xytext=(-53, 18), arrowprops={'arrowstyle': '->'}, fontsize=9)
side.text(0, 5.5, '8 mm pin-tail clearance', ha='center', fontsize=9)
side.set_xlim(-65, 39)
side.set_ylim(-1, 22)
side.set_aspect(3)
side.set_xlabel('length along board (mm)')
side.set_ylabel('height (mm)')
side.grid(alpha=.12)

fig.tight_layout()
fig.savefig(HERE / 'pico2w_open_case_preview.png', dpi=160)
