# 控件速查索引

## 页面内控件

| # | 类型 | XML Type | JoinNumber | 文件 |
|---|------|----------|------------|------|
| 1 | 按钮 | DFCButton | BUTTON_EVENT + SET_BUTTON | `DFCButton.md` |
| 2 | 图片 | DFCPicture | SEND_PICTURE | `DFCPicture.md` |
| 3 | 文本框 | DFCTextbox | SEND_TEXT | `DFCTextbox.md` |
| 4 | 可编辑文本框 | DFCEditTextbox | JN + TextSendJN | `DFCEditTextbox.md` |
| 5 | 密码框 | DFCPassword | JoinNumber | `DFCPassword.md` |
| 6 | 滑动条 | DFCSlider | LEVEL_EVENT + SET_LEVEL(双向同号) | `DFCSlider.md` |
| 7 | 进度条 | **DFCProgress** | SET_LEVEL(单向) | `DFCProgress.md` |
| 8 | 时间 | DFCTime | 无(仅显示) | `DFCTime.md` |
| 9 | 视频 | DFCVideo | JoinNumber | `DFCVideo.md` |
| 10 | 外部应用 | DFCApp | joinNumber(camelCase!) | `DFCApp.md` |
| 11 | 外部跳转链接 | **SPButton** | JoinNumber | `SPButton.md` |

## 页面/容器类型（Object 标签）

| # | 类型 | XML Type | 文件 |
|---|------|----------|------|
| 12 | 普通页面 | DFCForm | `DFCForm.md` |
| 13 | 弹窗 | DFCMessegeToast | `DFCMessegeToast.md` |
| 14 | 视频矩阵页 | **DFCVideoMatrix** | `DFCVideoMatrix.md` |
| 15 | 远程控制页 | **DFCRemoteControl** | `DFCRemoteControl.md` |

## BtnType / BtnUseType 默认值

| 控件 | BtnType | 说明 |
|------|---------|------|
| DFCButton | NormalBtn / AutolockBtn / MutualLockBtn / LoginBtn | 按功能选择 |
| DFCTextbox | NormalTextBox | 注意大写 B |
| DFCEditTextbox | NormalTextbox | 注意小写 b |
| DFCPassword | NormalPasswordBox | |
| DFCVideo | NormalVideo | |
| SPButton | NormalBtn | |

## JoinNumber 6 种通道

| 通道 | 方向 | 控件 | CHT 函数 |
|------|------|------|----------|
| 按钮事件 | 屏→控 | DFCButton.JN | `BUTTON_EVENT(tp,N){PUSH(){}}` |
| 滑条事件 | 屏→控 | DFCSlider.JN | `LEVEL_EVENT(tp,N){val=GET_LEVEL(tp,N);}` |
| 按钮反馈 | 控→屏 | DFCButton.JN | `SET_BUTTON(tp,N,1/0)` |
| 文本反馈 | 控→屏 | DFCTextbox.JN | `SEND_TEXT(tp,N,"文字")` |
| 滑条反馈 | 控→屏 | DFCSlider/DFCProgress.JN | `SET_LEVEL(tp,N,值)` |
| 图片切换 | 控→屏 | DFCPicture.JN | `SEND_PICTURE(tp,N,索引)` |
