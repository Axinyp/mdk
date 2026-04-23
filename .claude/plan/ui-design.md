# UI/UX 设计方案：MDK Web Platform -- ConfirmationView & ResultView

**设计时间**：2026-04-22
**目标平台**：Web（桌面端优先，平板适配）
**技术栈**：React 18+ / TypeScript 5+ / Tailwind CSS 3+
**状态管理**：Zustand（轻量，适合中小型应用）
**代码高亮**：Shiki 或 Prism（XML 语法支持好）
**Diff 引擎**：diff（npm 包）或 Monaco Editor 内置 diff

---

## 1. 设计目标

### 1.1 用户目标

用户是**运维人员**，不懂编程，不会看 JSON。核心诉求：

- 看懂 AI 解析出来的设备、功能、页面结构是否正确
- 能直接在界面上修改错误项（改名字、改 Join 号、删多余行、加遗漏项）
- 知道哪些信息缺失需要补充
- 确认后一键生成，拿到可用的 XML + CHT 文件

### 1.2 业务目标

- 将 JSON 结构对运维人员**零门槛可视化**，降低使用壁垒
- 通过内联编辑减少"修改 -> 重新对话 -> 重新解析"的反复循环
- 校验报告前置，避免生成后才发现问题
- 版本管理和 diff 对比支持迭代优化

### 1.3 设计原则

| 原则 | 落地方式 |
|------|----------|
| 系统匹配现实 | 使用"设备""功能""页面"等运维术语，不暴露 JSON 字段名 |
| 防错 | join_number 输入限制为数字；删除操作需二次确认 |
| 识别优于回忆 | join_source 用彩色标签而非文字代码；缺失信息用醒目卡片 |
| 状态可见 | 编辑中、保存中、生成中均有明确视觉反馈 |

---

## 2. 全局设计规范

### 2.1 配色方案

```
Primary:      #3B82F6  (Blue-500)    -- CTA、主操作、链接
Primary Dark: #2563EB  (Blue-600)    -- 按钮 hover
Secondary:    #10B981  (Emerald-500) -- 成功、用户指定标签
Warning:      #F59E0B  (Amber-500)   -- 缺失信息、告警卡片
Error:        #EF4444  (Red-500)     -- Critical 校验、删除
Info:         #6366F1  (Indigo-500)  -- 自动分配标签
Neutral-50:   #F9FAFB               -- 页面背景
Neutral-100:  #F3F4F6               -- 卡片背景
Neutral-200:  #E5E7EB               -- 边框、分割线
Neutral-500:  #6B7280               -- 次要文字
Neutral-900:  #111827               -- 主文字
```

### 2.2 字体排版

```
标题 H2:   text-xl  (20px), font-semibold, text-neutral-900
标题 H3:   text-lg  (18px), font-medium,   text-neutral-900
正文:      text-sm  (14px), font-normal,   text-neutral-700
辅助文字:  text-xs  (12px), font-normal,   text-neutral-500
代码:      text-sm  (14px), font-mono (JetBrains Mono / Fira Code)
```

### 2.3 间距系统（8px 网格）

```
组件内间距:   p-2 (8px), p-3 (12px), p-4 (16px)
组件间间距:   gap-4 (16px), gap-6 (24px)
区块间间距:   space-y-6 (24px), space-y-8 (32px)
卡片内边距:   p-4 (16px) ~ p-6 (24px)
表格单元格:   px-3 py-2 (12px/8px)
```

### 2.4 圆角与阴影

```
卡片:       rounded-lg (8px),  shadow-sm
按钮:       rounded-md (6px)
输入框:     rounded-md (6px)
标签 Badge: rounded-full (9999px)
弹窗:       rounded-xl (12px), shadow-xl
```

### 2.5 响应式断点

| 屏幕 | Breakpoint | 布局策略 |
|------|------------|----------|
| 小屏 (平板竖屏) | < 1024px | 表格横向滚动；结果预览切换为标签页模式 |
| 中屏 (平板横屏/小笔记本) | 1024px ~ 1440px | 表格正常展示；结果预览左右分栏 |
| 大屏 (桌面) | >= 1440px | 最大宽度 1280px 居中；充分利用空间 |

---

## 3. 页面 1：确认清单页（ConfirmationView）

### 3.1 布局草图

```
+================================================================+
|  [对话气泡区域 -- 上方是 AI 回复的文字]                          |
+================================================================+
|                                                                  |
|  +------------------------------------------------------------+  |
|  |  确认清单卡片 (嵌入对话流)                                   |  |
|  |                                                              |  |
|  |  [!] 缺失信息告警区 (黄色)                                   |  |
|  |  +--------------------------------------------------------+  |  |
|  |  | (!) 投影仪品牌型号未知，无法确定串口指令                  |  |  |
|  |  | (!) 空调红外 UserIRDB 路径未提供                          |  |  |
|  |  +--------------------------------------------------------+  |  |
|  |                                                              |  |
|  |  [i] 未提供图片，将使用纯色按钮                               |  |
|  |                                                              |  |
|  |  ┌─ Tab: 设备清单 | 功能清单 | 页面结构 ─────────────────┐  |  |
|  |  │                                                         │  |  |
|  |  │  ┌────────┬──────────┬──────┬──────────┐               │  |  |
|  |  │  │ 设备名  │ 类型      │ Board │ 通讯方式  │  [操作]     │  |  |
|  |  │  ├────────┼──────────┼──────┼──────────┤               │  |  |
|  |  │  │ 触摸屏  │ TP       │  10  │ 内置     │  [x]         │  |  |
|  |  │  │ TS-9101│ RELAY    │   1  │ 继电器   │  [x]         │  |  |
|  |  │  │ TR-0740│ 扩展模块  │   2  │ COM/IR   │  [x]         │  |  |
|  |  │  └────────┴──────────┴──────┴──────────┘               │  |  |
|  |  │  [+ 添加设备]                                           │  |  |
|  |  │                                                         │  |  |
|  |  └─────────────────────────────────────────────────────────┘  |  |
|  |                                                              |  |
|  |  ┌─────────────────────────────────────────────────────────┐  |  |
|  |  │  [修改后重新解析]              [确认生成 ->]             │  |  |
|  |  └─────────────────────────────────────────────────────────┘  |  |
|  |                                                              |  |
|  +------------------------------------------------------------+  |
|                                                                  |
+================================================================+
```

### 3.2 区块说明

| 区块 | 用途 | 优先级 |
|------|------|--------|
| MissingInfoAlert | 黄色告警卡片，展示 missing_info 数组 | 高 -- 必须首先被看到 |
| ImagePathNotice | 图片路径提示（null 时显示纯色按钮提示） | 中 |
| TabGroup | 标签页切换三个表格 | 高 |
| DeviceTable | 设备清单可编辑表格 | 高 |
| FunctionTable | 功能清单可编辑表格（含 join_source 标签） | 高 |
| PageTable | 页面结构可编辑表格 | 高 |
| ActionBar | 底部操作按钮组 | 高 |

### 3.3 组件树结构

```
ConfirmationView
├── MissingInfoAlert
│   └── AlertItem (repeated)
├── ImagePathNotice
├── TabGroup
│   ├── TabButton ("设备清单")
│   ├── TabButton ("功能清单")
│   └── TabButton ("页面结构")
├── TabPanel (conditional render)
│   ├── DeviceTable
│   │   ├── TableHeader
│   │   ├── EditableRow (repeated)
│   │   │   ├── EditableCell (repeated)
│   │   │   └── RowActions
│   │   │       ├── DeleteRowButton
│   │   │       └── DuplicateRowButton
│   │   ├── AddRowButton
│   │   └── EmptyState
│   ├── FunctionTable
│   │   ├── TableHeader
│   │   ├── EditableRow (repeated)
│   │   │   ├── EditableCell (repeated)
│   │   │   ├── JoinSourceBadge
│   │   │   └── RowActions
│   │   ├── AddRowButton
│   │   └── EmptyState
│   └── PageTable
│       ├── TableHeader
│       ├── EditableRow (repeated)
│       │   ├── EditableCell (repeated)
│       │   ├── PageTypeBadge
│       │   └── RowActions
│       ├── AddRowButton
│       └── EmptyState
├── ActionBar
│   ├── ReParseButton ("修改后重新解析")
│   └── ConfirmButton ("确认生成")
└── ConfirmDialog (modal, on confirm click)
    ├── SummaryStats
    └── DialogActions
```

### 3.4 组件详细定义

---

#### 3.4.1 `ConfirmationView`

**职责**：顶层容器，管理整体数据状态，协调子组件交互。

```typescript
interface ConfirmationViewProps {
  /** AI 解析输出的完整 JSON 数据 */
  data: ParsedProjectData
  /** 确认生成回调，将修改后的数据提交给后端 */
  onConfirm: (data: ParsedProjectData) => Promise<void>
  /** 重新解析回调，将修改后的数据送回 AI 重新解析 */
  onReParse: (data: ParsedProjectData) => void
  /** 当前是否正在生成中 */
  isGenerating?: boolean
}

interface ParsedProjectData {
  devices: DeviceItem[]
  functions: FunctionItem[]
  pages: PageItem[]
  missing_info: string[]
  image_path: string | null
}

interface DeviceItem {
  id: string           // 前端生成的唯一标识，用于 React key 和行操作
  name: string
  type: string
  board: number
  comm: string
}

interface FunctionItem {
  id: string
  name: string
  join_number: number
  join_source: 'auto' | 'user_specified'
  control_type: string
  btn_type: string | null
  device: string
  channel: number | null
}

interface PageItem {
  id: string
  name: string
  type: 'guide' | 'main' | 'sub' | 'dialog'
}
```

**状态管理**（Zustand store）：

```typescript
interface ConfirmationStore {
  // 数据
  devices: DeviceItem[]
  functions: FunctionItem[]
  pages: PageItem[]
  missingInfo: string[]
  imagePath: string | null

  // UI 状态
  activeTab: 'devices' | 'functions' | 'pages'
  editingCell: { rowId: string; field: string } | null
  hasUnsavedChanges: boolean
  isConfirmDialogOpen: boolean

  // Actions
  setActiveTab: (tab: 'devices' | 'functions' | 'pages') => void
  updateDevice: (id: string, field: keyof DeviceItem, value: string | number) => void
  addDevice: () => void
  removeDevice: (id: string) => void
  updateFunction: (id: string, field: keyof FunctionItem, value: any) => void
  addFunction: () => void
  removeFunction: (id: string) => void
  updatePage: (id: string, field: keyof PageItem, value: string) => void
  addPage: () => void
  removePage: (id: string) => void
  setEditingCell: (cell: { rowId: string; field: string } | null) => void
  getModifiedData: () => ParsedProjectData
  resetToOriginal: () => void
}
```

**样式要点**：

```html
<!-- 嵌入对话流的卡片容器 -->
<div class="
  w-full max-w-4xl mx-auto
  bg-white rounded-lg shadow-sm
  border border-neutral-200
  overflow-hidden
">
```

---

#### 3.4.2 `MissingInfoAlert`

**职责**：渲染缺失信息告警卡片。仅当 `missing_info.length > 0` 时显示。

```typescript
interface MissingInfoAlertProps {
  items: string[]
}
```

**样式**：

```html
<div class="
  bg-amber-50 border border-amber-200 rounded-lg
  p-4 mx-4 mt-4
" role="alert">
  <div class="flex items-start gap-3">
    <ExclamationTriangleIcon class="w-5 h-5 text-amber-500 mt-0.5 shrink-0" />
    <div class="space-y-1">
      <h3 class="text-sm font-medium text-amber-800">
        以下信息缺失，可能影响生成结果
      </h3>
      <ul class="text-sm text-amber-700 list-disc list-inside space-y-0.5">
        <li>投影仪品牌型号未知，无法确定串口指令</li>
        <li>空调红外 UserIRDB 路径未提供</li>
      </ul>
    </div>
  </div>
</div>
```

**A11y**：`role="alert"`, `aria-live="polite"`

---

#### 3.4.3 `ImagePathNotice`

**职责**：当 `image_path === null` 时显示蓝色信息提示。

```typescript
interface ImagePathNoticeProps {
  imagePath: string | null
}
```

**样式**：

```html
<div class="
  bg-blue-50 border border-blue-200 rounded-lg
  px-4 py-3 mx-4 mt-3
  flex items-center gap-2
  text-sm text-blue-700
">
  <InformationCircleIcon class="w-4 h-4 shrink-0" />
  <span>未提供触摸屏界面图片，将使用纯色按钮方案生成</span>
</div>
```

---

#### 3.4.4 `TabGroup` + `TabButton`

**职责**：三个标签页切换（设备清单 / 功能清单 / 页面结构），每个标签显示对应表格行数。

```typescript
interface TabGroupProps {
  activeTab: 'devices' | 'functions' | 'pages'
  onTabChange: (tab: 'devices' | 'functions' | 'pages') => void
  counts: {
    devices: number
    functions: number
    pages: number
  }
}

interface TabButtonProps {
  label: string
  count: number
  isActive: boolean
  onClick: () => void
}
```

**样式**：

```html
<!-- Tab 容器 -->
<div class="flex border-b border-neutral-200 px-4 mt-4" role="tablist">
  <!-- 单个 Tab -->
  <button
    role="tab"
    aria-selected="true"
    class="
      px-4 py-2.5 text-sm font-medium
      border-b-2 -mb-px
      text-blue-600 border-blue-500     /* active */
      /* inactive: text-neutral-500 border-transparent hover:text-neutral-700 */
    "
  >
    设备清单
    <span class="ml-1.5 px-1.5 py-0.5 text-xs rounded-full bg-blue-100 text-blue-600">
      3
    </span>
  </button>
</div>
```

---

#### 3.4.5 `EditableTable`（通用可编辑表格）

**职责**：可复用的内联编辑表格组件。三个表格共享此基础组件。

```typescript
interface Column<T> {
  key: keyof T & string
  label: string
  width?: string               // Tailwind width class, e.g. "w-32"
  editable?: boolean           // 默认 true
  inputType?: 'text' | 'number' | 'select'
  selectOptions?: { value: string; label: string }[]
  renderCell?: (value: any, row: T) => React.ReactNode  // 自定义渲染（如 Badge）
  validate?: (value: any) => string | null  // 返回错误信息或 null
}

interface EditableTableProps<T extends { id: string }> {
  columns: Column<T>[]
  data: T[]
  onUpdate: (id: string, field: keyof T, value: any) => void
  onAdd: () => void
  onRemove: (id: string) => void
  onDuplicate?: (id: string) => void
  addButtonLabel: string       // e.g. "+ 添加设备"
  emptyMessage: string         // e.g. "暂无设备，点击下方按钮添加"
  editingCell: { rowId: string; field: string } | null
  onEditingCellChange: (cell: { rowId: string; field: string } | null) => void
}
```

**内联编辑交互**：

- **进入编辑**：单击单元格 -> 该单元格变为输入框，自动聚焦
- **确认编辑**：Enter 键 / Tab 键 / 点击其他区域（onBlur）
- **取消编辑**：Escape 键，恢复原值
- **Tab 顺序**：Tab 跳到同行下一个可编辑列，Shift+Tab 反向
- **视觉反馈**：编辑中单元格有蓝色边框（`ring-2 ring-blue-500`）

**样式**：

```html
<table class="w-full text-sm">
  <thead>
    <tr class="bg-neutral-50 text-left">
      <th class="px-3 py-2 text-xs font-medium text-neutral-500 uppercase tracking-wider">
        设备名称
      </th>
    </tr>
  </thead>
  <tbody class="divide-y divide-neutral-100">
    <!-- 普通单元格 -->
    <td class="px-3 py-2 cursor-pointer hover:bg-blue-50 transition-colors">
      触摸屏
    </td>
    <!-- 编辑中单元格 -->
    <td class="px-1 py-1">
      <input
        class="
          w-full px-2 py-1 text-sm
          border border-blue-500 rounded-md
          ring-2 ring-blue-200
          focus:outline-none
        "
        autoFocus
      />
    </td>
  </tbody>
</table>
```

---

#### 3.4.6 `JoinSourceBadge`

**职责**：渲染 `join_source` 的彩色标签。

```typescript
interface JoinSourceBadgeProps {
  source: 'auto' | 'user_specified'
}
```

**样式**：

```html
<!-- auto -->
<span class="
  inline-flex items-center px-2 py-0.5 rounded-full
  text-xs font-medium
  bg-indigo-100 text-indigo-700
">
  自动分配
</span>

<!-- user_specified -->
<span class="
  inline-flex items-center px-2 py-0.5 rounded-full
  text-xs font-medium
  bg-emerald-100 text-emerald-700
">
  用户指定
</span>
```

---

#### 3.4.7 `PageTypeBadge`

**职责**：渲染页面类型标签。

```typescript
interface PageTypeBadgeProps {
  type: 'guide' | 'main' | 'sub' | 'dialog'
}
```

**映射**：

| type | label | 色系 |
|------|-------|------|
| guide | 引导页 | `bg-purple-100 text-purple-700` |
| main | 主页 | `bg-blue-100 text-blue-700` |
| sub | 子页 | `bg-neutral-100 text-neutral-600` |
| dialog | 弹窗 | `bg-amber-100 text-amber-700` |

---

#### 3.4.8 `RowActions`

**职责**：每行末尾的操作按钮（删除、复制）。

```typescript
interface RowActionsProps {
  onDelete: () => void
  onDuplicate?: () => void
  deleteConfirmMessage?: string  // 删除二次确认文案
}
```

**样式**：

```html
<div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
  <button
    class="p-1 rounded hover:bg-neutral-100 text-neutral-400 hover:text-neutral-600"
    title="复制此行"
    aria-label="复制此行"
  >
    <DocumentDuplicateIcon class="w-4 h-4" />
  </button>
  <button
    class="p-1 rounded hover:bg-red-50 text-neutral-400 hover:text-red-500"
    title="删除此行"
    aria-label="删除此行"
  >
    <TrashIcon class="w-4 h-4" />
  </button>
</div>
```

**交互**：表格行设置 `group` class，操作按钮 hover 时显示（`group-hover:opacity-100`）。

---

#### 3.4.9 `AddRowButton`

**职责**：表格底部的"添加行"按钮。

```typescript
interface AddRowButtonProps {
  label: string   // "+ 添加设备" / "+ 添加功能" / "+ 添加页面"
  onClick: () => void
}
```

**样式**：

```html
<button class="
  w-full py-2 mt-1
  text-sm text-blue-600
  border border-dashed border-blue-300 rounded-md
  hover:bg-blue-50 hover:border-blue-400
  transition-colors
">
  + 添加设备
</button>
```

---

#### 3.4.10 `ActionBar`

**职责**：底部操作按钮栏，包含"修改后重新解析"和"确认生成"。

```typescript
interface ActionBarProps {
  onReParse: () => void
  onConfirm: () => void
  isGenerating: boolean
  hasChanges: boolean  // 数据是否有修改
}
```

**按钮状态矩阵**：

| 状态 | "修改后重新解析" | "确认生成" |
|------|-----------------|-----------|
| 无修改 | 灰色 disabled | 蓝色 primary enabled |
| 有修改 | 蓝色 secondary enabled | 蓝色 primary enabled |
| 生成中 | 灰色 disabled | Loading spinner + "生成中..." disabled |

**样式**：

```html
<div class="
  flex justify-between items-center
  px-4 py-4 mt-4
  border-t border-neutral-200
  bg-neutral-50
">
  <button class="
    px-4 py-2 text-sm font-medium
    text-neutral-600 bg-white
    border border-neutral-300 rounded-md
    hover:bg-neutral-50
    disabled:opacity-50 disabled:cursor-not-allowed
  ">
    修改后重新解析
  </button>

  <button class="
    px-6 py-2 text-sm font-medium
    text-white bg-blue-600
    rounded-md
    hover:bg-blue-700
    disabled:opacity-50 disabled:cursor-not-allowed
    flex items-center gap-2
  ">
    <!-- Loading 态 -->
    <SpinnerIcon class="w-4 h-4 animate-spin" />
    确认生成
  </button>
</div>
```

---

#### 3.4.11 `ConfirmDialog`

**职责**：点击"确认生成"后弹出的确认弹窗，显示摘要统计。

```typescript
interface ConfirmDialogProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  summary: {
    deviceCount: number
    functionCount: number
    pageCount: number
    missingInfoCount: number
  }
  isGenerating: boolean
}
```

**弹窗内容**：

```
┌──────────────────────────────────────────┐
│  确认生成                           [X]  │
│──────────────────────────────────────────│
│                                          │
│  即将生成以下内容：                        │
│                                          │
│   设备数量:    3 个                       │
│   功能数量:    6 个                       │
│   页面数量:    5 个                       │
│   缺失信息:    2 条 (!)                  │
│                                          │
│  (!) 存在缺失信息，生成结果可能不完整。     │
│      建议先补充缺失信息后再生成。           │
│                                          │
│           [取消]    [仍然生成]             │
│──────────────────────────────────────────│
└──────────────────────────────────────────┘
```

---

### 3.5 三个表格的列定义

#### DeviceTable 列

| 列 | key | 类型 | 宽度 | 可编辑 | 说明 |
|----|-----|------|------|--------|------|
| 设备名称 | name | text | w-40 | Yes | |
| 类型 | type | select | w-32 | Yes | 选项: TP / RELAY / 扩展模块 / DSP / 矩阵 / 摄像机 / 投影仪 / 空调 |
| Board ID | board | number | w-20 | Yes | 0-255 |
| 通讯方式 | comm | select | w-36 | Yes | 选项: 内置 / 继电器 / COM/IR / RS232 / TCP/IP |
| 操作 | -- | actions | w-20 | -- | 删除/复制 |

#### FunctionTable 列

| 列 | key | 类型 | 宽度 | 可编辑 | 说明 |
|----|-----|------|------|--------|------|
| 功能名称 | name | text | w-36 | Yes | |
| Join 号 | join_number | number | w-24 | Yes | 正整数 |
| 来源 | join_source | badge | w-24 | No | JoinSourceBadge 渲染 |
| 控件类型 | control_type | select | w-32 | Yes | DFCButton / DFCSlider / DFCLevel 等 |
| 按钮类型 | btn_type | select | w-32 | Yes | NormalBtn / AutolockBtn / null |
| 关联设备 | device | select | w-28 | Yes | 下拉选项从 devices 数组动态获取 |
| 通道 | channel | number | w-20 | Yes | null 显示为 "--" |
| 操作 | -- | actions | w-20 | -- | |

#### PageTable 列

| 列 | key | 类型 | 宽度 | 可编辑 | 说明 |
|----|-----|------|------|--------|------|
| 页面名称 | name | text | w-48 | Yes | |
| 页面类型 | type | badge+select | w-32 | Yes | 显示为 Badge，点击弹出 select |
| 操作 | -- | actions | w-20 | -- | |

---

### 3.6 交互流程

#### 3.6.1 用户旅程

```
用户在对话中描述需求
     │
     v
AI 返回解析 JSON，前端渲染 ConfirmationView
     │
     v
用户首先看到 MissingInfoAlert（如有）
     │
     ├─ 用户决定补充信息 ──> 在对话中继续输入 ──> AI 重新解析 ──> 新的 ConfirmationView
     │
     └─ 用户继续查看表格
          │
          v
     查看 DeviceTable（默认激活标签）
          │
          ├─ 发现错误 ──> 点击单元格 ──> 内联编辑 ──> Enter/Blur 保存
          ├─ 缺少设备 ──> 点击"+ 添加设备" ──> 新行出现，首列自动聚焦
          ├─ 多余设备 ──> hover 行 ──> 点击删除 ──> 二次确认 ──> 行消失
          │
          v
     切换到 FunctionTable 标签
          │
          ├─ 检查 join_number 是否正确
          ├─ 检查 join_source 标签（自动分配 vs 用户指定）
          ├─ 修改关联设备（下拉选项来自 DeviceTable 数据）
          │
          v
     切换到 PageTable 标签
          │
          ├─ 检查页面结构是否合理
          ├─ 调整页面类型
          │
          v
     点击"确认生成"
          │
          v
     弹出 ConfirmDialog，显示摘要
          │
          ├─ 有缺失信息 ──> 显示警告文案
          │
          v
     点击"仍然生成" / "确认生成"
          │
          v
     Loading 状态 ──> 后端生成 ──> 跳转到 ResultView
```

#### 3.6.2 状态转换

| 当前状态 | 触发事件 | 下一状态 | UI 变化 |
|----------|----------|----------|---------|
| Viewing | 点击单元格 | Editing | 单元格变为 input，蓝色 ring |
| Editing | Enter / Blur | Viewing | input 消失，显示新值 |
| Editing | Escape | Viewing | input 消失，恢复原值 |
| Viewing | 点击"+ 添加" | Editing | 新行插入表格底部，首列自动聚焦 |
| Viewing | 点击删除 | Confirming | 弹出 inline 确认提示 |
| Confirming | 确认删除 | Viewing | 行消失，带 fade-out 动画 |
| Viewing | 点击"确认生成" | ConfirmDialog | 弹窗出现 |
| ConfirmDialog | 确认 | Generating | 弹窗关闭，按钮显示 spinner |
| Generating | 生成完成 | Done | 对话流中出现 ResultView |

#### 3.6.3 数据联动

- FunctionTable 的 `device` 列下拉选项 = DeviceTable 中所有 `name` 值
- 删除 DeviceTable 中的设备时，如果 FunctionTable 中有引用，弹出警告："该设备被 N 个功能引用，删除后这些功能的关联设备将变为空"
- 修改 DeviceTable 中设备名称时，FunctionTable 中引用该设备的行同步更新

---

## 4. 页面 2：结果预览页（ResultView）

### 4.1 布局草图

```
+================================================================+
|  [对话气泡区域 -- AI: "已生成完毕，请查看："]                     |
+================================================================+
|                                                                  |
|  +------------------------------------------------------------+  |
|  |  结果预览卡片                                                |  |
|  |                                                              |  |
|  |  ┌──────────────────────────────────────────────────────┐   |  |
|  |  │  [版本: v3 v]  [分栏模式|标签页模式]  [搜索 Ctrl+F]  │   |  |
|  |  │  [Diff 对比]                                          │   |  |
|  |  └──────────────────────────────────────────────────────┘   |  |
|  |                                                              |  |
|  |  ┌────────────────────┬─ ─ ─┬───────────────────────────┐  |  |
|  |  │  Project.xml       │  |  │  output.cht               │  |  |
|  |  │                    │  |  │                            │  |  |
|  |  │  1 | <?xml ...>    │  |  │  1 | /***...              │  |  |
|  |  │  2 | <Project>     │  |  │  2 | Digital              │  |  |
|  |  │  3 |   <Device     │  |  │  3 |   [灯光1开]          │  |  |
|  |  │  4 |     name=...  │  |  │  4 |     103 = ...        │  |  |
|  |  │  ...               │  |  │  ...                      │  |  |
|  |  │                    │  |  │                            │  |  |
|  |  │  [全屏] [复制]      │  |  │  [全屏] [复制]            │  |  |
|  |  └────────────────────┴─ ─ ─┴───────────────────────────┘  |  |
|  |                                                              |  |
|  |  ┌──────────────────────────────────────────────────────┐   |  |
|  |  │  校验报告                                              │   |  |
|  |  │  [!] Critical: 0   [!] Warning: 3                      │   |  |
|  |  │                                                        │   |  |
|  |  │  W  Join 103 在 CHT 中定义但 XML 中无对应控件          │   |  |
|  |  │  W  页面"电源确认"的 Dialog 类型无关闭按钮定义           │   |  |
|  |  │  W  设备 TR-0740S 的 Board 2 未在 XML header 中声明    │   |  |
|  |  └──────────────────────────────────────────────────────┘   |  |
|  |                                                              |  |
|  |  ┌──────────────────────────────────────────────────────┐   |  |
|  |  │  [下载 XML]  [下载 .cht]  [打包 .zip]                  │   |  |
|  |  └──────────────────────────────────────────────────────┘   |  |
|  |                                                              |  |
|  +------------------------------------------------------------+  |
|                                                                  |
+================================================================+
```

### 4.2 区块说明

| 区块 | 用途 | 优先级 |
|------|------|--------|
| Toolbar | 版本选择、视图模式切换、搜索、Diff 开关 | 高 |
| CodePreviewPanel | 左右分栏或标签页的代码预览区 | 高 |
| ValidationReport | 底部校验报告（Critical / Warning） | 高 |
| DownloadBar | 下载按钮组 | 高 |

### 4.3 组件树结构

```
ResultView
├── ResultToolbar
│   ├── VersionSelector
│   ├── ViewModeToggle (split | tabs)
│   ├── SearchTrigger
│   └── DiffToggle
├── CodePreviewArea
│   ├── SplitView (viewMode === 'split')
│   │   ├── CodePanel (file: "Project.xml")
│   │   │   ├── PanelHeader
│   │   │   │   ├── FileNameLabel
│   │   │   │   ├── FullscreenButton
│   │   │   │   └── CopyButton
│   │   │   ├── CodeBlock
│   │   │   │   ├── LineNumbers
│   │   │   │   └── HighlightedCode
│   │   │   └── SearchOverlay (when active)
│   │   ├── ResizableDivider
│   │   └── CodePanel (file: "output.cht")
│   │       └── (same structure)
│   └── TabView (viewMode === 'tabs')
│       ├── TabHeader
│       │   ├── TabButton ("Project.xml")
│       │   └── TabButton ("output.cht")
│       └── CodePanel (current tab)
├── DiffView (when diff mode active)
│   ├── DiffHeader
│   │   ├── VersionLabel (old)
│   │   └── VersionLabel (new)
│   └── DiffCodeBlock
│       ├── UnifiedDiff / SideBySideDiff
│       └── DiffLineNumbers
├── ValidationReport
│   ├── ReportHeader
│   │   ├── CriticalCount
│   │   └── WarningCount
│   ├── ValidationItem (repeated)
│   │   ├── SeverityIcon
│   │   ├── MessageText
│   │   └── LocationLink (optional, click to scroll to line)
│   └── EmptyReport ("校验通过，无异常")
├── DownloadBar
│   ├── DownloadButton ("下载 XML")
│   ├── DownloadButton ("下载 .cht")
│   └── DownloadButton ("打包 .zip")
└── FullscreenOverlay (when fullscreen active)
    └── CodePanel (fullscreen version)
```

### 4.4 组件详细定义

---

#### 4.4.1 `ResultView`

**职责**：顶层容器，管理预览状态。

```typescript
interface ResultViewProps {
  /** 当前生成结果 */
  result: GenerationResult
  /** 历史版本列表（同一需求的多次生成） */
  versions?: GenerationVersion[]
  /** 下载回调 */
  onDownload: (fileType: 'xml' | 'cht' | 'zip') => void
}

interface GenerationResult {
  xmlContent: string
  chtContent: string
  validation: ValidationReport
  generatedAt: string        // ISO timestamp
  versionId: string
}

interface GenerationVersion {
  versionId: string
  label: string              // e.g. "v1", "v2", "v3"
  generatedAt: string
  summary: string            // e.g. "初次生成" / "修改灯光 Join 号后重新生成"
}

interface ValidationReport {
  criticalCount: number
  warningCount: number
  items: ValidationItem[]
}

interface ValidationItem {
  severity: 'critical' | 'warning'
  message: string
  file?: 'xml' | 'cht'       // 问题所在文件
  line?: number               // 问题所在行号（用于跳转定位）
  rule: string                // 校验规则代码，e.g. "JOIN_MISMATCH"
}
```

**状态管理**（Zustand store）：

```typescript
interface ResultStore {
  // 视图状态
  viewMode: 'split' | 'tabs'
  activeTab: 'xml' | 'cht'           // 标签页模式下当前激活的文件
  fullscreenPanel: 'xml' | 'cht' | null
  splitRatio: number                  // 左侧面板占比 0.3-0.7，默认 0.5

  // 搜索状态
  isSearchOpen: boolean
  searchQuery: string
  searchResults: SearchMatch[]
  currentMatchIndex: number

  // Diff 状态
  isDiffMode: boolean
  diffBaseVersionId: string | null    // 对比的基准版本
  diffViewType: 'unified' | 'side-by-side'

  // 版本状态
  selectedVersionId: string

  // Actions
  setViewMode: (mode: 'split' | 'tabs') => void
  setActiveTab: (tab: 'xml' | 'cht') => void
  toggleFullscreen: (panel: 'xml' | 'cht') => void
  setSplitRatio: (ratio: number) => void
  openSearch: () => void
  closeSearch: () => void
  setSearchQuery: (query: string) => void
  nextMatch: () => void
  prevMatch: () => void
  toggleDiffMode: () => void
  setDiffBaseVersion: (versionId: string) => void
  setSelectedVersion: (versionId: string) => void
}

interface SearchMatch {
  file: 'xml' | 'cht'
  line: number
  column: number
  length: number
}
```

---

#### 4.4.2 `ResultToolbar`

**职责**：工具栏，包含版本选择、视图模式、搜索、Diff 开关。

```typescript
interface ResultToolbarProps {
  versions: GenerationVersion[]
  selectedVersionId: string
  onVersionChange: (versionId: string) => void
  viewMode: 'split' | 'tabs'
  onViewModeChange: (mode: 'split' | 'tabs') => void
  onSearchOpen: () => void
  isDiffMode: boolean
  onDiffToggle: () => void
  hasDiffVersions: boolean    // 是否有多个版本可对比
}
```

**样式**：

```html
<div class="
  flex items-center justify-between flex-wrap gap-3
  px-4 py-3
  border-b border-neutral-200
  bg-neutral-50
">
  <!-- 左侧：版本选择 -->
  <div class="flex items-center gap-3">
    <label class="text-xs text-neutral-500">版本</label>
    <select class="
      text-sm px-2 py-1.5
      border border-neutral-300 rounded-md
      bg-white
      focus:ring-2 focus:ring-blue-200 focus:border-blue-500
    ">
      <option>v3 - 修改后重新生成 (04-22 15:30)</option>
      <option>v2 - 调整 Join 号 (04-22 14:20)</option>
      <option>v1 - 初次生成 (04-22 14:00)</option>
    </select>
  </div>

  <!-- 右侧：操作按钮组 -->
  <div class="flex items-center gap-2">
    <!-- 视图模式切换 -->
    <div class="
      inline-flex rounded-md border border-neutral-300
      overflow-hidden
    " role="radiogroup">
      <button class="px-3 py-1.5 text-xs bg-blue-600 text-white">分栏</button>
      <button class="px-3 py-1.5 text-xs bg-white text-neutral-600 hover:bg-neutral-50">标签</button>
    </div>

    <!-- 搜索按钮 -->
    <button class="
      p-1.5 rounded-md
      text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100
    " title="搜索 (Ctrl+F)">
      <MagnifyingGlassIcon class="w-4 h-4" />
    </button>

    <!-- Diff 对比 -->
    <button class="
      px-3 py-1.5 text-xs rounded-md
      border border-neutral-300
      hover:bg-neutral-50
      disabled:opacity-40 disabled:cursor-not-allowed
    " :disabled="!hasDiffVersions">
      Diff 对比
    </button>
  </div>
</div>
```

---

#### 4.4.3 `CodePanel`

**职责**：单个文件的代码预览面板，含行号、高亮、搜索高亮。

```typescript
interface CodePanelProps {
  fileName: string            // "Project.xml" | "output.cht"
  fileType: 'xml' | 'cht'
  content: string
  onCopy: () => void
  onFullscreen: () => void
  isFullscreen: boolean
  searchQuery?: string
  searchMatches?: SearchMatch[]
  currentMatchIndex?: number
  highlightLines?: number[]   // 校验报告点击时高亮的行
}
```

**代码渲染策略**：

- XML 使用 Shiki/Prism 的 XML 语法高亮
- CHT 文件类似 C 语法，使用 C/C++ 高亮规则
- 行号列宽 = `max(3, Math.ceil(Math.log10(lineCount)))` 字符宽度
- 搜索匹配用 `bg-yellow-200` 高亮，当前匹配用 `bg-orange-300`
- 校验问题行用 `bg-red-50 border-l-2 border-red-500` 标记

**样式**：

```html
<div class="flex flex-col h-full min-h-0">
  <!-- Panel Header -->
  <div class="
    flex items-center justify-between
    px-3 py-2
    bg-neutral-800 text-neutral-300
    text-xs font-mono
  ">
    <span class="flex items-center gap-2">
      <DocumentIcon class="w-3.5 h-3.5" />
      Project.xml
      <span class="text-neutral-500">· 142 行</span>
    </span>
    <div class="flex items-center gap-1">
      <button class="p-1 rounded hover:bg-neutral-700" title="复制到剪贴板">
        <ClipboardIcon class="w-3.5 h-3.5" />
      </button>
      <button class="p-1 rounded hover:bg-neutral-700" title="全屏">
        <ArrowsPointingOutIcon class="w-3.5 h-3.5" />
      </button>
    </div>
  </div>

  <!-- Code Area -->
  <div class="
    flex-1 overflow-auto
    bg-neutral-900 text-neutral-100
    font-mono text-sm leading-6
  ">
    <table class="w-full">
      <tbody>
        <tr class="hover:bg-neutral-800/50">
          <!-- 行号 -->
          <td class="
            px-3 py-0 text-right text-neutral-500
            select-none w-12
            border-r border-neutral-700
          ">1</td>
          <!-- 代码 -->
          <td class="px-4 py-0 whitespace-pre">
            <span class="text-blue-400">&lt;?xml</span>
            <span class="text-green-400"> version</span>=...
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
```

---

#### 4.4.4 `ResizableDivider`

**职责**：分栏模式下的可拖拽分割线。

```typescript
interface ResizableDividerProps {
  onResize: (ratio: number) => void
  orientation: 'vertical'     // 垂直分割线
}
```

**交互**：

- 鼠标悬浮时显示 `cursor-col-resize`，分割线变为蓝色
- 拖拽时实时更新左右面板宽度比例
- 双击恢复 50/50

**样式**：

```html
<div class="
  w-1 bg-neutral-200 hover:bg-blue-400
  cursor-col-resize
  transition-colors
  relative
  group
">
  <!-- 拖拽手柄视觉提示 -->
  <div class="
    absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2
    w-1 h-8 rounded-full
    bg-neutral-400 group-hover:bg-blue-500
  " />
</div>
```

---

#### 4.4.5 `SearchOverlay`

**职责**：代码搜索浮层（Ctrl+F 触发），类似 VS Code 的搜索框。

```typescript
interface SearchOverlayProps {
  isOpen: boolean
  query: string
  onQueryChange: (query: string) => void
  onClose: () => void
  matchCount: number
  currentMatchIndex: number
  onNext: () => void
  onPrev: () => void
  caseSensitive: boolean
  onCaseSensitiveToggle: () => void
  useRegex: boolean
  onRegexToggle: () => void
}
```

**样式**：

```html
<div class="
  absolute top-2 right-2 z-10
  flex items-center gap-2
  bg-white rounded-lg shadow-lg
  border border-neutral-200
  px-3 py-2
">
  <input
    type="text"
    placeholder="搜索..."
    class="w-48 text-sm border-0 focus:ring-0 p-0"
  />
  <span class="text-xs text-neutral-400 whitespace-nowrap">
    3 / 12
  </span>
  <button class="p-0.5 rounded hover:bg-neutral-100" aria-label="上一个匹配">
    <ChevronUpIcon class="w-4 h-4" />
  </button>
  <button class="p-0.5 rounded hover:bg-neutral-100" aria-label="下一个匹配">
    <ChevronDownIcon class="w-4 h-4" />
  </button>
  <button class="p-0.5 rounded hover:bg-neutral-100" aria-label="关闭搜索">
    <XMarkIcon class="w-4 h-4" />
  </button>
</div>
```

**快捷键**：

| 快捷键 | 功能 |
|--------|------|
| Ctrl+F | 打开搜索 |
| Escape | 关闭搜索 |
| Enter | 下一个匹配 |
| Shift+Enter | 上一个匹配 |
| Ctrl+Shift+F | 在两个文件中同时搜索 |

---

#### 4.4.6 `VersionSelector`

**职责**：版本选择下拉框。

```typescript
interface VersionSelectorProps {
  versions: GenerationVersion[]
  selectedId: string
  onChange: (versionId: string) => void
}
```

**下拉选项格式**：

```
v3 -- 修改后重新生成 (04-22 15:30)
v2 -- 调整 Join 号 (04-22 14:20)
v1 -- 初次生成 (04-22 14:00)
```

---

#### 4.4.7 `DiffView`

**职责**：两个版本的 diff 对比视图。

```typescript
interface DiffViewProps {
  oldContent: string
  newContent: string
  oldLabel: string          // e.g. "v2 (04-22 14:20)"
  newLabel: string          // e.g. "v3 (04-22 15:30)"
  fileType: 'xml' | 'cht'
  viewType: 'unified' | 'side-by-side'
  onViewTypeChange: (type: 'unified' | 'side-by-side') => void
}
```

**Diff 渲染规则**：

- 新增行: `bg-green-900/30 text-green-300` + 行号列 `bg-green-900/20`
- 删除行: `bg-red-900/30 text-red-300` + 行号列 `bg-red-900/20`
- 修改行: `bg-yellow-900/20` + 行内变更文字用 `bg-yellow-700/40` 高亮
- 无变化行: 正常显示
- 折叠未变化区域: 超过 5 行连续无变化时折叠，显示 "... 展开 N 行 ..."

---

#### 4.4.8 `ValidationReport`

**职责**：底部校验报告面板。

```typescript
interface ValidationReportProps {
  report: ValidationReport
  onItemClick?: (item: ValidationItem) => void  // 点击跳转到对应代码行
}
```

**样式**：

```html
<div class="border-t border-neutral-200">
  <!-- 报告头部 -->
  <div class="
    flex items-center gap-4
    px-4 py-3
    bg-neutral-50
  ">
    <h3 class="text-sm font-medium text-neutral-700">校验报告</h3>

    <!-- Critical 计数 -->
    <span class="
      inline-flex items-center gap-1
      text-xs font-medium
      text-red-600
    ">
      <XCircleIcon class="w-4 h-4" />
      Critical: 0
    </span>

    <!-- Warning 计数 -->
    <span class="
      inline-flex items-center gap-1
      text-xs font-medium
      text-amber-600
    ">
      <ExclamationTriangleIcon class="w-4 h-4" />
      Warning: 3
    </span>
  </div>

  <!-- 报告列表 -->
  <div class="divide-y divide-neutral-100 max-h-48 overflow-y-auto">
    <!-- Warning 项 -->
    <div class="
      flex items-start gap-3
      px-4 py-2.5
      hover:bg-neutral-50
      cursor-pointer
    ">
      <ExclamationTriangleIcon class="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
      <div>
        <p class="text-sm text-neutral-700">
          Join 103 在 CHT 中定义但 XML 中无对应控件
        </p>
        <p class="text-xs text-neutral-400 mt-0.5">
          output.cht : 行 42 | 规则: JOIN_MISMATCH
        </p>
      </div>
    </div>

    <!-- Critical 项 -->
    <div class="
      flex items-start gap-3
      px-4 py-2.5
      bg-red-50
      hover:bg-red-100
      cursor-pointer
    ">
      <XCircleIcon class="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
      <div>
        <p class="text-sm text-red-800 font-medium">
          Board 2 声明了 COM 端口但未配置波特率
        </p>
        <p class="text-xs text-red-500 mt-0.5">
          Project.xml : 行 18 | 规则: MISSING_BAUDRATE
        </p>
      </div>
    </div>
  </div>
</div>
```

**交互**：点击某条校验项 -> 代码面板自动滚动到对应行并高亮。

---

#### 4.4.9 `DownloadBar`

**职责**：下载按钮组。

```typescript
interface DownloadBarProps {
  onDownload: (type: 'xml' | 'cht' | 'zip') => void
  isDownloading?: Record<'xml' | 'cht' | 'zip', boolean>
  hasCriticalErrors: boolean  // 有 Critical 错误时显示警告
}
```

**样式**：

```html
<div class="
  flex items-center justify-between
  px-4 py-4
  border-t border-neutral-200
  bg-white
">
  <!-- Critical 警告 -->
  <p class="text-xs text-red-500 flex items-center gap-1" v-if="hasCritical">
    <XCircleIcon class="w-3.5 h-3.5" />
    存在 Critical 错误，建议修复后再下载
  </p>
  <div class="flex-1" v-else />

  <!-- 按钮组 -->
  <div class="flex items-center gap-2">
    <button class="
      px-4 py-2 text-sm font-medium
      text-neutral-700 bg-white
      border border-neutral-300 rounded-md
      hover:bg-neutral-50
      flex items-center gap-2
    ">
      <ArrowDownTrayIcon class="w-4 h-4" />
      下载 XML
    </button>
    <button class="
      px-4 py-2 text-sm font-medium
      text-neutral-700 bg-white
      border border-neutral-300 rounded-md
      hover:bg-neutral-50
      flex items-center gap-2
    ">
      <ArrowDownTrayIcon class="w-4 h-4" />
      下载 .cht
    </button>
    <button class="
      px-4 py-2 text-sm font-medium
      text-white bg-blue-600
      rounded-md
      hover:bg-blue-700
      flex items-center gap-2
    ">
      <ArchiveBoxIcon class="w-4 h-4" />
      打包 .zip
    </button>
  </div>
</div>
```

---

#### 4.4.10 `FullscreenOverlay`

**职责**：全屏展示某个文件的代码。

```typescript
interface FullscreenOverlayProps {
  isOpen: boolean
  onClose: () => void
  fileName: string
  fileType: 'xml' | 'cht'
  content: string
  onCopy: () => void
}
```

**交互**：
- Escape 键关闭全屏
- 全屏状态下搜索功能依然可用
- 右上角显示关闭按钮 + 复制按钮

**样式**：固定定位覆盖全屏，`z-50`，深色背景。

```html
<div class="fixed inset-0 z-50 bg-neutral-900 flex flex-col">
  <div class="flex items-center justify-between px-4 py-2 bg-neutral-800">
    <span class="text-sm text-neutral-300 font-mono">Project.xml</span>
    <div class="flex items-center gap-2">
      <button class="text-neutral-400 hover:text-white">复制</button>
      <button class="text-neutral-400 hover:text-white">退出全屏 (Esc)</button>
    </div>
  </div>
  <div class="flex-1 overflow-auto">
    <!-- CodeBlock -->
  </div>
</div>
```

---

### 4.5 交互流程

#### 4.5.1 用户旅程

```
生成完毕，ResultView 出现在对话流中
     │
     v
默认分栏模式，左侧 XML 右侧 CHT
     │
     ├─ 浏览代码 ──> 上下滚动查看
     ├─ Ctrl+F 搜索 ──> 搜索框出现 ──> 输入关键词 ──> 高亮匹配 ──> Enter 跳转下一个
     ├─ 全屏某侧 ──> 点击全屏按钮 ──> 覆盖式全屏 ──> Esc 退出
     │
     v
查看底部校验报告
     │
     ├─ 无 Critical ──> 直接下载
     ├─ 有 Warning ──> 点击查看详情 ──> 跳转到对应代码行
     ├─ 有 Critical ──> 红色醒目提示 ──> 建议修复（回到对话修改需求）
     │
     v
下载文件
     │
     ├─ 点击"下载 XML" ──> 浏览器下载 Project.xml
     ├─ 点击"下载 .cht" ──> 浏览器下载 output.cht
     └─ 点击"打包 .zip" ──> 浏览器下载 project.zip (含两个文件)

多版本场景：
     │
     v
版本选择器切换到旧版本 ──> 代码内容切换
     │
     v
点击"Diff 对比" ──> 选择基准版本 ──> 显示 diff 视图
     │
     ├─ 绿色行 = 新增
     ├─ 红色行 = 删除
     └─ 行内黄色高亮 = 修改
```

#### 4.5.2 状态转换

| 当前状态 | 触发事件 | 下一状态 | UI 变化 |
|----------|----------|----------|---------|
| Split View | 点击"标签"按钮 | Tab View | 分栏变为标签页 |
| Tab View | 点击"分栏"按钮 | Split View | 标签页变为分栏 |
| Normal | Ctrl+F | Search Active | 搜索框出现 |
| Search Active | Escape | Normal | 搜索框消失 |
| Normal | 点击"全屏" | Fullscreen | 覆盖式全屏 |
| Fullscreen | Escape / 点击退出 | Normal | 回到分栏/标签 |
| Normal | 点击"Diff 对比" | Diff Mode | 代码区变为 diff 视图 |
| Diff Mode | 再次点击 | Normal | 恢复正常视图 |
| Normal | 版本选择器切换 | Loading | 加载新版本内容 |
| Loading | 加载完成 | Normal | 显示新版本代码 |
| Any | 点击校验项 | Scroll to Line | 对应面板滚动到指定行并高亮 |

#### 4.5.3 复制到剪贴板交互

1. 点击"复制"按钮
2. 图标从 ClipboardIcon 变为 CheckIcon（绿色）
3. 显示 Toast："已复制到剪贴板"
4. 2 秒后图标恢复

---

## 5. 共享组件库

以下组件在两个页面中共享使用。

### 5.1 `Toast`

```typescript
interface ToastProps {
  message: string
  type: 'success' | 'error' | 'info' | 'warning'
  duration?: number           // 默认 3000ms
  onClose: () => void
}
```

### 5.2 `Badge`

```typescript
interface BadgeProps {
  label: string
  variant: 'blue' | 'green' | 'amber' | 'red' | 'purple' | 'neutral' | 'indigo'
  size?: 'sm' | 'md'
}
```

### 5.3 `ConfirmPopover`

```typescript
interface ConfirmPopoverProps {
  trigger: React.ReactNode
  title: string
  message: string
  confirmLabel?: string       // 默认 "确认"
  cancelLabel?: string        // 默认 "取消"
  onConfirm: () => void
  variant?: 'danger' | 'default'
}
```

用于删除行的二次确认。使用 Popover 而非 Modal，更轻量，不打断上下文。

### 5.4 `EmptyState`

```typescript
interface EmptyStateProps {
  icon?: React.ReactNode
  title: string
  description?: string
  action?: {
    label: string
    onClick: () => void
  }
}
```

### 5.5 `Spinner`

```typescript
interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg'   // 16px / 24px / 32px
  color?: string               // 默认 currentColor
}
```

---

## 6. 无障碍访问（A11y）

### 6.1 关键实践

| 组件 | A11y 要求 |
|------|-----------|
| EditableTable | 使用 `role="grid"`, `role="gridcell"`; 单元格 `tabindex="0"` 支持键盘导航; Enter 进入编辑 |
| TabGroup | `role="tablist"`, `role="tab"`, `role="tabpanel"`; 方向键切换标签 |
| MissingInfoAlert | `role="alert"`, `aria-live="polite"` |
| ConfirmDialog | `role="dialog"`, `aria-modal="true"`, `aria-labelledby`; 焦点陷阱; Escape 关闭 |
| CodePanel | `aria-label="Project.xml 代码预览"`; 搜索框 `aria-label="在代码中搜索"` |
| DownloadBar | 按钮有明确 `aria-label`; 下载中状态用 `aria-busy="true"` |
| ValidationReport | 列表使用 `role="list"`, `role="listitem"`; Critical 用 `role="alert"` |
| FullscreenOverlay | 焦点陷阱; `role="dialog"`; Escape 关闭 |

### 6.2 键盘操作速查

| 按键 | 上下文 | 操作 |
|------|--------|------|
| Tab | 全局 | 在可交互元素间移动焦点 |
| Enter | 表格单元格 | 进入编辑模式 |
| Escape | 编辑中 / 搜索 / 弹窗 / 全屏 | 退出当前模式 |
| Arrow Left/Right | TabGroup | 切换标签页 |
| Ctrl+F | CodePanel | 打开搜索 |
| Ctrl+C (代码区) | CodePanel | 复制选中文本 |

### 6.3 色彩对比度

所有文本颜色确保与背景的对比度 >= 4.5:1（WCAG AA）：

| 文字 | 背景 | 对比度 |
|------|------|--------|
| neutral-900 (#111827) | white (#FFFFFF) | 17.4:1 |
| neutral-700 (#374151) | white (#FFFFFF) | 10.3:1 |
| neutral-500 (#6B7280) | white (#FFFFFF) | 5.2:1 |
| amber-800 (#92400E) | amber-50 (#FFFBEB) | 7.8:1 |
| red-800 (#991B1B) | red-50 (#FEF2F2) | 7.1:1 |
| neutral-300 (#D1D5DB) | neutral-900 (#111827) | 10.1:1 |

---

## 7. 图标清单

使用 Heroicons（Outline 风格，与 Tailwind 生态一致）。

| 图标 | 组件 | Heroicons 名称 |
|------|------|----------------|
| 警告三角 | MissingInfoAlert, ValidationReport | `ExclamationTriangleIcon` |
| 信息圆 | ImagePathNotice | `InformationCircleIcon` |
| 错误圆 | ValidationReport (Critical) | `XCircleIcon` |
| 删除/垃圾桶 | RowActions | `TrashIcon` |
| 复制文档 | RowActions, CodePanel | `DocumentDuplicateIcon` |
| 剪贴板 | CodePanel (复制) | `ClipboardIcon` |
| 打勾 | 复制成功反馈 | `CheckIcon` |
| 全屏展开 | CodePanel | `ArrowsPointingOutIcon` |
| 全屏收起 | FullscreenOverlay | `ArrowsPointingInIcon` |
| 搜索放大镜 | ResultToolbar | `MagnifyingGlassIcon` |
| 上箭头 | SearchOverlay | `ChevronUpIcon` |
| 下箭头 | SearchOverlay | `ChevronDownIcon` |
| 关闭 X | SearchOverlay, Dialog | `XMarkIcon` |
| 下载 | DownloadBar | `ArrowDownTrayIcon` |
| 打包 | DownloadBar (zip) | `ArchiveBoxIcon` |
| 文档 | CodePanel header | `DocumentIcon` |
| 加号 | AddRowButton | `PlusIcon` |
| 加载中 | ActionBar (生成中) | `ArrowPathIcon` (animate-spin) |

---

## 8. 开发交付清单

### 8.1 ConfirmationView 文件结构

```
src/features/confirmation/
├── ConfirmationView.tsx           # 顶层容器
├── store.ts                       # Zustand store
├── types.ts                       # TypeScript 接口定义
├── components/
│   ├── MissingInfoAlert.tsx
│   ├── ImagePathNotice.tsx
│   ├── TabGroup.tsx
│   ├── EditableTable.tsx          # 通用可编辑表格
│   ├── EditableCell.tsx           # 单元格内联编辑
│   ├── JoinSourceBadge.tsx
│   ├── PageTypeBadge.tsx
│   ├── RowActions.tsx
│   ├── AddRowButton.tsx
│   ├── ActionBar.tsx
│   └── ConfirmDialog.tsx
├── hooks/
│   ├── useEditableTable.ts        # 表格编辑逻辑
│   └── useKeyboardNavigation.ts   # 键盘导航
└── config/
    ├── deviceColumns.ts           # 设备表列定义
    ├── functionColumns.ts         # 功能表列定义
    └── pageColumns.ts             # 页面表列定义
```

### 8.2 ResultView 文件结构

```
src/features/result/
├── ResultView.tsx                 # 顶层容器
├── store.ts                       # Zustand store
├── types.ts                       # TypeScript 接口定义
├── components/
│   ├── ResultToolbar.tsx
│   ├── VersionSelector.tsx
│   ├── ViewModeToggle.tsx
│   ├── CodePanel.tsx
│   ├── CodeBlock.tsx              # 代码渲染 + 高亮
│   ├── LineNumbers.tsx
│   ├── ResizableDivider.tsx
│   ├── SearchOverlay.tsx
│   ├── DiffView.tsx
│   ├── ValidationReport.tsx
│   ├── ValidationItem.tsx
│   ├── DownloadBar.tsx
│   └── FullscreenOverlay.tsx
├── hooks/
│   ├── useCodeSearch.ts           # 搜索逻辑
│   ├── useResizable.ts            # 拖拽分割线
│   ├── useDiff.ts                 # Diff 计算
│   ├── useKeyboardShortcuts.ts    # 快捷键
│   └── useCopyToClipboard.ts      # 复制到剪贴板
└── utils/
    ├── highlight.ts               # 代码高亮配置
    └── diff.ts                    # Diff 工具函数
```

### 8.3 共享组件

```
src/components/shared/
├── Badge.tsx
├── Toast.tsx
├── ConfirmPopover.tsx
├── EmptyState.tsx
├── Spinner.tsx
└── index.ts                       # barrel export
```

### 8.4 开发优先级

| 优先级 | 组件 | 说明 |
|--------|------|------|
| P0 | EditableTable + EditableCell | 核心交互，建议最先开发并充分测试 |
| P0 | MissingInfoAlert | 简单但业务上最重要（用户必须先看到缺失信息） |
| P0 | CodePanel + CodeBlock | 结果预览的核心 |
| P0 | ValidationReport | 校验报告影响用户决策 |
| P1 | ActionBar + ConfirmDialog | 生成流程闭环 |
| P1 | DownloadBar | 交付物获取 |
| P1 | SearchOverlay | 代码搜索 |
| P2 | ResizableDivider | 分栏拖拽（可先用固定 50/50） |
| P2 | VersionSelector + DiffView | 多版本对比（第一期可不做） |
| P2 | FullscreenOverlay | 全屏查看（锦上添花） |

---

## 9. 动画与过渡

| 场景 | 动画 | 时长 | 缓动 |
|------|------|------|------|
| 标签页切换 | 内容 fade in | 150ms | ease-out |
| 新增行 | slide down + fade in | 200ms | ease-out |
| 删除行 | fade out + collapse | 200ms | ease-in |
| 搜索框出现 | slide down from top | 150ms | ease-out |
| Toast 出现 | slide in from right | 300ms | ease-out |
| Toast 消失 | fade out | 200ms | ease-in |
| 全屏展开 | scale from panel position | 200ms | ease-out |
| 编辑单元格 | 无动画，即时切换 | 0ms | -- |
| 按钮 hover | background color transition | 150ms | ease |

推荐使用 `framer-motion` 或 Tailwind 内置 `transition-*` 类实现，根据项目复杂度选择。

---

## 10. 技术选型建议

| 功能 | 推荐方案 | 备选方案 |
|------|----------|----------|
| 代码高亮 | Shiki (SSR-friendly, 精确高亮) | Prism.js (轻量) |
| Diff 引擎 | diff npm 包 + 自定义渲染 | Monaco Editor diffEditor (重但功能强) |
| 表格编辑 | 自研 EditableTable (贴合需求) | TanStack Table (功能过剩) |
| 搜索匹配 | 正则匹配 + 行号索引 | Fuse.js (模糊搜索不适合代码) |
| 拖拽分割线 | react-resizable-panels | 自研 (mousedown + mousemove) |
| 弹窗 | Headless UI Dialog | Radix Dialog |
| Toast | react-hot-toast | Sonner |
| 图标 | @heroicons/react | Lucide React |
| 文件下载 | file-saver + JSZip (zip打包) | 原生 Blob + URL.createObjectURL |
| 状态管理 | Zustand | Jotai (如需更细粒度) |

---

*本文档为 MDK Web Platform Phase 6 的 UI/UX 设计方案，供前端开发参考实施。*
