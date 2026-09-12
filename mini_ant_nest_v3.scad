// ============================================
// 迷你蚁巢 v3 —— 零悬空可打印版
// 全部件单方向打印：无支撑、无封闭腔
// 装配：巢体开口面朝上打印 → 打完后在开口面
//      覆上底板（v3_2）拧 M3 螺丝 → 翻转即为成品
// ============================================

body_l = 80;  body_w = 50;  body_h = 14;  wall = 3;
tower_d = 36; tower_h = 30; wall_t = 3;
plug_d  = 13;
screw_d = 3.2;
$fn = 64;

module rbox2(l,w,r){ hull(){ for(x=[r,l-r]) for(y=[r,w-r])
  translate([x,y]) circle(r);} }

// 巢室/隧道布置（俯视， 打印床坐标系）
rooms = [
  [10, 10, 30, 22],
  [46, 10, 24, 22],
];
tunnels = [[38, 21, 48, 21]];   // A↔B 走道(y=21)
door    = [74, 21];             // 前门到活动区的洞？

// ---------- v3_1 巢体：开口朝上打印 ----------
module nest_body() {
  difference() {
    linear_extrude(height=body_h) rbox2(body_l, body_w, 8);
    // 巢室+隧道从顶面挖到底 → 打印时每层都是实心环
    for (r = rooms)
      translate([r[0], r[1], -0.1])
        linear_extrude(height=body_h+0.2) rbox2(r[2], r[3], 8);
    for (t = tunnels)
      hull() {
        translate([t[0], t[1], -0.1]) cylinder(d=9, h=body_h+0.2);
        translate([t[2], t[3], -0.1]) cylinder(d=9, h=body_h+0.2);
      }
    // 侧壁斜向的活动区出口(门洞贯通到顶)
    translate([body_l-wall-0.1, 14, -0.1])
      cube([wall+0.2, 14, body_h+0.2]);
    // 四角 M3 过孔
    for (p=[[5,5] ,[body_l-5,5],[5,body_w-5],[body_l-5,body_w-5]])
      translate([p[0],p[1],-0.1]) cylinder(d=screw_d, h=body_h+0.2);
  }
}

// ---------- v3_2 底板（盖住开口面 = 成品地板） ----------
module base_plate() {
  difference() {
    linear_extrude(height=3) rbox2(body_l, body_w, 8);
    // 门洞位置保留开口做"入巢口"
    translate([body_l-4, 14, -0.1]) cube([7, 14, 5]);
    // 透气微孔(每个巢室 4 个)
    for (r = rooms)
      for (x=[r[0]+8:8:r[0]+r[2]-8], y=[r[1]+6:8:r[1]+r[3]-6])
        translate([x, y, -0.1]) cylinder(d=1.2, h=3.2);
    for (p=[[5,5],[body_l-5,5],[5,body_w-5],[body_l-5,body_w-5]])
      translate([p[0],p[1],-0.1]) cylinder(d=screw_d, h=3.2);
  }
  // 巢室区微透湿：底板内侧刻 1.2mm 微孔已含
}

// ---------- v3_3 水塔：杯口朝下打印 ----------
module tower() {
  difference() {
    // 外壳（现在开口向下 = 实际驾驶朝上的杯子）
    translate([0, 0, 0]) rotate([0,0,0])
      cylinder(d=tower_d, h=tower_h);
    // 挖内腔（同样开口向下）
    translate([0, 0, wall_t])
      cylinder(d=tower_d-2*wall_t, h=tower_h-wall_t+0.1);
  }
  // 塔顶环扣（朝下打印时这就是底部实心圈）
  translate([0, 0, tower_h])
    cylinder(d=tower_d+4, h=2);
}

// 陶粒/棉托盘（塞进塔底开口）
module tower_tray() {
  difference() {
    cylinder(d=tower_d-wall_t+0.4, h=3);
    for (i=[0:11]) rotate([0,0,i*30])
      translate([tower_d/2-4, 0, -0.1])
        cube([2.5, 10, 3.5]);   // 放射条缝代替微孔，绝不堵
  }
}

module tower_plug() {
  difference() {
    cylinder(d=plug_d+3, h=6);
    translate([0,0,-1]) cylinder(d=plug_d, h=8);
  }
}

// ---------- v3_5 喂食盆 ----------
module feeder() {
  difference() {
    translate([0,0,0]) cylinder(d=30, h=10);
    translate([0,0,wall]) cylinder(d=30-2*wall, h=10);
    // 分两仓隔条
    translate([-1.5, -20, wall+0.5]) cube([3, 40, 10]);
  }
}

module feeder_lid() {
  difference() {
    cylinder(d=33, h=3);
    translate([0,0,-1]) cylinder(d=24, h=5);
    // 出入口槽
    translate([12, -4, -0.1]) cube([5, 8, 3.2]);
  }
}

// ---- 单件导出 ----
// nest_body(); tower(); tower_tray(); tower_plug(); base_plate(); feeder(); feeder_lid();
