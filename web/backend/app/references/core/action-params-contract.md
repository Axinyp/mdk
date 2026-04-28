# MKControl action × params 契约表

> **依据**：`core/docs/系统函数库/`（官方）+ 兴业数金 1652 行 / 401 会议室 2352 行（真实工程）
> **配套**：`.claude/plan/design-principles.md` v0
> **范围**：Tier 1 核心 28（详写）+ Tier 3 工具函数（速查表）；Tier 2 扩展按需补
>
> **三个铁律**（生成 / 校验 / 解析三方共同遵守）：
> 1. `action` = **官方函数名直引**，全大写、不发明、不归类
> 2. `params` = **签名镜像**，键名严格对齐编辑器/文档（保留 `str` `MAC` 等原写）
> 3. **顶层无 device/channel 字段**，所有参数走 `params`
>
> **拼写约定**（详 design-principles §4）：
> - `chanel` 在 SET_LOVOCURTAIN 是文档手误，使用 `channel`
> - `VOLTOTOL` `VOLHIGHT` `SETHIGHT` `LITGHT` `hightMin` 等编辑器认这个写法，**保留**
>
> **仓库对齐点**：本表是唯一权威。出现矛盾时——
> - `app/prompts/cht_system.md` 的"Action 调用签名"表 → 以本表为准
> - `app/services/knowledge.py` 的 `ACTION_TO_FUNC` → 以本表为准
> - `app/schemas/gen.py` 的 `FunctionItem` → 以本表 §A.0 为准

---

## A. Schema 定义

### A.0 FunctionItem 结构（PR-1 后形态）

```python
class FunctionItem(BaseModel):
    name: str                      # 用户可见名（按键名）
    join_number: int = 0           # 由 join_registry 分配
    join_source: str | None = "auto"
    control_type: str = "DFCButton"
    btn_type: str | None = "NormalBtn"
    action: str                    # ★ 必填，全大写函数名（见下表）；批量时为 "TEMPLATE"
    params: dict[str, Any] = {}    # ★ 必填，签名镜像；无参函数填 {}
    image: str | None = None
    # 顶层 device/channel 字段移除——全部走 params
```

### A.1 params 通用类型约束

| 在 params 中出现 | 类型 | 校验规则 |
|---|---|---|
| `dev` | string | 必须命中 `confirmed_data.devices[*].name` |
| `channel` / `chanel` | int | ≥ 1（按键号 / 通道号） |
| `ip` | string | IPv4 字符串，如 `"192.168.1.20"` |
| `port` | int | 0 ~ 65535 |
| `MAC` | string | 12 位十六进制（无分隔符）`"4437e65b1735"` |
| `str` / `data` / `text` / `val` | string \| int | 看下列契约 |
| `out` / `in` | int | ≥ 1（矩阵通道） |
| `mute` | int | 0 / 1 |
| `vol` | int | 见各函数说明 |

### A.2 缺参时的处置

LLM 解析阶段无法从用户描述中提取出某 `params` 必填项时——

- 不要瞎编占位值
- 将该 function 暂记 `action="TBD"`，并在 `parsed.missing_info` 追加一条：`"功能 <name>: 缺少 <param> 参数"`
- 由用户在 confirm 阶段补全

---

## B. Tier 1 核心 28（详写）

### 设备控制（6）

#### B.1 `ON_RELAY`
- **官方签名**：`void ON_RELAY(String dev, int channel)`
- **功能**：打开继电器
- **类**：继电器控制
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `dev` | string | ✓ | 继电器设备名（已在 DEFINE_DEVICE 声明） |
| `channel` | int | ✓ | 通道号，从 1 开始 |

- **JSON**：
  ```json
  {"action":"ON_RELAY","params":{"dev":"RELAY_M","channel":2}}
  ```
- **生成 cht**：`ON_RELAY(RELAY_M, 2);`
- **触发关键词**：开 + (灯/继电器/Power/电源/插座/RELAY)

---

#### B.2 `OFF_RELAY`
- **官方签名**：`void OFF_RELAY(String dev, int channel)`
- **功能**：关闭继电器
- **类**：继电器控制
- **params**：同 ON_RELAY
- **JSON**：
  ```json
  {"action":"OFF_RELAY","params":{"dev":"RELAY_M","channel":2}}
  ```
- **生成 cht**：`OFF_RELAY(RELAY_M, 2);`
- **触发关键词**：关 + (灯/继电器/Power/电源/插座/RELAY)

---

#### B.3 `SEND_COM`
- **官方签名**：`void SEND_COM(String dev, int channel, String str)`
- **功能**：串口数据发送（支持透传 / 16 进制 / 混合三种格式）
- **类**：串口控制
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `dev` | string | ✓ | 串口设备名 |
| `channel` | int | ✓ | 串口通道号 |
| `str` | string | ✓ | 待发数据。`0x` 开头将作 16 进制解析（如 `"0x3132"` 实发 `"12"`） |

- **JSON**：
  ```json
  {"action":"SEND_COM","params":{"dev":"Com_m","channel":1,"str":"0x424c01910001"}}
  ```
- **生成 cht**：`SEND_COM(Com_m, 1, "0x424c01910001");`
- **触发关键词**：串口 / RS232 / RS485 / 协议下发 / 投影机 / 投影仪 / 矩阵切换串口
- **注**：纯 hex 数据混合时 LLM 应输出 `COMPOSE_COM` 模式（属 PR-2 模式库）

---

#### B.4 `SEND_IRCODE`
- **官方签名**：`void SEND_IRCODE(String dev, int channel, String str)`
- **功能**：发送红外数据（HEX 字符串或标准库引用）
- **类**：红外控制
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `dev` | string | ✓ | 红外设备名 |
| `channel` | int | ✓ | 红外通道号 |
| `str` | string | ✓ | 红外码：HEX 字符串 或 `IRCODE<"StanderIRDb:..."> ` 形式 |

- **JSON**：
  ```json
  {"action":"SEND_IRCODE","params":{"dev":"IR_M","channel":1,"str":"IRCODE<\"StanderIRDb:3M:CODEC:VCS3000:POLYCOM1:6289:6 (MNO)\">"}}
  ```
- **生成 cht**：`SEND_IRCODE(IR_M, 1, IRCODE<"StanderIRDb:3M:CODEC:VCS3000:POLYCOM1:6289:6 (MNO)">);`
- **触发关键词**：红外 / IR / 遥控 / 学习 / 空调红外 / 电视

---

#### B.5 `SEND_LITE`
- **官方签名**：`void SEND_LITE(String dev, int channel, int val)`
- **功能**：控制调光器灯光
- **类**：调光器控制
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `dev` | string | ✓ | 灯光设备名 |
| `channel` | int | ✓ | 通道号 |
| `val` | int | ✓ | 模拟量，**0 ~ 65535**（不是 0~100） |

- **JSON**：
  ```json
  {"action":"SEND_LITE","params":{"dev":"lite_n","channel":1,"val":65535}}
  ```
- **生成 cht**：`SEND_LITE(lite_n, 1, 65535);`
- **触发关键词**：调光 / 亮度 / 灯光强度 / 灯带

---

#### B.6 `SEND_IO`
- **官方签名**：`void SEND_IO(String dev, int channel, int vol)`
- **功能**：控制 IO 口输出电平
- **类**：IO 控制
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `dev` | string | ✓ | IO 设备名 |
| `channel` | int | ✓ | 通道号 |
| `vol` | int | ✓ | `1`=高电平，`0`=低电平 |

- **JSON**：
  ```json
  {"action":"SEND_IO","params":{"dev":"Io_m","channel":1,"vol":0}}
  ```
- **生成 cht**：`SEND_IO(Io_m, 1, 0);`
- **触发关键词**：IO 输出 / 触发 / 开关量
- **⚠ 警告**：函数名是 `SEND_IO` 而不是 `SET_IO`（文档标题写错了，签名才是真）

---

### 网络（7）

#### B.7 `SEND_TCP`
- **官方签名**：`void SEND_TCP(String ip, int port, String str)`
- **功能**：以 TCP 方式向主机发送数据
- **类**：网络控制
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `ip` | string | ✓ | 主机 IP |
| `port` | int | ✓ | 端口号 |
| `str` | string | ✓ | 数据串（同 SEND_COM 格式规则） |

- **JSON**：
  ```json
  {"action":"SEND_TCP","params":{"ip":"192.168.1.20","port":2000,"str":"0123456789"}}
  ```
- **生成 cht**：`SEND_TCP("192.168.1.20", 2000, "0123456789");`
- **触发关键词**：TCP / 长连接 + IP/端口
- **⚠ 重要**：3 参数，**不要传 dev/channel**

---

#### B.8 `SEND_UDP`
- **官方签名**：`void SEND_UDP(String ip, int port, String str)`
- **功能**：以 UDP 方式向主机发送数据
- **类**：网络控制
- **params**：同 SEND_TCP（`ip`/`port`/`str`）
- **JSON**：
  ```json
  {"action":"SEND_UDP","params":{"ip":"172.16.58.211","port":54433,"str":"0x424c01910001"}}
  ```
- **生成 cht**：`SEND_UDP("172.16.58.211", 54433, "0x424c01910001");`
- **触发关键词**：UDP / 网络命令 / 中央控制器 + IP/端口
- **⚠ 重要**：3 参数。本条目专门解决"LLM 凭空塞 5 参 device/channel"幻觉

---

#### B.9 `WAKEUP_ONLAN`
- **官方签名**：`void WAKEUP_ONLAN(String MAC)`
- **功能**：通过局域网唤醒电脑
- **类**：网络控制
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `MAC` | string | ✓ | 12 位十六进制，**无分隔符**，如 `"4437e65b1735"` |

- **JSON**：
  ```json
  {"action":"WAKEUP_ONLAN","params":{"MAC":"4437e65b1735"}}
  ```
- **生成 cht**：`WAKEUP_ONLAN("4437e65b1735");`
- **触发关键词**：网络唤醒 / 远程开机 / WOL / Wake on LAN
- **⚠ 重要**：键名是 **大写 `MAC`**，不是 `mac`

---

#### B.10 `SEND_M2M_DATA`
- **官方签名**：`void SEND_M2M_DATA(String ip, String data)`
- **功能**：向其他主机发送数据（级联工程）
- **类**：网络控制
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `ip` | string | ✓ | 目标主机 IP |
| `data` | string | ✓ | 数据串（注意键名是 `data` 不是 `str`） |

- **JSON**：
  ```json
  {"action":"SEND_M2M_DATA","params":{"ip":"192.168.1.30","data":"123456789"}}
  ```
- **生成 cht**：`SEND_M2M_DATA("192.168.1.30", "123456789");`
- **触发关键词**：级联 / 主机间通信 / M2M

---

#### B.11 `SEND_M2M_JNPUSH`
- **官方签名**：`void SEND_M2M_JNPUSH(String ip, int jNumber)`
- **功能**：向其他主机推送 join number 按下事件
- **类**：网络控制
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `ip` | string | ✓ | 目标主机 IP |
| `jNumber` | int | ✓ | 远端 join number |

- **JSON**：
  ```json
  {"action":"SEND_M2M_JNPUSH","params":{"ip":"192.168.1.30","jNumber":1}}
  ```
- **生成 cht**：`SEND_M2M_JNPUSH("192.168.1.30", 1);`
- **触发关键词**：级联按键 / 跨主机触发

---

#### B.12 `SEND_M2M_JNRELEASE`
- **官方签名**：`void SEND_M2M_JNRELEASE(String ip, int jNumber)`
- **功能**：向其他主机推送 join number 弹起事件
- **类**：网络控制
- **params**：同 SEND_M2M_JNPUSH
- **JSON**：
  ```json
  {"action":"SEND_M2M_JNRELEASE","params":{"ip":"192.168.1.30","jNumber":1}}
  ```
- **生成 cht**：`SEND_M2M_JNRELEASE("192.168.1.30", 1);`
- **触发关键词**：级联按键弹起

---

#### B.13 `SEND_M2M_LEVEL`
- **官方签名**：`void SEND_M2M_LEVEL(String ip, int jNumber, int val)`
- **功能**：向其他主机推送拉条值
- **类**：网络控制
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `ip` | string | ✓ | 目标主机 IP |
| `jNumber` | int | ✓ | 远端 join number |
| `val` | int | ✓ | 拉条值 |

- **JSON**：
  ```json
  {"action":"SEND_M2M_LEVEL","params":{"ip":"192.168.1.30","jNumber":1,"val":255}}
  ```
- **生成 cht**：`SEND_M2M_LEVEL("192.168.1.30", 1, 255);`
- **触发关键词**：级联拉条 / 跨主机滑块

---

### 触屏 UI（5）

#### B.14 `SET_BUTTON`
- **官方签名**：`void SET_BUTTON(String dev, int channel, int state)`
- **功能**：设置按钮状态（按下 / 弹起的视觉态）
- **类**：触屏控制
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `dev` | string | ✓ | 触屏设备名 |
| `channel` | int | ✓ | 按钮 join number |
| `state` | int | ✓ | `1`=按下，`0`=弹起 |

- **JSON**：
  ```json
  {"action":"SET_BUTTON","params":{"dev":"tp","channel":1,"state":1}}
  ```
- **生成 cht**：`SET_BUTTON(tp, 1, 1);`
- **触发关键词**：按钮高亮 / 按钮反馈 / 选中状态

---

#### B.15 `SET_LEVEL`
- **官方签名**：`void SET_LEVEL(String dev, int channel, int val)`
- **功能**：设置拉条值（屏幕上显示）
- **类**：触屏控制
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `dev` | string | ✓ | 触屏设备名 |
| `channel` | int | ✓ | 拉条 join number |
| `val` | int | ✓ | 拉条值，**0 ~ 65535** |

- **JSON**：
  ```json
  {"action":"SET_LEVEL","params":{"dev":"tp","channel":1,"val":255}}
  ```
- **生成 cht**：`SET_LEVEL(tp, 1, 255);`
- **触发关键词**：拉条显示 / 进度条 / 滑块回显

---

#### B.16 `SEND_TEXT`
- **官方签名**：`void SEND_TEXT(String dev, int channel, String text)`
- **功能**：向触屏发送文本
- **类**：触屏控制
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `dev` | string | ✓ | 触屏设备名 |
| `channel` | int | ✓ | 文本框 join number |
| `text` | string | ✓ | 文本内容（注意键名是 `text` 不是 `str`） |

- **JSON**：
  ```json
  {"action":"SEND_TEXT","params":{"dev":"tp","channel":1,"text":"Hello"}}
  ```
- **生成 cht**：`SEND_TEXT(tp, 1, "Hello");`
- **触发关键词**：文本显示 / 标签更新 / 状态文字

---

#### B.17 `SEND_PAGING`
- **官方签名**：`void SEND_PAGING(String dev, int channel, String text)`
- **功能**：触摸屏跳页
- **类**：触屏控制
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `dev` | string | ✓ | 触屏设备名 |
| `channel` | int | ✓ | 通常填 `1` |
| `text` | string | ✓ | 目标页面名（与 XML 中 `Page.name` 一致） |

- **JSON**：
  ```json
  {"action":"SEND_PAGING","params":{"dev":"tp","channel":1,"text":"矩阵控制"}}
  ```
- **生成 cht**：`SEND_PAGING(tp, 1, "矩阵控制");`
- **触发关键词**：跳页 / 翻页 / 进入页面 / 返回首页

---

#### B.18 `SEND_PICTURE`
- **签名（编辑器/工程实测）**：`void SEND_PICTURE(String dev, int channel, int picIndex)`
- **功能**：切换按钮 / 控件的图片帧（对 DFCPicture 控件）
- **类**：触屏控制
- **来源**：官方 docs **未列**，工程代码（401 会议室 cht:1270/1296）确认存在
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `dev` | string | ✓ | 触屏设备名 |
| `channel` | int | ✓ | 控件 join number |
| `picIndex` | int | ✓ | 图片索引（从 1 起） |

- **JSON**：
  ```json
  {"action":"SEND_PICTURE","params":{"dev":"tp","channel":150,"picIndex":1}}
  ```
- **生成 cht**：`SEND_PICTURE(tp, 150, 1);`
- **触发关键词**：图片切换 / 状态图 / 帧切换 / 多态图标

---

### 主板独占（2）

#### B.19 `SET_VOL_M`
- **官方签名**：`void SET_VOL_M(int channel, int mute, int vol)`
- **功能**：设置主板 DSP 输入通道音量 + 静音
- **类**：DSP 音量
- **params**：**无 dev**

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `channel` | int | ✓ | DSP 通道号 |
| `mute` | int | ✓ | `1`=静音，`0`=非静音 |
| `vol` | int | ✓ | 音量 dB 值，范围 [-60, 6] |

- **JSON**：
  ```json
  {"action":"SET_VOL_M","params":{"channel":1,"mute":1,"vol":-30}}
  ```
- **生成 cht**：`SET_VOL_M(1, 1, -30);`
- **触发关键词**：DSP / 主板音量 / 麦克音量
- **⚠ 重要**：3 参数，**没有 dev**

---

#### B.20 `SET_MATRIX_M`
- **官方签名**：`void SET_MATRIX_M(int out, int in)`
- **功能**：切换主板矩阵
- **类**：矩阵控制
- **params**：**无 dev**

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `out` | int | ✓ | 输出通道 |
| `in` | int | ✓ | 输入通道 |

- **JSON**：
  ```json
  {"action":"SET_MATRIX_M","params":{"out":1,"in":3}}
  ```
- **生成 cht**：`SET_MATRIX_M(1, 3);`
- **触发关键词**：矩阵切换 / 视频矩阵 / 信号源选择
- **⚠ 重要**：2 参数，**没有 dev**

---

### 流程控制（4）

#### B.21 `SLEEP`
- **官方签名**：`void SLEEP(int time)`
- **功能**：让主线程休眠（**会阻塞**，慎用；优先 WAIT）
- **类**：TIMER/WAIT
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `time` | int | ✓ | 毫秒 |

- **JSON**：
  ```json
  {"action":"SLEEP","params":{"time":1000}}
  ```
- **生成 cht**：`SLEEP(1000);`
- **触发关键词**：等待 / 延时（短时序，且不要求并行响应）

---

#### B.22 `START_TIMER`
- **官方签名（基础版）**：`void START_TIMER(String name, int time)`
- **官方签名（定时启动版）**：`void START_TIMER(String name, int time, int year, int mouth, int day, int hh, int minute, int second)`
- **功能**：启动周期性定时器（与 DEFINE_TIMER 中的 TIMER 函数搭配）
- **类**：TIMER/WAIT
- **params（基础版）**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `name` | string | ✓ | TIMER 函数名（**不带引号**，是函数引用） |
| `time` | int | ✓ | 间隔毫秒 |

- **JSON（基础）**：
  ```json
  {"action":"START_TIMER","params":{"name":"testTimer","time":1000}}
  ```
- **生成 cht**：`START_TIMER(testTimer, 1000);`
- **JSON（定时启动）**：
  ```json
  {"action":"START_TIMER","params":{"name":"testTimer","time":86400000,"year":2010,"mouth":10,"day":26,"hh":14,"minute":0,"second":0}}
  ```
- **生成 cht**：`START_TIMER(testTimer, 86400000, 2010, 10, 26, 14, 0, 0);`
- **触发关键词**：定时执行 / 周期任务 / 心跳 / 轮询
- **⚠ 拼写**：`mouth`（编辑器文档原写，**勿改 month**）

---

#### B.23 `CANCEL_TIMER`
- **官方签名**：`void CANCEL_TIMER(String name)`
- **功能**：取消定时器
- **类**：TIMER/WAIT
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `name` | string | ✓ | TIMER 函数名（**带引号**：调用时是字符串） |

- **JSON**：
  ```json
  {"action":"CANCEL_TIMER","params":{"name":"testTimer"}}
  ```
- **生成 cht**：`CANCEL_TIMER("testTimer");`
- **触发关键词**：取消定时 / 停止心跳 / 关闭轮询
- **⚠ 注意**：CANCEL_TIMER 第一参 **加引号**，START_TIMER 第一参 **不加引号**——这是中控的奇葩规则

---

#### B.24 `CANCEL_WAIT`
- **官方签名**：`void CANCEL_WAIT(string name)`
- **功能**：取消有名 WAIT 语句块
- **类**：TIMER/WAIT
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `name` | string | ✓ | WAIT 块名 |

- **JSON**：
  ```json
  {"action":"CANCEL_WAIT","params":{"name":"ty"}}
  ```
- **生成 cht**：`CANCEL_WAIT("ty");`
- **触发关键词**：取消等待 / 中断时序

---

### 初始化（2）

#### B.25 `SET_COM`
- **官方签名**：`void SET_COM(String dev, int channel, long sband, int databit, int jo, int stopbit, int dataStream, int comType)`
- **功能**：配置 COM 口（**每个 COM 设备必须在 DEFINE_START 调用一次**）
- **类**：串口控制
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `dev` | string | ✓ | COM 设备名 |
| `channel` | int | ✓ | COM 通道号 |
| `sband` | int | ✓ | 波特率（9600 / 115200 …） |
| `databit` | int | ✓ | 数据位 1~8（典型 8） |
| `jo` | int | ✓ | 奇偶位：0 无 / 1 奇 / 2 偶 / 3 标记 / 4 空格 |
| `stopbit` | int | ✓ | 停止位：10=1，15=1.5，20=2 |
| `dataStream` | int | ✓ | 数据流：0 无 / 1 xon-xoff / 2 硬件 |
| `comType` | int | ✓ | 通信方式：232 / 485 / 422（其他默认 232） |

- **JSON**：
  ```json
  {"action":"SET_COM","params":{"dev":"Com_m","channel":1,"sband":9600,"databit":8,"jo":0,"stopbit":10,"dataStream":0,"comType":232}}
  ```
- **生成 cht**：`SET_COM(Com_m, 1, 9600, 8, 0, 10, 0, 232);`
- **触发关键词**：串口初始化 / 波特率 / 9600 / 115200
- **⚠ 强制**：cht_system.md 已规定"每个 COM 设备必须有 SET_COM 初始化"

---

#### B.26 `SET_IO_DIR`
- **官方签名**：`void SET_IO_DIR(String dev, int channel, int dir, int pullordown)`
- **功能**：设置 IO 方向（输入 / 输出 + 上下拉）
- **类**：IO 控制
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `dev` | string | ✓ | IO 设备名 |
| `channel` | int | ✓ | 通道号 |
| `dir` | int | ✓ | `0`=输出，`1`=输入 |
| `pullordown` | int | ✓ | `0`=下拉，`1`=上拉 |

- **JSON**：
  ```json
  {"action":"SET_IO_DIR","params":{"dev":"Io_m","channel":1,"dir":0,"pullordown":0}}
  ```
- **生成 cht**：`SET_IO_DIR(Io_m, 1, 0, 0);`
- **触发关键词**：IO 方向 / IO 配置 / 输入输出
- **建议**：`SET_IO_DIR` 通常出现在 DEFINE_START

---

### 调试（1）

#### B.27 `TRACE`
- **官方签名**：`void TRACE(String msg)`
- **功能**：打印调试信息
- **类**：其他
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `msg` | string | ✓ | 调试文本（可包含 `\n`） |

- **JSON**：
  ```json
  {"action":"TRACE","params":{"msg":"This is my program!"}}
  ```
- **生成 cht**：`TRACE("This is my program!");`
- **触发关键词**：日志 / 打印 / debug / 调试输出

---

### 模板（1）

#### B.28 `TEMPLATE`
- **签名**：**无**——是占位符，由 PR-3 后端 renderer 注入实际代码
- **功能**：批量按键的模板引用（避免 LLM 重复生成 30~50 个雷同 BUTTON_EVENT）
- **来源**：本系统约定（非中控官方），由 join_registry + renderer 协作展开
- **params**：

| 键 | 类型 | 必填 | 说明 |
|---|---|:-:|---|
| `template_id` | string | ✓ | 模式库注册名，如 `"aircon_temp_button"` |
| `count` | int | ✓ | 重复次数（如 30 个温度按钮） |
| `start_join` | int | ✓ | 起始 join number |
| `vars` | object |   | 模板需要的额外变量字典（按模板要求） |

- **JSON 示例**（401 会议室 30 温度按钮）：
  ```json
  {"action":"TEMPLATE","params":{
    "template_id":"aircon_temp_button",
    "count":30,
    "start_join":1101,
    "vars":{"dev":"tp","com_dev":"AIRCON_COM","temp_base":16}
  }}
  ```
- **生成**：renderer 展开为 30 个 `BUTTON_EVENT(tp, 1101..1130) { PUSH() { send_ir(...,16+i); } }`
- **触发关键词**：批量按键 / 矩阵按钮 / 温度档位 / 预设位 / 拨号键盘
- **⚠ 注意**：解析阶段如未识别为模板，仍会展开为多个独立 FunctionItem——TEMPLATE 是优化路径，不是必需路径

---

## C. Tier 3 工具函数速查表（不进 action 枚举）

> 以下函数**不进 action 枚举**——它们在 `DEFINE_FUNCTION` / `BUTTON_EVENT` 等代码块**内部**由 LLM 自由使用（作为表达式、循环体、状态机的一部分）。
> Renderer 不直接生成这些调用；LLM 决定何时使用。

### C.1 字符串 / 字节数组（19）

| 函数 | 签名 | 用途速记 |
|---|---|---|
| `BYTES_TO_STRING` | `String BYTES_TO_STRING(byte[] bb)` | 字节→字符串 |
| `STRING_TO_BYTES` | `byte[] STRING_TO_BYTES(string str)` | 字符串→字节 |
| `STRING_EQ` | `boolean STRING_EQ(String src, String des)` | 严格相等（区分大小写） |
| `STRING_EQNOCASE` | `boolean STRING_EQNOCASE(String src, String des)` | 忽略大小写相等 |
| `STRING_STARTWITH` | `boolean STRING_STARTWITH(String s1, String s2)` | s2 是否以 s1 开头 |
| `STRING_ENDWITH` | `boolean STRING_ENDWITH(String s1, String s2)` | s2 是否以 s1 结尾 |
| `ATOI` | `int ATOI(String a)` | 字符串→int |
| `ITOA` | `String ITOA(int i)` | int→字符串 |
| `BYTES_ADD` | `byte[] BYTES_ADD(byte[] first, byte[] second)` | 字节数组拼接 |
| `GET_BYTES_LENGTH` | `int GET_BYTES_LENGTH(byte[] bsrc)` | 字节数组长度 |
| `BYTES_TO_HEX` | `String BYTES_TO_HEX(byte[] bb)` | 字节→16 进制串 |
| `HEX_TO_BYTES` | `byte[] HEX_TO_BYTES(String s)` | 16 进制串→字节 |
| `INT_TO_DOUBLE` | `double INT_TO_DOUBLE(int i)` | int→double |
| `DOUBLE_TO_INT` | `int DOUBLE_TO_INT(double i)` | double→int |
| `STRING_TO_DOUBLE` | `double STRING_TO_DOUBLE(string s)` | 字符串→double |
| `DOUBLE_TO_STRING` | `String DOUBLE_TO_STRING(double i)` | double→字符串 |
| `GET_SUB_STRING` | `String GET_SUB_STRING(String src, int beginIndex[, int endIndex])` | 子串截取 |
| `BYTES_TO_INT` | `int BYTES_TO_INT(byte[] b)` | 字节→int（大端，前 4 位） |
| `INT_TO_HEX` | `String INT_TO_HEX(int i)` | int→16 进制串 |

**典型场景**：
- `DATA_EVENT` 内对收到的字节流做协议解析（401 会议室 cht:765-807 Modbus）
- HTTP 响应 JSON 字符串切片（兴业数金 cht:1581-1650）
- CRC 计算填充入串口指令

---

### C.2 时间（9）

| 函数 | 签名 | 返回 |
|---|---|---|
| `GET_YEAR` | `int GET_YEAR()` | 年（如 2026） |
| `GET_MONTH` | `int GET_MONTH()` | 月 1~12 |
| `GET_DATE` | `int GET_DATE()` | 日 1~31 |
| `GET_HOUR_OF_DAY` | `int GET_HOUR_OF_DAY()` | 时 0~23 |
| `GET_MINUTE` | `int GET_MINUTE()` | 分 0~59 |
| `GET_SECOND` | `int GET_SECOND()` | 秒 0~59 |
| `GET_DAY` | `int GET_DAY()` | 星期几（0=周日，1=周一 … ） |
| `GET_DAY_OF_WEEK` | `int GET_DAY_OF_WEEK()` | 第几周 |
| `GET_NETTIME` | `void GET_NETTIME()` | 网络时间同步 |

**典型场景**：定时器内判断工作日 / 上下班时段；DEFINE_TIMER 周期性调用 GET_NETTIME。

---

### C.3 参数存取（3）

| 函数 | 签名 | 用途 |
|---|---|---|
| `SAVE_PARAM` | `void SAVE_PARAM(String name, <T> param)` | 持久化变量（断电不丢） |
| `LOAD_PARAM` | `<T> LOAD_PARAM(String name, <T> param)` | 读取持久化变量 |
| `DEL_ALL_PARAM` | `void DEL_ALL_PARAM()` | 清除所有 |

**支持类型**：int / double / string / int[] / double[] / string[]
**典型场景**：场景偏好记忆 / 上次音量 / 用户设置；DEFINE_START 处用 LOAD_PARAM 恢复状态。

---

### C.4 调试与杂项（4）

| 函数 | 签名 | 用途 |
|---|---|---|
| `TRACE` | `void TRACE(String msg)` | 调试打印（已在 Tier 1） |
| `RANDOM_NUMBER` | `int RANDOM_NUMBER(int n)` | 0~n 随机数 |
| `GET_VER_INFO` | `String GET_VER_INFO()` | 获取 AllInOne 固件版本 |
| `RESET_BYTE` | `void RESET_BYTE(byte[] arr)` | 字节数组清零（DATA_EVENT 缓冲常用） |

> `RESET_BYTE` 文档未单列，但 `BYTES_ADD` 示例中标准用法。

---

## D. Tier 2 扩展函数（按需补，**不写 params 详情**）

仅列函数名供未来 PR 增补；触发条件命中时再补完整契约。

| 类别 | 函数 |
|---|---|
| Lovo 灯光 | `OPEN_LOVOLIGHT` `CLOSE_LOVOLIGHT` `SYNC_LOVO_LITGHT_PANEL_STATE` `GET_LOVO_LITGHT_PANEL_STATE` |
| Lovo 窗帘 | `SET_LOVOCURTAIN(dev, channel, val)` `OPEN_LOVOCURTAIN` `CLOSE_LOVOCURTAIN` `STOP_LOVOCURTAIN` |
| Lovo 投影幕 | `SET_LOVOSCREEN` |
| 美声器 | `SET_VOLTOTOL` `SET_VOLHIGHT` |
| 声音控制器 | `SOUND_PLAY` `SOUND_PAUSE` `SOUND_SETHIGHT` `SOUND_SETLOW` |
| GSM | `GSM_SEND_MSG` `GSM_DIAL` `GSM_HANGUP` |
| 模拟卡 | `READ_AD` `WRITE_DA` |
| 墙上面板 | `SET_PANEL_LED` `READ_PANEL_KEY` |
| 遥控器 | `READ_REMOTE` |
| ZigBee | `Z_SEND_LITE` `Z_SEND_WMLITE` `Z_QUERY_LITE` `Z_READ_WM` |
| 传感器 | `READ_SENSOR` |
| DMX512 | `SEND_DMX` |
| DSP 输出 | `GET_VOL_OUT` `SET_VOL_OUT` `GET_MUTE_OUT` `SET_MUTE_OUT` |
| 矩阵查询 | `GET_MATRIX_M` |
| 继电器查询 | `QUERY_RELAY` |
| 串口辅助 | `COMPOSE_COM` / `SOMPOSE_COM`（拼写待集成测试确认） |

---

## E. 已知伪函数（**不进 action**，走模式库 PR-2）

工程师常自封装这些函数，**它们不是中控原语**，由代码模式片段提供。
**完整定义**详见 `.claude/plan/design-principles.md` §6.1（含真实签名、来源行号、配套依赖）。

| 伪函数 | 真实签名（按生产代码） | 真实组成 | 来源 | 模式库片段 |
|---|---|---|---|---|
| `HttpPost` | `void HttpPost(string url, string contentType, string cookieHandle, string postData)` | `SEND_UDP(loopbackIp, httpPort, "http post " + ...)` 给本地 HTTP 代理 | 兴业数金 cht:138-145 | `pattern.http.post` |
| `getJsonValue` | `string getJsonValue(string jsonStr, string key)` | `STRING_EQNOCASE` + `GET_SUB_STRING` 字符级遍历，处理 `""` `{}` int 三种 value | 兴业数金 cht:153-197 | `pattern.json.get` |
| `setJsonValue` | `string setJsonValue(string jsonStr, string key, string value)` | 同上扫描 + 字符串拼接 | 兴业数金 cht:206-253 | `pattern.json.set` |
| `crc_cal` | `string crc_cal(string str)` | CRC-16 (poly 0xA001) 字节级循环；末尾追加高低字节交换的校验码 | 401会议室 cht:765-794 | `pattern.crc.modbus` |
| `Modbus_read_register` | `void Modbus_read_register(string slave_addr, string func_code, string addr, string len, int com_channel)` | 拼 slave+func+addr+len → crc_cal → SEND_COM | 401会议室 cht:800-807 | `pattern.modbus.read` |
| `Get_Sensor_TEMPERATURE_HUMIDITY` | `double Get_Sensor_TEMPERATURE_HUMIDITY(string Datastring, int channel)` | 字节大端拼接 `(stob[5]<<8)+(stob[6]&255)` 后除 10.0 | 401会议室 cht:813-828 | `pattern.modbus.parse_th` |
| `send_ir` | `void send_ir(int tempture, int speed)` | 双层 `switch(speed) × switch(tempture)`（5×15=75 case），每 case 内 SEND_TEXT + 双路 SEND_IRCODE | 401会议室 cht:126-708 | `pattern.ir.aircon` |
| `get_date` | `void get_date()` | `GET_YEAR/MONTH/DATE/DAY` + 字符串拼接 + 7 路 if-else if 星期分支 + SEND_TEXT | 401会议室 cht:713-758 | `pattern.date.display` |

**关键警示**：
- `HttpPost` **不是真 HTTP**——是发 UDP 给本地代理进程。单独注入 HttpPost **没法跑**，必须打包：①`loopbackIp/httpPort/targetIp/debugIp/debugPort` 5 个全局变量；②按需 16 个 URL 常量；③M2MDATA_EVENT 响应解析状态机（兴业数金 cht:1581-1650）。详见 design-principles §6.1.A。
- `send_ir` **不是单纯 SEND_IRCODE 包装**——同步要更新触屏温度文本（SEND_TEXT(tp,300,...)）+ 双路红外发射器（IR2 + IR3），把这种"组合体"当伪函数处理才合理。
- `crc_cal` 共用变量（CRC/CRC_H/CRC_L/len/i/j/tmp/a/b/str/rstr）必须在 DEFINE_VARIABLE 中先声明。

**生成策略**：LLM 在 cht 中**直接调用**这些伪函数名，由 PR-2 在 prompt 中追加对应模式库片段（包含 `DEFINE_FUNCTION` 完整实现 + `DEFINE_VARIABLE` 状态变量 + 任何配套基础设施）。

**parse 阶段对策**：semantic_validator 检测到 LLM 把这些名字写成 `action="HttpPost"` 时——
- 不阻断流水线（`[warn]` 级）
- 在 `missing_info` 追加：`"功能 <name>: '<name>' 是伪函数，请改为 action=TBD 并在 pattern_hints[] 中标记 <pattern_id>"`

---

## F. 校验器规则（PR-1 后 validator 增量）

```python
# semantic_validator.py 新增检查
ACTION_PARAMS_CONTRACT = {
    "ON_RELAY":  {"required": ["dev", "channel"], "types": {"dev": str, "channel": int}},
    "OFF_RELAY": {"required": ["dev", "channel"], "types": {"dev": str, "channel": int}},
    "SEND_COM":  {"required": ["dev", "channel", "str"]},
    "SEND_IRCODE": {"required": ["dev", "channel", "str"]},
    "SEND_LITE": {"required": ["dev", "channel", "val"]},
    "SEND_IO":   {"required": ["dev", "channel", "vol"]},
    "SEND_TCP":  {"required": ["ip", "port", "str"], "forbidden": ["dev", "channel"]},
    "SEND_UDP":  {"required": ["ip", "port", "str"], "forbidden": ["dev", "channel"]},
    "WAKEUP_ONLAN":     {"required": ["MAC"]},
    "SEND_M2M_DATA":    {"required": ["ip", "data"]},
    "SEND_M2M_JNPUSH":  {"required": ["ip", "jNumber"]},
    "SEND_M2M_JNRELEASE": {"required": ["ip", "jNumber"]},
    "SEND_M2M_LEVEL":   {"required": ["ip", "jNumber", "val"]},
    "SET_BUTTON":  {"required": ["dev", "channel", "state"]},
    "SET_LEVEL":   {"required": ["dev", "channel", "val"]},
    "SEND_TEXT":   {"required": ["dev", "channel", "text"]},
    "SEND_PAGING": {"required": ["dev", "channel", "text"]},
    "SEND_PICTURE": {"required": ["dev", "channel", "picIndex"]},
    "SET_VOL_M":   {"required": ["channel", "mute", "vol"], "forbidden": ["dev"]},
    "SET_MATRIX_M": {"required": ["out", "in"], "forbidden": ["dev"]},
    "SLEEP":       {"required": ["time"]},
    "START_TIMER": {"required": ["name", "time"]},
    "CANCEL_TIMER": {"required": ["name"]},
    "CANCEL_WAIT":  {"required": ["name"]},
    "SET_COM": {"required": ["dev","channel","sband","databit","jo","stopbit","dataStream","comType"]},
    "SET_IO_DIR": {"required": ["dev","channel","dir","pullordown"]},
    "TRACE":   {"required": ["msg"]},
    "TEMPLATE": {"required": ["template_id", "count", "start_join"]},
}
```

**校验逻辑**：
1. `action` 不在 `ACTION_PARAMS_CONTRACT` 中 → Tier 2/未知，仅 warning
2. 缺少 `required` 键 → critical："缺参数 X"
3. 出现 `forbidden` 键 → critical："SEND_UDP 不接受 device 参数（你写的是网络函数）"
4. 类型不匹配（typings） → critical
5. `dev` 引用必须存在于 `confirmed.devices[*].name` → critical

---

## G. 修订历史

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-04-28 | v0.1 | 首版。Tier 1 核心 28 + Tier 3 速查表 + Tier 2 函数清单 + 伪函数清单 + validator 契约 |
| 2026-04-28 | v0.2 | §E 伪函数清单按生产代码核实签名：HttpPost 改为 4 参数 `(url, contentType, cookieHandle, postData)`；HttpGet 删除（生产中不存在）；新增 Modbus_read_register / Get_Sensor_TEMPERATURE_HUMIDITY / get_date；标注 HttpPost 非真 HTTP（实为 SEND_UDP 给本地代理）+ send_ir 强绑定 UI 状态同步。与 design-principles §6.1 对齐。 |
