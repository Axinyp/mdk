# IO控制函数

| **_ IO控制函数 _** | [](继电器控制函数.md "继电器控制函数")[](串口控制函数.md "串口控制函数") |
| --- | --- |
| --- | --- | --- | --- |

_导航: 帮助 > [控制设备函数](控制设备函数.md "MINICC设备控制函数") > _
* * *
SEND_IO SET_IO_DIR
***

#  SET_IO
```text
  void SEND_IO(String dev,int channel,int vol)
```
功能：控制IO口
**Parameters:**
`dev` \- ：io设备
`channel` \- :设备通道号
`vol` \- ：vol = 1时输出高电平，vol = 0时输出低电平
示例：
Io_m = M:1000:IO; //定义主机板号为1000的IO
SEND_IO(Io_m,1,0); //向Io_m的第一路输出低电平
* * *
#  SET_IO_DIR
```
void SET_IO_DIR(String dev,int channel,int dir, int pullordown)
```
功能：设置IO口方向IO口
**Parameters:**
`dev` \- ：io设备
`channel` \- :设备通道号
`dir` \- ：dir = 0 输出，dir = 1 输入
`pullordown` \- ：pullordown = 0 下拉，pullordown = 1 上拉
示例：
```
Io_m = M:1000:IO; //定义主机板号为1000的IO
SET_IO_DIR(Io_m,1,0,0); //向Io_m的第一路输出下拉
```
* * *
