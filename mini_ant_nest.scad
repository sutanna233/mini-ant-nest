// ============================================================
// 迷你打印蚁巢 MiniPrint-ant-nest v1
// 结构（自下而上）：
//   L1 保湿储水层：蜂窝状储水槽，注水孔+2mm排气孔，水面铺脱脂棉
//   L2 巢室层：底面开 1.2mm 微孔阵列，借毛细+扩散从储水层吸湿
//   L3 活动区：开放栖息场，带防逃内壁、通风孔、喂食坪
// 打印建议：
//   - PETG 或 PLA，0.2mm 层高，壁厚偏实心
//   - L2 巢室层建议打印后内壁可再"蜡浸"一次防渗
//   - 顶盖可选：UV 玻璃片(3mm 亚克力) 或打印透气盖
//   - 装配：三层用 M3 螺丝+螺母，接缝处涂食品硅胶密封
//   - 保湿方式：储水层注水至下层 2/3 高度，棉吸水后
//              通过 L2 底部微孔向巢室缓慢供湿
// ============================================================

/* [整体尺寸] */
nest_l  = 100;   // 巢体长 mm
nest_w  = 70;    // 巢体宽 mm
wall    = 4;     // 主壁厚 mm

/* [巢室] */
chamber_h = 10;  // 巢室高 mm（含顶板）
floor_t   = 3;   // 巢室底板厚（含吸湿微孔段）
mote_d    = 1.2; // 吸湿微孔直径 mm
mote_gap  = 6;   // 微孔间距 mm

/* [保湿层] */
res_h    = 8;    // 储水深 mm
port_d   = 7;    // 注水孔径
port_wall= 2;

/* [活动区] */
arena_h  = 12;   // 活动区高 mm（含顶）
arena_wall = 3;
vent_d   = 3;    // 通风孔径
vent_n   = 4;    // 每侧通风孔数

/* [其他] */
screw_d  = 3.4;  // M3 过孔
$fn = 48;

// ---------- 圆角盒工具 ----------
module rbox(l, w, r) {
    hull() {
        for (x=[r, l-r]) for (y=[r, w-r])
            translate([x, y]) circle(r);
    }
}

// ============ L1 保湿储水层 ============
module water_layer() {
    difference() {
        linear_extrude(height=res_h+wall)
            rbox(nest_l, nest_w, 6);
        // 内腔
        translate([wall, wall, wall])
            linear_extrude(height=res_h)
                rbox(nest_l-2*wall, nest_w-2*wall, 4);
        // 注水孔（右上角）
        translate([nest_l-14, nest_w-14, -1])
            cylinder(d=port_d+2*port_wall, h=res_h+wall+2);
        // 排水/注水塞孔
        translate([nest_l-14, 12, -1])
            cylinder(d=port_d, h=wall+2);
    }
    // 注水口凸台
    translate([nest_l-14, nest_w-14, res_h+wall])
        cylinder(d=port_d+2*port_wall, h=port_wall);
    // 底面支脚
    for (x=[10, nest_l-24], y=[8, nest_w-14])
        translate([x+4, y+4, -1.5])
            cylinder(d=8, h=1.5);
}

// ============ L2 巢室层 ============
chambers = [
    [20, 18, 26, 20],   // [x, y, w, d] 蛹室
    [58, 18, 16, 16],   // 幼工室
    [58, 42, 20, 14],   // 王室
];
tunnels = [          // [x1,y1,x2,y2]
    [46, 28, 58, 26],
    [24, 42, 58, 49],
];

module chamber_floor() {
    difference() {
        translate([0, 0, 0])
            cube([nest_l, nest_w, floor_t]);
        // 吸湿微孔阵列（仅巢室正下方）
        for (c = chambers)
            for (x = [c[0]+3 : mote_gap : c[0]+c[2]-3],
                 y = [c[1]+3 : mote_gap : c[1]+c[3]-3])
                translate([x, y, -0.1])
                    cylinder(d=mote_d, h=floor_t+0.2);
    }
}

module chamber_layer() {
    difference() {
        union() {
            translate([0, 0, floor_t])
                cube([nest_l, nest_w, wall]);          // 中隔层
            // 巢室外壁做实心，便于上开孔固定
        }
        // 巢室腔体（从底板顶面到中隔层顶面）
        for (c = chambers)
            translate([c[0], c[1], floor_t])
                linear_extrude(height=chamber_h-floor_t)
                    rbox(c[2], c[3], 4);
        // 连接隧道
        for (t = tunnels)
            hull() {
                translate([t[0], t[1], floor_t+2])
                    cylinder(d=7, h=chamber_h-floor_t-2);
                translate([t[2], t[3], floor_t+2])
                    cylinder(d=7, h=chamber_h-floor_t-2);
            }
        // 出巢口：右侧壁 → 活动区
        translate([nest_l-6, 34, floor_t+2])
            cube([8, 8, chamber_h-floor_t-3]);
        // 层间固定螺孔
        for (p = [[8,8],[nest_l-8,8],[8,nest_w-8],[nest_l-8,nest_w-8]])
            translate([p[0], p[1], floor_t-0.1])
                cylinder(d=screw_d, h=wall+0.2);
    }
}

// ============ L3 活动区 ============
module arena_layer() {
    arena_top = chamber_h + arena_h;
    difference() {
        linear_extrude(height=arena_h)
            rbox(nest_l, nest_w, 6);
        translate([arena_wall, arena_wall, 2])
            linear_extrude(height=arena_h)
                rbox(nest_l-2*arena_wall, nest_w-2*arena_wall, 4);
        // 入巢口（对接 L2 出巢口）
        translate([nest_l-arena_wall-2, 34, 2]) cube([6, 8, arena_h]);
        // 通风孔
        for (i = [0 : vent_n-1]) {
            translate([nest_l/2 - 6 + (i % 2)*12,
                       nest_w-arena_wall+1, arena_h/2])
                rotate([-90, 0, 0]) cylinder(d=vent_d, h=4);
            translate([nest_l/2 - 6 + (i % 2)*12,
                       arena_wall-1, arena_h/2])
                rotate([90, 0, 0]) cylinder(d=vent_d, h=4);
        }
        for (p = [[8,8],[nest_l-8,8],[8,nest_w-8],[nest_l-8,nest_w-8]])
            translate([p[0], p[1], -0.1])
                cylinder(d=screw_d, h=arena_h+0.2);
    }
    // 防逃内壁上缘加宽沿（可选涂防逃粉）
    translate([arena_wall, arena_wall, arena_h])
        difference() {
            linear_extrude(height=2)
                rbox(nest_l-2*arena_wall, nest_w-2*arena_wall, 4);
            translate([1.5, 1.5, -0.1])
                linear_extrude(height=2.2)
                    rbox(nest_l-2*(arena_wall+1.5),
                         nest_w-2*(arena_wall+1.5), 3);
        }
}

// ============ 顶盖（可选） ============
module lid() {
    translate([nest_l+10, 0, 0]) {
        linear_extrude(height=2) rbox(nest_l, nest_w, 6);
        for (p = [[8,8],[nest_l-8,8],[8,nest_w-8],[nest_l-8,nest_w-8]])
            translate([p[0], p[1], -1]) cylinder(d=screw_d, h=3);
        for (i = [0:5])
            translate([10 + i*16, nest_w/2, -1])
                cylinder(d=5, h=2);
    }
}

// 组装视图
water_layer();
translate([0, 0, res_h+wall+port_wall])   { chamber_floor(); chamber_layer(); }
translate([0, 0, res_h+wall+port_wall+chamber_h]) arena_layer();

// 单件导出时注释上面 4 行，放开下面所需模块：
// water_layer();       // L1
// chamber_floor();     // L2 底板
// chamber_layer();     // L2 主体
// arena_layer();       // L3
// lid();
