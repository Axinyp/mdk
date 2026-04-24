# 模板索引

模板使用 `{{变量名}}` 标记可变部分，所有固定属性已预填。

## XML 模板

| 模板 | 用途 | 关键变量 |
|------|------|---------|
| `xml/project.xml.tpl` | 项目根 | project_name, start_form, device_index, machine_id |
| `xml/page.xml.tpl` | 普通页面 | page_name, id, width, height, back_color, bk_image, is_home |
| `xml/dialog.xml.tpl` | 弹窗 | dialog_name, id, x, y, width, height, display_time, radius |
| `xml/button.xml.tpl` | 按钮 | name, id, x, y, w, h, btn_type, text, join_number, colors... |
| `xml/slider.xml.tpl` | 滑条 | name, id, x, y, w, h, join_number, min/max_value |
| `xml/picture.xml.tpl` | 图片 | name, id, x, y, w, h, join_number, image_pictures |
| `xml/textbox.xml.tpl` | 文本 | name, id, x, y, w, h, join_number, font_size |
| `xml/time.xml.tpl` | 时间 | name, id, x, y, w, h, time_type |

## CHT 模板

| 模板 | 用途 |
|------|------|
| `cht/simple-program.cht.tpl` | **CHT 骨架**：对齐中控软件”新建项目 → 简单程序模板”，含中文注释 + `{{变量}}` 占位 |
| `cht/devices.md` | 设备声明规则：按类型直接生成 |
| `cht/events.md` | 事件模板：NormalBtn / AutolockBtn / MutualLockBtn / LEVEL / DATA |

## 默认值

| 参数 | 默认值 |
|------|--------|
| 分辨率 | 2560 x 1600 |
| 版本 | 4.1.9 |
| 字体 | SourceHanSansCN-Regular (中文) / D-DIN (数字) |
| 按钮字号 | 28 |
| 文本色 | #FFFFFFFF |
| 背景色(无图) | NormalColor=#FF333355, PressColor=#FF555577 |
| 圆角 | 10 |
| 滑条范围 | 0-65535 |
| 滑条块大小 | 30x30 |

## 使用方式

生成时：
1. 读取 `_index.md` 了解有哪些模板
2. 读取需要的 `.tpl` 文件
3. 用确认清单中的数据替换 `{{变量}}`
4. 拼装输出

## CHT 注意事项

- CHT 骨架基于中控软件 **”新建项目 → 简单程序模板”**
- `DEFINE_TIMER` 和 `DEFINE_PROGRAME` 不能省略，即使内容为空
- `DEFINE_COMBINE` 也保留，即使为空
- 块顺序固定，不可调换

**LLM 只需决定**: 布局坐标(x,y,w,h)、配色方案、页面结构、控制逻辑。模板处理固定骨架。

