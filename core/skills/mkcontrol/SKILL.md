---
name: "mdk:mkcontrol"
description: "MKControl 中控系统开发套件核心生成器：从自然语言需求同时生成 Project.xml（触摸屏界面）和 .cht（控制程序）。当用户描述会议室/展厅/教室等中控需求时调用。支持命令：/mk-control"
commands:
  - /mk-control
---

# MKControl 主生成器 Skill

## 职责

根据用户自然语言需求，生成配套的 `Project.xml`（界面）+ `.cht`（控制程序），确保 JoinNumber 双文件一致。

---

## /mk-control — 核心生成命令

### 触发方式
```
/mk-control 我想控制灯光、窗帘、投影仪...
/mk-control                   → 进入引导式提问模式
```

---

## 执行流程（5 阶段）

### Phase 1：解析提取

从用户自然语言中识别：

**设备识别**：
- 触摸屏型号和板卡号（如 TS-1070C，板卡10）
- 外围设备型号和板卡号（如 TS-9101 RELAY，板卡1）
- 通信模块（如 TR-0740S 的 COM/IR 通道）

**功能识别**：
- 灯光（继电器）、窗帘（RS485）、空调（红外）
- 信号源切换（矩阵）、投影仪（串口/TCP）
- 音量控制（滑条/DSP）、场景模式（联动）
- 电源管理、视频会议、时间显示

**协议匹配**：
- 查询 `core/protocols/_index.md` 匹配已知设备协议
- 若匹配到 → 使用协议库中的指令
- 若未匹配 → 记录为「需要用户提供协议」

### Phase 2：确认清单（用户核对）

输出人可读的表格，不使用 YAML/JSON：

```markdown
## 请确认以下信息

### 设备清单
| 设备 | 类型 | 编号 | 通信方式 |
|------|------|------|---------|
| 触摸屏 | TP | 板卡10 | 内置 |
| TS-9101 | RELAY | 板卡1 | 内置继电器 |
| TR-0740S | 扩展模块 | 板卡2 | 内置 |
| 窗帘电机 | COM RS485 | TR-0740S 通道2 | RS485:9600 |

### 功能与逻辑连接号
| 功能 | JoinNumber | 来源 | 控件类型 | 控制方式 |
|------|-----------|------|---------|---------|
| 灯光1 开/关 | 103 | 用户指定 | DFCButton | AutolockBtn, 继电器通道1 |
| 灯光全开 | 101 | 自动分配 | DFCButton | NormalBtn |
| 窗帘总开 | 140 | 自动分配 | DFCButton | NormalBtn |
| 音量调节 | 1000 | 自动分配 | DFCSlider | LEVEL_EVENT |

### 页面结构
1. 引导页 → 主页（点击跳转）
2. 主页 → 灯光控制、窗帘控制、空调控制
3. 弹窗 → 电源确认

### 图片资源
- 用户提供图片目录：[路径] 或 [未提供，使用纯色按钮]

### 缺失信息（需用户补充）
- ⚠️ 投影仪品牌型号未知（无法确定串口指令格式）
- ⚠️ 空调 UserIRDB 路径未提供

---
以上信息是否正确？确认后开始生成，或直接告诉我需要修改的地方。
```

**等待用户确认或修改，收到确认后进入 Phase 3。**

### Phase 3：Join Registry（锁定所有 JoinNumber）

**混合分配规则**：
1. 用户指定的 JoinNumber → 直接使用，记录为「用户指定」
2. 未指定的功能 → 按号段规则自动分配，检查不冲突

**默认号段**（不向用户暴露，仅内部使用）：

| 号段 | 用途 |
|------|------|
| 0 | 无绑定（纯导航/静态控件） |
| 1-49 | 系统/导航/隐藏功能 |
| 100-139 | 灯光/窗帘控制 |
| 140-149 | 投影幕/场景模式 |
| 150-169 | 图片状态反馈 |
| 165-169 | 电源总开关 |
| 200-299 | 文本反馈 |
| 210-239 | 信号源/空调/音量动作 |
| 300-499 | 状态显示文本 |
| 500-599 | 特殊场景/全局 |
| 1000-1099 | 滑条/模拟量 |
| 1100-1199 | 扩展功能 |
| 1200+ | 弹窗/倒计时 |

**冲突检测**：若用户指定的号和自动分配的号冲突，自动调整自动分配的号，并在确认清单中告知用户。

**最终 Join 映射表**（内部数据结构，不输出给用户）：
```
{103: {name: "灯光1", type: "BUTTON_EVENT", desc: "灯光1开关"}}
{140: {name: "窗帘总开", type: "BUTTON_EVENT", desc: "窗帘全开"}}
{1000: {name: "音量", type: "LEVEL_EVENT", desc: "音量滑条"}}
```

### Phase 4：双文件生成

**生成顺序**：先生成 Join Registry，再同时输出两个文件

#### 4a. Project.xml 生成规则

- 版本：`Version="4.1.9"`（固定）
- 分辨率：2560×1600（默认）或用户指定
- 颜色格式：`#AARRGGBB`
- 图片路径：`.\图片名.png`（相对路径）

**控件映射规则**：

| 功能类型 | 控件选择 | 配置 |
|---------|---------|------|
| 开关类（切换） | DFCButton AutolockBtn | JoinNumber=N |
| 全开/全关 | DFCButton NormalBtn | JoinNumber=N |
| 场景选择 | DFCButton MutualLockBtn | JoinNumber=N, MutualLockGroup=场景 |
| 状态文本显示 | DFCTextbox | JoinNumber=N（接收 SEND_TEXT） |
| 状态图片显示 | DFCPicture | JoinNumber=N（接收 SEND_PICTURE），ImagePictures=[图片列表] |
| 音量/亮度滑条 | DFCSlider | JoinNumber=N（双向） |
| 时间显示 | DFCTime | JoinNumber=0, TimeType="HH:mm" |
| 页面跳转 | DFCButton NormalBtn | JumpPage=目标页面名 |
| 页面容器 | DFCForm | 页面名，BkImage=背景图 |
| 弹窗 | DFCMessegeToast | DisplayTime=0或N秒 |

**无图片退化规则**：
- 有图 → `NormalImage=".\xxx.png"` + `PressImage=".\xxx_press.png"`
- 无图 → `NormalColor="#FF666666"` + `PressColor="#FF888888"` + `Text="功能名"` + `Radius="10"`

#### 4b. .cht 文件生成规则

读取 `core/references/core/syntax-rules.md` 和 `core/references/core/code-patterns.md` 确保规范。

**块顺序严格遵守**：
```
DEFINE_DEVICE
DEFINE_COMBINE    (可选)
DEFINE_CONSTANT   (仅整型)
DEFINE_VARIABLE   (必须赋初值)
DEFINE_FUNCTION
DEFINE_TIMER      (可选)
DEFINE_START
DEFINE_EVENT
```

**设备声明规则**：
- 触摸屏：`tp = T:板卡号:TP;`
- 外围串口：`L9101_COM = L:板卡号:COM;` 或 `TR_COM = L:扩展模块号:COM;`
- 继电器：`L9101_RELAY = L:板卡号:RELAY;`
- 红外：`TR_0740S_IR = L:板卡号:IR;`

**DEFINE_START 初始化**：
- 所有串口设备调用 `SET_COM()`

**BUTTON_EVENT 模板**（根据功能类型选择）：
- NormalBtn：`PUSH() { ... }`
- AutolockBtn：`PUSH() { on; SET_BUTTON(tp,N,1); } RELEASE() { off; SET_BUTTON(tp,N,0); }`
- MutualLockBtn：`PUSH() { ...; SET_BUTTON(tp,N,1); SET_BUTTON(tp,其他N,0); }`

### Phase 5：交叉校验

生成完成后自动执行校验：

| 校验项 | 级别 | 说明 |
|--------|------|------|
| XML 非零 JN 在 .cht 中有 BUTTON/LEVEL_EVENT | Critical | 确保按钮都有事件处理 |
| .cht 中事件的 JN 在 XML 中有控件 | Critical | 确保没有孤立事件 |
| JoinNumber 唯一性 | Critical | 同号不同语义报错 |
| JumpPage 目标页面存在 | Warning | 跳转到不存在的页面 |
| DEFINE_DEVICE 覆盖所有使用设备 | Critical | 设备未声明 |
| SET_COM 覆盖所有串口 | Warning | 串口未初始化 |

---

## 缺失信息处理规则

| 缺失信息 | 处理方式 |
|---------|---------|
| 设备板卡号 | 在清单中标注 ⚠️，生成时用占位符 `TODO:板卡号` |
| 设备通信协议 | 停止生成，必须先获取协议信息，不猜测指令 |
| 图片路径 | 退化为纯色按钮，功能不受影响 |
| 页面数量/名称 | 根据功能自动规划，在清单中展示让用户确认 |

---

## 知识库路径（生成时必读）

| 需要 | 读取文件 |
|------|---------|
| 协议匹配 | `core/protocols/_index.md` → 对应 .md |
| 控件规范 | `core/references/controls/controls-spec.md` |
| XML 结构 | `core/references/controls/xml-structure.md` |
| 语法规则 | `core/references/core/syntax-rules.md` |
| 代码模式 | `core/references/core/code-patterns.md` |
| 系统函数 | `core/docs/系统函数库/对应分类.md` |

---

## 输出格式

```
## 确认完成，开始生成...

### Project.xml
[完整 XML 文件内容]

### output.cht
[完整 .cht 文件内容]

### 校验报告
- Critical: 0 项
- Warning: N 项（列出具体内容）

### 待确认事项
- [ ] TODO:板卡号 × N 处需要替换
- [ ] 图片路径待用户提供后替换 .\xxx.png
```
