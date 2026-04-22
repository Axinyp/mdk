# MKControl Development Kit (MDK) — 中控开发工具链

## 1. 产品定位

**MDK 不是一个 skill，而是一套完整的中控开发插件系统。**

```
MKControl Development Kit (MDK)
├── 🔧 生成器 — /mk:control     从自然语言需求生成 XML + .cht
├── 📚 协议库 — /protocol-*    设备协议的增删查改导入
├── 🔍 CHT 参考 — /cht-*       设备类型、系统函数、代码模式查询
├── 🔍 XML 参考 — /xml-*       控件类型、属性规范、结构查询
└── ✅ 校验器 — 内置            生成后自动交叉校验 XML ↔ .cht
```

**核心闭环**：

```
导入已有项目(.cht) → 丰富协议库 → 接收新需求 → 生成 XML + .cht → 校验 → 交付
        ↑                                                              |
        └──────────────── 下一个项目复用知识 ←──────────────────────────┘
```

**与现有 skill 的关系**：MDK 完整包含 `mkcontrol-code-generator` 的所有内容（文档、模板、校验脚本、协议库），旧 skill 退役。

---

## 2. 命令体系

### 2.1 总览

| 类别 | 命令 | 说明 |
|------|------|------|
| **生成** | `/mk:control` | 从自然语言需求生成 Project.xml + .cht |
| **协议管理** | `/mk:protocol-list` | 列出所有协议（支持按分类过滤） |
| | `/mk:protocol-add` | 引导式添加新协议 |
| | `/mk:protocol-show` | 查看某个协议详情 |
| | `/mk:protocol-update` | 修正已有协议 |
| | `/mk:protocol-delete` | 删除协议条目 |
| | `/mk:protocol-import` | 从已有 .cht 文件反向提取协议 |
| **CHT 参考** | `/mk:cht-devices` | 设备类型（载体+元设备）与声明方式 |
| | `/mk:cht-functions` | 系统函数签名、参数、示例 |
| | `/mk:cht-patterns` | 常见代码模式（场景联动/WAIT链/CRC等） |
| **XML 参考** | `/mk:xml-controls` | 13 种控件的属性与用法 |
| | `/mk:xml-structure` | Project.xml 整体结构规范 |

### 2.2 `/mk:control` — 核心生成流程

```
用户自然语言描述
    ↓
[Phase 1] 解析提取
  - 识别设备（TS-9101/TR-0740S/触摸屏等）
  - 识别功能（灯光/窗帘/空调/信号源/电源等）
  - 提取参数（JoinNumber/串口指令/红外码/IP端口等）
  - 从协议库匹配已知设备协议
    ↓
[Phase 2] 确认清单（用户可读的表格）
  - 设备清单表
  - 功能与逻辑连接号表（用户指定的 + skill 自动分配的）
  - 页面结构
  - 缺失信息提示（需用户补充）
    ↓
[Phase 3] 用户确认/修改
  - 确认 → 进入生成
  - 修改 → 更新后重新确认
  - 补充缺失信息 → 更新后重新确认
    ↓
[Phase 4] 生成
  - Join Registry 最终锁定所有 JoinNumber
  - XML Renderer 生成 Project.xml（v4.1.9）
  - CHT Renderer 生成 output.cht
    ↓
[Phase 5] 交叉校验
  - XML 所有非零 JoinNumber 在 .cht 中有处理
  - .cht 所有 BUTTON_EVENT/LEVEL_EVENT 在 XML 中有控件
  - JoinNumber 唯一性检查
  - 页面跳转目标存在性检查
    ↓
输出: Project.xml + output.cht + 校验报告
```

### 2.3 `/mk:protocol-*` — 协议管理命令

**`/mk:protocol-list`**
```
/mk:protocol-list           → 全部协议（按分类）
/mk:protocol-list 窗帘      → 只看窗帘类
```

**`/mk:protocol-add`** — 引导式，逐步提问：
1. 设备类型？（投影仪/窗帘/空调/音频处理器/摄像机/矩阵/显示器/其他）
2. 品牌型号？
3. 通信方式？（串口RS232/串口RS485/TCP/UDP/红外）
4. 串口参数？（波特率/数据位/停止位/校验）
5. 指令表？（功能: 指令）
→ 保存到 `protocols/分类/品牌-型号.md` + 更新 `_index.md`

**`/mk:protocol-show`**
```
/mk:protocol-show 格力空调   → 显示完整协议详情
```

**`/mk:protocol-update`**
```
/mk:protocol-update 格力空调 关机指令改为 xxx   → 修正指令 + 加更新记录
```

**`/mk:protocol-delete`**
```
/mk:protocol-delete 格力空调   → 删除协议文件 + 更新索引
```

**`/mk:protocol-import`** — 从已有 .cht 反向提取：
```
/mk:protocol-import path/to/project.cht
→ 解析 SEND_COM/SEND_IRCODE/SEND_TCP/SEND_UDP 等调用
→ 列出提取到的协议让用户确认
→ 保存到协议库
```

### 2.4 `/mk:cht-*` — CHT 参考查询

**`/mk:cht-devices`**
```
/mk:cht-devices           → 设备类型总览（载体类型+元设备类型表）
/mk:cht-devices RELAY     → 继电器详情（声明方式+相关函数+使用场景）
/mk:cht-devices COM       → 串口详情
```

**`/mk:cht-functions`**
```
/mk:cht-functions          → 系统函数分类总览
/mk:cht-functions 触屏控制  → 该分类下所有函数列表
/mk:cht-functions SEND_COM → 单个函数签名+参数+示例
```

**`/mk:cht-patterns`**
```
/mk:cht-patterns           → 代码模式总览
/mk:cht-patterns 场景联动   → 场景切换的 WAIT 链+SET_BUTTON 互斥模式
/mk:cht-patterns 窗帘控制   → 串口指令+SEND_PICTURE 状态切换模式
/mk:cht-patterns 音量控制   → LEVEL_EVENT+SET_LEVEL+CRC 计算模式
```

### 2.5 `/mk:xml-*` — XML 参考查询

**`/mk:xml-controls`**
```
/mk:xml-controls           → 13 种控件总览表
/mk:xml-controls DFCButton → 按钮完整属性（子类型+核心属性+样式属性+XML 示例+对应 .cht 代码）
/mk:xml-controls DFCSlider → 滑动条属性（含 SliderLocationStyle 子样式）
```

**`/mk:xml-structure`**
```
/mk:xml-structure          → Project.xml 整体结构树+属性说明
```

---

## 3. 知识库结构

### 3.1 协议库（protocols/）

```
protocols/
  _index.md              ← 总索引（一行一条，快速定位）
  _template.md           ← 条目标准模板

  projector/             ← 投影仪
    pjlink-generic.md
    sony-vw-hw.md
    epson-eb.md
  curtain/               ← 窗帘电机
    generic-rs485.md
  ac/                    ← 空调(红外)
    gree-ir.md
  audio/                 ← 音频处理器/DSP
    bss-blu.md
  display/               ← 显示设备(电视/拼接屏)
  camera/                ← 摄像机
    visca-generic.md
  matrix/                ← 矩阵切换器
    kramer-p3000.md
  screen/                ← 投影幕/电动幕
  lighting/              ← 调光器
  custom/                ← 用户自定义（对话中新增）
```

**标准协议条目模板**（每个 .md 文件格式统一）：
```markdown
# [设备类型] - [品牌] ([型号])

## 基本信息
- 设备类型：xxx
- 通信方式：串口RS485 / TCP / UDP / 红外
- 波特率：9600（串口时）
- 数据位/停止位/校验：8/1/无

## 设备声明
SET_COM(dev, channel, 9600, 8, 0, 10, 0, 485);

## 指令表
| 功能 | 指令 | 说明 |
|------|------|------|
| 开 | 0xFFAA0400110213 | |
| 停 | 0xFFAA0400110314 | |
| 关 | 0xFFAA0400110112 | |

## 代码示例
SEND_COM(dev, channel, "0xFFAA0400110213");

## 适用型号
- xxx

## 更新记录
- 2026-04-22: 来源描述
```

**协议扩充工作流**：
```
场景1: 用户提到已知设备 → 查 _index.md → 找到 → 直接使用
场景2: 用户给了协议    → 按模板写入 → 更新索引 → 使用
场景3: 用户没给协议    → 停止生成，提问要求提供
场景4: 用户纠正协议    → 更新文件 + 加更新记录
```

### 3.2 语言规范（references/）

```
references/
  core/
    syntax-rules.md          ← .cht 语法规则（块顺序、括号、变量初始化等）
    code-patterns.md         ← 代码模式库（场景联动/WAIT链/CRC/IO检测等）
    device-types.md          ← 设备类型总览（载体+元设备）
  controls/
    controls-spec.md         ← 13 种控件完整属性规范
    xml-structure.md         ← Project.xml 结构规范（v4.1.9）
```

### 3.3 系统函数文档（docs/）

```
docs/
  系统函数库/
    串口控制函数.md
    继电器控制函数.md
    触屏控制函数.md           ← 含 SEND_PICTURE/SEND_PAGING/SEND_M2M_JNPUSH
    红外控制函数.md
    网络控制相关函数.md
    IO控制函数.md
    字符串操作相关函数.md
    获取时间相关函数.md
    TIMER、WAIT相关函数.md
    其他函数.md
  代码组织/                   ← DEFINE_* 块规范
  基本语法规则/               ← 类型、运算符、流程控制等
```

---

## 4. 生成器核心设计

### 4.1 用户输入方式

用户用**自然语言+行业术语**描述需求，例如：

> "我想用外围设备TS-9101控制灯光，触摸屏编号是10，TS-9101编号是1，灯光1逻辑连接号是103，灯光2逻辑连接号是105，实现全开全关和单独控制..."

skill 从中提取的结构化信息：
- 设备：`tp = T:10:TP`, `L9101_RELAY = L:1:RELAY`
- 功能：灯光1(J103, RELAY通道1), 灯光2(J105, RELAY通道2), 全开(J101), 全关(J102)
- 按钮类型：全开全关=NormalBtn, 单独=AutolockBtn

### 4.2 确认清单（生成前防错）

skill 解析后输出人可读的表格让用户核对，**不是 YAML，是表格**：

```markdown
## 请确认以下信息

### 设备清单
| 设备 | 类型 | 编号 | 用途 |
|------|------|------|------|
| 触摸屏 | TP | 板卡10 | 主控界面 |
| TS-9101 | RELAY | 板卡1 | 灯光+电源 |

### 功能与逻辑连接号
| 功能 | 逻辑号 | 来源 | 控制方式 |
|------|--------|------|---------|
| 灯光1 开/关 | 103 | 用户指定 | 继电器通道1, AutolockBtn |
| 灯光2 开/关 | 105 | 用户指定 | 继电器通道2, AutolockBtn |
| 灯光全开 | 101 | 自动分配 | NormalBtn |
| 灯光全关 | 102 | 自动分配 | NormalBtn |

### 页面结构
1. 主页 → 灯光控制面板

### 缺失信息
- ⚠️ 灯光按钮图片路径未提供（将使用纯色按钮）

---
以上信息是否正确？确认后开始生成。
```

### 4.3 Join Registry（JoinNumber 管理）

**混合模式**：用户指定的优先，未指定的自动分配。

```
1. 解析用户描述，提取所有显式指定的 JoinNumber
2. 对未指定的功能点，按号段规则自动分配
3. 冲突检测（用户指定的号和自动分配的号不能重复）
4. 输出完整 Join 映射表
5. XML Renderer 和 CHT Renderer 都从这张表读取
```

**默认号段规则**（自动分配时使用，不暴露给用户）：

| 号段 | 用途 |
|------|------|
| 0 | 无绑定（纯导航/静态控件） |
| 1-49 | 系统/导航/隐藏功能 |
| 100-139 | 灯光/窗帘控制 |
| 140-149 | 投影幕/场景模式 |
| 150-169 | 图片状态反馈 |
| 165-169 | 电源总开关 |
| 200-299 | 文本反馈（日期/星期等） |
| 210-239 | 信号源/空调/音量动作 |
| 300-499 | 状态显示文本 |
| 500-599 | 特殊场景/全局 |
| 1000-1099 | 滑条/模拟量 |
| 1100-1199 | 扩展功能 |
| 1200+ | 弹窗/倒计时 |

### 4.4 三层防错机制

| 层级 | 时机 | 作用 |
|------|------|------|
| **确认清单** | 生成前 | 用户核对参数是否正确 |
| **生成规则** | 生成中 | skill 内部标准化规则确保 XML/CHT 结构正确 |
| **交叉校验** | 生成后 | 自动检查 XML 和 .cht 的 JoinNumber 一致性 |

**交叉校验项**：

| 校验项 | 级别 | 备注 |
|--------|------|------|
| XML 非零 Join 在 .cht 中有事件处理 | Critical | 纯导航按钮（只有 JumpPage）豁免，降为 Warning |
| .cht 事件的 Join 在 XML 中有控件 | **Warning** | 虚拟通道/外部触发合法，不强制 Critical |
| JoinNumber 无冲突（同号不同语义） | Critical | |
| JumpPage/SEND_PAGING 目标页面存在 | Warning | |
| DEFINE_DEVICE 覆盖所有使用的设备 | Critical | |
| MutualLockBtn 有 MutualLockGroup | Warning | |
| DEFINE_START 中 SET_COM 覆盖所有串口 | Warning | |

> ⚠️ **cross_validate.py 注意**：解析 .cht 前必须剥离 `//` 单行注释，否则注释掉的事件会被误识别为有效事件。

### 4.5 输出格式

- **XML**: 统一 Version="4.1.9"，分辨率可配置（默认 2560x1600）
- **CHT**: Creator 语言，块顺序严格遵守规范，通过 validate.py 校验

---

## 5. 控件规范（13 种）

| 控件类型 | XML Type | 交互性 | JoinNumber 用法 |
|---------|----------|--------|----------------|
| 按钮 | DFCButton | 可点击 | BUTTON_EVENT + SET_BUTTON |
| 文本框 | DFCTextbox | 显示/反馈 | SEND_TEXT |
| 可编辑文本框 | DFCEditTextbox | 用户输入 | JoinNumber + TextSendJoinNumber（双通道） |
| 密码输入框 | DFCPassword | 密码输入 | JoinNumber |
| 图片 | DFCPicture | 多状态显示 | SEND_PICTURE 切换索引 |
| 滑动条 | DFCSlider | 可拖动 | LEVEL_EVENT 输入 + SET_LEVEL 反馈（双向同号） |
| 进度条 | DFCTaskBar | 只读进度 | SET_LEVEL 单向 |
| 时间 | DFCTime | 自动时钟 | 仅显示，TimeType="HH:mm" |
| 视频 | DFCVideo | 流媒体播放 | JoinNumber |
| 外部应用 | DFCApp | 嵌入外部程序 | **注意：属性用 camelCase（与其他控件不同）** |
| 页面 | DFCForm | 页面容器 | — |
| 弹窗 | DFCMessegeToast | 模态弹窗 | DisplayTime 自动关闭 |

**按钮子类型**：
| BtnType | 行为 | 典型用途 | .cht 模式 |
|---------|------|---------|----------|
| NormalBtn | 按下松开 | 灯光全开/全关、窗帘开停关 | PUSH() { ... } |
| AutolockBtn | PUSH=开, RELEASE=关 | 电源通道、静音、单路灯 | PUSH() { on } RELEASE() { off } |
| MutualLockBtn | 同组互斥 | 场景切换、信号源选择 | PUSH() + SET_BUTTON 互斥 |
| LoginBtn | 登录专用 | 密码验证页 | JumpPage 跳转 |

**JoinNumber 绑定类型（6 种通道）**：
| 通道类型 | XML → .cht | 说明 |
|---------|------------|------|
| 按钮事件 | DFCButton.JoinNumber → BUTTON_EVENT(tp, N) | 用户按下触发 |
| 滑条事件 | DFCSlider.JoinNumber → LEVEL_EVENT(tp, N) | 用户拖动触发 |
| 按钮状态反馈 | .cht SET_BUTTON(tp, N, state) → DFCButton | 代码控制按钮状态 |
| 文本反馈 | .cht SEND_TEXT(tp, N, text) → DFCTextbox | 代码推送文字 |
| 滑条反馈 | .cht SET_LEVEL(tp, N, value) → DFCSlider | 代码设置滑条位置 |
| 图片切换 | .cht SEND_PICTURE(tp, N, index) → DFCPicture | 代码切换图片 |

---

## 6. 图片资源策略

- 用户提供图片目录路径，skill 在 XML 中生成相对路径引用（`.\xxx.png`）
- 未提供图片时，使用颜色 + 文字 + Radius 生成纯色按钮（功能可用）
- 不维护内置图标库

---

## 7. 项目结构（跨平台架构）

### 7.1 架构分层

```
MDK Core (平台无关)  ←  所有平台共享的知识库 + 校验 + 生成规则
      ↓
Platform Adapters    ←  每个平台一个适配层
      ↓
┌──────────┬──────────┬──────────┬──────────┬──────────┐
│ Claude   │ OpenClaw │ Hermes   │ Codex    │ MCP      │
│ Code     │ Plugin   │ Plugin   │ CLI      │ Server   │
│ SKILL.md │ .ts+json │ .py+yaml │ AGENTS.md│ HTTP/SSE │
└──────────┴──────────┴──────────┴──────────┴──────────┘
                                                ↑
                                          Web 前端连接此处
```

### 7.2 完整目录结构

```
mdk/
├── core/                                ← 平台无关核心（所有平台共享）
│   │
│   ├── protocols/                       ← 协议知识库
│   │   ├── _index.md                    ← 总索引（一行一条，快速定位）
│   │   ├── _template.md                 ← 标准条目模板
│   │   ├── projector/                   ← 投影仪
│   │   │   ├── pjlink-generic.md
│   │   │   ├── sony-vw-hw.md
│   │   │   └── epson-eb.md
│   │   ├── curtain/                     ← 窗帘电机
│   │   │   └── generic-rs485.md
│   │   ├── ac/                          ← 空调(红外)
│   │   │   └── gree-ir.md
│   │   ├── audio/                       ← 音频处理器/DSP
│   │   │   └── bss-blu.md
│   │   ├── display/                     ← 显示设备
│   │   ├── camera/                      ← 摄像机
│   │   │   └── visca-generic.md
│   │   ├── matrix/                      ← 矩阵切换器
│   │   │   └── kramer-p3000.md
│   │   ├── screen/                      ← 投影幕
│   │   ├── lighting/                    ← 调光器
│   │   └── custom/                      ← 用户自定义（对话中新增）
│   │
│   ├── references/                      ← 语言与控件规范
│   │   ├── core/
│   │   │   ├── syntax-rules.md          ← .cht 语法规则
│   │   │   ├── code-patterns.md         ← 代码模式库
│   │   │   └── device-types.md          ← 设备类型总览
│   │   └── controls/
│   │       ├── controls-spec.md         ← 13 种控件完整属性规范
│   │       └── xml-structure.md         ← Project.xml 结构规范 (v4.1.9)
│   │
│   ├── docs/                            ← 系统函数文档（从旧 skill 迁移）
│   │   ├── 系统函数库/*.md
│   │   ├── 代码组织/*.md
│   │   └── 基本语法规则/*.md
│   │
│   ├── scripts/                         ← 校验工具 (Python, 跨平台可用)
│   │   ├── validate.py                  ← .cht 语法校验（14 项）
│   │   ├── check_functions.py           ← 函数调用校验
│   │   └── cross_validate.py            ← XML ↔ .cht 交叉校验
│   │
│   └── skills/                          ← 通用 SKILL.md 文件（三平台共享格式）
│       ├── mkcontrol/SKILL.md           ← 主生成器 skill
│       ├── protocol/SKILL.md            ← 协议管理 skill
│       ├── cht-ref/SKILL.md             ← CHT 参考查询 skill
│       └── xml-ref/SKILL.md             ← XML 参考查询 skill
│
├── adapters/                            ← 平台适配层
│   │
│   ├── claude-code/                     ← Claude Code 适配
│   │   ├── install.sh                   ← 安装脚本: symlink core/ 到 ~/.claude/skills/mdk/
│   │   └── README.md
│   │
│   ├── openclaw/                        ← OpenClaw 插件
│   │   ├── openclaw.plugin.json         ← 插件清单
│   │   ├── package.json                 ← npm 包定义 (含 openclaw metadata)
│   │   ├── index.ts                     ← definePluginEntry() + 注册 12 个 tools
│   │   └── README.md
│   │
│   ├── hermes/                          ← Hermes Agent 插件
│   │   ├── plugin.yaml                  ← 插件清单
│   │   ├── __init__.py                  ← register(ctx) + 注册 tools + 注册 skills
│   │   ├── schemas.py                   ← 12 个工具的 JSON Schema
│   │   ├── tools.py                     ← 工具处理函数（调用 core/）
│   │   └── README.md
│   │
│   ├── codex/                           ← Codex CLI 适配
│   │   ├── AGENTS.md                    ← Codex 指令文件（引用 core/ 知识库）
│   │   └── README.md
│   │
│   └── mcp-server/                      ← MCP Server（网页调用的核心）
│       ├── server.py                    ← MCP Server 实现（12 个 tools）
│       ├── requirements.txt             ← Python 依赖
│       ├── Dockerfile                   ← 容器化部署
│       └── README.md
│
└── web/                                 ← Web 前端（Phase 4）
    └── (后续设计)
```

### 7.3 MCP Server 注册的 Tools

MCP Server 是网页调用的核心，注册以下 12 个工具：

```python
tools = [
    # 生成
    "mkcontrol_generate",         # 解析需求 → 输出确认清单
    "mkcontrol_confirm",          # 确认后执行 → 输出 XML + .cht

    # 协议管理
    "protocol_list",              # 列出协议（支持分类过滤）
    "protocol_add",               # 添加新协议
    "protocol_show",              # 查看协议详情
    "protocol_update",            # 修正协议
    "protocol_delete",            # 删除协议
    "protocol_import",            # 从 .cht 反向提取

    # 参考查询
    "cht_devices",                # 设备类型查询
    "cht_functions",              # 系统函数查询
    "cht_patterns",               # 代码模式查询
    "xml_controls",               # 控件类型查询
    "xml_structure",              # XML 结构查询

    # 校验
    "validate_cht",               # 校验 .cht 文件
    "cross_validate",             # 交叉校验 XML + .cht
]
```

### 7.4 平台适配对比

| 维度 | Claude Code | OpenClaw | Hermes | Codex | MCP Server |
|------|------------|----------|--------|-------|-----------|
| 安装方式 | `install.sh` | `openclaw plugins install` | 放 `~/.hermes/plugins/` 或 pip | 复制 AGENTS.md | `python server.py` 或 Docker |
| Skill 格式 | SKILL.md (直接复用) | SKILL.md (自动发现) | SKILL.md (register_skill) | AGENTS.md (改写) | 不需要 (走 tool 协议) |
| Tool 注册 | 无需 (Claude 能力) | `api.registerTool()` TS | `ctx.register_tool()` PY | 无需 (用 Bash) | MCP tool 协议 |
| 知识库访问 | 直接读文件 | 通过 tool handler | 通过 tool handler | 直接读文件 | 通过 tool handler |
| Web 可用 | 否 | 自带 Dashboard | 兼容 Open WebUI | 否 | **任何 MCP Client** |

---

## 8. 实施步骤

### Phase 1：Core 知识库搭建

**Step 1: 目录初始化 + 旧 skill 迁移**
- 创建 `mdk/core/` 目录结构
- 从 `mkcontrol-code-generator` 复制 docs/、scripts/、references/ 到 core/
- 预期产物：core/ 基础框架

**Step 2: 协议库重构**
- 将旧 `references/devices/*.md` 拆分到 `core/protocols/` 按功能分类
- 统一条目格式（创建 `_template.md`）
- 从 401 .cht 实码提取协议补充入库（窗帘/空调/音频处理器）
- 建立 `_index.md` 总索引
- 预期产物：完整的 core/protocols/ 目录

**Step 3: 控件规范 + XML 结构**
- 基于 `基本控件分类.md` 编写 `controls-spec.md`（13 种控件完整属性）
- 基于 401 Project.xml 编写 `xml-structure.md`（v4.1.9 结构规范）
- 预期产物：core/references/controls/ 目录

**Step 4: 代码模式库 + API 文档补充**
- 从 401 .cht 提取标准代码模式（场景联动/WAIT链/CRC校验/IO检测等）
- 补充新发现的 API 到系统函数文档（SEND_PICTURE/SEND_PAGING/SEND_M2M_JNPUSH/LEVEL_EVENT 等）
- 预期产物：更新后的 core/references/core/ 和 core/docs/

### Phase 2：Skill 命令实现（Claude Code 首发）

**Step 5: 参考查询 skill**
- 实现 `core/skills/cht-ref/SKILL.md`（/mk:cht-devices, /mk:cht-functions, /mk:cht-patterns）
- 实现 `core/skills/xml-ref/SKILL.md`（/mk:xml-controls, /mk:xml-structure）
- 预期产物：两个 SKILL.md 文件

**Step 6: 协议管理 skill**
- 实现 `core/skills/protocol/SKILL.md`（/mk:protocol-list/add/show/update/delete/import）
- 预期产物：protocol SKILL.md

**Step 7: 主生成器 skill + 交叉校验器**
- 实现 `core/skills/mkcontrol/SKILL.md`（/mk:control 入口，含生成流程+确认清单+Join Registry）
- 实现 `core/scripts/cross_validate.py`（XML ↔ .cht 交叉校验）
- 预期产物：主 SKILL.md + 校验脚本

### Phase 3：Claude Code 适配 + 验证

**Step 8: Claude Code 命令注册** ✅ 已完成（2026-04-22）
- ~~编写 `adapters/claude-code/install.sh`（symlink core/ 到 ~/.claude/skills/mdk/）~~
- **实际方式**：在 `~/.claude/commands/mk/` 下创建 12 个 `.md` 命令文件（非 symlink 方案）
  - Claude Code 从 `~/.claude/commands/<namespace>/` 自动发现斜杠命令
  - 命名约定：`commands/mk/control.md` → 可调用 `/mk:control`（namespace:command）
  - 每个命令文件读取对应 SKILL.md 并执行工作流
- **实际产物**：`~/.claude/commands/mk/` 下 12 个命令文件，全部立即生效

**Step 9: 回归验证** ✅ 已完成（2026-04-22）
- 用 401 案例做端到端测试：自然语言 → 确认清单 → XML + .cht → 交叉校验 → 与原文件对比
- 用之前用户的灯光描述做测试
- 确认旧 skill 所有能力在 MDK 中可用
- **实际产物：验证报告**
  - `validate.py`：401.cht 报告 7 个未初始化变量（`int i/j/len/CRC/CRC_L/CRC_H/tmp`），为真实代码质量问题（参考代码本身的瑕疵），非工具误报
  - `cross_validate.py`：修复 3 个 Bug 后通过验证（Critical=0, Warning=44 均为预期良性）
    - Bug 1：未剥离 `//` 单行注释导致注释掉的 `BUTTON_EVENT` 被误识别（48 个假 Critical）
    - Bug 2：CHT→XML 缺控件误报 Critical（虚拟通道/外部触发属合法设计，降为 Warning）
    - Bug 3：纯导航按钮（JumpPage only）无 CHT 处理被误报 Critical（加豁免逻辑）

**Step 10: 旧 skill 退役** ✅ 已完成（2026-04-22）
- 确认 MDK 完全覆盖旧 skill 功能后，删除 `skills/mk:control-code-generator/`
- **实际产物：干净的 skill 目录**（`mkcontrol-code-generator` 已删除）

### Phase 4：MCP Server 适配（网页调用基础）

**Step 11: MCP Server 实现** ✅ 已完成（2026-04-22）
- `adapters/mcp-server/server.py` 832行，14 个 MCP tools（stdio 协议）
- 验证：`initialize` 握手 ✅、`tools/list` 14个工具 ✅、`protocol_list` 调用 ✅、核心逻辑直测 ✅
- **实际产物**：可运行的 MCP Server，依赖仅 `mcp>=1.0.0`

**Step 12: MCP Server 部署** ✅ 已完成（2026-04-22）
- Dockerfile 已修复（build context 从 `mdk/` 根目录，`COPY ../../core` 路径错误已改正）
- 注册到 `~/.claude/claude.json`（`mcpServers.mdk` 条目）
- `adapters/claude-code/install.sh` 更新：安装时自动注册 MCP，卸载时自动移除
- **实际产物**：Claude Code 重启后可通过 MCP 调用 MDK 所有工具

### Phase 5：多平台适配

**Step 13: OpenClaw 插件**
- 实现 `adapters/openclaw/`（openclaw.plugin.json + index.ts）
- `definePluginEntry()` 注册 12 个 tools + 引用 core/skills/
- 预期产物：可安装的 OpenClaw 插件

**Step 14: Hermes Agent 插件**
- 实现 `adapters/hermes/`（plugin.yaml + __init__.py + schemas.py + tools.py）
- `register(ctx)` 注册 tools + skills
- 预期产物：可安装的 Hermes 插件

**Step 15: Codex CLI 适配**
- 编写 `adapters/codex/AGENTS.md`（引用 core/ 知识库路径）
- 预期产物：AGENTS.md 文件

### Phase 6：Web 前端（后续）

**Step 16: Web 前端设计与实现**
- 基于 MCP Server 的 tool 接口
- 提供对话式交互 + 文件下载（XML/.cht）+ 协议管理 UI
- 具体技术选型待定
- 预期产物：Web 应用

### 实施优先级

```
Phase 1-3 (立即)：Core + Claude Code    ← 你现在用的环境，先跑通
Phase 4   (紧接)：MCP Server            ← 网页调用的基础，工作量不大
Phase 5   (之后)：OpenClaw + Hermes     ← 扩展平台
Phase 6   (最终)：Web 前端               ← 面向终端用户
```

---

## 9. 风险与缓解

| 风险 | 严重度 | 缓解措施 |
|------|--------|----------|
| 自然语言解析不准确 | High | 确认清单让用户核对 + 缺失信息主动追问 |
| JoinNumber XML/CHT 失同步 | Critical | Join Registry 单一数据源 + 交叉校验 |
| 协议库条目格式不一致 | Medium | 标准模板 + /mk:protocol-add 引导式录入 |
| 场景联动逻辑复杂 | High | 代码模式库提供标准化 WAIT 链模板 |
| DFCApp 属性名 camelCase 异常 | Medium | XML 生成时对 DFCApp 做特殊映射 |
| 红外码库依赖 | Medium | 协议库存储 IRCODE 格式，未知则停止并提问 |
| 图片资源缺失 | Low | 退化为纯色+文字按钮，功能不受影响 |
| 跨平台适配器维护成本 | Medium | core/ 共享知识库，adapter 只做薄包装 |
| MCP Server 安全性 | High | 网页部署需加认证层，MCP tool 做输入校验 |

---

## 10. 决策记录

| 问题 | 决策 | 理由 |
|------|------|------|
| 新旧 skill 关系 | MDK 完整包含旧 skill，旧 skill 退役 | 单一入口，无歧义，避免文档不同步 |
| XML 版本 | 统一 v4.1.9 | v2 是 v4.1.9 子集，以 401 实案为准 |
| 用户输入方式 | 自然语言 + 确认清单 | 用户是运维，不会写 YAML/JSON |
| JoinNumber 管理 | 混合模式：用户指定优先，未指定自动分配 | 尊重老运维习惯，降低新用户门槛 |
| 图片策略 | 用户提供路径，不内置图标库 | 避免资源同步负担 |
| 页面结构 | 根据用户需求动态生成 | 不预设固定房型模板 |
| 协议库 | 按设备功能分目录 + 标准模板 + 总索引 | 可无限扩展，用得越多越丰富 |
| 产品形态 | 跨平台插件系统，core/ 共享 + adapters/ 适配 | 一套核心多平台复用 |
| 跨平台策略 | core/ 平台无关 + 5 个 adapter | Claude Code/OpenClaw/Hermes/Codex/MCP Server |
| 网页方案 | MCP Server 作为网页调用入口 | 标准协议，任何 MCP Client 可连接 |
| 实施顺序 | Phase 1-3 Claude Code → Phase 4 MCP → Phase 5 多平台 → Phase 6 Web | 先跑通再扩展 |

---

## SESSION_ID（供 /ccg:execute 使用）
- CODEX_SESSION: 019db2dc-a24e-7dc2-930f-64e750efe6cb
- GEMINI_SESSION: (需重建)
