# 投影仪 - 爱普生 (EB 系列)

## 基本信息
- 设备类型：投影仪
- 通信方式：串口RS232
- 波特率：9600
- 数据位/停止位/校验：8/1/无

## 设备声明
```
SET_COM(M_COM, ch, 9600, 8, 0, 10, 0, 232);
```

## 指令表
| 功能 | 指令 | 说明 |
|------|------|------|
| 开机 | `PWR ON\r` | |
| 关机 | `PWR OFF\r` | |
| 查询电源 | `PWR?\r` | 返回 PWR=01/00/02/03 |
| 信号源HDMI1 | `SOURCE 30\r` | |
| 信号源HDMI2 | `SOURCE A0\r` | |
| 信号源VGA1 | `SOURCE 11\r` | |
| 静音开 | `MUTE ON\r` | |
| 静音关 | `MUTE OFF\r` | |

## 代码示例
```
// 开机
SEND_COM(M_COM, ch, "PWR ON\r");

// 关机
SEND_COM(M_COM, ch, "PWR OFF\r");

// 查询（需在 DATA_EVENT 中处理返回）
SEND_COM(M_COM, ch, "PWR?\r");
```

## 适用型号
- 爱普生 EB-X/W/L/G 系列
- 爱普生 CB 系列

## 更新记录
- 2026-04-22: 初始录入，来源：旧协议库迁移
