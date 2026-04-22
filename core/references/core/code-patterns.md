# MKControl 代码模式库

> 来源：旧 skill 基础 + 401 会议室实码验证补充
> ✅ 修正：LEVEL_EVENT 已确认支持（401.cht 第2192行）

---

## 模式 1：串口设备控制（投影仪/矩阵/摄像机）

```
DEFINE_DEVICE
    M_COM = M:1002:COM;
    tp = T:10:TP;

DEFINE_FUNCTION
    void ProjectorOn()
    {
        SEND_COM(M_COM, 1, "PWR ON\r");
    }
    void ProjectorOff()
    {
        SEND_COM(M_COM, 1, "PWR OFF\r");
    }

DEFINE_START
    SET_COM(M_COM, 1, 9600, 8, 0, 10, 0, 232);

DEFINE_EVENT
    BUTTON_EVENT(tp, 1)
    {
        PUSH() { ProjectorOn(); }
    }
    BUTTON_EVENT(tp, 2)
    {
        PUSH() { ProjectorOff(); }
    }
    DATA_EVENT(M_COM, 1)
    {
        ONDATA()
        {
            string resp;
            resp = BYTES_TO_STRING(DATA.Data);
            TRACE("投影仪响应: " + resp);
        }
    }
```

---

## 模式 2：继电器控制灯光/幕布

```
DEFINE_DEVICE
    L9101_RELAY = L:1:RELAY;
    tp = T:10:TP;

DEFINE_EVENT
    // AutolockBtn — PUSH开/RELEASE关
    BUTTON_EVENT(tp, 103)
    {
        PUSH()
        {
            ON_RELAY(L9101_RELAY, 1);
            SET_BUTTON(tp, 103, 1);
        }
        RELEASE()
        {
            OFF_RELAY(L9101_RELAY, 1);
            SET_BUTTON(tp, 103, 0);
        }
    }

    // NormalBtn — 全开
    BUTTON_EVENT(tp, 101)
    {
        PUSH()
        {
            ON_RELAY(L9101_RELAY, 1);
            ON_RELAY(L9101_RELAY, 2);
            SET_BUTTON(tp, 101, 1);
        }
    }
    // NormalBtn — 全关
    BUTTON_EVENT(tp, 102)
    {
        PUSH()
        {
            OFF_RELAY(L9101_RELAY, 1);
            OFF_RELAY(L9101_RELAY, 2);
            SET_BUTTON(tp, 101, 0);
        }
    }
```

---

## 模式 3：场景联动（WAIT 链 + MutualLockBtn 互斥）

```
DEFINE_DEVICE
    L9101_RELAY = L:1:RELAY;
    TR_0740S_COM2 = L:2:COM;
    tp = T:10:TP;

DEFINE_FUNCTION
    void SceneStart()
    {
        ON_RELAY(L9101_RELAY, 1);
        // MutualLockBtn 互斥：手动更新状态
        SET_BUTTON(tp, 148, 1);
        SET_BUTTON(tp, 144, 0);
        SET_BUTTON(tp, 146, 0);

        WAIT 2000
        {
            SEND_COM(TR_0740S_COM2, 2, "0xFFAA0400110213");
        }
        WAIT 5000
        {
            SEND_PAGING(tp, 1, "主控页");
        }
    }

    void SceneEnd()
    {
        SEND_COM(TR_0740S_COM2, 2, "0xFFAA0400110112");
        WAIT 3000
        {
            OFF_RELAY(L9101_RELAY, 1);
        }
    }

DEFINE_EVENT
    BUTTON_EVENT(tp, 148)
    {
        PUSH() { SceneStart(); }
    }
    BUTTON_EVENT(tp, 500)
    {
        PUSH() { SceneEnd(); }
    }
```

---

## 模式 4：滑条音量控制（LEVEL_EVENT）

> ✅ LEVEL_EVENT 支持（401.cht 第2192行验证）

```
DEFINE_DEVICE
    tp = T:10:TP;

DEFINE_CONSTANT
    SLIDER_VOL = 1087;
    TXT_VOL    = 300;

DEFINE_VARIABLE
    int currentVol = 0;
    int crcVal = 0;

DEFINE_FUNCTION
    void SendVolume(int vol)
    {
        int byte1;
        int byte2;
        int sum;
        byte1 = vol / 256;
        byte2 = vol - (byte1 * 256);
        sum = 0xF0 + 0x0D + byte1 + byte2;
        crcVal = sum - ((sum / 256) * 256);
        SET_LEVEL(tp, SLIDER_VOL, vol);
        SEND_TEXT(tp, TXT_VOL, ITOA(vol));
    }

DEFINE_EVENT
    LEVEL_EVENT(tp, SLIDER_VOL)
    {
        currentVol = GET_LEVEL(tp, SLIDER_VOL);
        SendVolume(currentVol);
    }
```

---

## 模式 5：红外控制空调（UserIRDB 格式）

```
DEFINE_DEVICE
    TR_0740S_IR2 = L:2:IR;
    TR_0740S_IR3 = L:3:IR;
    tp = T:10:TP;

DEFINE_EVENT
    BUTTON_EVENT(tp, 125)
    {
        PUSH()
        {
            SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:meeting room:F401:GREE:T20211021105429:25_1">);
            SEND_IRCODE(TR_0740S_IR3, 1, IRCODE<"UserIRDB:meeting room:F401:GREE:T20211021105429:25_1">);
            SET_BUTTON(tp, 125, 1);
        }
    }
```

---

## 模式 6：SEND_PICTURE 图片状态切换

```
DEFINE_DEVICE
    tp = T:10:TP;

DEFINE_EVENT
    BUTTON_EVENT(tp, 140)  // 开
    {
        PUSH() { SEND_PICTURE(tp, 150, 1); }
    }
    BUTTON_EVENT(tp, 141)  // 停
    {
        PUSH() { SEND_PICTURE(tp, 150, 2); }
    }
    BUTTON_EVENT(tp, 142)  // 关
    {
        PUSH() { SEND_PICTURE(tp, 150, 0); }
    }
```

---

## 模式 7：窗帘 RS485 控制

```
DEFINE_DEVICE
    TR_0740S_COM2 = L:2:COM;
    TR_0740S_COM3 = L:3:COM;
    tp = T:10:TP;

DEFINE_START
    SET_COM(TR_0740S_COM2, 2, 9600, 8, 0, 10, 0, 485);
    SET_COM(TR_0740S_COM3, 2, 9600, 8, 0, 10, 0, 485);

DEFINE_EVENT
    BUTTON_EVENT(tp, 140)  // 窗帘总开
    {
        PUSH()
        {
            SET_COM(TR_0740S_COM2, 2, 9600, 8, 0, 10, 0, 485);
            SET_COM(TR_0740S_COM3, 2, 9600, 8, 0, 10, 0, 485);
            SEND_COM(TR_0740S_COM2, 2, "0xFFAA0400110213");
            SEND_COM(TR_0740S_COM3, 2, "0xFFAA0400110112");
        }
    }
    BUTTON_EVENT(tp, 141)  // 窗帘总停
    {
        PUSH()
        {
            SEND_COM(TR_0740S_COM2, 2, "0xFFAA0400110314");
            SEND_COM(TR_0740S_COM3, 2, "0xFFAA0400110314");
        }
    }
    BUTTON_EVENT(tp, 142)  // 窗帘总关
    {
        PUSH()
        {
            SEND_COM(TR_0740S_COM2, 2, "0xFFAA0400110112");
            SEND_COM(TR_0740S_COM3, 2, "0xFFAA0400110213");
        }
    }
```

---

## 模式 8：HTTP API（视频会议终端）

```
DEFINE_VARIABLE
    string loopbackIp = "127.0.0.1";
    int httpPort = 71455;
    string targetIp = "192.168.1.200";
    string cookie = "1";

DEFINE_FUNCTION
    void HttpPost(string apiPath, string postData)
    {
        SEND_UDP(loopbackIp, httpPort,
            "http post " + targetIp + apiPath +
            "+1+Content-Type: application/json" +
            "+" + postData + "+" + cookie + "+filename\n");
    }

DEFINE_EVENT
    BUTTON_EVENT(tp, 60)
    {
        PUSH()
        {
            HttpPost("/action.cgi?ActionID=WEB_MakeCallAPI",
                     "{\"callee\":\"192.168.1.50\"}");
        }
    }
```

---

## 模式 9：IO 检测（DATA_EVENT(M_IO)）

```
DEFINE_DEVICE
    M_IO = M:1:IO;
    tp = T:10:TP;

DEFINE_EVENT
    DATA_EVENT(M_IO)
    {
        ONDATA()
        {
            int ioState;
            ioState = DATA.Value;
            if (ioState == 1)
            {
                SEND_TEXT(tp, 300, "有人");
            }
            else
            {
                SEND_TEXT(tp, 300, "无人");
            }
        }
    }
```

---

## 模式 10：参数持久化

```
DEFINE_VARIABLE
    string savedIp = "192.168.1.100";
    int savedVol = 50;

DEFINE_START
    savedIp  = LOAD_PARAM("device_ip",  savedIp);
    savedVol = LOAD_PARAM("volume",     savedVol);

DEFINE_FUNCTION
    void SaveSettings()
    {
        SAVE_PARAM("device_ip",  savedIp);
        SAVE_PARAM("volume",     savedVol);
    }
```
