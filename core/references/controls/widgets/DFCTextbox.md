# DFCTextbox 文本框

## XML

```xml
<Control Name="状态文字" Type="DFCTextbox" ID="N" X="0" Y="0" Width="200" Height="60" BlockWidth="0" BlockHeight="0">
  <Appearance Visible="True" Enable="True" Border="False" Opacity="1" IsLock="True" />
  <Style FontFamily="D-DIN" FontSize="48" TextColor="#FFAAAAAA"
         NormalColor="#00000000" Text=""
         HorizontalContentAlignment="Left" VerticalCententAlignment="Center"
         ImageStretch="False" IsDrag="False" Radius="0" />
  <Event JoinNumber="200" />
</Control>
```

## 核心属性

| 属性 | 说明 |
|------|------|
| Text | 静态文本(生成时为空, 由 SEND_TEXT 更新) |
| JoinNumber | → CHT: `SEND_TEXT(tp,N,"文字")` |
| FontFamily | 字体 |
| TextColor | 文字色 |
