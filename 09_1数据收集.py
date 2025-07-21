# 搜索学不会电磁场看教程
# 第九课，AI识别数字，电赛题目智能送药小车需要识别数字，现在，我们先收集数据

import time
import os
import sys

from media.sensor import *
from media.display import *
from media.media import *
from time import ticks_ms
from machine import FPIOA
from machine import Pin
from machine import PWM
from machine import Timer
import time


sensor = None

try:

    print("camera_test")
    fpioa = FPIOA()
    fpioa.help()
    fpioa.set_function(53, FPIOA.GPIO53)

    key = Pin(53, Pin.IN, Pin.PULL_DOWN)


    sensor = Sensor(width=1024, height=768)
    sensor.reset()

    # 鼠标悬停在函数上可以查看允许接收的参数
    sensor.set_framesize(width=1024, height=768)
    sensor.set_pixformat(Sensor.RGB565)

    Display.init(Display.ST7701, width=800, height=480, to_ide=True)
    # 初始化媒体管理器
    MediaManager.init()
    # 启动 sensor
    sensor.run()
    clock = time.clock()

    counter = 0
    save_folder = "/data/data/images/"
    class_lst = ["one", "two", "three", "four", "five", \
                 "six", "seven", "eight", "nine", "zero"]
    class_id = -1
    prefix = "batch_1_"
    while True:
        clock.tick()
        os.exitpoint()
        img = sensor.snapshot(chn=CAM_CHN_ID_0)
        if key.value() == 1:
            class_id = (class_id + 1) % len(class_lst)
            os.mkdir(save_folder+class_lst[class_id])
            for i in range(3):
                print("will collect {} class in {} s".format(class_lst[class_id], 3-i))
                time.sleep_ms(1000)
            counter = 100
        if not counter == 0:
            time.sleep_ms(50)
            file_name = "{}_{}_{}.jpg".format(prefix, class_lst[class_id], str(counter))
            save_img = img.compress(95)
            file_path = save_folder + class_lst[class_id] + "/" + file_name
            with open(file_path, 'wb') as f:
                f.write(save_img)
            print("img saved to \"{}\"".format(file_path))
            counter -= 1


#        # 绘制字符串，参数依次为：x, y, 字符高度，字符串，字符颜色（RGB三元组）
#        img.draw_string_advanced(50, 50, 80, "hello k230\n学不会电磁场", color=(255, 0, 0))

#        # 绘制直线，参数依次为：x1, y1, x2, y2, 颜色，线宽
#        img.draw_line(50, 50, 300, 130, color=(0, 255, 0), thickness=2)

#        # 绘制方框，参数依次为：x, y, w, h, 颜色，线宽，是否填充
#        img.draw_rectangle(1000, 50, 300, 200, color=(0, 0, 255), thickness=4, fill=False)

#        # 绘制关键点, 列表[(x, y, 旋转角度)]
#        img.draw_keypoints([[960, 540, 200]], color=(255, 255, 0), size=30, thickness=2, fill=False)

#        # 绘制圆, x, y, r
#        img.draw_circle(640, 640, 50, color=(255, 0, 255), thickness=2, fill=True)
#        # 精细的像素级操作，虽然说其实一般用不上，这里利用像素填充的方式绘制一个非常奇怪的方块吧
#        for i in range(1200, 1250):
#            for j in range(700, 750):
#                color =((i + j)%256, (i*j)%256, abs(i-j)%256)
#                img.set_pixel(i, j, color)

        # 矩形识别，可以用来找矩形的四个角的坐标
#        img_rect = img.to_grayscale(copy=True)
#        img_rect = img_rect.binary([(82, 212)])
#        rects = img_rect.find_rects(threshold=10000)

#        if not rects == None:
#            for rect in rects:
#                corner = rect.corners()
#                img.draw_line(corner[0][0], corner[0][1], corner[1][0], corner[1][1], color=(0, 255, 0), thickness=5)
#                img.draw_line(corner[2][0], corner[2][1], corner[1][0], corner[1][1], color=(0, 255, 0), thickness=5)
#                img.draw_line(corner[2][0], corner[2][1], corner[3][0], corner[3][1], color=(0, 255, 0), thickness=5)
#                img.draw_line(corner[0][0], corner[0][1], corner[3][0], corner[3][1], color=(0, 255, 0), thickness=5)

        img.draw_string_advanced(50, 50, 80, "fps: {}".format(clock.fps()), color=(255, 0, 0))
        img.midpoint_pool(2, 2)
        img.compressed_for_ide()
        Display.show_image(img, x=(800-320)//2, y=(480-320)//2)

except KeyboardInterrupt as e:
    print("用户停止: ", e)
except BaseException as e:
    print(f"异常: {e}")
finally:
    if isinstance(sensor, Sensor):
        sensor.stop()
    Display.deinit()
    os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
    time.sleep_ms(100)
    MediaManager.deinit()
