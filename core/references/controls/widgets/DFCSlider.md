# DFCSlider 滑动条

## XML

```xml
<Control Name="音量条" Type="DFCSlider" ID="N" X="0" Y="0" Width="600" Height="60" BlockWidth="30" BlockHeight="30">
  <Appearance Visible="True" Enable="True" IsLock="False" Opacity="1" />
  <Style MinValue="0" MaxValue="100" Percent="50"
         IsVertical="False"
         BackgroundColor="#FF333333" ElapsedColor="#FF00AAFF"
         BlockColor="#FFFFFFFF" BlockRadius="15" BlockWidth="30" BlockHeight="30"
         NormalColor="#00000000" Radius="5" />
  <SliderLocationStyle LocationMargin="" LocationWidth="" LocationHeight=""
                       LocationFontFamily="" LocationFontSize=""
                       LocationForeground="" LocationBackground=""
                       LocationHorizontalContentAlignment="Center"
                       LocationVerticalContentAlignment="Center"
                       LocationCtrlBorderEnable="False" LocationBorderType="2D"
                       LocationBorderColor="" LocationRadius="" />
  <Event JoinNumber="1000" />
</Control>
```

## 核心属性

| 属性 | 说明 |
|------|------|
| JoinNumber | 双向: `LEVEL_EVENT(tp,N)` 接收拖动 + `SET_LEVEL(tp,N,val)` 推送反馈 |
| MinValue/MaxValue | 范围（默认 0-65535） |
| Percent | 当前值（非百分比，是绝对值） |
| ValueLocation | 数值标签位置: Bottom/Top/Left/Right/空 |
| IsVertical | False=水平, True=垂直 |
| BlockWidth/Height | 拖动块大小 |
| ElapsedColor | 已滑动颜色 |
| BackgroundColor | 轨道背景色 |
