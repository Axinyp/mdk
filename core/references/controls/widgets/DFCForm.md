# DFCForm 页面

## XML

```xml
<Object Name="主页" Type="DFCForm" ID="N" X="0" Y="0" Width="2560" Height="1600"
        IsActive="False" DisplayTime="" Radius=""
        RemoteControlIP="" RemoteControlAccount="" RemoteControlPassWord="">
  <Style Visible="True" Enable="True" BackColor="#FFFFFFFF"
         BkImage=".\背景.png" Opacity="1" ModalLayerOpacity="1"
         IsChecklayer="False" LayerColor="#A0000000" />
  <Appearance Grid="False" Border="False" HomePage="False"
              LeftJumpPage="" RightJumpPage="" TopJumpPage="" BottomJumpPage=""
              LeftCmdType="" RightCmdType="" TopCmdType="" BottomCmdType="" />
  <MatrixVideo MatrixWidth="0" MatrixHeight="0" MatrixLayout="Layout1"
               MatrixVideoType="Splicer" MatrixName="" MatrixUrl=""
               VideoCount="1" PreviewChannel="" VideoColumns="4" VideoRows="4"
               MatrixOpticalVideoName="" MatrixOpticalVideoUrl="" MatrixOpticalVideoCount="1" />
  <!-- 子控件 -->
</Object>
```

## 核心属性

| 属性 | 说明 |
|------|------|
| Name | 页面名(JumpPage 引用此名) |
| HomePage | True=主页(仅一个) |
| BkImage | 背景图 `.\xxx.png` |
| StartForm | Project 根属性, 指定启动页面名 |
