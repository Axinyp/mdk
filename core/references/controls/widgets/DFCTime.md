# DFCTime 时间

## XML

```xml
<Control Name="时间" Type="DFCTime" ID="N" X="97" Y="21" Width="286" Height="149" BlockWidth="0" BlockHeight="0">
  <Style FontFamily="D-DIN" FontSize="108" TextColor="#FFFFFFFF"
         NormalColor="#00000000" TimeType="HH:mm" />
  <Event JoinNumber="0" />
</Control>
```

## 核心属性

| 属性 | 说明 |
|------|------|
| TimeType | 格式: `HH:mm` / `HH:mm:ss` / `yyyy-MM-dd` / `dddd`(星期) |
| JoinNumber | 通常为 0(仅显示) |
