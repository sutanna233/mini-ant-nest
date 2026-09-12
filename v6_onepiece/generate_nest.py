# -*- coding: utf-8 -*-
"""
Mini one-piece soil formicarium  v6  (单件一体成型)
一体式蚁巢: 一次打印成型, 免支撑.
  - 后部圆筒: 干燥活动区 (arena)
  - 前部敞开: 保湿土槽 (soil)
  - 底层水仓 + 前壁加水孔 (加水口)
  - 圆筒前壁一个门洞把活动区与土槽连通
  - 水仓顶(土槽底板)开 Ø2 网格孔供水汽上行, 圆筒下方不开孔保持干燥
  - 水仓内 9 根 Ø3 短柱把 50mm 桥接分成小格, 可免支撑打印

尺寸: 56 x 56 x 50 mm
依赖: shapely, trimesh, manifold3d, numpy, matplotlib
"""
import os
import numpy as np
from shapely.geometry import box, Point
from shapely.ops import unary_union
import trimesh
import trimesh.transformations as tf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "design")
PRE = os.path.join(HERE, "preview")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PRE, exist_ok=True)

# ---------------------------------------------------------------- parameters
S = 56.0              # square footprint
R = 4.0               # outer corner radius
T = 3.0               # wall thickness
BODY_H = 36.0         # solid base block height

TANK_FLOOR = 3.0      # water tank floor
PLATE_Z0, PLATE_T = 16.0, 4.0          # soil plate 16..20 (grill holes here)
SOIL_Z0, SOIL_TOP = 20.0, 36.0         # open soil pocket

FILL_R, FILL_Z = 3.5, 12.0             # Ø7 fill hole on the front wall; water max z=8.5
POSTS = [(x, y) for x in (13.0, 28.0, 43.0) for y in (13.0, 28.0, 43.0)]
POST_R = 1.5

CYL = (28.0, 31.0)                     # cylinder centre (back)
CYL_OD, CYL_WALL = 40.0, 2.5
CYL_TOP = 50.0
GRILL_R, GRILL_PITCH = 1.0, 5.0
DOOR = (20.0, 36.0, 8.0, 18.0, 20.0, 29.0)   # x0,x1, y0,y1, z0,z1


# ---------------------------------------------------------------- helpers
def rounded_rect(x0, y0, x1, y1, r):
    if r <= 0:
        return box(x0, y0, x1, y1)
    rects = [box(x0 + r, y0, x1 - r, y1), box(x0, y0 + r, x1, y1 - r)]
    circles = [Point(x, y).buffer(r, resolution=48)
               for x, y in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                            (x0 + r, y1 - r), (x1 - r, y1 - r))]
    return unary_union(rects + circles)


def circle(c, r, res=64):
    return Point(*c).buffer(r, resolution=res)


def annulus(c, ro, ri, res=64):
    return circle(c, ro, res).difference(circle(c, ri, res))


def extrude(poly, z0, height):
    m = trimesh.creation.extrude_polygon(poly, height=height)
    m.apply_translation([0.0, 0.0, z0])
    return m


def box3(x0, y0, z0, x1, y1, z1):
    m = trimesh.creation.box(extents=(x1 - x0, y1 - y0, z1 - z0))
    m.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return m


def cyl(r, c, z0, z1, sections=64):
    m = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=sections)
    m.apply_translation([c[0], c[1], (z0 + z1) / 2])
    return m


def ycyl(r, x, yc, z, length=12.0, sections=48):
    m = trimesh.creation.cylinder(radius=r, height=length, sections=sections)
    m.apply_transform(tf.rotation_matrix(np.pi / 2.0, [1, 0, 0]))
    m.apply_translation([x, yc, z])
    return m


# ---------------------------------------------------------------- build
def build():
    part = extrude(rounded_rect(0, 0, S, S, R), 0.0, BODY_H)
    # free-standing arena tube on the back (square base + round tube look)
    ring = extrude(annulus(CYL, CYL_OD / 2, CYL_OD / 2 - CYL_WALL),
                   SOIL_Z0, CYL_TOP - SOIL_Z0)
    part = trimesh.boolean.union([part, ring])

    cuts = []
    # water tank
    cuts.append(extrude(rounded_rect(T, T, S - T, S - T, 1.0),
                        TANK_FLOOR, PLATE_Z0 - TANK_FLOOR))
    # open soil pocket (everything except the tube footprint)
    soil_poly = rounded_rect(T, T, S - T, S - T, 1.0).difference(
        circle(CYL, CYL_OD / 2))
    cuts.append(extrude(soil_poly, SOIL_Z0, SOIL_TOP - SOIL_Z0))
    # arena interior (tube bore)
    cuts.append(cyl(CYL_OD / 2 - CYL_WALL, CYL, SOIL_Z0, CYL_TOP + 1.0))
    # door between arena and soil pocket
    cuts.append(box3(DOOR[0], DOOR[2], DOOR[4], DOOR[1], DOOR[3], DOOR[5]))
    # fill hole on the front wall
    cuts.append(ycyl(FILL_R, CYL[0], T / 2, FILL_Z))
    # soil plate grill holes (skip the area under the dry arena)
    holes = []
    for x in np.arange(T + GRILL_PITCH / 2, S - T, GRILL_PITCH):
        for y in np.arange(T + GRILL_PITCH / 2, S - T, GRILL_PITCH):
            if np.hypot(x - CYL[0], y - CYL[1]) < CYL_OD / 2 + 1.5:
                continue
            holes.append(circle((x, y), GRILL_R, 12))
    cuts.append(trimesh.util.concatenate(
        [extrude(p, PLATE_Z0 - 2.0, PLATE_T + 4.0) for p in holes]))
    part = trimesh.boolean.difference([part] + cuts)

    posts = [cyl(POST_R, p, TANK_FLOOR, PLATE_Z0) for p in POSTS]
    return trimesh.boolean.union([part] + posts)


# ---------------------------------------------------------------- render
def render(ax, mesh, color="#c8a165"):
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from matplotlib.colors import to_rgb
    nrm = mesh.face_normals
    light = np.array([-0.35, -0.55, 0.75])
    light /= np.linalg.norm(light)
    inten = np.clip(nrm @ light, 0.25, 1.0)
    base = np.array(to_rgb(color))
    ax.add_collection3d(Poly3DCollection(mesh.triangles,
                                         facecolors=base[None, :] * inten[:, None],
                                         edgecolors="none"))


def make_previews(part):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(16, 5.4), dpi=140)
    views = [(26, -58, "isometric (back-tube + open soil)"),
             (66, -90, "top view"),
             (-22, -58, "underside (water tank)")]
    for i, (elev, azim, title) in enumerate(views):
        ax = fig.add_subplot(1, 3, i + 1, projection="3d")
        render(ax, part, "#c8a165")
        ax.set_xlim(-4, S + 4)
        ax.set_ylim(-4, S + 4)
        ax.set_zlim(-6, CYL_TOP + 4)
        ax.set_box_aspect((S, S, CYL_TOP + 10))
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()
        ax.set_title(title, fontsize=9)
    fig.suptitle("Mini Soil Nest v6  |  one-piece print")
    fig.tight_layout()
    fig.savefig(os.path.join(PRE, "preview.png"))
    plt.close(fig)


def make_schematic():
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "sans-serif"]
    matplotlib.rcParams["axes.unicode_minus"] = False
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    fig, ax = plt.subplots(figsize=(7.6, 7), dpi=140)
    GRAY, EDGE, SOIL, WATER = "#eef2f5", "#5b6b78", "#c8a165", "#9fd0f5"
    xs = 25.5                                    # section plane

    def cy_sp(ro):
        dx = xs - CYL[0]
        half = (ro * ro - dx * dx) ** 0.5
        return CYL[1] - half, CYL[1] + half

    yf0, yf1 = cy_sp(CYL_OD / 2)                 # outer
    yi0, yi1 = cy_sp(CYL_OD / 2 - CYL_WALL)      # bore

    ax.add_patch(Rectangle((0, 0), S, 36, fc=GRAY, ec=EDGE, lw=1.6))   # body
    ax.add_patch(Rectangle((3, 3), 50, 5.5, fc=WATER, ec="none"))      # water
    ax.add_patch(Rectangle((0, 8.5), 3, 7, fc="white", ec=EDGE, lw=0.9))  # fill hole
    ax.add_patch(Rectangle((3, 20), yf0 - 3, 16, fc=SOIL, ec="#8a6a3a", lw=1.0))
    ax.add_patch(Rectangle((yf1, 20), 53 - yf1, 16, fc=SOIL, ec="#8a6a3a", lw=1.0))
    for x in range(6, 51, 5):                                          # plate holes
        ax.plot([x, x], [16, 20], color="#1f6fb2", lw=1.1)
    ax.add_patch(Rectangle((yf0, 20), yi0 - yf0, 30, fc=GRAY, ec=EDGE, lw=1.3))
    ax.add_patch(Rectangle((yi1, 20), yf1 - yi1, 30, fc=GRAY, ec=EDGE, lw=1.3))
    ax.add_patch(Rectangle((yf0, 20), yi0 - yf0, 9, fc="white", ec=EDGE,
                           lw=0.9, ls="--"))                           # door
    ax.plot([yf0, yf1], [24, 24], color="#c0392b", lw=1.0, ls=":")     # water vapour

    ax.annotate("", xy=(-8, 0), xytext=(-8, 50),
                arrowprops=dict(arrowstyle="<->", color="#444"))
    ax.text(-10, 25, "50 mm", rotation=90, va="center", ha="right", fontsize=9)
    ax.annotate("", xy=(0, -4), xytext=(56, -4),
                arrowprops=dict(arrowstyle="<->", color="#444"))
    ax.text(28, -6, "56 mm", ha="center", va="top", fontsize=9)

    def tag(txt, xy, xytext, color):
        ax.annotate(txt, xy=xy, xytext=xytext, fontsize=12, color=color,
                    ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", color=color, lw=1.5))
    tag("干燥区 · 圆筒活动区", (CYL[1], 42), (60, 45), "#2f7d4f")
    tag("保湿区 · 敞开土槽", (6, 30), (60, 33), "#8a6a3a")
    tag("连通门洞", (yf0 + 1, 25), (60, 24), "#666666")
    tag("加水口", (0, 12), (60, 12), "#1f6fb2")
    tag("水仓 (水汽上行)", (28, 6), (60, 5), "#1f6fb2")
    ax.set_xlim(-14, 122)
    ax.set_ylim(-12, 54)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Mini Soil Nest v6  |  one-piece section", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(PRE, "schematic.png"))
    plt.close(fig)


# ---------------------------------------------------------------- main
def main():
    part = build()
    p = os.path.join(OUT, "nest_onepiece.stl")
    part.export(p, file_type="stl")
    print(f"[ok] {p}")
    print(f"     tris={len(part.faces)} watertight={part.is_watertight} "
          f"volume={part.volume/1000:.2f}cm3 bounds={np.round(part.bounds,1).tolist()}")
    make_previews(part)
    make_schematic()
    print("[ok] preview/preview.png  preview/schematic.png")


if __name__ == "__main__":
    main()
