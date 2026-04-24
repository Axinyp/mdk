# Lovo无线窗帘控制器控制函数 (help)

| **_ Lovo无线窗帘控制器控制函数 _** | [](Lovo无线投影幕控制器控制函数.md "Lovo无线投影幕控制器控制函数")[](矩阵控制函数.md "矩阵控制函数") |
| --- | --- |
| --- | --- | --- | --- |

_导航: 帮助 > [MINICC设备控制函数](MINICC设备控制函数.md "MINICC设备控制函数") > _

---

# SET_LOVOCURTAIN
```text
void SET_LOVOCURTAIN(String dev, int chanel, int val)
```

功能：设置Lovo无线窗帘控制器状态
**Parameters:**
`dev` \- :输入设备
`Chanel` \- :通道号
`val` \- :状态值(1:打开, 0:停止, -1:关闭)
示例：
```
curtain = Z:00:ZIGBEE:"500000112";//劳沃窗帘控制器
SET_LOVOCURTAIN(curtain,1,1);//控制劳沃控制器打开窗帘
```
* * *
# ##  GET_LOVOCURTAIN_STATE
```text
int GET_LOVOCURTAIN_STATE(String str)
```

功能：解析无线劳沃窗帘控制器当前状态值
**Parameters:**
`str` \- :劳沃状态值
示例：
```
int status;
status = GET_LOVOCURTAIN_STATE(DATA.DataString);//获取Lovo无线窗帘控制器状态值
```
* * *
**示例：******
```
DEFINE_DEVICE
	tp = T:10:TP;
	tp1 = T:11:TP;
	curtain = Z:00:ZIGBEE:"500000112";//劳沃窗帘控制器
DEFINE_COMBINE
	[ tp, tp1 ];
DEFINE_CONSTANT
DEFINE_VARIABLE
DEFINE_FUNCTION
DEFINE_TIMER
DEFINE_START
DEFINE_EVENT
	//触摸屏控制劳沃窗帘控制器
	BUTTON_EVENT(tp,16);
	{
		PUSH()
		{
			SET_LOVOCURTAIN(curtain,1,1);//控制劳沃控制器打开窗帘
		}
	}
	BUTTON_EVENT(tp,17);
	{
		PUSH()
		{
			SET_LOVOCURTAIN(curtain,1,0);//控制劳沃控制器停止
		}
	}
	BUTTON_EVENT(tp,18);
	{
		PUSH()
		{
			SET_LOVOCURTAIN(curtain,1,-1);//控制劳沃控制器关闭窗帘
		}
	}
	//同步劳沃窗帘控制器状态
	DATA_EVENT(screen)
	{
		ONDATA()
		{
			if(GET_LOVOCURTAIN_STATE(DATA.DataString) == 1)
			{
				SET_BUTTON(tp,16,1);
			}
			else if(GET_LOVOCURTAIN_STATE(DATA.DataString) == 0)
			{
				SET_BUTTON(tp,17,1);
			}
			else if(GET_LOVOCURTAIN_STATE(DATA.DataString) == -1)
			{
				SET_BUTTON(tp,18,1);
			}
		}
	}

DEFINE_PROGRAME
```
* * *
