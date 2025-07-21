# bilibili搜索学不会电磁场看教程
# 第12课，开始实践，做一个类似于2023年E题的激光点回位

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

sensor = None

try:
    class PID:
        def __init__(self, kp, ki, input_value, target=320):
            self.e = 0
            self.e_last = 0
            self.kp = kp
            self.ki = ki
            self.target = target
            self.input_value = input_value
        def cal(self, value):
            self.e = self.target - value
            delta = self.kp * (self.e-self.e_last) + self.ki * self.e
            self.e_last = self.e
            self.input_value = self.input_value + delta
            return self.input_value

    print("camera_test")

    sensor = Sensor(width=1920, height=1080)
    sensor.reset()

    # 鼠标悬停在函数上可以查看允许接收的参数
    sensor.set_framesize(width=1920, height=1080)
    sensor.set_pixformat(Sensor.RGB565)

    Display.init(Display.LT9611, to_ide=True)
    # 初始化媒体管理器
    MediaManager.init()
    # 启动 sensor
    sensor.run()

    fpioa = FPIOA()
    fpioa.help()
    # 设置按键
    fpioa.set_function(53, FPIOA.GPIO53)
    key = Pin(53, Pin.IN, Pin.PULL_DOWN)

    #设置舵机和激光笔
    fpioa.set_function(33, FPIOA.GPIO33)
    fpioa.set_function(46, FPIOA.PWM2)
    fpioa.set_function(42, FPIOA.PWM0)
    pin = Pin(33, Pin.OUT)
    pin.value(0)

    #上下转
    pwm_2 = PWM(2, 50)
    pwm_2.duty(1.5/20*100)
    pwm_2.enable(1)

    #左右转
    pwm_0 = PWM(0, 50)
    pwm_0.duty(1.6/20*100)
    pwm_0.enable(1)

    clock = time.clock()

    flag = 0
    c_x = 320
    c_y = 320

    pid_x = PID(-0.002, -0.0003, 1.5/20*100, c_x)
    pid_y = PID(-0.002, -0.0003, 1.5/20*100, c_y)

    while True:
        clock.tick()
        os.exitpoint()
        img = sensor.snapshot(chn=CAM_CHN_ID_0)
        img = img.copy(roi=(540, 300, 520, 520))
#        # 绘制方框，参数依次为：x, y, w, h, 颜色，线宽，是否填充
#        img.draw_rectangle(1000, 50, 300, 200, color=(0, 0, 255), thickness=4, fill=False)
        if key.value() == 1:
            time.sleep_ms(2000)
            for i in range(5):
                img = sensor.snapshot(chn=CAM_CHN_ID_0)
                img = img.copy(roi=(540, 300, 520, 520))
                img_rect = img.to_grayscale(copy=True)
                img_rect = img_rect.binary([(59, 246)])
                rects = img_rect.find_rects(threshold=10000)

                if not rects == None:
                    for rect in rects:
                        corner = rect.corners()
                        img.draw_line(corner[0][0], corner[0][1], corner[1][0], corner[1][1], color=(0, 255, 0), thickness=5)
                        img.draw_line(corner[2][0], corner[2][1], corner[1][0], corner[1][1], color=(0, 255, 0), thickness=5)
                        img.draw_line(corner[2][0], corner[2][1], corner[3][0], corner[3][1], color=(0, 255, 0), thickness=5)
                        img.draw_line(corner[0][0], corner[0][1], corner[3][0], corner[3][1], color=(0, 255, 0), thickness=5)
                        c_x = sum([corner[k][0] for k in range(4)])/4
                        c_y = sum([corner[k][1] for k in range(4)])/4
                if len(rects) == 2:
                    img.compressed_for_ide()
                    Display.show_image(img)
                    print("center_point: {}".format([round(c_x), round(c_y)]))
                    flag = 1
                    time.sleep_ms(3000)
                    pid_x.target = c_x
                    pid_y.target = c_y
                    break
            if flag == 0:
                print("识别错误")
        if flag == 1:
            pin.value(1)
            img = sensor.snapshot(chn=CAM_CHN_ID_0)
            img = img.copy(roi=(540, 300, 520, 520))
            blobs = img.find_blobs([(47, 80, 9, 91, -55, 63), (16, 37, 23, 74, -48, 52)], False,\
                                   (0, 0, 640, 640), x_stride=1, y_stride=1, \
                                   pixels_threshold=40, margin=False)
            for blob in blobs:
                img.draw_rectangle(blob.x(), blob.y(), blob.w(), blob.h(), color=(0, 255, 0), thickness=2, fill=False)
                c_x = blob.x() + blob.w() / 2
                c_y = blob.y() + blob.h() / 2
                new_duty = pid_x.cal(c_x)
                if new_duty > 2.5/20*100:
                    new_duty = 2.5/20*100
                if new_duty < 0.5/20*100:
                    new_duty = 0.5/20*100
                pwm_0.enable(0)
                pwm_0.duty(round(new_duty, 2))

                pwm_0.enable(1)
                new_duty = pid_y.cal(c_y)
                if new_duty > 2.5/20*100:
                    new_duty = 2.5/20*100
                if new_duty < 0.5/20*100:
                    new_duty = 0.5/20*100
                pwm_2.enable(0)
                pwm_2.duty(round(new_duty, 2))
                print(round(new_duty, 1))
                pwm_2.enable(1)
                break

        img.draw_string_advanced(50, 50, 80, "fps: {}".format(clock.fps()), color=(255, 0, 0))
        img.compressed_for_ide()
        Display.show_image(img)

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
