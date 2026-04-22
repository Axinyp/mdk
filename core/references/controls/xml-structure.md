# Project.xml 结构规范（v4.1.9）

> 来源：401 会议室 Project.xml 实际文件分析

---

## 整体结构树

```xml
<?xml version="1.0" encoding="utf-8"?>
<Project Name="项目名称" Version="4.1.9"
         StartForm="启动页面名"
         DeviceIndex="16"
         IsOpenProject="True"
         MachineID="10">

  <!-- 页面1（含弹窗，都用 Object 标签） -->
  <Object Name="帮助指引" Type="DFCForm" ID="1" X="0" Y="0" Width="2560" Height="1600"
          IsActive="False" DisplayTime="" Radius=""
          RemoteControlIP="" RemoteControlAccount="" RemoteControlPassWord="">
    <Style Visible="True" Enable="True" BackColor="#FFFFFFFF"
           BkImage=".\背景.png" Opacity="1" ModalLayerOpacity="1"
           IsChecklayer="False" LayerColor="#A0000000" />
    <Appearance Grid="False" Border="False" HomePage="True"
                LeftJumpPage="" RightJumpPage="" TopJumpPage="" BottomJumpPage=""
                LeftCmdType="" RightCmdType="" TopCmdType="" BottomCmdType="" />
    <MatrixVideo MatrixWidth="0" MatrixHeight="0" MatrixLayout="Layout1"
                 MatrixVideoType="Splicer" MatrixName="" MatrixUrl=""
                 VideoCount="1" PreviewChannel="" VideoColumns="4" VideoRows="4"
                 MatrixOpticalVideoName="" MatrixOpticalVideoUrl="" MatrixOpticalVideoCount="1" />

    <!-- 控件（平铺，无嵌套层级） -->
    <Control Name="时间" Type="DFCTime" ID="54" X="97" Y="21" Width="286" Height="149" BlockWidth="0" BlockHeight="0">
      ...
    </Control>
    <Control Name="按钮" Type="DFCButton" ID="53" X="0" Y="0" Width="2558" Height="1598" BlockWidth="0" BlockHeight="0">
      ...
    </Control>
  </Object>

  <!-- 页面2 -->
  <Object Name="主页" Type="DFCForm" ID="2" ...>
    ...
  </Object>

  <!-- 弹窗（也是 Object，Type=DFCMessegeToast） -->
  <Object Name="确认弹窗" Type="DFCMessegeToast" ID="99" X="600" Y="400" Width="1360" Height="800"
          IsActive="False" DisplayTime="10" Radius="20" ...>
    ...
  </Object>

</Project>
```

---

## Project 根标签属性

| 属性 | 说明 | 典型值 |
|------|------|--------|
| `Name` | 项目名称 | "401会议室改造" |
| `Version` | 格式版本 | **"4.1.9"**（必须填此值） |
| `StartForm` | 启动页面名（填 Object 的 Name） | "帮助指引" 或 "主页" |
| `DeviceIndex` | 触摸屏设备板卡号 | "16" |
| `IsOpenProject` | 是否开放项目 | "True" |
| `MachineID` | 机器ID | "10" |

---

## Object（页面/弹窗）标签属性

| 属性 | 说明 |
|------|------|
| `Name` | 页面名称（被 JumpPage/DialogPage 引用） |
| `Type` | `DFCForm`（普通页面）或 `DFCMessegeToast`（弹窗） |
| `ID` | 全局唯一整数（不重复） |
| `X`, `Y` | 页面位置，通常 0,0 |
| `Width`, `Height` | 分辨率，通常 2560×1600 |
| `IsActive` | 是否激活（运行时由系统控制） |
| `DisplayTime` | 弹窗自动关闭秒数（页面留空） |
| `Radius` | 页面圆角（通常留空） |
| `RemoteControlIP/Account/PassWord` | 远程控制参数（按需填写） |

### Object > Style 子标签
| 属性 | 说明 |
|------|------|
| `BackColor` | 背景色（ARGB，如 #FFFFFFFF） |
| `BkImage` | 背景图片路径（相对路径，如 `.\背景.png`） |
| `Opacity` | 页面透明度（0~1） |
| `ModalLayerOpacity` | 弹窗遮罩透明度（0~1） |
| `IsChecklayer` | 是否显示检查层 |
| `LayerColor` | 遮罩层颜色（如 #A0000000） |

### Object > Appearance 子标签
| 属性 | 说明 |
|------|------|
| `Grid` | 显示网格（设计时） |
| `Border` | 显示边框 |
| `HomePage` | True = 主页（首次显示的页面） |
| `LeftJumpPage` 等 | 滑动手势跳转页面 |

---

## Control 标签（所有非页面控件）

> 注意：页面/弹窗用 `<Object>` 标签，页面内的控件用 `<Control>` 标签

### Control 根属性
| 属性 | 说明 |
|------|------|
| `Name` | 控件名称（如 "按钮1"、"时间控件"） |
| `Type` | 控件类型（如 DFCButton、DFCSlider 等） |
| `ID` | 全局唯一整数 |
| `X`, `Y`, `Width`, `Height` | 位置和尺寸 |
| `BlockWidth`, `BlockHeight` | 滑块宽高（DFCSlider 专用，其他填 0） |

### Control > Appearance 子标签
| 属性 | 说明 |
|------|------|
| `Visible` | True/False 是否显示 |
| `Enable` | True/False 是否可交互 |
| `Border` | 边框开关 |
| `BorderType` | "2D"/"3D" |
| `BorderColor` | 边框色 ARGB |
| `BtnType` | 按钮子类型（NormalBtn/MutualLockBtn 等） |
| `Opacity` | 透明度 |
| `IsLock` | 编辑器锁定（不影响运行） |

### Control > Style 子标签（主要属性）
| 属性 | 说明 |
|------|------|
| `FontFamily` | 字体（D-DIN / SourceHanSansCN-Regular 等） |
| `FontSize` | 字号（px） |
| `TextColor` | 文字色 |
| `PressTextColor` | 按下文字色 |
| `NormalColor` | 常态背景色 |
| `PressColor` | 按下背景色 |
| `NormalImage` | 常态图（`.\xxx.png`） |
| `PressImage` | 按下图 |
| `ImageStretch` | False=自适应/True=拉伸 |
| `Radius` | 圆角半径 |
| `HorizontalContentAlignment` | Left/Center/Right |
| `VerticalCententAlignment` | Top/Center/Bottom（注意拼写：Centent） |
| `Autolock` | 自锁（True/False 或留空） |
| `MutualLockGroup` | 互斥组名 |
| `TextSendJoinNumber` | 关联文本框的逻辑号 |
| `IsLoginBtn` | 登录按钮标记 |
| `ImagePictures` | DFCPicture 多图列表（逗号分隔） |
| `ImgItemIndex` | DFCPicture 当前索引（0开始） |
| `TimeType` | DFCTime 时间格式（HH:mm 等） |
| `MinValue`, `MaxValue`, `Percent` | DFCSlider 范围和当前值 |
| `IsVertical` | DFCSlider 方向 |
| `ElapsedColor`, `BackgroundColor` | DFCSlider 颜色 |
| `BlockColor`, `BlockRadius` | DFCSlider 滑块样式 |

### Control > SliderLocationStyle 子标签
DFCSlider 专用，显示滑块旁边的数值标签：
```xml
<SliderLocationStyle LocationMargin="" LocationWidth="" LocationHeight=""
                     LocationFontFamily="" LocationFontSize=""
                     LocationForeground="" LocationBackground=""
                     LocationHorizontalContentAlignment="Center"
                     LocationVerticalContentAlignment="Center"
                     LocationCtrlBorderEnable="False"
                     LocationBorderType="2D" LocationBorderColor=""
                     LocationRadius="" />
```

### Control > Event 子标签
| 属性 | 说明 |
|------|------|
| `JoinNumber` | 逻辑连接号（关键！对应 .cht 中的事件号） |
| `JumpPage` | 跳转页面名（留空=不跳转，"无"=关闭弹窗） |
| `DialogPage` | 触发弹窗名称 |
| `Autolock` | True/False（也可在 Style 中设） |
| `MutualLockGroup` | 互斥组名 |
| `DelayTime` | 延迟执行毫秒数（通常 0） |
| `CmdType` | 命令类型（通常留空） |
| `ButtonSoundSource` | 点击音效路径 |

---

## 路径规范

- 图片使用**相对路径**：`.\xxx.png`（单反斜杠前置点）
- 路径根目录 = Project.xml 所在目录
- 不支持绝对路径（移植时会失效）

---

## 颜色格式

MKControl 使用 ARGB 8位十六进制格式：
```
#AARRGGBB
AA = 透明度（FF=不透明，00=完全透明）
RR = 红色分量
GG = 绿色分量
BB = 蓝色分量
```

常用色值：
| 颜色 | 值 |
|------|---|
| 白色不透明 | `#FFFFFFFF` |
| 黑色不透明 | `#FF000000` |
| 完全透明 | `#00000000` |
| 半透明黑遮罩 | `#A0000000` |

---

## 分辨率

| 设备 | 分辨率 |
|------|--------|
| 标准触摸屏（10英寸） | 2560 × 1600 |
| 其他分辨率 | 按实际设备设置 |

---

## DFCApp 特殊说明

DFCApp 控件不使用 `<Control>` 标签结构，其所有属性直接写在单个标签上，且属性名全部为 **camelCase**（与其他控件的 PascalCase 不同）：

```xml
<DFCApp Name="外部应用" ID="唯一整数"
        left="0" top="0" width="1920" height="1080"
        opacity="1" visible="True"
        AppPath="C:\xxx\app.exe" AppParam="" AppWindowType="Fullscreen"
        IsEmbed="True"
        hasBorder="False" borderColor="#FF000000" borderStyle="2D" cornerRadius="0"
        bgColor="#FF000000" normalImage="" imageFillType="Stretch"
        joinNumber="0" clickSound="" jumpPage="" />
```

---

## 控件 ID 分配原则

- ID 在整个项目中唯一（包括跨页面）
- 通常按出现顺序递增分配
- 建议保留一定间隔（如每页 100 个）便于后续插入
