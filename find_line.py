import time, os, sys

from media.sensor import *
from media.display import *
from media.media import *

picture_width = 400
picture_height = 240

sensor_id = 2
sensor = None

DISPLAY_WIDTH = 800
DISPLAY_HEIGHT = 480

def get_line_segment_points(line):
    # line.line() usually returns (x1, y1, x2, y2)
    return line.line()

def compute_intersection(line1, line2):
    # 获取两条线段的端点
    x1, y1, x2, y2 = get_line_segment_points(line1)
    x3, y3, x4, y4 = get_line_segment_points(line2)

    # 计算交点
    denom = (y4 - y3)*(x2 - x1) - (x4 - x3)*(y2 - y1)
    if denom == 0:
        return None

    ua = ((x4 - x3)*(y1 - y3) - (y4 - y3)*(x1 - x3)) / denom
    ub = ((x2 - x1)*(y1 - y3) - (y2 - y1)*(x1 - x3)) / denom

    # 交点仅在线段范围内时有效
    if 0 <= ua <= 1 and 0 <= ub <= 1:
        x = x1 + ua * (x2 - x1)
        y = y1 + ua * (y2 - y1)
        return int(x), int(y)
    return None

try:
    # 构造一个具有默认配置的摄像头对象
    sensor = Sensor(id=sensor_id)
    sensor.reset()
    sensor.set_framesize(width=picture_width, height=picture_height, chn=CAM_CHN_ID_0)
    sensor.set_pixformat(Sensor.GRAYSCALE)
    Display.init(Display.ST7701, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, to_ide=True)
    MediaManager.init()
    sensor.run()

    while True:
        os.exitpoint()
        img = sensor.snapshot(chn=CAM_CHN_ID_0)
        # 线段查找
        lines = img.find_line_segments(merge_distance=20, max_theta_diff=10)
        count = 0

        # 绘制所有线段
        for line in lines:
            img.draw_line(line.line(), color=(1, 147, 230), thickness=5)
            print(f"Line {count}: {line}")
            count += 1

        # 计算并绘制所有交点
        intersections = []
        for i in range(len(lines)):
            for j in range(i+1, len(lines)):
                pt = compute_intersection(lines[i], lines[j])
                if pt:
                    intersections.append(pt)
                    img.draw_circle(pt[0], pt[1], 6, color=(255, 0, 0), thickness=3)
                    print(f"Intersection at: {pt}")

        Display.show_image(img, x=int((DISPLAY_WIDTH - picture_width) / 2), y=int((DISPLAY_HEIGHT - picture_height) / 2))

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
