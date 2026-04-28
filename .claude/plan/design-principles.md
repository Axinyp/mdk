# MKControl 解析层设计原则 v0

> 决策依据：基于 `core/docs/` 全部官方文档（110+ 函数）+ 真实工程代码（兴业数金 1652 行 / 401 会议室 2352 行）。
> **目标**：让 action × params 1:1 对齐中控真实函数签名，消除幻觉。

---

## 1. action 字段命名

**原则**：`action` = 中控官方函数名，全大写下划线，**1:1 映射、不发明、不归类、不简化**。


| ✅ 正确                  | ❌ 错误                        | 原因                                                     |
| ------------------------ | ------------------------------ | -------------------------------------------------------- |
| `ON_RELAY` / `OFF_RELAY` | `RELAY.On` / `RELAY.Off`       | 我自己发明的"归类"，文档无依据                           |
| `SEND_UDP`               | `Net.SendUdp` / `UDP.Send`     | 同上                                                     |
| `SEND_IRCODE`            | `IR.Send`                      | 同上                                                     |
| `SET_LOVOCURTAIN`        | `Curtain.Set` / `CURTAIN.Open` | 同上                                                     |
| (走模式库)               | `HTTP_POST` / `HTTP_GET`       | **官方根本没有此函数**，是工程师用 SEND_UDP 包装的伪函数 |

**特殊值**：`TEMPLATE` —— 批量按键模板占位（PR-3 由后端 renderer 注入代码）。

---

## 2. params 字段命名

**原则**：`params` 镜像函数完整签名，键名**严格对齐文档参数名**，包括拼写不一致。


| 函数                                | params 形态            | 注意点               |
| ----------------------------------- | ---------------------- | -------------------- |
| `ON_RELAY(dev, channel)`            | `{dev, channel}`       | —                   |
| `SEND_UDP(ip, port, str)`           | `{ip, port, str}`      | 是`str` 不是 `data`  |
| `WAKEUP_ONLAN(MAC)`                 | `{MAC}`                | **大写**             |
| `SET_LOVOCURTAIN(dev, chanel, val)` | `{dev, chanel, val}`   | 保留官方拼写`chanel` |
| `SET_VOL_M(channel, mute, vol)`     | `{channel, mute, vol}` | 无 dev               |
| `SET_MATRIX_M(out, in)`             | `{out, in}`            | 无 dev               |

---

## 3. 顶层 device/channel 字段处置

**移除**。所有参数统一走 params。

理由：

- 顶层 device/channel 只对部分函数有意义（如 ON_RELAY）
- 网络类（SEND_UDP）/ 主板独占（SET_VOL_M）/ 无参数（SOUND_PAUSE）都强制空填
- 统一走 params 后 schema 自洽，UI 按 action 动态渲染

---

## 4. 拼写约定（已与编辑器实际签名核对）

**原则**：以**编辑器签名**为准（编译器认的是这个）。文档手误才修正。

**类别 A — 文档手误，修正**：
- `SET_LOVOCURTAIN(dev, chanel, val)` → 实际 `SET_LOVOCURTAIN(dev, channel, val)`（编辑器无参数提示，但 `chanel` 是 channel 的手误）

**类别 B — 编辑器即此，保留原拼写不修正**：
- `SET_VOLTOTOL(dev, channel, val)`（不改 VOLTOTAL）
- `SET_VOLHIGHT(dev, channel, val)`（不改 VOLHIGH）
- `SOUND_SETHIGHT(dev, hightMin, gain)`（不改 SETHIGH，第二参 `hightMin` 也保留）
- `SYNC_LOVO_LITGHT_PANEL_STATE` / `GET_LOVO_LITGHT_PANEL_STATE`（LITGHT 保留）

**类别 C — 待集成测试**：
- `COMPOSE_COM` vs `SOMPOSE_COM`（文档前后不一致，测试时确认）

> 注：B 类函数为低频（生产代码两份均未使用），全部归入 Tier 2 扩展。Tier 1 核心 28 不受影响。

---

## 5. action 分级

**Tier 1 — 核心 28 个**（首批必须支持，覆盖 90% 工程）：

```
设备控制：ON_RELAY OFF_RELAY SEND_COM SEND_IRCODE SEND_LITE SEND_IO        (6)
网络：    SEND_UDP SEND_TCP WAKEUP_ONLAN SEND_M2M_DATA
          SEND_M2M_JNPUSH SEND_M2M_JNRELEASE SEND_M2M_LEVEL                (7)
触屏 UI： SET_BUTTON SET_LEVEL SEND_TEXT SEND_PAGING SEND_PICTURE          (5)
主板独占：SET_VOL_M SET_MATRIX_M                                           (2)
流程控制：SLEEP START_TIMER CANCEL_TIMER CANCEL_WAIT                       (4)
初始化：  SET_COM SET_IO_DIR                                               (2)
调试：    TRACE                                                            (1)
模板：    TEMPLATE (PR-3 用)                                               (1)
```

**Tier 2 — 扩展按需**：Lovo 三件套 / 传感器 / 美声器 / GSM / 模拟卡 / 墙上面板 / 遥控器 / ZigBee 系列。当用户描述命中关键词时启用。

**Tier 3 — 工具函数**：字符串处理（19）/ 时间获取（9）/ 参数存取（3）/ 调试（4）。**不进 action 枚举**，由 LLM 在 DEFINE_FUNCTION/事件块内自由使用。

---

## 6. 用户自定义函数 / 复杂模式

**不进 action 枚举，走 PR-2 模式库**。这一节列出从两份生产代码中抽出的全部伪函数（工程师自封装）+ 复杂代码模式，作为 PR-2 模式库的种子清单。

### 6.1 伪函数清单（工程师自封装，由原语组合而成）

> **判定规则**：以下函数**不在中控官方 docs**，是工程师在 DEFINE_FUNCTION 中自定义的。它们**不进 action 枚举**，走 PR-2 模式库（few-shot 注入 + DEFINE_FUNCTION 实现一并提供）。
> **解析阶段对策**：parse 阶段如果 LLM 把它们当 action（如 `action="HttpPost"`），semantic_validator 会标 `[warn]` 提示走模式库。

#### A. HTTP 三件套（实际是 SEND_UDP 走本地代理）

| 伪函数 | 真实签名 | 真实组成 | 来源 | 模式库片段 |
|---|---|---|---|---|
| `HttpPost` | `void HttpPost(string url, string contentType, string cookieHandle, string postData)` | 拼字符串后 `SEND_UDP(loopbackIp, httpPort, "http post " + ...)` 给本地 HTTP 代理进程 | 兴业数金 cht:138-145 | `pattern.http.post` |
| `getJsonValue` | `string getJsonValue(string jsonStr, string key)` | `STRING_EQNOCASE` + `GET_SUB_STRING` 字符级遍历，处理 `""` `{}` int 三种 value 形态 | 兴业数金 cht:153-197 | `pattern.json.get` |
| `setJsonValue` | `string setJsonValue(string jsonStr, string key, string value)` | 同上扫描 + 字符串拼接 | 兴业数金 cht:206-253 | `pattern.json.set` |

**配套基础设施**（HTTP 三件套必须打包提供，否则单独注入 HttpPost 没法跑）：
- `DEFINE_VARIABLE` 内的 `loopbackIp` `httpPort` `targetIp` `debugIp` `debugPort` 全局变量声明
- 16 个 URL 常量（兴业数金 cht:18-127）按需拷贝
- `M2MDATA_EVENT` 内的 HTTP 响应解析状态机（兴业数金 cht:1581-1650）

**触发关键词**：HTTP / REST / API / POST / GET / JSON / Webhook + 描述里出现具体 URL

#### B. Modbus / 串口协议套件

| 伪函数 | 真实签名 | 真实组成 | 来源 | 模式库片段 |
|---|---|---|---|---|
| `crc_cal` | `string crc_cal(string str)` | CRC-16 (poly 0xA001) 字节级循环；末尾追加高低字节交换的校验码 | 401会议室 cht:765-794 | `pattern.crc.modbus` |
| `Modbus_read_register` | `void Modbus_read_register(string slave_addr, string func_code, string addr, string len, int com_channel)` | 拼 `slave+func+addr+len` → `crc_cal` 加校验 → `SEND_COM(...,"0x"+rstr)` | 401会议室 cht:800-807 | `pattern.modbus.read` |
| `Get_Sensor_TEMPERATURE_HUMIDITY` | `double Get_Sensor_TEMPERATURE_HUMIDITY(string Datastring, int channel)` | `STRING_TO_BYTES` + 大端拼接 `(stob[5]<<8) + (stob[6]&255)` 后除 10.0 | 401会议室 cht:813-828 | `pattern.modbus.parse_th` |

**配套基础设施**：
- `DEFINE_VARIABLE`：`int CRC, CRC_H, CRC_L, len, i, j, tmp; byte a[0], b[1]; string str, rstr;`
- 与 `crc_cal` 配套的 DSP 音量场景（401 cht:2192-2226）也用同一套 CRC

**触发关键词**：Modbus / 485 寄存器 / 温湿度 / PM2.5 / CO2 / 传感器查询

#### C. 红外发码包装器（带 UI 状态同步）

| 伪函数 | 真实签名 | 真实组成 | 来源 | 模式库片段 |
|---|---|---|---|---|
| `send_ir` | `void send_ir(int tempture, int speed)` | `switch(speed)` × `switch(tempture)` 双层嵌套（5 风速 × 15 温度 = 75 case），每 case 内 `SEND_TEXT(tp,300,"<temp>°")` + 双 `SEND_IRCODE`（IR2 + IR3） | 401会议室 cht:126-708 | `pattern.ir.aircon` |

**为什么不是直接 SEND_IRCODE**：因为每次发码同时要 ① 更新触屏状态文本 ② 同时发往两路红外发射器（前后）③ 把当前温度持久化为变量。这个组合体值得被当作单一伪函数处理。

**配套基础设施**：
- `DEFINE_VARIABLE int air_conditioner; int fan_speed;` （温度状态变量）
- `IRCODE<"UserIRDB:KKK:KKK:KKK::<temp>">` 这种 user IR 库引用语法

**触发关键词**：空调 + 温度 / 制冷 / 制热 / 风速

#### D. 触屏状态同步包装器

| 伪函数 | 真实签名 | 真实组成 | 来源 | 模式库片段 |
|---|---|---|---|---|
| `get_date` | `void get_date()` | 9 个 system 函数（`GET_YEAR/MONTH/DATE/DAY`）+ 字符串拼接 + 7 路 `if-else if` 分支星期几 + `SEND_TEXT(tp,201,"星期X")` | 401会议室 cht:713-758 | `pattern.date.display` |

**触发关键词**：日期 / 星期 / 时钟显示 / 时间显示

### 6.2 复杂代码模式（不是函数，是代码块结构）

这些不是"伪函数"，是 BUTTON_EVENT / DEFINE_TIMER / DATA_EVENT 等代码块的**典型组织形态**，LLM 自由生成最容易出错。PR-2 模式库要把这些块作为 few-shot 例子注入 prompt。

| 模式 | 形态 | 来源 | 模式库片段 |
|---|---|---|---|
| **嵌套 WAIT 时序场景** | `BUTTON_EVENT { PUSH() { ... ON_RELAY ... WAIT 1000 { ... WAIT 1000 { ... } } SLEEP(7000); SEND_IRCODE(...); }}` 5 层嵌套 | 401会议室 cht:922-1175（4 个 scene 按键） | `pattern.scene.sequential_relay` |
| **批量等价按键群（强模板候选）** | 30 个 `BUTTON_EVENT(tp,1101..1130)` 仅温度值递增 | 401会议室 cht:1845-2143 | PR-3 `template_id=aircon_temp_buttons` |
| **预置位 ×N 摄像机** | 12 预置位按键 × 3 摄像机 = 36 等价 BUTTON_EVENT | 兴业数金 cht:894-1462 | PR-3 `template_id=camera_preset_x12` |
| **LEVEL_EVENT 拉条 + CRC 拼接** | `LEVEL_EVENT(tp,1087) { ON_EVENT() { val=LEVEL.Lvalue; ...crc_cal... SEND_COM... } }` | 401会议室 cht:2192-2226 | `pattern.level.dsp_volume` |
| **DATA_EVENT hex 状态机** | `DATA_EVENT(M_COM,1) { ONDATA() { if(BYTES_TO_HEX(DATA.Data)=="...") {...} else if(...) }` 17 路分支 | 兴业数金 cht:256-429 (handlerTimer 类似) / 兴业 cht:1581-1650 | `pattern.data.state_machine` |
| **多 join 范围分发的 BUTTON_EVENT 大块** | 单个 `BUTTON_EVENT(tp)` 不带 channel，`PUSH()` 内 `if (BUTTON.Lid >= 100 && BUTTON.Lid <= 130) { ... } else if (BUTTON.Lid == ...) { ... }` | 兴业数金 cht:614-752 | `pattern.button.range_dispatch` |
| **巡检定时器（多 IP 循环）** | `TIMER test() { for(i=0;i<8;i+=1){ SEND_UDP(ipList[i], port, msg); SLEEP(50); } }` | 兴业数金 cht:431-525 | `pattern.timer.polling` |
| **协议脚手架变量声明** | 16 个 URL 常量 + 6 个 JSON 模板字符串集中在 DEFINE_VARIABLE 顶部 | 兴业数金 cht:18-127 | `pattern.scaffold.huawei_box` |

### 6.3 伪函数与契约的边界

| 场景 | 处置 |
|---|---|
| 用户描述 "通过 UDP 发到 192.168.1.20:2000 字节串 0xAA01" | `action=SEND_UDP, params={ip,port,str}` —— 走契约表 |
| 用户描述 "通过 HTTP POST 调华为 Box 接口" | parse 输出 `action="TBD"` + `pattern_hints=["pattern.http.post","pattern.scaffold.huawei_box"]`，由 PR-2 注入 HttpPost + 16 URL 常量整套 |
| 用户描述 "读取 Modbus 寄存器获取温湿度" | parse 输出 `action="TBD"` + `pattern_hints=["pattern.crc.modbus","pattern.modbus.read","pattern.modbus.parse_th"]` |
| 用户描述 "空调温度 16-30 度按键群" | PR-3 `action="TEMPLATE", template_id="aircon_temp_buttons"`，但 `send_ir` 函数体本身仍由 PR-2 `pattern.ir.aircon` 注入到 DEFINE_FUNCTION |
| 用户描述 "空调红外发码 25 度风速 0" | `action=SEND_IRCODE` —— 单次发码走契约（如果用户已知具体 ircode 串） |
| 用户描述 "实时显示日期和星期" | `action="TBD"` + `pattern_hints=["pattern.date.display"]` + 一个 TIMER 调用 |

**关键边界**：契约表只覆盖"原子函数调用"。任何"组合调用 + 状态管理 + 多设备协调"都属于伪函数 / 复杂模式领地。

### 6.4 模式库命名规范（PR-2 设定）

```
pattern.<domain>.<specific>
```

- `pattern.http.post` / `pattern.http.get`
- `pattern.json.get` / `pattern.json.set`
- `pattern.crc.modbus`
- `pattern.modbus.read` / `pattern.modbus.parse_th`
- `pattern.ir.aircon`
- `pattern.date.display`
- `pattern.scene.sequential_relay`
- `pattern.level.dsp_volume`
- `pattern.data.state_machine`
- `pattern.button.range_dispatch`
- `pattern.timer.polling`
- `pattern.scaffold.huawei_box`

每个 pattern 文件结构（`backend/app/references/core/patterns/pro/<id>.md`）：
- frontmatter：`pattern_id` / `name` / `triggers[]` / `applies_to[]`（DEFINE_FUNCTION / DEFINE_EVENT / DEFINE_VARIABLE 等）/ `size_tokens`
- 模式说明（一句话）
- 关键技术点
- 代码模板（来自具体生产文件 + 行号引用）
- 套用方法（如何替换变量名 / join 号 / 设备名）
- 配套依赖（必须同时注入哪些 DEFINE_VARIABLE / 其他 pattern）

**注入策略**（PR-2 落地）：parse 输出 `pattern_hints[]` → cht prompt 注入命中 pattern 的代码模板 + 配套依赖（递归收集，避免缺定义）。

---

## 7. 当前 schema 表达不了的（需未来 PR-4）

- 跨函数共享的全局状态变量（`save` / `track` / `Call_number` 等）
- DATA_EVENT / LEVEL_EVENT 数据驱动事件
- BUTTON_EVENT 大块（同一 device 多 join 范围统一处理）

**当前阶段**：这些场景由 LLM 自由生成 + 模式库参考。

---

## 8. 决策记录（已确认 2026-04-28）

1. ✅ **action = 大写函数名直引**（不发明 `Net.SendUdp` 这种归类）
2. ✅ **params 键名严格对齐编辑器签名**（保留 `str` `MAC` 等原写，`chanel` 修正为 `channel`）
3. ✅ **顶层 device/channel 字段移除**（全走 params，schema 仅保留 `action + params`）
4. ✅ **拼写约定**：编辑器签名为准；文档手误才修正（详见 §4 ABC 三类）
5. ✅ **Tier 1 核心 28 个范围**确认
6. ✅ **HttpPost 类伪函数不进 action**，作为模式库片段
7. ✅ **当前 schema 不强升级**（DATA_EVENT/全局状态变量等留给 LLM + 模式库）

下一步：写完整契约表 `backend/app/references/core/action-params-contract.md`，并据此修订 `.claude/plan/cht-quality-improvement.md` 的 PR-1 章节。
