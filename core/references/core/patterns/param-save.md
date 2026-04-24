# 模式 10：参数持久化

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
