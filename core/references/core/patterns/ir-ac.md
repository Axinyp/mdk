# 模式 5：红外控制空调（UserIRDB 格式）

## 重要限制

`IRCODE<>` 是编译期宏，内部**只接受字面字符串常量**。
**禁止**在 `IRCODE<>` 内使用 `+` 拼接、`ITOA()` 或任何变量/表达式。

错误示例（编译报错）：
```
IRCODE<"UserIRDB:room:F401:GREE:T2021:" + ITOA(temp) + "_1">   // ❌ 非法
```

## 固定温度发送（单按钮 → 单温度）

适用于：按钮直接发送某个固定温度。

```
DEFINE_DEVICE
    TR_0740S_IR2 = L:2:IR;
    tp = T:10:TP;

DEFINE_EVENT
    BUTTON_EVENT(tp, 125)
    {
        PUSH()
        {
            SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:meeting room:F401:GREE:T20211021105429:25_1">);
            SET_BUTTON(tp, 125, 1);
        }
    }
```

## 动态温度调节（温度加减 + 文本显示）

适用于：有温度加/减按钮，支持 16-30°C 范围，界面显示当前温度。

核心思路：用 `int` 变量记录当前温度，`if-else` 逐值匹配发送对应的 IRCODE 字面量。

```
DEFINE_DEVICE
    TR_0740S_IR2 = L:2:IR;
    tp = T:10:TP;

DEFINE_VARIABLE
    int curTemp = 25;

DEFINE_FUNCTION
    void SendAcTemp(int temp)
    {
        if (temp == 16) { SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:room:brand:model:timestamp:16_1">); }
        else if (temp == 17) { SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:room:brand:model:timestamp:17_1">); }
        else if (temp == 18) { SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:room:brand:model:timestamp:18_1">); }
        else if (temp == 19) { SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:room:brand:model:timestamp:19_1">); }
        else if (temp == 20) { SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:room:brand:model:timestamp:20_1">); }
        else if (temp == 21) { SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:room:brand:model:timestamp:21_1">); }
        else if (temp == 22) { SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:room:brand:model:timestamp:22_1">); }
        else if (temp == 23) { SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:room:brand:model:timestamp:23_1">); }
        else if (temp == 24) { SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:room:brand:model:timestamp:24_1">); }
        else if (temp == 25) { SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:room:brand:model:timestamp:25_1">); }
        else if (temp == 26) { SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:room:brand:model:timestamp:26_1">); }
        else if (temp == 27) { SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:room:brand:model:timestamp:27_1">); }
        else if (temp == 28) { SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:room:brand:model:timestamp:28_1">); }
        else if (temp == 29) { SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:room:brand:model:timestamp:29_1">); }
        else if (temp == 30) { SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:room:brand:model:timestamp:30_1">); }
        SEND_TEXT(tp, 300, ITOA(temp));
    }

DEFINE_EVENT
    BUTTON_EVENT(tp, 301)
    {
        PUSH()
        {
            if (curTemp < 30)
            {
                curTemp = curTemp + 1;
                SendAcTemp(curTemp);
            }
        }
    }
    BUTTON_EVENT(tp, 302)
    {
        PUSH()
        {
            if (curTemp > 16)
            {
                curTemp = curTemp - 1;
                SendAcTemp(curTemp);
            }
        }
    }
```

## 多 IR 设备同步控制（多台空调同步）

当需要同时控制多台 IR 设备（如两个 TR-0740S 的红外口），**每个设备都必须有完整的 if-else 链**，禁止对任一设备使用字符串拼接。

```
DEFINE_DEVICE
    TR_0740S_IR1 = L:2:IR;
    TR_0740S_IR2 = L:3:IR;
    tp = T:10:TP;

DEFINE_FUNCTION
    void SendAcTemp(int temp)
    {
        // IR设备1 — 完整 if-else 链
        if (temp == 16) { SEND_IRCODE(TR_0740S_IR1, 1, IRCODE<"UserIRDB:room:brand:model:ts:16_1">); }
        else if (temp == 17) { SEND_IRCODE(TR_0740S_IR1, 1, IRCODE<"UserIRDB:room:brand:model:ts:17_1">); }
        // ... 18-29 ...
        else if (temp == 30) { SEND_IRCODE(TR_0740S_IR1, 1, IRCODE<"UserIRDB:room:brand:model:ts:30_1">); }

        // IR设备2 — 同样必须完整 if-else 链，禁止用拼接
        if (temp == 16) { SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:room:brand:model:ts:16_1">); }
        else if (temp == 17) { SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:room:brand:model:ts:17_1">); }
        // ... 18-29 ...
        else if (temp == 30) { SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:room:brand:model:ts:30_1">); }

        SEND_TEXT(tp, 300, ITOA(temp));
    }
```

⚠️ 常见错误：对第二个设备使用拼接"偷懒"：
```
SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:..." + ITOA(temp) + "_1">);  // ❌ 编译报错
```

## UserIRDB 码格式说明

格式：`UserIRDB:{group}:{subgroup}:{brand}:{learning_timestamp}:{instruction_id}`

- `group` — 空间名（如 meeting room）
- `subgroup` — 子区域（如 F401）
- `brand` — 品牌（如 GREE）
- `learning_timestamp` — 学码时间戳（如 T20211021105429）
- `instruction_id` — 指令编号（如 `25_1` 表示 25°C 制冷模式1）

**用户必须提供完整的 UserIRDB 路径**，生成代码时原样填入 IRCODE<> 内，仅替换末尾温度编号部分。
