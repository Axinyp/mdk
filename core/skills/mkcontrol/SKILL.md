---
name: "mdk:mkcontrol"
description: "MKControl 中控开发套件：生成 Project.xml + .cht、查询控件/语法/协议。命令：/mk-control /mk-xml-controls /mk-xml-structure /mk-cht-devices /mk-cht-functions /mk-cht-patterns /mk-protocol-list /mk-protocol-add /mk-protocol-show /mk-protocol-update /mk-protocol-delete /mk-protocol-import"
commands:
  - /mk-control
  - /mk-xml-controls
  - /mk-xml-structure
  - /mk-cht-devices
  - /mk-cht-functions
  - /mk-cht-patterns
  - /mk-protocol-list
  - /mk-protocol-add
  - /mk-protocol-show
  - /mk-protocol-update
  - /mk-protocol-delete
  - /mk-protocol-import
---

# MKControl 开发套件 (MDK)

## 命令路由

| 命令 | 功能 | 需读取 |
|------|------|--------|
| `/mk-control [描述]` | 核心生成器：自然语言 → XML + CHT | 按需读取下方知识库 |
| `/mk-xml-controls [类型]` | 查控件属性 | `references/controls/widgets/_index.md` → 对应控件文件 |
| `/mk-xml-structure [主题]` | 查 XML 结构 | `references/controls/xml-structure.md` |
| `/mk-cht-devices [类型]` | 查设备声明 | `references/core/syntax-rules.md` |
| `/mk-cht-functions [名称]` | 查系统函数 | `docs/系统函数库/*.md` |
| `/mk-cht-patterns [关键词]` | 查代码模式 | `references/core/patterns/_index.md` → 对应模式文件 |
| `/mk-protocol-*` | 协议库增删查改 | `protocols/` 目录 |

> 路径前缀均为 `core/`，如 `core/references/controls/controls-spec.md`

---

## /mk-control — 核心生成（5 阶段）

### Phase 1：解析

从用户描述中提取：
- **设备**：型号、板卡号、通信方式
- **功能**：灯光/窗帘/空调/投影/音量/场景/电源等
- **协议匹配**：查 `protocols/_index.md`，匹配到则读取对应协议文件

### Phase 2：确认清单

输出 3 张表格让用户核对：

**设备清单** — 设备名/类型/编号/通信方式
**功能清单** — 功能名/JoinNumber/来源(用户指定|自动)/控件类型/控制方式
**页面结构** — 页面名/类型(guide|main|sub|dialog)

标注缺失信息（⚠️），等待用户确认后进入 Phase 3。

### Phase 3：JoinNumber 分配

**规则**：用户指定的直接使用，未指定的按号段自动分配。同一设备的开/关共用同一 JoinNumber。

| 号段 | 用途 |
|------|------|
| 1-49 | 系统/导航 |
| 100-139 | 灯光/窗帘 |
| 140-149 | 幕布/场景 |
| 150-164 | 图片状态 |
| 165-169 | 电源开关 |
| 200-209, 240-299 | 文本反馈 |
| 210-239 | 信号源/空调 |
| 300-499 | 状态文本 |
| 500-599 | 全局/特殊 |
| 1000-1099 | 滑条 |
| 1100-1199 | 扩展 |
| 1200+ | 弹窗 |

### Phase 4：双文件生成

**优先使用模板 (`templates/`) 生成固定结构，LLM 只负责决定布局和逻辑。**

#### 4a. Project.xml

**生成方式**：读取 `templates/xml/*.tpl` 模板 → 填充变量 → 拼装。仅在模板不覆盖的场景才参考 `references/controls/widgets/` 中对应控件文件。

决策规则：

| 功能 | 控件 | BtnType | 说明 |
|------|------|---------|------|
| 单路开关 | DFCButton | AutolockBtn | PUSH=开, RELEASE=关 |
| 全开/全关 | DFCButton | NormalBtn | PUSH 触发 |
| 场景/信号源 | DFCButton | MutualLockBtn | 同组互斥 |
| 音量/亮度 | DFCSlider | — | 双向: LEVEL_EVENT + SET_LEVEL |
| 状态文字 | DFCTextbox | — | SEND_TEXT 推送 |
| 状态图片 | DFCPicture | — | SEND_PICTURE 切换 |
| 时间显示 | DFCTime | — | TimeType="HH:mm" |
| 页面跳转 | DFCButton | NormalBtn | JumpPage="目标页" |
| 弹窗 | DFCMessegeToast | — | 注意拼写 Messege |

无图退化：`NormalColor` + `PressColor` + `Text` + `Radius="10"`

#### 4b. .cht 文件

**生成方式**：读取 `templates/cht/simple-program.cht.tpl`(骨架) + `templates/cht/devices.md`(设备声明规则) + `templates/cht/events.md`(事件模板) → 填充。复杂逻辑参考 `references/core/patterns/` 中匹配的模式 + `references/core/syntax-rules.md` + 匹配的协议文件。

块顺序：`DEFINE_DEVICE → DEFINE_COMBINE → DEFINE_CONSTANT(仅整型!) → DEFINE_VARIABLE(必须赋初值) → DEFINE_FUNCTION → DEFINE_TIMER → DEFINE_START → DEFINE_EVENT → DEFINE_PROGRAME`

说明：以上顺序以 **中控软件“新建项目 → 简单程序模板”** 为准；即使内容为空，也保留空块。

### Phase 5：交叉校验

| 校验项 | 级别 |
|--------|------|
| XML 非零 JN 在 CHT 有事件 | Critical |
| CHT 事件 JN 在 XML 有控件 | Critical |
| JoinNumber 唯一性 | Critical |
| JumpPage 目标存在 | Warning |
| DEFINE_DEVICE 覆盖所有设备 | Critical |
| SET_COM 覆盖所有串口 | Warning |

---

## 缺失信息处理

| 缺失 | 处理 |
|------|------|
| 板卡号 | 标注 ⚠️，用 `TODO:板卡号` 占位 |
| 通信协议 | **停止生成**，必须获取协议 |
| 图片 | 退化为纯色按钮 |
| 页面结构 | 自动规划，清单确认 |

---

## /mk-protocol-* — 协议管理

协议库：`core/protocols/` ，索引：`_index.md`，模板：`_template.md`

分类目录：`projector/ curtain/ ac/ audio/ display/ camera/ matrix/ screen/ lighting/ custom/`

| 命令 | 操作 |
|------|------|
| `/mk-protocol-list [关键词]` | 读 `_index.md`，可按分类/通信方式过滤 |
| `/mk-protocol-add` | 引导式：类型→品牌→通信→参数→指令表→写入+更新索引 |
| `/mk-protocol-show [名称]` | 模糊搜索 `_index.md` → 读取对应文件 |
| `/mk-protocol-update [名称] [修改]` | 定位→修改→追加更新记录 |
| `/mk-protocol-delete [名称]` | 二次确认→删除文件→更新索引 |
| `/mk-protocol-import [.cht路径]` | 扫描 SEND_COM/TCP/IRCODE → 按设备分组 → 确认后存入 |

---

## 知识库索引（按需加载，禁止全量读取）

| 类别 | 索引文件 | 详情文件 | 何时读取 |
|------|---------|---------|---------|
| **模板(优先)** | `templates/_index.md` | `templates/xml/*.tpl` + `templates/cht/*.tpl` | **Phase 4 生成时首选** |
| 协议库 | `protocols/_index.md` | `protocols/<分类>/<文件>.md` | Phase 1 匹配后读详情 |
| 控件规范 | `references/controls/widgets/_index.md` | `widgets/DFCButton.md` 等 | 模板不够时补充，**只读用到的** |
| XML结构 | — | `references/controls/xml-structure.md` | 仅首次生成需了解全局结构 |
| 代码模式 | `references/core/patterns/_index.md` | `patterns/relay-light.md` 等 | 生成 CHT 时，**只读匹配的模式** |
| 语法规则 | — | `references/core/syntax-rules.md` | 生成 CHT 时 |
| 系统函数 | — | `docs/系统函数库/<分类>.md` | 按需查函数签名 |

**加载原则**: 模板优先 → 索引定位 → 按需读取详情 → 绝不全量加载
