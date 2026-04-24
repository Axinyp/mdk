# 模式 6：SEND_PICTURE 图片状态切换

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
