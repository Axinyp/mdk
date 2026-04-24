# 模式 8：HTTP API（视频会议终端）

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
