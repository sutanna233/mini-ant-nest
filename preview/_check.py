# -*- coding: utf-8 -*-
"""
几何自检: 直接对生成出的 nest_body.stl 采样, 验证通道连通、门洞开孔、
磁铁孔有料、石膏腔连通, 以及是否为单一可打印连通体。
用法: python preview/_check.py
"""
import os
import sys
import numpy as np
import trimesh

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import generate_nest as G  # noqa: E402

body = trimesh.load(os.path.join(ROOT, "design", "nest_body.stl"))
assert body.is_watertight, "nest_body 不是水密网格"

# 单一连通体检查 (不依赖 graph engine, 用面邻接做并查集)
adj = body.face_adjacency
parent = np.arange(len(body.faces))


def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]
        a = parent[a]
    return a


for a, b in adj:
    ra, rb = find(a), find(b)
    if ra != rb:
        parent[ra] = rb
n_parts = len({find(i) for i in range(len(body.faces))})

# 期望为"空腔"(未填充实体) 的采样点
void_pts = {
    "活动区": (20, 18, 20),
    "活动区地面(干)": (20, 18, 9),
    "注水井": (50, 18, 20),
    "注水井底(石膏)": (50, 18, 5),
    "门洞(活动区->巢区)": (16, 41.5, 14),
    "过水通道(井->石膏)": (46, 41.5, 5),
    "巢室A": (11, 66, 20),
    "巢室B": (30, 66, 20),
    "巢室C": (48, 66, 20),
    "巢区石膏层": (30, 66, 5),
    "巢室A-B 连通口": (21.5, 77, 14),
    "巢室B-C 连通口": (38.5, 55, 14),
    "石膏缺口 A-B": (21.5, 55, 5),
    "石膏缺口 B-C": (38.5, 77, 5),
}
# 期望为"实心"的采样点
solid_pts = {
    "活动区/井 隔墙": (42, 18, 20),
    "隔断带中央": (30, 41, 20),
    "外墙-左": (1.5, 44, 20),
    "巢室A-B 隔墙(非口)": (21.5, 60, 14),
    "巢室B-C 隔墙(非口)": (38.5, 70, 14),
    "底板": (30, 44, 1.0),
}

pts = list(void_pts.values()) + list(solid_pts.values())
inside = body.contains(np.array(pts, dtype=float))
n_void = len(void_pts)

print(f"水密={body.is_watertight}  连通体数={n_parts}  体积={body.volume/1000:.1f}cm3")
print(f"包围盒={np.round(body.bounds,1).tolist()}")

fail = 0
print("\n[应悬空/开孔]")
for i, (name, p) in enumerate(void_pts.items()):
    ok = not inside[i]
    fail += 0 if ok else 1
    print(f"  {'OK ' if ok else 'FAIL'} {name:22s} {p} -> inside={inside[i]}")

print("\n[应为实心]")
for i, (name, p) in enumerate(solid_pts.items()):
    ok = inside[n_void + i]
    fail += 0 if ok else 1
    print(f"  {'OK ' if ok else 'FAIL'} {name:22s} {p} -> inside={inside[n_void + i]}")

# 磁铁孔: 孔心应空, 孔壁应有料
print("\n[磁铁孔]")
for name, pos in (("磁柱-活动", G.MAG_ACT), ("磁柱-巢区", G.MAG_NEST)):
    for x, y in pos:
        pocket = (x, y, G.H - 1.0)                       # 孔内应为空
        wall = (x + G.MAG_D / 2 + 0.8, y, G.H - 1.0)     # 孔壁应为料
        a = body.contains(np.array([pocket], dtype=float))[0]
        b = body.contains(np.array([wall], dtype=float))[0]
        ok = (not a) and b
        fail += 0 if ok else 1
        print(f"  {'OK ' if ok else 'FAIL'} {name} ({x:.0f},{y:.0f}) "
              f"孔心空={not a} 孔壁有料={b}")

print(f"\n连通体数={n_parts} (期望 1); 失败项={fail}")
sys.exit(1 if (fail or n_parts != 1) else 0)
