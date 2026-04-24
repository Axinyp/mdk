# Lovo无线灯光控制器控制函数 (help)

| **_ Lovo无线灯光控制器控制函数 _** | [](DSP音量控制函数.md "DSP音量控制函数")[](Lovo无线投影幕控制器控制函数.md "Lovo无线投影幕控制器控制函数") |
| --- | --- |
| --- | --- | --- | --- |

_导航: 帮助 > [MINICC设备控制函数](MINICC设备控制函数.md "MINICC设备控制函数") > _

---

#   SYNC_LOVOLIGHT
```text
void SYNC_LOVOLIGHT(String dev)
```

功能：同步Lovo灯关控制状态
**Parameters:**
`dev` \- :输入设备
示例：
```
lovo = Z:00:ZIGBEE:"735002296";
SYNC_LOVOLIGHT(lovo);
```
* * *
# ##  SET_LOVOLIGHT
```text
void SET_LOVOLIGHT(String dev,int Chanel, int val)
```
功能：控制劳沃灯光控制器开关
**Parameters:**
`dev` \- :输入设备
`channel` \- :通道号
`val` \- :开关值(开:1, 关:0)
示例：
```
SET_LOVOLIGHT(lovo,1,1);//设置Love灯光控制器第一通道开
```
* * *
# SYNC_LOVO_LITGHT_PANEL_STATE
```text
int [] SYNC_LOVO_LITGHT_PANEL_STATE(String str)
```

功能：
**Parameters:**
`str` \- :返回数据
示例：
```
int Lovo_light_status[3];
Lovo_light_status = SYNC_LOVO_LITGHT_PANEL_STATE(DATA.DataString);
```
* * *
**示例：******
```
DEFINE_DEVICE
	tp = T:10:TP;
	tp1 = T:11:TP;
	lovo = Z:00:ZIGBEE:"735002296";//劳沃灯光控制模块
DEFINE_COMBINE
	[ tp, tp1 ];
DEFINE_CONSTANT
DEFINE_VARIABLE
	int Lovo_light_status[3];
DEFINE_FUNCTION
DEFINE_TIMER
DEFINE_START
	SYNC_LOVOLIGHT(lovo); //开机先同步劳沃按键状态;
DEFINE_EVENT
	//触摸屏控制劳沃灯关面板开关
	BUTTON_EVENT(tp,10);
	{
		PUSH()
		{
			SET_LOVOLIGHT(lovo,1,1); //控制劳沃灯关控制面板第一通道开
		}
		RELEASE()
		{
			SET_LOVOLIGHT(lovo,1,0);//控制劳沃灯关控制面板第一通道关
		}
	}
	BUTTON_EVENT(tp,11);
	{
		PUSH()
		{
			SET_LOVOLIGHT(lovo,2,1); //控制劳沃灯关控制面板第二通道开
		}
		RELEASE()
		{
			SET_LOVOLIGHT(lovo,2,0);//控制劳沃灯关控制面板第二通道关
		}
	}
	BUTTON_EVENT(tp,12);
	{
		PUSH()
		{
		SET_LOVOLIGHT(lovo,3,1); //控制劳沃灯关控制面板第三通道开
		}
		RELEASE()
		{
		SET_LOVOLIGHT(lovo,3,0);//控制劳沃灯关控制面板第三通道关
		}
	}
	//调用SYNC_LOVOLIGHT(lovo)函数后接收到数据在改DATA_EVENT中处理数据，更新劳沃灯关控制器的状态
	DATA_EVENT(lovo,0);
	{
		ONDATA()
		{
			Lovo_light_status = SYNC_LOVO_LITGHT_PANEL_STATE(DATA.DataString);//获取劳沃灯关面板状态值
			if(Lovo_light_status[0] == 1)
			{
				SET_BUTTON(tp,10,1);
			}
			if(Lovo_light_status[1] == 1)
			{
				SET_BUTTON(tp,11,1);
			}
			if(Lovo_light_status[2] == 1)
			{
				SET_BUTTON(tp,12,1);
			}
		}
	}
	DATA_EVENT(lovo,1);
	{
		ONDATA()
		{
			if(GET_LOVO_LITGHT_PANEL_STATE(DATA.DataString,1) == 1)
			{
				SET_BUTTON(tp,10,1);
			}
			else if(GET_LOVO_LITGHT_PANEL_STATE(DATA.DataString,1) == 0)
			{
				SET_BUTTON(tp,10,0);
			}
		}
	}
	DATA_EVENT(lovo,2);
	{
		ONDATA()
		{
			if(GET_LOVO_LITGHT_PANEL_STATE(DATA.DataString,2) == 1)
			{
				SET_BUTTON(tp,11,1);
			}
			else if(GET_LOVO_LITGHT_PANEL_STATE(DATA.DataString,2) == 0)
			{
				SET_BUTTON(tp,11,0);
			}
		}
	}
	DATA_EVENT(lovo,3);
	{
		ONDATA()
		{
			if(GET_LOVO_LITGHT_PANEL_STATE(DATA.DataString,3) == 1)
			{
				SET_BUTTON(tp,12,1);
			}
			else if(GET_LOVO_LITGHT_PANEL_STATE(DATA.DataString,3) == 0)
			{
				SET_BUTTON(tp,12,0);
			}
		}
	}

DEFINE_PROGRAME
```
* * *