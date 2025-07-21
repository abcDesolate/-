import sensor, image, time
from machine import UART

uart = UART(3,115200)

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)
sensor.skip_frames(time = 2000)

clock = time.clock()
# 初始化标志位
flag_find_first_rect = False
flag_find_second_rect = False
data_sent = False  # 新增标志位，用于标记数据是否已发送
first_rect_corners = [[0,0] for _ in range(4)]
second_rect_corners = [[0,0] for _ in range(4)]
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
        img.draw_rectangle(roi, color=(0, 255, 0), thickness=1)
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
threshold_roi = (50, 50, 15, 15)  # 中心位置附近

# 自动计算阈值（只执行一次）
#threshold = calculate_threshold(threshold_roi)
threshold =(53, 95, -86, -24, 16, 82)
while(True):
    clock.tick()
    img = sensor.snapshot()
    img = img.gaussian(1)

    # 找内框
    if not flag_find_first_rect:
        for rect in img.find_rects(threshold=100000, x_gradient=20, y_gradient=20):
            if rect:
                flag_find_first_rect = True
                first_rect_corners = rect.corners()
                area = rect.magnitude()
                print("First rect area:", area)

    # 找外框
    if flag_find_first_rect and not flag_find_second_rect:
        for rect in img.find_rects(threshold=70000, x_gradient=20, y_gradient=20):
            if rect:
                area = rect.magnitude()
                print("Second rect area:", area)
                if area < 100000:
                    flag_find_second_rect = True
                    second_rect_corners = rect.corners()
                    break  # 找到后立即跳出循环

    # 当两个矩形都找到且数据未发送时，执行一次
    if flag_find_first_rect and flag_find_second_rect and not data_sent:
        # 绘制内框
        img.draw_line(first_rect_corners[0][0], first_rect_corners[0][1],
                     first_rect_corners[1][0], first_rect_corners[1][1],
                     color=(255, 255, 255))
        img.draw_line(first_rect_corners[1][0], first_rect_corners[1][1],
                     first_rect_corners[2][0], first_rect_corners[2][1],
                     color=(255, 255, 255))
        img.draw_line(first_rect_corners[2][0], first_rect_corners[2][1],
                     first_rect_corners[3][0], first_rect_corners[3][1],
                     color=(255, 255, 255))
        img.draw_line(first_rect_corners[3][0], first_rect_corners[3][1],
                     first_rect_corners[0][0], first_rect_corners[0][1],
                     color=(255, 255, 255))
        # 绘制外框
        img.draw_line(second_rect_corners[0][0], second_rect_corners[0][1],
                     second_rect_corners[1][0], second_rect_corners[1][1],
                     color=(255, 255, 255))
        img.draw_line(second_rect_corners[1][0], second_rect_corners[1][1],
                     second_rect_corners[2][0], second_rect_corners[2][1],
                     color=(255, 255, 255))
        img.draw_line(second_rect_corners[2][0], second_rect_corners[2][1],
                     second_rect_corners[3][0], second_rect_corners[3][1],
                     color=(255, 255, 255))
        img.draw_line(second_rect_corners[3][0], second_rect_corners[3][1],
                     second_rect_corners[0][0], second_rect_corners[0][1],
                     color=(255, 255, 255))
        # 标记内框顶点（绿色）
        for p in first_rect_corners:
            img.draw_circle(p[0], p[1], 3, color=(0, 255, 0))

        # 标记外框顶点（红色）
        for p in second_rect_corners:
            img.draw_circle(p[0], p[1], 3, color=(255, 0, 0))

        # 发送内框数据（后3个点相对于第一个点的偏移）
        for i in range(1, 4):
            dx = first_rect_corners[i][0] - first_rect_corners[0][0]
            dy = first_rect_corners[i][1] - first_rect_corners[0][1]
            data = bytearray([0xA3, 0xB3, dx & 0xFF, dy & 0xFF, 0xC3])
            uart.write(data)
            print("Sent inner:", dx, dy)

        # 发送外框数据（4个点相对于第一个点的偏移）
        for i in range(0, 4):
            dx = second_rect_corners[i][0] - second_rect_corners[0][0]
            dy = second_rect_corners[i][1] - second_rect_corners[0][1]
            data = bytearray([0xA3, 0xB3, dx & 0xFF, dy & 0xFF, 0xC3])
            uart.write(data)
            print("Sent outer:", dx, dy)

        # 标记数据已发送
        data_sent = True
        print("Data sent once!")
    blobs = img.find_blobs([threshold],
                            pixels_threshold=50,   # 最小像素数
                            area_threshold=50,     # 最小面积
                            merge=True)            # 合并相邻色块
    print(threshold)
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
