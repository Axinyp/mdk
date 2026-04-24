# 模式 9：IO 检测

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
