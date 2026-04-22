---
name: "mdk:xml-ref"
description: "MKControl Project.xml 参考查询：控件类型、属性规范、XML 结构。当用户执行 /mk-xml-controls 或 /mk-xml-structure 命令时调用。"
commands:
  - /mk-xml-controls
  - /mk-xml-structure
---

# XML 参考查询 Skill

## 职责

查询 MKControl Project.xml 格式规范，包括 12 种控件的完整属性、JoinNumber 绑定规则、XML 结构树。

---

## /mk-xml-controls — 控件类型查询

### 触发方式
```
/mk-xml-controls               → 12 种控件总览表
/mk-xml-controls DFCButton     → 按钮完整属性（含子类型）
/mk-xml-controls DFCSlider     → 滑动条属性
/mk-xml-controls DFCPicture    → 图片控件属性
/mk-xml-controls DFCTextbox    → 文本框属性
/mk-xml-controls DFCApp        → 外部应用（注意 camelCase）
```

### 执行步骤

1. 读取 `core/references/controls/controls-spec.md`
2. 根据参数定位对应控件章节
3. 若无参数：输出控件总览表 + JoinNumber 绑定类型汇总
4. 若指定控件名：输出该控件的完整属性表 + XML 示例 + .cht 对应代码

### 输出格式

```
## [控件类型] — [控件名]

### 用途
[控件的使用场景]

### XML 示例
[完整 XML 代码块]

### 核心属性
| 属性 | 位置 | 说明 |
|------|------|------|

### 对应 .cht 事件/函数
[.cht 代码示例]

### 注意事项
[特殊注意点]
```

### 控件速查表

| 控件 | XML Type | JoinNumber 用法 | 说明 |
|------|----------|----------------|------|
| 按钮 | DFCButton | BUTTON_EVENT(tp, N) | 子类型：Normal/Autolock/MutualLock/Login |
| 图片 | DFCPicture | SEND_PICTURE(tp, N, idx) | ImagePictures 多图切换 |
| 文本框 | DFCTextbox | SEND_TEXT(tp, N, str) | 只读显示 |
| 可编辑文本框 | DFCEditTextbox | 双通道：JN + TextSendJN | 用户可输入 |
| 密码框 | DFCPassword | JoinNumber | 配合 LoginBtn |
| 滑动条 | DFCSlider | LEVEL_EVENT + SET_LEVEL（同号双向） | 拖动输入+反馈 |
| 进度条 | DFCTaskBar | SET_LEVEL 单向 | 只读显示 |
| 时间 | DFCTime | 无（TimeType格式显示） | 自动显示系统时间 |
| 视频 | DFCVideo | JoinNumber | 流媒体播放 |
| 外部应用 | DFCApp | joinNumber（camelCase！） | 嵌入外部程序 |
| 页面 | DFCForm | 无 | 页面容器（用 Object 标签） |
| 弹窗 | DFCMessegeToast | 无 | 模态弹窗（注意 Messege 拼写） |

---

## /mk-xml-structure — XML 整体结构查询

### 触发方式
```
/mk-xml-structure              → Project.xml 完整结构树
/mk-xml-structure 颜色          → 颜色格式说明 (#AARRGGBB)
/mk-xml-structure 路径          → 图片路径规范 (.\xxx.png)
/mk-xml-structure DFCForm       → 页面标签完整属性
```

### 执行步骤

1. 读取 `core/references/controls/mk-xml-structure.md`
2. 根据参数定位对应章节
3. 若无参数：输出完整结构树

### 关键规范速查

| 规范 | 说明 |
|------|------|
| **版本** | `Version="4.1.9"`（必须） |
| **分辨率** | 2560×1600（标准 10 英寸） |
| **颜色格式** | `#AARRGGBB`（FF=不透明，00=透明） |
| **图片路径** | `.\xxx.png`（相对路径，点+反斜杠） |
| **页面标签** | `<Object Type="DFCForm">` |
| **弹窗标签** | `<Object Type="DFCMessegeToast">` |
| **控件标签** | `<Control Type="DFCButton">` 等 |
| **DFCApp 异常** | camelCase 属性（left/top/width/height/joinNumber） |
| **JumpPage 关闭弹窗** | `JumpPage="无"` 关闭当前弹窗 |
