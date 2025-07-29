import time, os, sys
from media.sensor import *
from media.display import *
from media.media import *
from machine import UART
from machine import FPIOA
sensor_id = 2
sensor = None

fpioa = FPIOA()
fpioa.set_function(11, FPIOA.UART2_TXD)
fpioa.set_function(12, FPIOA.UART2_RXD)
uart = UART(UART.UART2, baudrate=115200, bits=UART.EIGHTBITS, parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE)

    # 3.1寸屏幕模式
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480

try:
    # 构造一个具有默认配置的摄像头对象
    sensor = Sensor(id=sensor_id)
    # 重置摄像头sensor
    sensor.reset()

    # 设置通道0的输出尺寸为显示分辨率
    sensor.set_framesize(width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, chn=CAM_CHN_ID_0)
    # 设置通道0的输出像素格式为RGB565
    sensor.set_pixformat(Sensor.RGB565, chn=CAM_CHN_ID_0)


    Display.init(Display.ST7701, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)

    # 初始化媒体管理器
    MediaManager.init()
    # 启动传感器
    sensor.run()

    blue_threshold = [(44, 100, -10, 44, -61, -40),(84, 100, -28, -17, -19, -5)]
    red_threshold = [(68, 76, 15, 52, -8, 9),(80, 87, -3, 35, -21, 13)]
    while True:
        os.exitpoint()

        # 捕获通道0的图像
        img = sensor.snapshot(chn=CAM_CHN_ID_0)

        # 查找蓝色色块
        blue_blobs = img.find_blobs(blue_threshold,area_threshold = 100,merge=True)
        # 如果检测到蓝色色块
        if blue_blobs:
            # 遍历每个检测到的蓝色色块
            for blob in blue_blobs:
                # 用蓝色绘制颜色块的外接矩形
                # blob[0:4] 表示颜色块的矩形框 [x, y, w, h]
                img.draw_rectangle(blob[0:4], color=(0, 0, 255))
                # 绘制中心十字
                img.draw_cross(blob[5], blob[6])
                # 通过串口发送带'b'前缀的坐标
                uart.write(f"c,{blob[5]},{blob[6]}\n")

        # 查找红色色块
        red_blobs = img.find_blobs(red_threshold,area_threshold = 100,merge=True)
        # 如果检测到红色色块
        if red_blobs:
            # 遍历每个检测到的红色色块
            for blob in red_blobs:
                # 用红色绘制颜色块的外接矩形
                img.draw_rectangle(blob[0:4], color=(255, 0, 0))
                # 绘制中心十字
                img.draw_cross(blob[5], blob[6])
                # 通过串口发送带'r'前缀的坐标
                uart.write(f"t,{blob[5]},{blob[6]}\n")

        # 显示捕获的图像，中心对齐，居中显示
        Display.show_image(img)

except KeyboardInterrupt as e:
    print("用户停止: ", e)
except BaseException as e:
    print(f"异常: {e}")
finally:
    # 停止传感器运行
    if isinstance(sensor, Sensor):
        sensor.stop()
    # 反初始化显示模块
    Display.deinit()
    os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
    time.sleep_ms(100)
    # 释放媒体缓冲区
    MediaManager.deinit()
