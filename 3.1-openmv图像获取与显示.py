# This work is licensed under the MIT license.
# Copyright (c) 2013-2023 OpenMV LLC. All rights reserved.
#教程作者: 好家伙VCC
#教程作者:好家伙VCC
#欢迎交流群QQ: 771027961 作者邮箱: 1930299709@qq.com
#更多教程B站主页:[好家伙VCC的个人空间-好家伙VCC个人主页-哔哩哔哩视频](https://space.bilibili.com/434192043)
#淘宝主页链接:[首页-好家伙VCC-淘宝网](https://shop415231378.taobao.com)
#更多嵌入式手把手教程-尽在好家伙VCC
#
# Welcome to the OpenMV IDE! Click on the green run arrow button below to run the script!

import sensor # 引入感光元件的模块，用于操作摄像头传感器
import time # 引入时间模块，用于控制时间延迟和FPS计算

# 初始化传感器
sensor.reset()  # Reset and initialize the sensor. 重置并初始化传感器
sensor.set_pixformat(sensor.RGB565)  # Set pixel format to RGB565 (or GRAYSCALE) 设置像素格式为RGB565（或者灰度）
sensor.set_framesize(sensor.QVGA)  # Set frame size to QVGA (320x240) 设置帧大小为QVGA（320x240分辨率）
#***************************如果不需要镜像就注释掉 下面 的代码********************
# 设置摄像头镜像/翻转操作，根据摄像头安装的方向决定是否需要
sensor.set_vflip(True)  # 垂直方向翻转。根据实际摄像头模块的安装位置调整是否需要此操作
#！！！重要：不同摄像头是否需要镜像，根据实际情况定。如果不需要镜像，请注释掉以下代码：
sensor.set_hmirror(True)  # 水平方向反转。根据实际摄像头模块的安装位置调整是否需要此操作
#！！！重要：不同摄像头是否需要镜像，根据实际情况定。如果不需要镜像，请注释掉上述代码。
#***************************如果不需要镜像就注释掉 上面 的代码********************
sensor.skip_frames(time=2000)  # Wait for settings take effect. 等待2秒钟让设置生效
clock = time.clock()  # Create a clock object to track the FPS. 创建一个时钟对象，用于追踪FPS（每秒帧数）



while True:
    clock.tick()  # Update the FPS clock. 更新FPS时钟
    img = sensor.snapshot()  # Take a picture and return the image. 拍摄一张照片并返回图像
    print(clock.fps())  # 输出当前的帧率（FPS），用来衡量摄像头的拍摄速度
    # Note: OpenMV Cam runs about half as fast when connected
    # to the IDE. The FPS should increase once disconnected.
    # 注意：当OpenMV相机连接到IDE时，速度大约是平时的一半。断开连接后，FPS应该会提高。
