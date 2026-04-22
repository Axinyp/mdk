# DSP音量控制函数 (help)

| **_ DSP音量控制函数 _** | [](MINICC设备控制函数.md "MINICC设备控制函数")[](Lovo无线灯光控制器控制函数.md "Lovo无线灯光控制器控制函数") |
| --- | --- |
| --- | --- | --- | --- |

_导航: 帮助 > [MINICC设备控制函数](MINICC设备控制函数.md "MINICC设备控制函数") > _

---
#   GET_VOL_M
```text
int GET_VOL_M(int channel)
```
功能：获取输入通道的音量db值
**Parameters:**
`channel` \- :通道号
示例：
```
GET_VOL_M(1);//获取第一路输入通道的音量值
```
* * *
# ##  GET_MUTE_M
```text
int GET_MUTE_M(int channel)
```

功能：获取输入通道是否静音
**Parameters:**
`channel` \- :通道号
示例：
GET_MUTE_M(1);//获取第一路输入通道的是否静音
* * *
# SET_VOL_M
```text
  void SET_VOL_M(int channel,int mute,int vol)
```
功能：设置输入通道音量db值和设置输入通道是否静音
**Parameters:**
`channel` \- :通道号
`mute` \- :静音使能
`vol` \- :音量db值[6db,-60db]
示例：
```
SET_VOL_M(1,1,-30);//设置第一路输入通道静音、音量db值为-30db
```
* * *
**示例：******
```
DEFINE_DEVICE
	tp = T:10:TP;
	tp1 = T:11:TP;
DEFINE_COMBINE
	[ tp, tp1 ];
DEFINE_CONSTANT
DEFINE_VARIABLE
	int chanel_vol_value[3];
	int chanel_mute_status[3];
	int i;
DEFINE_FUNCTION
DEFINE_TIMER
DEFINE_START
DEFINE_EVENT
	BUTTON_EVENT(tp,1);
	{
		PUSH()
		{
			for(i=0;i<3;i=i+1) 
			{
				//获取各个通道的音量值
				chanel_vol_value[i] = GET_VOL_M(i);
				//获取各个通道的是否静音
				chanel_mute_status[i] = GET_MUTE_M(i);
			}
		}
	}
	BUTTON_EVENT(tp,2);
	{
		PUSH()
		{
			//设置通道音量、是否静音
			SET_VOL_M(1,1,-30);
		}
	}

DEFINE_PROGRAME
```
* * *
