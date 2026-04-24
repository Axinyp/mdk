# 模式 2：继电器控制灯光/幕布

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
