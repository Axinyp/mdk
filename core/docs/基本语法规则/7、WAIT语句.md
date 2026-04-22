**1、WAIT语句定义**
作用是定义一段在等待指定时间之后执行的语句块。
WAIT语句的定义格式如下：
```
WAIT  TIME  NAME{
语句块
}
```
其中**TIME**必须是**整形常量**，表示等待多少毫秒。
**NAME**必须是**字符串常量**，表示WAIT语句的名字。WAIT语句的名字是可有可无的；有名字的WAIT语句我们称为命名WAIT语句，在程序里可以使用`CANCEL_WAIT(WAIT语句名字)`来取消对应名字的WAIT语句；没有名字的WAIT语句我们称为匿名WAIT语句，这种WAIT语句将不可以使用`CANCEL_WAIT()`来取消。

**注意：
1、WAIT语句名字的命名规则与变量命名规则一样，具体请参考 ”**[**类型和值**](1、类型和值.md)**“ 里标识符的命名规则。**
**2、程序里出现的任何命名WAIT语句的名字必须是唯一的。**
**3、WAIT语句只能使用`DEFINE_DEVICE`里定义的设备、`DEFINE_CONSTANT`里定义的常量、`DEFINE_VARIABLE`里定义的变量、`DEFINE_FUNCTION`里定义的函数或本WAIT语句里定义的变量。其他地方出现的任何变量都不可以使用，并且也不可以使用BUTTON、LEVEL和DATA这些系统内部对象。**
**例子：**
```
DEFINE_EVENT  
     BUTTON_EVENT(TP,1)  
     {  
          PUSH()  
          {  
               WAIT 1000 "tp_push_1"  
               {  
                    TRACE("TP PUSH JoinNumber=1");  
               }  
          }  
     }
```
当触发设备 “TP” 通道号为1的按钮时，将马上开始WAIT语句的计时，当计时为1000毫秒后，才会执行WAIT语句里的 “TRACE” 语句。
**匿名WAIT例子：**
```
DEFINE_EVENT  
     BUTTON_EVENT(TP,1)  
     {  
          PUSH()  
          {  
               WAIT 1000  
               {  
                    TRACE("TP PUSH JoinNumber=1");  
               }  
          }  
     }
```

**2、WAIT语句的嵌套**
有时会需要完成这样的功能：先等待一段时间TIME1 然后执行操作1，接着又要等待一段时间TIME1 然后执行操作2。这种功能就需要使用嵌套WAIT语句来完成。
```
WAIT  TIME1  NAME1{
操作1
// 名为NAME2的WAIT语句嵌套在名为NAME1的WAIT语句中
WAIT  TIME2  NAME2{ 
    操作2
}
```

}

外面的WAIT语句等待完成（即计时已达到TIME1）后才会开始里面WAIT语句的计时，里面WAIT语句等待完成后才会执行操作2。因此操作2实际等待了时间TIME1+TIME2。

**3、WAIT语句的取消**

对于任何命名的WAIT语句，都可以使用函数CANCEL_WAIT(WAIT语句名字)来进行取消操作。

取消操作的效果是：

(1) 如果WAIT语句还在计时，那么将停止计时并放弃整个WAIT的执行。

(2) 如果WAIT语句已经计时完成并正在执行WAIT语句里的语句块是，那么将停止执行并放弃整个WAIT的执行。

**例子：**
```
DEFINE_EVENT  
     BUTTON_EVENT(TP,1)  
     {  
          PUSH()  
          {  
               WAIT 1000 "tp_push_1"  
               {

                    TRACE("TP PUSH JoinNumber=1");  
               }  
          }  
     }  
   
     BUTTON_EVENT(TP,2)  
     {  
          PUSH()  
          {  
               CANCEL_WAIT( "tp_push_1" );  
          }  
     }

```
当触发设备 “TP” 通道号为2的按钮时，将取消名为 "tp_push_1" 的WAIT语句。