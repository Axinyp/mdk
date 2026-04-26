# Stage 5 PRD 实施计划：智能中控编程生成系统

## 任务类型

- [X]  全栈（前端 + 后端）

## 背景

Stage 4（Agent Web）已稳定通过 Gate 1-4。
当前与 PRD 对齐度约 35%，以下 5 个需求是核心差距。
Gemini 不可用，前端架构建议由 Claude 综合 Codex 后端分析结果自行推演。

---

## Phase 0：基础设施（S，1-2 天）

### 目标

消除阻塞后续所有 schema 变更的技术风险。

### 实施步骤

**0.1 引入 Alembic 迁移**

- 当前用 `Base.metadata.create_all`，不安全演进已有表
- 安装 alembic，生成初始快照 revision，配置 `env.py` 使用 async SQLAlchemy
- 后续每个 Phase 必须生成对应迁移脚本

```
web/backend/
  alembic.ini
  alembic/
    env.py
    versions/
      0001_initial.py
```

**0.2 文件存储抽象**

- 新建 `services/storage.py`，接口：`save(data, filename) → key`，`load(key) → bytes`
- MVP：本地 `uploads/` 目录；接口不变可替换为 OSS/S3

**0.3 分页工具**

- 新建 `schemas/pagination.py`：`PagedResponse[T]`，供管理后台通用

### 关键文件


| 文件                                    | 操作 |
| --------------------------------------- | ---- |
| `web/backend/alembic.ini`               | 新建 |
| `web/backend/alembic/env.py`            | 新建 |
| `web/backend/app/services/storage.py`   | 新建 |
| `web/backend/app/schemas/pagination.py` | 新建 |

---

## Phase 1：多轮对话 + 反向追问（M，3-5 天）

### 目标

将"单次描述 → 处理完事"升级为真正的对话：系统发现缺失信息时主动追问，用户回复后继续。

### 后端变更那种

**新增 Model：`SessionMessage` + `ParseRevision`**

```python
class SessionMessage(Base):
    __tablename__ = "session_messages"
    id: Mapped[int]
    session_id: Mapped[str] = mapped_column(ForeignKey("gen_sessions.id"), index=True)
    role: Mapped[str]          # user | assistant
    kind: Mapped[str]          # description | clarification | answer
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime]

class ParseRevision(Base):
    __tablename__ = "parse_revisions"
    id: Mapped[int]
    session_id: Mapped[str] = mapped_column(ForeignKey("gen_sessions.id"), index=True)
    revision: Mapped[int]
    parsed_data: Mapped[str] = mapped_column(Text)   # JSON
    missing_info: Mapped[str] = mapped_column(Text)  # JSON array
    created_at: Mapped[datetime]
```

**GenSession 新增状态**

```
created → parsing → clarifying → parsed → confirmed → generating → completed/error
                        ↑_______↓
```

`clarifying`：`missing_info` 非空，等待用户补充

**新增 API**

```
POST /api/gen/sessions/{id}/messages      # 用户发回复，触发 re-parse
GET  /api/gen/sessions/{id}/messages      # 获取对话历史（按 created_at asc）
```

**新增 Service：`conversation_service.py`**

```python
async def reply_and_reparse(session_id: str, user_message: str, db) -> ParsedData:
    await add_message(session_id, role="user", kind="answer", content=user_message, db=db)
    history = await get_window(session_id, limit=12, db=db)  # 最多 12 轮防止 prompt 膨胀
    parsed = await llm_parse_with_history(history, config, db)
    revision_no = await save_revision(session_id, parsed, db)
    session.status = "clarifying" if parsed.missing_info else "parsed"
    await add_message(session_id, role="assistant", kind="clarification",
                      content=format_clarification(parsed.missing_info), db=db)
    return parsed
```

**修改 orchestrator.py**

- `stage_parse`：保存第一条 `description` 消息 + 解析结果 revision
- 若 `missing_info` 非空 → 状态转为 `clarifying`，生成追问消息

### 前端变更

**Generator.tsx**：重构为对话气泡 UI

- 左侧气泡：assistant（系统追问、状态提示）
- 右侧气泡：user（初始描述、后续回复）
- 底部：输入框（初次描述 or 回复）
- 确认按钮仅在 `status === "parsed"` 且 `missing_info.length === 0` 时可用

**移除补充信息区块**，改为对话流

### 关键文件


| 文件                                               | 操作                                  |
| -------------------------------------------------- | ------------------------------------- |
| `web/backend/app/models/session.py`                | 追加`SessionMessage`, `ParseRevision` |
| `web/backend/app/services/conversation_service.py` | 新建                                  |
| `web/backend/app/routers/gen.py`                   | 新增`/messages` 端点                  |
| `web/backend/app/services/orchestrator.py`         | 修改 stage_parse 支持 clarifying      |
| `web/frontend/src/pages/Generator.tsx`             | 重构为对话 UI                         |
| `alembic/versions/0002_multi_turn.py`              | 新建迁移                              |

### 风险


| 风险                              | 缓解                                            |
| --------------------------------- | ----------------------------------------------- |
| 多轮 parse 漂移（每轮结果不一致） | 持久化每次 ParseRevision，前端展示最新 revision |
| prompt 过长                       | 对话窗口限制 12 轮，超出后摘要压缩              |

---

## Phase 2：协议上传 + 审核工作流（L+M，7-10 天）

### 目标

用户在对话中上传协议文档（或粘贴文本）→ LLM 解析结构化协议 → 研发审核 → 入库。

### 后端变更

**新增 Model：`ProtocolSubmission`**

```python
class ProtocolSubmission(Base):
    __tablename__ = "protocol_submissions"
    id: Mapped[str]  # uuid
    session_id: Mapped[str | None] = mapped_column(ForeignKey("gen_sessions.id"))
    submitter_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    source_type: Mapped[str]    # paste | file
    raw_content: Mapped[str] = mapped_column(Text)
    filename: Mapped[str | None]
    extracted_protocol: Mapped[str | None] = mapped_column(Text)  # JSON，LLM 解析结果
    review_status: Mapped[str]  # processing | pending_review | approved | rejected
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    reviewer_note: Mapped[str | None]
    approved_protocol_id: Mapped[int | None] = mapped_column(ForeignKey("protocols.id"))
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

**扩展 `Protocol` Model**

```python
source: Mapped[str] = mapped_column(String, default="builtin")  # builtin | user_upload
source_submission_id: Mapped[str | None]
is_builtin: Mapped[bool] = mapped_column(default=True)
version: Mapped[str | None]  # v1.0 / v2.0
```

**新增 API（售后端）**

```
POST /api/gen/sessions/{id}/protocol-submissions   # 上传（multipart/form-data 或 JSON text）
GET  /api/gen/sessions/{id}/protocol-submissions   # 查看本次会话的提交状态
```

**新增 API（管理员端）**

```
GET  /api/admin/protocol-submissions?status=pending_review
GET  /api/admin/protocol-submissions/{id}
PUT  /api/admin/protocol-submissions/{id}          # 审核时编辑
POST /api/admin/protocol-submissions/{id}/approve
POST /api/admin/protocol-submissions/{id}/reject
```

**新增 Service：`protocol_ingestion.py`**

```python
async def ingest(raw_text: str, session_id: str, submitter_id: int, db) -> ProtocolSubmission:
    sub = await submission_repo.create(session_id, submitter_id, raw_text, status="processing", db=db)
    extracted = await llm_extract_protocol(raw_text, config)
    sub.extracted_protocol = json.dumps(extracted, ensure_ascii=False)
    sub.review_status = "pending_review"
    await db.commit()
    return sub

async def approve(submission_id: str, reviewer_id: int, edited: dict, db) -> Protocol:
    sub = await submission_repo.lock(submission_id, db)
    proto = Protocol(source="user_upload", source_submission_id=sub.id, is_builtin=False, **edited)
    db.add(proto)
    sub.review_status = "approved"
    sub.approved_protocol_id = proto.id
    await db.commit()
    return proto
```

**新增 LLM 协议解析 prompt**

- `web/backend/app/prompts/protocol_extract.md`
- 输入：原始文本（设备说明书片段 / 串口指令表 / IR code list）
- 输出：`{category, brand_model, comm_type, content（标准 Markdown 协议格式）}`

### 前端变更

**Generator.tsx**：在对话面板中增加"上传协议"操作

- 当系统提示某设备型号未在协议库中找到时，显示"上传协议"按钮
- 打开抽屉：tab1 粘贴文本，tab2 上传文件（accept: .txt,.md,.pdf,.docx）
- 提交后轮询 `review_status`，展示"待审核"状态徽章

**admin/Protocols.tsx**：拆分为两个 Tab

- Tab 1：审批通过的协议库（原有功能）
- Tab 2：待审核队列（diff 视图 + 编辑 + 批准/拒绝）

### 关键文件


| 文件                                                   | 操作                           |
| ------------------------------------------------------ | ------------------------------ |
| `web/backend/app/models/protocol.py`                   | 追加 source/version 字段       |
| `web/backend/app/models/submission.py`                 | 新建 ProtocolSubmission        |
| `web/backend/app/services/protocol_ingestion.py`       | 新建                           |
| `web/backend/app/prompts/protocol_extract.md`          | 新建                           |
| `web/backend/app/routers/gen.py`                       | 新增 protocol-submissions 端点 |
| `web/backend/app/routers/admin.py`                     | 新增审核端点                   |
| `web/frontend/src/pages/admin/Protocols.tsx`           | 重构加 Review Queue tab        |
| `web/frontend/src/components/ProtocolUploadDrawer.tsx` | 新建                           |
| `alembic/versions/0003_protocol_review.py`             | 新建迁移                       |

### 风险


| 风险              | 缓解                                                                     |
| ----------------- | ------------------------------------------------------------------------ |
| PDF/DOCX 解析复杂 | MVP 仅支持纯文本/Markdown，PDF 用 pdfplumber 提取文本后走同一路径        |
| 恶意上传          | MIME 白名单（text/plain, text/markdown, application/pdf），大小限制 10MB |
| 重复提交          | SHA256 去重，相同内容直接返回已有提交                                    |

---

## Phase 3：场景模式生成（M，3-5 天）

### 目标

自动生成会议/休息/离场等场景宏，在 CHT 代码中产生正确的 DEFINE_FUNCTION 场景联动。

### 后端变更

**扩展 Schema**

```python
class SceneActionItem(BaseModel):
    device: str
    action: str   # RELAY.On / COM.Send / IR.Send 等
    value: str | None = None

class SceneModeItem(BaseModel):
    name: str
    scene_type: Literal["meeting", "rest", "leave", "custom"]
    trigger_join: int = 0
    actions: list[SceneActionItem] = []

class ParsedData(BaseModel):
    ...
    scenes: list[SceneModeItem] = []
```

**新增 Service：`scene_service.py`**

- 确定性编译：将 `SceneModeItem` 直接编译为 CHT 片段，不依赖 LLM

```python
def compile_scene_to_cht(scene: SceneModeItem) -> str:
    lines = [f"DEFINE_FUNCTION {scene.name}()"]
    lines.append("{")
    for act in scene.actions:
        lines.append(f"    {render_action(act)};")
    lines.append("}")
    return "\n".join(lines)
```

**修改 parse_system.md**

- 添加规则：识别"会议/离场/休息"等场景关键词 → 填充 `scenes` 字段

**修改 cht_system.md**

- 添加场景 DEFINE_FUNCTION 生成规范（使用预编译片段注入）

**修改 orchestrator.py - stage_generate**

- 在构建 CHT prompt 前，调用 `scene_service.compile_all(confirmed.scenes)`，注入为已知片段

### 前端变更

**ConfirmationView.tsx**：新增场景编辑区

- 显示解析出的场景列表
- 每个场景卡片：名称、触发 JoinNumber、设备动作列表（可编辑）
- 新增场景按钮

### 关键文件


| 文件                                               | 操作                                |
| -------------------------------------------------- | ----------------------------------- |
| `web/backend/app/schemas/gen.py`                   | 追加 SceneModeItem, SceneActionItem |
| `web/backend/app/services/scene_service.py`        | 新建                                |
| `web/backend/app/services/orchestrator.py`         | 修改 stage_generate 注入场景        |
| `web/backend/app/prompts/parse_system.md`          | 新增场景解析规则                    |
| `web/backend/app/prompts/cht_system.md`            | 新增场景 CHT 规范                   |
| `web/frontend/src/components/ConfirmationView.tsx` | 新增场景编辑块                      |

---

## Phase 4：模板库（L，7-10 天）

### 目标

管理员上传 UI 风格模板，生成时 AI 推荐，用户选择后影响 XML 样式输出。

### 后端变更

**新增 Model**

```python
class UiTemplate(Base):
    __tablename__ = "ui_templates"
    id: Mapped[str]       # uuid
    name: Mapped[str]
    scene_type: Mapped[str]   # meeting | rest | leave | generic
    tags: Mapped[str] = mapped_column(Text)   # JSON list
    resolution: Mapped[str | None]            # 2560x1600 等
    manifest: Mapped[str] = mapped_column(Text)   # JSON，描述颜色/字体/组件样式
    preview_url: Mapped[str | None]
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime]

# GenSession 追加
selected_template_id: Mapped[str | None] = mapped_column(ForeignKey("ui_templates.id"))
template_recommendations: Mapped[str | None] = mapped_column(Text)  # JSON list of template ids + scores
```

**新增 API（管理员）**

```
POST   /api/admin/templates
GET    /api/admin/templates
PUT    /api/admin/templates/{id}
DELETE /api/admin/templates/{id}
POST   /api/admin/templates/{id}/preview    # 上传预览图
```

**新增 API（生成流程）**

```
POST /api/gen/sessions/{id}/template-recommendations   # 根据解析结果推荐模板
POST /api/gen/sessions/{id}/template-selection         # 用户选择
```

**新增 Service：`template_service.py`**

```python
def recommend(parsed: ParsedData, templates: list[UiTemplate]) -> list[TemplateScore]:
    scene_types = {s.scene_type for s in parsed.scenes}
    device_count = len(parsed.devices)
    scores = []
    for t in templates:
        score = (
            (2 if t.scene_type in scene_types else 0)
            + (1 if t.resolution == session_resolution else 0)
        )
        scores.append(TemplateScore(template=t, score=score))
    return sorted(scores, key=lambda x: -x.score)[:5]
```

### 前端变更

**新增 admin/Templates.tsx**：模板上传/管理/预览

**Generator.tsx**：在进入生成前增加"选择风格"步骤

- Step 0: 描述需求 → Step 0.5: 选择风格（可跳过）→ Step 1: 确认清单 → Step 2: 生成中

---

## 整体交付排期（建议）


| Phase     | 内容                           | 规模 | 依赖    |
| --------- | ------------------------------ | ---- | ------- |
| Phase 0   | 基础设施（Alembic + 存储抽象） | S    | -       |
| Phase 1   | 多轮对话 + 反向追问            | M    | Phase 0 |
| Phase 2+3 | 协议上传 + 审核工作流          | L+M  | Phase 0 |
| Phase 4   | 场景模式生成                   | M    | Phase 1 |
| Phase 5   | 模板库                         | L    | Phase 4 |

---

## SESSION_ID（供 /ccg:execute 使用）

- CODEX_SESSION: 019dc8b5-9824-71a1-9602-c3a701229887
- GEMINI_SESSION: N/A（不可用）
