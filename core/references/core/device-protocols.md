# 设备协议知识库索引

> 查找设备协议的入口文件。先查本文件（MKControl 自有硬件），再按设备类型查对应分类文件。

---

## MKControl 自有硬件

### TR-0740S 主控器

```
设备类型：主控板（带串口、继电器、红外、IO接口）
地址格式：L:板卡号:类型
  串口：  TR_0740S_COM   = L:2:COM;
  红外：  TR_0740S_IR    = L:2:IR;
  继电器：TR_0740S_RELAY = L:1:RELAY;  // 板卡号视实际配置

常用串口设置：
  SET_COM(TR_0740S_COM, 1, 9600, 8, 0, 10, 0, 232);
```

### TS-9101

```
设备类型：CRLINK 设备（含继电器、串口、红外、IO 等外设）
地址格式：L:设备号:元设备类型
  继电器：relay = L:设备号:RELAY;  // 例：L:1:RELAY
  串口：  com   = L:设备号:COM;
  红外：  ir    = L:设备号:IR;
```


---

## 第三方设备分类文件

| 设备类型 | 文件 | 包含品牌/型号 |
|---------|------|-------------|
| 投影仪 | `references/devices/projectors.md` | PJLink、索尼 VW/HW、爱普生 EB |
| 摄像机 | `references/devices/cameras.md` | VISCA（索尼/松下） |
| 矩阵切换 | `references/devices/matrix.md` | Kramer、顶点/创维 |
| 音频 | `references/devices/audio.md` | BSS BLU |
| 用户新增 | `references/devices/user-added.md` | 对话中由用户提供的协议 |

---

## 未知设备处理规则

1. 先查上方分类文件（包括 `user-added.md`）
2. 若全部查不到 → **停止生成代码**，向用户提问：

```
我没有找到 [设备型号] 的协议文档，请提供：
- 通信方式（串口/TCP/UDP/HTTP）
- 波特率（如使用串口）
- 开机/关机/切换等关键指令（十六进制或ASCII格式）
- 响应格式（如有）
```

3. 收到协议后 → **立即写入 `references/devices/user-added.md`**，再生成代码

> ⚠️ 禁止基于"常见设备可能用这个协议"的假设杜撰指令。错误指令可能导致设备损坏。
