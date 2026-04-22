---
name: "mdk:cht-ref"
description: "MKControl .cht 语言参考查询：设备类型、系统函数、代码模式。当用户执行 /mk-cht-devices、/mk-cht-functions 或 /mk-cht-patterns 命令时调用。"
commands:
  - /mk-cht-devices
  - /mk-cht-functions
  - /mk-cht-patterns
---

# CHT 参考查询 Skill

## 职责

查询 MKControl Creator 语言（.cht）的参考文档，包括设备类型、系统函数签名、代码模式。

---

## /mk-cht-devices — 设备类型查询

### 触发方式
```
/mk-cht-devices              → 显示所有设备类型总览
/mk-cht-devices RELAY        → 继电器详情
/mk-cht-devices COM          → 串口详情
/mk-cht-devices IR           → 红外详情
/mk-cht-devices TP           → 触摸屏详情
```

### 执行步骤

1. 读取 `core/references/core/syntax-rules.md` 中设备命名格式章节
2. 读取 `core/docs/系统函数库/` 中对应设备类型的函数文件
3. 输出格式：

```
## [设备类型] — 设备声明与函数

### 声明格式
[声明语法示例]

### 常用函数
| 函数 | 参数 | 说明 |
|------|------|------|
| ... | ... | ... |

### 使用示例
[代码示例]
```

### 设备类型速查表

| 声明符号 | 设备类型 | 声明格式 |
|---------|---------|---------|
| `TP` | 触摸屏 | `tp = T:设备号:TP;` |
| `COM` | 串口 | `M_COM = M:1002:COM;` 或 `TR_COM = L:N:COM;` |
| `RELAY` | 继电器 | `L9101_RELAY = L:1:RELAY;` |
| `IR` | 红外 | `M_IR = M:1004:IR;` 或 `TR_IR = L:N:IR;` |
| `IO` | IO | `M_IO = M:1:IO;` |
| `DSP` | 音频处理 | `M_DSP = M:N:DSP;` |
| `MATRIX` | 矩阵 | `M_MATRIX = M:N:MATRIX;` |
| `CAM` | 摄像机 | `M_CAM = M:N:CAM;` |

---

## /mk-cht-functions — 系统函数查询

### 触发方式
```
/mk-cht-functions                → 系统函数分类总览
/mk-cht-functions 串口控制        → 串口函数列表
/mk-cht-functions SEND_COM       → 单个函数详情
/mk-cht-functions 触屏控制        → 触屏控制函数
```

### 执行步骤

1. 若无参数或按分类查询：列出 `core/docs/系统函数库/` 下所有文件名
2. 若按分类查询：读取对应的 `.md` 文件
3. 若按函数名查询：在所有函数文件中搜索该函数名
4. 输出格式：

```
## [函数名]

**所属模块**：串口控制 / 继电器控制 / 触屏控制 / ...
**签名**：函数名(参数类型 参数名, ...)
**返回值**：void / int / string

### 参数说明
| 参数 | 类型 | 说明 |
|------|------|------|

### 示例
[代码示例]

### 注意事项
[注意点]
```

### 函数分类总览

| 分类 | 文件 | 常用函数 |
|------|------|---------|
| 串口控制 | `串口控制函数.md` | SEND_COM, SET_COM, DATA_EVENT |
| 继电器控制 | `继电器控制函数.md` | ON_RELAY, OFF_RELAY |
| 触屏控制 | `触屏控制函数.md` | SEND_TEXT, SET_BUTTON, SET_LEVEL, SEND_PICTURE, SEND_PAGING, LEVEL_EVENT |
| 红外控制 | `红外控制函数.md` | SEND_IRCODE, IRCODE<> |
| 网络控制 | `网络控制相关函数.md` | SEND_TCP, SEND_UDP |
| IO控制 | `IO控制函数.md` | SET_IO_DIR, DATA_EVENT(M_IO) |
| 字符串操作 | `字符串操作相关函数.md` | ITOA, ATOI, LEFT, RIGHT, MID, LEN |
| 时间 | `获取时间相关函数.md` | GET_DATE, GET_TIME |
| 定时器/WAIT | `TIMER、WAIT相关函数.md` | START_TIMER, CANCEL_TIMER, WAIT |
| 其他 | `其他函数.md` | TRACE, BYTES_TO_STRING, SAVE_PARAM, LOAD_PARAM |

---

## /mk-cht-patterns — 代码模式查询

### 触发方式
```
/mk-cht-patterns                 → 所有模式总览
/mk-cht-patterns 场景联动         → 场景切换的 WAIT 链 + SET_BUTTON 互斥
/mk-cht-patterns 窗帘控制         → 窗帘 RS485 + SEND_PICTURE 状态
/mk-cht-patterns 音量控制         → LEVEL_EVENT + SET_LEVEL + CRC
/mk-cht-patterns 投影仪           → 串口控制 + DATA_EVENT 响应
/mk-cht-patterns 红外空调         → IRCODE + UserIRDB 格式
```

### 执行步骤

1. 读取 `core/references/core/code-patterns.md`
2. 根据关键词定位对应模式章节
3. 输出完整模式代码 + 关键说明

### 模式速查

| 模式 | 关键字 |
|------|-------|
| 串口设备控制 | 投影仪, 矩阵, 摄像机, 串口, COM |
| 继电器灯光/幕布 | 继电器, 灯光, 幕布, RELAY, ON_RELAY |
| 场景联动 | 场景, WAIT链, 互斥, MutualLockBtn |
| 滑条音量 | 音量, 滑条, LEVEL_EVENT, SET_LEVEL |
| 红外空调 | 红外, 空调, IRCODE, UserIRDB, IR |
| 图片状态切换 | 图片, SEND_PICTURE, 状态反馈 |
| 窗帘RS485 | 窗帘, RS485, 0xFFAA |
| HTTP控制 | HTTP, 视频会议, loopback, 71455 |
| IO检测 | IO, DATA_EVENT(M_IO), 传感器 |
| 参数持久化 | 存储, SAVE_PARAM, LOAD_PARAM |
