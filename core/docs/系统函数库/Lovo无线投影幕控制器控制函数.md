# Lovo无线投影幕控制器控制函数 (help)

| **_ Lovo无线投影幕控制器控制函数 _** | [](Lovo无线灯关控制器控制函数.md "后退")[](Lovo无线窗帘控制器控制函数.md "Lovo无线窗帘控制器控制函数") |
| --- | --- |
| --- | --- | --- | --- |

_导航: 帮助 > [MINICC设备控制函数](MINICC设备控制函数.md "MINICC设备控制函数") > _

---

#  SET_LOVOSCREEN
```text
void SET_LOVOSCREEN(String dev, int chanel, int val)
```

功能：设置Lovo无线投影幕控制器状态
**Parameters:**
`dev` \- :输入设备
`Chanel` \- :通道号
`val` \- :状态值(1:上升, 0:停止, -1:下降)
示例：
```
screen = Z:00:ZIGBEE:"510000070";//Lovo无线投影幕控制器
SET_LOVOSCREEN(screen,1,1);//设置劳沃无线投影幕控制器上升
```
* * *
#  GET_LOVOSCREEN_STATE
```text
void GET_LOVOSCREEN_STATE(String str)
```

功能：解析劳沃当前状态值
**Parameters:**
`str` \- :劳沃状态值
示例：
```
int status;
status = GET_LOVOSCREEN_STATE(DATA.DataString);//获取Lovo无线投影幕状态值
```
* * *
**示例：******
```
DEFINE_DEVICE
	tp = T:10:TP;
	tp1 = T:11:TP;
	screen = Z:00:ZIGBEE:"510000070";//Lovo无线投影幕控制器
DEFINE_COMBINE
	[ tp, tp1 ];

DEFINE_CONSTANT
DEFINE_VARIABLE
DEFINE_FUNCTION
DEFINE_TIMER
DEFINE_START
DEFINE_EVENT
//触摸屏按钮控制劳沃投影幕控制器
	BUTTON_EVENT(tp,13);
	{
		PUSH()
		{
		SET_LOVOSCREEN(screen,1,1); //控制劳沃投影幕控制面板上升
		}
	}
	BUTTON_EVENT(tp,14);
	{
		PUSH()
		{
		SET_LOVOSCREEN(screen,1,0); //控制劳沃投影幕控制面板停止
		}
	}
	BUTTON_EVENT(tp,15);
	{
		PUSH()
		{
		SET_LOVOSCREEN(screen,1,-1); //控制劳沃投影幕控制面板下降
		}
	}
//同步劳沃投影幕控制器状态
	DATA_EVENT(screen)
	{
		ONDATA()
		{
			if(GET_LOVOSCREEN_STATE(DATA.DataString) == 1)
			{
				SET_BUTTON(tp,13,1);
			}
			else if(GET_LOVOSCREEN_STATE(DATA.DataString) == 0)
			{
				SET_BUTTON(tp,14,1);
			}
			else if(GET_LOVOSCREEN_STATE(DATA.DataString) == -1)
			{
				SET_BUTTON(tp,15,1);
			}
		}
	}
DEFINE_PROGRAME
```
* * *