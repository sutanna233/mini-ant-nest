import numpy as np
import trimesh

base = trimesh.load("design/nest_base.stl")
tray = trimesh.load("design/water_tray.stl")


def probe_point(m, p, r=0.25):
    s = trimesh.creation.icosphere(subdivisions=2, radius=r)
    s.apply_translation(p)
    it = trimesh.boolean.intersection([m, s])
    return 0.0 if it is None or it.is_empty else abs(it.volume)


def probe_cyl(m, p1, p2, r=0.2):
    p1 = np.array(p1, float)
    p2 = np.array(p2, float)
    v = p2 - p1
    L = np.linalg.norm(v)
    c = trimesh.creation.cylinder(radius=r, height=L, sections=24)
    c.apply_transform(trimesh.geometry.align_vectors([0, 0, 1], v / L))
    c.apply_translation((p1 + p2) / 2.0)
    it = trimesh.boolean.intersection([m, c])
    return 0.0 if it is None or it.is_empty else abs(it.volume)


print("== base floor: grill vs solid ==")
print(f"  grill hole  (36,5,z2)      vol={probe_point(base,(36,5,2)):.3f}  (expect 0)")
print(f"  nest solid  (61.5,9.5,z2)  vol={probe_point(base,(61.5,9.5,2)):.3f}  (expect >0)")
print(f"  outworld floor (17,23,z2)  vol={probe_point(base,(17,23,2)):.3f}  (expect >0)")
print(f"  base tube port open (x-1..5,y13,z9) vol={probe_cyl(base,(-1,13,9),(5,13,9)):.3f} (expect 0)")
print(f"  chamber D void (57,32,z10) vol={probe_point(base,(57,32,10)):.3f}  (expect 0)")
print(f"  socket (36.5,6.5,z1)       vol={probe_point(base,(36.5,6.5,1)):.3f}  (expect 0)")

print("== tray ==")
print(f"  cavity centre (38,23,z3)   vol={probe_point(tray,(38,23,3)):.3f}  (expect 0)")
print(f"  tray floor    (38,23,z0.5) vol={probe_point(tray,(38,23,0.5)):.3f}  (expect >0)")
print(f"  tray wall     (1.5,23,z3)  vol={probe_point(tray,(1.5,23,3)):.3f}  (expect >0)")
print(f"  post          (36.5,6.5,z4)vol={probe_point(tray,(36.5,6.5,4)):.3f}  (expect >0)")
print(f"  fill port open   (74->78,y23,z3) vol={probe_cyl(tray,(73,23,3),(79,23,3)):.3f} (expect 0)")
print(f"  overflow open    (74->78,y32,z4.5) vol={probe_cyl(tray,(73,32,4.5),(79,32,4.5)):.3f} (expect 0)")
print(f"  wall between ports (74.5,16,z4.5) vol={probe_point(tray,(74.5,16,4.5)):.3f} (expect >0)")

print("== fit: post top vs socket depth ==")
print(f"  post top z={tray.bounds[1][2]:.2f} (<=8.0), socket from base underside")
