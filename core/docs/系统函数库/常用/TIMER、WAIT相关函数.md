# TIMER、WAIT相关函数

| **_ TIMER、WAIT相关函数 _** | [](参数存取相关函数.md "参数存取相关函数")[](其他函数.md "其他函数") |
| --- | --- |
| --- | --- | --- | --- |

_导航: 帮助 > [MKControl函数](系统函数.md) > _
* * *
[START_TIMER](#start_timer)    [CANCEL_TIMER](#cancel_timer)   [WAIT](#wait)   [CANCEL_WAIT](#cancel_wait)   [SLEEP](#sleep)

# START_TIMER
```
void START_TIMER(String name,int time);
```
功能：启动名为name的Timer的定时执行器,定时器间隔执行时间为time毫秒。与CANCEL_TIMER(XXX)搭配使用
参数：name -: Timer的定时执行器的名字，也即是START_TIMER(XXX)中的XXX
示例：
1、定义Timer触发函数
```
TIMER testTimer()
{
	SEND_ LITE (lite_n,1,65535); //向lite_n的第一路发送模拟量65535
}
```
2、运行一个定时器,并将间隔设为1000毫秒
```
START_TIMER(testTimer,1000);
```
3、取消一个正在运行的定时器
```
CANCEL_TIMER("testTimer");// 注：这里要加双引号标识
```

---
# START_TIMER
```
void START_TIMER(String name,int time ,int year,int mouth,int day,int hh,int minute,int second);
```
功能：在时间year, mouth, day, hh, minute, second启动名为name的Timer的定时执行器 ,定时器间隔执行时间为time毫秒。与CANCEL_TIMER(XXX)搭配使用
参数：
`name` -: Timer的定时执行器的名字，也即是START_TIMER(XXX)中的XXX
示例：

1、定义Timer触发函数
```
TIMER testTimer()
{
	SEND_ LITE (lite_n,1,65535); //向lite_n的第一路发送模拟量65535
}
```

2、运行一个定时器,并将间隔设为日，并设定定时器启动时间为2010年10月26日14时。
```
START_TIMER(testTimer,1000*3600*24 2010,10,26,14,00,00);
```
3、取消一个正在运行，或已经用START_TIMER(testTimer,1000*3600*24 2010,10,26,14,00,00) 启动，但没执行的定时器。
```
   CANCEL_TIMER("testTimer");// 注：这里要加双引号标识
```
---
# CANCEL_TIMER
```
void CANCEL_TIMER(String name);
```
功能：取消名为name的Timer的定时执行器。与START_TIMER(XXX,t)搭配使用
参数：
`name` -: Timer的定时执行器的名字，也即是START_TIMER(XXX)中的XXX
示例：
1、定义Timer触发函数
```text
TIMER testTimer()
{
	SEND_ LITE (lite_n,1,65535); //向lite_n的第一路发送模拟量65535
}
```
2、运行一个定时器,并将间隔设为1000毫秒
START_TIMER(testTimer,1000);
3、取消一个正在运行的定时器
```
   CANCEL_TIMER("testTimer");// 注：这里要加双引号标识
```
# WAIT
 格式：WAIT 数值常量 或WAIT 数值常量 “该语块名”
功能：类似SLEEP函数，将WAIT语句块里面的操作催迟到一定时间（WAIT的最小单位为毫秒）才执行。与SLEEP不同的是，该语句块不会影响触摸继续操作其他操作。
分类：据定义格式分为匿名WAIT语句块和有名WAIT语句块。匿名WAIT语句块有系统分配名字，不可以用CANCEL_WAIT取消正在执行的操作。有名WAIT语句块，可调用CANCEL_WAIT函数取消正在执行的WAIT语句块。
 示例：
1、匿名
```
WAIT 1000
{
 ON_RELAY(relay_M,2);//延迟一秒再打开relay_M的第二路。
}
```
2、有名
```
WAIT 3000 "xxx"
{
	ON_RELAY(relay_M,2);//延迟三秒再打开relay_M的第二路。
}
```
  3、取消
```
 CANCEL_WAIT("xxx ");
```

# CANCEL_WAIT
```text
void  CANCEL_WAIT(string name)
```
功能：取消名为name的WAIT语句
参数：
`name` -: WAIT语句的名字
示例：

```
// tp 通道号 3 的 button 事件处理
BUTTON_EVENT(tp,3)
{
	PUSH()
	{
	    WAIT 4000 "ty"    // 此WAIT语句名为"ty"
	    {
	        TRACE("WAIT 4000 \"ty\"\n");
		}
	}  
}
```
// 取消名为 "ty" 的 WAIT 语句
```
BUTTON_EVENT(tp,4)
{
	PUSH()
	{
	  CANCEL_WAIT("ty");
	} 
}
```
  

---
# SLEEP   
```
  void SLEEP(int time)
```
**功能 ：让程序休眠一段时间。**
**Parameters:**
`time`\- 休眠时间，单位：毫秒
示例：
``` 
BUTTON_EVENT(tp,4)
{
	PUSH()
	{
		SLEEP(1000); //这里休眠一秒（注：这里会使主线程休眠一秒）
	} 
}
```
