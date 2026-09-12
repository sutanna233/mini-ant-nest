# 迷你 3D 打印蚁巢（MiniPrint Ant Nest）

参数化 OpenSCAD 设计：`mini_ant_nest.scad`

## 结构
```
[L3 活动区] 防逃内壁 + 通风孔 + 观察顶盖
[L2 巢室层] 蛹室 / 幼工室 / 王室 + 连接隧道 → 出巢口
[L2 底板]   1.2mm 吸湿微孔阵列（毛细供湿）
[L1 储水层] 蜂窝储水腔 + 注水孔 + 脱脂棉芯
```

- 整体 100×70×28mm，适合小群（10~100 只举腹蚁/弓背蚁小种）
- 保湿原理：储水层棉芯吸水 → 微孔毛细扩散到巢室底面，无需通电
- 装配：M3 螺丝 4 颗 + 食品级硅胶密封接缝

## 打印参数
- 材料：PETG（耐湿首选）/ PLA
- 层高 0.2mm，巢室壁做实心（漏水风险最低的部分）
- L1、L2 单独打印后拼合，接缝涂硅胶

## 使用
1. OpenSCAD 打开 `.scad`，底部注释/放开对应模块导出 STL
2. 储水层注水至 2/3，铺脱脂棉，水 3~7 天补一次
3. 微孔堵塞时用 1mm 针疏通

## 上手建议
- 先养 20 只工的小群试运行 2 周确认无漏水、湿度合适

---

## v4 - 迷你紧凑版 (v4_mini_compact)

单板式 2.5D 蚁巢（76x46mm，免支撑）：活动区 + 4 巢室 + 微缝保湿槽。
见 `v4_mini_compact/`，源码 `v4_mini_compact/generate_nest.py`。

---

## v5 - 垂直分层土巢 (v5_soil_tower)

市面主流样式：上部干燥活动区 / 中部铺土保湿区 / 底部水仓推拉加水口（56x56x81mm，免支撑）。
见 `v5_soil_tower/`，源码 `v5_soil_tower/generate_nest.py`。

---

## v6 - 一体式土巢 (v6_onepiece)

单件一次打印成型（56x56x50mm，免支撑）：后部圆筒活动区 + 前部敞开保湿土槽 + 底层水仓侧壁加水孔。
见 `v6_onepiece/`，源码 `v6_onepiece/generate_nest.py`。

---

## v8 - 塑料巢 + 石膏干湿分区 (v8_plaster)

塑料盒体（100x55x30mm）：左侧活动区，右侧石膏巢区分干燥区/湿润区，中间塑料隔墙挡水，湿润区直接浇水。
见 `v8_plaster/`，源码 `v8_plaster/generate_nest.py`。

---

## v9 - 小群落打样包 (v9_small_colony)

按 ant-nest-builder skill baseline 缩小版（60x88x38mm）：塑料巢体 + 浇筑石膏保湿 + 亚克力磁吸盖 + 304 网压框。
含 STL、亚克力 DXF/SVG、装配图、BOM、中文装配/加水/清洁/验收说明。见 `v9_small_colony/`。
