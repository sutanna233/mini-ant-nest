# -*- coding: utf-8 -*-
"""
Mini 3D-printable ant nest (formicarium) generator.  v4 - gypsum hydration
迷你 3D 打印蚁巢生成器  v4 - 石膏/珍珠岩蓄水层保湿

三个零件:
  1) nest_base   巢体: 活动区 + 4 巢室 + 通道 + 对外管接口;
                 巢区地板开 Ø1.5 网格孔 (透气/透湿), 活动区地板实心保持干燥。
  2) water_tray  蓄水托盘: 浅腔填石膏/珍珠岩, 侧壁注水孔 + 溢流孔 (限水位),
                 4 根定位柱与巢体底面配合。
  3) nest_cover  盖板: 活动区透气孔, 巢区保留少量泄压微孔。

装配: 托盘 (0..6) -> 巢体 (6..20) -> 盖板 (20..22), 总高 22mm。
全部竖直挖孔, 免支撑。依赖: shapely, trimesh, manifold3d, numpy, matplotlib
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
W, D, H = 76.0, 46.0, 14.0   # nest base outer size / thickness
T = 3.0                      # side wall thickness
FLOOR = 4.0                  # floor thickness under cavities
CAV = H - FLOOR              # cavity depth (z = 4 .. 14) = 10
R_OUT = 4.0                  # outer corner radius

OW = dict(x0=3.0, y0=3.0, x1=31.0, y1=43.0, r=3.0)   # outworld footprint

CH_R = 6.0
CHAMBERS = {
    "A": (44.0, 14.0),
    "B": (44.0, 32.0),
    "C": (57.0, 14.0),
    "D": (57.0, 32.0),
}
CH_W = 3.5                   # chamber-to-chamber tunnel width
ENTRY_W = 4.0                # outworld -> chamber A tunnel width

PORT_R = 3.0                 # external tube port radius
PORT_Y, PORT_Z = 13.0, 9.0   # port on the left wall

DISH_C = (9.0, 9.0)          # drinking/feeding dish in the outworld
DISH_R = 4.0
DISH_DEPTH = 2.0

# --- gypsum hydration layer ---
GRILL_R = 0.75               # floor hole radius (Ø1.5)
GRILL_PITCH = 3.0            # hole spacing
GRILL_X0, GRILL_X1 = 36.0, 70.0
GRILL_Y0, GRILL_Y1 = 5.0, 41.0

TRAY_H = 6.0                 # water tray total height
TRAY_WALL = 3.0
TRAY_BOTTOM = 1.0
FILL_R, FILL_Y, FILL_Z = 2.0, 23.0, 3.0        # Ø4 fill port on the right wall
OVER_R, OVER_Y, OVER_Z = 1.25, 32.0, 5.0       # Ø2.5 overflow port
POST_R = 1.5
POST_POS = [(36.5, 6.5), (70.5, 6.5), (36.5, 39.5), (70.5, 39.5)]
POST_Z0, POST_Z1 = TRAY_BOTTOM, 8.0            # post spans z 1 .. 8
SOCKET_R = 1.6
SOCKET_DEPTH = 2.2                             # blind socket in the base floor

COVER_T = 2.0
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


def xcyl(r, x_center, y, z, length=12.0, sections=48):
    c = trimesh.creation.cylinder(radius=r, height=length, sections=sections)
    c.apply_transform(tf.rotation_matrix(np.pi / 2.0, [0, 1, 0]))
    c.apply_translation([x_center, y, z])
    return c


# ---------------------------------------------------------------- 2D layout
def outworld_poly():
    return rounded_rect(OW["x0"], OW["y0"], OW["x1"], OW["y1"], OW["r"])


def nest_void_poly():
    """Everything carved from the top at cavity depth (outworld + chambers)."""
    parts = [outworld_poly()]
    for c in CHAMBERS.values():
        parts.append(circle(c, CH_R))
    for a, b in (("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")):
        parts.append(LineString([CHAMBERS[a], CHAMBERS[b]]).buffer(
            CH_W / 2.0, cap_style=1, resolution=32))
    parts.append(LineString([(OW["x1"], 23.0), CHAMBERS["A"]]).buffer(
        ENTRY_W / 2.0, cap_style=1, resolution=32))
    return unary_union(parts)


def grill_holes():
    xs = np.arange(GRILL_X0, GRILL_X1 + 1e-6, GRILL_PITCH)
    ys = np.arange(GRILL_Y0, GRILL_Y1 + 1e-6, GRILL_PITCH)
    return [circle((x, y), GRILL_R, 12) for x in xs for y in ys]


# ---------------------------------------------------------------- build base
def build_base():
    base = extrude(rounded_rect(0, 0, W, D, R_OUT), 0.0, H)

    cuts = [extrude(nest_void_poly(), FLOOR, CAV + 1.0)]
    cuts.append(extrude(circle(DISH_C, DISH_R, 48), FLOOR - DISH_DEPTH,
                        DISH_DEPTH + 2.0))
    cuts.append(xcyl(PORT_R, T / 2.0, PORT_Y, PORT_Z))
    # floor grill -> hydration vapour path (stops exactly at the floor top)
    cuts.append(trimesh.util.concatenate(
        [extrude(p, -1.0, FLOOR + 1.0) for p in grill_holes()]))
    # blind alignment sockets on the underside
    for x, y in POST_POS:
        cuts.append(extrude(circle((x, y), SOCKET_R, 24), -0.1,
                            SOCKET_DEPTH + 0.1))
    return trimesh.boolean.difference([base] + cuts)


# ---------------------------------------------------------------- build tray
def build_tray():
    tray = extrude(rounded_rect(0, 0, W, D, R_OUT), 0.0, TRAY_H)
    inner = rounded_rect(TRAY_WALL, TRAY_WALL, W - TRAY_WALL, D - TRAY_WALL,
                         R_OUT - TRAY_WALL)
    cuts = [extrude(inner, TRAY_BOTTOM, TRAY_H - TRAY_BOTTOM + 1.0),
            xcyl(FILL_R, W - T / 2.0, FILL_Y, FILL_Z),
            xcyl(OVER_R, W - T / 2.0, OVER_Y, OVER_Z)]
    tray = trimesh.boolean.difference([tray] + cuts)

    posts = []
    for x, y in POST_POS:
        c = trimesh.creation.cylinder(radius=POST_R,
                                      height=POST_Z1 - POST_Z0, sections=32)
        c.apply_translation([x, y, (POST_Z0 + POST_Z1) / 2.0])
        posts.append(c)
    return trimesh.boolean.union([tray] + posts)


# ---------------------------------------------------------------- build cover
def build_cover():
    cover = extrude(rounded_rect(0, 0, W, D, R_OUT), 0.0, COVER_T)
    cuts = []
    xs = np.arange(OW["x0"] + 4.0, OW["x1"] - 2.5, 5.0)
    ys = np.arange(OW["y0"] + 3.0, OW["y1"] - 2.5, 5.0)
    for x in xs:
        for y in ys:
            cuts.append(extrude(circle((x, y), COVER_VENT_R, 24), -1.0,
                                COVER_T + 2.0))
    for c in (CHAMBERS["B"], CHAMBERS["D"]):        # pressure-relief micro vents
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
    ax.add_collection3d(Poly3DCollection(tri, facecolors=base[None, :] * inten[:, None],
                                         edgecolors="none"))


def make_previews(base, tray, cover):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MPoly, Circle as MCircle
    from matplotlib.collections import PatchCollection

    # ---- blueprint ----
    fig, ax = plt.subplots(figsize=(9.5, 6.2), dpi=140)
    outer = rounded_rect(0, 0, W, D, R_OUT)
    inner = rounded_rect(TRAY_WALL, TRAY_WALL, W - TRAY_WALL, D - TRAY_WALL,
                         R_OUT - TRAY_WALL)
    void = nest_void_poly()

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
    add(inner, "#eef2f5", "#7f9bb0", 1.5)                 # tray cavity outline
    add(void, "#dff0e6", "#2f7d4f", 2)
    # floor grill holes
    ph = [MCircle((p.centroid.x, p.centroid.y), GRILL_R) for p in grill_holes()]
    ax.add_collection(PatchCollection(ph, facecolor="#8ec9ff",
                                      edgecolor="#1f6fb2", linewidths=0.4,
                                      zorder=3))
    ax.add_collection(PatchCollection(
        [MCircle((p.centroid.x, p.centroid.y), GRILL_R) for p in grill_holes()],
        facecolor="none", edgecolor="#1f6fb2", linewidths=0.5, zorder=3))
    ax.add_collection(PatchCollection(
        [MCircle((x, y), SOCKET_R) for x, y in POST_POS],
        facecolor="#d9d9d9", edgecolor="#666", linewidths=0.7, zorder=4))
    ax.add_collection(PatchCollection(
        [MCircle((x, y), POST_R) for x, y in POST_POS],
        facecolor="none", edgecolor="#666", linewidths=0.7, zorder=4))
    ax.add_collection(PatchCollection(
        [MCircle((DISH_C[0], DISH_C[1]), DISH_R)], facecolor="#ffe9b0",
        edgecolor="#b98b1e", linewidths=1.0, zorder=4))
    for name, c in CHAMBERS.items():
        ax.text(c[0], c[1], name, ha="center", va="center", fontsize=9,
                color="#1d5b38", zorder=6)
    ax.text(17, 23, "OUTWORLD\n(dry)", ha="center", va="center", fontsize=10,
            color="#2f7d4f", zorder=6)
    ax.text(53, 23, "NEST\n(gypsum humidity)", ha="center", va="center",
            fontsize=9, color="#1f6fb2", zorder=6)
    ax.text(DISH_C[0], DISH_C[1], "food", ha="center", va="center",
            fontsize=6, color="#8a6a1e", zorder=7)
    ax.annotate("fill port", xy=(W, FILL_Y), xytext=(W - 2, FILL_Y - 8),
                fontsize=7, color="#c0392b",
                arrowprops=dict(arrowstyle="->", color="#c0392b"))
    ax.text(W - 1, OVER_Y + 2.5, "overflow", fontsize=7, color="#c0392b",
            ha="right")
    ax.plot([], [], marker="o", ls="none", ms=5, mfc="#8ec9ff", mec="#1f6fb2",
            label="floor grill Ø1.5 (vapour)")
    ax.plot([], [], marker="o", ls="none", ms=6, mfc="#d9d9d9", mec="#666",
            label="alignment post/socket")
    ax.legend(loc="upper left", fontsize=7, framealpha=0.9)
    ax.set_xlim(-8, W + 12)
    ax.set_ylim(-13, D + 6)
    ax.set_aspect("equal")
    ax.set_title("Mini Ant Nest v4  |  gypsum hydration  |  76 x 46 mm")
    ax.annotate("", xy=(W, -4), xytext=(0, -4),
                arrowprops=dict(arrowstyle="<->", color="#444"))
    ax.text(W / 2, -5.6, "76 mm", ha="center", va="top", fontsize=8)
    ax.annotate("", xy=(-4, D), xytext=(-4, 0),
                arrowprops=dict(arrowstyle="<->", color="#444"))
    ax.text(-5.2, D / 2, "46 mm", ha="right", va="center", rotation=90,
            fontsize=8)
    ax.plot([OW["x0"], OW["x0"] + 10], [-9, -9], color="#333", lw=3,
            solid_capstyle="butt")
    ax.text(OW["x0"] + 5, -10.5, "10 mm", ha="center", va="top", fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(PRE, "blueprint.png"))
    plt.close(fig)

    # ---- 3D preview ----
    tray_a = tray.copy()
    base_a = base.copy()
    base_a.apply_translation([0, 0, TRAY_H])
    cover_a = cover.copy()
    cover_a.apply_translation([0, 0, TRAY_H + H])
    fig = plt.figure(figsize=(15.5, 5.2), dpi=140)
    panels = [
        ("assembled: tray + base + cover",
         [(tray_a, "#a9c7dd"), (base_a, "#c8a165"), (cover_a, "#8fb0c8")],
         (22, -60), TRAY_H + H + COVER_T + 2),
        ("nest base (underside grill + sockets)", [(base, "#c8a165")],
         (-35, -60), H + TRAY_H),
        ("water tray (fill / overflow / posts)", [(tray, "#a9c7dd")],
         (30, 45), TRAY_H + 3),
    ]
    for i, (title, layers, (elev, azim), ztop) in enumerate(panels):
        ax = fig.add_subplot(1, 3, i + 1, projection="3d")
        for mesh, col in layers:
            render(ax, mesh, col)
        ax.set_xlim(0, W)
        ax.set_ylim(0, D)
        ax.set_zlim(-2 if i == 1 else 0, ztop)
        ax.set_box_aspect((W, D, ztop + 2))
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()
        ax.set_title(title, fontsize=9)
    fig.suptitle("Mini Ant Nest v4  |  gypsum / perlite hydration layer")
    fig.tight_layout()
    fig.savefig(os.path.join(PRE, "preview.png"))
    plt.close(fig)


# ---------------------------------------------------------------- main
def main():
    base = build_base()
    tray = build_tray()
    cover = build_cover()

    for name, m in (("nest_base", base), ("water_tray", tray),
                    ("nest_cover", cover)):
        p = os.path.join(OUT, name + ".stl")
        m.export(p, file_type="stl")
        print(f"[ok] {p}  tris={len(m.faces)}  watertight={m.is_watertight}  "
              f"volume={m.volume/1000:.2f} cm^3")

    make_previews(base, tray, cover)
    print("[ok] preview/blueprint.png  preview/preview.png")
    print(f"base bounds : {np.round(base.bounds,2).tolist()}")
    print(f"tray bounds : {np.round(tray.bounds,2).tolist()}")
    print(f"cover bounds: {np.round(cover.bounds,2).tolist()}")


if __name__ == "__main__":
    main()
