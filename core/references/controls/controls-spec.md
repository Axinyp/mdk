# MKControl 控件完整属性规范（13 种控件）

> 来源：基本控件分类.md + 401 Project.xml 实测数据

---

## 控件总览

| # | 控件类型 | XML Type | 交互性 | JoinNumber 用法 |
|---|---------|----------|--------|----------------|
| 1 | 按钮 | DFCButton | 可点击 | BUTTON_EVENT + SET_BUTTON |
| 2 | 图片 | DFCPicture | 多状态显示 | SEND_PICTURE 切换索引 |
| 3 | 文本框 | DFCTextbox | 显示/反馈 | SEND_TEXT |
| 4 | 可编辑文本框 | DFCEditTextbox | 用户输入 | JoinNumber + TextSendJoinNumber（双通道） |
| 5 | 密码输入框 | DFCPassword | 密码输入 | JoinNumber |
| 6 | 滑动条 | DFCSlider | 可拖动 | LEVEL_EVENT 输入 + SET_LEVEL 反馈（双向同号） |
| 7 | 进度条 | DFCTaskBar | 只读进度 | SET_LEVEL 单向 |
| 8 | 时间 | DFCTime | 自动时钟 | 仅显示，TimeType="HH:mm" |
| 9 | 视频 | DFCVideo | 流媒体播放 | JoinNumber |
| 10 | 外部应用 | DFCApp | 嵌入外部程序 | **注意：属性全部 camelCase（与其他控件不同）** |
| 11 | 页面 | DFCForm | 页面容器 | 无 JoinNumber |
| 12 | 弹窗 | DFCMessegeToast | 模态弹窗 | DisplayTime 自动关闭 |

---

## 1. 按钮（DFCButton）

### 子类型（BtnType）
| BtnType | 行为 | 典型用途 | .cht 模式 |
|---------|------|---------|----------|
| `NormalBtn` | 按下触发，松开无事件 | 灯光全开/全关、窗帘开停关 | `PUSH() { ... }` |
| `AutolockBtn` (Autolock=True) | PUSH=锁定/执行, RELEASE=解锁 | 电源通道、静音、单路灯光 | `PUSH(){ on } RELEASE(){ off }` 或按状态反转 |
| `MutualLockBtn` | 同组互斥（点一个其他释放） | 场景切换、信号源选择 | `PUSH(){ ... SET_BUTTON 互斥 }` |
| `LoginBtn` | 登录专用触发 | 密码验证、JumpPage 跳转 | 配合 DFCPassword 使用 |

### XML 结构
```xml
<Control Name="按钮名" Type="DFCButton" ID="唯一整数" X="0" Y="0" Width="200" Height="80" BlockWidth="0" BlockHeight="0">
  <Appearance Visible="True" Enable="True" Border="False" BorderType="3D" BorderColor="#FFCD6633"
              BtnType="NormalBtn" Opacity="1" IsLock="False" />
  <Style FontFamily="SourceHanSansCN-Regular" FontSize="25" FontStyle="Normal" FontWeight="Normal"
         Text="" TextPos="middle" TextColor="#FF000000" PressTextColor="#FF000000"
         IsLock="False" IsDrag="False" IsDropSource="False" IsTouchSource="False"
         PressColor="#FFB86D3A" NormalColor="#FFD1A282"
         NormalImage=".\按钮普通.png" PressImage=".\按钮按下.png"
         ImageStretch="False"
         Autolock="" MutualLockGroup=""
         TextSendJoinNumber="0" IsLoginText="False" IsLoginBtn=""
         HorizontalContentAlignment="Center" VerticalCententAlignment="Center"
         Radius="0"
         ImagePictures="" OldImagePictures="" ImgItemIndex="0" ImgPItemIndex="0"
         TimeType="" VideoURL="" BtnBackgroundColor="" IsKeepPwdMind=""
         IsDisplayedPower="False" IsVertical="" IsEdit=""
         ElapsedColor="" MaxValue="" MinValue="" Percent="" BackgroundColor=""
         BlockColor="" BlockPicture="" SliderPicture="" SliderTextPicture="" BlockRadius=""
         ValueLocation="" IsContainsPic="False" ImageColors="" Icon="" IconImage="" IconAilgn="" />
  <SliderLocationStyle />
  <Event DialogPage="" JumpPage="" JoinNumber="103" DelayTime="0" Autolock="False"
         MutualLockGroup="" CmdType="" ButtonSoundSource="" />
</Control>
```

### 核心属性说明
| 属性 | 位置 | 说明 |
|------|------|------|
| `Name` | Control | 控件名称（唯一标识，编辑器显示用） |
| `ID` | Control | 系统内部唯一整数 ID，不可重复 |
| `X`, `Y` | Control | 左上角坐标（像素） |
| `Width`, `Height` | Control | 宽高（像素） |
| `BtnType` | Appearance | 按钮类型（NormalBtn/MutualLockBtn/LoginBtn） |
| `Autolock` | Appearance/Event | True = 自锁按钮（等效 AutolockBtn） |
| `NormalImage` | Style | 常态背景图（相对路径，如 `.\xxx.png`） |
| `PressImage` | Style | 按下背景图 |
| `NormalColor` | Style | 常态背景色（图片+色可共存，图片覆盖色） |
| `PressColor` | Style | 按下背景色 |
| `Radius` | Style | 圆角半径（0=直角） |
| `MutualLockGroup` | Style/Event | 互斥组名，同名按钮互斥 |
| `JoinNumber` | Event | 逻辑连接号（对应 .cht 中 BUTTON_EVENT(tp, N)） |
| `JumpPage` | Event | 点击后跳转页面（填页面名称） |
| `DialogPage` | Event | 点击后弹出弹窗（填弹窗名称） |
| `TextSendJoinNumber` | Style | 绑定文本框的逻辑号（LoginBtn 用） |

---

## 2. 图片（DFCPicture）

```xml
<Control Name="图片名" Type="DFCPicture" ID="唯一整数" X="0" Y="0" Width="100" Height="100" BlockWidth="0" BlockHeight="0">
  <Appearance Visible="True" Enable="True" Border="False" BorderType="2D" BorderColor=""
              Opacity="1" IsLock="False" />
  <Style NormalImage=".\默认图.png" PressImage=""
         ImagePictures=".\状态0.png,.\状态1.png,.\状态2.png"
         ImgItemIndex="0"
         ImageStretch="False" IsDrag="False" IsTouchSource="False"
         Autolock="False" MutualLockGroup="" JumpPage="" DialogPage=""
         ButtonSoundSource="" Radius="0"
         ... />
  <Event JoinNumber="150" ... />
</Control>
```

| 属性 | 说明 |
|------|------|
| `NormalImage` | 默认显示图片路径 |
| `ImagePictures` | 多图切换集合（逗号分隔），用于 SEND_PICTURE |
| `ImgItemIndex` | 当前显示索引（0开始），SEND_PICTURE(tp, N, index) 控制 |
| `ImageStretch` | False=自适应等比；True=拉伸铺满 |
| `JoinNumber` | 对应 .cht 中 SEND_PICTURE(tp, N, index) 的 N |

---

## 3. 文本框（DFCTextbox）

```xml
<Control Name="文本名" Type="DFCTextbox" ID="唯一整数" X="0" Y="0" Width="200" Height="60" BlockWidth="0" BlockHeight="0">
  <Appearance Visible="True" Enable="True" Border="False" Opacity="1" IsLock="True" />
  <Style FontFamily="D-DIN" FontSize="48" TextColor="#FFAAAAAA"
         NormalColor="#00000000" Text=""
         HorizontalContentAlignment="Left" VerticalCententAlignment="Center"
         ImageStretch="False" IsDrag="False" Radius="0" ... />
  <Event JoinNumber="200" ... />
</Control>
```

| 属性 | 说明 |
|------|------|
| `Text` | 静态文本（生成时为空，由 SEND_TEXT 更新） |
| `JoinNumber` | 对应 .cht 中 SEND_TEXT(tp, N, 文本) 的 N |
| `TimeType` | 用于 DFCTime 子类（HH:mm、yyyy-MM-dd 等格式） |

---

## 4. 可编辑文本框（DFCEditTextbox）

| 属性 | 说明 |
|------|------|
| `JoinNumber` | 接收文本的逻辑号 |
| `TextSendJoinNumber` | 用户输入并发送时使用的逻辑号（双通道） |
| `IsEdit` | True = 可手动输入 |
| `MaxValue` / `MinValue` | 输入字符数限制 |
| `IsKeepPwdMind` | 是否记住输入 |

---

## 5. 密码输入框（DFCPassword）

| 属性 | 说明 |
|------|------|
| `JoinNumber` | 密码验证逻辑号 |
| `IsEdit` | True = 可输入 |
| `Text` | 提示文本 |

---

## 6. 滑动条（DFCSlider）

```xml
<Control Name="音量条" Type="DFCSlider" ID="唯一整数" X="0" Y="0" Width="600" Height="60" BlockWidth="30" BlockHeight="30">
  <Appearance Visible="True" Enable="True" IsLock="False" Opacity="1" />
  <Style MinValue="0" MaxValue="100" Percent="50"
         IsVertical="False"
         BackgroundColor="#FF333333" ElapsedColor="#FF00AAFF"
         BlockColor="#FFFFFFFF" BlockRadius="15" BlockWidth="30" BlockHeight="30"
         NormalColor="#00000000" Radius="5"
         ... />
  <SliderLocationStyle LocationMargin="" LocationWidth="" LocationHeight=""
                       LocationFontFamily="" LocationFontSize=""
                       LocationForeground="" LocationBackground=""
                       LocationHorizontalContentAlignment="Center"
                       LocationVerticalContentAlignment="Center"
                       LocationCtrlBorderEnable="False" LocationBorderType="2D"
                       LocationBorderColor="" LocationRadius="" />
  <Event JoinNumber="1000" ... />
</Control>
```

| 属性 | 说明 |
|------|------|
| `JoinNumber` | 双向绑定：LEVEL_EVENT(tp, N) 接收用户拖动，SET_LEVEL(tp, N, val) 推送反馈 |
| `MinValue` / `MaxValue` | 滑条范围 |
| `Percent` | 初始百分比 |
| `IsVertical` | False=水平，True=垂直 |
| `BlockWidth/Height` | 拖动块大小 |
| `ElapsedColor` | 已滑动部分颜色 |

---

## 7. 进度条（DFCTaskBar）

| 属性 | 说明 |
|------|------|
| `JoinNumber` | 只接收 SET_LEVEL(tp, N, val)，不产生 LEVEL_EVENT |
| `MinValue` / `MaxValue` | 进度范围 |
| `CurrentValue` | 当前值 |
| `ProgressDirection` | 从左到右 / 从下到上 |
| `ProgressColor` | 进度颜色 |

---

## 8. 时间（DFCTime）

```xml
<Control Name="时间" Type="DFCTime" ID="唯一整数" X="97" Y="21" Width="286" Height="149" BlockWidth="0" BlockHeight="0">
  <Style FontFamily="D-DIN" FontSize="108" TextColor="#FFFFFFFF"
         NormalColor="#00000000" TimeType="HH:mm" ... />
  <Event JoinNumber="0" ... />
</Control>
```

| 属性 | 说明 |
|------|------|
| `TimeType` | 时间格式：`HH:mm`（小时:分）、`HH:mm:ss`、`yyyy-MM-dd`、`dddd`（星期） |
| `JoinNumber` | 通常为 0（仅显示，不联动） |

---

## 9. 视频（DFCVideo）

| 属性 | 说明 |
|------|------|
| `VideoURL` | 视频/流媒体地址 |
| `AutoPlay` | 打开页面自动播放 |
| `IsLoop` | 循环播放 |
| `IsMute` | 静音播放 |
| `JoinNumber` | 联动逻辑号 |

---

## 10. 外部应用（DFCApp）

> **⚠️ 重要：DFCApp 的所有属性名使用 camelCase，与其他所有控件的 PascalCase 不同**

```xml
<Control Name="xxx" Type="DFCApp" ID="唯一整数"
         left="100" top="200" width="800" height="600"
         opacity="1" visible="True"
         AppPath="C:\Program Files\xxx.exe"
         AppParam="" AppWindowType="Fullscreen" IsEmbed="True"
         hasBorder="False" borderColor="#FF000000" borderStyle="2D" cornerRadius="0"
         bgColor="#FF000000" normalImage="" imageFillType="Stretch"
         joinNumber="0" clickSound="" jumpPage="" />
```

| camelCase 属性 | 含义 |
|---------------|------|
| `left`, `top` | 坐标（⚠️ 不是 X/Y） |
| `width`, `height` | 尺寸（⚠️ 不是 Width/Height） |
| `joinNumber` | 逻辑连接号（⚠️ 不是 JoinNumber） |
| `opacity` | 透明度 |
| `hasBorder` | 边框开关 |
| `cornerRadius` | 圆角 |

---

## 11. 页面（DFCForm）

```xml
<Object Name="页面名" Type="DFCForm" ID="唯一整数"
        X="0" Y="0" Width="2560" Height="1600"
        IsActive="False" DisplayTime="" Radius=""
        RemoteControlIP="" RemoteControlAccount="" RemoteControlPassWord="">
  <Style Visible="True" Enable="True" BackColor="#FFFFFFFF"
         BkImage=".\背景图.png" Opacity="1" ModalLayerOpacity="1"
         IsChecklayer="False" LayerColor="#A0000000" />
  <Appearance Grid="False" Border="False" HomePage="False"
              LeftJumpPage="" RightJumpPage="" TopJumpPage="" BottomJumpPage=""
              LeftCmdType="" RightCmdType="" TopCmdType="" BottomCmdType="" />
  <MatrixVideo MatrixWidth="0" MatrixHeight="0" MatrixLayout="Layout1" ... />
  <!-- 子控件在这里 -->
</Object>
```

| 属性 | 说明 |
|------|------|
| `Name` | 页面名称（被 JumpPage 引用时使用此名） |
| `StartForm` | Project 根标签的属性，指定启动页面名 |
| `HomePage` | True = 主页（仅一个页面为 True） |
| `BkImage` | 背景图路径（相对路径） |
| `DisplayTime` | 弹窗自动关闭时间（秒），正常页面留空 |

---

## 12. 弹窗（DFCMessegeToast）

> 注：系统原始拼写为 `DFCMessegeToast`（非 MessageToast），生成时必须使用此拼写

```xml
<Object Name="弹窗名" Type="DFCMessegeToast" ID="唯一整数"
        X="600" Y="400" Width="1360" Height="800"
        IsActive="False" DisplayTime="10" Radius="20"
        RemoteControlIP="" ...>
  <Style BackColor="#FFFFFFFF" BkImage="" Opacity="1" ModalLayerOpacity="0.5" ... />
  <!-- 子控件 -->
</Object>
```

| 属性 | 说明 |
|------|------|
| `DisplayTime` | 自动关闭倒计时（秒），0 = 手动关闭 |
| `ModalLayerOpacity` | 遮罩层透明度（0=透明，1=不透明） |
| 触发方式 | 按钮的 `DialogPage` 属性填弹窗名称 |

---

## JoinNumber 绑定类型汇总（6 种通道）

| 通道类型 | 方向 | XML 控件属性 | .cht 事件/函数 |
|---------|------|------------|--------------|
| 按钮事件 | 触摸屏 → 中控 | DFCButton.JoinNumber | `BUTTON_EVENT(tp, N) { PUSH(){} }` |
| 滑条事件 | 触摸屏 → 中控 | DFCSlider.JoinNumber | `LEVEL_EVENT(tp, N) { val = GET_LEVEL(tp, N); }` |
| 按钮状态反馈 | 中控 → 触摸屏 | DFCButton.JoinNumber | `SET_BUTTON(tp, N, 1/0)` |
| 文本反馈 | 中控 → 触摸屏 | DFCTextbox.JoinNumber | `SEND_TEXT(tp, N, "文字")` |
| 滑条反馈 | 中控 → 触摸屏 | DFCSlider.JoinNumber | `SET_LEVEL(tp, N, 值)` |
| 图片切换 | 中控 → 触摸屏 | DFCPicture.JoinNumber | `SEND_PICTURE(tp, N, 索引)` |
