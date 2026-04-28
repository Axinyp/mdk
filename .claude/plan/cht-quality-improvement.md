# CHT 生成质量优化计划

> **目标**：在不大改架构的前提下，逐步降低 LLM 生成 .cht 时的参数幻觉、提升准确率、减少 token 用量。
>
> **方法论**：基于真实生产代码（`兴业数金.cht` 1652 行 + `401会议室.cht` 2352 行）反推最有杠杆的改动点，按 PR 拆分，最小可上线为单位推进。
>
> **当前痛点（2026-04-28）**：
> - LLM 写出 `SEND_UDP(TP_10, 1, "192.168.1.100", 8000, "SWITCH")` 这种 5 参数错误调用（实际签名只支持 3 参数；详见契约表 §B.8）
> - cht_system.md 系统提示词中"Action 调用签名"表充满杜撰函数名（`UDP.Send` / `HTTP.Post` / `DIMMER.Set` 等中控并不存在），LLM 跟着学
> - 顶层 `device/channel` 字段对部分函数（SEND_UDP/SET_VOL_M/SET_MATRIX_M）无意义但被强制留空，schema 不自洽
> - cht_system.md 约 15-20k tokens，每次生成都全量注入
> - parse 阶段抽不到 IP/port/MAC 等附加参数 → 描述全文塞进 cht 阶段让 LLM 再抽一次（双重幻觉风险）
> - 强模板按键（如空调 30 个温度按键）每个 LLM 都重新生成一遍，浪费 token 且容易写错地址字节
>
> **基线文档（2026-04-28 已就位）**：
> - 设计原则：`.claude/plan/design-principles.md`（7 条已确认决策）
> - 契约表：`backend/app/references/core/action-params-contract.md`（Tier 1 核心 28 详写 + Tier 3 速查 + validator 规则）
> 本计划的所有改动基于这两份文档。

---

## 0. 真实生产代码现状分析

### 0.1 兴业数金.cht（1652 行）核心模式分布

| 模式 | 行数 | 行号区间 | 特征 |
|------|------|----------|------|
| 协议脚手架变量声明（华为 Box600 HTTP） | 110 | 18-127 | 16 个 URL 常量、6 个 JSON 模板字符串 |
| HttpPost / getJsonValue / setJsonValue 工具函数 | 125 | 129-253 | 字符级 JSON 解析（中控无 JSON 库） |
| handlerTimer hex 状态机 | 175 | 256-429 | 17 个 hex 码 → 摄像头预置位映射 |
| test/test1-5 巡检定时器 | 100 | 431-525 | 8 IP 循环 SEND_UDP + SLEEP |
| stayAlive 保活定时器 | 50 | 547-591 | HTTP 状态机 + 超时检测 |
| BUTTON_EVENT(tp) 大块（矩阵+拨号+业务） | 140 | 614-752 | if-else if 链 + switch case |
| 摄像机三套预置位（左/右/前）| 600 | 894-1462 | 12 按键 × 3 摄像机 = 36 等价块 |
| M2MDATA_EVENT HTTP 响应解析 | 70 | 1581-1650 | 嵌套状态机 |

### 0.2 401会议室.cht（2352 行）核心模式分布

| 模式 | 行数 | 行号区间 | 特征 |
|------|------|----------|------|
| send_ir 空调红外发码函数 | 580 | 126-708 | 5 风速 × 15 温度 = 75 case 嵌套 switch |
| get_date 日期更新函数 | 50 | 713-758 | 7 day 分支 SEND_TEXT |
| crc_cal CRC 计算 + Modbus_read_register | 60 | 765-807 | Modbus 协议工具函数 |
| Get_Sensor 温湿度处理 | 30 | 813-828 | 字节级数据解析 |
| BUTTON_EVENT(tp,144/145/146/147) scene 大块 | 250 | 922-1175 | 5 层嵌套 WAIT/SLEEP + 跨设备时序协调 |
| 窗帘 9 路控制（总开/总停/总关 + 前/后各 3 路） | 110 | 1261-1371 | 强模板：SET_COM 初始化 + SLEEP + SEND_COM hex |
| 空调温度按键 1101-1130（30 个等价按键） | 300 | 1845-2143 | 强模板：仅 air_conditioner 值不同 |
| LEVEL_EVENT(tp,1087) 音量拉条 | 35 | 2192-2226 | CRC 计算 + hex 拼接 + 定时器分发 |
| DATA_EVENT 传感器/IO | 35 | 2145-2173 / 2332-2347 | 数据驱动状态机 |

### 0.3 重新归类（整体可优化部分）

| 类别 | 占比 | 处置方式 |
|------|------|----------|
| 简单单按键 SEND_COM/SEND_IR 块 | ~30% | **代码渲染**（预先生成） |
| 强模板批量按键群（空调温度 30 个、摄像机预置位 36 个） | ~20% | **模板批量生成**（template_id 字段） |
| 工具函数（CRC/JSON 解析/get_date/Modbus） | ~10% | **模板库直接复用**（按需注入完整代码块） |
| 复杂 scene PUSH() 嵌套时序 | ~20% | **模式库召回**（few-shot LLM） |
| 数据驱动事件（DATA_EVENT/LEVEL_EVENT） | ~10% | **模式库召回** + LLM |
| 协议脚手架变量 | ~5% | **模式库召回**（HTTP 协议绑定整套变量） |
| 注释/空行/版权 | ~5% | 模板生成 |

**结论**：约 30% 直接代码渲染，约 30% 模板/模式库直接复用，约 35% LLM 处理（但有 few-shot 加持），约 5% 工程头注释。

---

## 1. 总体架构演进

### 1.1 当前架构

```
┌──────────────┐
│ user desc    │
└──────┬───────┘
       │
       ▼ parse stage (LLM)
┌──────────────────────────────────────┐
│ ParsedData                            │
│  ├─ devices[]                         │
│  ├─ functions[] (无 params 字段)      │
│  ├─ pages[]                           │
│  └─ scenes[]                          │
└──────┬───────────────────────────────┘
       │
       ▼ confirm stage
┌──────────────────────────────────────┐
│ ParsedData + join_registry            │
└──────┬───────────────────────────────┘
       │
       ▼ cht generation (LLM, 15-20k system prompt)
       │ ❌ description 全文塞进 prompt 让 LLM 二次抽参数
       │ ❌ 全量知识注入（syntax/blocks/functions/patterns/protocols）
       │ ❌ 强模板按键（空调 30 个）每个都让 LLM 写一遍
       │
       ▼
┌──────────────┐
│ cht 文件      │
└──────────────┘
```

### 1.2 改造后架构（PR-1 + PR-2 + PR-3 完成态）

```
┌──────────────┐
│ user desc    │
└──────┬───────┘
       │
       ▼ parse stage (LLM)
┌──────────────────────────────────────────────┐
│ ParsedData                                    │
│  ├─ devices[]                                 │
│  ├─ functions[]                               │
│  │    ├─ action: "SEND_UDP"|"ON_RELAY"|...    │ ← PR-1 真名直引
│  │    ├─ params {ip,port,str} / {dev,channel} │ ← PR-1 签名镜像
│  │    │   (顶层 device/channel 字段已移除)     │
│  │    └─ template_id "ac_temp" / "curtain"... │ ← PR-3 新增
│  ├─ pages[]                                   │
│  └─ scenes[] + pattern_hints[]                │ ← PR-2 新增
└──────┬───────────────────────────────────────┘
       │
       ▼ confirm stage（UI 条件渲染 params 输入框）
       │
       ▼ cht generation
       ┌────────────────────────────────────────┐
       │ Step A: pattern_hint 召回模式片段       │ ← PR-2
       │ Step B: template_id 批量预生成强模板    │ ← PR-3
       │ Step C: LLM 处理剩余（含 few-shot）     │
       │   - system prompt 缩到 ~5k tokens       │
       │   - 不再注入 description 全文           │
       │   - 仅注入命中的模式片段                │
       │ Step D: 拼接为完整 cht                  │
       └────────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│ cht 文件      │
└──────────────┘
```

### 1.3 三个核心改动总览

| PR | 主题 | 改动文件数 | 工作量 | 风险 |
|----|------|------------|--------|------|
| **PR-0**（已完成 2026-04-28）| 设计原则 + action × params 契约表 | 2（plan + ref） | 1 天 | 低 |
| **PR-1** | action 重命名（真名直引）+ FunctionItem 重构 + 契约校验 | 9 | 2-3 天 | 中（前后端 schema 同改） |
| **PR-2** | 模式库 + pattern_hint 召回 | 8 | 3-5 天 | 中 |
| **PR-3** | template_id 批量模板生成 | 6 | 2-3 天 | 中 |
| **PR-4**（暂缓） | scene 结构升级为"流程图" | 12+ | 5-7 天 | 高 |

---

## 2. PR-1：action × params 契约 + FunctionItem 重构

> **基线文档**：`backend/app/references/core/action-params-contract.md`（v0.1，2026-04-28）
> 本 PR 的所有改动以契约表为唯一权威。出现矛盾时，**以契约表为准**，再回头修正本计划。

### 2.1 目标

让 `action × params` 1:1 对齐中控官方函数签名，从根上消除"凭空多塞参数"幻觉：

1. **action 命名重构**：所有 action 改为**官方函数名直引**（`SEND_UDP` / `ON_RELAY` / `WAKEUP_ONLAN`...），不再使用 `UDP.Send` / `RELAY.On` / `Net.SendUdp` 这类杜撰归类
2. **params 字段引入**：在 parse 阶段把 IP/端口/数据/MAC/红外码等附加参数结构化抽出，cht 阶段直接读
3. **顶层 device/channel 字段移除**：所有参数统一走 params，schema 仅保留 `action + params`（详 design-principles §3）
4. **契约校验上线**：semantic_validator 加入 `ACTION_PARAMS_CONTRACT` 检查（缺/多/错都拦下）

### 2.2 收益

- ✅ 消除 SEND_UDP 类参数计数幻觉（`SEND_UDP("ip", port, "str")` 3 参数硬约束，多塞 device/channel 即报错）
- ✅ action 命名收敛到 Tier 1 核心 28 个枚举，LLM 不能再随手发明 `Net.Send`
- ✅ cht prompt 不再注入 description 全文（省 1-3k tokens）
- ✅ ConfirmationView 按契约表渲染 params 输入框，类型可校验
- ✅ schema 自洽：无论 SEND_UDP（无 dev）还是 SET_VOL_M（无 dev）都用一致的 `params{}` 表达

### 2.3 具体例子

**用户描述**：
> 投屏切换通过 UDP 发送到 192.168.1.100 端口 8000，开启发 0x424c01910001，关闭发 0x424c01910002。MAC 唤醒电脑使用 4437e65b1735。

**当前 parse 输出**（错的）：
```json
{
  "functions": [
    {"name":"投屏开","action":"UDP.Send","device":"TP_10","channel":1,"join_number":0},
    {"name":"电脑唤醒","action":"WAKEUP_ONLAN","device":"","join_number":0}
  ]
}
```
↑ 三处问题：①action 杜撰；②IP/端口/数据/MAC 全没抽；③`UDP.Send` 强塞 device/channel 没法对齐 `SEND_UDP(ip,port,str)` 签名。

**PR-1 后 parse 输出**：
```json
{
  "functions": [
    {
      "name": "投屏开",
      "join_number": 0,
      "action": "SEND_UDP",
      "params": {"ip":"192.168.1.100","port":8000,"str":"0x424c01910001"}
    },
    {
      "name": "投屏关",
      "join_number": 0,
      "action": "SEND_UDP",
      "params": {"ip":"192.168.1.100","port":8000,"str":"0x424c01910002"}
    },
    {
      "name": "电脑唤醒",
      "join_number": 0,
      "action": "WAKEUP_ONLAN",
      "params": {"MAC":"4437e65b1735"}
    }
  ]
}
```

**关键差异**（必须严格遵循契约表）：
- `action="SEND_UDP"` 不是 `"UDP.Send"`
- `params.str` 不是 `params.data`（官方签名第三参叫 `str`）
- `params.MAC` 大写，不是 `mac`（官方签名 `WAKEUP_ONLAN(String MAC)`）
- 顶层 device/channel 字段不存在
- `port` 是 int 不是 string

cht 阶段 LLM 收到 `{"action":"SEND_UDP","params":{"ip","port","str"}}` ←→ `void SEND_UDP(String ip, int port, String str)` 1:1 镜像，**多一个键就被 validator 拒**。

### 2.4 文件改动清单

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `backend/app/references/core/action-params-contract.md` | **已新增** | Tier 1 核心 28 函数契约 + Tier 3 工具速查 + validator 规则 |
| `backend/app/schemas/gen.py` | 修改 | FunctionItem 移除 device/channel/btn_type 顶层字段；新增 `params: dict[str,Any] = {}`；action 默认值改为必填 |
| `backend/app/services/semantic_validator.py` | 修改 | 加入 `ACTION_PARAMS_CONTRACT` 字典 + `validate_action_params(func)` 检查必填/禁用键/类型 |
| `backend/app/services/knowledge.py` | 修改 | `ACTION_TO_FUNC` 替换为契约表的 28 项；新增 `get_action_contract(action)` 返回单条契约描述 |
| `backend/app/prompts/parse_system.md` | 修改 | functions schema 用真名 action + params；新增"params 抽取规则"小节直接引用契约表 |
| `backend/app/prompts/cht_system.md` | 修改 | 整块替换"Action 调用签名"表为契约表摘要；强调"按 params 渲染，不要从描述中重抽" |
| `backend/app/services/prompt_builder.py` | 修改 | `build_cht_prompt` 移除 `raw_description_block`；XML/CHT 两处的 control_type/action 映射全部用真名 |
| `backend/app/services/orchestrator.py` | 修改 | `stage_confirm` 末尾追加契约校验；不通过则 `_mark_error` |
| `frontend/src/types/api.ts`（或同名 schema 镜像） | 修改 | FunctionItem 类型同步：移除 device/channel，新增 params |
| `frontend/src/components/ConfirmationView.tsx` | 修改 | 按 action 渲染 params 输入框（IP/port/MAC/str 等）；旧 device/channel 输入框删除或迁移到 params 内部 |

### 2.5 详细步骤

#### Step 1：扩展 schema（`backend/app/schemas/gen.py`）

**当前代码**（行 15-29）：

```python
class FunctionItem(BaseModel):
    name: str
    join_number: int = 0
    join_source: str | None = "auto"
    control_type: str | None = "DFCButton"
    btn_type: str | None = "NormalBtn"
    device: str | None = None
    channel: int | None = None
    action: str | None = ""
    image: str | None = None

    @field_validator('device', 'action', 'join_source', 'control_type', mode='before')
    @classmethod
    def coerce_none_str(cls, v: object) -> object:
        return "" if v is None else v
```

**改造后**（按 design-principles §3 + 契约表 §A.0）：

```python
from typing import Any

class FunctionItem(BaseModel):
    name: str
    join_number: int = 0
    join_source: str | None = "auto"
    control_type: str = "DFCButton"
    btn_type: str | None = "NormalBtn"
    action: str = ""                       # ★ 真名直引（SEND_UDP / ON_RELAY ...）
    params: dict[str, Any] = {}            # ★ 签名镜像，无参函数填 {}
    image: str | None = None
    template_id: str | None = None         # 预留 PR-3 占位符

    @field_validator('action', 'join_source', 'control_type', mode='before')
    @classmethod
    def coerce_none_str(cls, v: object) -> object:
        return "" if v is None else v

    # 顶层 device/channel/btn_type 字段移除（btn_type 仍保留是因前端控件区分需要）
    # 所有原 device/channel 数据迁入 params{}
```

**迁移代码（一次性脚本，针对存量 session）**：

```python
# backend/scripts/migrate_func_to_params.py
import json
from sqlalchemy import select
from app.database import SessionLocal
from app.models.session import GenSession

ACTION_RENAME = {
    "RELAY.On": "ON_RELAY", "RELAY.Off": "OFF_RELAY",
    "COM.Send": "SEND_COM", "IR.Send": "SEND_IRCODE",
    "DIMMER.Set": "SEND_LITE",
    "UDP.Send": "SEND_UDP", "TCP.Send": "SEND_TCP",
    "IP.Send": "SEND_UDP",   # 兜底：之前误用 IP.Send 的统一归到 SEND_UDP
    # 其他映射按契约表补
}

def migrate_one(func: dict) -> dict:
    action = ACTION_RENAME.get(func.get("action", ""), func.get("action", ""))
    dev = func.pop("device", None)
    ch = func.pop("channel", None)
    params = dict(func.get("params") or {})
    if action in ("ON_RELAY", "OFF_RELAY", "SEND_COM", "SEND_IRCODE", "SEND_LITE", "SEND_IO"):
        if dev: params["dev"] = dev
        if ch is not None: params["channel"] = int(ch)
    elif action in ("SET_BUTTON", "SET_LEVEL", "SEND_TEXT", "SEND_PAGING", "SEND_PICTURE"):
        if dev: params["dev"] = dev
        if ch is not None: params["channel"] = int(ch)
    func["action"] = action
    func["params"] = params
    return func
```

**验证**：
- 启动后端，老 session 反序列化迁移后不报错
- pydantic 接受 `params: {}` 和 `params: {"dev":"X","channel":1}` 两种输入
- `device`/`channel` 顶层字段从 API 响应中消失（前端类型同步更新）

#### Step 2：parse_system.md 改用契约表真名 + params

functions schema 中字段列表替换为：

```json
{
  "name": "投屏开",
  "control_type": "DFCButton",
  "btn_type": "NormalBtn",
  "action": "SEND_UDP",
  "params": {"ip": "192.168.1.100", "port": 8000, "str": "0x424c01910001"},
  "image": null
}
```

新增"规则 16 — action × params 契约"小节（直接引用契约表，避免重复维护）：

```markdown
### 16. action × params 契约

**action 必须从契约表 Tier 1 核心 28 中取**（详见 `backend/app/references/core/action-params-contract.md`）：

| 类别 | 可选 action |
|---|---|
| 设备控制 | ON_RELAY OFF_RELAY SEND_COM SEND_IRCODE SEND_LITE SEND_IO |
| 网络 | SEND_UDP SEND_TCP WAKEUP_ONLAN SEND_M2M_DATA SEND_M2M_JNPUSH SEND_M2M_JNRELEASE SEND_M2M_LEVEL |
| 触屏 UI | SET_BUTTON SET_LEVEL SEND_TEXT SEND_PAGING SEND_PICTURE |
| 主板独占 | SET_VOL_M SET_MATRIX_M |
| 流程控制 | SLEEP START_TIMER CANCEL_TIMER CANCEL_WAIT |
| 初始化 | SET_COM SET_IO_DIR |
| 调试 | TRACE |
| 模板（PR-3） | TEMPLATE |

**params 抽取规则**（键名严格按契约，不要改写）：

| action | 必填 params | 注意点 |
|---|---|---|
| ON_RELAY / OFF_RELAY | dev, channel | channel 是 int，从 1 起 |
| SEND_COM | dev, channel, str | **键名是 `str` 不是 `data`**；`0x` 开头表示 hex |
| SEND_IRCODE | dev, channel, str | `str` 可以是 `IRCODE<"...">` 引用 |
| SEND_LITE | dev, channel, val | val 范围 0~65535（不是 0~100） |
| SEND_IO | dev, channel, vol | vol = 0/1（高/低电平） |
| SEND_UDP / SEND_TCP | ip, port, str | **3 参数；不要塞 dev/channel** |
| WAKEUP_ONLAN | MAC | **大写 MAC**；12 位无分隔符（4437e65b1735） |
| SEND_M2M_DATA | ip, data | 这里键就叫 `data`（特例，不是 str） |
| SEND_M2M_JNPUSH/JNRELEASE | ip, jNumber | jNumber 驼峰 |
| SEND_M2M_LEVEL | ip, jNumber, val | |
| SET_BUTTON | dev, channel, state | state = 0/1 |
| SET_LEVEL | dev, channel, val | val 范围 0~65535 |
| SEND_TEXT | dev, channel, text | 键叫 text |
| SEND_PAGING | dev, channel, text | 同上 |
| SEND_PICTURE | dev, channel, picIndex | 文档未列，工程实测存在 |
| SET_VOL_M | channel, mute, vol | **无 dev**；vol 范围 [-60, 6] dB |
| SET_MATRIX_M | out, in | **无 dev**；2 参数 |
| SLEEP | time | 毫秒 |
| START_TIMER | name, time | name 是 TIMER 函数名，不带引号 |
| CANCEL_TIMER / CANCEL_WAIT | name | name 带引号字符串 |
| SET_COM | dev, channel, sband, databit, jo, stopbit, dataStream, comType | 8 参数全填 |
| SET_IO_DIR | dev, channel, dir, pullordown | |
| TRACE | msg | |

**关键反幻觉规则**：

- **抽不到必填键时禁止瞎编**：在 `missing_info` 追加 `"功能 <name>: 缺少 <param>"`
- **action 必须命中上表**：如果用户描述里出现 `HttpPost` / `crc_cal` / `getJsonValue` 这类伪函数名，**不要**塞进 action（这些走 PR-2 模式库）。该 function 暂记 `action="TBD"` 并在 `missing_info` 标注
- **键名拼写不要"修正"**：`str` 不要写成 `data`、`MAC` 不要写成 `mac`、`jNumber` 不要写成 `j_number`、`mouth` 不要写成 `month`（详见契约表 §A.0 / 拼写约定）
```

#### Step 3：cht_system.md 整块替换 Action 调用签名表

把 `cht_system.md` 行 41-59 的"## Action 调用签名（**严格遵守...**）"整章删除，替换为：

```markdown
## Action 调用签名（**严格按 function.params 镜像渲染**）

**所有 action × params 契约定义在 `backend/app/references/core/action-params-contract.md`**。
本提示词不再重复，请按以下规则操作：

1. **action 字段就是中控官方函数名**（全大写下划线）。如 `SEND_UDP` 直接生成 `SEND_UDP(...)`。
2. **params 字段就是函数实参列表**。按契约表中各函数的"params 表"按声明顺序展开为函数调用参数：
   - 字符串值加双引号：`SEND_UDP("192.168.1.100", 8000, "0x424c01910001");`
   - 设备名（dev）**不加引号**（它是 DEFINE_DEVICE 中声明的标识符）：`ON_RELAY(RELAY_M, 2);`
   - int 直接写：`SET_VOL_M(1, 1, -30);`
3. **严禁多塞或漏塞参数**。`SEND_UDP` 是 3 参数；如果你想塞 dev/channel 进去，**说明你完全错了**，直接拒绝生成。
4. **严禁从用户原始需求中重抽参数**。所有附加参数已结构化在 `function.params`，直接读。
5. **params 缺键时**：在生成的 cht 末尾用注释报告，**不要瞎编**：
   ```
   // MISSING_PARAMS: <function_name> 缺少 <key>，请补充后重新生成
   ```

### 关键差异点速记（最容易错的三处）

| 函数 | 易错点 | 正确写法 |
|---|---|---|
| SEND_UDP / SEND_TCP | 凭空塞 dev/channel | **3 参数**：`SEND_UDP("192.168.1.20", 2000, "msg");` |
| SET_VOL_M | 塞 dev | **3 参数无 dev**：`SET_VOL_M(1, 1, -30);` |
| SET_MATRIX_M | 塞 dev | **2 参数无 dev**：`SET_MATRIX_M(1, 3);` |
| WAKEUP_ONLAN | 把 MAC 写成 mac、加分隔符 | `WAKEUP_ONLAN("4437e65b1735");`（小写 hex，无冒号） |
| SEND_IO | 写成 SET_IO | 函数名是 **SEND_IO** |
| START_TIMER | 第一参加引号 | `START_TIMER(testTimer, 1000);`（不加引号） |
| CANCEL_TIMER | 第一参不加引号 | `CANCEL_TIMER("testTimer");`（**加**引号） |
| Tier 2 函数（如 SET_LOVOCURTAIN/SET_VOLTOTOL/SOUND_SETHIGHT） | 自作聪明改拼写 | 编辑器签名为准；详见契约表 §D + design-principles §4 |
```

#### Step 4：prompt_builder.build_cht_prompt 移除描述全文注入

**当前代码**（`backend/app/services/prompt_builder.py` 行 161-167）：

```python
raw_description_block = ""
if project_description:
    raw_description_block = (
        f"\n\n## 用户原始需求（提取 IP/端口/红外码/MAC 等附加参数时参考）\n"
        f"```\n{project_description}\n```\n"
    )
```

**改造后**：直接删除 `raw_description_block` 变量与 user_content 中对它的引用：

```python
user_content = (
    f"根据以下配置生成完整的 .cht 文件：\n\n"
    f"```json\n{json.dumps(config, ensure_ascii=False, indent=2)}\n```\n"
    f"{header_info}"
    f"{scenes_instruction}\n"
    f"基于 CHT 骨架模板填充各 {{block}} 占位符，输出完整代码。\n"
    f"块顺序：DEFINE_DEVICE → DEFINE_COMBINE → DEFINE_CONSTANT → DEFINE_VARIABLE → "
    f"DEFINE_FUNCTION → DEFINE_TIMER → DEFINE_START → DEFINE_EVENT → DEFINE_PROGRAME\n"
    f"输出纯代码，不要 markdown 包裹。"
)
```

`header_info` 中的"需求描述（注释用，简述）"保留，仅供工程头注释；不再用于参数抽取。

`collect_matched_patterns` 内的 action 关键词匹配同步从 `("RELAY",)` 等老风格改成 `("ON_RELAY","OFF_RELAY")`：

```python
def collect_matched_patterns(confirmed_data: ParsedData) -> list[str]:
    keywords = set()
    for func in confirmed_data.functions:
        action = (func.action or "").upper()
        if action in ("ON_RELAY", "OFF_RELAY"):
            keywords.add("继电器")
        elif action == "SEND_COM":
            keywords.add("串口")
        elif action == "SEND_IRCODE":
            keywords.add("红外")
        elif action in ("SET_LEVEL", "SET_VOL_M", "SEND_M2M_LEVEL"):
            keywords.add("音量")
        elif action == "SEND_IO":
            keywords.add("IO")
        elif action in ("SEND_UDP", "SEND_TCP", "WAKEUP_ONLAN"):
            keywords.add("网络")
        # ... PR-2 后改为 confirmed.pattern_hints 精确召回
    ...
```

#### Step 5：semantic_validator.py 加入契约校验

**新增模块（或扩展现有 `semantic_validator.py`）**：把契约表 §F 的 `ACTION_PARAMS_CONTRACT` 字典直接挪过来：

```python
# backend/app/services/semantic_validator.py

ACTION_PARAMS_CONTRACT: dict[str, dict] = {
    "ON_RELAY":          {"required": ["dev", "channel"]},
    "OFF_RELAY":         {"required": ["dev", "channel"]},
    "SEND_COM":          {"required": ["dev", "channel", "str"]},
    "SEND_IRCODE":       {"required": ["dev", "channel", "str"]},
    "SEND_LITE":         {"required": ["dev", "channel", "val"]},
    "SEND_IO":           {"required": ["dev", "channel", "vol"]},
    "SEND_TCP":          {"required": ["ip", "port", "str"], "forbidden": ["dev", "channel"]},
    "SEND_UDP":          {"required": ["ip", "port", "str"], "forbidden": ["dev", "channel"]},
    "WAKEUP_ONLAN":      {"required": ["MAC"]},
    "SEND_M2M_DATA":     {"required": ["ip", "data"]},
    "SEND_M2M_JNPUSH":   {"required": ["ip", "jNumber"]},
    "SEND_M2M_JNRELEASE":{"required": ["ip", "jNumber"]},
    "SEND_M2M_LEVEL":    {"required": ["ip", "jNumber", "val"]},
    "SET_BUTTON":        {"required": ["dev", "channel", "state"]},
    "SET_LEVEL":         {"required": ["dev", "channel", "val"]},
    "SEND_TEXT":         {"required": ["dev", "channel", "text"]},
    "SEND_PAGING":       {"required": ["dev", "channel", "text"]},
    "SEND_PICTURE":      {"required": ["dev", "channel", "picIndex"]},
    "SET_VOL_M":         {"required": ["channel", "mute", "vol"], "forbidden": ["dev"]},
    "SET_MATRIX_M":      {"required": ["out", "in"], "forbidden": ["dev"]},
    "SLEEP":             {"required": ["time"]},
    "START_TIMER":       {"required": ["name", "time"]},
    "CANCEL_TIMER":      {"required": ["name"]},
    "CANCEL_WAIT":       {"required": ["name"]},
    "SET_COM":           {"required": ["dev","channel","sband","databit","jo","stopbit","dataStream","comType"]},
    "SET_IO_DIR":        {"required": ["dev","channel","dir","pullordown"]},
    "TRACE":             {"required": ["msg"]},
    "TEMPLATE":          {"required": ["template_id", "count", "start_join"]},
}


def validate_action_params(func: FunctionItem, devices: list[DeviceItem]) -> list[str]:
    """对单个 FunctionItem 跑契约校验。返回问题列表（空表示通过）。"""
    issues: list[str] = []
    action = (func.action or "").upper()
    if not action or action == "TBD":
        return issues  # 解析阶段标记的待确认项，不在此层校验
    contract = ACTION_PARAMS_CONTRACT.get(action)
    if not contract:
        # Tier 2/3 或未知函数 — 仅记 warning（前缀 [warn]）
        issues.append(f"[warn] 功能 '{func.name}': action '{action}' 不在 Tier 1 契约表，无法校验参数")
        return issues
    params = func.params or {}
    for key in contract.get("required", []):
        if key not in params or params[key] in (None, ""):
            issues.append(f"功能 '{func.name}' ({action}): 缺少必填参数 '{key}'")
    for key in contract.get("forbidden", []):
        if key in params:
            issues.append(
                f"功能 '{func.name}' ({action}): 不应包含参数 '{key}'，"
                f"{action} 只接受 {contract.get('required')}"
            )
    if "dev" in (contract.get("required") or []):
        dev_name = params.get("dev")
        device_names = {d.name for d in devices}
        if dev_name and dev_name not in device_names:
            issues.append(f"功能 '{func.name}' ({action}): dev='{dev_name}' 未在 DEFINE_DEVICE 声明")
    return issues


def validate_parsed_data(parsed: ParsedData) -> list[str]:
    """整体校验。原有语义检查 + 契约检查合并返回。"""
    issues = _legacy_semantic_checks(parsed)        # 现有逻辑保留
    for func in parsed.functions:
        issues.extend(validate_action_params(func, parsed.devices))
    return issues
```

#### Step 6：orchestrator 在 confirm 阶段挂上契约校验

**当前**（`orchestrator.py` 行 158-172 `stage_confirm`）只做 join 分配。改造后追加契约校验：

```python
async def stage_confirm(db: AsyncSession, session_id: str, confirmed: ParsedData) -> list[FunctionItem]:
    logger.info("[FLOW] ===== 确认阶段 session={} =====", session_id[:8])
    session = await _transition(db, session_id, SessionStatus.CONFIRMED)

    try:
        # ── PR-1: 契约校验（critical 级阻断；warning 级仅入库提示） ──
        issues = semantic_validator.validate_parsed_data(confirmed)
        critical = [s for s in issues if not s.startswith("[warn]")]
        if critical:
            logger.warning("[FLOW] 契约校验阻断 — {} 个 critical 问题", len(critical))
            await _mark_error(session, db, "Contract validation failed:\n" + "\n".join(critical))
            raise ValueError("Contract validation failed: " + "; ".join(critical[:3]))

        functions_with_joins = join_registry.allocate(confirmed.functions)
        logger.debug("[FLOW] Join 分配完成, 功能数={}", len(functions_with_joins))
        session.confirmed_data = json.dumps(confirmed.model_dump(), ensure_ascii=False)
        session.join_registry = json.dumps([f.model_dump() for f in functions_with_joins], ensure_ascii=False)
        await db.commit()
        logger.debug("[DB] 确认数据已持久化 session={}", session_id[:8])
        return functions_with_joins
    except Exception:
        await _mark_error(session, db, "Confirm stage failed")
        raise
```

#### Step 7：ConfirmationView.tsx 按契约渲染 params

按契约表的"params 表"为每个 action 渲染对应输入框。建议抽出 `ParamsForm` 子组件 + 一份 `ACTION_PARAMS_FORM_SPEC` 配置（前端版本的契约镜像）：

```tsx
// frontend/src/components/ParamsForm.tsx
type FieldSpec = { key: string; label: string; type: 'string' | 'int' | 'hex'; placeholder?: string }

const ACTION_PARAMS_FORM_SPEC: Record<string, FieldSpec[]> = {
  SEND_UDP: [
    { key: 'ip',   label: 'IP 地址', type: 'string', placeholder: '192.168.1.100' },
    { key: 'port', label: '端口',    type: 'int',    placeholder: '8000' },
    { key: 'str',  label: '数据串',  type: 'string', placeholder: '0x424c01910001' },
  ],
  SEND_TCP: [/* 同上 */],
  WAKEUP_ONLAN: [
    { key: 'MAC', label: 'MAC 地址（无分隔符）', type: 'string', placeholder: '4437e65b1735' },
  ],
  ON_RELAY: [
    { key: 'dev',     label: '设备',   type: 'string', placeholder: 'RELAY_M' },
    { key: 'channel', label: '通道',   type: 'int',    placeholder: '1' },
  ],
  SEND_IRCODE: [
    { key: 'dev',     label: '设备',     type: 'string' },
    { key: 'channel', label: '通道',     type: 'int' },
    { key: 'str',     label: '红外码',   type: 'string', placeholder: 'IRCODE<"...">' },
  ],
  SEND_LITE: [
    { key: 'dev',     label: '设备',   type: 'string' },
    { key: 'channel', label: '通道',   type: 'int' },
    { key: 'val',     label: '亮度',   type: 'int',    placeholder: '0~65535' },
  ],
  SET_VOL_M: [
    { key: 'channel', label: '通道',   type: 'int' },
    { key: 'mute',    label: '静音',   type: 'int',    placeholder: '0/1' },
    { key: 'vol',     label: '音量dB', type: 'int',    placeholder: '-60~6' },
  ],
  // ... 其余 action 按契约表逐一对齐
}

export function ParamsForm({ action, params, onChange }: Props) {
  const fields = ACTION_PARAMS_FORM_SPEC[action]
  if (!fields) return null
  return (
    <div className="grid grid-cols-3 gap-2">
      {fields.map(f => (
        <input
          key={f.key}
          placeholder={`${f.label}${f.placeholder ? ` (${f.placeholder})` : ''}`}
          type={f.type === 'int' ? 'number' : 'text'}
          value={params?.[f.key] ?? ''}
          onChange={(e) => {
            const v = f.type === 'int' ? Number(e.target.value) : e.target.value
            onChange({ ...params, [f.key]: v })
          }}
        />
      ))}
    </div>
  )
}
```

ConfirmationView 中替换原 device/channel 输入为：

```tsx
<ParamsForm
  action={func.action}
  params={func.params}
  onChange={(next) => updateFunc(idx, { params: next })}
/>
```

> **同步注意**：`ACTION_PARAMS_FORM_SPEC` 与 `ACTION_PARAMS_CONTRACT` 必须同步；建议在 `frontend/src/types/contract.ts` 单独维护 + 写一个单测对比 keys 一致。

### 2.6 验收标准

- [ ] **契约校验**：`semantic_validator.validate_parsed_data` 对契约表 §F 全部 28 项有单测覆盖（require/forbidden 双向）
- [ ] **action 命名**：parse 输出的 `action` 字段 100% 在契约表 Tier 1 枚举内（命中率 = 1）
- [ ] **SEND_UDP 反幻觉**：以"通过 UDP 发送 192.168.1.100:8000 0x424c01910001"为输入，生成的 cht 中 `SEND_UDP\(` 行参数计数严格为 3（不出现 device/channel）
- [ ] **键名严格性**：parse 输出 params 的键名完全等于契约表（`str` 不是 `data`、`MAC` 不是 `mac`、`jNumber` 不是 `j_number`），用单测固定
- [ ] **schema 顶层无 device/channel**：`FunctionItem.model_json_schema()` 不包含这两个字段
- [ ] **token 下降**：cht user prompt 较改造前下降 1-3k（描述全文已移除），用 tiktoken 测量
- [ ] **存量迁移**：`migrate_func_to_params.py` 跑过后，所有历史 session 反序列化通过且 `device`/`channel` 已搬入 `params`
- [ ] **前端表单**：ConfirmationView 切换 action 后 ParamsForm 正确渲染对应字段；保存后 params 形态 = 契约表

---

## 3. PR-2：模式库 + pattern_hint 召回

### 3.1 目标

把生产 cht 文件中的高复用模式切成"片段"入库，parse 阶段为每个 scene/function 标记 `pattern_hint`，cht 阶段按命中模式注入对应片段作为 few-shot，让 LLM **抄**而不是**编**。

### 3.2 收益

- ✅ 消除"凭空发明协议变量"问题（华为 Box600 的 16 个 URL 常量直接整套注入）
- ✅ 复杂 scene 嵌套时序有了参考蓝本，不再 LLM 自由发挥
- ✅ CRC/JSON 解析这类工具函数直接复制粘贴，零幻觉

### 3.3 模式库初版（基于现有两份生产代码可抽取出的模式）

| pattern_id | 名称 | 触发关键词 | 来源 | 大小 |
|------------|------|-----------|------|------|
| `huawei_box_http` | 华为 Box600 视频会议接入 | 华为/Box/视频会议/SessionID | 兴业数金 18-127 + 138-145 | ~2k tokens |
| `json_parse_kit` | JSON 字符级解析工具集 | HTTP/JSON/API | 兴业数金 153-253 | ~1.5k tokens |
| `matrix_switch` | HDMI 矩阵输入输出按键耦合 | 矩阵/HDMI 切换 | 兴业数金 614-628 | ~300 tokens |
| `dial_pad` | 12 键拨号面板 | 拨号/号码输入 | 兴业数金 646-717 | ~500 tokens |
| `camera_preset_x12` | 12 预置位摄像机 | 摄像机/预置位 | 兴业数金 894-1083 | ~1.5k tokens（一套，模板化复用） |
| `camera_ptz` | 摄像机方向键+变焦 PUSH/RELEASE | 摄像机/上下左右/变焦 | 兴业数金 895-967 | ~600 tokens |
| `mic_tracking` | 会议单元 hex 码跟踪 | 跟踪/会议单元/话筒 | 兴业数金 256-429 | ~2k tokens |
| `device_polling` | 巡检定时器（多 IP 循环 + SLEEP） | 学生机/巡检/批量 | 兴业数金 431-525 | ~600 tokens |
| `aircon_ir_temp` | 空调红外发码（含 SEND_TEXT 状态） | 空调/温度/红外 | 401会议室 126-708 | ~3k tokens（按需截取） |
| `curtain_3way` | 窗帘开/停/关三按键模板 | 窗帘 | 401会议室 1261-1371 | ~400 tokens |
| `crc_modbus` | CRC 校验 + Modbus 寄存器读 | 传感器/Modbus | 401会议室 765-807 | ~500 tokens |
| `volume_dsp_slider` | DSP 音量拉条 + CRC 增益计算 | 音量/拉条/DSP | 401会议室 2192-2226 | ~500 tokens |
| `relay_on_release_off` | 继电器按下开/松开关 PUSH/RELEASE | 临时开/点动 | 401会议室 1741-1771 | ~200 tokens |
| `scene_sequential_relay` | 场景多级延时通电（WAIT 嵌套） | 场景/会议模式/极简模式 | 401会议室 922-1175 | ~2k tokens |
| `date_display` | 实时日期星期几显示 | 日期/星期 | 401会议室 713-758 | ~500 tokens |
| `sensor_data_event` | 串口传感器 DATA_EVENT 解析 | 温湿度/传感器 | 401会议室 813-828 + 2145-2173 | ~600 tokens |
| `io_input_state` | IO 口电平变化驱动状态同步 | IO/电平/接通 | 401会议室 2332-2347 | ~300 tokens |

总计 17 个模式，覆盖 ~85% 的生产代码场景。

### 3.4 模式文件结构

每个模式存为一个 markdown 文件：

```
backend/app/references/core/patterns/
├── _index.md                  # 现有，扩展为模式查询索引
├── relay.md                   # 现有
├── ir.md                      # 现有
├── ...                        # 其他现有
└── pro/                       # 新增子目录：生产级模式（来自真实工程）
    ├── _index.md
    ├── huawei-box-http.md
    ├── json-parse-kit.md
    ├── matrix-switch.md
    ├── dial-pad.md
    ├── camera-preset-x12.md
    ├── aircon-ir-temp.md
    ├── curtain-3way.md
    ├── crc-modbus.md
    ├── volume-dsp-slider.md
    ├── scene-sequential-relay.md
    ├── date-display.md
    ├── sensor-data-event.md
    └── io-input-state.md
```

每个文件结构：

```markdown
---
pattern_id: scene_sequential_relay
name: 场景多级延时通电
triggers: [场景, 会议模式, 极简模式, 离开模式, 上电时序]
applies_to: [DEFINE_EVENT]
size_tokens: 2000
---

## 模式说明
适用于"场景按键触发后按时序通电多个继电器，并同步触摸屏按钮状态"的需求。

## 关键技术点
- 嵌套 `WAIT N { ... }` 实现毫秒级时序
- 每开一路继电器同时调用 `SET_BUTTON(tp, <btn_id>, 1)` 同步 UI 状态
- 末尾用 `SLEEP(7000)` 等待硬件稳定后再发其他设备指令

## 代码模板（来自 401会议室.cht 行 1019-1097）

```cht
BUTTON_EVENT(tp,144) // 显示与投屏场景
{
    PUSH()
    {
        currentScene = 3;
        // 互斥按钮状态清零
        SET_BUTTON(tp, 145, 0);
        SET_BUTTON(tp, 146, 0);
        SET_BUTTON(tp, 147, 0);
        SET_BUTTON(tp, 144, 1);
        // 第 1 级：电脑、分屏器、POE 交换机
        ON_RELAY(L9101_RELAY, 4);
        SET_BUTTON(tp, 115, 1);
        WAIT 1000
        {
            // 第 2 级：前灯关闭
            OFF_RELAY(L9101_RELAY, 1);
            SET_BUTTON(tp, 112, 0);
            WAIT 1000
            {
                // 第 3 级：投影、演讲桌
                ON_RELAY(L9101_RELAY, 3);
                SET_BUTTON(tp, 114, 1);
                // ... 继续嵌套
            }
        }
        // 时序结束后发空调红外、设置音量等
        SLEEP(7000);
        SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"...">); 
    }
}
```

## 套用方法
- 替换 `tp,144` 为 scene 触发的 join_number
- 替换 `currentScene = 3` 为该场景的整数 ID
- 互斥 SET_BUTTON 列表 = 其他 scene 按键的 join_number
- 各级 ON_RELAY/OFF_RELAY 按 scene.actions 顺序展开
```

### 3.5 召回流程

```
┌────────────────────────────────────┐
│ ParsedData (含 scenes + functions) │
└──────────┬─────────────────────────┘
           │
           ▼ parse_system.md 的新规则要求 LLM 输出 pattern_hints
┌────────────────────────────────────┐
│ ParsedData.pattern_hints[]:         │
│   ["scene_sequential_relay",        │
│    "aircon_ir_temp",                │
│    "curtain_3way"]                  │
└──────────┬─────────────────────────┘
           │
           ▼ build_cht_prompt（PR-2 修改）
┌────────────────────────────────────┐
│ load_patterns(pattern_hints)        │
│   for hint in hints:                │
│     片段 = pattern_dir/<hint>.md    │
│     注入 system prompt              │
└──────────┬─────────────────────────┘
           │
           ▼
┌────────────────────────────────────┐
│ system prompt =                     │
│   原 cht_system.md 模板             │
│   + 命中的模式片段（few-shot）       │
└────────────────────────────────────┘
```

### 3.6 文件改动清单

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `backend/app/references/core/patterns/pro/*.md` | 新增 | 17 个模式文件（首批先做 6 个最高频的） |
| `backend/app/references/core/patterns/pro/_index.md` | 新增 | 模式索引 + 触发关键词表 |
| `backend/app/schemas/gen.py` | 修改 | ParsedData 添加 `pattern_hints: list[str] = []` |
| `backend/app/prompts/parse_system.md` | 修改 | 新增 pattern_hints 字段 + 抽取规则 |
| `backend/app/services/knowledge.py` | 修改 | 新增 `get_pro_pattern(pattern_id: str) -> str` 函数 |
| `backend/app/services/prompt_builder.py` | 修改 | `collect_matched_patterns` 改为读 `confirmed.pattern_hints` |
| `backend/app/prompts/cht_system.md` | 修改 | `{{ code_patterns }}` 占位符的注释更新（说明这是模式库召回片段） |
| `frontend/src/components/ConfirmationView.tsx` | 修改 | 在确认面板顶部展示命中的模式列表（可读，不可编辑） |

### 3.7 详细步骤

#### Step 1：建立模式库目录与首批 6 个高频模式

优先抽取这 6 个（覆盖最常见场景）：

1. `scene-sequential-relay.md` — 几乎所有工程都有 scene 时序
2. `curtain-3way.md` — 窗帘控制几乎所有会议室都有
3. `aircon-ir-temp.md` — 空调红外 30 个温度按键的强模板
4. `volume-dsp-slider.md` — 音量 LEVEL_EVENT 拉条
5. `relay_on_release_off.md` — 继电器点动控制
6. `crc-modbus.md` — Modbus 串口传感器

每个文件按 §3.4 的结构写，从生产代码精确复制带注释。

#### Step 2：扩展 ParsedData

```python
class ParsedData(BaseModel):
    devices: list[DeviceItem] = []
    functions: list[FunctionItem] = []
    pages: list[PageItem] = []
    missing_info: list[str] = []
    image_path: str | None = None
    scenes: list[SceneModeItem] = []
    pattern_hints: list[str] = []   # ← 新增
```

#### Step 3：parse_system.md 增加 pattern_hints 抽取规则

在 JSON schema 末尾追加：

```json
{
  ...,
  "pattern_hints": ["scene_sequential_relay", "curtain_3way"]
}
```

并新增"规则 17"：

```
17. **pattern_hints 字段**：根据用户描述中出现的关键词，从模式库中匹配可能用到的模式 ID。
    可用模式 ID 与触发词对照（命中即填入数组，不命中则空数组）：

    | pattern_id | 触发词 |
    |------------|--------|
    | scene_sequential_relay | 场景/模式/会议模式/极简/离开/扩声 |
    | curtain_3way | 窗帘 |
    | aircon_ir_temp | 空调/温度/制冷 |
    | volume_dsp_slider | 音量/拉条/DSP |
    | relay_on_release_off | 点动/按住/临时开 |
    | crc_modbus | 传感器/Modbus/485 寄存器 |
    | huawei_box_http | 华为/Box/视频会议主机 |
    | json_parse_kit | HTTP/REST/JSON 接口 |
    | matrix_switch | HDMI 矩阵/视频矩阵 |
    | dial_pad | 拨号/号码盘 |
    | camera_preset_x12 | 摄像机预置位 |
    | camera_ptz | 摄像机云台/PTZ |
    | mic_tracking | 会议单元/话筒跟踪 |
    | device_polling | 巡检/学生机/批量发包 |
    | date_display | 日期/时间/星期 |
    | sensor_data_event | 温湿度/PM2.5/CO2 |
    | io_input_state | IO 接通/断开/电平变化 |
```

#### Step 4：knowledge.py 新增 get_pro_pattern

在 `backend/app/services/knowledge.py` 末尾追加：

```python
PRO_PATTERNS_DIR = PATTERNS_DIR / "pro"

def get_pro_pattern(pattern_id: str) -> str:
    """读取生产级模式片段（来自真实工程切片）"""
    safe_id = re.sub(r'[^a-z0-9_-]', '', pattern_id.lower())
    if not safe_id:
        return ""
    path = PRO_PATTERNS_DIR / f"{safe_id.replace('_', '-')}.md"
    return _read(path)


def list_pro_patterns() -> list[str]:
    """列出所有可用的生产模式 ID"""
    if not PRO_PATTERNS_DIR.exists():
        return []
    return sorted(
        f.stem.replace('-', '_')
        for f in PRO_PATTERNS_DIR.glob("*.md")
        if not f.name.startswith("_")
    )
```

#### Step 5：prompt_builder.collect_matched_patterns 改造

**当前代码**（`backend/app/services/prompt_builder.py` 行 209-239）使用关键词匹配做软召回，改造为优先用 pattern_hints 精确召回：

```python
def collect_matched_patterns(confirmed: ParsedData) -> list[str]:
    """优先使用 LLM 标记的 pattern_hints，回落到关键词匹配"""
    results = []

    # 优先：精确召回 pattern_hints 标记的生产模式
    if confirmed.pattern_hints:
        for hint in confirmed.pattern_hints:
            content = knowledge.get_pro_pattern(hint)
            if content:
                results.append(content)
            else:
                logger.warning("[KNOWLEDGE] pattern_hint 未找到: {}", hint)

    # 回落：原有关键词匹配（兼容老 session）
    if not results:
        keywords = set()
        for func in confirmed.functions:
            action = (func.action or "").upper()
            if action == "RELAY":
                keywords.add("继电器")
            elif action == "COM":
                keywords.add("串口")
            # ... 现有逻辑保持

        for kw in keywords:
            pattern = knowledge.get_pattern(kw)
            if pattern:
                results.append(pattern)

    return results
```

#### Step 6：cht_system.md 占位符注释更新

在 `## 代码模式参考` 章节标题下方追加一句：

```markdown
## 代码模式参考
> 以下片段从真实生产工程（兴业数金、401 会议室等）中切片而来，是经过验证的代码模板。
> **请优先按这些片段的风格生成代码**：变量命名、注释格式、嵌套时序写法都要保持一致。
> 当模式中的代码与你的常识冲突时，**以模式片段为准**。

{{ code_patterns }}
```

#### Step 7：ConfirmationView 展示命中模式（可选展示）

在确认面板顶部增加一行：

```tsx
{parsedData.pattern_hints && parsedData.pattern_hints.length > 0 && (
  <div className="mb-3 px-3 py-2 bg-blue-50 border border-blue-200 rounded text-xs">
    <span className="font-semibold text-blue-700">💡 已识别参考模式：</span>
    {parsedData.pattern_hints.map(h => (
      <span key={h} className="ml-2 px-2 py-0.5 bg-white rounded border">{h}</span>
    ))}
  </div>
)}
```

只读展示，让用户知道生成时会参考哪些模板。

### 3.8 验收标准

- [ ] 描述含"窗帘开关" → parse 输出 pattern_hints 包含 `curtain_3way`
- [ ] 生成 cht 时，windowed 控制按键的代码风格与 401会议室.cht 行 1261-1300 一致（SET_COM 初始化 + SLEEP + SEND_COM hex）
- [ ] 描述含"会议模式 + 灯光 + 空调 + 投影" → parse 标记 `scene_sequential_relay`，生成的场景按键带正确的 WAIT 嵌套时序
- [ ] cht system prompt 在命中 3 个模式时总长度仍小于 25k tokens（可控）
- [ ] 用 401 会议室原描述回归生成，对比手写代码 diff 减少 30%+ 行数差异

---

## 4. PR-3：FunctionItem.template_id 字段（强模板批量生成）

### 4.1 目标

对于"30 个空调温度按键"、"36 个摄像机预置位按键"这种**只有少量参数差异的等价按键群**，让 LLM 标记一个 template_id + 参数表，后端代码直接批量渲染，**完全跳过 LLM 写代码**。

### 4.2 收益

- ✅ 批量按键（30/36 个等）零幻觉（地址字节绝不会写错）
- ✅ 节省 1-3k 输出 tokens
- ✅ LLM 从"写 30 段相似代码"变成"标记 1 个 template_id + 1 个参数列表"

### 4.3 触发场景

| template_id | 应用场景 | 参数 | 来源 |
|-------------|----------|------|------|
| `aircon_temp_buttons` | 空调温度按键群（16-30°） | start_join, ir_device, ir_codes_map | 401会议室 1845-2143 |
| `camera_preset_x12` | 摄像机 12 预置位按键 | start_join, com_device, com_channel | 兴业数金 985-1083 |
| `relay_simple_toggle` | 单按键开关继电器 | join, relay_device, channel | 普遍 |
| `relay_pulse` | 短脉冲继电器（按下开 1 秒后自动关） | join, relay_device, channel, pulse_ms | 401 行 2322-2330 |
| `curtain_3way` | 窗帘开/停/关三按键 | open_join, stop_join, close_join, com_device, hex_codes | 401 行 1261-1300 |

### 4.4 具体例子（空调温度按键）

**当前 LLM 输出**（约 300 行）：

```cht
BUTTON_EVENT(tp,1101)  { PUSH() { air_conditioner = 16; send_ir(air_conditioner,0); } }
BUTTON_EVENT(tp,1102)  { PUSH() { air_conditioner = 17; send_ir(air_conditioner,0); } }
BUTTON_EVENT(tp,1103)  { PUSH() { air_conditioner = 18; send_ir(air_conditioner,0); } }
... (再来 27 个等价块)
BUTTON_EVENT(tp,1130)  { PUSH() { air_conditioner = 30; send_ir(air_conditioner,0); } }
```

**改造后 parse 输出**：

```json
{
  "functions": [
    {
      "name": "空调温度按键群",
      "action": "TEMPLATE",
      "template_id": "aircon_temp_buttons",
      "params": {
        "start_join": 1101,
        "temp_min": 16,
        "temp_max": 30,
        "var_name": "air_conditioner",
        "send_func": "send_ir",
        "send_func_args_template": "<temp>, 0"
      }
    }
  ]
}
```

**后端代码渲染**（`cht_template_renderer.py`）：

```python
def render_aircon_temp_buttons(params: dict) -> str:
    blocks = []
    start = params["start_join"]
    for i, temp in enumerate(range(params["temp_min"], params["temp_max"] + 1)):
        join = start + i
        var = params["var_name"]
        func = params["send_func"]
        args = params["send_func_args_template"].replace("<temp>", str(temp))
        blocks.append(f"""
    BUTTON_EVENT(tp,{join})\t//空调温度 {temp}°
    {{
        PUSH()
        {{
            SET_BUTTON(tp,231,1);
            {var} = {temp};
            {func}({args});
        }}
    }}""")
    return "\n".join(blocks)
```

### 4.5 文件改动清单

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `backend/app/services/cht_template_renderer.py` | 新增 | 模板渲染器，每个 template_id 一个 render 函数 |
| `backend/app/schemas/gen.py` | 修改 | FunctionItem 添加 `template_id: str \| None = None` |
| `backend/app/prompts/parse_system.md` | 修改 | 增加 template_id 标记规则 |
| `backend/app/prompts/cht_system.md` | 修改 | 告诉 LLM "遇到 template_id 字段则跳过该 function 的事件块生成"（避免重复） |
| `backend/app/services/orchestrator.py` | 修改 | cht 生成完成后调用 renderer 注入模板生成的代码 |
| `frontend/src/components/ConfirmationView.tsx` | 修改 | 模板 function 的展示样式不同（折叠显示，参数可编辑） |

### 4.6 详细步骤

#### Step 1：编写 cht_template_renderer.py

```python
# backend/app/services/cht_template_renderer.py

from typing import Callable
from loguru import logger
from ..schemas.gen import FunctionItem


_RENDERERS: dict[str, Callable[[dict], str]] = {}


def register(template_id: str):
    def decorator(fn: Callable[[dict], str]):
        _RENDERERS[template_id] = fn
        return fn
    return decorator


@register("aircon_temp_buttons")
def render_aircon_temp_buttons(params: dict) -> str:
    """空调温度按键群（16-30°），每度一个按键"""
    start = params.get("start_join", 1101)
    temp_min = params.get("temp_min", 16)
    temp_max = params.get("temp_max", 30)
    var_name = params.get("var_name", "air_conditioner")
    send_func = params.get("send_func", "send_ir")
    args_tpl = params.get("send_func_args_template", "<temp>, 0")
    state_btn = params.get("state_button_join", 231)

    blocks = []
    for i, temp in enumerate(range(temp_min, temp_max + 1)):
        join = start + i
        args = args_tpl.replace("<temp>", str(temp))
        blocks.append(
            f"\tBUTTON_EVENT(tp,{join})\t//空调温度 {temp}°\n"
            f"\t{{\n"
            f"\t\tPUSH()\n"
            f"\t\t{{\n"
            f"\t\t\tSET_BUTTON(tp,{state_btn},1);\n"
            f"\t\t\t{var_name} = {temp};\n"
            f"\t\t\t{send_func}({args});\n"
            f"\t\t}}\n"
            f"\t}}\n"
        )
    return "\n".join(blocks)


@register("relay_simple_toggle")
def render_relay_simple_toggle(params: dict) -> str:
    """单按键继电器开关（PUSH=ON, RELEASE=OFF）"""
    join = params["join"]
    device = params["relay_device"]
    channel = params.get("channel", 1)
    label = params.get("label", "")
    return (
        f"\tBUTTON_EVENT(tp,{join})\t//{label}\n"
        f"\t{{\n"
        f"\t\tPUSH()    {{ ON_RELAY({device},{channel}); }}\n"
        f"\t\tRELEASE() {{ OFF_RELAY({device},{channel}); }}\n"
        f"\t}}\n"
    )


@register("curtain_3way")
def render_curtain_3way(params: dict) -> str:
    """窗帘开/停/关三按键模板"""
    open_join = params["open_join"]
    stop_join = params["stop_join"]
    close_join = params["close_join"]
    com_device = params["com_device"]
    com_channel = params.get("com_channel", 2)
    open_hex = params["open_hex"]
    stop_hex = params["stop_hex"]
    close_hex = params["close_hex"]
    setcom_args = params.get("setcom_args", "9600,8,0,10,0,485")

    init = f"SET_COM({com_device},{com_channel},{setcom_args});"
    return f"""
\tBUTTON_EVENT(tp,{open_join})\t//窗帘开
\t{{
\t\tPUSH()
\t\t{{
\t\t\t{init}
\t\t\tSLEEP(1000);
\t\t\tSEND_COM({com_device},{com_channel},"{open_hex}");
\t\t}}
\t}}

\tBUTTON_EVENT(tp,{stop_join})\t//窗帘停
\t{{
\t\tPUSH()
\t\t{{
\t\t\t{init}
\t\t\tSLEEP(1000);
\t\t\tSEND_COM({com_device},{com_channel},"{stop_hex}");
\t\t}}
\t}}

\tBUTTON_EVENT(tp,{close_join})\t//窗帘关
\t{{
\t\tPUSH()
\t\t{{
\t\t\t{init}
\t\t\tSLEEP(1000);
\t\t\tSEND_COM({com_device},{com_channel},"{close_hex}");
\t\t}}
\t}}
"""


def render(template_id: str, params: dict) -> str:
    """根据 template_id 调用对应渲染器"""
    fn = _RENDERERS.get(template_id)
    if not fn:
        logger.warning("[CHT_RENDER] 未知模板: {}", template_id)
        return f"\t// UNKNOWN_TEMPLATE: {template_id}\n"
    try:
        return fn(params)
    except KeyError as exc:
        logger.error("[CHT_RENDER] 模板 {} 缺少参数: {}", template_id, exc)
        return f"\t// TEMPLATE_PARAM_MISSING: {template_id} -> {exc}\n"


def list_supported_templates() -> list[str]:
    return sorted(_RENDERERS.keys())
```

#### Step 2：扩展 FunctionItem

```python
class FunctionItem(BaseModel):
    name: str
    join_number: int = 0
    join_source: str | None = "auto"
    control_type: str | None = "DFCButton"
    btn_type: str | None = "NormalBtn"
    device: str | None = None
    channel: int | None = None
    action: str | None = ""
    image: str | None = None
    params: dict[str, Any] | None = None
    template_id: str | None = None    # ← PR-3 新增
```

#### Step 3：parse_system.md 增加 template_id 标记规则

新增"规则 18"：

```
18. **template_id 字段**：当用户描述涉及"按键群"或"批量等价按键"时，标记 template_id 而不是逐个生成 function。
    可用模板 ID 与触发条件：

    | template_id | 何时使用 | 必需 params |
    |-------------|----------|-------------|
    | aircon_temp_buttons | 描述提到空调有温度调节按键群（16-30°） | start_join, temp_min, temp_max, var_name, send_func |
    | camera_preset_x12 | 描述提到摄像机 12 个预置位按键 | start_join, com_device, com_channel |
    | curtain_3way | 描述提到窗帘开/停/关三按键 | open_join, stop_join, close_join, com_device, open_hex, stop_hex, close_hex |
    | relay_simple_toggle | 描述提到 1 个继电器单按键控制 | join, relay_device, channel |
    | relay_pulse | 描述提到电脑开关机按钮（短脉冲） | join, relay_device, channel, pulse_ms |

    使用模板时：
    - 该 function 的 action 设为 "TEMPLATE"
    - device/channel/join_number 留空（实际值在 params 中）
    - 在 params 中填入模板要求的所有键
    - 不要再为 16-30° 各生成一个 function（用模板会一次性渲染）
```

#### Step 4：cht_system.md 告诉 LLM 跳过模板 function

在"## 生成策略"章节追加一条：

```
8. **遇到 action="TEMPLATE" 的 function，跳过其 BUTTON_EVENT 生成**。
   这类 function 会由后端模板渲染器在 LLM 输出后注入对应代码块。
   你只需要：
   - 在 DEFINE_VARIABLE 中按需声明配套变量（如 air_conditioner）
   - 在 DEFINE_FUNCTION 中按需声明配套函数（如 send_ir，参考 aircon_ir_temp 模式）
   - **不要为模板 function 生成 BUTTON_EVENT 块**
```

#### Step 5：orchestrator.stage_generate 注入模板渲染结果

**当前代码**（`backend/app/services/orchestrator.py` 行 277-285）：

```python
cht_content = _strip_control_chars(_strip_fence(cht_content))
session.cht_content = cht_content
```

**改造后**：

```python
cht_content = _strip_control_chars(_strip_fence(cht_content))

# PR-3: 注入模板渲染的代码块
from . import cht_template_renderer
template_blocks = []
for func in functions_with_joins:
    if func.action == "TEMPLATE" and func.template_id:
        rendered = cht_template_renderer.render(func.template_id, func.params or {})
        if rendered.strip():
            template_blocks.append(f"\t// [模板:{func.template_id}] {func.name}\n{rendered}")
            logger.info("[CHT_RENDER] 注入模板 {} -> {} 行", func.template_id, rendered.count('\n'))

if template_blocks:
    cht_content = _inject_into_define_event(cht_content, "\n".join(template_blocks))

session.cht_content = cht_content
```

并实现注入辅助函数：

```python
def _inject_into_define_event(cht: str, blocks: str) -> str:
    """在 DEFINE_PROGRAME 之前插入额外的事件块"""
    marker = "\nDEFINE_PROGRAME"
    if marker in cht:
        idx = cht.index(marker)
        return cht[:idx] + "\n\n" + blocks + cht[idx:]
    # 兜底：追加到末尾
    return cht + "\n\n" + blocks
```

#### Step 6：ConfirmationView 模板 function 展示

```tsx
{func.action === 'TEMPLATE' ? (
  <div className="border-l-4 border-purple-400 pl-3 bg-purple-50">
    <div className="font-mono text-xs text-purple-700">📦 {func.template_id}</div>
    <div className="text-sm text-gray-700 mt-1">{func.name}</div>
    <details className="mt-2">
      <summary className="text-xs cursor-pointer">参数预览</summary>
      <pre className="text-xs bg-white p-2 mt-1 border rounded">
        {JSON.stringify(func.params, null, 2)}
      </pre>
    </details>
  </div>
) : (
  // 原有 function 编辑表单
)}
```

### 4.7 验收标准

- [ ] 描述含"空调温度 16 到 30 度可调，按键从 1101 开始" → parse 输出 1 个 function with template_id=aircon_temp_buttons
- [ ] 生成的 cht 中，BUTTON_EVENT(tp,1101) 到 BUTTON_EVENT(tp,1115) 全部存在且完全一致（除温度值与 join 号外）
- [ ] LLM 输出的 cht 中**不**包含温度按键的事件块（已由后端注入）
- [ ] `cht_template_renderer.list_supported_templates()` 返回所有已注册模板，单测覆盖每个 render 函数

---

## 5. PR-4（暂缓）：scene 结构升级为"流程图"

### 5.1 为什么暂缓

当前 `SceneActionItem` 只有 device/action/value 三字段，**无法表达**：
- 嵌套 WAIT 时序（401 会议室场景按键里 5 层嵌套）
- 条件分支（`if (pcpower == 0) { ... }`）
- 跨场景互斥按钮状态同步

如果要支持，需要把 SceneActionItem 升级为：

```python
class SceneStep(BaseModel):
    type: Literal["call", "wait", "if", "set_button", "sleep"]
    # type=call: device + action + value
    # type=wait: duration_ms + children: list[SceneStep]
    # type=if: condition + then_branch + else_branch
    # type=set_button: join + state
    # type=sleep: duration_ms
    ...
```

ConfirmationView 也要从"action 平铺列表"改为"嵌套树形编辑器"，这部分前端工作量很大。

### 5.2 推荐策略

**先靠 PR-2 的 `scene_sequential_relay` 模式片段让 LLM 抄写正确的 WAIT 嵌套**，观察实际效果。如果 LLM 抄得对，PR-4 就不需要做。如果抄错率仍高，再启动 PR-4。

---

## 6. 时间表与上线节奏

```
Week 1
├─ Day 1-2: PR-1（params 字段）开发 + 测试 + 上线
├─ Day 3-5: PR-2 第 1 批（6 个高频模式）开发
└─ Week 1 验证：用现有真实工程描述回归生成，对比 diff

Week 2
├─ Day 6-7: PR-2 第 2 批（剩余 11 个模式）补齐
├─ Day 8-9: PR-3（template_id）开发 + 模板 5 个
└─ Day 10:  上线观察，收集 1 周用户反馈

Week 3+
└─ 视效果决定是否启动 PR-4
```

每个 PR **独立可发布**，互不阻塞。如果 PR-1 上线后效果已经达标，后续 PR 可以延期。

---

## 7. 验收基线（回归测试方案）

### 7.1 基线工程

将以下两份真实工程作为黄金基准：
- `兴业数金.cht`（1652 行，复杂业务）
- `401会议室.cht`（2352 行，多场景多设备）

### 7.2 基线描述提取

针对每份工程，**人工**编写一份"用户原始描述"（如 401 会议室约 600 字描述）。这份描述模拟真实用户提交给系统的输入。

存放位置：`backend/tests/fixtures/regression/`：
- `xingye_jinjin/description.md`（兴业数金的需求描述）
- `xingye_jinjin/expected.cht`（手写 cht，作为黄金基准）
- `room401/description.md`
- `room401/expected.cht`

### 7.3 衡量指标

每个 PR 上线后跑回归脚本，对比生成结果 vs 黄金基准：

| 指标 | 衡量方法 | 改造前 | PR-1 目标 | PR-2 目标 | PR-3 目标 |
|------|----------|--------|-----------|-----------|-----------|
| `SEND_UDP/TCP/WAKEUP_ONLAN` 参数计数错误率 | grep 调用 + 计参数数 | 30% | <5% | <2% | <1% |
| cht system prompt token 数 | tiktoken 计算 | 18k | 16k | 22k（含模式） | 22k |
| cht user prompt token 数 | tiktoken 计算 | 5k | 3k | 3k | 3k |
| cht 输出 token 数 | tiktoken 计算 | 12k | 12k | 11k | 8k（模板减负） |
| 与黄金基准 diff 行数（仅看结构差异，不看具体值） | difflib 比较 | 800 行 | 700 | 500 | 350 |
| 编译通过率（用中控编译器测） | 编译命令 | 60% | 75% | 88% | 92% |

### 7.4 自动化脚本

```python
# backend/tests/regression_cht.py
import json
import difflib
from pathlib import Path

def regression_test(case_dir: Path) -> dict:
    desc = (case_dir / "description.md").read_text(encoding="utf-8")
    golden = (case_dir / "expected.cht").read_text(encoding="utf-8")

    # 调用完整 parse → confirm → generate 流水线
    parsed = parse_pipeline(desc)
    confirmed = confirm_pipeline(parsed)
    generated = generate_pipeline(confirmed)

    diff = list(difflib.unified_diff(
        golden.splitlines(), generated.splitlines(),
        n=0
    ))

    return {
        "case": case_dir.name,
        "diff_lines": len(diff),
        "udp_arg_errors": count_udp_arg_errors(generated),
        "compile_pass": try_compile(generated),
    }
```

每次 PR 合并前必须跑这个脚本，所有指标不得倒退。

---

## 8. 总结

### 8.1 三个 PR 的杠杆点

| PR | 关键洞察 |
|----|----------|
| PR-1 | 与其让 cht 阶段 LLM 二次抽参数，不如让 parse 阶段一次抽到位（结构化优先） |
| PR-2 | 与其让 LLM 凭空写复杂代码，不如让它"抄"经过验证的生产模式（few-shot 优先） |
| PR-3 | 与其让 LLM 重复写 30 个等价按键，不如让它标记一个 template_id（编码确定性优先） |

### 8.2 共同哲学

**LLM 擅长的**：
- 理解需求 → 结构化 JSON
- 选择合适的模式（pattern_hints / template_id）
- 处理罕见的、需要"理解"的逻辑

**LLM 不擅长的**：
- 一字不差地复制长字节序列（hex 码、地址字节）
- 重复书写多个等价单元（30 个温度按键）
- 严格遵守参数计数（SEND_UDP 3 参数 vs 5 参数）

我们要做的就是**把 LLM 不擅长的部分挪给代码做**，把 LLM 擅长的部分留给 LLM。

### 8.3 不做什么

- ❌ 不重写整个 cht 生成路径（保留 LLM 主流程）
- ❌ 不删除现有的关键词匹配 `collect_matched_patterns`（作为 fallback）
- ❌ 不强制要求 LLM 100% 使用 template_id（标记不到时回落到普通生成）
- ❌ PR-4 暂不做（先验证 PR-2 的模式召回效果）

### 8.4 开工前你需要确认

1. ✅ 这个方向你认可吗？还是觉得某个 PR 价值不够？
2. ✅ 模式库初版的 17 个模式覆盖率合适吗？还有哪些场景需要追加？
3. ✅ 时间表（Week 1 完成 PR-1+PR-2 第一批）合理吗？
4. ✅ 验收基线放在你已有的两份工程上 OK 吗？还是需要补充更多基线？

确认后我从 **PR-1（params 字段）开始**，因为它是最小风险、最快见效的改动。

---

## 附录 A：当前 cht_system.md 的占位符与改造对照

| 占位符 | 当前注入内容 | PR-1 后 | PR-2 后 | PR-3 后 |
|--------|--------------|---------|---------|---------|
| `{{ cht_skeleton }}` | 完整骨架 | 不变 | 不变 | 不变 |
| `{{ cht_devices_ref }}` | 设备声明规则 | 不变 | 不变 | 不变 |
| `{{ cht_events_ref }}` | 事件模板 | 不变 | 不变 | 不变 |
| `{{ syntax_rules_summary }}` | 通用语法规则 | 不变 | 不变 | 不变 |
| `{{ block_definitions }}` | DEFINE_DEVICE/EVENT/START 语法 | 不变 | 不变 | 不变 |
| `{{ system_functions }}` | 按 action 类型注入 | **action 名换契约表真名后注入对应函数文档** | 不变 | 不变 |
| `{{ code_patterns }}` | 关键词匹配的旧 patterns | 触发关键词同步真名 | **改为 pattern_hints 精确召回** | 不变 |
| `{{ matched_protocols }}` | 设备协议手册 | 不变 | 不变 | 不变 |
| Action 调用签名表（嵌在模板里） | 杜撰风格（UDP.Send/HTTP.Post...） | **删除该表，改为引用 action-params-contract.md + 速记表** | 不变 | 不变 |
| 用户描述全文 | 注入 user prompt | **删除** | 不变 | 不变 |

## 附录 B：FunctionItem 演进表

| 字段 | 当前 | PR-1 | PR-3 | 备注 |
|------|------|------|------|------|
| name | ✅ | ✅ | ✅ | |
| join_number | ✅ | ✅ | ✅ | join_registry 分配 |
| join_source | ✅ | ✅ | ✅ | |
| control_type | ✅ | ✅ | ✅ | |
| btn_type | ✅ | ✅ | ✅ | 前端控件区分仍需要 |
| **device** | ✅ | ❌（移除） | ❌ | 数据迁移到 `params.dev` |
| **channel** | ✅ | ❌（移除） | ❌ | 数据迁移到 `params.channel` |
| **action** | ✅ 杜撰风格 | ✅ **契约表真名**（Tier 1 枚举） | ✅ 新增 `"TEMPLATE"` 值 | `SEND_UDP` 等官方函数名 |
| image | ✅ | ✅ | ✅ | |
| **params** | ❌ | ✅ 必填 dict | ✅ | 签名镜像；契约表 §B |
| **template_id** | ❌ | ❌ | ✅ | PR-3 占位符 |

**action 取值范围（PR-1 起强约束）**：
```
ON_RELAY OFF_RELAY SEND_COM SEND_IRCODE SEND_LITE SEND_IO
SEND_UDP SEND_TCP WAKEUP_ONLAN
SEND_M2M_DATA SEND_M2M_JNPUSH SEND_M2M_JNRELEASE SEND_M2M_LEVEL
SET_BUTTON SET_LEVEL SEND_TEXT SEND_PAGING SEND_PICTURE
SET_VOL_M SET_MATRIX_M
SLEEP START_TIMER CANCEL_TIMER CANCEL_WAIT
SET_COM SET_IO_DIR
TRACE
TEMPLATE     ← PR-3
TBD          ← parse 标记缺参待确认（不进 cht 渲染）
```
其他值由 `semantic_validator.validate_action_params` 标 `[warn]`，进入 missing_info；不阻断流水线。

## 附录 C：ParsedData 演进表

| 字段 | 当前 | PR-2 |
|------|------|------|
| devices | ✅ | ✅ |
| functions | ✅ | ✅ |
| pages | ✅ | ✅ |
| missing_info | ✅ | ✅ |
| image_path | ✅ | ✅ |
| scenes | ✅ | ✅ |
| **pattern_hints** | ❌ | ✅ |

## 附录 D：相关文档索引

| 文档 | 路径 | 角色 |
|---|---|---|
| 设计原则 | `.claude/plan/design-principles.md` | 7 条决策（action 命名 / params 命名 / 顶层字段移除 / 拼写约定 / Tier 分级 / 伪函数处置 / schema 边界） |
| **契约表（权威）** | `backend/app/references/core/action-params-contract.md` | Tier 1 核心 28 详写 + Tier 3 速查表 + Tier 2 占位 + 伪函数清单 + validator 规则 |
| 本计划 | `.claude/plan/cht-quality-improvement.md` | PR-1/2/3/4 实施计划（基于契约表） |

> **维护规则**：契约表是唯一权威。本计划与 `cht_system.md` / `parse_system.md` / `semantic_validator.py` / `ConfirmationView.tsx` 出现矛盾时，**全部以契约表为准**，再回头修正这些文件。
