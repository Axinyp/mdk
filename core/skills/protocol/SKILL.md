---
name: "mdk:protocol"
description: "MKControl 设备协议库管理：列出、添加、查看、修改、删除、从 .cht 反向提取协议。当用户执行 /mk-protocol-* 命令时调用。"
commands:
  - /mk-protocol-list
  - /mk-protocol-add
  - /mk-protocol-show
  - /mk-protocol-update
  - /mk-protocol-delete
  - /mk-protocol-import
---

# 协议管理 Skill

## 职责

管理 MKControl 设备协议知识库（`core/protocols/`），提供协议的增删查改和从 .cht 反向提取功能。

## 协议库路径

```
core/protocols/
  _index.md          ← 总索引（所有协议一行一条）
  _template.md       ← 标准条目模板
  projector/         ← 投影仪
  curtain/           ← 窗帘电机
  ac/                ← 空调（红外）
  audio/             ← 音频处理器
  display/           ← 显示设备
  camera/            ← 摄像机
  matrix/            ← 矩阵切换器
  screen/            ← 投影幕
  lighting/          ← 调光器
  custom/            ← 用户自定义
```

---

## /mk-protocol-list — 列出协议

### 触发方式
```
/mk-protocol-list            → 全部协议（按分类）
/mk-protocol-list 窗帘        → 只看窗帘类
/mk-protocol-list projector  → 只看投影仪
/mk-protocol-list TCP        → 只看 TCP 通信方式
```

### 执行步骤

1. 读取 `core/protocols/_index.md`
2. 若有过滤关键词，按关键词筛选（大小写不敏感）
3. 格式化输出

### 输出格式

```
## 协议库 — [过滤条件或"全部"]

| 分类 | 文件 | 设备 | 通信方式 |
|------|------|------|---------|
| projector | pjlink-generic.md | 通用PJLink | TCP:4352 |
| curtain | generic-rs485.md | 通用RS485窗帘 | RS485:9600 |
...

共 N 条协议。
```

---

## /mk-protocol-add — 添加新协议

### 触发方式
```
/mk-protocol-add             → 引导式添加（逐步提问）
/mk-protocol-add 格力空调 RS232  → 带初始信息添加
```

### 执行步骤（引导式）

1. 询问设备类型：
   ```
   请选择设备功能类型：
   1. 投影仪 (projector)
   2. 窗帘电机 (curtain)
   3. 空调 (ac)
   4. 音频处理器 (audio)
   5. 显示设备 (display)
   6. 摄像机 (camera)
   7. 矩阵切换器 (matrix)
   8. 投影幕 (screen)
   9. 调光器 (lighting)
   10. 其他/自定义 (custom)
   ```

2. 询问品牌和型号（如：格力 YY1001/F）

3. 询问通信方式（串口RS232 / 串口RS485 / TCP / UDP / 红外）

4. 根据通信方式询问详细参数：
   - 串口：波特率、数据位、停止位、校验
   - TCP/UDP：IP地址、端口号
   - 红外：UserIRDB 路径格式

5. 询问指令表（功能: 指令，可多行）

6. 生成协议文件（基于 `_template.md` 格式）并写入对应目录

7. 更新 `_index.md` 添加新条目

8. 确认完成：
   ```
   已添加协议：[设备名] → core/protocols/[分类]/[文件名].md
   ```

---

## /mk-protocol-show — 查看协议详情

### 触发方式
```
/mk-protocol-show 格力空调      → 显示完整协议
/mk-protocol-show visca        → 显示 VISCA 协议
```

### 执行步骤

1. 在 `_index.md` 中搜索匹配的协议条目（模糊匹配）
2. 若找到唯一匹配：读取对应文件并输出
3. 若找到多个匹配：列出候选让用户确认
4. 若未找到：提示 "未找到，可用 /mk-protocol-add 添加"

### 输出格式

直接输出协议文件完整内容。

---

## /mk-protocol-update — 修正协议

### 触发方式
```
/mk-protocol-update 格力空调 关机指令改为 0xXXXX
/mk-protocol-update epson-eb 波特率改为 19200
```

### 执行步骤

1. 找到目标协议文件（同 /mk-protocol-show 步骤）
2. 读取文件内容
3. 理解修改意图，定位需要修改的位置
4. 执行修改（使用 Edit 工具）
5. 在文件末尾追加更新记录：
   ```
   - 2026-04-22: [修改描述]
   ```
6. 确认更新完成

---

## /mk-protocol-delete — 删除协议

### 触发方式
```
/mk-protocol-delete 格力空调    → 删除该协议
```

### 执行步骤

1. 找到目标协议文件
2. **二次确认**：`确认删除 [协议文件]？输入 Y 确认`
3. 用户确认后：
   - 删除协议文件（Bash rm 命令）
   - 更新 `_index.md` 删除对应条目
4. 确认完成

---

## /mk-protocol-import — 从 .cht 反向提取

### 触发方式
```
/mk-protocol-import path/to/project.cht
/mk-protocol-import 中控程序/401会议室程序/401会议室.cht
```

### 执行步骤

1. 读取指定 .cht 文件

2. 扫描提取以下调用：
   - `SEND_COM(dev, ch, "指令")` → 串口协议
   - `SEND_TCP(ip, port, "指令")` → TCP 协议
   - `SEND_UDP(ip, port, "指令")` → UDP 协议
   - `SEND_IRCODE(dev, ch, IRCODE<"...">)` → 红外协议
   - `SET_COM(dev, ch, baud, ...)` → 串口配置
   - `SEND_COM` 配合 `DATA_EVENT` → 有回传的串口

3. 按设备分组整理，输出提取结果让用户确认：
   ```
   ## 提取到的协议（请确认）

   ### 设备1：TR_0740S_COM2 (RS485:9600)
   | 功能（推测） | 指令 |
   |------------|------|
   | 开（BUTTON_EVENT tp,140）| 0xFFAA0400110213 |
   | 停（BUTTON_EVENT tp,141）| 0xFFAA0400110314 |
   | 关（BUTTON_EVENT tp,142）| 0xFFAA0400110112 |
   设备类型？（投影仪/窗帘/空调/...）
   品牌型号？
   ```

4. 用户确认并补充信息后，保存到协议库

---

## 协议存储规范

所有协议文件遵循 `_template.md` 格式：

```markdown
# [设备类型] - [品牌] ([型号])

## 基本信息
- 设备类型：xxx
- 通信方式：串口RS485 / TCP / UDP / 红外
- 波特率：9600（串口时）
- 数据位/停止位/校验：8/1/无

## 设备声明
[.cht 声明代码]

## 指令表
| 功能 | 指令 | 说明 |

## 代码示例
[.cht 调用代码]

## 适用型号
- xxx

## 更新记录
- 日期: 来源描述
```

文件名规范：`品牌-型号.md`（小写，连字符分隔，无空格）
