# 空调 - 格力 (红外控制)

## 基本信息
- 设备类型：空调
- 通信方式：红外（通过 TR-0740S 红外模块发射）

## 设备声明
```
// TR-0740S 红外通道声明（在 DEFINE_DEVICE 中）
TR_0740S_IR2 = L:2:IR;  // 0740S 的红外2
TR_0740S_IR3 = L:3:IR;  // 0740S 的红外3
```

## 指令格式（MKControl UserIRDB）

MKControl 使用 `IRCODE<"UserIRDB:...">` 格式引用用户录制的红外码库：

```
SEND_IRCODE(设备, 通道, IRCODE<"UserIRDB:{组}:{子组}:{品牌}:{学习时间戳}:{指令ID}">`);
```

401 项目实际格式：
```
IRCODE<"UserIRDB:meeting room:F401:GREE:T20211021105429:{温度}_{模式}">
```

## 指令表（401 项目格式，温度16-30度）
| 功能 | 指令 | 说明 |
|------|------|------|
| 制冷 16度 | `UserIRDB:meeting room:F401:GREE:T20211021105429:16_1` | 模式1=制冷 |
| 制冷 17度 | `UserIRDB:meeting room:F401:GREE:T20211021105429:17_1` | |
| 制冷 18度 | `UserIRDB:meeting room:F401:GREE:T20211021105429:18_1` | |
| 制冷 19度 | `UserIRDB:meeting room:F401:GREE:T20211021105429:19_1` | |
| 制冷 20度 | `UserIRDB:meeting room:F401:GREE:T20211021105429:20_1` | |
| 制冷 21度 | `UserIRDB:meeting room:F401:GREE:T20211021105429:21_1` | |
| 制冷 22度 | `UserIRDB:meeting room:F401:GREE:T20211021105429:22_1` | |
| 制冷 23度 | `UserIRDB:meeting room:F401:GREE:T20211021105429:23_1` | |
| 制冷 24度 | `UserIRDB:meeting room:F401:GREE:T20211021105429:24_1` | |
| 制冷 25度 | `UserIRDB:meeting room:F401:GREE:T20211021105429:25_1` | |
| 制冷 26度 | `UserIRDB:meeting room:F401:GREE:T20211021105429:26_1` | |
| 制冷 27度 | `UserIRDB:meeting room:F401:GREE:T20211021105429:27_1` | |
| 制冷 28度 | `UserIRDB:meeting room:F401:GREE:T20211021105429:28_1` | |
| 制冷 29度 | `UserIRDB:meeting room:F401:GREE:T20211021105429:29_1` | |
| 制冷 30度 | `UserIRDB:meeting room:F401:GREE:T20211021105429:30_1` | |

## 代码示例
```
// 格力空调制冷25度（发送到两个红外通道）
SEND_IRCODE(TR_0740S_IR2, 1, IRCODE<"UserIRDB:meeting room:F401:GREE:T20211021105429:25_1">);
SEND_IRCODE(TR_0740S_IR3, 1, IRCODE<"UserIRDB:meeting room:F401:GREE:T20211021105429:25_1">);
```

## 重要说明
- 红外码必须事先通过 MKControl 软件学习并录入 UserIRDB
- 每个项目的红外码路径（group:subgroup:brand:timestamp）会不同
- 新项目需要用户提供已学习好的 UserIRDB 路径
- 格式：`UserIRDB:{自定义组}:{自定义子组}:{品牌}:{学习时间戳}:{指令标识}`

## 适用型号
- 格力空调（所有型号，通过红外学习）
- 其他红外控制空调品牌（需修改 IRCODE 路径中的品牌和时间戳）

## 更新记录
- 2026-04-22: 初始录入，来源：401 会议室实际生产代码提取（格力空调，制冷模式16-30度）
