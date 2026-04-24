# DFCApp 外部应用

> **属性全部 camelCase (与其他控件不同!)**

## XML

```xml
<DFCApp Name="外部应用" ID="N"
        left="0" top="0" width="1920" height="1080"
        opacity="1" visible="True"
        AppPath="C:\xxx\app.exe" AppParam="" AppWindowType="Fullscreen"
        IsEmbed="True"
        hasBorder="False" borderColor="#FF000000" borderStyle="2D" cornerRadius="0"
        bgColor="#FF000000" normalImage="" imageFillType="Stretch"
        joinNumber="0" clickSound="" jumpPage="" />
```

## 注意

- 不使用 `<Control>` 标签, 直接用 `<DFCApp>` 单标签
- 坐标: `left/top` (不是 X/Y)
- 尺寸: `width/height` (不是 Width/Height)
- 连接号: `joinNumber` (不是 JoinNumber)
