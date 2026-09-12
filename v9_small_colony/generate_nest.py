# -*- coding: utf-8 -*-
"""
Small-colony plastic nest with cast-gypsum humidity + magnetic acrylic mesh lid.
小群落蚁巢: 塑料巢体(一次性打印) + 石膏保湿层 + 亚克力磁吸盖 + 金属网压框.

来源: ant-nest-builder skill 的 baseline (80x112x43). 尺寸均为起点, 需按目标物种复核.
输出:
  design/nest_body.stl        巢体 (打印)
  design/mesh_clamp.stl        金属网压框 (打印)
  design/fill_plug.stl         注水口塞 (打印)
  design/acrylic_activity_cover.dxf/.svg   活动区盖 (3mm 亚克力)
  design/acrylic_nest_cover.dxf/.svg       巢区盖 (3mm 亚克力)
  bom.csv                      物料清单
  preview/assembly.png         装配图
  preview/section.png          剖视示意

依赖: shapely, trimesh, manifold3d, numpy, matplotlib, ezdxf
"""
import csv
import os
import numpy as np
import ezdxf
from shapely.geometry import box, Point
from shapely.ops import unary_union
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "design")
PRE = os.path.join(HERE, "preview")
os.makedirs(OUT, exist_ok=True)
os.makedirs(PRE, exist_ok=True)

# ---------------------------------------------------------------- parameters
SX, SY, H = 60.0, 88.0, 38.0      # body envelope (scaled down from the 80x112 baseline)
T = 3.0                            # wall thickness
R = 3.0                            # outer corner radius
PLATE = 3.0                        # bottom plate
Z_FLOOR = 8.0                      # activity floor / gypsum surface
GYP_Z0 = 3.0                       # gypsum pocket bottom (5 mm thick)

ACT = (3.0, 3.0, 40.0, 32.0)       # activity cavity  (x0,y0,x1,y1)
WELL = (43.0, 3.0, 57.0, 32.0)     # refill well (floor Z3)
DIV = (3.0, 32.0, 57.0, 46.0)      # solid divider band
NEST = (3.0, 46.0, 57.0, 85.0)     # nest zone (chambers + gypsum)
NEST_WALLS = [(20.0, 23.0), (37.0, 40.0)]     # printed partition walls
NOTCH_Y = (55.0, 70.0)             # gypsum connecting notches
DOOR_Y = (72.0, 52.0)              # ant doorways between chambers
CHANNEL = (44.0, 54.0, 3.0, 8.0)   # well -> gypsum (x0,x1,z0,z1)
DOOR = (12.0, 22.0)                # activity -> nest doorway (x0,x1), Z8..21

MAG_POS = [(6, 6), (54, 6), (6, 39), (54, 39),
           (6, 49), (54, 49), (6, 79), (54, 79)]
PAD = 12.0
MAG_D, MAG_T = 6.4, 2.3            # magnet pocket dia / magnet thickness
HEAD_D, HEAD_T = 6.0, 1.8          # screw-head recess
POCKET_D = MAG_T + HEAD_T          # total pocket depth 4.1

ACRYLIC_T = 3.0
ACT_COVER = (0.0, 3.0, 60.0, 42.0)     # activity cover outline
NEST_COVER = (0.0, 43.0, 60.0, 85.0)   # nest cover outline
WINDOW_C = (28.0, 17.5)                # vent window centre
WINDOW = (20.0, 10.0)
CLAMP = (38.0, 26.0, 3.0)
CLAMP_HOLE = (15.5, 11.0)              # clamp screw offset from window centre
MESH = (28.0, 18.0)
Vent_hole_r = 4.0                  # fill hole in acrylic (dia 8)
FILL_C = (50.0, 18.5)


# ---------------------------------------------------------------- helpers
def rr(x0, y0, x1, y1, r):
    if r <= 0:
        return box(x0, y0, x1, y1)
    rects = [box(x0 + r, y0, x1 - r, y1), box(x0, y0 + r, x1, y1 - r)]
    cs = [Point(x, y).buffer(r, resolution=48)
          for x, y in ((x0 + r, y0 + r), (x1 - r, y0 + r),
                       (x0 + r, y1 - r), (x1 - r, y1 - r))]
    return unary_union(rects + cs)


def circ(c, r, res=64):
    return Point(*c).buffer(r, resolution=res)


def ex(poly, z0, h):
    m = trimesh.creation.extrude_polygon(poly, height=h)
    m.apply_translation([0, 0, z0])
    return m


def b3(x0, y0, z0, x1, y1, z1):
    m = trimesh.creation.box(extents=(x1 - x0, y1 - y0, z1 - z0))
    m.apply_translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    return m


def cyl(r, c, z0, z1, sec=48):
    m = trimesh.creation.cylinder(radius=r, height=z1 - z0, sections=sec)
    m.apply_translation([c[0], c[1], (z0 + z1) / 2])
    return m


# ---------------------------------------------------------------- body
def build_body():
    body = ex(rr(0, 0, SX, SY, R), 0, H)
    geo = [
        ex(rr(*ACT, 2), Z_FLOOR, H),                       # activity cavity
        ex(rr(*WELL, 2), GYP_Z0, H),                       # refill well
        ex(rr(*NEST, 2), GYP_Z0, H),                       # nest cavity (pocket+chambers)
    ]
    body = trimesh.boolean.difference([body] + geo)

    add = [b3(0, 0, 0, PAD, PAD, H), b3(SX - PAD, 0, 0, SX, PAD, H),
           b3(0, SY - PAD, 0, PAD, SY, H), b3(SX - PAD, SY - PAD, 0, SX, SY, H)]
    for x in (0, SX - PAD):
        add.append(b3(x, DIV[1], 0, x + PAD, DIV[3], H))   # divider corner pads
    for x0, x1 in NEST_WALLS:
        add.append(b3(x0, NEST[1], 0, x1, NEST[3], H))     # chamber walls
    body = trimesh.boolean.union([body] + add)

    cuts = [b3(DOOR[0], DIV[1] - 1, Z_FLOOR, DOOR[1], DIV[3] + 1, Z_FLOOR + 13),
            b3(CHANNEL[0], DIV[1] - 1, CHANNEL[2], CHANNEL[1], DIV[3] + 1,
               CHANNEL[3])]
    # gypsum bridging notches at the bottom of each chamber wall
    for (x0, x1), y in zip(NEST_WALLS, NOTCH_Y):
        cuts.append(b3(x0 - 1, y, GYP_Z0, x1 + 1, y + 12, Z_FLOOR + 0.01))
    # ant doorways between chambers
    for (x0, x1), y in zip(NEST_WALLS, DOOR_Y):
        cuts.append(b3(x0 - 1, y, Z_FLOOR, x1 + 1, y + 10, Z_FLOOR + 13))
    # magnet pockets
    for x, y in MAG_POS:
        cuts.append(cyl(MAG_D / 2, (x, y), H - POCKET_D, H + 1, 40))
    body = trimesh.boolean.difference([body] + cuts)
    return body


# ---------------------------------------------------------------- mesh clamp
def build_clamp():
    cx, cy = WINDOW_C
    outer = rr(cx - CLAMP[0] / 2, cy - CLAMP[1] / 2,
               cx + CLAMP[0] / 2, cy + CLAMP[1] / 2, 3)
    c = ex(outer, 0, CLAMP[2])
    win = rr(cx - WINDOW[0] / 2, cy - WINDOW[1] / 2,
             cx + WINDOW[0] / 2, cy + WINDOW[1] / 2, 2)
    cuts = [ex(win, -1, CLAMP[2] + 2)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            cuts.append(cyl(1.7, (cx + sx * CLAMP_HOLE[0], cy + sy * CLAMP_HOLE[1]),
                            -1, CLAMP[2] + 2, 24))
    return trimesh.boolean.difference([c] + cuts)


# ---------------------------------------------------------------- fill plug
def build_plug():
    top = cyl(5.5, FILL_C, 0, 2.0, 48)
    boss = cyl(3.8, FILL_C, -3.0, 0.5, 48)
    tab = b3(FILL_C[0] - 2.5, FILL_C[1] - 9.5, 0, FILL_C[0] + 2.5, FILL_C[1] - 5.5, 2.0)
    return trimesh.boolean.union([top, boss, tab])


# ---------------------------------------------------------------- acrylic dxf
def acrylic(cover, holes, window=None, fill=None, tab=None, name="cover"):
    x0, y0, x1, y1 = cover
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_lwpolyline([(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
                       close=True, dxfattribs={"layer": "CUT"})
    if tab:
        tx0, ty0, tx1, ty1 = tab
        msp.add_lwpolyline([(tx0, ty0), (tx1, ty0), (tx1, ty1), (tx0, ty1)],
                           close=True, dxfattribs={"layer": "CUT"})
    if window:
        cx, cy = window
        msp.add_circle((cx, cy), 0.1, dxfattribs={"layer": "CUT"}) if False else None
        w, h = WINDOW
        msp.add_lwpolyline([(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
                            (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)],
                           close=True, dxfattribs={"layer": "CUT"})
    for hx, hy, hr in holes:
        msp.add_circle((hx, hy), hr, dxfattribs={"layer": "CUT"})
    if fill:
        msp.add_circle(fill, Vent_hole_r, dxfattribs={"layer": "CUT"})
    doc.saveas(os.path.join(OUT, name + ".dxf"))
    return doc


def acrylic_svg(cover, holes, window=None, fill=None, tab=None, name="cover"):
    x0, y0, x1, y1 = cover
    w, h = int(SX + 40), int(SY + 40)

    def rect(a, b, c, d):
        return (f'<rect x="{a+20:.2f}" y="{20+SY-d:.2f}" '
                f'width="{c-a:.2f}" height="{d-b:.2f}" fill="none" stroke="black"/>')

    sg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
          f'viewBox="0 0 {w} {h}">']
    sg.append(rect(x0, y0, x1, y1))
    if tab:
        sg.append(rect(*tab))
    if window:
        cx, cy = window
        ww, hh = WINDOW
        sg.append(rect(cx - ww / 2, cy - hh / 2, cx + ww / 2, cy + hh / 2))
    for hx, hy, hr in holes:
        sg.append(f'<circle cx="{hx+20:.2f}" cy="{20+SY-hy:.2f}" r="{hr}" '
                  f'fill="none" stroke="black"/>')
    if fill:
        sg.append(f'<circle cx="{fill[0]+20:.2f}" cy="{20+SY-fill[1]:.2f}" '
                  f'r="{Vent_hole_r}" fill="none" stroke="black"/>')
    sg.append("</svg>")
    with open(os.path.join(OUT, name + ".svg"), "w", encoding="utf-8") as f:
        f.write("\n".join(sg))


def build_acrilics():
    act_holes = [(x, y, 1.7) for x, y in
                 [(6, 6), (54, 6), (6, 39), (54, 39)]]
    cx, cy = WINDOW_C
    act_holes += [(cx + sx * CLAMP_HOLE[0], cy + sy * CLAMP_HOLE[1], 1.7)
                  for sx in (-1, 1) for sy in (-1, 1)]     # mesh clamp screws
    act_tab = (22.0, -4.0, 38.0, 3.0)
    acrylic(ACT_COVER, act_holes, window=WINDOW_C, fill=FILL_C, tab=act_tab,
            name="acrylic_activity_cover")
    acrylic_svg(ACT_COVER, act_holes, window=WINDOW_C, fill=FILL_C, tab=act_tab,
                name="acrylic_activity_cover")
    nest_holes = [(x, y, 1.7) for x, y in [(6, 49), (54, 49), (6, 79), (54, 79)]]
    acrylic(NEST_COVER, nest_holes, name="acrylic_nest_cover")
    acrylic_svg(NEST_COVER, nest_holes, name="acrylic_nest_cover")


# ---------------------------------------------------------------- render
def render(ax, mesh, color):
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from matplotlib.colors import to_rgb
    n = mesh.face_normals
    light = np.array([-0.35, -0.55, 0.75])
    light /= np.linalg.norm(light)
    inten = np.clip(n @ light, 0.3, 1.0)
    c = np.array(to_rgb(color))
    ax.add_collection3d(Poly3DCollection(mesh.triangles,
                                         facecolors=c[None, :] * inten[:, None],
                                         edgecolors="none"))


def make_assembly(body, clamp, plug):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    fig = plt.figure(figsize=(13, 6.2), dpi=140)

    def plate3d(ax, cover, color, z, tab=None):
        x0, y0, x1, y1 = cover
        polys = [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]
        if tab:
            polys.append([(tab[0], tab[1]), (tab[2], tab[1]),
                          (tab[2], tab[3]), (tab[0], tab[3])])
        for p in polys:
            ax.add_collection3d(Poly3DCollection(
                [[(x, y, z) for x, y in p]], facecolors=color, edgecolors="#46708f"))

    for idx, (elev, azim, title) in enumerate(
            [(30, -60, "isometric (with covers)"),
             (90, -90, "top (body only, covers off)")]):
        ax = fig.add_subplot(1, 2, idx + 1, projection="3d")
        render(ax, body, "#c8a165")
        if idx == 0:
            plate3d(ax, ACT_COVER, "#9fc4dc", H + ACRYLIC_T, tab=(22, -4, 38, 3))
            plate3d(ax, NEST_COVER, "#9fc4dc", H + ACRYLIC_T)
            cp = clamp.copy(); cp.apply_translation([0, 0, H + ACRYLIC_T])
            render(ax, cp, "#7fa8c0")
            pg = plug.copy(); pg.apply_translation([0, 0, H + ACRYLIC_T])
            render(ax, pg, "#c0392b")
        ax.set_xlim(-10, SX + 10); ax.set_ylim(-15, SY + 10); ax.set_zlim(0, 80)
        ax.set_box_aspect((SX + 20, SY + 25, 80))
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()
        ax.set_title(title, fontsize=9)
    fig.suptitle("Small-colony nest | printed body + cast gypsum + acrylic mesh lid")
    fig.tight_layout()
    fig.savefig(os.path.join(PRE, "assembly.png"))
    plt.close(fig)


def make_section():
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "sans-serif"]
    matplotlib.rcParams["axes.unicode_minus"] = False
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    GRAY, EDGE, DRY, WET = "#eef2f5", "#5b6b78", "#f3ead8", "#a9cfe8"
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), dpi=140)

    def frame(ax, title):
        ax.add_patch(Rectangle((0, 0), SY, H, fc=GRAY, ec=EDGE, lw=1.6))
        ax.add_patch(Rectangle((3, H), SY - 6, ACRYLIC_T, fc="#bcd8ea",
                               ec=EDGE, lw=0.9))
        ax.set_xlim(-6, SY + 6)
        ax.set_ylim(-6, H + 12)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, fontsize=10)

    # --- section A: through the activity (X = 30) ---
    ax = axes[0]
    frame(ax, "A-A  (x=30, through activity)")
    ax.add_patch(Rectangle((ACT[1], Z_FLOOR), ACT[3] - ACT[1], H - Z_FLOOR,
                           fc=DRY, ec=EDGE, lw=0.6))
    ax.add_patch(Rectangle((DIV[1], Z_FLOOR), DIV[3] - DIV[1], 21 - Z_FLOOR,
                           fc="white", ec="#c0392b", lw=1.0, ls="--"))
    ax.add_patch(Rectangle((NEST[1], GYP_Z0), NEST[3] - NEST[1], 5,
                           fc=WET, ec=EDGE, lw=0.6))
    ax.add_patch(Rectangle((NEST[1], Z_FLOOR), NEST[3] - NEST[1], H - Z_FLOOR,
                           fc=DRY, ec=EDGE, lw=0.6))
    ax.text(17, 26, "活动区 (干)", ha="center", fontsize=9, color="#8a6a3a")
    ax.text(39, 26, "门洞", ha="center", fontsize=8, color="#c0392b")
    ax.text(65, 26, "巢区 (巢室)", ha="center", fontsize=9, color="#8a6a3a")
    ax.text(65, 5.5, "石膏层 5mm", ha="center", fontsize=8, color="#1f6fb2")

    # --- section B: through the refill well (X = 50) ---
    ax = axes[1]
    frame(ax, "B-B  (x=50, through refill well)")
    ax.add_patch(Rectangle((WELL[1], GYP_Z0), WELL[3] - WELL[1], 5,
                           fc=WET, ec=EDGE, lw=0.6))
    ax.add_patch(Rectangle((WELL[1], Z_FLOOR), WELL[3] - WELL[1], H - Z_FLOOR,
                           fc=GRAY, ec=EDGE, lw=0.6))
    ax.add_patch(Rectangle((DIV[1], GYP_Z0), DIV[3] - DIV[1], 5,
                           fc="white", ec="#1f6fb2", lw=1.0, ls="--"))
    ax.add_patch(Rectangle((NEST[1], GYP_Z0), NEST[3] - NEST[1], 5,
                           fc=WET, ec=EDGE, lw=0.6))
    ax.add_patch(Rectangle((NEST[1], Z_FLOOR), NEST[3] - NEST[1], H - Z_FLOOR,
                           fc=DRY, ec=EDGE, lw=0.6))
    ax.text(17, 26, "注水井 (加水)", ha="center", fontsize=9, color="#1f6fb2")
    ax.text(39, 12, "12×5\n通道", ha="center", fontsize=8, color="#1f6fb2")
    ax.text(65, 26, "巢区 (石膏面)", ha="center", fontsize=9, color="#8a6a3a")
    ax.text(65, 5.5, "石膏层 5mm", ha="center", fontsize=8, color="#1f6fb2")

    fig.suptitle("Small-colony nest | dry activity / external refill well / cast gypsum", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(PRE, "section.png"))
    plt.close(fig)


# ---------------------------------------------------------------- BOM
def write_bom():
    rows = [
        ["nest_body", "打印件", "PLA", "60 x 88 x 38 mm", 1,
         "0.4mm 喷嘴 / 0.2 层高 / 5 壁 / 6 顶底 / 20-30% 填充, 免支撑"],
        ["mesh_clamp", "打印件", "PLA", "38 x 26 x 3 mm", 1, "网面朝下平放打印"],
        ["fill_plug", "打印件", "PLA", "Ø11 x 5 mm", 1, "注水口塞"],
        ["acrylic_activity_cover", "外购/加工", "亚克力 3mm(实测)",
         "60 x 39 mm + 拉手", 1, "含 20x10 通风窗 + 8×Ø3.4 孔 + Ø8 注水孔"],
        ["acrylic_nest_cover", "外购/加工", "亚克力 3mm(实测)", "60 x 42 mm", 1,
         "4×Ø3.4 磁吸孔"],
        ["mesh_304_100", "外购", "304 编织网 100 目",
         "28 x 18 mm/(约 0.1mm 丝 / 0.18mm 孔)", 1, "剪裁, 不要冲孔"],
        ["magnet", "外购", "钕磁铁 Ø6 x 2 mm", "Ø6 x 2 mm", 8,
         "装入巢体磁铁孔, 需确认极性/吸力"],
        ["screw_M3x6", "外购", "磁性钢 M3x6", "M3 x 6 mm", 8,
         "亚克力盖用, 需实测能否被磁铁吸住; 配 M3 螺母"],
        ["screw_M3x10", "外购", "M3x10 + 螺母", "M3 x 10 mm", 4, "压网框"],
        ["gypsum", "外购", "无香精陶瓷模具石膏", "约 1 kg", 1,
         "无抗菌/防霉/防水/香精添加剂; 参考用量 ~5.4mL/件"],
    ]
    with open(os.path.join(HERE, "bom.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["件名", "来源", "材料", "规格", "数量", "备注"])
        w.writerows(rows)
    md = ["# 物料清单 (BOM)", "",
          "| 件名 | 来源 | 材料 | 规格 | 数量 | 备注 |",
          "|------|------|------|------|------|------|"]
    for r in rows:
        md.append("| " + " | ".join(str(c) for c in r) + " |")
    md += ["", "> 单价/运费未含；报价与实付金额需分开记录。",
           "> 采购前须先确认规格（尤其磁铁实际尺寸、亚克力实测厚度、网目），未获授权不下单、不代付。"]
    with open(os.path.join(HERE, "BOM.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    return rows


# ---------------------------------------------------------------- main
def main():
    body = build_body()
    clamp = build_clamp()
    plug = build_plug()
    for name, m in (("nest_body", body), ("mesh_clamp", clamp), ("fill_plug", plug)):
        p = os.path.join(OUT, name + ".stl")
        m.export(p, file_type="stl")
        print(f"[ok] {name:16s} tris={len(m.faces):6d} watertight={m.is_watertight} "
              f"vol={m.volume/1000:.1f}cm3 bounds={np.round(m.bounds,1).tolist()}")
    build_acrilics()
    print("[ok] acrylic DXF + SVG")
    make_assembly(body, clamp, plug)
    make_section()
    print("[ok] preview/assembly.png  preview/section.png")
    write_bom()
    print("[ok] bom.csv")


if __name__ == "__main__":
    main()
