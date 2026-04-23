# MDK Web Platform — 架构设计文档

> 版本：v1.0 草稿
> 日期：2026-04-23
> 状态：待确认

---

## 1. 产品概述

### 1.1 目标

为公司运维人员提供一个 **Web 对话式界面**，通过自然语言描述中控需求，自动生成 Project.xml + .cht 文件。

### 1.2 用户角色

| 角色 | 权限 |
|------|------|
| **普通成员** | 对话生成（描述需求→确认→生成→预览→下载）、查看历史记录 |
| **管理员** | 全部普通权限 + LLM 配置 + 协议管理 + 用户管理 + 系统设置 |

### 1.3 技术选型

| 层 | 技术 | 理由 |
|---|------|------|
| 后端 | **FastAPI (Python 3.12)** | 异步流式响应、与现有 scripts 同语言 |
| LLM 适配 | **litellm** | 统一 100+ 模型 API（OpenAI/Anthropic/DeepSeek/通义千问/Ollama） |
| 前端 | **React 19 + TypeScript + Tailwind CSS** | 主流生态、组件丰富 |
| 数据库 | **SQLite**（初期）→ PostgreSQL（扩展） | 零依赖启动，后续可迁移 |
| 认证 | **JWT + bcrypt** | 轻量、无外部依赖 |
| 部署 | **Docker Compose** | 前端 + 后端 + 数据库一键启动 |

---

## 2. 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│  ┌──────────┐  ┌───────────┐  ┌───────────┐            │
│  │ 对话生成  │  │ 协议管理   │  │ 系统设置   │            │
│  │ (SSE流式) │  │ (管理员)   │  │ (管理员)   │            │
│  └────┬─────┘  └─────┬─────┘  └─────┬─────┘            │
└───────┼──────────────┼──────────────┼───────────────────┘
        │ HTTP/SSE     │ REST         │ REST
┌───────┼──────────────┼──────────────┼───────────────────┐
│       ▼              ▼              ▼                    │
│                 FastAPI Backend                           │
│                                                          │
│  ┌──────────────────────────────────────────────┐       │
│  │            API Router Layer                    │       │
│  │  /api/auth/*  /api/gen/*  /api/proto/*        │       │
│  │  /api/admin/*  /api/ref/*                     │       │
│  └──────────────────┬───────────────────────────┘       │
│                     │                                    │
│  ┌──────────────────▼───────────────────────────┐       │
│  │         Orchestrator (工作流编排)              │       │
│  │                                               │       │
│  │  [解析] → [确认] → [JoinNumber] → [生成] → [校验]│     │
│  │   LLM      展示     纯算法      LLM×2    Python │     │
│  └──────┬────────────────────────┬──────────────┘       │
│         │                        │                       │
│  ┌──────▼──────┐  ┌─────────────▼────────────┐         │
│  │ LLM Router  │  │    MDK Core (知识库)      │         │
│  │  (litellm)  │  │  protocols/ references/   │         │
│  │             │  │  docs/ scripts/           │         │
│  │ OpenAI      │  └──────────────────────────┘         │
│  │ Anthropic   │                                        │
│  │ DeepSeek    │  ┌──────────────────────────┐         │
│  │ 通义千问    │  │      SQLite / PG          │         │
│  │ Ollama      │  │  users / sessions /       │         │
│  │ vLLM        │  │  history / settings       │         │
│  └─────────────┘  └──────────────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 后端 API 设计

### 3.1 认证

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/auth/login` | 登录，返回 JWT |
| POST | `/api/auth/register` | 注册（管理员创建账号时调用） |
| GET | `/api/auth/me` | 获取当前用户信息 |
| PUT | `/api/auth/password` | 修改密码 |

### 3.2 对话生成（核心）

| Method | Path | 说明 |
|--------|------|------|
| POST | `/api/gen/sessions` | 创建生成会话 |
| GET | `/api/gen/sessions` | 历史会话列表 |
| GET | `/api/gen/sessions/{id}` | 获取会话详情（含所有阶段数据） |
| POST | `/api/gen/sessions/{id}/parse` | 阶段1：发送需求描述，SSE 流式返回解析结果 |
| POST | `/api/gen/sessions/{id}/confirm` | 阶段2：用户确认/修改清单 |
| POST | `/api/gen/sessions/{id}/generate` | 阶段3-4：生成 XML + .cht，SSE 流式返回 |
| GET | `/api/gen/sessions/{id}/result` | 获取生成结果（XML + .cht + 校验报告） |
| GET | `/api/gen/sessions/{id}/download` | 下载文件（zip 包） |

### 3.3 协议管理

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/protocols` | 列表（支持 ?category=&keyword= 过滤） |
| GET | `/api/protocols/{id}` | 详情 |
| POST | `/api/protocols` | 添加 |
| PUT | `/api/protocols/{id}` | 修改 |
| DELETE | `/api/protocols/{id}` | 删除 |
| POST | `/api/protocols/import` | 从 .cht 文件导入 |

### 3.4 参考查询

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/ref/cht/devices?type=` | 设备类型查询 |
| GET | `/api/ref/cht/functions?query=` | 系统函数查询 |
| GET | `/api/ref/cht/patterns?keyword=` | 代码模式查询 |
| GET | `/api/ref/xml/controls?type=` | 控件类型查询 |
| GET | `/api/ref/xml/structure?topic=` | XML 结构查询 |

### 3.5 管理员

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/admin/users` | 用户列表 |
| POST | `/api/admin/users` | 创建用户 |
| PUT | `/api/admin/users/{id}` | 修改用户（角色/状态） |
| DELETE | `/api/admin/users/{id}` | 禁用用户 |
| GET | `/api/admin/llm/config` | 获取 LLM 配置 |
| PUT | `/api/admin/llm/config` | 修改 LLM 配置 |
| POST | `/api/admin/llm/test` | 测试 LLM 连接 |
| GET | `/api/admin/settings` | 系统参数（分辨率、号段等） |
| PUT | `/api/admin/settings` | 修改系统参数 |

---

## 4. 数据库设计

### 4.1 表结构

```sql
-- 用户表
CREATE TABLE users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    username    TEXT UNIQUE NOT NULL,
    password    TEXT NOT NULL,          -- bcrypt hash
    role        TEXT NOT NULL DEFAULT 'member',  -- 'admin' | 'member'
    status      TEXT NOT NULL DEFAULT 'active',  -- 'active' | 'disabled'
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- LLM 配置表（管理员可在网页配置）
CREATE TABLE llm_config (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,          -- 显示名：如 "DeepSeek V3"
    provider    TEXT NOT NULL,          -- litellm provider: "openai" / "anthropic" / "ollama" ...
    model       TEXT NOT NULL,          -- 模型ID: "deepseek-chat" / "gpt-4o" / "claude-sonnet-4-20250514"
    api_base    TEXT,                   -- API 地址（Ollama: http://localhost:11434）
    api_key     TEXT,                   -- 加密存储
    is_default  BOOLEAN DEFAULT FALSE,  -- 是否默认模型
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 生成会话表
CREATE TABLE gen_sessions (
    id          TEXT PRIMARY KEY,       -- UUID
    user_id     INTEGER REFERENCES users(id),
    title       TEXT,                   -- 自动从需求描述提取
    status      TEXT NOT NULL DEFAULT 'created',
    -- status: created → parsing → parsed → confirmed → generating → completed → error
    description TEXT,                   -- 原始需求描述
    parsed_data TEXT,                   -- 阶段1输出（JSON：设备/功能/缺失信息）
    confirmed_data TEXT,               -- 阶段2用户确认后的数据（JSON）
    join_registry TEXT,                -- 阶段3 JoinNumber 分配结果（JSON）
    xml_content TEXT,                  -- 生成的 Project.xml
    cht_content TEXT,                  -- 生成的 .cht
    validation_report TEXT,            -- 校验报告（JSON）
    llm_model   TEXT,                  -- 使用的模型
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 协议表（同步自文件系统，也可纯数据库管理）
CREATE TABLE protocols (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    category    TEXT NOT NULL,          -- projector / curtain / ac / ...
    brand_model TEXT NOT NULL,
    comm_type   TEXT NOT NULL,          -- RS232 / RS485 / TCP / UDP / IR
    filename    TEXT UNIQUE,            -- 对应 core/protocols/ 下的文件名
    content     TEXT NOT NULL,          -- 完整 markdown 内容
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 系统设置表（KV 存储）
CREATE TABLE settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    description TEXT
);

-- 默认系统设置
INSERT INTO settings VALUES ('default_resolution', '2560x1600', '默认触摸屏分辨率');
INSERT INTO settings VALUES ('xml_version', '4.1.9', 'Project.xml 版本号');
```

---

## 5. 核心工作流：对话生成编排

### 5.1 流程概览

```
用户描述 ──→ [阶段1:解析] ──→ [阶段2:确认] ──→ [阶段3:分配] ──→ [阶段4:生成] ──→ [阶段5:校验]
             LLM              前端交互           纯算法            LLM×2          Python脚本
             ↓                ↓                  ↓                ↓              ↓
           JSON结构化       用户修改/确认     JoinNumber表     XML + .cht     校验报告
```

### 5.2 阶段1：需求解析（LLM）

**调用方式**：`POST /api/gen/sessions/{id}/parse`，SSE 流式返回

**Prompt 设计**（后端组装，非 SKILL.md 全文注入）：

```
System Prompt:
  你是 MKControl 中控系统需求解析器。
  从用户的自然语言描述中提取结构化信息。

  ## 协议库参考
  {从 _index.md 动态注入当前可用的协议列表}

  ## 输出格式（严格 JSON）
  {JSON Schema 定义}

User Prompt:
  {用户的自然语言需求描述}
```

**输出 JSON Schema**：

```json
{
  "devices": [
    {
      "name": "触摸屏",
      "type": "TP",
      "board": 10,
      "comm": "内置",
      "protocol_match": null
    },
    {
      "name": "TS-9101",
      "type": "RELAY",
      "board": 1,
      "comm": "内置继电器",
      "protocol_match": null
    }
  ],
  "functions": [
    {
      "name": "灯光1 开/关",
      "join_number": 103,
      "join_source": "user_specified",
      "control_type": "DFCButton",
      "btn_type": "AutolockBtn",
      "device": "TS-9101",
      "channel": 1,
      "action": "RELAY"
    }
  ],
  "pages": [
    {"name": "引导页", "type": "guide"},
    {"name": "主页", "type": "main"},
    {"name": "灯光控制", "type": "sub"}
  ],
  "missing_info": [
    "投影仪品牌型号未知，无法确定串口指令",
    "空调红外 UserIRDB 路径未提供"
  ],
  "image_path": null
}
```

### 5.3 阶段2：确认清单（前端渲染）

**后端将 JSON 转为前端可渲染的结构**，前端展示为可编辑表格：

- 设备清单表（可修改板卡号、删除设备、添加设备）
- 功能与 JoinNumber 表（可修改连接号、控件类型）
- 页面结构（可调整顺序、重命名）
- 缺失信息高亮提示
- 「确认」/「修改后重新解析」按钮

**用户确认后**：`POST /api/gen/sessions/{id}/confirm` 提交修改后的 JSON。

### 5.4 阶段3：JoinNumber 分配（纯算法，不用 LLM）

```python
class JoinRegistry:
    """JoinNumber 分配器"""

    SEGMENTS = {
        "system":    (1, 49),
        "light":     (100, 139),
        "curtain":   (100, 139),    # 与灯光共用号段，按顺序分配
        "screen":    (140, 149),
        "scene":     (140, 149),
        "picture":   (150, 169),
        "power":     (165, 169),
        "text":      (200, 299),
        "source":    (210, 239),
        "status":    (300, 499),
        "global":    (500, 599),
        "slider":    (1000, 1099),
        "extend":    (1100, 1199),
        "dialog":    (1200, 1299),
    }

    def allocate(self, confirmed_functions):
        """
        1. 先锁定用户指定的号
        2. 对未指定的按号段规则自动分配
        3. 冲突检测
        4. 输出完整 Join 映射表
        """
```

### 5.5 阶段4：双文件生成（LLM × 2，可并行）

**4a. XML 生成 Prompt**：

```
System:
  你是 MKControl Project.xml 生成器。
  严格按以下规范生成 XML。

  ## XML 结构规范（精简摘要）
  {从 xml-structure.md 提取关键规则，约 500 字}

  ## 控件规范（精简摘要）
  {从 controls-spec.md 提取本次用到的控件属性，约 800 字}

User:
  根据以下配置生成完整的 Project.xml：
  {confirmed_data JSON + join_registry JSON}

  版本：4.1.9
  分辨率：{settings.default_resolution}
  输出纯 XML，不要 markdown 包裹。
```

**4b. CHT 生成 Prompt**：

```
System:
  你是 MKControl .cht 程序生成器。
  严格按以下规范生成 Creator 代码。

  ## 语法规则（精简摘要）
  {从 syntax-rules.md 提取关键规则，约 500 字}

  ## 代码模式（按需注入匹配的模式）
  {根据 functions 中的设备类型，从 code-patterns.md 选择性注入}

  ## 设备协议（按需注入）
  {从 protocols/ 读取匹配的协议文件内容}

User:
  根据以下配置生成完整的 .cht 文件：
  {confirmed_data JSON + join_registry JSON}

  块顺序：DEFINE_DEVICE → DEFINE_VARIABLE → DEFINE_FUNCTION → DEFINE_START → DEFINE_EVENT
  输出纯代码，不要 markdown 包裹。
```

**Prompt 精简策略**：不注入整个参考文件，只注入本次生成相关的片段。减少 token 消耗，提升弱模型表现。

### 5.6 阶段5：交叉校验（Python 脚本，不用 LLM）

```python
# 直接调用已有的校验脚本
from core.scripts.cross_validate import cross_validate
from core.scripts.validate import validate_cht

report = {
    "cht_syntax": validate_cht(cht_content),
    "cross_check": cross_validate(xml_content, cht_content),
    "summary": {
        "critical": 0,
        "warning": 0,
        "details": []
    }
}
```

---

## 6. LLM 路由层

### 6.1 litellm 统一接口

```python
import litellm

async def llm_chat(messages, model=None, stream=True):
    """统一 LLM 调用入口"""
    if model is None:
        model = get_default_model()  # 从 llm_config 表读取

    response = await litellm.acompletion(
        model=model,
        messages=messages,
        stream=stream,
        temperature=0,           # 生成代码需要确定性
        response_format={"type": "json_object"},  # 阶段1强制JSON
    )
    return response
```

### 6.2 管理员配置模型示例

| 显示名 | provider | model | api_base |
|-------|----------|-------|----------|
| DeepSeek V3 | openai | deepseek-chat | https://api.deepseek.com |
| GPT-4o | openai | gpt-4o | https://api.openai.com |
| Claude Sonnet | anthropic | claude-sonnet-4-20250514 | — |
| 通义千问 Max | openai | qwen-max | https://dashscope.aliyuncs.com/compatible-mode |
| 本地 Qwen2.5 | ollama | qwen2.5:32b | http://localhost:11434 |

管理员在网页上填写以上信息，存入 `llm_config` 表。普通成员生成时使用默认模型，或管理员开放模型选择。

---

## 7. 前端页面设计

### 7.1 页面结构

```
/login                     ← 登录页
/                          ← 对话生成主页（普通成员默认页）
/history                   ← 历史记录
/history/:id               ← 查看某次生成详情
/admin/protocols           ← 协议管理（管理员）
/admin/protocols/new       ← 添加协议
/admin/protocols/:id/edit  ← 编辑协议
/admin/llm                 ← LLM 配置（管理员）
/admin/users               ← 用户管理（管理员）
/admin/settings            ← 系统设置（管理员）
```

### 7.2 核心页面：对话生成

```
┌─────────────────────────────────────────────────────────────┐
│  MDK Control Generator                    [用户名] [退出]    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─ 步骤指示器 ─────────────────────────────────────────┐  │
│  │ ① 描述需求  →  ② 确认清单  →  ③ 生成中  →  ④ 结果   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ 对话区域 ──────────────────────────────────────────┐   │
│  │                                                      │   │
│  │  [用户] 我需要用 TS-9101 控制 4 路灯光...           │   │
│  │                                                      │   │
│  │  [AI] 正在解析您的需求...                            │   │
│  │  ████████░░ 解析中                                   │   │
│  │                                                      │   │
│  │  [AI] 解析完成，请确认以下信息：                      │   │
│  │  ┌─ 设备清单 ─────────────────────────┐             │   │
│  │  │ 设备     | 类型  | 编号 | 通信方式  │             │   │
│  │  │ 触摸屏   | TP    | 10   | 内置     │             │   │
│  │  │ TS-9101  | RELAY | 1    | 继电器   │  [编辑]     │   │
│  │  └────────────────────────────────────┘             │   │
│  │  ┌─ 功能清单 ─────────────────────────┐             │   │
│  │  │ 功能   | Join | 控件类型 | 控制方式 │             │   │
│  │  │ 灯光1  | 103  | Button  | Autolock │  [编辑]     │   │
│  │  │ 全开   | 101  | Button  | Normal   │             │   │
│  │  └────────────────────────────────────┘             │   │
│  │  ⚠️ 缺失：投影仪品牌型号未知                         │   │
│  │                                                      │   │
│  │         [确认生成]  [修改后重新解析]                   │   │
│  │                                                      │   │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─ 输入框 ────────────────────────────────────────────┐   │
│  │ 描述你的中控需求...                         [发送]   │   │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 结果页面

```
┌─────────────────────────────────────────────────────────────┐
│  ④ 生成结果                                                 │
│                                                             │
│  ┌─ 标签页 ─────────────────────────────────────────────┐  │
│  │ [Project.xml]  [output.cht]  [校验报告]               │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │                                                      │  │
│  │  <?xml version="1.0" encoding="UTF-8"?>             │  │
│  │  <Project Version="4.1.9" Name="会议室控制"           │  │
│  │    Width="2560" Height="1600">                       │  │
│  │    <Object Type="DFCForm" Name="引导页">              │  │
│  │      <Control Type="DFCButton" ...>                  │  │
│  │      ...                                             │  │
│  │                                                      │  │
│  │                        代码高亮 + 行号                │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  [下载 XML]  [下载 .cht]  [打包下载 .zip]  [复制到剪贴板]   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. 后端项目结构

```
mdk/
├── web/                              ← 新增：Web 平台
│   ├── backend/                      ← FastAPI 后端
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py              ← FastAPI 入口
│   │   │   ├── config.py            ← 配置管理
│   │   │   ├── database.py          ← SQLite/PG 连接
│   │   │   │
│   │   │   ├── models/              ← 数据模型 (SQLAlchemy)
│   │   │   │   ├── user.py
│   │   │   │   ├── session.py
│   │   │   │   ├── protocol.py
│   │   │   │   └── setting.py
│   │   │   │
│   │   │   ├── schemas/             ← Pydantic 请求/响应模型
│   │   │   │   ├── auth.py
│   │   │   │   ├── gen.py           ← 生成相关（ParsedData/ConfirmedData 等）
│   │   │   │   ├── protocol.py
│   │   │   │   └── admin.py
│   │   │   │
│   │   │   ├── routers/             ← API 路由
│   │   │   │   ├── auth.py
│   │   │   │   ├── gen.py           ← 对话生成（核心）
│   │   │   │   ├── protocols.py
│   │   │   │   ├── ref.py           ← 参考查询
│   │   │   │   └── admin.py
│   │   │   │
│   │   │   ├── services/            ← 业务逻辑
│   │   │   │   ├── llm.py           ← LLM 路由层 (litellm 封装)
│   │   │   │   ├── orchestrator.py  ← 工作流编排（5 阶段）
│   │   │   │   ├── join_registry.py ← JoinNumber 分配算法
│   │   │   │   ├── prompt_builder.py← Prompt 模板组装
│   │   │   │   ├── knowledge.py     ← 知识库读取（protocols/references/docs）
│   │   │   │   └── validator.py     ← 调用 core/scripts/ 校验
│   │   │   │
│   │   │   └── prompts/             ← Prompt 模板（Jinja2）
│   │   │       ├── parse_system.md  ← 阶段1 system prompt
│   │   │       ├── xml_system.md    ← 阶段4a system prompt
│   │   │       └── cht_system.md    ← 阶段4b system prompt
│   │   │
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── alembic/                 ← 数据库迁移
│   │
│   └── frontend/                    ← React 前端
│       ├── src/
│       │   ├── App.tsx
│       │   ├── pages/
│       │   │   ├── Login.tsx
│       │   │   ├── Generator.tsx    ← 对话生成主页
│       │   │   ├── History.tsx
│       │   │   ├── admin/
│       │   │   │   ├── Protocols.tsx
│       │   │   │   ├── LlmConfig.tsx
│       │   │   │   ├── Users.tsx
│       │   │   │   └── Settings.tsx
│       │   ├── components/
│       │   │   ├── ChatMessage.tsx
│       │   │   ├── ConfirmTable.tsx  ← 可编辑确认清单
│       │   │   ├── CodePreview.tsx   ← 代码高亮预览
│       │   │   ├── StepIndicator.tsx
│       │   │   └── ProtocolForm.tsx
│       │   ├── hooks/
│       │   │   ├── useSSE.ts        ← SSE 流式接收
│       │   │   └── useAuth.ts
│       │   └── api/
│       │       └── client.ts        ← axios 封装
│       ├── package.json
│       ├── Dockerfile
│       └── vite.config.ts
│
├── core/                             ← 现有：知识库（不变）
├── commands/                         ← 现有：Claude Code 命令（不变）
├── adapters/                         ← 现有：各平台适配（不变）
└── docker-compose.yml               ← 新增：一键部署
```

---

## 9. Prompt 模板设计原则

### 9.1 与 SKILL.md 的关系

| SKILL.md（Claude Code 用） | Prompt 模板（Web 后端用） |
|---------------------------|-------------------------|
| 一个大文档，LLM 自行解读全部 | 按阶段拆分，每次只给必要信息 |
| LLM 自己决定读哪些文件 | 后端预读并注入相关片段 |
| 输出格式靠 LLM 自觉 | 强制 JSON Schema 输出 |
| 整个流程一次完成 | 分 5 步，后端编排 |

### 9.2 动态注入策略

```python
class PromptBuilder:
    def build_parse_prompt(self, description, protocols_index):
        """阶段1：只注入协议索引（~200 字），不注入控件规范"""

    def build_xml_prompt(self, confirmed_data, join_registry):
        """阶段4a：注入 xml-structure 摘要 + 用到的控件属性"""

    def build_cht_prompt(self, confirmed_data, join_registry, matched_protocols):
        """阶段4b：注入 syntax-rules 摘要 + 匹配的协议 + 匹配的代码模式"""
```

**每个 prompt 控制在 2000-4000 token**，确保弱模型也能处理。

---

## 10. Docker 部署

```yaml
# docker-compose.yml
version: "3.9"
services:
  backend:
    build: web/backend
    ports:
      - "8000:8000"
    volumes:
      - ./core:/app/core          # 挂载知识库
      - ./data:/app/data          # SQLite 数据持久化
    environment:
      - DATABASE_URL=sqlite:///data/mdk.db
      - CORE_DIR=/app/core

  frontend:
    build: web/frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    environment:
      - VITE_API_BASE=http://backend:8000
```

---

## 11. 实施阶段

### Phase W1：后端基础（预计 3 天工作量）
- FastAPI 项目初始化 + 数据库模型
- JWT 认证（login/register/me）
- LLM 路由层（litellm 封装 + 管理员配置接口）
- 知识库读取服务

### Phase W2：核心生成流程（预计 5 天工作量）
- Prompt 模板设计与调试
- 工作流编排器（5 阶段）
- JoinNumber 分配算法
- SSE 流式响应
- 校验器对接

### Phase W3：前端基础（预计 5 天工作量）
- React 项目初始化 + 路由 + 认证
- 对话生成主页（输入→解析→确认→生成→结果）
- 代码预览与下载
- 历史记录

### Phase W4：管理后台（预计 3 天工作量）
- 协议管理 CRUD
- LLM 配置界面
- 用户管理
- 系统设置

### Phase W5：部署与打磨（预计 2 天工作量）
- Docker Compose
- 首次部署测试
- UI 打磨（响应式、错误提示、加载状态）

---

## 12. 已确认决策

| 问题 | 决策 |
|------|------|
| 首个管理员账号 | 初始化时写入数据库（seed data），默认 admin/admin123，首次登录强制改密码 |
| 多人同时生成 | ✅ 支持并发，每个 session 独立 |
| 协议库存储 | 数据库为主（方便网页 CRUD），启动时从 core/protocols/ 同步初始数据 |
| 生成结果保留 | 永久保存，支持历史查询 |
| 版本对比 | ✅ 同一会话多次生成支持 diff 对比（unified + side-by-side） |
| 前端风格 | 简约专业风，浅色主题，Blue-500 主色调（详见 ui-design.md） |
| 确认清单渲染 | JSON → 可编辑表格（Tab 切换设备/功能/页面），内联编辑，join_source 彩色标签 |
| 结果预览 | 左右分栏（XML + .cht 对比），支持切换标签页模式，代码高亮+行号，校验报告可点击定位 |

详细 UI 设计文档：`.claude/plan/ui-design.md`
