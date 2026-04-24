# 模式 5：红外控制空调（UserIRDB 格式）

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
