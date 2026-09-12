// ============================================
// 迷你蚁巢 v2 —— 紧凑一体式（参考市售塔式巢）
// 一体打印件：巢体(带阶梯外观) + 顶部水塔
// 附件：喂食盆 + 盆盖
// 用法：巢室与水塔填腐殖土/沙 → 水塔插湿润棉芯
//       盖板磁吸/插销式，亚克力可选
// ============================================

/* [尺寸] */
body_l = 80;      // 巢体长
body_w = 50;      // 巢体宽
base_h = 18;      // 巢体高
wall   = 3;

/* [水塔] */
tower_d = 34;     // 水塔外径（双圆筒并排）
tower_h = 26;
cotton_d = 13;    // 棉芯孔径

/* [巢室] */
room_r = 14;      // 圆角巢室半径
chamber_depth = 14;

/* [其他] */
screw_d  = 3.2;
$fn = 64;

module rbox2(l, w, r)
  hull(){ for(x=[r,l-r]) for(y=[r,w-r]) translate([x,y]) circle(r); }

// ---------- 一体巢体 ----------
module nest_body() {
  // 下层 体座 + 上层 后沿
  difference() {
    union() {
      linear_extrude(height=chamber_depth) rbox2(body_l, body_w, 10);   // 主巢体
      // 顶部后沿凸缘（放水塔的基座）
      translate([0, body_w-16, chamber_depth])
        linear_extrude(height=5) rbox2(body_l-16, 16, 6);
    }
    // 巢室 A（左）
    translate([wall+16, wall+8, wall])
      linear_extrude(height=chamber_depth)
        rbox2(28, room_r*2, room_r);
    // 巢室 B（右）
    translate([wall+48, wall+8, wall])
      linear_extrude(height=chamber_depth)
        rbox2(22, room_r*2, room_r);
    // B→水塔 竖井（蚂蚁沿坡上塔补水）
    translate([body_l-14, body_w-42, wall])
      cylinder(d=10, h=chamber_depth+8);
    // A→B 走道
    hull(){
      translate([wall+44, wall+room_r+8, wall+5]) cylinder(d=8, h=6);
      translate([wall+50, wall+room_r+8, wall+5]) cylinder(d=8, h=6);
    }
    // 前门洞（接活动场）
    translate([-1, body_w/2-5, wall+4])
      cube([wall+2, 10, 6]);
    // 四角 M3 螺丝沉孔
    for (p=[[6,6],[body_l-6,6],[6,body_w-6],[body_l-6,body_w-6]])
      translate([p[0],p[1],-0.1]) cylinder(d=screw_d, h=wall+2);
  }
  // 巢室间十字隔墙（防止塌腔）
}

// ---------- 水塔（放在后方凸座上） ----------
module tower() {
  difference() {
    union() {
      hull(){
        translate([10, 0, 0]) cylinder(d=tower_d, h=tower_h);
        translate([30, 0, 0]) cylinder(d=tower_d, h=tower_h);
      }
      // 和巢体一起打印时的底部开口（向下插棉芯）
    }
    // 内腔（储水，填棉）
    hull(){
      translate([10, 0, wall]) cylinder(d=tower_d-2*wall, h=tower_h);
      translate([30, 0, wall]) cylinder(d=tower_d-2*wall, h=tower_h);
    }
    // 底部渗水微孔阵列
    for (x=[6:6:34], y=[-6:6:6])
      translate([x, y, -0.1]) cylinder(d=1.5, h=wall+0.2);
    // 注水口
    translate([30, 0, tower_h-2]) cylinder(d=cotton_d, h=6);
  }
  // 注水口环
  translate([30, 0, tower_h-2])
    difference(){
      cylinder(d=cotton_d+4, h=6);
      translate([0,0,-1]) cylinder(d=cotton_d, h=8);
    }
}

// 塔口小塞
module tower_plug()
  difference(){
    cylinder(d=cotton_d+2, h=6);
    translate([0,0,-1]) cylinder(d=cotton_d-1, h=8);
  }

// ---------- 喂食盆附件 ----------
module feeder() {
  difference() {
    hull(){
      translate([10, 12, 0]) cylinder(d=22, h=10);
      translate([26, 12, 0]) cylinder(d=22, h=10);
    }
    hull(){
      translate([10, 12, wall]) cylinder(d=22-2*wall, h=10);
      translate([26, 12, wall]) cylinder(d=22-2*wall, h=10);
    }
  }
}

module feeder_lid()
  difference(){
    hull(){
      translate([10, 12, 0]) cylinder(d=25, h=3);
      translate([26, 12, 0]) cylinder(d=25, h=3);
    }
    hull(){
      translate([10, 12, -1]) cylinder(d=19, h=5);
      translate([26, 12, -1]) cylinder(d=19, h=5);
    }
  }

// ---- 预览组装 ----
nest_body();
translate([body_l/2-22, body_w-6, chamber_depth+5]) rotate([90,0,0]) tower();
translate([body_l/22+22, body_w+22, 0]) feeder();

// ---- 单件导出 ----
// nest_body();                                   // 主巢体
// translate([0,0,0]) tower();                    // 水塔
// translate([0,0,0]) tower_plug();               // 塔塞
// feeder();                                      // 喂食盆
// feeder_lid();                                  // 盆盖
