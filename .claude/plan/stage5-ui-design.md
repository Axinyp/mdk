# Stage 5 UI 设计规范

> 最后更新：2026-04-27
> 状态：Phase 0~3 已交付（部分需统一），Phase 4 设计定稿待实现，Phase 5 设计先行

---

## 第一部分：设计系统基础

### 颜色令牌

**主色板（统一使用 slate 系，禁用 neutral）**

| 用途 | Token | 备注 |
|------|-------|------|
| 主背景 | `slate-50` (`#F8FAFC`) | 页面/section 背景 |
| 卡片背景 | `white` | 所有卡片、面板 |
| 边框 | `slate-200` | 默认边框 |
| 边框（hover） | `slate-300` | 卡片悬停 |
| 分割线 | `slate-100` | 列表项分隔 |
| 一级文字 | `slate-900` | 标题、强调 |
| 二级文字 | `slate-700` | 正文 |
| 三级文字 | `slate-500` | 描述、辅助 |
| 四级文字 | `slate-400` | 占位、禁用 |
| 微弱文字 | `slate-300` | 极辅助 |

**功能色**

| 用途 | Token | 用法 |
|------|-------|------|
| 主 CTA | `blue-600` / `blue-700`(hover) | 登录、保存、确认生成 |
| 次 CTA | `slate-700` / `slate-900`(hover) | 发送、提交（区别于 blue 主 CTA）|
| 成功 | `emerald-500` / `emerald-50`(bg) | 已完成、批准 |
| 警告 | `amber-500` / `amber-50`(bg) | 待审核、缺失信息 |
| 危险 | `red-500` / `red-50`(bg) | 删除、错误、拒绝 |
| 处理中 | `blue-500` / `purple-500` | 解析中 / 生成中 |

### 字体与排版

```
Plus Jakarta Sans 300/400/500/600/700
等宽：默认 ui-monospace（代码/JoinNumber）
```

| 用途 | Class | 像素 |
|------|-------|------|
| 页面标题 H1 | `text-xl font-semibold` | 20px |
| 卡片标题 H2 | `text-base font-semibold` | 16px |
| 段落标题 H3 | `text-sm font-semibold` | 14px |
| 正文 | `text-sm` | 14px |
| 辅助文字 | `text-xs` | 12px |
| 微小文字 | `text-[10px]` | 10px |

### 圆角与间距

| 用途 | Token |
|------|-------|
| 输入框 / 按钮 | `rounded-lg`（统一，禁用 `rounded-md`）|
| 面板 / 卡片 | `rounded-xl` |
| 徽章 / 标签 | `rounded-full` |
| 容器内边距 | `p-4`（小）/ `p-6`（中）/ `p-8`（大）|
| 表单字段间距 | `space-y-3` 或 `space-y-4` |

### 阴影

| 用途 | Class |
|------|-------|
| 卡片 | `shadow-sm` |
| 浮层 / 抽屉 | `shadow-xl` 或 `shadow-2xl` |
| 弹窗（Modal） | `shadow-xl` |

---

## 第二部分：共通模式

### 1. 页面头部（Page Header）

```
┌─────────────────────────────────────────────────────┐
│  页面标题                            [主操作按钮]    │
│  text-xl font-semibold              CTA            │
└─────────────────────────────────────────────────────┘
```

**Class**：`flex items-center justify-between mb-6`
**容器**：`max-w-6xl mx-auto px-4 py-6`（管理后台标准）

### 2. 卡片（Card）

```
┌─────────────────────────────────────────────────────┐
│  bg-white rounded-xl border border-slate-200       │
│  shadow-sm                                          │
│                                                     │
│  内容 padding 由内部决定                             │
└─────────────────────────────────────────────────────┘
```

### 3. 表单字段（Form Field）

```
标签                           text-sm font-medium text-slate-700 mb-1.5
输入框                         w-full px-3 py-2 text-sm
                              border border-slate-200 rounded-lg
                              focus:outline-none
                              focus:ring-2 focus:ring-blue-500
                              focus:border-transparent
                              placeholder-slate-400
```

**密码字段**：`type="password"`（可选眼睛图标显示明文，新功能）

**字段间距**：`space-y-3`（紧凑）或 `space-y-4`（宽松）

### 4. 按钮（Button）

| 类型 | Class |
|------|-------|
| 主 CTA | `px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg disabled:opacity-50` |
| 次按钮 | `px-4 py-2 border border-slate-300 text-slate-700 text-sm rounded-lg hover:bg-slate-50` |
| 危险按钮 | `px-4 py-2 bg-red-500 hover:bg-red-600 text-white text-sm font-medium rounded-lg` |
| 文字按钮 | `text-xs text-blue-600 hover:text-blue-800`（表格内联操作）|
| 图标按钮 | `w-8 h-8 flex items-center justify-center rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100` |

**加载态**：`disabled + opacity-50` + 内嵌 `<span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />`

### 5. 状态徽章（Status Badge）

```
基础：text-xs font-medium px-2.5 py-0.5 rounded-full
```

| 业务含义 | 样式 |
|----------|------|
| 待处理 / 待描述 | `bg-slate-100 text-slate-500` |
| 信息 / 解析中 / 已解析 | `bg-blue-50 text-blue-600` |
| 处理中 / 生成中 | `bg-purple-100 text-purple-700 animate-pulse` |
| 警告 / 待审核 | `bg-amber-50 text-amber-700` |
| 成功 / 已完成 / 已批准 | `bg-emerald-50 text-emerald-700` |
| 错误 / 已拒绝 | `bg-red-50 text-red-600` |

### 6. 表格（Table）

```
表头：bg-slate-50 + text-xs font-medium text-slate-500
行：hover:bg-slate-50
分割：divide-y divide-slate-100
单元格 padding：px-3 py-2 (紧凑) / px-4 py-3 (宽松)
内联编辑输入框：与表单输入框相同，但 border 弱化
```

### 7. Modal（弹窗）

```
背景层    fixed inset-0 bg-black/30 flex items-center justify-center z-50
容器      bg-white rounded-xl shadow-xl w-full max-w-{sm|md|lg}
         max-h-[90vh] overflow-y-auto
内边距    p-6
头部      h2: text-lg font-semibold mb-4
底部      mt-6 flex justify-end gap-2
```

**适用**：表单提交、二次确认、详情查看（窄）

### 8. Drawer（抽屉）

```
背景层    fixed inset-0 bg-slate-900/40 backdrop-blur-[2px] z-40
容器      fixed right-0 top-0 bottom-0 w-[480px]
         bg-white shadow-2xl border-l border-slate-200 z-50
         flex flex-col
头部      px-6 py-4 border-b border-slate-200 + 关闭按钮
内容      flex-1 overflow-y-auto px-6 py-5
底部      px-6 py-4 border-t border-slate-200
```

**适用**：详情查看（宽）、上传向导、复杂表单

### 9. 空状态（Empty State）

```
容器：flex flex-col items-center justify-center py-12 text-center
图标：w-12 h-12 rounded-2xl bg-slate-100 + text-slate-400
主文：text-sm text-slate-500 mb-1
副文：text-xs text-slate-400 mb-4
CTA：可选
```

### 10. 确认弹窗（Lightweight Confirm）

```
窄 Modal（max-w-sm）：
- 标题：text-base font-semibold（"确认操作？"）
- 描述：text-sm text-slate-500（解释影响）
- 按钮：[取消] [继续] 或 [取消] [删除（红）]
```

---

## 第三部分：页面设计

### 3.1 认证类页面

#### Login.tsx

```
┌─────────────────────────────────────────┐
│           min-h-screen bg-slate-50      │
│                                         │
│       ┌─────────────────────────┐       │
│       │  bg-white rounded-xl    │       │
│       │  shadow-lg p-8          │       │
│       │  max-w-sm                │       │
│       │                          │       │
│       │       MDK Control       │       │
│       │   text-2xl font-semibold│       │
│       │  中控系统代码生成平台     │       │
│       │                          │       │
│       │  用户名 [_____________]  │       │
│       │  密码  [_____________]  │       │
│       │                          │       │
│       │  [    登录    ]         │       │
│       │  bg-blue-600            │       │
│       └─────────────────────────┘       │
└─────────────────────────────────────────┘
```

**当前问题**：使用 `neutral-` 系颜色 + `rounded-md`，需统一为 `slate-` + `rounded-lg`。

**待实现**：
- [ ] 颜色令牌统一
- [ ] 圆角统一
- [ ] 错误提示统一为 `text-red-700 bg-red-50 border border-red-200`

#### ChangePassword.tsx

布局结构与 Login 一致，仅字段不同：当前密码 / 新密码 / 确认新密码。

**附加规则**：
- 客户端校验：长度 ≥ 6（应升级为符合 PRD 的强密码策略）
- 校验失败用就近错误提示，不用 alert
- 成功后自动跳转 `/`

---

### 3.2 全局布局（Layout.tsx）

```
┌─────────────────────────────────────────────────────────────┐
│ Header  height-14  bg-white border-b border-slate-200      │
│                                                             │
│ MDK Control  | 协议管理  模型配置  用户       张三 [管理员] 退出│
│ font-semibold | text-sm text-slate-600                      │
└─────────────────────────────────────────────────────────────┘
│                                                             │
│  Main flex-1 min-h-0 (子页面填满剩余高度)                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**导航**：管理员可见 3 个链接，普通成员仅看到品牌 + 自己的菜单。

**用户区域**：
- 用户名：`text-sm text-slate-500`
- 角色徽章：`text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-600`（管理员）/ `bg-slate-100 text-slate-600`（成员）
- 退出：`text-sm text-slate-500 hover:text-red-500`

---

### 3.3 主工作区（Workspace.tsx）—— Phase 4 重设计

详见原 Phase 4 章节，此处仅列三步骤映射：

| Step | 内容 | 主要组件 |
|------|------|---------|
| 1. 描述需求 | textarea + CTA | `<DescribeStep>` |
| 2. 确认清单 | 折叠描述条 + ConfirmationView | `<ConfirmStep>` |
| 3. 生成结果 | 折叠描述条 + ResultView 或生成中 | `<ResultStep>` |

**侧边栏**（共用三步骤）：
- 默认 224px，可拖动 160~320px
- 状态圆点 + 标题截断 + 状态文字（"已完成 · 4月27日"）
- 首次空：底部"暂无记录"

详细设计见前一份提案，此处不重复。

---

### 3.4 管理后台

#### 3.4.1 LlmConfig.tsx（LLM 模型配置）

```
┌─ Page Header ────────────────────────────────────┐
│ LLM 模型配置                       [+ 添加模型]   │
└──────────────────────────────────────────────────┘

┌─ 配置卡片列表 (space-y-3) ────────────────────────┐
│ ┌──────────────────────────────────────────────┐ │
│ │ DeepSeek V3   [默认]                  编辑 删除 │ │
│ │ openai/deepseek-chat (api.deepseek.com)       │ │
│ │ • Key 已配置                                   │ │
│ └──────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────┐ │
│ │ Claude 4.6  [已禁用]                  编辑 删除 │ │
│ └──────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘

弹窗（Modal max-w-lg）：
  显示名称 / 提供商 / 模型 ID / API 地址 / API Key
  [☐] 设为默认模型
  [测试连接] -------- [取消] [保存]
```

**测试结果展示**：
- 短消息（≤60 字符）直接显示
- 长消息显示前 60 字符 + "查看详情"折叠按钮 + 等宽字体可滚动区

**待实现**：
- 当前 form border 用 `rounded-md`，需统一 `rounded-lg`
- 卡片容器当前 `rounded-lg`（应为 `rounded-xl`）

#### 3.4.2 Users.tsx（用户管理）

```
┌─ Page Header ────────────────────────────────────┐
│ 用户管理                            [+ 添加用户] │
└──────────────────────────────────────────────────┘

┌─ Table（bg-white rounded-xl border） ─────────────┐
│ ID │ 用户名 │ 角色 │ 状态 │ 创建时间 │ 操作          │
├────┼───────┼─────┼─────┼─────────┼──────────────┤
│ 1  │ admin │管理员│正常 │ 04-27   │ 降为成员 禁用 │
│ 2  │ alice │成员 │正常 │ 04-27   │ 升为管理员 禁用 │
└──────────────────────────────────────────────────┘

弹窗（Modal max-w-sm）：
  用户名 / 密码 / 角色（成员/管理员）
  [取消] [创建]
```

**操作设计**：
- 角色切换：直接点击文字按钮
- 状态切换：直接点击文字按钮
- 删除用户：暂未提供（避免误操作，未来用"禁用"代替"删除"）

#### 3.4.3 Protocols.tsx（协议管理）

```
┌─ Page Header ────────────────────────────────────┐
│ 协议管理                          [+ 提交协议]    │
│                                  ↑ Phase 4 新增  │
└──────────────────────────────────────────────────┘

┌─ Tab 栏 (border-b border-slate-200) ─────────────┐
│ [协议库] [待审核 (3)]                            │
│  ↑当前      ↑橙色徽章                           │
└──────────────────────────────────────────────────┘
```

**Tab 1：协议库**

```
┌──────────────┬─────────────────────────────────┐
│ 搜索框        │   选中后的协议详情               │
│ (300ms 防抖) │                                 │
│              │   品牌 + 类别 + 通信 + 文件名    │
│ 协议列表      │                                 │
│ - 爱普生 EB  │   ┌─────────────────────────┐   │
│ - 索尼 VW    │   │ Markdown 内容             │   │
│ - 顶点矩阵   │   │ font-mono text-xs        │   │
│ ...         │   │ max-h-[600px] 滚动        │   │
│              │   └─────────────────────────┘   │
│              │   [删除]（右上角）              │
└──────────────┴─────────────────────────────────┘
```

**Tab 2：待审核**

```
┌──────────────────┬───────────────────────────────┐
│ 列表 (40%)       │   详情 + 编辑 (60%)             │
│                  │                                │
│ 提交人 · 时间    │   ┌──────────┬────────────┐   │
│ 设备名           │   │ 原始内容  │ AI 提取结果 │   │
│ ━ 选中蓝色高亮   │   │ pre 等宽  │ textarea   │   │
│                  │   └──────────┴────────────┘   │
│                  │                                │
│                  │   [拒绝]  [编辑后批准] [直接批准] │
└──────────────────┴───────────────────────────────┘
```

**协议提交按钮（Phase 4 新增）**：
- Tab 1 头部右侧增加 `[+ 提交协议]` 按钮
- 点击打开 `ProtocolUploadDrawer`（`sessionId` 改可选，无 sessionId 时为独立提交）

#### 3.4.4 Templates.tsx（Phase 5 设计先行）

```
┌─ Page Header ────────────────────────────────────┐
│ 风格模板                            [+ 上传模板]  │
└──────────────────────────────────────────────────┘

┌─ 过滤栏 ──────────────────────────────────────────┐
│ [全部▾] [会议] [教室] [离场]   分辨率 [全部▾]     │
└──────────────────────────────────────────────────┘

┌─ 模板卡片网格（grid-cols-3 gap-4） ───────────────┐
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐│
│ │ [16:9 预览图] │ │ [16:9 预览图] │ │ [16:9 预览图] ││
│ │              │ │              │ │              ││
│ │ 现代简约     │ │ 深色商务     │ │ 暖色教育     ││
│ │ 2560x1600   │ │ 2560x1600   │ │ 1920x1080   ││
│ │ #会议 #简约  │ │ #会议 #商务  │ │ #教室        ││
│ │              │ │              │ │              ││
│ │ [✏ 编辑] [🗑] │ │ [✏ 编辑] [🗑] │ │ [✏ 编辑] [🗑] ││
│ └──────────────┘ └──────────────┘ └──────────────┘│
└──────────────────────────────────────────────────┘
```

**上传 Drawer**：
- 模板名称 / 场景类型（select）/ 分辨率
- 标签（多选 chip）
- Manifest JSON 编辑器
- 预览图上传（拖拽，PNG/JPG，建议 1280×720）

**生成流程集成**（Phase 5 工作）：
- Step 2 确认清单后插入 Step 2.5："选择风格"
- AI 推荐 Top 3（按场景类型 + 分辨率评分）
- 可跳过使用默认风格

---

## 第四部分：组件状态规范

### Loading 状态

| 场景 | 表现 |
|------|------|
| 按钮加载 | `disabled` + 内嵌 spinner + 文字"处理中..." |
| 表单加载 | 字段 `disabled`，提交按钮 spinner |
| 页面加载 | 中央 spinner 或骨架屏（推荐骨架屏） |
| 列表加载 | 骨架屏 3-5 行 |

### 错误状态

| 场景 | 表现 |
|------|------|
| 字段错误 | 字段下方红色文字 `text-xs text-red-600 mt-1` |
| 表单错误 | 顶部红色条 `bg-red-50 border-red-200 text-red-700 rounded-lg px-3 py-2` |
| 操作失败 | Toast 通知 或 就近错误条 |
| API 错误 | `err.response?.data?.detail` 优先，否则通用文案 |

**禁止使用**：`alert()`、`confirm()`、`prompt()`（系统弹窗，与设计风格不一致）

### Toast 通知（待实现，统一组件）

```
位置：右下角 fixed bottom-4 right-4 z-50
样式：bg-slate-800 text-white rounded-lg shadow-xl px-4 py-3
最大宽度：max-w-sm
自动消失：3 秒
变体：success（emerald 边）/ error（red 边）/ info（默认）
```

---

## 第五部分：交付状态

| 组件/页面 | Phase | 状态 | Phase 4 调整 |
|-----------|-------|------|-------------|
| Login.tsx | - | ✅ 完成 | 🔧 颜色 + 圆角统一 |
| ChangePassword.tsx | - | ✅ 完成 | 🔧 颜色 + 圆角统一 |
| Layout.tsx | - | ✅ 完成 | 无需变更 |
| Workspace.tsx | Phase 4 | 🔲 待全量重构 | 三步骤布局 |
| ConfirmationView.tsx | Phase 1+3 | ✅ 完成 | 🔧 适配全宽，去掉 onReParse |
| ResultView.tsx | Phase 1 | ✅ 完成 | 🔧 高度自适应 |
| ProtocolUploadDrawer.tsx | Phase 2 | ✅ 完成 | 🔧 sessionId 改可选 |
| ClarificationCard.tsx | Phase 1 | ⛔ 废弃 | 删除 |
| admin/LlmConfig.tsx | - | ✅ 完成 | 🔧 圆角统一（rounded-md→lg/xl） |
| admin/Users.tsx | - | ✅ 完成 | 无需变更 |
| admin/Protocols.tsx | Phase 2 | ✅ 完成 | 🔧 增加"提交协议"按钮 |
| admin/Templates.tsx | Phase 5 | 🔲 设计先行 | - |
| 共通 Toast 组件 | Phase 4 | 🔲 新建 | - |

**图例**：✅ 已交付 | 🔲 待实现 | 🔧 需小改 | ⛔ 废弃

---

## 第六部分：Phase 4 实现 Checklist

### 必须完成（核心交付）

- [ ] `Workspace.tsx` 三步骤布局重构
- [ ] 侧边栏拖动调宽 + 状态文字标签
- [ ] Step 指示器组件
- [ ] 描述折叠条组件
- [ ] `ConfirmationView` 全宽适配（去掉 `onReParse`）
- [ ] `ResultView` 全宽适配（`flex-1`）
- [ ] 删除 `ClarificationCard.tsx`
- [ ] 协议上传入口迁移（`ProtocolUploadDrawer` sessionId 改可选 + admin/Protocols 加按钮）

### 应该完成（一致性）

- [ ] Login / ChangePassword 颜色 + 圆角统一
- [ ] LlmConfig 卡片 / 表单圆角统一
- [ ] Toast 通知组件（替代 `alert()` 调用）
- [ ] 生成中会话返回时的轮询逻辑

### 可以延后（不阻塞 Phase 4）

- [ ] 强密码策略升级（ChangePassword）
- [ ] 审核队列状态过滤
- [ ] PDF/DOCX 解析支持
- [ ] 移动端适配
