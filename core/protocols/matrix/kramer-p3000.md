# 矩阵切换器 - Kramer (Protocol 3000)

## 基本信息
- 设备类型：矩阵切换器
- 通信方式：串口RS232 或 TCP
- 波特率：9600（串口时）
- 数据位/停止位/校验：8/1/无
- TCP端口：23（Telnet）或 5000

## 设备声明
```
// 串口方式
SET_COM(M_COM, ch, 9600, 8, 0, 10, 0, 232);

// TCP方式
CONNECT_TCP(dev, ch, ip_addr, 5000);
```

## 指令表（Kramer Protocol 3000）
| 功能 | 指令 | 说明 |
|------|------|------|
| 视频切换 | `#VID {in}>{out}\r\n` | 将输入in切到输出out |
| 音频切换 | `#AUD {in}>{out}\r\n` | |
| 视音频同切 | `#ALL {in}>{out}\r\n` | 视频+音频同时切换 |
| 全输出切到同一输入 | `#ALL {in}\r\n` | 所有输出切到输入in |
| 查询视频路由 | `#VID ?\r\n` | 返回当前路由状态 |

## 代码示例
```
// 将输入1切到输出1（视频）
SEND_COM(M_COM, ch, "#VID 1>1\r\n");

// 将输入2切到输出1（视音频同切）
SEND_COM(M_COM, ch, "#ALL 2>1\r\n");

// TCP方式
SEND_TCP(dev, ch, "#VID 1>1\r\n");
```

## 适用型号
- Kramer VS 系列矩阵（支持 Protocol 3000）
- Kramer VP 系列

## 更新记录
- 2026-04-22: 初始录入，来源：旧协议库迁移 + Kramer Protocol 3000 规范
