# DFCPicture 图片

## XML

```xml
<Control Name="状态图" Type="DFCPicture" ID="N" X="0" Y="0" Width="100" Height="100" BlockWidth="0" BlockHeight="0">
  <Appearance Visible="True" Enable="True" Border="False" BorderType="2D" BorderColor=""
              Opacity="1" IsLock="False" />
  <Style NormalImage=".\默认图.png" PressImage=""
         ImagePictures=".\状态0.png,.\状态1.png,.\状态2.png"
         ImgItemIndex="0" ImageStretch="False"
         IsDrag="False" IsTouchSource="False"
         Autolock="False" MutualLockGroup="" JumpPage="" DialogPage=""
         ButtonSoundSource="" Radius="0" />
  <Event JoinNumber="150" />
</Control>
```

## 核心属性

| 属性 | 说明 |
|------|------|
| NormalImage | 默认显示图 |
| ImagePictures | 多图集合(逗号分隔), 用于 SEND_PICTURE 切换 |
| ImgItemIndex | 当前索引(0开始) |
| JoinNumber | → CHT: `SEND_PICTURE(tp,N,index)` |
