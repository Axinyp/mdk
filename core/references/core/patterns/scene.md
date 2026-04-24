# 模式 3：场景联动（WAIT 链 + MutualLockBtn 互斥）

```
DEFINE_DEVICE
    L9101_RELAY = L:1:RELAY;
    TR_0740S_COM2 = L:2:COM;
    tp = T:10:TP;

DEFINE_FUNCTION
    void SceneStart()
    {
        ON_RELAY(L9101_RELAY, 1);
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
