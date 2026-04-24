# MDK Web Platform — 迭代 2 计划

> 基准日期：2026-04-24
> 前置文档：`web-platform-design.md`（架构设计）、`ui-design.md`（UI 规范）

---

## 1. 当前实现状态

### 1.1 后端（Phase W1 + W2 ✅ 完成）

| 模块 | 文件 | 状态 |
|------|------|------|
| FastAPI 入口 | `app/main.py` | ✅ 含 seed/sync/lifespan |
| 日志系统 | `app/log.py` | ✅ 独立模块，彩色输出，6 类操作标签 |
| 配置 | `app/config.py` | ✅ pydantic-settings |
| 数据库 | `app/database.py` | ✅ SQLite async |
| 数据模型 | `app/models/` | ✅ User/GenSession/LlmConfig/Protocol/Setting |
| 认证 | `app/routers/auth.py` | ✅ JWT login/me/password |
| 生成流程 | `app/routers/gen.py` | ✅ sessions CRUD + parse/confirm/generate(SSE)/result/download |
| 管理后台 | `app/routers/admin.py` | ✅ users/llm-config CRUD + test |
| 协议管理 | `app/routers/protocols.py` | ✅ CRUD |
| 参考查询 | `app/routers/ref.py` | ✅ cht/xml 查询接口 |
| LLM 封装 | `app/services/llm.py` | ✅ litellm + 加密 key + [LLM] 日志 |
| 工作流编排 | `app/services/orchestrator.py` | ✅ 5 阶段 + [FLOW]/[DB] 日志 |
| 知识库 | `app/services/knowledge.py` | ✅ 按需加载：协议/语法/模式/控件/代码块/系统函数 |
| Prompt 构建 | `app/services/prompt_builder.py` | ✅ parse/xml/cht + 知识注入 + [PROMPT] 日志 |
| Join 分配 | `app/services/join_registry.py` | ✅ 号段规则 + 冲突检测 |
| 校验器 | `app/services/validator.py` | ✅ CHT 语法 + 交叉校验 + [SCRIPT] 日志 |
| Prompt 模板 | `app/prompts/*.md` | ✅ parse/xml/cht 三套 |

### 1.2 前端（Phase W3 ✅ 基本完成，W4 🔶 部分完成）

| 页面 | 文件 | 状态 |
|------|------|------|
| 登录 | `Login.tsx` | ✅ |
| 修改密码 | `ChangePassword.tsx` | ✅ |
| 生成主页 | `Generator.tsx` | ✅ 步骤条 + 描述回看 + textarea 可拉伸 |
| 确认清单 | `ConfirmationView.tsx` | ✅ 基础版（Tab 切换 + 内联编辑 + 增删行） |
| 结果预览 | `ResultView.tsx` | ✅ 基础版（分栏/标签页 + 行号 + 下载） |
| 历史列表 | `History.tsx` | ✅ |
| 会话详情 | `SessionDetail.tsx` | ✅ 5 步导航 + 代码预览 + 校验报告 |
| LLM 配置 | `admin/LlmConfig.tsx` | ✅ CRUD + 连接测试 |
| 用户管理 | `admin/Users.tsx` | ✅ 列表 + 角色/状态切换 |
| 协议管理 | `admin/Protocols.tsx` | ✅ 列表（CRUD 待完善） |
| 布局 | `Layout.tsx` | ✅ 导航 + 角色权限 |
| 路由 | `App.tsx` | ✅ 全部路由 |
| 状态管理 | `stores/auth.ts` | ✅ Zustand（仅 auth） |
| API 客户端 | `api/client.ts` | ✅ axios + interceptor |

### 1.3 知识库（✅ 重构完成）

| 目录 | 说明 |
|------|------|
| `core/docs/系统函数库/常用/` | 高频函数文档（继电器/串口/红外/DSP 等） |
| `core/docs/系统函数库/专用硬件/` | 低频硬件函数文档 |
| `core/docs/代码组织/` | DEFINE_DEVICE/EVENT/START 等代码块规范 |
| `core/references/controls/widgets/` | 按控件类型拆分的规范文件 |
| `core/references/core/patterns/` | 按场景拆分的代码模式 |
| `core/templates/xml/` | XML 控件模板（button/slider/picture 等） |
| `core/templates/cht/` | CHT 骨架模板 + 设备/事件参考 |

### 1.4 未实现（设计文档中有但未做）

| 功能 | 原设计位置 | 优先级 |
|------|-----------|--------|
| Docker Compose 部署 | `web-platform-design.md` §10 | P1 |
| 系统设置页面 `/admin/settings` | `web-platform-design.md` §3.5 | P2 |
| 协议管理详细 CRUD（添加/编辑弹窗） | `web-platform-design.md` §3.3 | P2 |
| 代码高亮（Shiki/Prism） | `ui-design.md` §4.4.3 | P2 |
| 搜索 Ctrl+F（SearchOverlay） | `ui-design.md` §4.4.5 | P3 |
| 全屏预览（FullscreenOverlay） | `ui-design.md` §4.4.10 | P3 |
| Diff 版本对比 | `ui-design.md` §4.4.7 | P3 |
| 可拖拽分栏（ResizableDivider） | `ui-design.md` §4.4.4 | P3 |
| 校验项点击跳转到代码行 | `ui-design.md` §4.4.8 | P3 |
| Toast 通知组件 | `ui-design.md` §5.1 | P3 |
| 确认生成弹窗（ConfirmDialog） | `ui-design.md` §3.4.11 | P3 |

---

## 2. 已知问题

| # | 问题 | 严重度 | 来源 |
|---|------|--------|------|
| B1 | 生成阶段 SSE 解析不够健壮，error 事件的 data 未正确显示 | Medium | 用户测试 |
| B2 | ConfirmationView 功能表 btn_type/control_type 显示混合 | Low | 代码审查 |
| B3 | Generator SSE 读取中无超时/重连机制 | Medium | 代码审查 |
| B4 | 协议管理 Protocols 页面只有列表，缺少添加/编辑/删除操作 | Medium | 功能缺口 |
| B5 | 前端无全局错误边界（ErrorBoundary） | Low | 代码审查 |

---

## 3. 迭代 2 计划

### Phase A：核心流程打通与 Bug 修复（优先级最高）

> 目标：确保从"描述需求 → 生成 → 下载"的完整链路可靠运行

| # | 任务 | 涉及文件 | 估计 |
|---|------|----------|------|
| A1 | 实际跑通一次完整生成，修复发现的问题 | orchestrator/llm/validator | — |
| A2 | SSE 事件解析健壮化（error data 展示、超时处理） | Generator.tsx | 小 |
| A3 | ConfirmationView 功能表字段显示修正 | ConfirmationView.tsx | 小 |
| A4 | 生成阶段增加耗时显示（每个 Phase 的用时） | orchestrator.py + Generator.tsx | 小 |

### Phase B：管理后台补全

| # | 任务 | 涉及文件 | 估计 |
|---|------|----------|------|
| B1 | 协议管理：添加/编辑弹窗 + 删除确认 | admin/Protocols.tsx | 中 |
| B2 | 系统设置页面（分辨率、XML 版本） | 新建 admin/Settings.tsx + router | 中 |

### Phase C：UI 体验提升

| # | 任务 | 涉及文件 | 估计 |
|---|------|----------|------|
| C1 | ResultView 代码高亮（XML 用 Shiki/Prism） | ResultView.tsx | 中 |
| C2 | 复制到剪贴板反馈（CheckIcon + 短暂提示） | ResultView/SessionDetail | 小 |
| C3 | 全局错误边界 + 友好 fallback UI | 新建 ErrorBoundary.tsx | 小 |
| C4 | Generator 生成进度增强（阶段进度条而非纯文字） | Generator.tsx | 中 |

### Phase D：部署

| # | 任务 | 涉及文件 | 估计 |
|---|------|----------|------|
| D1 | 后端 Dockerfile | web/backend/Dockerfile | 小 |
| D2 | 前端 Dockerfile（Vite build + nginx） | web/frontend/Dockerfile | 小 |
| D3 | docker-compose.yml（前端 + 后端 + 数据卷） | 根目录 | 小 |
| D4 | 环境变量文档 + .env.example | 新建 | 小 |

### Phase E：锦上添花（低优先级）

| # | 任务 |
|---|------|
| E1 | 搜索 Ctrl+F 代码内搜索 |
| E2 | 全屏代码预览 |
| E3 | Diff 版本对比 |
| E4 | 校验项点击定位到代码行 |
| E5 | 可拖拽分栏比例 |
| E6 | 确认生成摘要弹窗 |

---

## 4. 建议执行顺序

```
A1 → A2 → A3 → A4（先保证核心流程可靠）
      ↓
B1 → B2（管理后台补全）
      ↓
D1 → D2 → D3 → D4（可部署）
      ↓
C1 → C2 → C3 → C4（体验优化）
      ↓
E*（按需选做）
```

Phase A 是阻塞项，必须先完成。B/D 可并行。C/E 按时间充裕度选做。
