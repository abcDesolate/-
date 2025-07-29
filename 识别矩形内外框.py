# Untitled - By: ZhouLongTao - Sat Jul 20 2024
import sensor, image, time
sensor.reset()
sensor.set_pixformat(sensor.RGB565) # 灰度更快(160x120 max on OpenMV-M7)
sensor.set_framesize(sensor.QQVGA)
sensor.skip_frames(time = 2000)
sensor.set_vflip(True)          # 视角垂直翻转
sensor.set_hmirror(True)        # 视角水平翻转
clock = time.clock()
flag_find_first_rect = False
flag_find_second_rect = False
first_rect_corners = [[0,0] for _ in range(4)]
second_rect_corners =[[0,0] for _ in range(4)]
while(True):
    clock.tick()
    img = sensor.snapshot()
    img = img.gaussian(1)
    # 找内框
    if flag_find_first_rect == False:
        # threshold 参数用于设置检测阈值(threshold大小和要检测矩形的像素大小有关，将阈值设定在要检测矩形的面积范围内可以减少外界其他噪声)
        # x_gradient 和 y_gradient 参数用于设置边缘梯度阈值（x_gradient 和 y_gradient越大识别越准确但耗费时间越长，x_gradient 和 y_gradient越小越快但干扰性大）
        # 两者都和环境亮度有关
        # 找矩形调整threshold，x_gradient, y_gradient这三个值
        for rect in img.find_rects(threshold = 80000, x_gradient=20, y_gradient=20):
            if rect:
                flag_find_first_rect = True
                # 获取矩形的四个角的坐标
                first_rect_corners = rect.corners()
                area = rect.magnitude() #矩形像素面积大小
                print(area)
    # 找外框
    if flag_find_first_rect == True:
        if flag_find_second_rect == False:
            for rect in img.find_rects(threshold = 50000, x_gradient=20, y_gradient=20):
                if rect:
                    area = rect.magnitude()
                    if area < 76000:
                        flag_find_second_rect = True
                        # 获取矩形的四个角的坐标
                        second_rect_corners = rect.corners()
                    print(area)
    if flag_find_first_rect == True and flag_find_second_rect == True:
        # 绘制内框矩形的四条边
        img.draw_line(first_rect_corners[0][0], first_rect_corners[0][1], first_rect_corners[1][0], first_rect_corners[1][1], color=(255, 255, 255))
        img.draw_line(first_rect_corners[1][0], first_rect_corners[1][1], first_rect_corners[2][0], first_rect_corners[2][1], color=(255, 255, 255))
        img.draw_line(first_rect_corners[2][0], first_rect_corners[2][1], first_rect_corners[3][0], first_rect_corners[3][1], color=(255, 255, 255))
        img.draw_line(first_rect_corners[3][0], first_rect_corners[3][1], first_rect_corners[0][0], first_rect_corners[0][1], color=(255, 255, 255))
        # 圈出内框顶点
        for p in first_rect_corners:
            img.draw_circle(p[0], p[1], 3, color = (0, 255, 0))
        # 绘制外框矩形的四条边
        img.draw_line(second_rect_corners[0][0], second_rect_corners[0][1], second_rect_corners[1][0], second_rect_corners[1][1], color=(255, 255, 255))
        img.draw_line(second_rect_corners[1][0], second_rect_corners[1][1], second_rect_corners[2][0], second_rect_corners[2][1], color=(255, 255, 255))
        img.draw_line(second_rect_corners[2][0], second_rect_corners[2][1], second_rect_corners[3][0], second_rect_corners[3][1], color=(255, 255, 255))
        img.draw_line(second_rect_corners[3][0], second_rect_corners[3][1], second_rect_corners[0][0], second_rect_corners[0][1], color=(255, 255, 255))
        # 圈出外框顶点
        for p in second_rect_corners:
            img.draw_circle(p[0], p[1], 3, color = (255,0, 0))
