import sensor, image
from pyb import UART
from machine import LED
import time

# 蓝灯初始化
led = LED("LED_BLUE")
threshold_calculated = False  # 阈值计算标志
threshold_roi = (80, 60, 20, 20)  # 阈值采集区域
target_roi = (120, 80, 20, 20)    # 目标检测区域

#****************[1]-阈值获取函数********************
def get_threshold(roi):
    threshold = [0, 0, 0, 0, 0, 0]  # LAB阈值初始化
    for _ in range(50):
        img = sensor.snapshot()
        hist = img.get_histogram(roi=roi)
        img.draw_rectangle(roi, color=(0, 255, 0), thickness=2)
        img.draw_string(roi[0], roi[1]-10, "Calculating...", color=(0,255,0))

        lo = hist.get_percentile(0.05)
        hi = hist.get_percentile(0.95)  # 修正拼写错误：percentile

        # 累积平均计算阈值
        threshold[0] = (threshold[0] + lo.l_value()) // 2
        threshold[1] = (threshold[1] + hi.l_value()) // 2
        threshold[2] = (threshold[2] + lo.a_value()) // 2
        threshold[3] = (threshold[3] + hi.a_value()) // 2
        threshold[4] = (threshold[4] + lo.b_value()) // 2
        threshold[5] = (threshold[5] + hi.b_value()) // 2
    return tuple(threshold)  # 返回元组格式的阈值

#****************[2]-硬件初始化********************
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(30)
sensor.set_auto_gain(False)  # 关闭自动增益

uart = UART(1, 115200)       # 初始化串口
led.on()                     # 开启蓝灯指示

#****************[3]-主循环********************
while True:
    img = sensor.snapshot()

    # --- 二维码处理部分 ---
    codes = img.find_qrcodes()
    if codes:
        payload = codes[0].payload()  # 取第一个检测到的二维码
        uart.write(payload + "\n")    # 添加换行符方便接收
        print("Sent:", payload)

    # --- 阈值计算部分 ---
    if not threshold_calculated:
        try:
            threshold = get_threshold(threshold_roi)
            threshold_calculated = True
            print("Final Threshold:", threshold)
        except Exception as e:
            print("Threshold Error:", e)

    # --- 目标区域检测 ---
    if threshold_calculated:
        blobs = img.find_blobs([threshold], roi=target_roi, merge=True)
        result = 1 if blobs else 0

        # 可视化标注
        img.draw_rectangle(target_roi, color=(255,0,0), thickness=2)
        #if blobs:
         #   img.draw_cross(blobs[0].cx(), blobs[0].cy(), color=(0,255,0))

        #print(f"Check Result: {result}")

    time.sleep_ms(100)  # 降低CPU负载



