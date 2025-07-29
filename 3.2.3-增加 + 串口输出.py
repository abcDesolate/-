import pyb, sensor, image, math, time
from pyb import UART
import ustruct
from image import SEARCH_EX, SEARCH_DS
import time
import sensor, lcd
#导入需要的库和模块
#教程作者:好家伙VCC
#欢迎交流群QQ: 771027961 作者邮箱: 1930299709@qq.com
#更多教程B站主页:[好家伙VCC的个人空间-好家伙VCC个人主页-哔哩哔哩视频](https://space.bilibili.com/434192043)
#淘宝主页链接:[首页-好家伙VCC-淘宝网](https://shop415231378.taobao.com)
#更多嵌入式手把手教程-尽在好家伙VCC
#使用中可能根据自己情况需要修改的值
#1. GROUND_THRESHOLD 阈值参数 通过工具->机器视觉->阈值编辑器->帧缓冲区 调整出要识别的LAB阈值。
#2.注意是否有下面两句根据自己摄像头调整
  #sensor.set_vflip(True)
  #sensor.set_hmirror(True)


#sensor.set_contrast(1)#设置相机图像对比度。-3至+3。
#sensor.set_gainceiling(16)#设置相机图像增益上限。2, 4, 8, 16, 32, 64, 128。

uart = UART(3,115200,bits=8, parity=None, stop=1, timeout_char = 1000)#初始化串口三、波特率115200 TXD:P4\PB10 RXD:P5\PB11

roi1 =	 [( 20,   105, 10, 10),
          ( 45,   105, 10, 10),
          ( 75,   105, 10, 10),
          ( 105,  105, 10, 10),
          (130,   105, 10, 10)]#定义一个名为roi1的列表，其中包含了5个元组。每个元组代表了一个矩形感兴趣区域在图像上的位置和大小。
#具体而言，每个元组包含了4个数值依次的含义是：ROI左上角点的x坐标、ROI左上角点的y坐标、ROI的宽度、ROI的高度

led = pyb.LED(1) # led = pyb.LED(1)表示led表示红灯。各种状态如下:Red LED = 1, Green LED = 2, Blue LED = 3, IR LEDs = 4.
led.on()         #点亮红灯 板载红灯点亮表示程序得到执行

sensor.reset()#初始化相机传感器。
sensor.set_pixformat(sensor.RGB565)#设置相机模块的像素模式:sensor.RGB565: 16 bits/像素。
sensor.set_framesize(sensor.QQVGA)#设置图像分辨率、如果改变分辨率也要调整ROI区域。摄像头不同、应用场景不同可以选择不同分辨率。这里使用QQVGA可能画质很胡，但是为了兼容不同型号摄像头我们先使用QQVGA 不影响循迹效果
# ***************************如果不需要镜像就注释掉 下面 的代码********************
# 设置摄像头镜像/翻转操作，根据摄像头安装的方向决定是否需要
sensor.set_vflip(True)  # 垂直方向翻转。根据实际摄像头模块的安装位置调整是否需要此操作
# ！！！重要：不同摄像头是否需要镜像，根据实际情况定。如果不需要镜像，请注释掉以下代码：
sensor.set_hmirror(True)  # 水平方向反转。根据实际摄像头模块的安装位置调整是否需要此操作
# ！！！重要：不同摄像头是否需要镜像，根据实际情况定。如果不需要镜像，请注释掉上述代码。
# ***************************如果不需要镜像就注释掉 上面 的代码********************
sensor.skip_frames(time=2000)#跳过指定数目的帧。在这里，设置为跳过2000毫秒（即2秒）的帧。这样可以给传感器一些时间进行初始化和自适应调整。
sensor.set_auto_whitebal(True)#设置为自动白平衡模式。这使得摄像头可以根据场景中的光照条件自动调整图像的白平衡，从而保持图像色彩更加准确和自然。
sensor.set_auto_gain(False)#关闭自动增益模式。通常情况下，开启自动增益会帮助摄像头自动调整亮度，并在低亮度环境下提高图像清晰度。通过设置为False，禁用了这个功能，使用固定增益值。

#lcd.init() #初始化lcd屏幕

#最好根据自己情况设置一下！！！
#GROUND_THRESHOLD=(0, 8, -128, 23, -128, 80)#阈值参数，用于在图像处理中对标物体进行颜色识别分割。在OpenMV IDE软件 工具->机器视觉->阈值编辑器->帧缓冲区 调整出要识别的LAB阈值。
GROUND_THRESHOLD=(0, 30, -22, 23, -128, 80)#阈值参数，用于在图像处理中对标物体进行颜色识别分割。在OpenMV IDE软件 工具->机器视觉->阈值编辑器->帧缓冲区 调整出要识别的LAB阈值。
def send_five_uchar(c1,c2,c3,c4,c5):#功能发送五个无符号字符（unsigned char）
    global uart;
    data = ustruct.pack("<BBBBBBBB",#使用了 ustruct.pack() 函数将这些数据打包为二进制格式。使用 "<BBBBBBBB" 作为格式字符串来指定要打包的数据的类型和顺序：
                   0xA5,
                   0xA6,
                   c1,
                   c2,
                   c3,
                   c4,
                   c5,
                   0x5B
                   )
    uart.write(data);#uart.write(data) 将打包好的二进制数据帧写入 UART 发送缓冲区，从而将数据通过串口发送出去
    print(data)#通过 print(data) 打印发送的数据到串行终端，方便调试和确认发送的内容。

while(True):
    data=0
    blob1=None
    blob2=None
    blob3=None
    blob4=None
    blob5=None
    flag = [0,0,0,0,0]
    img = sensor.snapshot().lens_corr(strength = 1.7 , zoom = 1.0)#对获取到的图像执行镜头校正的操作。
    blob1 = img.find_blobs([GROUND_THRESHOLD], roi=roi1[0])#在图像中通过颜色阈值 GROUND_THRESHOLD1 检测 roi1[0] 区域内的色块，并将检测结果赋值给 blob1。
    blob2 = img.find_blobs([GROUND_THRESHOLD], roi=roi1[1])#同理
    blob3 = img.find_blobs([GROUND_THRESHOLD], roi=roi1[2])
    blob4 = img.find_blobs([GROUND_THRESHOLD], roi=roi1[3])
    blob5 = img.find_blobs([GROUND_THRESHOLD], roi=roi1[4])

    if blob1:#如果roi1区域内找到阈值色块 就会赋值flag[0]为1
        flag[0] = 1
    if blob2:
        flag[1] = 1
    if blob3:
        flag[2] = 1
    if blob4:
        flag[3] = 1
    if blob5:
        flag[4] = 1
 #   print(flag[0],flag[1],flag[2],flag[3],flag[4])#把数据打印在串行终端方便调试
    send_five_uchar(flag[0],flag[1],flag[2],flag[3],flag[4])#把五个数据通过串口发送出去、发送五个无符号字符。

    # 遍历所有感兴趣的区域，并绘制矩形框及其识别结果
    for i, rec in enumerate(roi1):
        img.draw_rectangle(rec, color=(255, 0, 0))  # 绘制矩形框
        # 根据flag显示识别结果
        result_text = str(flag[i])  # 显示 1 或 0
        #rec 中的 rec[0] 对应的是矩形框左上角的 横坐标（x），而 rec[1] 对应的是矩形框左上角的 纵坐标（y）
        text_y_position = rec[1] - 15  # 调整文本显示位置，使其位于矩形框的上方
        img.draw_string(rec[0], text_y_position, result_text, color=(255, 255, 255), scale=2)  # 在矩形框内绘制文本
        # lcd.display(img)  # 将图像显示在lcd中
