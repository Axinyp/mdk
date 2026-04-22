# [设备类型] - [品牌] ([型号])

## 基本信息
- 设备类型：xxx（投影仪 / 窗帘电机 / 空调 / 音频处理器 / 摄像机 / 矩阵 / 显示器 / 调光器 / 其他）
- 通信方式：串口RS232 / 串口RS485 / TCP / UDP / 红外
- 波特率：9600（串口时填写）
- 数据位/停止位/校验：8/1/无
- TCP端口：xxxx（TCP时填写）

## 设备声明（.cht 中的 DEFINE_DEVICE 内容）
```
// 串口示例
SET_COM(dev, channel, 9600, 8, 0, 10, 0, 232);  // RS232
SET_COM(dev, channel, 9600, 8, 0, 10, 0, 485);  // RS485

// TCP示例（在 DEFINE_START 中连接）
CONNECT_TCP(dev, channel, ip, port);
```

## 指令表
| 功能 | 指令 | 说明 |
|------|------|------|
| 开 | xxx | |
| 关 | xxx | |

## 代码示例
```
// 串口发送
SEND_COM(dev, channel, "xxx");

// TCP发送
SEND_TCP(dev, channel, "xxx");

// 红外发送
SEND_IRCODE(dev, channel, "xxx");
```

## 适用型号
- xxx

## 更新记录
- 2026-04-22: 初始录入
