import time, os, sys
from media.sensor import *
from media.display import *
from media.media import *
from machine import UART
from machine import FPIOA

# 配置引脚
fpioa = FPIOA()
fpioa.set_function(11, FPIOA.UART2_TXD)
fpioa.set_function(12, FPIOA.UART2_RXD)
uart = UART(UART.UART2, baudrate=115200, bits=UART.EIGHTBITS, parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE)
picture_width = 800
picture_height = 480

sensor_id = 2
sensor = None

# 显示模式选择
DISPLAY_MODE = "LCD"
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480
# 图像处理参数
BLACK_BLOCK_THRESHOLD = [(0, 60, -128, 127, -128, 127)]  # 黑色方块的颜色阈值
Green_BLOCK_THRESHOLD = [(74, 83, -51, -20, 16, 37), (87, 92, -47, -33, 6, 26),
                         (86, 94, -68, -48, 24, 52), (53, 64, -46, -22, 16, 36),
                         (53, 68, -63, -46, 30, 57),(62, 79, -78, -12, 3, 68)]
Red_BLOCK_THRESHOLD = [(51, 73, 2, 49, -14, 19),(24, 65, 18, 69, -2, 35)]
# 定义全局变量
x_start = 0
y_start = 0
img = None
detection_width = 10  # 检测区域宽度（像素）
scan_step = 10        # 正常扫描步长
precision_step = 10   # 精确定位步长
is_precision_mode = False  # 精确定位模式标志
height_threshold = 60    # 色块高度切分阈值（像素）
split_height = 30         # 切分后每个小区域的高度（像素）
scan_flag = -1
point0 = []  # 横向扫描点集
point1 = []  # 纵向扫描点集
contour_points = []  # 轮廓点集
point_Num = 0
time_flag = 0
green_detect_timeout = 0
MAX_GREEN_TIMEOUT = 100  # 约3秒 (100 * 30ms)

# 提取轮廓点函数
def extract_contour_points(horizontal_points, vertical_points, grid_size=10, tolerance=10):
    contour_points = []
    grid_dict = {}
    for hp in horizontal_points:
        for vp in vertical_points:
            distance = ((hp[0] - vp[0])**2 + (hp[1] - vp[1])**2)**0.5
            if distance < tolerance:
                avg_x = (hp[0] + vp[0]) // 2
                avg_y = (hp[1] + vp[1]) // 2
                grid_x = avg_x // grid_size
                grid_y = avg_y // grid_size
                grid_key = f"{grid_x},{grid_y}"
                if grid_key not in grid_dict:
                    grid_dict[grid_key] = (avg_x, avg_y)
                    contour_points.append((avg_x, avg_y))
                break
    return contour_points

try:
    sensor = Sensor(id=sensor_id)
    sensor.reset()
    sensor.set_framesize(width=picture_width, height=picture_height, chn=0)
    sensor.set_pixformat(Sensor.RGB565, chn=0)

    Display.init(Display.ST7701, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)
    MediaManager.init()
    sensor.run()

    while True:
        os.exitpoint()
        if time_flag == 0:
            time_flag = 1
            time.sleep(1.1)  # 初始延时

        img = sensor.snapshot(chn=0)

        # 绿色块检测 - 作为启动扫描的触发条件
        if scan_flag == -1:
            green_detect_timeout += 1
            if green_detect_timeout > MAX_GREEN_TIMEOUT:
                scan_flag = 0
            else:
                green_blobs = img.find_blobs(
                    Green_BLOCK_THRESHOLD,
                    pixels_threshold=100,
                    area_threshold=100,
                    merge=True
                )
                if green_blobs:
                    max_blob = None
                    max_area = 0
                    for blob in green_blobs:
                        if blob.area() > max_area:
                            max_area = blob.area()
                            max_blob = blob

                    img.draw_rectangle(max_blob.x(), max_blob.y(), max_blob.w(), max_blob.h(), (0, 255, 0), thickness=3)
                    img.draw_cross(max_blob.cx(), max_blob.cy(), size=10, color=(0, 255, 0))
                    uart.write("g,{},{}\n".format(max_blob.x(), max_blob.y()))
                    scan_flag = 0

        # 横向扫描
        if scan_flag == 0:
            if is_precision_mode:
                if x_start >= picture_width - detection_width - 10:
                    x_start = 0
                    scan_flag = 1
                else:
                    x_start += precision_step
            else:
                if x_start >= picture_width - detection_width - 10:
                    scan_flag = 1
                else:
                    x_start += scan_step

            gray_img = img.to_grayscale()
            binary_img = gray_img.binary([(60, 255)])

            blobs = binary_img.find_blobs(
                BLACK_BLOCK_THRESHOLD,
                x_stride=2, y_stride=2,
                pixels_threshold=15,
                area_threshold=25,
                merge=True,
                roi=(x_start, 0, detection_width, picture_height)
            )

            if blobs:
                for blob in blobs:
                    x, y, w, h = blob.x(), blob.y(), blob.w(), blob.h()
                    center_x = x + w // 2
                    center_y = y + h // 2
                    img.draw_rectangle(x, y, w, h, (0, 255, 0), thickness=2)
                    img.draw_cross(center_x, center_y, size=5, color=(255, 0, 0))
                    if h > height_threshold:
                        split_count = h // split_height
                        if h % split_height > 0:
                            split_count += 1
                        for i in range(split_count):
                            split_y = y + i * split_height
                            current_height = min(split_height, h - i * split_height)
                            split_center_x = center_x
                            split_center_y = split_y + current_height // 2
                            img.draw_rectangle(x, split_y, w, current_height, (255, 255, 0), thickness=1)
                            img.draw_cross(split_center_x, split_center_y, size=3, color=(0, 0, 255))
                            point0.append((split_center_x, split_center_y))
                            point_Num += 1
                    else:
                        point0.append((center_x, center_y))
                        point_Num += 1

            img.draw_rectangle(x_start, 0, detection_width, picture_height, (255, 0, 0), thickness=1)

        # 纵向扫描
        elif scan_flag == 1:
            if is_precision_mode:
                if y_start >= picture_height - detection_width - 10:
                    y_start = 0
                    scan_flag = 2
                else:
                    y_start += precision_step
            else:
                if y_start >= picture_height - detection_width - 10:
                    scan_flag = 2
                else:
                    y_start += scan_step

            gray_img = img.to_grayscale()
            binary_img = gray_img.binary([(60, 255)])

            blobs = binary_img.find_blobs(
                BLACK_BLOCK_THRESHOLD,
                x_stride=2, y_stride=2,
                pixels_threshold=15,
                area_threshold=25,
                merge=True,
                roi=(0, y_start, picture_width, detection_width)
            )

            if blobs:
                for blob in blobs:
                    x, y, w, h = blob.x(), blob.y(), blob.w(), blob.h()
                    center_x = x + w // 2
                    center_y = y + h // 2
                    img.draw_rectangle(x, y, w, h, (0, 255, 0), thickness=2)
                    img.draw_cross(center_x, center_y, size=5, color=(255, 0, 0))
                    if w > height_threshold:
                        split_count = w // split_height
                        if w % split_height > 0:
                            split_count += 1
                        for i in range(split_count):
                            split_x = x + i * split_height
                            current_width = min(split_height, w - i * split_height)
                            split_center_x = split_x + current_width // 2
                            split_center_y = center_y
                            img.draw_rectangle(split_x, y, current_width, h, (255, 255, 0), thickness=1)
                            img.draw_cross(split_center_x, split_center_y, size=3, color=(0, 0, 255))
                            point1.append((split_center_x, split_center_y))
                            point_Num += 1
                    else:
                        point1.append((center_x, center_y))
                        point_Num += 1

            img.draw_rectangle(0, y_start, picture_width, detection_width, (255, 0, 0), thickness=1)

        # 提取轮廓点并发送
        elif scan_flag == 2:
            contour_points = extract_contour_points(point0, point1, grid_size=10, tolerance=10)
            for p in contour_points:
                message = f"{p[0]},{p[1]}\n"
                uart.write(message)
            uart.write("\\")
            scan_flag = 3

        if img:
            Display.show_image(
                img,
                x=int((DISPLAY_WIDTH - picture_width) / 2),
                y=int((DISPLAY_HEIGHT - picture_height) / 2)
            )

        time.sleep_ms(30)

except KeyboardInterrupt:
    pass
finally:
    if sensor:
        sensor.stop()
    Display.deinit()
    MediaManager.deinit()
