# 模式 4：滑条音量控制（LEVEL_EVENT）

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
        currentVol = LEVEL.Value;
        SendVolume(currentVol);
    }
```
