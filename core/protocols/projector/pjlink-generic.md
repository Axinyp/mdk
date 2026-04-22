# 投影仪 - 通用 PJLink 协议

## 基本信息
- 设备类型：投影仪
- 通信方式：TCP
- TCP端口：4352

## 设备声明
```
// 在 DEFINE_START 或按需连接
CONNECT_TCP(tp, 1, ip_addr, 4352);
```

## 指令表
| 功能 | 指令 | 说明 |
|------|------|------|
| 开机 | `%1POWR 1\r` | Class 1 电源开 |
| 关机 | `%1POWR 0\r` | Class 1 电源关 |
| 查询电源 | `%1POWR ?\r` | 返回 %1POWR=1/0/2/3 |
| 查询输入 | `%1INPT ?\r` | 返回当前信号源 |
| 切换输入1 | `%1INPT 11\r` | RGB 1 |
| 切换输入3 | `%1INPT 31\r` | HDMI 1 |

## 代码示例
```
// 开机
SEND_TCP(dev, ch, "%1POWR 1\r");

// 关机
SEND_TCP(dev, ch, "%1POWR 0\r");

// 查询状态（需在 DATA_EVENT 中处理返回）
SEND_TCP(dev, ch, "%1POWR ?\r");
```

## 适用型号
- 所有支持 PJLink Class 1 标准的投影仪
- 爱普生、NEC、日立、松下等主流品牌

## 更新记录
- 2026-04-22: 初始录入，来源：PJLink Class 1 标准协议
