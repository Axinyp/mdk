**DEFINE_COMBINE:  设备定义块**  
使用说明：
该模块只要是针对多触摸屏的情况。如实际中需要多个触屏屏设备，该模块可以很好的匹配。
格式：
[tp1,tp2]; //tp1 等同于tp2
如：
[tp1,tp2,tp3];
[tp1,tp4];
[tp5,tp6];
表明 tp1 == tp2==tp3==tp4
tp5==tp6 但与tp1，tp2,tp3，tp4不等。