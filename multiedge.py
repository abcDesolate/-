import time, os, sys
from media.sensor import *
from media.display import *
from media.media import *
from machine import UART
from machine import FPIOA

sensor_id = 2
DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480
# Lab色彩空间阈值
try:
    # 配置引脚
    fpioa = FPIOA()
    fpioa.set_function(11, FPIOA.UART2_TXD)
    fpioa.set_function(12, FPIOA.UART2_RXD)

    # 初始化UART2，波特率115200，8位数据位，无校验，1位停止位
    uart = UART(UART.UART2, baudrate=115200, bits=UART.EIGHTBITS, parity=UART.PARITY_NONE, stop=UART.STOPBITS_ONE)

    sensor = Sensor(id=sensor_id)
    sensor.reset()
    sensor.set_framesize(width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, chn=CAM_CHN_ID_0)
    sensor.set_pixformat(Sensor.RGB565, chn=CAM_CHN_ID_0)

    Display.init(Display.ST7701, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)
    MediaManager.init()
    sensor.run()
    color_threshold = [(13, 26, -9, 0, -6, 8)]

    # 初始化扫描位置
    scan_x = 1
    roi_width = 75
    roi_height = 469

    # 创建存储坐标的列表
    all_x_coords = []
    all_y_coords = []


    start_time = time.time()
    while time.time() - start_time < 2:  # 等待2秒
        img = sensor.snapshot(chn=CAM_CHN_ID_0)

        countdown = 2 - int(time.time() - start_time)
        Display.show_image(img)
        time.sleep_ms(50)
    # ============= 结束调整时间 =============


    while scan_x < DISPLAY_WIDTH - roi_width:
        # 获取新的一帧图像
        img = sensor.snapshot(chn=CAM_CHN_ID_0)

        # 设置当前扫描区域
        current_roi = (scan_x, 1, roi_width, roi_height)

        # 在图像上画出当前扫描区域
        img.draw_rectangle(scan_x, 1, roi_width, roi_height, color=(255, 0, 0), thickness=1)

        # 在扫描区域内查找色块
        blobs = img.find_blobs(color_threshold, False, area_threshold=25,pixels_threshold=25, roi=current_roi, merge=True)

        # 处理找到的色块
        for blob_index, blob in enumerate(blobs):
            img.draw_rectangle(blob.x(), blob.y(), blob.w(), blob.h(), color=(0, 255, 0), thickness=2)

            # 计算色块中心点（所有色块都会添加）
            center_x = blob.x() + blob.w() // 2
            center_y = blob.y() + blob.h() // 2

            # 添加色块中心点到列表
            all_x_coords.append(center_x)
            all_y_coords.append(center_y)

            # 打印中心点坐标
            print(center_x)  # 单独打印x坐标
            print(center_y)  # 单独打印y坐标

            # 对于高度大于150的色块，进行7等分处理
            if blob.h() > 250:
                segments = 7
                segment_height = blob.h() // segments

                # 绘制等分线并收集等分点
                for i in range(1, segments):
                    split_y = blob.y() + i * segment_height
                    img.draw_line(
                        blob.x(), split_y,
                        blob.x() + blob.w(), split_y,
                        color=(255, 255, 0), thickness=2
                    )

                # 处理每个等分区域
                for seg in range(segments):
                    seg_y = blob.y() + seg * segment_height
                    seg_center_x = center_x  # 使用色块中心x坐标
                    seg_center_y = seg_y + segment_height // 2

                    # 将等分点添加到列表
                    all_x_coords.append(seg_center_x)
                    all_y_coords.append(seg_center_y)

                    # 打印等分点坐标
                    print(seg_center_x)  # 单独打印x坐标
                    print(seg_center_y)  # 单独打印y坐标


        # 显示图像
        Display.show_image(img)

        # 更新扫描位置
        scan_x += 30  # 每次移动20个像素
        time.sleep_ms(20)

    # ============= 改进的数据处理步骤 =============
    # 处理连续多组segment产生的重复x坐标
    processed_x_coords = []
    processed_y_coords = []

    i = 0
    while i < len(all_x_coords):
        # 检查当前位置是否是一个segment组的开始
        # 一个segment组由8个点组成：1个中心点 + 7个等分点
        if i + 7 < len(all_x_coords) and all_x_coords[i] == all_x_coords[i + 7]:
            # 找到连续相同x坐标的segment组的结束位置
            group_count = 1
            j = i + 8  # 移动到下一组开始位置

            # 计算连续相同x坐标的segment组数量
            while j < len(all_x_coords):
                # 检查是否还有完整的下一组（8个点）
                if j + 7 >= len(all_x_coords):
                    break

                # 检查下一组的x坐标是否相同
                if all_x_coords[j] == all_x_coords[i]:
                    group_count += 1
                    j += 8  # 移动到再下一组
                else:
                    break

            # 如果连续组数达到3组或以上
            if group_count >= 3:
                # 计算中间组的起始位置
                middle_group_index = i + (group_count // 2) * 8

                # 添加中间组的8个点（1个中心点 + 7个等分点）
                processed_x_coords.extend(all_x_coords[middle_group_index:middle_group_index + 8])
                processed_y_coords.extend(all_y_coords[middle_group_index:middle_group_index + 8])

                # 跳过所有连续组
                i = i + group_count * 8
                continue
            else:
                # 组数不足3组，保留所有点
                processed_x_coords.extend(all_x_coords[i:j])
                processed_y_coords.extend(all_y_coords[i:j])
                i = j
        else:
            # 如果不是segment组或组不完整，直接添加当前点
            processed_x_coords.append(all_x_coords[i])
            processed_y_coords.append(all_y_coords[i])
            i += 1

    # 使用处理后的坐标
    all_x_coords = processed_x_coords
    all_y_coords = processed_y_coords
    # ============= 数据处理结束 =============

    # 扫描结束后打印所有坐标（分别打印）
    print("处理后的X坐标列表:")
    for x in all_x_coords:
        print(x)  # 单独打印每个x坐标

    print("\n处理后的Y坐标列表:")
    for y in all_y_coords:
        print(y)  # 单独打印每个y坐标

    # ============= 添加串口发送功能 =============
    # 通过串口发送所有坐标点
    for i in range(len(all_x_coords)):
        # 构造"x,y\n"格式的字符串
        coord_str = f"{all_x_coords[i]},{all_y_coords[i]}\n"

        uart.write(coord_str.encode())

        time.sleep_ms(10)
    # ============= 串口发送结束 =============

    uart.deinit()


except Exception as e:
    print("Error:", e)
