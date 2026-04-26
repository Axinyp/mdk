# UI/UX 设计方案：MDK 新功能模块

**设计时间**：2026/04/26
**目标平台**：Web Desktop（主断点 1280px+）
**技术栈**：React + TypeScript + Tailwind CSS + Plus Jakarta Sans

---

## 全局设计令牌（继承现有系统）

```
主暗色：slate-700 (#334155) / slate-900 (#0f172a)
表面色：white，边框 slate-200
强调色：
  - blue-600   → 解析中 (parsing)
  - orange-400 → 追问/警告 (clarifying)
  - emerald-500 → 已完成 (completed)
  - red-500    → 错误 (error)
圆角：rounded-xl (12px) 卡片 / rounded-2xl (16px) 气泡
阴影：shadow-sm（贴地）/ shadow-md（悬浮）/ shadow-lg（抽屉）
过渡：duration-200 ease-out（微交互） / duration-300 ease-out（面板）
     duration-150 ease-in（退出）
字体：Plus Jakarta Sans 300/400/500/600/700
```

---

## Feature 1：多轮追问 UX 升级 — `ClarificationCard`

### 1.1 设计目标

**用户目标**：在 AI 追问时，清晰知道"还差哪些信息"并快速逐条作答。
**业务目标**：减少追问轮次，提升解析成功率，避免用户在长聊天记录中迷失。

### 1.2 页面区块变化（clarifying 状态）

```
+---------------------------+-----------------------------+
|  Chat 列（55%）            |  右侧面板（45%）             |
|                           |                             |
|  ...历史消息...             |  ┌─────────────────────┐   |
|                           |  │  ClarificationCard   │   |
|  ┌─ AI 气泡（orange）────┐ |  │                     │   |
|  │  ⚠ 我需要确认以下信息  │ |  │  缺失信息            │   |
|  │                      │ |  │  ━━━━━━━━━━━━━━━━━  │   |
|  │  1. 品牌型号是什么？   │ |  │  ① 品牌型号   ○     │   |
|  │  2. 支持的通信协议？   │ |  │  ② 通信协议   ○     │   |
|  │  3. 控制指令格式？     │ |  │  ③ 控制指令格式 ○   │   |
|  └──────────────────────┘ |  │                     │   |
|                           |  │  ── 进度 ──          │   |
|  用户输入框                 |  │  已收集 0 / 3 项     │   |
|                           |  │  [░░░░░░░░░░░░░░░]  │   |
+---------------------------+  └─────────────────────┘   |
                                                          |
```

### 1.3 组件树

```
ClarificationCard
├── CardHeader
│   ├── OrangeIcon (AlertCircle)
│   └── Title "缺失信息"
├── ItemList
│   └── ClarificationItem × N
│       ├── IndexBadge  ("①②③")
│       ├── QuestionText
│       └── StatusDot (待回答/已回答)
├── ProgressSection
│   ├── ProgressLabel "已收集 X / N 项信息"
│   └── ProgressBar
└── HintText "请在左侧对话框逐一回答"
```

### 1.4 Tailwind 精确类决策

#### 卡片容器
```tsx
// 主卡片
<div className="
  bg-orange-50
  border border-orange-200
  rounded-xl
  p-5
  shadow-sm
  flex flex-col gap-4
">
```

#### 卡片标题行
```tsx
<div className="flex items-center gap-2">
  {/* Heroicons AlertCircle, 20px */}
  <AlertCircleIcon className="w-5 h-5 text-orange-500 flex-shrink-0" />
  <span className="text-sm font-600 text-orange-700 tracking-wide">
    缺失信息
  </span>
</div>
```

#### 分隔线
```tsx
<div className="h-px bg-orange-200" />
```

#### 单条追问项（待回答状态）
```tsx
<div className="
  flex items-start gap-3
  p-3
  rounded-lg
  bg-white
  border border-orange-100
  transition-all duration-300 ease-out
">
  {/* 序号徽标 */}
  <span className="
    inline-flex items-center justify-center
    w-5 h-5
    rounded-full
    bg-orange-100 text-orange-600
    text-xs font-700
    flex-shrink-0 mt-0.5
  ">1</span>
  
  <p className="text-sm text-slate-700 leading-relaxed flex-1">
    品牌型号是什么？
  </p>
  
  {/* 状态点 — 待回答 */}
  <div className="
    w-2 h-2 rounded-full
    bg-orange-300
    flex-shrink-0 mt-1.5
    animate-pulse
  " />
</div>
```

#### 单条追问项（已回答状态）—— fade + 绿色变化
```tsx
// 已回答：border 变 emerald，背景变浅绿，状态点变实心绿
<div className="
  flex items-start gap-3
  p-3
  rounded-lg
  bg-emerald-50
  border border-emerald-200
  transition-all duration-500 ease-out
  opacity-60
">
  <span className="
    inline-flex items-center justify-center
    w-5 h-5 rounded-full
    bg-emerald-100 text-emerald-600
    text-xs font-700
    flex-shrink-0 mt-0.5
  ">✓</span>
  
  <p className="text-sm text-slate-400 line-through leading-relaxed flex-1">
    品牌型号是什么？
  </p>
  
  <div className="
    w-2 h-2 rounded-full
    bg-emerald-400
    flex-shrink-0 mt-1.5
  " />
</div>
```

#### 进度条区域
```tsx
<div className="flex flex-col gap-2">
  <div className="flex justify-between items-center">
    <span className="text-xs text-slate-500">已收集信息</span>
    <span className="text-xs font-600 text-orange-600">
      {collected} / {total} 项
    </span>
  </div>
  
  {/* 轨道 */}
  <div className="h-1.5 bg-orange-100 rounded-full overflow-hidden">
    {/* 填充条 */}
    <div
      className="
        h-full
        bg-gradient-to-r from-orange-400 to-orange-500
        rounded-full
        transition-all duration-500 ease-out
      "
      style={{ width: `${(collected / total) * 100}%` }}
    />
  </div>
</div>
```

#### 提示文字
```tsx
<p className="text-xs text-slate-400 text-center">
  请在左侧对话框逐一回答上述问题
</p>
```

### 1.5 AI 气泡 — clarifying 样式

AI 消息气泡在 clarifying 时叠加 orange tint：

```tsx
// 普通 AI 气泡：bg-slate-100 border border-slate-200
// clarifying AI 气泡：
<div className="
  max-w-[85%]
  bg-orange-50
  border border-orange-200
  rounded-2xl rounded-tl-sm
  px-4 py-3
  shadow-sm
">
  {/* 追问头部标签 */}
  <div className="
    inline-flex items-center gap-1.5
    px-2 py-0.5
    bg-orange-100
    rounded-full
    mb-2
  ">
    <div className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse" />
    <span className="text-xs font-500 text-orange-600">需要确认信息</span>
  </div>
  
  {/* 问题列表 */}
  <ol className="flex flex-col gap-2">
    {questions.map((q, i) => (
      <li key={i} className="flex gap-2 text-sm text-slate-700">
        <span className="
          font-600 text-orange-500
          flex-shrink-0 w-4 text-right
        ">{i + 1}.</span>
        <span className="leading-relaxed">{q}</span>
      </li>
    ))}
  </ol>
</div>
```

### 1.6 交互状态流转

| 状态 | ClarificationItem 外观 | 动画 |
|------|----------------------|------|
| 待回答 | white bg + orange border + 脉冲橙点 | animate-pulse on dot |
| 正在消化回答 | 轻微 opacity-80 + skeleton shimmer | 150ms ease-in |
| 已回答 | emerald bg + strikethrough text + 实心绿点 | 300ms ease-out，opacity 0.6 |
| 全部完成 | 整卡片 fade-out + 右面板切换到 ConfirmationView | 500ms delay 后替换 |

### 1.7 动效规范

```
单项完成动画：
  1. 文字 color 从 slate-700 → slate-400（200ms）
  2. 文字添加 line-through（即时）
  3. 背景 bg-white → bg-emerald-50（300ms）
  4. border 从 orange-100 → emerald-200（300ms）
  5. 状态点 bg-orange-300 → bg-emerald-400（200ms）
  6. opacity → 0.6（200ms，延迟 150ms）

进度条：
  width 过渡：transition-all duration-500 ease-out

全部完成后退场：
  整个 ClarificationCard：opacity 0 + translateX(16px)（300ms ease-in）
  ConfirmationView 入场：opacity 1 + translateX 0（300ms ease-out，延迟 200ms）
```

### 1.8 Props 接口

```typescript
interface ClarificationItem {
  id: string
  question: string
  answered: boolean
}

interface ClarificationCardProps {
  items: ClarificationItem[]
  collectedCount: number          // 已收集项目数
  totalCount: number              // 总问题数
  onAllAnswered?: () => void      // 全部回答完成回调
}
```

---

## Feature 2：协议上传抽屉 — `ProtocolUploadDrawer`

### 2.1 设计目标

**用户目标**：当遇到未知设备时，能零摩擦地提交协议文档，不打断主流程。
**业务目标**：积累协议库，提升平台覆盖率。

### 2.2 触发入口 — AI 气泡内联操作按钮

当 AI 消息类型为 `unknown_device` 时，在气泡底部追加：

```tsx
{/* AI 气泡尾部 — 协议上传 CTA */}
<div className="
  mt-3 pt-3
  border-t border-slate-200
  flex items-center justify-between
">
  <span className="text-xs text-slate-400">
    找不到此设备的协议文档
  </span>
  <button
    onClick={openDrawer}
    className="
      inline-flex items-center gap-1.5
      px-3 py-1.5
      bg-blue-600 hover:bg-blue-700
      text-white text-xs font-600
      rounded-lg
      transition-colors duration-150
      focus-visible:outline-2 focus-visible:outline-blue-400
      focus-visible:outline-offset-2
    "
  >
    <UploadIcon className="w-3.5 h-3.5" />
    上传协议
  </button>
</div>
```

### 2.3 抽屉布局结构

```
+----------------------------------------+
| Drawer（width: 480px，固定右侧，全高）    |
|                                        |
| ┌── Header ─────────────────────────┐  |
| │  [UploadIcon]  提交协议文档    [✕] │  |
| └────────────────────────────────────┘  |
|                                        |
| ┌── Tabs ────────────────────────────┐  |
| │  [粘贴文本]  [上传文件]             │  |
| └────────────────────────────────────┘  |
|                                        |
| ┌── Tab Content ─────────────────────┐  |
| │                                    │  |
| │  (粘贴文本 Tab)                     │  |
| │  ┌────────────────────────────┐   │  |
| │  │  textarea                  │   │  |
| │  │  min-h: 200px              │   │  |
| │  └────────────────────────────┘   │  |
| │                                    │  |
| │  (上传文件 Tab)                     │  |
| │  ┌── Drop Zone ──────────────┐    │  |
| │  │  [CloudUploadIcon]        │    │  |
| │  │  拖拽文件到此处             │    │  |
| │  │  或点击选择文件             │    │  |
| │  │  .txt .md .pdf  最大 10MB │    │  |
| │  └────────────────────────────┘   │  |
| └────────────────────────────────────┘  |
|                                        |
| ┌── 设备信息（Auto-fill）─────────────┐  |
| │  品牌  [___________]               │  |
| │  型号  [___________]               │  |
| └────────────────────────────────────┘  |
|                                        |
| ┌── Footer ──────────────────────────┐  |
| │        [提交审核]                   │  |
| └────────────────────────────────────┘  |
+----------------------------------------+
```

### 2.4 组件树

```
ProtocolUploadDrawer
├── DrawerOverlay                  // 半透明遮罩，点击关闭
├── DrawerPanel
│   ├── DrawerHeader
│   │   ├── HeaderIcon (Upload)
│   │   ├── Title "提交协议文档"
│   │   └── CloseButton
│   ├── TabSwitcher
│   │   ├── Tab "粘贴文本"
│   │   └── Tab "上传文件"
│   ├── TabContent
│   │   ├── PasteTextTab
│   │   │   └── ProtocolTextarea
│   │   └── UploadFileTab
│   │       ├── DropZone
│   │       │   ├── UploadIcon
│   │       │   ├── DropLabel
│   │       │   └── FileInput (hidden)
│   │       └── FilePreview (上传后显示)
│   ├── DeviceInfoFields
│   │   ├── BrandInput
│   │   └── ModelInput
│   └── DrawerFooter
│       └── SubmitButton
```

### 2.5 Tailwind 精确类决策

#### 抽屉遮罩 + 面板入场动画
```tsx
// 遮罩
<div className="
  fixed inset-0
  bg-slate-900/40
  backdrop-blur-[2px]
  z-40
  transition-opacity duration-300
  data-[state=open]:opacity-100
  data-[state=closed]:opacity-0
" onClick={onClose} />

// 面板
<div className="
  fixed right-0 top-0 bottom-0
  w-[480px]
  bg-white
  shadow-2xl
  z-50
  flex flex-col
  border-l border-slate-200
  transition-transform duration-300 ease-out
  data-[state=open]:translate-x-0
  data-[state=closed]:translate-x-full
">
```

#### Header 区
```tsx
<div className="
  flex items-center justify-between
  px-6 py-4
  border-b border-slate-200
  flex-shrink-0
">
  <div className="flex items-center gap-2.5">
    <div className="
      w-8 h-8
      bg-blue-50
      rounded-lg
      flex items-center justify-center
    ">
      <UploadIcon className="w-4 h-4 text-blue-600" />
    </div>
    <h2 className="text-base font-600 text-slate-900">
      提交协议文档
    </h2>
  </div>
  <button className="
    w-8 h-8
    flex items-center justify-center
    rounded-lg
    text-slate-400 hover:text-slate-600
    hover:bg-slate-100
    transition-colors duration-150
  ">
    <XIcon className="w-4 h-4" />
  </button>
</div>
```

#### Tab 切换器
```tsx
<div className="
  flex
  mx-6 mt-5
  bg-slate-100
  rounded-lg
  p-0.5
  flex-shrink-0
">
  {/* 激活 Tab */}
  <button className="
    flex-1
    py-2 px-4
    text-sm font-500
    text-slate-900
    bg-white
    rounded-[7px]
    shadow-sm
    transition-all duration-200
  ">粘贴文本</button>
  
  {/* 非激活 Tab */}
  <button className="
    flex-1
    py-2 px-4
    text-sm font-500
    text-slate-500
    hover:text-slate-700
    transition-colors duration-150
  ">上传文件</button>
</div>
```

#### 粘贴文本 Tab — Textarea
```tsx
<div className="px-6 pt-4 flex-1 flex flex-col min-h-0">
  <textarea
    className="
      w-full flex-1
      min-h-[200px]
      px-4 py-3
      bg-slate-50
      border border-slate-200
      rounded-xl
      text-sm text-slate-700
      placeholder:text-slate-400
      leading-relaxed
      resize-none
      focus:outline-none
      focus:ring-2 focus:ring-blue-500/30
      focus:border-blue-400
      transition-all duration-200
    "
    placeholder="粘贴设备说明书中的通信协议部分..."
  />
  <p className="mt-2 text-xs text-slate-400">
    支持 RS232、RS485、TCP/IP 等通信协议格式
  </p>
</div>
```

#### 上传文件 Tab — DropZone（空态）
```tsx
<div className="px-6 pt-4">
  <div
    className="
      border-2 border-dashed border-slate-300
      hover:border-blue-400
      rounded-xl
      p-8
      flex flex-col items-center gap-3
      bg-slate-50
      hover:bg-blue-50/40
      cursor-pointer
      transition-all duration-200
      group
    "
    onDragOver={...}
    onDrop={...}
    onClick={() => fileInputRef.current?.click()}
  >
    <div className="
      w-12 h-12
      bg-slate-200
      group-hover:bg-blue-100
      rounded-xl
      flex items-center justify-center
      transition-colors duration-200
    ">
      <CloudUploadIcon className="
        w-6 h-6
        text-slate-400
        group-hover:text-blue-500
        transition-colors duration-200
      " />
    </div>
    <div className="text-center">
      <p className="text-sm font-500 text-slate-600">
        拖拽文件到此处
      </p>
      <p className="text-xs text-slate-400 mt-0.5">
        或 <span className="text-blue-500 underline">点击选择文件</span>
      </p>
    </div>
    <p className="text-xs text-slate-400">
      支持 .txt .md .pdf · 最大 10MB
    </p>
    <input
      ref={fileInputRef}
      type="file"
      accept=".txt,.md,.pdf"
      className="hidden"
      onChange={...}
    />
  </div>
</div>
```

#### 上传文件 Tab — DropZone（拖拽激活态）
```
border-2 border-blue-400 bg-blue-50
内部图标 text-blue-500
文字变为 "松开以上传"
```

#### 上传文件 Tab — 文件预览态（已选择）
```tsx
<div className="
  flex items-center gap-3
  p-3
  bg-slate-50
  border border-slate-200
  rounded-xl
  mt-3
">
  <div className="
    w-8 h-8
    bg-blue-100
    rounded-lg
    flex items-center justify-center
    flex-shrink-0
  ">
    <DocumentIcon className="w-4 h-4 text-blue-600" />
  </div>
  <div className="flex-1 min-w-0">
    <p className="text-sm font-500 text-slate-700 truncate">
      {fileName}
    </p>
    <p className="text-xs text-slate-400">{fileSize}</p>
  </div>
  <button className="
    text-slate-400 hover:text-red-500
    transition-colors duration-150
  ">
    <XIcon className="w-4 h-4" />
  </button>
</div>
```

#### 设备信息字段
```tsx
<div className="
  px-6 py-4
  border-t border-slate-100
  flex flex-col gap-3
  flex-shrink-0
">
  <p className="text-xs font-600 text-slate-500 uppercase tracking-wider">
    设备信息
  </p>
  <div className="grid grid-cols-2 gap-3">
    {/* 品牌 */}
    <div>
      <label className="block text-xs font-500 text-slate-600 mb-1">
        品牌
      </label>
      <input
        className="
          w-full px-3 py-2
          bg-white
          border border-slate-200
          rounded-lg
          text-sm text-slate-700
          focus:outline-none
          focus:ring-2 focus:ring-blue-500/30
          focus:border-blue-400
          transition-all duration-200
        "
        defaultValue={autoFilledBrand}
      />
    </div>
    {/* 型号 */}
    <div>
      <label className="block text-xs font-500 text-slate-600 mb-1">
        型号
      </label>
      <input
        className="
          w-full px-3 py-2
          bg-white
          border border-slate-200
          rounded-lg
          text-sm text-slate-700
          focus:outline-none
          focus:ring-2 focus:ring-blue-500/30
          focus:border-blue-400
          transition-all duration-200
        "
        defaultValue={autoFilledModel}
      />
    </div>
  </div>
</div>
```

#### Footer — 提交按钮
```tsx
{/* 底部固定区 */}
<div className="
  px-6 py-4
  border-t border-slate-200
  flex-shrink-0
">
  {/* 空闲态 */}
  <button className="
    w-full py-2.5
    bg-slate-900 hover:bg-slate-700
    text-white text-sm font-600
    rounded-xl
    transition-colors duration-150
    focus-visible:outline-2 focus-visible:outline-slate-400
    focus-visible:outline-offset-2
  ">
    提交审核
  </button>
  
  {/* Loading 态 */}
  <button disabled className="
    w-full py-2.5
    bg-slate-400
    text-white text-sm font-600
    rounded-xl
    flex items-center justify-center gap-2
    cursor-not-allowed
  ">
    <SpinnerIcon className="w-4 h-4 animate-spin" />
    提交中...
  </button>
</div>
```

#### 提交后 — 状态徽标（替换按钮区）
```tsx
{/* 提交成功后，在抽屉底部替换按钮 */}
<div className="
  px-6 py-4
  border-t border-slate-200
  flex items-center justify-center gap-2.5
">
  {/* 脉冲橙点 */}
  <div className="relative flex-shrink-0">
    <div className="
      w-2.5 h-2.5
      rounded-full
      bg-orange-400
      animate-pulse
    " />
    {/* 外环扩散 */}
    <div className="
      absolute inset-0
      rounded-full
      bg-orange-400/30
      animate-ping
    " />
  </div>
  <span className="text-sm font-500 text-orange-600">
    审核中...
  </span>
  <span className="text-xs text-slate-400">
    通常在 24 小时内处理
  </span>
</div>
```

### 2.6 交互状态流转

| 状态 | DropZone | 按钮 | 说明 |
|------|----------|------|------|
| Idle | 虚线灰边框 | 深色实心 | 默认 |
| DragOver | 蓝色边框 + 浅蓝背景 | — | 拖拽悬停 |
| FileSelected | 收起 DropZone，显示文件预览卡 | 可点击 | 已选文件 |
| Uploading | 禁用 | bg-slate-400 + spinner | 上传中 |
| Success | — | 替换为橙色"审核中"徽标 | 提交成功 |
| Error | 显示红色提示 | 恢复可用 | 上传失败 |

### 2.7 动效规范

```
抽屉入场：
  translateX(100%) → translateX(0)，300ms ease-out
  遮罩：opacity 0 → 0.4，200ms ease-out（同步）

抽屉退场：
  translateX(0) → translateX(100%)，250ms ease-in
  遮罩：opacity 0.4 → 0，150ms ease-in

DropZone hover：
  border-color 变化：200ms ease
  background 变化：200ms ease
  图标 color 变化：200ms ease

文件预览入场：
  opacity 0 + translateY(8px) → opacity 1 + translateY(0)，250ms ease-out

审核中徽标入场：
  opacity 0 + scale(0.95) → opacity 1 + scale(1)，300ms ease-out
```

### 2.8 Props 接口

```typescript
interface ProtocolUploadDrawerProps {
  isOpen: boolean
  onClose: () => void
  defaultBrand?: string           // AI 提取的品牌名，自动填充
  defaultModel?: string           // AI 提取的型号名，自动填充
  onSubmit: (payload: ProtocolSubmitPayload) => Promise<void>
}

interface ProtocolSubmitPayload {
  type: 'text' | 'file'
  content?: string                // 粘贴文本内容
  file?: File                     // 上传文件
  brand: string
  model: string
}
```

---

## Feature 3：管理后台 — 协议审核队列 `ProtocolReviewPanel`

### 3.1 设计目标

**用户目标（管理员）**：快速浏览待审核提交，对比原始文本与 AI 提取结果，一键批准或拒绝。
**业务目标**：提升审核效率，保证协议库数据质量。

### 3.2 tabs 标题区变化

在 `/admin/protocols` 页面，现有 Tab 栏添加"待审核"tab：

```tsx
{/* Tab 列表 */}
<div className="flex gap-1 border-b border-slate-200 px-6">
  <TabTrigger value="approved">已通过协议</TabTrigger>
  
  {/* 待审核 Tab — 带计数徽标 */}
  <TabTrigger value="pending" className="relative">
    待审核
    {pendingCount > 0 && (
      <span className="
        absolute -top-0.5 -right-3
        inline-flex items-center justify-center
        min-w-[18px] h-[18px]
        px-1
        bg-orange-400
        text-white text-[10px] font-700
        rounded-full
        leading-none
      ">
        {pendingCount > 99 ? '99+' : pendingCount}
      </span>
    )}
  </TabTrigger>
</div>
```

### 3.3 待审核列表布局（master-detail 模式）

```
+------------------------------------------------------------+
|  Tab: 待审核 [12]                                           |
+----------------------+-------------------------------------+
|  LIST（40%）          |  DETAIL PANEL（60%）                |
|                      |                                     |
|  ┌─ 行 1（选中）─────┐|  ┌─── 原始文本 ────┬── AI 提取 ──┐  |
|  │ Samsung QN85B    ││  │ 原始文本         │ 对比        │  |
|  │ 张三 · 10分钟前   ││  │ (scrollable)    │ (editable)  │  |
|  └──────────────────┘│  │ monospace       │ JSON view   │  |
|                      │  │                 │             │  |
|  ┌─ 行 2 ────────────┐│  ├────── 对比 ─────┼─────────────┤  |
|  │ Epson EB-L615U   ││  │                 │             │  |
|  │ 李四 · 1小时前    ││  └─────────────────┴─────────────┘  |
|  └──────────────────┘│                                     |
|                      │  ┌── 底部操作栏 ───────────────────┐  |
|  ┌─ 行 3 ────────────┐│  │  [拒绝] [编辑后批准] [直接批准] │  |
|  │ ...               ││  └────────────────────────────────┘  |
+----------------------+-------------------------------------+
```

### 3.4 组件树

```
ProtocolReviewPage
├── PageTabs
│   ├── Tab "已通过协议"
│   └── Tab "待审核" (with badge)
├── PendingTab
│   ├── PendingListPanel (left, w-[40%])
│   │   ├── ListHeader (count summary)
│   │   └── PendingListItem × N
│   │       ├── DeviceInfo (brand + model)
│   │       ├── SubmitterInfo (name + time)
│   │       └── TypeBadge (文本/文件)
│   └── ReviewDetailPanel (right, flex-1)
│       ├── DetailHeader
│       │   ├── DeviceTitle
│       │   └── SubmissionMeta
│       ├── SplitView
│       │   ├── RawTextPane (left 50%)
│       │   │   ├── PaneLabel "原始文本"
│       │   │   └── ScrollableText (mono font)
│       │   ├── DividerBar ("对比" label)
│       │   └── AIExtractPane (right 50%)
│       │       ├── PaneLabel "AI 提取结果"
│       │       └── EditableFieldList
│       │           ├── EditableField "brand"
│       │           ├── EditableField "model"
│       │           ├── EditableField "comm_type"
│       │           └── EditableField "content" (textarea)
│       └── ActionBar
│           ├── RejectButton
│           ├── RejectionReasonTextarea (条件渲染)
│           ├── EditApproveButton
│           └── ApproveButton
```

### 3.5 Tailwind 精确类决策

#### 列表面板容器
```tsx
<div className="
  w-[40%] flex-shrink-0
  border-r border-slate-200
  overflow-y-auto
  flex flex-col
">
  {/* 列表头 */}
  <div className="
    px-4 py-3
    border-b border-slate-100
    flex items-center justify-between
    flex-shrink-0
  ">
    <span className="text-xs font-600 text-slate-500 uppercase tracking-wider">
      待审核
    </span>
    <span className="text-xs text-slate-400">
      共 {total} 条
    </span>
  </div>
</div>
```

#### 列表行 — 默认态
```tsx
<div className="
  px-4 py-3.5
  border-b border-slate-100
  hover:bg-slate-50
  cursor-pointer
  transition-colors duration-150
  flex flex-col gap-1.5
">
  <div className="flex items-center justify-between">
    <span className="text-sm font-600 text-slate-800">
      Samsung · QN85B
    </span>
    {/* 类型徽标 */}
    <span className="
      px-1.5 py-0.5
      bg-slate-100 text-slate-500
      text-[10px] font-500
      rounded
    ">文本</span>
  </div>
  <div className="flex items-center gap-2 text-xs text-slate-400">
    <span>张三</span>
    <span>·</span>
    <span>10 分钟前</span>
  </div>
</div>
```

#### 列表行 — 选中态
```tsx
// 外层 div 追加：
className="... bg-blue-50 border-b border-blue-100"
// 品牌型号文字追加：
className="... text-blue-700"
// 左侧追加 3px 蓝色选中条：
<div className="absolute left-0 top-0 bottom-0 w-[3px] bg-blue-500 rounded-r" />
```

#### 详情面板 — 分栏容器
```tsx
<div className="flex-1 flex flex-col min-h-0">
  {/* 详情头 */}
  <div className="
    px-6 py-4
    border-b border-slate-200
    flex-shrink-0
  ">
    <h3 className="text-base font-600 text-slate-900">
      Samsung QN85B
    </h3>
    <p className="text-xs text-slate-400 mt-0.5">
      提交人：张三 · 2026/04/26 14:32 · 类型：粘贴文本
    </p>
  </div>
  
  {/* 双栏对比区 */}
  <div className="flex flex-1 min-h-0">
    {/* 左栏 — 原始文本 */}
    <div className="flex-1 flex flex-col min-h-0 border-r border-slate-200">
      <div className="
        px-4 py-2.5
        border-b border-slate-100
        flex items-center gap-2
        flex-shrink-0
      ">
        <div className="w-1.5 h-1.5 rounded-full bg-slate-400" />
        <span className="text-xs font-600 text-slate-500">原始文本</span>
      </div>
      <div className="
        flex-1 overflow-y-auto
        px-4 py-3
      ">
        <pre className="
          text-xs text-slate-600
          font-mono
          leading-relaxed
          whitespace-pre-wrap
          break-words
        ">{rawText}</pre>
      </div>
    </div>
    
    {/* 分隔线 — "对比" 标签 */}
    {/* 注意：分隔线已通过 border-r 实现，此处仅添加居中标签 */}
    {/* 可选：在两栏中间叠加一个绝对定位徽标 */}
    <div className="
      absolute
      left-[calc(40%+50%-18px)]
      top-1/2 -translate-y-1/2
      z-10
      px-2 py-1
      bg-white
      border border-slate-200
      rounded-full
      text-[10px] font-600
      text-slate-400
    ">对比</div>
    
    {/* 右栏 — AI 提取结果 */}
    <div className="flex-1 flex flex-col min-h-0">
      <div className="
        px-4 py-2.5
        border-b border-slate-100
        flex items-center gap-2
        flex-shrink-0
      ">
        <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
        <span className="text-xs font-600 text-slate-500">AI 提取结果</span>
        <span className="
          ml-auto
          px-1.5 py-0.5
          bg-blue-50 text-blue-500
          text-[10px] font-500
          rounded
        ">可编辑</span>
      </div>
      <div className="
        flex-1 overflow-y-auto
        px-4 py-3
        flex flex-col gap-3
      ">
        {/* 可编辑字段列表 */}
        {fields.map(field => (
          <EditableField key={field.key} {...field} />
        ))}
      </div>
    </div>
  </div>
</div>
```

#### AI 提取结果 — 可编辑字段
```tsx
// 单个字段
<div className="flex flex-col gap-1">
  <label className="text-[10px] font-600 text-slate-400 uppercase tracking-wider">
    {field.label}  {/* brand / model / comm_type */}
  </label>
  <input
    defaultValue={field.value}
    className="
      px-3 py-2
      bg-slate-50
      border border-slate-200
      rounded-lg
      text-sm font-mono text-slate-700
      focus:outline-none
      focus:ring-2 focus:ring-blue-500/30
      focus:border-blue-400
      focus:bg-white
      transition-all duration-150
    "
  />
</div>

// content 字段用 textarea
<div className="flex flex-col gap-1">
  <label className="text-[10px] font-600 text-slate-400 uppercase tracking-wider">
    content
  </label>
  <textarea
    rows={6}
    defaultValue={field.value}
    className="
      px-3 py-2
      bg-slate-50
      border border-slate-200
      rounded-lg
      text-xs font-mono text-slate-700
      leading-relaxed
      resize-y
      focus:outline-none
      focus:ring-2 focus:ring-blue-500/30
      focus:border-blue-400
      focus:bg-white
      transition-all duration-150
    "
  />
</div>
```

#### 底部操作栏
```tsx
<div className="
  px-6 py-4
  border-t border-slate-200
  flex items-center gap-3
  flex-shrink-0
">
  {/* 拒绝按钮 */}
  <button
    onClick={handleRejectClick}
    className="
      px-4 py-2
      border border-red-300
      text-red-500
      hover:bg-red-50
      text-sm font-500
      rounded-lg
      transition-colors duration-150
    "
  >拒绝</button>
  
  {/* 弹性空间 */}
  <div className="flex-1" />
  
  {/* 编辑后批准 */}
  <button
    onClick={handleEditApprove}
    className="
      px-4 py-2
      bg-slate-100
      hover:bg-slate-200
      text-slate-700
      text-sm font-500
      rounded-lg
      transition-colors duration-150
    "
  >编辑后批准</button>
  
  {/* 直接批准 */}
  <button
    onClick={handleApprove}
    className="
      px-4 py-2
      bg-emerald-500
      hover:bg-emerald-600
      text-white
      text-sm font-600
      rounded-lg
      transition-colors duration-150
      flex items-center gap-1.5
    "
  >
    <CheckIcon className="w-4 h-4" />
    直接批准
  </button>
</div>
```

#### 拒绝原因文本框（点击"拒绝"后展开）
```tsx
{/* 在操作栏上方，动画展开 */}
{isRejecting && (
  <div className="
    px-6 pb-3
    flex flex-col gap-2
    animate-in
  ">
    <label className="text-xs font-500 text-red-500">
      拒绝原因（将通知提交人）
    </label>
    <textarea
      autoFocus
      rows={3}
      placeholder="请说明拒绝原因..."
      className="
        w-full px-3 py-2
        bg-red-50
        border border-red-200
        rounded-lg
        text-sm text-slate-700
        placeholder:text-red-300
        resize-none
        focus:outline-none
        focus:ring-2 focus:ring-red-400/30
        focus:border-red-400
        transition-all duration-150
      "
    />
    <div className="flex justify-end gap-2">
      <button
        onClick={cancelReject}
        className="
          px-3 py-1.5
          text-xs font-500 text-slate-500
          hover:text-slate-700
          transition-colors
        "
      >取消</button>
      <button
        onClick={confirmReject}
        className="
          px-3 py-1.5
          bg-red-500 hover:bg-red-600
          text-white text-xs font-600
          rounded-lg
          transition-colors duration-150
        "
      >确认拒绝</button>
    </div>
  </div>
)}
```

### 3.6 交互状态流转

| 状态 | UI 变化 |
|------|---------|
| 列表空态 | 显示 EmptyState 插图 + "暂无待审核提交" |
| 选中一行 | 右侧 DetailPanel 滑入（translateX opacity），左侧行高亮蓝色 |
| 点击"拒绝" | 操作栏上方展开 RejectionReason 区域（max-h 0 → max-h-40，200ms ease-out）|
| 确认拒绝 | 该行从列表移除（opacity 0 + height 0，200ms），计数 -1 |
| 直接批准 | 同上，顶部出现 Toast "已批准：Samsung QN85B" (emerald) |
| 编辑后批准 | AI 提取栏高亮提示已修改字段，然后走批准流程 |

### 3.7 动效规范

```
列表行移除（批准/拒绝后）：
  height: auto → 0（300ms ease-in）
  opacity: 1 → 0（200ms ease-in）
  overflow: hidden

拒绝原因展开：
  max-height: 0 → 200px（250ms ease-out）
  opacity: 0 → 1（200ms ease-out，延迟 50ms）

DetailPanel 切换（选择不同行）：
  opacity: 1 → 0（100ms）→ opacity: 0 → 1（200ms）
  内容替换在中间 opacity=0 时完成

Toast 通知：
  右下角 slideInRight（translateX 100% → 0，300ms ease-out）
  3秒后 fadeOut（opacity 1 → 0，200ms ease-in）
```

---

## Feature 4：确认视图场景编辑器 — 第 4 个 Tab "场景模式"

### 4.1 设计目标

**用户目标**：在确认解析结果时，查看和编辑 AI 检测到的场景模式，或手动新增自定义场景。
**业务目标**：提升生成代码质量，减少场景配置错误。

### 4.2 Tab 栏变化

```tsx
// ConfirmationView.tsx 中的 Tab 列表
// 原有：设备  功能  页面
// 新增：场景模式

<TabsList>
  <TabsTrigger value="devices">
    设备 <Badge>{devices.length}</Badge>
  </TabsTrigger>
  <TabsTrigger value="functions">
    功能 <Badge>{functions.length}</Badge>
  </TabsTrigger>
  <TabsTrigger value="pages">
    页面 <Badge>{pages.length}</Badge>
  </TabsTrigger>
  {/* 新 Tab */}
  <TabsTrigger value="scenes">
    场景模式
    {scenes.length > 0 && (
      <Badge className="bg-purple-100 text-purple-600">
        {scenes.length}
      </Badge>
    )}
  </TabsTrigger>
</TabsList>
```

### 4.3 场景类型定义

| 类型 key | 显示名 | 徽标色 |
|----------|--------|--------|
| `meeting` | 会议 | blue-100 / blue-600 |
| `rest` | 休息 | slate-100 / slate-500 |
| `leave` | 离开 | orange-100 / orange-600 |
| `custom` | 自定义 | purple-100 / purple-600 |

### 4.4 场景列表布局

```
+-------------------------------------------+
|  场景模式 Tab 内容区                         |
|                                           |
|  ┌── 场景卡片 1（展开）────────────────────┐ |
|  │  [▼]  会议模式  [会议]  触发 Join#: 1   │ |
|  │  ─────────────────────────────────────  │ |
|  │  动作列表：                              │ |
|  │  ┌──────────┬──────────┬────────┬──┐  │ |
|  │  │ 投影仪    │ 开机     │ —      │🗑│  │ |
|  │  │ 遮光帘   │ 放下     │ —      │🗑│  │ |
|  │  │ 灯光     │ 亮度     │ 50%    │🗑│  │ |
|  │  └──────────┴──────────┴────────┴──┘  │ |
|  │  [+ 添加动作]                           │ |
|  └───────────────────────────────────────┘ |
|                                           |
|  ┌── 场景卡片 2（折叠）────────────────────┐ |
|  │  [▶]  休息模式  [休息]  触发 Join#: 2   │ |
|  └───────────────────────────────────────┘ |
|                                           |
|  [+ 新增场景]                              |
+-------------------------------------------+
```

### 4.5 组件树

```
ScenesTab
├── SceneList
│   └── SceneCard × N
│       ├── SceneCardHeader (折叠控制行)
│       │   ├── CollapseToggle (ChevronRight/Down)
│       │   ├── SceneNameInput (inline editable)
│       │   ├── SceneTypeBadge (meeting/rest/leave/custom)
│       │   ├── TriggerJoinInput
│       │   └── DeleteSceneButton
│       └── SceneCardBody (条件渲染，展开时)
│           ├── ActionTable
│           │   └── ActionRow × N
│           │       ├── DeviceSelect
│           │       ├── ActionSelect
│           │       ├── ValueInput
│           │       └── DeleteRowButton
│           └── AddActionButton
├── AddSceneButton
└── EmptyState (scenes.length === 0 时)
    ├── EmptyIllustration
    └── EmptyText
```

### 4.6 Tailwind 精确类决策

#### Tab 内容区容器
```tsx
<div className="
  flex flex-col gap-3
  py-4
  overflow-y-auto
  flex-1 min-h-0
">
```

#### 场景卡片 — 展开态
```tsx
<div className="
  border border-slate-200
  rounded-xl
  overflow-hidden
  bg-white
  shadow-sm
  transition-all duration-200
">
```

#### 场景卡片 Header 行
```tsx
<div className="
  flex items-center gap-3
  px-4 py-3
  cursor-pointer
  hover:bg-slate-50
  transition-colors duration-150
  select-none
">
  {/* 折叠图标 */}
  <ChevronDownIcon className="
    w-4 h-4 text-slate-400
    transition-transform duration-200
    data-[collapsed=true]:-rotate-90
  " />
  
  {/* 场景名称内联编辑 */}
  <input
    value={scene.name}
    onChange={...}
    onClick={e => e.stopPropagation()}
    className="
      flex-1
      bg-transparent
      text-sm font-600 text-slate-800
      focus:outline-none
      focus:ring-0
      border-b border-transparent
      focus:border-slate-300
      pb-0.5
      transition-colors duration-150
    "
  />
  
  {/* 类型徽标 */}
  <SceneTypeBadge type={scene.type} />
  
  {/* 触发 Join 号输入 */}
  <div className="flex items-center gap-1.5">
    <span className="text-xs text-slate-400 whitespace-nowrap">
      触发 Join#
    </span>
    <input
      type="number"
      value={scene.triggerJoin}
      onClick={e => e.stopPropagation()}
      className="
        w-14
        px-2 py-1
        text-xs font-600 text-slate-700 text-center
        bg-slate-100
        border border-slate-200
        rounded-lg
        focus:outline-none
        focus:ring-2 focus:ring-blue-500/30
        focus:border-blue-400
        focus:bg-white
        transition-all duration-150
      "
    />
  </div>
  
  {/* 删除场景 */}
  <button
    onClick={e => { e.stopPropagation(); onDeleteScene(scene.id) }}
    className="
      p-1.5
      text-slate-300 hover:text-red-400
      hover:bg-red-50
      rounded-lg
      transition-all duration-150
    "
  >
    <TrashIcon className="w-3.5 h-3.5" />
  </button>
</div>
```

#### 场景类型徽标

```tsx
const badgeConfig = {
  meeting: 'bg-blue-100 text-blue-600',
  rest:    'bg-slate-100 text-slate-500',
  leave:   'bg-orange-100 text-orange-600',
  custom:  'bg-purple-100 text-purple-600',
}
const labelConfig = {
  meeting: '会议',
  rest:    '休息',
  leave:   '离开',
  custom:  '自定义',
}

<span className={`
  px-2 py-0.5
  text-[10px] font-600
  rounded-full
  flex-shrink-0
  ${badgeConfig[scene.type]}
`}>
  {labelConfig[scene.type]}
</span>
```

#### 卡片 Body — 动作表格
```tsx
{isExpanded && (
  <div className="
    border-t border-slate-100
    px-4 py-3
    flex flex-col gap-2
    animate-in
  ">
    {/* 表头 */}
    <div className="
      grid grid-cols-[1fr_1fr_100px_32px]
      gap-2
      px-1
    ">
      <span className="text-[10px] font-600 text-slate-400 uppercase tracking-wider">
        设备
      </span>
      <span className="text-[10px] font-600 text-slate-400 uppercase tracking-wider">
        动作
      </span>
      <span className="text-[10px] font-600 text-slate-400 uppercase tracking-wider">
        值
      </span>
      <span />
    </div>
    
    {/* 动作行 */}
    {scene.actions.map((action, idx) => (
      <ActionRow
        key={action.id}
        action={action}
        devices={allDevices}
        onDelete={() => deleteAction(scene.id, action.id)}
        onChange={...}
      />
    ))}
    
    {/* 添加动作按钮 */}
    <button
      onClick={() => addAction(scene.id)}
      className="
        mt-1
        flex items-center gap-1.5
        px-3 py-2
        text-xs font-500 text-blue-500
        hover:text-blue-600
        hover:bg-blue-50
        rounded-lg
        border border-dashed border-blue-200
        hover:border-blue-300
        transition-all duration-150
        w-full justify-center
      "
    >
      <PlusIcon className="w-3.5 h-3.5" />
      添加动作
    </button>
  </div>
)}
```

#### 动作行
```tsx
<div className="
  grid grid-cols-[1fr_1fr_100px_32px]
  gap-2
  items-center
  group
">
  {/* 设备 Select */}
  <select className="
    w-full px-2 py-1.5
    bg-slate-50
    border border-slate-200
    rounded-lg
    text-xs text-slate-700
    focus:outline-none
    focus:ring-2 focus:ring-blue-500/30
    focus:border-blue-400
    transition-all duration-150
  ">
    {devices.map(d => (
      <option key={d.id} value={d.id}>{d.name}</option>
    ))}
  </select>
  
  {/* 动作 Select */}
  <select className="/* 同上 */">
    {/* 根据设备动态变化 */}
  </select>
  
  {/* 值 Input */}
  <input
    type="text"
    placeholder="—"
    className="
      w-full px-2 py-1.5
      bg-slate-50
      border border-slate-200
      rounded-lg
      text-xs text-slate-700
      text-center
      focus:outline-none
      focus:ring-2 focus:ring-blue-500/30
      focus:border-blue-400
      transition-all duration-150
    "
  />
  
  {/* 删除行 */}
  <button
    onClick={() => deleteAction(action.id)}
    className="
      w-8 h-8
      flex items-center justify-center
      text-transparent
      group-hover:text-slate-400
      hover:!text-red-400
      hover:bg-red-50
      rounded-lg
      transition-all duration-150
    "
  >
    <TrashIcon className="w-3.5 h-3.5" />
  </button>
</div>
```

#### 新增场景按钮
```tsx
<button
  onClick={addScene}
  className="
    mt-2
    flex items-center gap-2
    px-4 py-3
    text-sm font-500 text-slate-500
    hover:text-slate-700
    border-2 border-dashed border-slate-200
    hover:border-slate-300
    rounded-xl
    hover:bg-slate-50
    transition-all duration-150
    w-full justify-center
  "
>
  <PlusIcon className="w-4 h-4" />
  新增场景
</button>
```

#### 空态 — 无场景
```tsx
<div className="
  flex flex-col items-center gap-4
  py-12 px-6
  text-center
">
  {/* 插图区域 — 可用 SVG 或图片占位 */}
  <div className="
    w-20 h-20
    bg-slate-100
    rounded-2xl
    flex items-center justify-center
    mx-auto
  ">
    <LayersIcon className="w-10 h-10 text-slate-300" />
  </div>
  
  <div>
    <p className="text-sm font-600 text-slate-500">
      暂未检测到场景
    </p>
    <p className="text-xs text-slate-400 mt-1 leading-relaxed">
      AI 未从需求中解析出场景模式<br />
      可手动新增自定义场景
    </p>
  </div>
  
  <button
    onClick={addScene}
    className="
      inline-flex items-center gap-1.5
      px-4 py-2
      bg-slate-900 hover:bg-slate-700
      text-white text-sm font-500
      rounded-lg
      transition-colors duration-150
    "
  >
    <PlusIcon className="w-4 h-4" />
    手动添加场景
  </button>
</div>
```

### 4.7 Props 接口

```typescript
type SceneType = 'meeting' | 'rest' | 'leave' | 'custom'

interface SceneAction {
  id: string
  deviceId: string
  action: string
  value?: string
}

interface Scene {
  id: string
  name: string
  type: SceneType
  triggerJoin: number
  actions: SceneAction[]
  isExpanded?: boolean
}

interface ScenesTabProps {
  scenes: Scene[]
  availableDevices: { id: string; name: string; actions: string[] }[]
  onChange: (scenes: Scene[]) => void
}
```

### 4.8 交互状态流转

| 操作 | 动画 |
|------|------|
| 展开/折叠卡片 | ChevronIcon 旋转 200ms；body 区域 max-height 0→auto（300ms ease-out）|
| 删除场景 | 卡片 opacity 1→0 + height→0（250ms ease-in）|
| 新增场景 | 新卡片从底部 fadeInUp（opacity 0 + translateY 8px → 正常，300ms ease-out）|
| 新增动作行 | 同上，200ms |
| 删除动作行 | opacity 1→0 + height→0（150ms ease-in）|
| 类型切换 | 徽标背景/文字色交叉淡变（200ms）|

### 4.9 动效规范

```
卡片折叠动画（推荐用 Framer Motion AnimatePresence）：
  展开：
    initial: { height: 0, opacity: 0 }
    animate: { height: 'auto', opacity: 1 }
    transition: { duration: 0.25, ease: 'easeOut' }
  
  折叠：
    exit: { height: 0, opacity: 0 }
    transition: { duration: 0.2, ease: 'easeIn' }

Chevron 旋转：
  CSS: transition-transform duration-200
  展开: rotate-0  折叠: -rotate-90

场景卡片新增：
  initial: { opacity: 0, y: 12 }
  animate: { opacity: 1, y: 0 }
  transition: { duration: 0.3, ease: 'easeOut' }
```

---

## 全局动效参数汇总

| 场景 | duration | easing | Tailwind class |
|------|----------|--------|----------------|
| 微交互（hover/focus） | 150ms | ease | `duration-150` |
| 颜色/透明度变化 | 200ms | ease-out | `duration-200 ease-out` |
| 面板滑动/展开 | 250-300ms | ease-out | `duration-300 ease-out` |
| 面板退出/折叠 | 150-200ms | ease-in | `duration-200 ease-in` |
| 抽屉入场 | 300ms | ease-out | CSS custom |
| 进度条填充 | 500ms | ease-out | `duration-500 ease-out` |

---

## 无障碍（A11y）清单

| 组件 | 要点 |
|------|------|
| ClarificationCard | `role="status"` 包裹进度文字，`aria-live="polite"` |
| ClarificationItem | `aria-label="第1项：品牌型号，待回答"` |
| ProtocolUploadDrawer | `role="dialog"` + `aria-modal="true"` + `aria-labelledby` |
| DropZone | `role="button"` + `aria-label="上传协议文件"` + `onKeyDown Enter/Space` |
| ProtocolReviewPanel | `role="list"` 列表 + `aria-selected` 选中行 |
| SceneCard | `aria-expanded` 控制折叠状态 |
| SceneNameInput | `aria-label="场景名称"` |

Tab 键顺序：
- 抽屉打开时 focus trap 在抽屉内
- Escape 键关闭抽屉/取消拒绝输入框
- 列表行支持键盘 ↑↓ 导航 + Enter 选中

---

## 文件交付清单

| 文件 | 说明 |
|------|------|
| `components/generator/ClarificationCard.tsx` | Feature 1 追问卡片 |
| `components/generator/ClarificationItem.tsx` | 单条追问项（含动画） |
| `components/protocol/ProtocolUploadDrawer.tsx` | Feature 2 上传抽屉 |
| `components/protocol/DropZone.tsx` | 拖拽上传区（可复用） |
| `components/admin/ProtocolReviewPanel.tsx` | Feature 3 审核详情面板 |
| `components/admin/PendingListItem.tsx` | 待审核列表行 |
| `components/admin/EditableField.tsx` | AI 提取结果可编辑字段 |
| `components/confirmation/ScenesTab.tsx` | Feature 4 场景 Tab 主容器 |
| `components/confirmation/SceneCard.tsx` | 场景卡片（折叠/展开） |
| `components/confirmation/ActionRow.tsx` | 动作行（device→action→value） |
| `types/scene.ts` | Scene / SceneAction / SceneType 类型定义 |
| `types/protocol.ts` | ProtocolSubmitPayload 类型定义 |
