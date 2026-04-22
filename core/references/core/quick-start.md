# MKControl Creator 语言快速入门

## 程序结构

MKControl .cht 程序由以下固定段落组成（顺序不可颠倒）：

```creator
DEFINE_DEVICE      // 设备定义段（必须）
DEFINE_COMBINE     // 设备组合段（可选）
DEFINE_CONSTANT    // 常量定义段（可选）
DEFINE_VARIABLE    // 变量定义段（可选）
DEFINE_FUNCTION    // 自定义函数段（可选）
DEFINE_START       // 启动初始化段（可选）
DEFINE_EVENT       // 事件处理段（核心逻辑）
```

---

## 数据类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `int` | 整数 | `int count = 0;` |
| `long` | 长整数 | `long baud = 9600;` |
| `double` | 浮点数 | `double temp = 25.5;` |
| `string` | 字符串 | `string name = "test";` |
| `boolean` | 布尔 | `boolean flag = false;` |
| `byte[]` | 字节数组 | `byte buf[0];` |

---

## 设备地址格式

```
主机板卡：  设备名 = M:板卡号:设备类型;
Touch屏：   设备名 = T:设备号:TP;
CRNET设备： 设备名 = N:CRNET号:设备类型;
```

**设备类型列表：**

| 类型关键字 | 说明 |
|-----------|------|
| `COM` | 串口 |
| `RELAY` | 继电器 |
| `IR` | 红外 |
| `IO` | IO口 |
| `TP` | 触摸屏 |
| `DMX` | DMX512灯光 |
| `LITE` | DALI灯光 |

---

## 事件类型

| 事件 | 触发条件 |
|------|----------|
| `BUTTON_EVENT(dev, ch)` | 触摸屏按钮操作 |
| `DATA_EVENT(dev, ch)` | 设备数据接收 |
| `ONLINE_EVENT(dev, ch)` | 设备上线 |
| `OFFLINE_EVENT(dev, ch)` | 设备下线 |
| `LEVEL_EVENT(dev, ch)` | 触摸屏拉条变化 |
| `TIMER 名称()` | 定时器触发 |

---

## 控制流

```creator
// 条件判断
if (condition)
{
    // ...
}
else if (condition2)
{
    // ...
}
else
{
    // ...
}

// 循环
while (condition)
{
    // ...
}
for (int i = 0; i < 10; i++)
{
    // ...
}

// switch
switch (var)
{
    case 1:
        // ...
        break;
    default:
        // ...
        break;
}
```

---

## 字符串拼接

```creator
string result;
result = "Hello" + " " + "World";     // 字符串拼接用 +
result = "数量: " + ITOA(count);       // 整数转字符串拼接
TRACE("设备IP: " + deviceIp);
```

---

## 完整程序示例（最小可运行）

```creator
DEFINE_DEVICE
    tp = T:10:TP;
    M_RELAY = M:100:RELAY;

DEFINE_CONSTANT
    CH_LIGHT = 1;  // 灯光继电器通道

DEFINE_VARIABLE
    int lightOn = 0;

DEFINE_START
    OFF_RELAY(M_RELAY, CH_LIGHT);
    SEND_TEXT(tp, 1, "系统就绪");

DEFINE_EVENT
    BUTTON_EVENT(tp, 1)
    {
        PUSH()
        {
            if (lightOn == 0)
            {
                ON_RELAY(M_RELAY, CH_LIGHT);
                lightOn = 1;
                SET_BUTTON(tp, 1, 1);
            }
            else
            {
                OFF_RELAY(M_RELAY, CH_LIGHT);
                lightOn = 0;
                SET_BUTTON(tp, 1, 0);
            }
        }
    }
```
