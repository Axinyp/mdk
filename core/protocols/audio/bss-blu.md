# 音频处理器 - BSS BLU 系列 (HiQnet)

## 基本信息
- 设备类型：音频处理器 / DSP
- 通信方式：TCP
- TCP端口：1023

## 设备声明
```
// TCP 连接（在 DEFINE_START 中）
CONNECT_TCP(dev, ch, ip_addr, 1023);
```

## 指令说明
BSS BLU 系列使用 HiQnet 协议，指令为二进制格式。建议向用户索取设备的具体 HiQnet 地址和参数节点信息。

常用操作：
| 功能 | 说明 |
|------|------|
| 音量调节 | 通过 HiQnet SET_VALUE 指令，参数节点由厂家提供 |
| 静音 | 通过 HiQnet SET_VALUE 指令控制 Mute 参数 |
| 场景切换 | 通过 HiQnet RECALL_PRESET 指令 |

## 代码示例
```
// HiQnet 数据帧结构（十六进制）
// 以下为静音开的示例帧，实际地址需替换
SEND_TCP(dev, ch, "0x{完整HiQnet帧}");

// 建议方式：从用户处获取完整帧数据后填入
SEND_TCP(dev, ch, "xxx");
```

## 注意事项
- 需要用户提供设备 IP 地址和 HiQnet 节点地址
- 帧格式包含：起始符、长度、版本、序列号、源节点、目标节点、命令码、参数

## 适用型号
- BSS BLU-320
- BSS BLU-160
- BSS BLU-100
- BSS BLU-DAN

## 更新记录
- 2026-04-22: 初始录入，HiQnet 协议框架，具体帧需项目提供
