# 模式 7：窗帘 RS485 控制

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
