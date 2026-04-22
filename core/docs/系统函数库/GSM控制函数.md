# GSM控制函数

| GSM_ON        | GSM_OFF          | GSM_QUERY       | GSM_MSG_BACK    | GSM_VOL_BACK | GSM_STATE_BACK[] |
| ------------- | ---------------- | --------------- | --------------- | ------------ | ---------------- |
| GSM_DIAL      | GSM_SHOW_NUMBER  | GSM_SEND_SIGNAL | GSM_SEND_MSG    | GSM_RECV_MSG | GSM_SET_PLAYID   |
| GSM_PAUSE     | GSM_STOP         | GSM_SET_VOL     | GSM_FRONT       | GSM_NEXT     | GSM_SINGLE_PLAY  |
| GSM_ALL_CYCLE | GSM_SINGLE_CYCLE | GSM_RING_OFF    | GSM_RECV_SIGNAL | GSM_RESUME   |                  |

* * *
关于GSM数据回复的例子：
```
DEFINE_DEVICE
cc = L:7:GSM;
DEFINE_VARIABLE
string s; //这里为了简洁只定义了一个变量，请按自己需要去定义变量。
int i;
DATA_EVENT(cc)
{
	ONDATA()
	{
		// 当收到设备的数据时执行的动作
		//注：这里一定是BYTES_TO_HEX();不要使用BYTES_TO_STRING();否则无法正确解码。
		str = BYTES_TO_HEX(DATA.Data);
		if (STRING_STARTWITH("00",str))
		{
			s = GSM_SHOW_NUMBER(str);
			//and do something…
		}
		if (STRING_STARTWITH("01",str))
		{
			s = GSM_RECV_SIGNAL(str);
			//and do something…
		}
		if (STRING_STARTWITH("02",str))
		{
			s = GSM_RECV_MSG(str);
			//and do something…
		}
		if (STRING_STARTWITH("03",str))
		{
			i = GSM_MSG_BACK(str);
			i = GSM_VOL_BACK(str);
			//and do something…
		} 
		if (STRING_STARTWITH("04",str))
		{
			i = GSM_STATE_BACK(str);
			//and do something…
		}
	}
}
```
首先必须将回传的数据转换成String类型，然后通过STRING_STARTWITH()函数判断字符串头回复的是哪种数据（00：来电显示。01：双音多频数据。02：短信内容。03短信/语音处理结果。04：状态回复）。处理后的数据返回也是String类型，必须用String类型接(03 短信/语音处理结果、04 GSM状态回复除外)。
* * *
# GSM_ON
```
void GSM_ON(String dev)  
```
功能：GSM开机或重启  
**Parameters:** 
`dev` ：设备名
示例：  
```
GSM_L = L:7:GSM; //定义CRLINK号为7的gsm  
GSM_ON(GSM_L); // 打开CRLINK号为7上的gsm卡
```
* * *
# GSM_OFF
```
void GSM_OFF(String dev)  
```
功能：GSM关机  
**Parameters:** `
dev` ：设备名
示例：  
```
GSM_L = L:7:GSM; //定义CRLINK号为7的gsm卡  
GSM_OFF(GSM_L); // 关闭CRLINK号为7上的gsm卡。
```
* * *
# GSM_QUERY
void GSM_QUERY(String dev)
功能：查询GSM状态
**Parameters:** `
` dev` ：设备名
示例：  
```
GSM_L = L:7:GSM; //定义CRLINK号为7的gsm卡  
GSM_QUERY(GSM_L); //向CRLINK号为7的gsm卡发送查询信息 ，回复的信息用GSM_STATE_BACK()读取。
```
* * *
# GSM_MSG_BACK
```
int GSM_MSG_BACK(String data)  
```
功能：读取短信结果回复信息  
返回值：1 or 2。1成功，2失败。其他状态无效
示例：
```
（假设已经定义有 String str;）  
PS：该函数在数据事件中读取数据，由于数据事件返回的数据是字节数组，所以需先使用 BYTES_TO_HEX函数转换成String类型。  
int i;  
str = BYTES_TO_HEX(DATA.Data);  
i = GSM_MSG_BACK(str);
```
* * *
# GSM_VOL_BACK
```
int GSM_VOL_BACK(String data)  
```
功能：读取语音结果回复信息  
返回值：1-5。1来电或去电，2应答，3无应答，4呼叫失败，5通话结束。其他状态无效
示例：
```
（假设已经定义有 String str;）  
PS：该函数在数据事件中读取数据，由于数据事件返回的数据是字节数组，所以需先使用 BYTES_TO_HEX函数转换成String类型。  
int i;  
str = BYTES_TO_HEX(DATA.Data);  
i = GSM_VOL_BACK(str);
```
* * *
# GSM_STATE_BACK
```
int GSM_VOL_BACK(String data)  
```
功能：读取GSM状态回复信息  
返回值：0-3。0：未开机；1:正在开机；2：待机；3：通话中。其他状态无效
示例：
```
（假设已经定义有 String str;）  
PS：该函数在数据事件中读取数据，由于数据事件返回的数据是字节数组，所以需先使用 BYTES_TO_HEX函数转换成String类型。  
int i;  
str = BYTES_TO_HEX(DATA.Data);  
i = GSM_STATE_BACK(str);
```
****
# GSM_DIAL
```
void GSM_DIAL(String dev , String num)  
```
* 功能：拨打电话  
* **Parameters:** 
`dev` ：设备名  
`num`：要拨的号码，填写时需加双引号。
示例：  
```
GSM_L = L:7:GSM; //定义CRLINK号为7的gsm卡  
GSM_DIAL(GSM_L, "10086"); //CRLINK号为7的gsm卡致电10086
```
* * *
# GSM_SHOW_NUMBER
```
String GSM_SHOW_NUMBER(String num)  
```
功能：来电显示  
返回值：返回字符串类型的号码。
示例：
```
假设已经定义有 String str;）  
PS：该函数在数据事件中读取数据，由于数据事件返回的数据是字节数组，所以需先使用 BYTES_TO_HEX函数转换成String类型。  
string s;  
str = BYTES_TO_HEX(DATA.Data);  
s = GSM_SHOW_NUMBER(str);
```
* * *
# GSM_SEND_SIGNAL  
```
void GSM_SEND_SIGNAL(String dev, String key)  
```
功能：向GSM发送双音多频信号 
 **Parameters:**
`dev` ：设备名  
`key`：0-9，\*，#，A,B,C,D
示例：  
```
GSM_L = L:7:GSM; //定义CRLINK号为7的gsm卡  
GSM_SEND_SIGNAL(GSM_L,"#"); //向CRLINK号为7的gsm卡发送按键 # 命令
```
* * *
# GSM_SEND_MSG
```
void GSM_SEND_MSG(String dev, String smsc, String strRecv, String msg)  
```
功能：发送短信  
**Parameters:**
`dev` :设备名  
`smsc`：短信中心号码  
`strRecv`：接收方号码  
`msg`：信息内容
示例：  
```
GSM_L = L:7:GSM; //定义CRLINK号为7的gsm卡  
GSM_SEND_MSG(GSM_L,"13800200500","13580443427","你好！"); //CRLINK号为7的gsm卡向13580443427用户发送信息，信息内容：你好！
注:经多次测试发现@符号不可正确解码，所以请勿在短信内容中发送@符号。否则会影响整条短信内容无法正确解码。
短信中心号码，请根据GSM卡所在地和运营商对应填写。例子中的短信中心号为广州移动。
```
* * *
# GSM_RECV_MSG
```
String GSM_RECV_MSG(String pdu)  
```
功能：接收短信。对GSM返回的PDU串解码  
返回值：字符串类型。
示例：
```
（假设已经定义有 String msg;）  
//该函数在数据事件中读取数据，由于数据事件返回的数据是字节数组，所以需先使用 BYTES_TO_HEX函数转换成String类型。  
msg = BYTES_TO_HEX(DATA.Data);  
s = GSM_RECV_MSG(msg);
```
* * *
# GSM_SET_PLAYID   
```
void GSM_SET_PLAYID(String dev, String model, int id)  
```
功能：播放指定曲目  
**Parameters:** 
`dev`：设备名  
``model`：播放模式，U盘或者SD卡播放。例："SD" or "U"，大小写均可。  
`id`：要播放曲目的编号，1-99999。
示例：  
```
GSM_L = L:7:GSM; //定义CRLINK号为7的gsm卡  
GSM_SET_PLAYID(GSM_L,"SD",1024); //指定CRLINK号为7的gsm卡以SD卡方式播放，曲目为第1024首
```
* * *
# GSM_RESUME
```
void GSM_RESUME(String dev)  
```
功能：从暂停中恢复播放  
**Parameters:** 
`dev`：设备名
示例：  
```
GSM_L = L:7:GSM; //定义CRLINK号为7的gsm卡  
GSM_RESUME(GSM_L);//恢复CRLINK号为7上的gsm卡音乐播放
```
---
# GSM_STOP
```
void GSM_STOP(String dev)  
```
功能：停止播放  
**Parameters:** 
`dev`：设备名
示例：  
```
GSM_L = L:7:GSM; //定义CRLINK号为7的gsm卡  
GSM_STOP(GSM_L);//停止CRLINK号为7上的gsm卡音乐播放
```
---
# GSM_SET_VOL
```
void GSM_SET_VOL(String dev, int val)  
```
 功能：设置声音大小。val的范围是0-25。  
 **Parameters:** 
`dev`：设备名
示例：  
```
GSM_L = L:7:GSM; //定义CRLINK号为7的gsm卡  
GSM_SET_VOL(GSM_L, 12);//设定CRLINK号为7上的gsm卡声音大小为12
```
---
# GSM_FRONT
```
void GSM_FRONT(String dev)  
```
功能：上一曲  
**Parameters:** 
`dev`：设备名
示例：  
```
GSM_L = L:7:GSM; //定义CRLINK号为7的gsm卡  
GSM_FRONT(GSM_L);//播放CRLINK号为7上的gsm卡上一曲目
```
---
# GSM_NEXT  
```
void GSM_NEXT(String dev)  
```
* 功能：下一曲  
**Parameters:** 
`dev`：设备名
示例：  
```
GSM_L = L:7:GSM; //定义CRLINK号为7的gsm卡  
GSM_NEXT(GSM_L);//播放CRLINK号为7上的gsm卡下一曲目
```
---
# GSM_SINGLE_PLAY  
```
void GSM_SINGLE_PLAY(String dev)  
```
 功能：只播放一首歌曲
 **Parameters:** 
 `dev`：设备名
示例：  
```
GSM_L = L:7:GSM; //定义CRLINK号为7的gsm卡  
GSM_SINGLE_PLAY(GSM_L);//顺序播放CRLINK号为7上的gsm卡曲目
```
---
# GSM_ALL_CYCLE  
```
void GSM_ALL_CYCLE(String dev)  
```
功能：全部循环  
**Parameters:** `
 dev`：设备名
示例：  
```
GSM_L = L:7:GSM; //定义CRLINK号为7的gsm卡  
GSM_ALL_CYCLE(GSM_L);//全部循环播放CRLINK号为7上的gsm卡曲目
```
---
# GSM_SINGLE_CYCLE
```
void GSM_SINGLE_CYCLE(String dev)  
```
功能：单曲循环  
 **Parameters:** `
 `dev`：设备名
示例：  
```
GSM_L = L:7:GSM; //定义CRLINK号为7的gsm卡  
GSM_SINGLE_CYCLE(GSM_L);//单曲循环播放CRLINK号为7上的gsm卡曲目
```
---
# GSM_RING_OFF
```
void GSM_RING_OFF(String dev)  
```
 功能：挂断电话  
 **Parameters:** 
 `dev`：设备名
示例：  
```
GSM_L = L:7:GSM; //定义CRLINK号为7的gsm卡  
GSM_RING_OFF(GSM_L);//挂断CRLINK号为7正在进行的通话
```
---
# GSM_RECV_SIGNAL
```
String GSM_RECV_SIGNAL(String key)  
```
功能：读取GSM卡返回的双音多频信号键值  
返回值：字符串类型。
示例：
```
（假设已经定义有 String str;）  
PS：该函数在数据事件中读取数据，由于数据事件返回的数据是字节数组，所以需先使用 BYTES_TO_HEX函数转换成String类型
str = BYTES_TO_HEX(DATA.Data);  
s = GSM_RECV_SIGNAL(str);
```
* * *