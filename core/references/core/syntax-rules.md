# MKControl Creator 语言语法约束

> 生成代码时必须遵守的语法规则

## 代码块结构

```
DEFINE_DEVICE    → 设备定义
DEFINE_COMBINE   → 设备组合（可选）
DEFINE_CONSTANT  → ★★★ 只允许整型常量 ★★★
DEFINE_VARIABLE  → 变量定义（必须赋初值）
DEFINE_FUNCTION  → 自定义函数
DEFINE_START     → 启动初始化
DEFINE_EVENT     → 事件处理
```

---

## DEFINE_CONSTANT - 常量块

### ⚠️ 约束：只允许整型

```creator
// ✅ 正确
DEFINE_CONSTANT
    CH_PJ = 1;
    CH_MATRIX = 2;

// ❌ 错误
DEFINE_CONSTANT
    IR_CMD = "0xAB...";      // 字符串禁止！
    HOST_IP = "192.168.1.100"; // 字符串禁止！
```

> 详细规范 → `docs/代码组织/DEFINE_CONSTANT.md`

---

## DEFINE_VARIABLE - 变量块

### 格式：`类型 变量名 = 值;`

```creator
DEFINE_VARIABLE
    int x = 222;           // 整型
    float f = 2.5;         // 浮点
    string s = "hello";    // 字符串
    char c = 'A';          // 字符
    boolean b = true;      // 布尔
    byte w = 255;          // 字节
```

### ⚠️ 约束：必须赋初值

```creator
// ❌ 错误
DEFINE_VARIABLE
    int x;      // 未赋初值！
    string s;   // 未赋初值！
```

> 详细规范 → `docs/代码组织/DEFINE_VARIABLE.md`

---

## 串口通信

### SEND_COM

```creator
// ✅ 正确：字符串格式的十六进制
SEND_COM(M_COM, 5, "0x4330300D");
SEND_COM(M_COM, 6, "0x8101060107060301FF");
SEND_COM(M_COM, 2, "(sw,1,3)");       // 文本格式

// ❌ 错误
SEND_COM(dev, ch, byteArr);           // 不能用字节数组
```

### SET_COM

```creator
// ✅ 完整参数
SET_COM(M_COM, 5, 9600, 8, 0, 10, 0, 232);
//     设备,端口,波特率,数据位,校验位,停止位,,类型
```

---

## 其他约束

| 场景 | 错误写法 | 正确写法 |
|-----|---------|---------|
| 变量类型关键字 | `INTEGER` `STRING` `BOOLEAN` | `int` `string` `boolean`（全部小写） |
| 条件语句关键字 | `IF` `ELSE IF` `ELSE` | `if` `else if` `else`（全部小写） |
| 事件括号 | `BUTTON_EVENT[tp, 1]` | `BUTTON_EVENT(tp, 1)`（圆括号） |
| 触摸屏拉条 | ~~`LEVEL_EVENT` 不支持~~ | ✅ **已修正：LEVEL_EVENT 支持**，见 `code-patterns.md` 模式4 |
| 延时（匿名） | `WAIT(3000)` | `WAIT 3000 { ... }` |
| 延时（命名） | `WAIT(3000, "name")` | `WAIT 3000 "name" { ... }` |
| TCP/UDP事件 | `DATA_EVENT(SOCKET_TCP)` | 不支持，只支持单向发送 |
| 参数存取 | `SAVE_STRING() / LOAD_INT()` | `SAVE_PARAM() / LOAD_PARAM()` |
| 取消定时器 | `CANCEL_TIMER(heartbeat)` | `CANCEL_TIMER("heartbeat")` |
| 显示数值到触摸屏 | `SET_VALUE(10, 1200, val)` | `SEND_TEXT(tp, 1200, ITOA(val))` |
| 页面跳转 | `POPUP_TO(10, "页面")` | `SEND_PAGING(tp, pageNum, "页面名")` |
| 全角标点 | `（` `）` `，` | 必须使用半角 `(` `)` `,` |

---

## 支持的语法

| 语法 | 示例 |
|-----|------|
| for 循环 | `for (i = 0; i <= 10; i += 1) { }` |
| else if | `if (...) { } else if (...) { }` |
| switch | `switch(var) { case 1: ... break; default: ... break; }` |
| 字符串拼接 | `"hello" + name + " world"` |

---

## 设备命名格式

```
主机设备：  设备名 = M:板卡号:设备类型;
            例：M_COM = M:1002:COM;

Touch屏：   设备名 = T:设备号:TP;
            例：tp = T:10:TP;

CRNET设备： 设备名 = N:CRNET号:设备类型;
            例：RELAY_N = N:7:RELAY;
```