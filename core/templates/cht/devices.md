# CHT 设备声明模板

根据设备类型和参数，直接生成 DEFINE_DEVICE 行：

## 触摸屏
```
tp = T:{{board}}:TP;
```

## 继电器 (板载)
```
L9101_RELAY = L:{{board}}:RELAY;
```

## 串口 (主机 COM)
```
M_COM = M:{{port_id}}:COM;
```
port_id 规则: 主机端口 1001-1008

## 串口 (扩展模块 COM)
```
TR_{{module}}_COM{{ch}} = L:{{board}}:COM;
```

## 红外 (扩展模块 IR)
```
TR_{{module}}_IR{{ch}} = L:{{board}}:IR;
```

## IO
```
M_IO = M:{{board}}:IO;
```

## DEFINE_START 初始化

每个串口设备必须 SET_COM：
```
SET_COM({{dev_name}}, {{channel}}, {{baud}}, {{data_bits}}, {{parity}}, {{stop_bits}}, 0, {{type}});
```
type: 232=RS232, 485=RS485
