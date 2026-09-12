# -*- coding: utf-8 -*-
"""
Mini 3D-printable ant nest (formicarium) generator.
迷你 3D 打印蚁巢生成器

结构:
  一块底板 (nest base) 上挖出:
    - 活动区 outworld (觅食/垃圾区), 内含小饮水盘
    - 4 个巢室 chamber A-D, 用通道连成环
    - 1 个保湿槽 hydration well (塞吸水棉, 通过微缝向巢室缓慢扩湿)
    - 1 个对外管接口 tube port (接外接活动区/试管)
  一块可拆卸盖板 (nest cover), 带保湿槽加水孔与活动区透气孔。

整体 76 x 46 x 14 mm (底板) + 76 x 46 x 2 mm (盖板)。全部竖直挖空, 免支撑。
依赖: shapely, trimesh, manifold3d, numpy, matplotlib
"""
import os
import numpy as np
import shapely
from shapely.geometry import box, Point, LineString
from shapely.ops import unary_union
import trimesh
import trimesh.transformations as tf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "design")
PRE = os.path.join(HERE, "preview")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PRE, exist_ok=True)

# ---------------------------------------------------------------- parameters
W, D, H = 76.0, 46.0, 14.0   # base plate width / depth / thickness (mm)
T = 3.0                      # side wall thickness
FLOOR = 4.0                  # remaining floor thickness under cavities
CAV = H - FLOOR              # cavity depth (z = FLOOR .. H) = 10
R_OUT = 4.0                  # outer corner radius

OW = dict(x0=3.0, y0=3.0, x1=31.0, y1=43.0, r=3.0)   # outworld footprint

CH_R = 6.0                   # chamber radius
CHAMBERS = {                 # chamber centres (x, y)
    "A": (44.0, 14.0),
    "B": (44.0, 32.0),
    "C": (57.0, 14.0),
    "D": (57.0, 32.0),
}
CH_W = 3.5                   # chamber-to-chamber tunnel width
ENTRY_W = 4.0                # outworld -> chamber A tunnel width

WELL_C = (67.0, 23.0)        # hydration well centre
WELL_R = 5.5                 # well radius
WELL_FLOOR = 2.0             # well floor thickness (z = 2 .. H)

VENT_W = 0.6                 # micro-slit width (water vapour diffusion)
VENT_OFFSETS = (-2.0, 0.0, 2.0)
VENT_Z0 = 6.0                # slits run from z=6 up to the top
VENT_SIDES = ("C", "D")     # well connects to chamber C and D via slits

PORT_R = 3.0                 # external tube port radius
PORT_Y, PORT_Z = 13.0, 9.0   # port centre on the left wall

DISH_C = (9.0, 9.0)          # small drinking/feeding dish inside outworld
DISH_R = 4.0
DISH_DEPTH = 2.0

COVER_T = 2.0                # cover thickness
COVER_VENT_R = 0.9


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


# ---------------------------------------------------------------- 2D layout
def outworld_poly():
    return rounded_rect(OW["x0"], OW["y0"], OW["x1"], OW["y1"], OW["r"])


def nest_void_poly():
    """Everything that is carved from the top at cavity depth."""
    parts = [outworld_poly()]
    for c in CHAMBERS.values():
        parts.append(circle(c, CH_R))
    # tunnels
    links = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")]
    for a, b in links:
        parts.append(LineString([CHAMBERS[a], CHAMBERS[b]]).buffer(
            CH_W / 2.0, cap_style=1, resolution=32))
    # entry tunnel outworld -> A
    parts.append(LineString([(OW["x1"], 23.0), CHAMBERS["A"]]).buffer(
        ENTRY_W / 2.0, cap_style=1, resolution=32))
    return unary_union(parts)


def vent_polys():
    """Thin slits crossing the wall between the well and chamber C / D."""
    polys = []
    for a in VENT_SIDES:
        p1 = np.array(CHAMBERS[a], dtype=float)
        p2 = np.array(WELL_C, dtype=float)
        d = p2 - p1
        d /= np.linalg.norm(d)
        n = np.array([-d[1], d[0]])
        for off in VENT_OFFSETS:
            q1 = p1 + n * off
            q2 = p2 + n * off
            polys.append(LineString([q1, q2]).buffer(VENT_W / 2.0, cap_style=2))
    return polys


# ---------------------------------------------------------------- build base
def build_base():
    base = extrude(rounded_rect(0, 0, W, D, R_OUT), 0.0, H)

    cuts = [extrude(nest_void_poly(), FLOOR, CAV + 1.0)]
    cuts.append(extrude(circle(WELL_C, WELL_R), WELL_FLOOR, H - WELL_FLOOR + 1.0))
    for p in vent_polys():
        cuts.append(extrude(p, VENT_Z0, H - VENT_Z0 + 1.0))
    cuts.append(extrude(circle(DISH_C, DISH_R, 48), FLOOR - DISH_DEPTH,
                        DISH_DEPTH + 1.0))
    # tube port through the left wall
    port = trimesh.creation.cylinder(radius=PORT_R, height=10.0, sections=64)
    port.apply_transform(tf.rotation_matrix(np.pi / 2.0, [0, 1, 0]))
    port.apply_translation([1.5, PORT_Y, PORT_Z])
    cuts.append(port)

    res = trimesh.boolean.difference([base] + cuts)
    return res


# ---------------------------------------------------------------- build cover
def build_cover():
    cover = extrude(rounded_rect(0, 0, W, D, R_OUT), 0.0, COVER_T)
    cuts = [extrude(circle(WELL_C, WELL_R - 0.5), -1.0, COVER_T + 2.0)]
    # vent holes over the outworld
    xs = np.arange(OW["x0"] + 4.0, OW["x1"] - 2.5, 5.0)
    ys = np.arange(OW["y0"] + 3.0, OW["y1"] - 2.5, 5.0)
    for x in xs:
        for y in ys:
            cuts.append(extrude(circle((x, y), COVER_VENT_R, 24), -1.0,
                                COVER_T + 2.0))
    # a few micro vents over the nest for minimal air exchange
    for c in (CHAMBERS["B"], CHAMBERS["D"]):
        cuts.append(extrude(circle(c, 0.8, 24), -1.0, COVER_T + 2.0))
    return trimesh.boolean.difference([cover] + cuts)


# ---------------------------------------------------------------- render
def render(ax, mesh, color="#c8a165"):
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from matplotlib.colors import to_rgb
    tri = mesh.triangles
    nrm = mesh.face_normals
    light = np.array([-0.35, -0.55, 0.75])
    light /= np.linalg.norm(light)
    inten = np.clip(nrm @ light, 0.25, 1.0)
    base = np.array(to_rgb(color))
    pc = Poly3DCollection(tri, facecolors=base[None, :] * inten[:, None],
                          edgecolors="none")
    ax.add_collection3d(pc)


def make_previews(base, cover):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MPoly
    from matplotlib.collections import PatchCollection

    # ---- blueprint ----
    fig, ax = plt.subplots(figsize=(9, 6), dpi=140)
    outer = rounded_rect(0, 0, W, D, R_OUT)
    void = nest_void_poly()
    well = circle(WELL_C, WELL_R)
    dish = circle(DISH_C, DISH_R)

    def add(geom, fc, ec, z, alpha=1.0):
        geoms = getattr(geom, "geoms", [geom])
        patches = []
        for g in geoms:
            if g.geom_type != "Polygon":
                continue
            patches.append(MPoly(np.array(g.exterior.coords), closed=True))
            for ring in g.interiors:
                patches.append(MPoly(np.array(ring.coords), closed=True))
        ax.add_collection(PatchCollection(patches, facecolor=fc,
                                          edgecolor=ec, linewidths=1.1,
                                          zorder=z, alpha=alpha))

    add(outer, "#f3ead8", "#8a6a3a", 1)
    add(void, "#dff0e6", "#2f7d4f", 2)
    add(well, "#bfe3ff", "#1f6fb2", 3)
    add(dish, "#ffe9b0", "#b98b1e", 4)
    for name, c in CHAMBERS.items():
        ax.text(c[0], c[1], name, ha="center", va="center", fontsize=9,
                color="#1d5b38", zorder=5)
    ax.text(np.mean([OW["x0"], OW["x1"]]), 23, "OUTWORLD", ha="center",
            va="center", fontsize=11, color="#2f7d4f", zorder=5)
    ax.text(WELL_C[0], WELL_C[1] - 0.2, "H2O", ha="center", va="center",
            fontsize=7, color="#1f6fb2", zorder=5)
    ax.text(DISH_C[0], DISH_C[1], "food", ha="center", va="center",
            fontsize=6, color="#8a6a1e", zorder=6)
    # mark micro-slit locations between the well and chambers C / D
    for a in VENT_SIDES:
        p1 = np.array(CHAMBERS[a])
        p2 = np.array(WELL_C)
        mid = (p1 + p2) / 2.0
        ax.plot([mid[0]], [mid[1]], marker="*", ms=9, color="#d9534f",
                zorder=7)
    ax.plot([], [], marker="*", ls="none", ms=8, color="#d9534f",
            label="micro-slits (vapour)")
    ax.legend(loc="upper left", fontsize=7, framealpha=0.9)
    # scale bar
    ax.plot([OW["x0"], OW["x0"] + 10], [-9, -9], color="#333", lw=3,
            solid_capstyle="butt")
    ax.text(OW["x0"] + 5, -10.5, "10 mm", ha="center", va="top", fontsize=7)
    ax.set_xlim(-8, W + 8)
    ax.set_ylim(-13, D + 6)
    ax.set_aspect("equal")
    ax.set_title("Mini Ant Nest  |  top view  |  76 x 46 mm")
    ax.add_patch(plt.Rectangle((0, 0), W, D, fill=False, ec="#8a6a3a", lw=0.8))
    ax.annotate("", xy=(W, -4), xytext=(0, -4),
                arrowprops=dict(arrowstyle="<->", color="#444"))
    ax.text(W / 2, -5.6, "76 mm", ha="center", va="top", fontsize=8)
    ax.annotate("", xy=(-4, D), xytext=(-4, 0),
                arrowprops=dict(arrowstyle="<->", color="#444"))
    ax.text(-5.2, D / 2, "46 mm", ha="right", va="center", rotation=90,
            fontsize=8)
    ax.set_xlabel("tube port -> outworld -> entry -> chambers -> hydration well")
    fig.tight_layout()
    fig.savefig(os.path.join(PRE, "blueprint.png"))
    plt.close(fig)

    # ---- 3D preview ----
    cover_up = cover.copy()
    cover_up.apply_translation([0, 0, H])
    fig = plt.figure(figsize=(15, 5.4), dpi=140)
    panels = [
        ("assembled (opaque cover)", [(base, "#c8a165"), (cover_up, "#8fb0c8")],
         (22, -60), H + COVER_T + 2),
        ("base only - carved layout", [(base, "#c8a165")], (28, 40), H),
        ("base only - top", [(base, "#c8a165")], (90, -90), H),
    ]
    for i, (title, layers, (elev, azim), ztop) in enumerate(panels):
        ax = fig.add_subplot(1, 3, i + 1, projection="3d")
        for mesh, col in layers:
            render(ax, mesh, col)
        ax.set_xlim(0, W)
        ax.set_ylim(0, D)
        ax.set_zlim(0, ztop)
        ax.set_box_aspect((W, D, ztop))
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()
        ax.set_title(title)
    fig.suptitle("Mini Ant Nest  |  support-free 2.5D print")
    fig.tight_layout()
    fig.savefig(os.path.join(PRE, "preview.png"))
    plt.close(fig)


# ---------------------------------------------------------------- main
def main():
    base = build_base()
    cover = build_cover()

    for name, m in (("nest_base", base), ("nest_cover", cover)):
        p = os.path.join(OUT, name + ".stl")
        m.export(p, file_type="stl")
        print(f"[ok] {p}  tris={len(m.faces)}  watertight={m.is_watertight}  "
              f"volume={m.volume/1000:.2f} cm^3")

    make_previews(base, cover)
    print("[ok] preview/blueprint.png  preview/preview.png")
    print(f"base bounds  : {np.round(base.bounds,2).tolist()}")
    print(f"cover bounds : {np.round(cover.bounds,2).tolist()}")


if __name__ == "__main__":
    main()
