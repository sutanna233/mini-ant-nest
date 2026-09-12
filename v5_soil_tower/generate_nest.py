# -*- coding: utf-8 -*-
"""
Mini stacked soil formicarium  v5
迷你垂直分层土巢: 干燥区(活动区) / 保湿区(土槽) / 加水口(推拉盖)

零件 (全部免支撑平放打印):
  1) water_tank   底座水仓 + 正面推拉式加水口 (+ 导轨)
  2) slider       加水口滑盖
  3) nest_tray    保湿区: 土槽 + 多孔底板(水汽上行) + 顶部台阶承托活动区
  4) arena        干燥区: 方形底座 + 圆形围栏 + 中央下落通道(带围堰)
  5) arena_lid    圆形顶盖: 透气孔 + 定位凸环

装配: tank 0-14 / nest 14-34 / arena 34-74 / lid 74-77  (总高 77mm, 56x56mm)

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
S = 56.0            # square footprint
R = 4.0             # outer corner radius
T = 3.0             # wall thickness

# --- water tank (加水口) ---
TANK_H = 18.0
TANK_FLOOR = 3.0
MOUTH_X0, MOUTH_X1 = 16.0, 40.0      # fill mouth (width 24)
MOUTH_Z0, MOUTH_Z1 = 8.0, 16.0       # mouth bottom = max water level
RAIL_Z = ((7.0, 8.3), (16.7, 18.0))  # slider rails (lower/upper)
RAIL_X0, RAIL_X1 = 12.0, 44.0
RAIL_OUT = 3.0                       # rails stick out this far (-y)

# --- slider (滑盖) ---
SLD_W, SLD_T, SLD_H = 22.0, 2.5, 8.0
SLD_GAP = 0.4

# --- nest tray (保湿区) ---
NEST_H = 20.0
SOIL_DEPTH = 16.0                    # soil pocket depth
SOIL_FLOOR = NEST_H - SOIL_DEPTH     # 4
STAIR = [(4.0, 12.0, 50.0), (12.0, 16.0, 42.0), (16.0, 20.0, 34.0)]
#        (z_lo, z_hi, opening)  inset stair -> 45deg printable ledge
GRILL_R = 1.0                        # floor hole Ø2
GRILL_PITCH = 5.0

# --- arena (干燥区) ---
ARENA_BASE_H = 10.0
CYL_OD, CYL_WALL = 40.0, 2.5
CYL_H = 30.0
TUNNEL_R = 7.0                       # Ø14 fall-through tunnel
DIKE_R0, DIKE_R1, DIKE_H = 7.0, 9.5, 1.5

# --- lid ---
LID_T = 3.0
LID_PLUG_D, LID_PLUG_H = 33.6, 2.0
VENT_CEN_R, VENT_CEN_RR = 1.5, 0.9
VENT_RING_R = 11.0


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


def cyl(r, cx, cy, z0, z1, sections=64):
    m = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=sections)
    m.apply_translation([cx, cy, (z0 + z1) / 2])
    return m


# ---------------------------------------------------------------- 1. tank
def build_tank():
    t = extrude(rounded_rect(0, 0, S, S, R), 0.0, TANK_H)
    cavity = extrude(rounded_rect(T, T, S - T, S - T, R - T),
                     TANK_FLOOR, TANK_H - TANK_FLOOR + 1.0)
    mouth = box3(MOUTH_X0, -1.0, MOUTH_Z0, MOUTH_X1, T + 1.0, MOUTH_Z1)
    t = trimesh.boolean.difference([t, cavity, mouth])
    rails = [box3(RAIL_X0, -RAIL_OUT, z0, RAIL_X1, 0.5, z1)
             for z0, z1 in RAIL_Z]
    return trimesh.boolean.union([t] + rails)


# ---------------------------------------------------------------- 2. slider
def build_slider():
    s = box3(0, 0, 0, SLD_W, SLD_T, SLD_H)
    # thumb tab on the outer face
    tab = box3(SLD_W - 7.0, -1.6, 1.5, SLD_W - 1.0, 0.0, SLD_H - 1.5)
    s = trimesh.boolean.union([s, tab])
    return s


# ---------------------------------------------------------------- 3. nest
def build_nest():
    n = extrude(rounded_rect(0, 0, S, S, R), 0.0, NEST_H)
    # 3 mm rim on the underside, seats into the tank cavity (keeps the middle open)
    lip_out = extrude(box(4.0, 4.0, S - 4.0, S - 4.0), -3.0, 4.0)
    lip_in = extrude(box(7.0, 7.0, S - 7.0, S - 7.0), -4.0, 6.0)
    lip = trimesh.boolean.difference([lip_out, lip_in])
    n = trimesh.boolean.union([n, lip])

    cuts = []
    for z0, z1, opening in STAIR:
        inset = (S - opening) / 2.0
        cuts.append(extrude(rounded_rect(inset, inset, S - inset, S - inset, 1.0),
                            z0, z1 - z0 + 0.01))
    # vapour holes run all the way through floor + underside lip
    cuts.append(trimesh.util.concatenate(
        [extrude(circle((x, y), GRILL_R, 12), -4.0, SOIL_FLOOR + 8.0)
         for x in np.arange(T + GRILL_PITCH / 2, S - T, GRILL_PITCH)
         for y in np.arange(T + GRILL_PITCH / 2, S - T, GRILL_PITCH)]))
    return trimesh.boolean.difference([n] + cuts)


# ---------------------------------------------------------------- 4. arena
def build_arena():
    cx = cy = S / 2.0
    base = extrude(rounded_rect(0, 0, S, S, R), 0.0, ARENA_BASE_H)
    wall = extrude(annulus((cx, cy), CYL_OD / 2, CYL_OD / 2 - CYL_WALL),
                   ARENA_BASE_H - 1.0, CYL_H + 1.0)
    a = trimesh.boolean.union([base, wall])
    tunnel = cyl(TUNNEL_R, cx, cy, -1.0, ARENA_BASE_H + 1.0)
    a = trimesh.boolean.difference([a, tunnel])
    dike = extrude(annulus((cx, cy), DIKE_R1, DIKE_R0),
                   ARENA_BASE_H - 0.5, DIKE_H + 0.5)
    return trimesh.boolean.union([a, dike])


# ---------------------------------------------------------------- 5. lid
def build_lid():
    cx = cy = S / 2.0
    lid = cyl(CYL_OD / 2, cx, cy, 0.0, LID_T, 64)
    plug = cyl(LID_PLUG_D / 2, cx, cy, -LID_PLUG_H, 0.5, 64)
    lid = trimesh.boolean.union([lid, plug])
    cuts = [cyl(VENT_CEN_RR, cx, cy, -LID_PLUG_H - 1, LID_T + 1, 32)]
    for i in range(8):
        ang = 2 * np.pi * i / 8
        cuts.append(cyl(VENT_CEN_RR, cx + VENT_RING_R * np.cos(ang),
                        cy + VENT_RING_R * np.sin(ang),
                        -LID_PLUG_H - 1, LID_T + 1, 24))
    # a round feeding hatch on the rim
    cuts.append(cyl(4.0, cx, cy + (CYL_OD / 2 - 5.0), -LID_PLUG_H - 1,
                    LID_T + 1, 48))
    return trimesh.boolean.difference([lid] + cuts)


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


def make_previews(tank, slider, nest, arena, lid):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    Z_TANK = 0.0
    Z_NEST = TANK_H
    Z_ARENA = TANK_H + NEST_H
    Z_LID = Z_ARENA + CYL_H

    def placed(m, dz, dy=0.0, dx=0.0):
        o = m.copy()
        o.apply_translation([dx, dy, dz])
        return o

    SLD_X, SLD_Y, SLD_Z = 17.0, -2.5, 8.5

    fig = plt.figure(figsize=(16, 5.2), dpi=140)

    # assembled
    ax = fig.add_subplot(1, 3, 1, projection="3d")
    render(ax, placed(tank, Z_TANK), "#dfe6ea")
    render(ax, placed(nest, Z_NEST), "#c8a165")
    render(ax, placed(arena, Z_ARENA), "#dfe6ea")
    render(ax, placed(lid, Z_LID), "#9fb8c9")
    render(ax, placed(slider, SLD_Z, SLD_Y, SLD_X), "#c0392b")

    # cutaway-ish: no lid, no nest top
    ax2 = fig.add_subplot(1, 3, 2, projection="3d")
    render(ax2, placed(tank, Z_TANK), "#dfe6ea")
    render(ax2, placed(nest, Z_NEST), "#c8a165")
    render(ax2, placed(arena, Z_ARENA), "#dfe6ea")

    # exploded
    ax3 = fig.add_subplot(1, 3, 3, projection="3d")
    render(ax3, placed(tank, 0), "#dfe6ea")
    render(ax3, placed(slider, SLD_Z, SLD_Y, SLD_X), "#c0392b")
    render(ax3, placed(nest, Z_NEST + 16), "#c8a165")
    render(ax3, placed(arena, Z_ARENA + 34), "#dfe6ea")
    render(ax3, placed(lid, Z_LID + 56), "#9fb8c9")

    for ax, title, ztop in ((ax, "assembled", Z_LID + LID_T + 6),
                            (ax2, "without lid (inside view)", Z_LID + LID_T + 6),
                            (ax3, "exploded", Z_LID + 60)):
        ax.set_xlim(-S * 0.3, S * 1.3)
        ax.set_ylim(-S * 0.5, S * 1.3)
        ax.set_zlim(0, ztop)
        ax.set_box_aspect((S * 1.4, S * 1.6, ztop))
        ax.view_init(elev=20, azim=-58)
        ax.set_axis_off()
        ax.set_title(title, fontsize=9)
    fig.suptitle("Mini Soil Nest v5  |  dry arena / soil humidity / fill port")
    fig.tight_layout()
    fig.savefig(os.path.join(PRE, "preview.png"))
    plt.close(fig)


def make_schematic():
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "sans-serif"]
    matplotlib.rcParams["axes.unicode_minus"] = False
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Polygon

    fig, ax = plt.subplots(figsize=(7.2, 8), dpi=140)
    GRAY, EDGE, SOIL, WATER = "#eef2f5", "#5b6b78", "#c8a165", "#9fd0f5"

    ax.add_patch(Rectangle((0, 0), 56, 18, fc=GRAY, ec=EDGE, lw=1.5))     # tank
    ax.add_patch(Rectangle((3, 3), 50, 5, fc=WATER, ec="none"))           # water
    ax.add_patch(Rectangle((0, 18), 56, 20, fc=GRAY, ec=EDGE, lw=1.5))    # nest
    soil = [(3, 22), (53, 22), (53, 30), (49, 30), (49, 34), (45, 34),
            (45, 38), (11, 38), (11, 34), (7, 34), (7, 30), (3, 30)]
    ax.add_patch(Polygon(soil, closed=True, fc=SOIL, ec="#8a6a3a", lw=1.0))
    ax.add_patch(Rectangle((0, 38), 56, 10, fc=GRAY, ec=EDGE, lw=1.5))    # arena base
    ax.add_patch(Rectangle((21, 37), 14, 11, fc="white", ec=EDGE, lw=0.8,
                           ls="--"))                                      # tunnel
    for x in (8, 45.5):                                                    # cylinder
        ax.add_patch(Rectangle((x, 48), 2.5, 30, fc=GRAY, ec=EDGE, lw=1.5))
    ax.add_patch(Rectangle((10.5, 48), 35, 6, fc=SOIL, ec="none"))        # sand
    ax.add_patch(Rectangle((8, 78), 40, 3, fc="#dfe6ea", ec=EDGE, lw=1.5))  # lid

    for i, x in enumerate(range(12, 45, 6)):                              # lid vents
        ax.plot([x, x], [78, 81], color=EDGE, lw=0.8)
    # dimension
    ax.annotate("", xy=(60, 0), xytext=(60, 81),
                arrowprops=dict(arrowstyle="<->", color="#444"))
    ax.text(62, 40, "81 mm", rotation=90, va="center", fontsize=9, color="#444")
    ax.annotate("", xy=(0, -4), xytext=(56, -4),
                arrowprops=dict(arrowstyle="<->", color="#444"))
    ax.text(28, -6, "56 mm", ha="center", va="top", fontsize=9, color="#444")

    def tag(txt, xy, xytext, color="#c0392b"):
        ax.annotate(txt, xy=xy, xytext=xytext, fontsize=12, color=color,
                    ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", color=color, lw=1.6))

    tag("干燥区 · 活动区", (18, 62), (66, 66), "#2f7d4f")
    tag("保湿区 · 土槽", (28, 28), (66, 30), "#8a6a3a")
    tag("加水口 / 水仓", (30, 5), (66, 8), "#1f6fb2")
    tag("下落通道", (28, 42), (66, 48), "#666666")

    ax.set_xlim(-6, 118)
    ax.set_ylim(-12, 90)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Mini Soil Nest v5  |  side section", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(PRE, "schematic.png"))
    plt.close(fig)


# ---------------------------------------------------------------- main
def main():
    parts = {
        "water_tank": build_tank(),
        "slider": build_slider(),
        "nest_tray": build_nest(),
        "arena": build_arena(),
        "arena_lid": build_lid(),
    }
    for name, m in parts.items():
        p = os.path.join(OUT, name + ".stl")
        m.export(p, file_type="stl")
        print(f"[ok] {name:11s} tris={len(m.faces):6d} watertight={m.is_watertight} "
              f"vol={m.volume/1000:.2f}cm3 bounds={np.round(m.bounds,1).tolist()}")

    make_previews(*[parts[k] for k in
                    ("water_tank", "slider", "nest_tray", "arena", "arena_lid")])
    make_schematic()
    print("[ok] preview/preview.png  preview/schematic.png")


if __name__ == "__main__":
    main()
