# CHT 事件模板

## NormalBtn 按钮 (单次触发)
```
    BUTTON_EVENT(tp, {{join}})
    {
        PUSH()
        {
            {{action}};
        }
    }
```

## AutolockBtn 按钮 (开关切换)
```
    BUTTON_EVENT(tp, {{join}})
    {
        PUSH()
        {
            {{on_action}};
            SET_BUTTON(tp, {{join}}, 1);
        }
        RELEASE()
        {
            {{off_action}};
            SET_BUTTON(tp, {{join}}, 0);
        }
    }
```

## MutualLockBtn 按钮 (互斥选择)
```
    BUTTON_EVENT(tp, {{join}})
    {
        PUSH()
        {
            {{action}};
            SET_BUTTON(tp, {{join}}, 1);
{{reset_others}}
        }
    }
```
reset_others 格式: `            SET_BUTTON(tp, {{other_join}}, 0);`

## LEVEL_EVENT 滑条
```
    LEVEL_EVENT(tp, {{join}})
    {
        int val;
        val = LEVEL.Value;
        {{action}};
    }
```
注意：LEVEL_EVENT 内部通过 LEVEL 对象访问属性，不存在 GET_LEVEL 函数。
可用属性：LEVEL.Value（滑条值）、LEVEL.JoinNumber（通道号）、LEVEL.Channel、LEVEL.DeviceID。

## DATA_EVENT 串口回传
```
    DATA_EVENT({{dev}}, {{channel}})
    {
        ONDATA()
        {
            string resp;
            resp = BYTES_TO_STRING(DATA.Data);
            {{handler}};
        }
    }
```
