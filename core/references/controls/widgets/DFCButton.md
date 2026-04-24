# DFCButton 按钮

## 子类型

| BtnType | 行为 | 用途 | CHT 模式 |
|---------|------|------|----------|
| NormalBtn | 按下触发 | 全开/全关、窗帘开停关 | `PUSH(){...}` |
| AutolockBtn | 锁定/解锁 | 单路灯光、电源、静音 | `PUSH(){on} RELEASE(){off}` |
| MutualLockBtn | 同组互斥 | 场景、信号源选择 | `PUSH(){... SET_BUTTON互斥}` |
| LoginBtn | 登录触发 | 密码验证 | 配合 DFCPassword |

## XML

```xml
<Control Name="按钮名" Type="DFCButton" ID="N" X="0" Y="0" Width="200" Height="80" BlockWidth="0" BlockHeight="0">
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

## 核心属性

| 属性 | 位置 | 说明 |
|------|------|------|
| BtnType | Appearance | NormalBtn/MutualLockBtn/LoginBtn |
| Autolock | Appearance+Event | True=自锁(AutolockBtn) |
| NormalImage/PressImage | Style | 常态/按下背景图 `.\xxx.png` |
| NormalColor/PressColor | Style | 无图时的背景色 |
| Radius | Style | 圆角半径 |
| MutualLockGroup | Style+Event | 互斥组名 |
| JoinNumber | Event | → CHT: `BUTTON_EVENT(tp,N)` |
| JumpPage | Event | 跳转页面名, "无"=关闭弹窗 |
| DialogPage | Event | 弹出弹窗名 |
| TextSendJoinNumber | Style | 关联文本框(LoginBtn用) |
