# MDK (MKControl Development Kit) — Codex CLI 配置

## 项目概述

MKControl 中控系统开发工具链，用于生成触摸屏界面（Project.xml）和控制程序（.cht）。

## 核心知识库路径

所有知识库文件位于 `mdk/core/` 目录下：

```
mdk/core/
├── protocols/          ← 设备协议库（投影仪/窗帘/空调/摄像机/矩阵等）
│   ├── _index.md       ← 协议总索引（先查这里）
│   ├── projector/      ← 投影仪协议
│   ├── curtain/        ← 窗帘电机协议
│   ├── ac/             ← 空调红外协议
│   ├── camera/         ← 摄像机协议
│   └── matrix/         ← 矩阵切换器协议
├── references/
│   ├── core/
│   │   ├── syntax-rules.md    ← .cht 语法约束（必读）
│   │   ├── code-patterns.md   ← 12 种代码模式（必读）
│   │   └── device-types.md    ← 设备类型总览
│   └── controls/
│       ├── controls-spec.md   ← 13 种 XML 控件规范
│       └── xml-structure.md   ← Project.xml 结构规范
├── docs/
│   └── 系统函数库/     ← 所有系统函数文档（用前必查）
└── scripts/
    ├── validate.py         ← .cht 语法校验（14 项）
    └── cross_validate.py   ← XML ↔ .cht 交叉校验
```

## 操作规范

### 生成 .cht 文件前

1. 读取 `mdk/core/references/core/syntax-rules.md`
2. 读取 `mdk/core/references/core/code-patterns.md`
3. 查询用到的设备协议：读取 `mdk/core/protocols/_index.md` → 找到对应文件
4. 查询用到的系统函数：读取 `mdk/core/docs/系统函数库/对应分类.md`

### 生成 Project.xml 前

1. 读取 `mdk/core/references/controls/controls-spec.md`
2. 读取 `mdk/core/references/controls/xml-structure.md`

### 生成后

运行校验：
```bash
python3 mdk/core/scripts/validate.py output.cht
python3 mdk/core/scripts/cross_validate.py Project.xml output.cht
```

## 关键规则（必须遵守）

1. **块顺序**：DEFINE_DEVICE → DEFINE_CONSTANT → DEFINE_VARIABLE → DEFINE_FUNCTION → DEFINE_TIMER → DEFINE_START → DEFINE_EVENT
2. **DEFINE_CONSTANT**：只允许整型常量，字符串放 DEFINE_VARIABLE
3. **变量初始化**：所有变量必须赋初值
4. **大小写**：`if/else/for/int/string` 小写；`SEND_COM/ON_RELAY/SET_BUTTON` 大写
5. **LEVEL_EVENT**：支持（已验证），用于滑条输入
6. **WAIT 语法**：`WAIT 毫秒 { ... }` 不是 `WAIT(毫秒)`
7. **XML 版本**：`Version="4.1.9"`（固定）
8. **DFCApp 特殊**：属性用 camelCase（`left`/`top`/`joinNumber`）

## 协议未知时

停止生成，要求用户提供：
- 通信方式（串口/TCP/UDP/红外）
- 波特率（串口时）
- 具体指令

**绝对禁止猜测指令格式。**

## JoinNumber 规则

- XML 控件的 JoinNumber 必须在 .cht 中有对应事件处理
- .cht 中的 BUTTON_EVENT/LEVEL_EVENT 必须在 XML 中有对应控件
- 不同功能不共享同一个 JoinNumber（除非有意复用 SET_BUTTON 反馈）
