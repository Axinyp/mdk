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
        val = GET_LEVEL(tp, {{join}});
        {{action}};
    }
```

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
