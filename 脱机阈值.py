import sensor,display
import image
import time

# 初始化摄像头
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)  # 160x120分辨率

sensor.skip_frames(time=2000)  # 等待摄像头稳定
lcd = display.SPIDisplay()  # 初始化 LCD
# 自动阈值计算函数
def calculate_threshold(roi, sample_frames=150):
    """
    自动计算指定ROI区域的LAB颜色阈值
    :param roi: 感兴趣区域 (x, y, w, h)
    :param sample_frames: 采样帧数，默认为150帧
    :return: LAB颜色阈值 [Lmin, Lmax, Amin, Amax, Bmin, Bmax]
    """
    threshold = [0, 0, 0, 0, 0, 0]
    print(f"开始计算阈值，采样帧数: {sample_frames}...")

    for _ in range(sample_frames):
        img = sensor.snapshot()

        # 在图像上标记采样区域
        img.draw_rectangle(roi, color=(0, 255, 0), thickness=2)
        img.draw_string(roi[0], roi[1] - 15, "Sampling...", color=(0, 255, 0), scale=1)

        # 获取区域颜色直方图
        hist = img.get_histogram(roi=roi)

        # 获取颜色分布的5%和95%分位值
        lo = hist.get_percentile(0.05)
        hi = hist.get_percentile(0.95)

        # 累加并平均阈值
        threshold[0] = (threshold[0] + lo.l_value()) // 2
        threshold[1] = (threshold[1] + hi.l_value()) // 2
        threshold[2] = (threshold[2] + lo.a_value()) // 2
        threshold[3] = (threshold[3] + hi.a_value()) // 2
        threshold[4] = (threshold[4] + lo.b_value()) // 2
        threshold[5] = (threshold[5] + hi.b_value()) // 2

    return threshold

# 设置ROI区域 - 用于计算阈值的区域
threshold_roi = (70, 50, 20, 20)  # 中心位置附近

# 自动计算阈值（只执行一次）
threshold = calculate_threshold(threshold_roi)

# 主循环 - 在整个图像中进行颜色识别
while True:
    img = sensor.snapshot()
    print(threshold)
    # 在整个图像中查找匹配阈值的色块
    blobs = img.find_blobs([threshold],
                          pixels_threshold=50,   # 最小像素数
                          area_threshold=50,     # 最小面积
                          merge=True)            # 合并相邻色块



    if blobs:
        # 找到最大色块
        max_blob = max(blobs, key=lambda b: b.area())

        # 绘制矩形框和中心点
        img.draw_rectangle(max_blob.rect(), color=(0, 255, 0))
        img.draw_cross(max_blob.cx(), max_blob.cy(), color=(255, 0, 0))

        # 显示检测信息
        info = f"Pos:({max_blob.cx()},{max_blob.cy()}) Size:{max_blob.w()}x{max_blob.h()}"
        img.draw_string(0, 0, "Target Detected", color=(0, 255, 0))
        img.draw_string(0, 15, info, color=(255, 255, 0))

        # 在色块中心显示LAB值
        lab = img.get_pixel(max_blob.cx(), max_blob.cy())
        img.draw_string(max_blob.cx() + 10, max_blob.cy(), f"L:{lab[0]} A:{lab[1]} B:{lab[2]}", color=(255, 255, 0))

        print(f"目标位置: ({max_blob.cx()}, {max_blob.cy()}), 尺寸: {max_blob.w()}x{max_blob.h()}")
    else:
        img.draw_string(0, 0, "No Target", color=(255, 0, 0))
        print("未检测到目标")

    time.sleep_ms(50)  # 控制刷新率
    lcd.write(img)
