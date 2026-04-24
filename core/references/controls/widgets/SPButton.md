# SPButton 外部跳转链接

## XML

```xml
<Control Name="外部链接" Type="SPButton" ID="N" X="0" Y="0" Width="297" Height="140" BlockWidth="0" BlockHeight="0">
  <Appearance Visible="True" Enable="True" Border="False" BorderType="3D" BorderColor="#FFCD6633" BtnType="NormalBtn" Opacity="1" IsLock="False" />
  <Style FontFamily="SourceHanSansCN-Regular" FontSize="25" FontStyle="Normal" FontWeight="Normal"
         Text="SPButton" TextPos="middle" TextColor="#FF000000" PressTextColor="#FF000000"
         PressColor="#FFB86D3A" NormalColor="#FFD1A282"
         BtnUseType="NormalBtn" TextSendJoinNumber="0"
         HorizontalContentAlignment="Center" VerticalCententAlignment="Center" Radius="0"
         IsContainsPic="False" />
  <SliderLocationStyle />
  <Event DialogPage="" JumpPage="" JoinNumber="0" DelayTime="0" Autolock="False" MutualLockGroup="" CmdType="" ButtonSoundSource="" />
</Control>
```

## 核心属性

| 属性 | 说明 |
|------|------|
| 用途 | 触摸屏跳转到外部链接/应用 |
| 结构 | 与 DFCButton 类似，Type 不同 |
