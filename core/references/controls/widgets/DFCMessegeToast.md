# DFCMessegeToast 弹窗

> 注意拼写: Messege (非 Message)

## XML

```xml
<Object Name="确认弹窗" Type="DFCMessegeToast" ID="N" X="600" Y="400" Width="1360" Height="800"
        IsActive="False" DisplayTime="10" Radius="20"
        RemoteControlIP="" RemoteControlAccount="" RemoteControlPassWord="">
  <Style BackColor="#FFFFFFFF" BkImage="" Opacity="1" ModalLayerOpacity="0.5"
         IsChecklayer="False" LayerColor="#A0000000" />
  <!-- 子控件 -->
</Object>
```

## 核心属性

| 属性 | 说明 |
|------|------|
| DisplayTime | 自动关闭秒数, 0=手动关闭 |
| ModalLayerOpacity | 遮罩透明度 |
| 触发方式 | 按钮 `DialogPage="弹窗名"` |
| 关闭方式 | 按钮 `JumpPage="无"` |
