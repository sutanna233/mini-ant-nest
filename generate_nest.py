# -*- coding: utf-8 -*-
"""
紧凑型小群落蚁巢 v0.6 —— 参数化生成脚本
Compact small-colony ant nest: printed body + cast gypsum humidity + magnetic acrylic mesh lid.

设计出发点: ant-nest-builder skill 的 small-colony baseline (80x112x43)。
本版缩为紧凑型 60x88x38，适合新后/初创小群落（几只~几十只）。
所有尺寸均为起点，必须按目标物种与实测物料复核后再批量。

结构:
  前带(y 3..34): 活动区(干) + 独立注水井(右侧)
  隔断(y 34..49): 实心挡水墙，仅留 门洞 + 石膏过水通道
  巢区(y 49..85): 3 个巢室，底部 5mm 石膏保湿层
  顶部: 亚克力活动区盖(通风窗+网压框+注水孔) + 亚克力巢区盖(全封闭避光)

输出:
  design/nest_body.stl            巢体(打印)
  design/mesh_clamp.stl           金属网压框(打印)
  design/fill_plug.stl            注水口塞(打印)
  design/entrance_reducer.stl     门洞缩小插件(打印, 小型蚁可选)
  design/acrylic_activity_cover.dxf/.svg  活动区盖(3mm 亚克力)
  design/acrylic_nest_cover.dxf/.svg      巢区盖(3mm 亚克力)
  preview/assembly.png            装配图
  preview/plan.png                俯视图(去盖)
  preview/section.png             剖视示意
  bom.csv / BOM.md                物料清单

依赖: numpy, shapely, trimesh, manifold3d, ezdxf, matplotlib
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

# ================================================================ 参数
# ---- 外形 ----
SX, SY, H = 60.0, 88.0, 38.0     # 巢体外形 (x 宽 / y 深 / z 高)
T = 3.0                          # 壁厚
R = 3.0                          # 外形圆角
PLATE = 3.0                      # 底板厚
Z_FLOOR = 8.0                    # 活动区地面 / 巢区石膏表面 高度
GYP_Z0 = 3.0                     # 石膏层底面 -> 石膏厚 = Z_FLOOR - GYP_Z0 = 5mm

# ---- 平面分区 (x0,y0,x1,y1) ----
ACT = (3.0, 3.0, 40.0, 34.0)     # 活动区腔 (干)
WELL = (44.0, 3.0, 57.0, 34.0)   # 注水井腔 (底 z=GYP_Z0, 只在这里加水)
DIV = (3.0, 34.0, 57.0, 49.0)    # 实心隔断带 (挡水, 同时给盖提供支撑)
NEST = (3.0, 49.0, 57.0, 85.0)   # 巢区腔 (底石膏)
NEST_WALLS = [(20.0, 23.0), (37.0, 40.0)]   # 巢室内隔墙

# ---- 洞口 / 通道 (均为穿过隔断带的切口) ----
DOORWAY = (12.0, 20.0, 33.0, 50.0, Z_FLOOR, Z_FLOOR + 12.0)   # 活动区->巢区 门洞
CHANNEL = (44.0, 48.0, 33.0, 50.0, GYP_Z0, Z_FLOOR)           # 注水井->石膏 通道
# 巢室之间的连通口(错位布置) 与 石膏连通缺口(同样错位)
CH_DOORS = [((20.0, 23.0), 72.0, 82.0), ((37.0, 40.0), 50.0, 60.0)]
CH_NOTCH = [((20.0, 23.0), 50.0, 60.0), ((37.0, 40.0), 72.0, 82.0)]

# ---- 磁吸 (钉在腹部, 钢件在亚克力盖) ----
# 4 + 4 个位置必须落在实心材料上, 由 Ø10 磁柱保证
MAG_ACT = [(6.0, 6.0), (54.0, 6.0), (6.0, 38.0), (54.0, 38.0)]
MAG_NEST = [(6.0, 46.0), (54.0, 46.0), (6.0, 82.0), (54.0, 82.0)]
MAG_BOSS_D = 10.0                # 磁柱直径 (保证磁孔四周有料)
MAG_D = 6.6                      # 磁铁孔直径 (Ø6 磁铁 + 装配间隙, 需实测)
MAG_T = 2.0                      # 磁铁实际厚度 (Ø6x2)
NUT_T = 2.4                      # M3 螺母厚 (对边 5.5, 对角约 6.35)
# 孔深 = 螺母 + 磁铁 + 螺钉尖到磁铁面的余量; 螺钉 M3x6, 亚克力 3.0 时取 5.0
POCKET_D = 5.0

# ---- 亚克力盖 ----
ACRYLIC_T = 3.0                  # 名义厚度, 采购后必须实测
ACT_COVER = (0.0, 0.0, 60.0, 42.0)     # 活动区盖轮廓
NEST_COVER = (0.0, 43.0, 60.0, 88.0)   # 巢区盖轮廓
COVER_TAB = (22.0, -5.0, 38.0, 0.0)    # 活动区盖前拉手
WINDOW_C = (21.5, 18.5)          # 通风窗中心 (对准活动区)
WINDOW = (20.0, 10.0)            # 通风窗 20x10
CLAMP = (38.0, 26.0, 3.0)        # 网压框 外形/厚
CLAMP_HOLE = (15.5, 11.0)        # 压框螺钉相对窗心的偏移
MESH = (28.0, 18.0)              # 304 网片 (窗口四周各留 4mm 压边)
FILL_C = (50.5, 18.5)            # 注水孔中心 (对准注水井)
FILL_D = 8.0                     # 注水孔直径
SCREW_HOLE_R = 1.7               # 亚克力通孔 Ø3.4

# ---- 门洞缩小插件 ----
REDUCER_DOOR_R = 1.5             # 缩小后门洞 Ø3 (小型蚁)
REDUCER_CLR = 0.2                # 与门洞的装配间隙


# ================================================================ 工具
def rr(x0, y0, x1, y1, r):
    """圆角矩形 (shapely)"""
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
    """拉伸 shapely 多边形"""
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


def cyl_y(r, c, y0, y1, sec=32):
    """沿 Y 轴的圆柱; c=(x,z)"""
    m = trimesh.creation.cylinder(radius=r, height=y1 - y0, sections=sec)
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    m.apply_translation([c[0], (y0 + y1) / 2, c[1]])
    return m


def diff(meshes):
    return trimesh.boolean.difference(meshes)


def union(meshes):
    return trimesh.boolean.union(meshes)


# ================================================================ 巢体
def build_body():
    body = ex(rr(0, 0, SX, SY, R), 0, H)
    hollow = [
        ex(rr(*ACT, 2), Z_FLOOR, H),          # 活动区, 地面干燥
        ex(rr(*WELL, 2), GYP_Z0, H),          # 注水井, 到石膏底
        ex(rr(*NEST, 2), GYP_Z0, H),          # 巢区, 到石膏底
    ]
    body = diff([body] + hollow)

    # 实心: 巢室内隔墙 + 磁柱 (隔断带与外墙由未挖空部分自然形成)
    add = []
    for x0, x1 in NEST_WALLS:
        add.append(b3(x0, NEST[1], 0, x1, NEST[3], H))
    for x, y in MAG_ACT + MAG_NEST:
        add.append(cyl(MAG_BOSS_D / 2, (x, y), 0, H, 48))
    body = union([body] + add)

    cuts = []
    # 活动区 -> 巢区 门洞
    x0, x1, y0, y1, z0, z1 = DOORWAY
    cuts.append(b3(x0, y0, z0, x1, y1, z1))
    # 注水井 -> 石膏 过水通道 (必须避开磁柱: 通道 x44..48, 磁柱 x49..59)
    x0, x1, y0, y1, z0, z1 = CHANNEL
    cuts.append(b3(x0, y0, z0, x1, y1, z1))
    # 巢室连通口 (上层)
    for (x0, x1), ya, yb in CH_DOORS:
        cuts.append(b3(x0 - 1, ya, Z_FLOOR, x1 + 1, yb, Z_FLOOR + 12))
    # 石膏连通缺口 (底层)
    for (x0, x1), ya, yb in CH_NOTCH:
        cuts.append(b3(x0 - 1, ya, GYP_Z0, x1 + 1, yb, Z_FLOOR + 0.01))
    # 磁铁孔 (从顶面向下钻孔)
    for x, y in MAG_ACT + MAG_NEST:
        cuts.append(cyl(MAG_D / 2, (x, y), H - POCKET_D, H + 1, 48))
    body = diff([body] + cuts)
    return body


# ================================================================ 网压框
def build_clamp():
    cx, cy = WINDOW_C
    w, d, t = CLAMP
    outer = rr(cx - w / 2, cy - d / 2, cx + w / 2, cy + d / 2, 3)
    c = ex(outer, 0, t)
    win = rr(cx - WINDOW[0] / 2, cy - WINDOW[1] / 2,
             cx + WINDOW[0] / 2, cy + WINDOW[1] / 2, 2)
    cuts = [ex(win, -1, t + 2)]
    for sx in (-1, 1):
        for sy in (-1, 1):
            cuts.append(cyl(SCREW_HOLE_R, (cx + sx * CLAMP_HOLE[0],
                                           cy + sy * CLAMP_HOLE[1]), -1, t + 2, 24))
    return diff([c] + cuts)


# ================================================================ 注水口塞
def build_plug():
    top = cyl(5.5, FILL_C, 0, 2.0, 48)
    boss = cyl(3.8, FILL_C, -3.5, 0.5, 48)
    tab = b3(FILL_C[0] - 2.5, FILL_C[1] - 9.5, 0, FILL_C[0] + 2.5, FILL_C[1] - 5.5, 2.0)
    return union([top, boss, tab])


# ================================================================ 门洞缩小插件
def build_reducer():
    x0, x1 = DOORWAY[0], DOORWAY[1]
    z0, z1 = DOORWAY[4], DOORWAY[5]
    c = REDUCER_CLR
    xa, xb = x0 + c, x1 - c
    za, zb = z0 + c, z1 - c
    ya, yb = 43.0, 49.0                       # 从巢区侧插入
    plug = b3(xa, ya, za, xb, yb, zb)
    # 前唇 + 拉手 (卡在门洞外的巢区一侧, 便于取出)
    lip = b3(x0 - 1.5, yb, z0 - 1.5, x1 + 1.5, yb + 1.5, z1 + 1.5)
    tab = b3(x0 + 2.0, yb, z0 + 3.0, x1 - 2.0, yb + 5.0, z0 + 7.0)
    m = union([plug, lip, tab])
    xc, zc = (x0 + x1) / 2, (z0 + z1) / 2
    hole = cyl_y(REDUCER_DOOR_R, (xc, zc), ya - 2.0, yb + 6.0, 32)
    return diff([m, hole])


# ================================================================ 亚克力 DXF/SVG
def _rect_pts(r):
    x0, y0, x1, y1 = r
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _tile_paths(outline, tab, window, fill, holes):
    """把投影元素统一成 (kind, data) 列表, 供 dxf/svg 复用"""
    items = [("poly", _rect_pts(outline))]
    if tab:
        items.append(("poly", _rect_pts(tab)))
    if window:
        cx, cy = WINDOW_C
        w, h = WINDOW
        items.append(("poly", [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
                               (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]))
    for hx, hy, hr in holes:
        items.append(("circ", ((hx, hy), hr)))
    if fill:
        items.append(("circ", (fill, FILL_D / 2)))
    return items


def acrylic(cover, holes, window=None, fill=None, tab=None, name="cover"):
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    items = _tile_paths(cover, tab, window, fill, holes)
    for kind, data in items:
        if kind == "poly":
            msp.add_lwpolyline(data, close=True, dxfattribs={"layer": "CUT"})
        else:
            msp.add_circle(data[0], data[1], dxfattribs={"layer": "CUT"})
    doc.saveas(os.path.join(OUT, name + ".dxf"))


def acrylic_svg(cover, holes, window=None, fill=None, tab=None, name="cover"):
    x0, y0, x1, y1 = cover
    W, Hh = int(SX + 40), int(SY + 40)
    m = 20
    items = _tile_paths(cover, tab, window, fill, holes)
    sg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hh}" '
          f'viewBox="0 0 {W} {Hh}">',
          '<g fill="none" stroke="black" stroke-width="0.4">']
    for kind, data in items:
        if kind == "poly":
            pts = " ".join(f"{px + m:.2f},{m + SY - py:.2f}" for px, py in data)
            sg.append(f'<polygon points="{pts}"/>')
        else:
            (hx, hy), hr = data
            sg.append(f'<circle cx="{hx + m:.2f}" cy="{m + SY - hy:.2f}" r="{hr:.2f}"/>')
    sg.append("</g></svg>")
    with open(os.path.join(OUT, name + ".svg"), "w", encoding="utf-8") as f:
        f.write("\n".join(sg))


def build_acrylics():
    cx, cy = WINDOW_C
    act_holes = [(x, y, SCREW_HOLE_R) for x, y in MAG_ACT]
    act_holes += [(cx + sx * CLAMP_HOLE[0], cy + sy * CLAMP_HOLE[1], SCREW_HOLE_R)
                  for sx in (-1, 1) for sy in (-1, 1)]
    for tag in ("dxf", "svg"):
        fn = acrylic if tag == "dxf" else acrylic_svg
        fn(ACT_COVER, act_holes, window=WINDOW_C, fill=FILL_C, tab=COVER_TAB,
           name="acrylic_activity_cover")
        nest_holes = [(x, y, SCREW_HOLE_R) for x, y in MAG_NEST]
        fn(NEST_COVER, nest_holes, name="acrylic_nest_cover")


# ================================================================ 预览
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
    matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "sans-serif"]
    matplotlib.rcParams["axes.unicode_minus"] = False
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
            [(30, -60, "轴测 (含上下盖)"),
             (90, -90, "俯视 (去盖)")]):
        ax = fig.add_subplot(1, 2, idx + 1, projection="3d")
        render(ax, body, "#c8a165")
        if idx == 0:
            plate3d(ax, ACT_COVER, "#9fc4dc", H + ACRYLIC_T, tab=COVER_TAB)
            plate3d(ax, NEST_COVER, "#9fc4dc", H + ACRYLIC_T)
            cp = clamp.copy()
            cp.apply_translation([0, 0, H + ACRYLIC_T])
            render(ax, cp, "#7fa8c0")
            pg = plug.copy()
            pg.apply_translation([0, 0, H + ACRYLIC_T])
            render(ax, pg, "#c0392b")
        ax.set_xlim(-10, SX + 10)
        ax.set_ylim(-15, SY + 10)
        ax.set_zlim(0, 80)
        ax.set_box_aspect((SX + 20, SY + 25, 80))
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()
        ax.set_title(title, fontsize=10)
    fig.suptitle("紧凑型小群落蚁巢 v0.6 | 打印巢体 + 浇筑石膏 + 亚克力磁吸网盖")
    fig.tight_layout()
    fig.savefig(os.path.join(PRE, "assembly.png"))
    plt.close(fig)


def make_plan(body):
    """去盖俯视示意: 用 shapely 平面几何重绘分区, 标注门洞/通道/磁柱"""
    import matplotlib
    matplotlib.use("Agg")
    matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "sans-serif"]
    matplotlib.rcParams["axes.unicode_minus"] = False
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    fig, ax = plt.subplots(figsize=(6.4, 8.4), dpi=140)
    ax.add_patch(Rectangle((0, 0), SX, SY, fc="#c8a165", ec="#5b4326", lw=1.4))
    ax.add_patch(Rectangle((ACT[0], ACT[1]), ACT[2] - ACT[0], ACT[3] - ACT[1],
                           fc="#f3ead8", ec="#8a6a3a", lw=0.8))
    ax.add_patch(Rectangle((WELL[0], WELL[1]), WELL[2] - WELL[0], WELL[3] - WELL[1],
                           fc="#a9cfe8", ec="#1f6fb2", lw=0.8))
    ax.add_patch(Rectangle((NEST[0], NEST[1]), NEST[2] - NEST[0], NEST[3] - NEST[1],
                           fc="#e8ddc5", ec="#8a6a3a", lw=0.8))
    for x0, x1 in NEST_WALLS:
        ax.add_patch(Rectangle((x0, NEST[1]), x1 - x0, NEST[3] - NEST[1],
                               fc="#c8a165", ec="#5b4326", lw=0.6))
    # 门洞 / 过水通道
    ax.add_patch(Rectangle((DOORWAY[0], DOORWAY[2]), DOORWAY[1] - DOORWAY[0],
                           DOORWAY[3] - DOORWAY[2], fc="#ffffff", ec="#c0392b",
                           lw=1.0, ls="--"))
    ax.add_patch(Rectangle((CHANNEL[0], CHANNEL[2]), CHANNEL[1] - CHANNEL[0],
                           CHANNEL[3] - CHANNEL[2], fc="#a9cfe8", ec="#1f6fb2",
                           lw=1.0, ls="--"))
    for x, y in MAG_ACT + MAG_NEST:
        ax.add_patch(plt.Circle((x, y), MAG_D / 2, fc="#7b2222", ec="black", lw=0.4))
    ax.text(ACT[0] + 12, 18, "活动区\n(干)", ha="center", fontsize=9, color="#8a6a3a")
    ax.text(50.5, 18, "注水井\n(加水)", ha="center", fontsize=9, color="#1f6fb2")
    ax.text(16, 41, "门洞", ha="center", fontsize=8, color="#c0392b")
    ax.text(46, 41, "过水", ha="center", fontsize=8, color="#1f6fb2")
    ax.text(30, 66, "巢区 (3 室 + 石膏底)", ha="center", fontsize=9, color="#5b4326")
    ax.set_xlim(-5, SX + 5)
    ax.set_ylim(-5, SY + 5)
    ax.set_aspect("equal")
    ax.set_xlabel("x / mm")
    ax.set_ylabel("y / mm")
    ax.set_title("俯视 (去盖) 前=活动区/注水井, 后=巢区 (红=磁铁)", fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(PRE, "plan.png"))
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
        ax.add_patch(Rectangle((0, H), SY, ACRYLIC_T, fc="#bcd8ea", ec=EDGE, lw=0.9))
        ax.set_xlim(-6, SY + 6)
        ax.set_ylim(-6, H + 12)
        ax.set_aspect("equal")
        ax.axis("off")
        ax.set_title(title, fontsize=10)

    ax = axes[0]
    frame(ax, "A-A  (x=16, 过活动区-门洞-巢室)")
    ax.add_patch(Rectangle((ACT[1], Z_FLOOR), ACT[3] - ACT[1], H - Z_FLOOR,
                           fc=DRY, ec=EDGE, lw=0.6))
    ax.add_patch(Rectangle((DIV[1], Z_FLOOR), DIV[3] - DIV[1], 12,
                           fc="white", ec="#c0392b", lw=1.0, ls="--"))
    ax.add_patch(Rectangle((NEST[1], GYP_Z0), NEST[3] - NEST[1], 5,
                           fc=WET, ec=EDGE, lw=0.6))
    ax.add_patch(Rectangle((NEST[1], Z_FLOOR), NEST[3] - NEST[1], H - Z_FLOOR,
                           fc=DRY, ec=EDGE, lw=0.6))
    ax.text(18, 26, "活动区(干)", ha="center", fontsize=9, color="#8a6a3a")
    ax.text(41, 26, "门洞", ha="center", fontsize=8, color="#c0392b")
    ax.text(67, 26, "巢室", ha="center", fontsize=9, color="#8a6a3a")
    ax.text(67, 5.5, "石膏 5mm", ha="center", fontsize=8, color="#1f6fb2")

    ax = axes[1]
    frame(ax, "B-B  (x=46, 过注水井-过水通道-巢室)")
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
    ax.text(17, 26, "注水井(加水)", ha="center", fontsize=9, color="#1f6fb2")
    ax.text(41, 12, "4×5\n过水", ha="center", fontsize=8, color="#1f6fb2")
    ax.text(67, 26, "巢室(石膏面)", ha="center", fontsize=9, color="#8a6a3a")
    ax.text(67, 5.5, "石膏 5mm", ha="center", fontsize=8, color="#1f6fb2")

    fig.suptitle("紧凑型小群落蚁巢 v0.6 | 干活动区 / 外部注水井 / 浇筑石膏巢区", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(PRE, "section.png"))
    plt.close(fig)


# ================================================================ BOM
def write_bom():
    rows = [
        ["nest_body", "打印件", "PETG(首选)/PLA", "60 x 88 x 38 mm", 1,
         "0.4mm 喷嘴 / 0.2 层高 / 5 壁 / 6 顶底 / 20-30% 填充, 免支撑; 石膏腔与通道不得留封死的支撑料"],
        ["mesh_clamp", "打印件", "PETG/PLA", "38 x 26 x 3 mm", 1,
         "网面朝下平放打印, 贴网面必须平整"],
        ["fill_plug", "打印件", "PETG/PLA", "Ø11 x 5.5 mm", 1, "注水口塞"],
        ["entrance_reducer", "打印件", "PETG/PLA", "约 22 x 7 x 16 mm", 1,
         "可选: 小型蚁用, 把 8x12 门洞缩到 Ø3, 压入巢区侧门洞"],
        ["acrylic_activity_cover", "外购/加工", "亚克力 实测厚度",
         "60 x 42 mm + 拉手", 1,
         "含 20x10 通风窗 + 4×Ø3.4 磁吸孔 + 4×Ø3.4 压框孔 + Ø8 注水孔; 必须实测厚度"],
        ["acrylic_nest_cover", "外购/加工", "亚克力 实测厚度", "60 x 45 mm", 1,
         "4×Ø3.4 磁吸孔; 全封闭避光"],
        ["mesh_304_100", "外购", "304 编织网 100 目",
         "28 x 18 mm (约 0.1mm 丝 / 0.18mm 孔)", 1, "剪裁, 不要冲孔; 到货检查散丝与边缘"],
        ["magnet_NdFeB", "外购", "钕磁铁 Ø6 x 2 mm", "Ø6 x 2 mm", 8,
         "只装在打印巢体磁柱孔内, 需实测直径/厚度"],
        ["screw_M3x6_steel", "外购", "磁性钢 M3x6 + M3 螺母", "M3 x 6 mm", 8,
         "亚克力磁吸孔用; 装盖前先确认螺钉/螺母确实被磁铁吸住, 不可用 304 不锈钢替代"],
        ["screw_M3x8", "外购", "M3 x 8 (自攻入亚克力)", "M3 x 8 mm", 4,
         "压网框用; 轻载, 拧入亚克力 Ø2.5 预钻孔"],
        ["gypsum", "外购", "无添加陶瓷模具石膏", "约 1 kg", 1,
         "无香精/抗菌/防霉/防水添加剂; 参考单件用量约 5 mL 浆料"],
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
    md += ["",
           "> 单价/运费未含；**报价(ex-ante)与实际付款(实付)必须分开记录**。",
           "> 采购前必须确认规格：磁铁实测直径/厚度、亚克力实测厚度、网目与丝径、石膏是否含添加剂。",
           "> 未获授权不下单、不代付；订单到付款页即停止并报出准确总额。"]
    with open(os.path.join(HERE, "BOM.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    return rows


# ================================================================ main
def main():
    body = build_body()
    clamp = build_clamp()
    plug = build_plug()
    reducer = build_reducer()
    for name, m in (("nest_body", body), ("mesh_clamp", clamp),
                    ("fill_plug", plug), ("entrance_reducer", reducer)):
        p = os.path.join(OUT, name + ".stl")
        m.export(p, file_type="stl")
        print(f"[ok] {name:18s} tris={len(m.faces):6d} watertight={m.is_watertight} "
              f"vol={m.volume/1000:6.1f}cm3 bounds={np.round(m.bounds,1).tolist()}")
    build_acrylics()
    print("[ok] acrylic DXF + SVG")
    make_assembly(body, clamp, plug)
    make_plan(body)
    make_section()
    print("[ok] preview/assembly.png  preview/plan.png  preview/section.png")
    write_bom()
    print("[ok] bom.csv / BOM.md")


if __name__ == "__main__":
    main()
