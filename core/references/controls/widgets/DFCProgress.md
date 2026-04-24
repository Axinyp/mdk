# DFCProgress 进度条

> XML Type 是 `DFCProgress`（不是 DFCTaskBar）

## XML

```xml
<Control Name="进度条" Type="DFCProgress" ID="N" X="0" Y="0" Width="282" Height="120" BlockWidth="0" BlockHeight="0">
  <Appearance Visible="True" Enable="True" Border="True" BorderType="2D" BorderColor="#FF000000" BtnType="" Opacity="1" IsLock="False" />
  <Style IsVertical="False" ElapsedColor="#FF00FF80" MaxValue="65535" MinValue="0" Percent="13107"
         BackgroundColor="#FFFFFFFF" Radius="10" BtnUseType="" TextSendJoinNumber="0" IsContainsPic="False" />
  <SliderLocationStyle />
  <Event DialogPage="" JumpPage="" JoinNumber="0" DelayTime="" Autolock="" MutualLockGroup="" CmdType="" ButtonSoundSource="" />
</Control>
```

## 核心属性

| 属性 | 说明 |
|------|------|
| JoinNumber | 只接收 `SET_LEVEL(tp,N,val)`, 不产生 LEVEL_EVENT |
| MinValue/MaxValue | 范围（默认 0-65535） |
| Percent | 当前值 |
| IsVertical | False=水平, True=垂直 |
| ElapsedColor | 进度颜色 |
| BackgroundColor | 轨道背景色 |
