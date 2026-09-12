# -*- coding: utf-8 -*-
"""
3D printed plastic nest with plaster, split dry / wet, plus an outworld.  v8

一个塑料盒体, 一次打印:
  - 左侧  : 活动区 (outworld), 铺沙
  - 右上  : 干燥区 石膏 (不加水)
  - 右下  : 湿润区 石膏 (直接浇水)
  - 干湿之间一道塑料隔墙挡水; 活动区各开一个门洞分别通干区/湿区
石膏由用户自己倒 (铺到与活动区沙面同高), 蚂蚁在石膏里挖巢.
保湿 = 直接往湿润区石膏上浇水, 石膏吸水缓释.

尺寸: 100 x 55 x 30 mm   (免支撑)
依赖: shapely, trimesh, manifold3d, numpy, matplotlib
"""
import os
import numpy as np
from shapely.geometry import box, Point
from shapely.ops import unary_union
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "design")
PRE = os.path.join(HERE, "preview")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PRE, exist_ok=True)

# ---------------------------------------------------------------- parameters
SX, SY, H = 100.0, 55.0, 30.0
R = 5.0
T = 3.0
BASE = 3.0                 # floor thickness

PZ = 18.0                  # plaster / sand surface height
DOOR_H = 8.0               # doorway height above the plaster surface

OW = (3.0, 3.0, 35.0, 52.0)          # outworld cavity (x0,y0,x1,y1)
NEST = (38.0, 3.0, 97.0, 52.0)       # plaster region
DIV_Y = (28.0, 31.0)                 # dry/wet divider band
DOOR_DRY = (38.0, 48.0)              # doorway to the DRY half  (y0,y1)
DOOR_WET = (8.0, 18.0)               # doorway to the WET half  (y0,y1)

LID_T = 2.0


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


# ---------------------------------------------------------------- build body
def build_body():
    body = extrude(rounded_rect(0, 0, SX, SY, R), 0.0, H)
    cuts = [
        extrude(rounded_rect(OW[0], OW[1], OW[2], OW[3], 3.0), BASE, H),
        extrude(rounded_rect(NEST[0], DIV_Y[1], NEST[2], NEST[3], 3.0),
                BASE, H),                                   # dry plaster
        extrude(rounded_rect(NEST[0], NEST[1], NEST[2], DIV_Y[0], 3.0),
                BASE, H),                                   # wet plaster
        box3(OW[2] - 1.0, DOOR_DRY[0], PZ, NEST[0] + 1.0, DOOR_DRY[1],
             PZ + DOOR_H),                                  # doorway -> dry
        box3(OW[2] - 1.0, DOOR_WET[0], PZ, NEST[0] + 1.0, DOOR_WET[1],
             PZ + DOOR_H),                                  # doorway -> wet
    ]
    return trimesh.boolean.difference([body] + cuts)


# ---------------------------------------------------------------- build lid
def build_lid():
    lid = extrude(rounded_rect(0, 0, SX, SY, R), 0.0, LID_T)
    cuts = []
    xs = np.arange(OW[0] + 4, OW[2] - 3, 5.0)
    ys = np.arange(OW[1] + 4, OW[3] - 3, 5.0)
    for x in xs:
        for y in ys:
            cuts.append(extrude(circle((x, y), 0.9, 24), -1, LID_T + 2))
    for y in (12.0, 20.0, 40.0, 47.0):                       # a few over the nest
        cuts.append(extrude(circle((90.0, y), 0.8, 24), -1, LID_T + 2))
    return trimesh.boolean.difference([lid] + cuts)


# ---------------------------------------------------------------- render
def render(ax, mesh, color):
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


def make_previews(body, lid):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    lid_up = lid.copy()
    lid_up.apply_translation([0, 0, H])
    fig = plt.figure(figsize=(16, 5.4), dpi=140)
    panels = [
        ("assembled (body + lid)", [(body, "#c8a165"), (lid_up, "#9fb8c9")],
         (30, -60), H + LID_T + 4),
        ("top: outworld | dry | wet", [(body, "#c8a165")], (78, -90), H),
        ("body isometric", [(body, "#c8a165")], (26, -60), H),
    ]
    for i, (title, layers, (elev, azim), ztop) in enumerate(panels):
        ax = fig.add_subplot(1, 3, i + 1, projection="3d")
        for mesh, col in layers:
            render(ax, mesh, col)
        ax.set_xlim(0, SX)
        ax.set_ylim(0, SY)
        ax.set_zlim(0, ztop)
        ax.set_box_aspect((SX, SY, ztop))
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()
        ax.set_title(title, fontsize=9)
    fig.suptitle("Plastic plaster nest v8  |  outworld + dry/wet plaster")
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

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2), dpi=140)

    # --- top view ---
    ax = axes[0]
    GRAY, EDGE, SOIL, WET = "#eef2f5", "#5b6b78", "#e9d3ac", "#a9cfe8"
    ax.add_patch(Rectangle((0, 0), SX, SY, fc=GRAY, ec=EDGE, lw=1.6))
    ax.add_patch(Rectangle((OW[0], OW[1]), OW[2] - OW[0], OW[3] - OW[1],
                           fc=SOIL, ec=EDGE, lw=1.2))
    ax.add_patch(Rectangle((NEST[0], DIV_Y[1]), NEST[2] - NEST[0],
                           NEST[3] - DIV_Y[1], fc="#f4e3c4", ec=EDGE, lw=1.2))
    ax.add_patch(Rectangle((NEST[0], NEST[1]), NEST[2] - NEST[0],
                           DIV_Y[0] - NEST[1], fc=WET, ec=EDGE, lw=1.2))
    ax.add_patch(Rectangle((OW[2], DOOR_DRY[0]), NEST[0] - OW[2],
                           DOOR_DRY[1] - DOOR_DRY[0], fc="white", ec="#c0392b",
                           lw=1.0, ls="--"))
    ax.add_patch(Rectangle((OW[2], DOOR_WET[0]), NEST[0] - OW[2],
                           DOOR_WET[1] - DOOR_WET[0], fc="white", ec="#c0392b",
                           lw=1.0, ls="--"))
    ax.text(19, 28, "活动区\n(铺沙)", ha="center", va="center", fontsize=10,
            color="#8a6a3a")
    ax.text(68, 41, "干燥区 · 石膏", ha="center", va="center", fontsize=10,
            color="#8a6a3a")
    ax.text(68, 15, "湿润区 · 石膏 (浇水)", ha="center", va="center", fontsize=10,
            color="#1f6fb2")
    ax.annotate("门洞", xy=(36.5, 43), xytext=(36.5, 52.5), fontsize=8,
                color="#c0392b", ha="center",
                arrowprops=dict(arrowstyle="->", color="#c0392b"))
    ax.annotate("门洞", xy=(36.5, 13), xytext=(36.5, 1.5), fontsize=8,
                color="#c0392b", ha="center",
                arrowprops=dict(arrowstyle="->", color="#c0392b"))
    ax.set_xlim(-4, SX + 4)
    ax.set_ylim(-6, SY + 6)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("top view", fontsize=10)

    # --- section through the plaster nest (dry | wet) ---
    ax = axes[1]
    ax.add_patch(Rectangle((0, 0), SY, H, fc=GRAY, ec=EDGE, lw=1.6))
    ax.add_patch(Rectangle((NEST[1], BASE), DIV_Y[0] - NEST[1], PZ - BASE,
                           fc=WET, ec=EDGE, lw=0.6))
    ax.add_patch(Rectangle((DIV_Y[1], BASE), NEST[3] - DIV_Y[1], PZ - BASE,
                           fc="#f4e3c4", ec=EDGE, lw=0.6))
    ax.annotate("", xy=(DIV_Y[0] + 1.5, PZ), xytext=(DIV_Y[0] + 1.5, H),
                arrowprops=dict(arrowstyle="<->", color="#c0392b"))
    ax.text(DIV_Y[0] + 3, PZ + 2.5, "挡水墙高过石膏面", fontsize=8,
            color="#c0392b", va="bottom")
    ax.text(15, 26, "湿润区 石膏 (浇水)", ha="center", fontsize=9, color="#1f6fb2")
    ax.text(42, 26, "干燥区 石膏", ha="center", fontsize=9, color="#8a6a3a")
    ax.annotate("塑料盒体 / 外壁", xy=(0.5, 25), xytext=(7, 4), fontsize=8,
                color="#5b6b78", arrowprops=dict(arrowstyle="->", color="#5b6b78"))
    ax.set_xlim(-4, SY + 4)
    ax.set_ylim(-6, H + 10)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("section through the plaster nest", fontsize=10)

    fig.suptitle("Plastic plaster nest v8", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(PRE, "schematic.png"))
    plt.close(fig)


# ---------------------------------------------------------------- main
def main():
    body = build_body()
    lid = build_lid()
    for name, m in (("nest_body", body), ("nest_lid", lid)):
        p = os.path.join(OUT, name + ".stl")
        m.export(p, file_type="stl")
        print(f"[ok] {name:10s} tris={len(m.faces)} watertight={m.is_watertight} "
              f"vol={m.volume/1000:.1f}cm3 bounds={np.round(m.bounds,1).tolist()}")
    make_previews(body, lid)
    make_schematic()
    print("[ok] preview/preview.png  preview/schematic.png")


if __name__ == "__main__":
    main()
