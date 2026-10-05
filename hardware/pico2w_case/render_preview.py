"""Draw dimensioned base, lid and assembled side views of the case."""

from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle
import trimesh

HERE = Path(__file__).resolve().parent
for file in ('pico2w_open_case.stl', 'pico2w_lid.stl'):
    mesh = trimesh.load(HERE / file, force='mesh')
    assert mesh.is_watertight and mesh.body_count == 1

fig = plt.figure(figsize=(14, 12))
fig.patch.set_facecolor('#f4f7f3')
grid = fig.add_gridspec(2, 2, height_ratios=[1.4, .65])
base, lid = fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])
side = fig.add_subplot(grid[1, :])
for ax in (base, lid, side):
    ax.set_facecolor('#fff')

base.set_title('Base · four external holes surround the Pico')
base.add_patch(Rectangle((-31, -64), 49, 103, facecolor='#28765a'))
base.add_patch(Rectangle((18, -39), 37, 78, facecolor='#28765a'))
base.add_patch(Rectangle((-7.5, 7), 15, 11, facecolor='#fff'))
base.add_patch(Rectangle((-10.5, -25.5), 21, 51, fill=False,
                         edgecolor='#f5a623', linewidth=2, linestyle='--'))
for x in (-5.7, 5.7):
    for y in (-23.5, 23.5):
        base.add_patch(Circle((x, y), 2.5, facecolor='#12513c'))
        base.add_patch(Circle((x, y), 1.1, facecolor='#fff'))
base.text(0, -45, 'OPEN USB\nCABLE AREA', ha='center', va='center', fontsize=9)
base.text(0, 12.5, 'ANTENNA\nWINDOW', ha='center', va='center', fontsize=7)
base.text(33, 0, 'EXTRA-WIDE\nSIDE', ha='center', va='center',
          fontsize=9, color='white')

lid.set_title('Separate lid · printed roof down, posts up')
lid.add_patch(Rectangle((-31, -39), 86, 78, facecolor='#326d58'))
# Full perimeter walls, with a very large 50 mm USB opening at the front.
lid.plot([-31, -31], [-39, 39], color='#102f24', linewidth=5)
lid.plot([55, 55], [-39, 39], color='#102f24', linewidth=5)
lid.plot([-31, 55], [39, 39], color='#102f24', linewidth=5)
lid.plot([-31, -13], [-39, -39], color='#102f24', linewidth=5)
lid.plot([37, 55], [-39, -39], color='#102f24', linewidth=5)
for x in (-11.75, 11.75):
    for centre, length in ((-9.5, 33), (17.5, 17)):
        lid.add_patch(Rectangle((x - 6.25, centre - length / 2), 12.5,
                                length, facecolor='#fff'))
lid.add_patch(Rectangle((-12.5, -39), 25, 29, facecolor='#fff'))
lid.add_patch(Rectangle((-7.5, 10), 15, 16, facecolor='#fff'))
lid.text(12, -34, '50 mm USB + CABLE OPENING', ha='center', va='center', fontsize=7)
lid.text(0, 18, 'ANTENNA', ha='center', va='center', fontsize=7)
lid.text(0, -2, 'CHIP COVER', ha='center', va='center', fontsize=7)
# Integrated OLED mount on the wide side. Dashed outline is the breakout PCB.
lid.add_patch(Rectangle((20.35, -21.9), 27.3, 27.8, fill=False,
                        edgecolor='#f5a623', linewidth=2, linestyle='--'))
for x in (34 - 11.85, 34 + 11.85):
    for y in (-8 - 11.85, -8 + 11.85):
        lid.add_patch(FancyBboxPatch((x - 2.25, y - 1.25), 4.5, 2.5,
                                    boxstyle='round,pad=0,rounding_size=1.25',
                                    facecolor='#fff'))
lid.add_patch(Rectangle((27, .85), 14, 6, facecolor='#fff'))
lid.text(34, -8, 'SSD1306', ha='center', va='center', fontsize=8)
lid.text(34, 3.85, 'HEADER / WIRE', ha='center', va='center', fontsize=4.5)

for ax, show_posts in ((base, False), (lid, True)):
    for x in (-24, 45):
        for y in (-30, 30):
            if show_posts:
                ax.add_patch(Circle((x, y), 5.2, facecolor='#174936'))
            ax.add_patch(Circle((x, y), 1.7, facecolor='#fff'))
    ax.set_xlim(-36, 60)
    ax.set_ylim(44, -69)
    ax.set_aspect('equal')
    ax.set_xlabel('mm')
    ax.set_ylabel('mm')
    ax.grid(alpha=.12)

side.set_title('Assembled side profile · USB end open')
side.add_patch(Rectangle((-64, 0), 103, 4.5, facecolor='#28765a'))
for y in (-23.5, 23.5):
    side.add_patch(Rectangle((y - 2.5, 4.5), 5, 8,
                             facecolor='#12513c'))
side.add_patch(Rectangle((-25.5, 12.5), 51, 1, facecolor='#f5a623'))
for y in (-30, 30):
    side.add_patch(Rectangle((y - 5.2, 4.5), 10.4, 12.25,
                             facecolor='#174936', alpha=.6))
side.add_patch(Rectangle((-39, 16.75), 78, 2.4,
                         facecolor='#326d58', alpha=.75))
side.text(0, 14.5, '3.25 mm above PCB', ha='center', fontsize=9)
side.text(0, 7, '8 mm below PCB', ha='center', fontsize=9)
side.annotate('USB cable exits here', xy=(-32, 15), xytext=(-60, 25),
              arrowprops={'arrowstyle': '->'}, fontsize=9)
side.set_xlim(-69, 44)
side.set_ylim(-1, 22)
side.set_aspect(1.4)
side.set_xlabel('length along board (mm)')
side.set_ylabel('height (mm)')
side.grid(alpha=.12)

fig.tight_layout()
fig.savefig(HERE / 'pico2w_case_with_oled_preview.png', dpi=150)
