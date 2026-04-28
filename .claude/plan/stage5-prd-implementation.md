# Stage 5 PRD 实施计划：智能中控编程生成系统

> 最后更新：2026-04-27
> 完成度：Phase 0~3 已交付，Phase 4（UI 重设计）设计定稿待实现，Phase 5（模板库）未启动

---

## 完成状态总览

| Phase | 内容 | 状态 |
|-------|------|------|
| Phase 0 | 基础设施（Alembic + 存储 + 分页） | ✅ 完成 |
| Phase 1 | 解析流程 + 直接确认 | ✅ 完成 |
| Phase 2 | 协议上传 + 审核工作流 | ✅ 完成 |
| Phase 3 | 场景模式解析 + 状态机清理 | ✅ 完成 |
| Phase 4 | UI 整体重设计（三步骤布局） | 🔲 设计定稿，待实现 |
| Phase 5 | 模板库 | 🔲 未启动 |

---

## Phase 0：基础设施 ✅

- Alembic 4 个迁移版本（`0001_initial` → `0004_session_version`）
- `schemas/pagination.py`：`PagedResponse[T]`
- 协议文件上传通过 multipart 接收，本地存储

---

## Phase 1：解析流程 ✅

### 实际实现（与原设计的偏差）

| 项目 | 原设计 | 实际 |
|------|--------|------|
| 交互模式 | 多轮追问循环 | 一次解析 → 直接确认 |
| clarifying 状态 | 核心流程 | 已退出，仅兼容历史数据 |
| missing_info | LLM 追问用户 | 确认面板顶部显示，用户直接编辑表格 |

### 状态机（当前）

```
created → parsing → parsed → confirmed → generating → completed
                                                     ↘ error
clarifying（历史兼容，新建会话不再进入，clarifying→confirmed 已放开）
```

### 已实现

- `SessionMessage`、`ParseRevision` 模型（数据层保留）
- `conversation_service.py`：消息持久化、parse context 构建
- `orchestrator.stage_parse`：始终写入 `PARSED` 状态
- API：`GET/POST /gen/sessions/{id}/messages`、`POST /gen/sessions/{id}/parse`

---

## Phase 2：协议上传 + 审核工作流 ✅

### 已实现

**后端**
- `ProtocolSubmission` 模型（`0003_protocol_submissions` 迁移）
- `protocol_ingestion.py`：LLM 协议提取 + 状态流转
- API：用户端上传 + 管理员审核（批准/拒绝）

**前端**
- `ProtocolUploadDrawer.tsx`：粘贴/文件两 Tab，10MB 限制，审核中状态展示
- `admin/Protocols.tsx`：协议库 Tab + 待审核 Tab

### 协议提交入口调整（Phase 4 同步修改）

原设计：上传按钮在生成对话框内（依赖 sessionId）
**新设计**：上传入口统一在"协议管理"页面，独立于生成流程

- `ProtocolUploadDrawer` 的 `sessionId` 改为可选参数
- `admin/Protocols.tsx` Tab 1 顶部增加"提交协议"按钮
- 生成流程中不再有协议上传入口

---

## Phase 3：场景模式 + 状态机清理 ✅

### 已实现

- `SceneModeItem`、`SceneActionItem` schema
- parse prompt 场景识别规则
- `ConfirmationView.tsx` 场景 Tab（新增/编辑/折叠/删除）
- 状态机：`clarifying → confirmed` 放开；新建会话不再进入 clarifying

### 已知技术债务

- 场景 CHT 编译（`scene_service.compile_scene_to_cht`）**未实现**，场景数据确认后暂不影响生成输出

---

## Phase 4：UI 整体重设计 🔲 设计定稿，待实现

### 设计决策（已定稿）

| 决策点 | 方案 |
|--------|------|
| 布局 | 侧边栏 + 主区三步骤（去掉左右双栏）|
| Step 指示器 | 主区顶部固定：① 描述需求 → ② 确认清单 → ③ 生成结果 |
| 侧边栏 | 可拖动调宽（160px~320px），状态文字标签，宽度存 localStorage |
| 状态说明 | 彩色圆点 + 状态文字（如"已完成 · 4月27日"） |
| Step 1 描述 | 纯 textarea，无气泡，含示例引导 placeholder |
| Step 1+2 合并 | 描述折叠条 + 下方确认面板（解析后描述收起为单行摘要）|
| 重新解析 | 描述展开 → 编辑 → [重新解析] / [取消]；Tab 位置保持 |
| 确认生成 | 有缺失信息时轻量确认弹窗，不禁用按钮 |
| 新建对话 | 有实质编辑时弹确认提示，防止数据丢失 |
| Step 3 生成中 | SSE 状态文字显示，不做多步进度条 |
| 生成独立性 | Session 级独立，导航离开不中断；返回时若仍 generating 则轮询 |
| 协议上传 | 移出生成流程，统一在协议管理页面提交 |

### 需要实现的文件

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `src/pages/Workspace.tsx` | 全量重构 | 三步骤布局，拖动侧边栏，Step 指示器 |
| `src/components/ConfirmationView.tsx` | 小调整 | 去掉 `onReParse` prop，适配全宽 |
| `src/components/ResultView.tsx` | 小调整 | `height: 500px` 改 `flex-1` |
| `src/components/ClarificationCard.tsx` | 删除 | 已废弃 |
| `src/components/ProtocolUploadDrawer.tsx` | 小调整 | `sessionId` 改可选 |
| `src/pages/admin/Protocols.tsx` | 小改 | Tab 1 增加"提交协议"按钮 |

### 实现顺序建议

1. 重构 `Workspace.tsx`（主体工作）
2. 调整 `ConfirmationView` / `ResultView`（适配全宽）
3. 拖动侧边栏
4. 协议上传入口迁移（`ProtocolUploadDrawer` + `admin/Protocols`）
5. 删除 `ClarificationCard.tsx`

---

## Phase 5：模板库 🔲 未启动

### 目标

管理员上传 UI 风格模板，生成时可选，影响 XML 样式输出。

### 依赖

Phase 4 UI 重设计完成后再启动，避免在旧布局上做无效工作。

---

## 技术债务

| 项目 | 说明 | 优先级 |
|------|------|--------|
| 场景 CHT 编译 | `compile_scene_to_cht` 未实现，场景不影响生成输出 | 中 |
| 协议上传 sessionId 解耦 | Phase 4 时一并处理 | 中（Phase 4）|
| 生成中轮询 | 返回 generating 状态的会话时，需轮询直至完成 | 中（Phase 4）|
| PDF/DOCX 解析 | 协议上传仅支持纯文本 | 低 |
| 审核队列过滤 | 无状态过滤器（全部/待审核/已通过） | 低 |
| 测试覆盖 | orchestrator / generation 流程无测试 | 中 |
