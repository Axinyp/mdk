# 模式 1：串口设备控制（投影仪/矩阵/摄像机）

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
