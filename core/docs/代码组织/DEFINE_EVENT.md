**DEFINE_EVENT: 事件定义块**

**事件定义必须放在此块中。**
**1、按钮事件**
语法规则：参数可以是0个、1个 、2个。有2个参数，即制定设备名和jionNumber时，事件只对指定设备、指定jionNumber有效； 当有1个参数，即指定设备时，事件对指定设备有效。 当参数为0个时，事件对所有设备有效。事件中可以有响应“按下”、“松开”、“按住”、“整个按键过程”四种 动作的函数。事件处理代码必须放到相应的函数当中。
```
BUTTON_EVENT([device] [,JionNumber])  
{  
    PUSH()  
    {  
        // 当按钮按下去时执行的动作  
    }  
    RELEASE()  
    {  
        // 当按钮松手时执行的动作  
    }  
    HOLD(<TIME>[,TRUE|FALSE])  
    {  
        // 当按钮按住时过了多长时间/或每隔多长重复执行的动作  
    }  
    REPEAT()  
    {  
        // 当按钮被按住时重复做的动作  
    }  
}
```
**例子：**
```
DEFINE_EVENT  
    // 响应设备tp，JionNumber=3的BUTTON事件  
    BUTTON_EVENT(tp,3)  
    {  
        PUSH()  
        {  
            TRACE("BUTTON_EVENT(tp,3) push\n");  
            int i = 34;  
            ON_RELAY(relay1);  
            ON_RELAY(relay2);  
        }  
         
        HOLD(2000)  
        {  
            TRACE("HOLD");  
        }  
         
        REPEAT()  
        {  
            TRACE("REPEAT");  
        }  
    }  
   
    // 响应设备tp的所有BUTTON事件  
    BUTTON_EVENT(tp)  
    {  
        PUSH()  
        {  
            TRACE("BUTTON_EVENT(tp,3) push\n");  
        }  
    }  
   
    // 响应所有的BUTTON事件  
    BUTTON_EVENT()  
    {  
        RELEASE()  
        {  
            TRACE("BUTTON_EVENT(tp,3) push\n");  
        }  
    }
```
**2、拉条事件  
**语法规则：参数可以是0个、1个、2个。有2个参数，即制定设备名和通道号时，事件只对指定设备、指定jionNumber有效；当有1个参数，即指定设备时，事件对指定设备有效。 当参数为0个时，事件对所有设备有效。
```
LEVEL_EVENT([device] [, JionNumber])  
{  
    // 当按拉条变化时执行的动作  
}
```
**例子：**
```
DEFINE_EVENT  
    // 响应设备tp，JionNumber= 3的LEVEL事件  
    LEVEL_EVENT(tp,2)  
    {  
        TRACE("LEVEL_EVENT(tp,2)\n");  
        OFF_RELAY(relay3);  
        ON_RELAY(relay2);  
    }  
   
    // 响应设备tp的所有LEVEL事件  
    LEVEL_EVENT(tp)  
    {  
        TRACE("LEVEL_EVENT(tp)\n");  
        OFF_RELAY(relay1);  
        ON_RELAY(relay2);  
    }  
   
    // 响应所有的LEVEL事件  
    LEVEL_EVENT(){  
        TRACE("LEVEL_EVENT()\n");  
        OFF_RELAY(relay2);  
        ON_RELAY(relay3);  
   
        TRACE( LEVEL.DeviceType + " " +  
            LEVEL.DeviceID + " " +  
            LEVEL.Module + " " +  
            LEVEL.Channel + " " +  
            LEVEL.Value + " " +  
            LEVEL.JoinNumber + "\n");  
    }
```

**3、数据事件**

```
DATA_EVENT([device])  
{  
    ONLINE()  
    {  
        // 当收到设备的数据在线指令时执行的动作  
    }  
    OFFLINE（）  
    {  
        // 当收到设备的数据离线指令时执行的动作  
    }  
    ONERROR（）  
    {  
        // 当收到设备的数据错误指令时执行的动作  
    }  
    ONDATA()  
    {  
        // 当收到设备的数据时执行的动作  
    }  
}
```
**例子：**
```
DEFINE_EVENT  
    // 响应设备com的DATA事件  
    DATA_EVENT(com,1)  
    {  
        ONLINE()  
        {  
            TRACE("DATA_EVENT(relay1)\n");   
        }  
    }  
   
    // 响应所有com设备的DATA事件  
    DATA_EVENT(com)  
    {  
        ONLINE()  
        {  
            TRACE("DATA_EVENT(relay1)\n");  
        }  
    }
```