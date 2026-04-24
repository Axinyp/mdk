# DFCRemoteControl 远程控制页

## XML

```xml
<Object Name="远程控制" Type="DFCRemoteControl" ID="N" X="0" Y="0" Width="1624" Height="750"
        IsActive="False" DisplayTime="" Radius="0"
        RemoteControlIP="" RemoteControlAccount="" RemoteControlPassWord="">
  <Style Visible="True" Enable="True" BackColor="#FFFFFFFF" Opacity="1" ModalLayerOpacity="1"
         IsChecklayer="False" LayerColor="#A0000000" />
  <Appearance Grid="False" Border="False" HomePage="False"
              LeftJumpPage="" RightJumpPage="" TopJumpPage="" BottomJumpPage=""
              LeftCmdType="" RightCmdType="" TopCmdType="" BottomCmdType="" />
  <MatrixVideo MatrixWidth="0" MatrixHeight="0" MatrixLayout="Layout1"
               MatrixVideoType="Splicer" MatrixName="" MatrixUrl=""
               VideoCount="1" PreviewChannel="" VideoColumns="4" VideoRows="4"
               MatrixOpticalVideoName="" MatrixOpticalVideoUrl="" MatrixOpticalVideoCount="1" />
</Object>
```

## 核心属性

| 属性 | 说明 |
|------|------|
| RemoteControlIP | 远程设备 IP |
| RemoteControlAccount | 远程登录账号 |
| RemoteControlPassWord | 远程登录密码 |
