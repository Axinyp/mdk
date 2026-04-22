## DEFINE_TIMER: 定时器定义块
**定时器定义必须放在此块中。**
**说明:对于一些实际要求，可能需要定义一个时钟，一些动作需要每隔一段时间执行一次。**
**格式：**
```
TIMER 函数名()
{
  //执行动作
}
```
**调用：**
START_TIMER(函数名, 时间间隔毫秒);
CANCEL_TIMER("函数名");   // 注：这里的函数名需用双引号引起
**举例：**
```
DEFINE_TIMER
TIMER setVol()
{
 if(65536 > vol_value)
 {
  SET_VOLTOTOL(dev_vol, 2, vol_value);
  vol_value = vol_value + 100;
 }
 else
 {
  CANCEL_TIMER("setVol");
 }
}

// 调用：每隔1秒执行一次
START_TIMER(setVol, 1000);
// 关闭
CANCEL_TIMER("setVol");
```
**注**：可在 `setVol` 内部调用 `CANCEL_TIMER` 关闭，防止不关闭造成的资源浪费
