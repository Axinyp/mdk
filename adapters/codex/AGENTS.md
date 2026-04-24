# MDK (MKControl Development Kit) — Codex CLI 配置

## 项目概述

MKControl 中控系统开发工具链，用于生成触摸屏界面（Project.xml）和控制程序（.cht）。

## 核心知识库路径

所有知识库文件位于 `mdk/core/` 目录下：

```
mdk/core/
├── skills/mkcontrol/SKILL.md    ← 唯一入口（流程+规则+路径指针）
├── templates/                    ← 生成模板（XML + CHT 骨架）
│   ├── _index.md                 ← 模板索引 + 默认值
│   ├── xml/*.tpl                 ← XML 控件模板（8 个）
│   └── cht/
│       └── simple-program.cht.tpl ← CHT 骨架（对齐中控软件官方模板）
├── protocols/                    ← 设备协议库
│   ├── _index.md                 ← 协议总索引（先查这里）
│   └── projector/curtain/ac/...  ← 按分类存放
├── references/
│   ├── controls/
│   │   ├── widgets/_index.md     ← 15 种控件索引
│   │   ├── widgets/DFCButton.md  ← 按控件拆分（按需读取）
│   │   └── xml-structure.md      ← Project.xml 结构规范
│   └── core/
│       ├── patterns/_index.md    ← 10 种代码模式索引
│       ├── patterns/*.md         ← 按模式拆分（按需读取）
│       └── syntax-rules.md       ← .cht 语法约束（必读）
├── docs/
│   └── 系统函数库/
│       ├── 常用/*.md             ← 日常生成用到的函数（16 个）
│       └── 专用硬件/*.md         ← 特定设备函数（10 个）
└── scripts/
    ├── validate.py               ← .cht 语法校验（10 项）
    └── cross_validate.py         ← XML ↔ .cht 交叉校验
```

## 操作规范

### 生成前：按需加载，禁止全量读取

1. 读取 `templates/_index.md` 了解模板和默认值
2. 读取 `protocols/_index.md` 匹配设备协议 → 命中则读对应文件
3. 读取 `references/controls/widgets/_index.md` → 只读用到的控件文件
4. 读取 `references/core/patterns/_index.md` → 只读匹配的模式文件

### 生成 .cht 文件

1. 读取 `templates/cht/simple-program.cht.tpl` 获取骨架
2. 读取 `templates/cht/devices.md` 获取设备声明规则
3. 读取 `templates/cht/events.md` 获取事件模板
4. 替换 `{{变量}}` 占位符

### 生成 Project.xml

1. 读取 `templates/xml/project.xml.tpl` + 需要的控件模板
2. 替换 `{{变量}}` 占位符

### 生成后

运行校验：
```bash
python3 mdk/core/scripts/validate.py output.cht
python3 mdk/core/scripts/cross_validate.py Project.xml output.cht
```

## 关键规则（必须遵守）

1. **块顺序**：DEFINE_DEVICE → DEFINE_COMBINE → DEFINE_CONSTANT → DEFINE_VARIABLE → DEFINE_FUNCTION → DEFINE_TIMER → DEFINE_START → DEFINE_EVENT → DEFINE_PROGRAME
2. **即使内容为空，也保留所有块**（对齐中控软件官方模板）
3. **DEFINE_CONSTANT**：只允许整型常量，字符串放 DEFINE_VARIABLE
4. **变量初始化**：所有变量必须赋初值
5. **大小写**：`if/else/for/int/string` 小写；`SEND_COM/ON_RELAY/SET_BUTTON` 大写
6. **LEVEL_EVENT**：支持（已验证），用于滑条输入
7. **WAIT 语法**：`WAIT 毫秒 { ... }` 不是 `WAIT(毫秒)`
8. **XML 版本**：`Version="4.1.9"`（固定）
9. **DFCApp 特殊**：属性用 camelCase（`left`/`top`/`joinNumber`）
10. **进度条**：XML Type 是 `DFCProgress`（不是 DFCTaskBar）
11. **滑条范围**：默认 0-65535

## 协议未知时

停止生成，要求用户提供：
- 通信方式（串口/TCP/UDP/红外）
- 波特率（串口时）
- 具体指令

**绝对禁止猜测指令格式。**
