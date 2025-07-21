import sensor
import image
import time
from pyb import UART
from machine import LED
from pyb import Pin

QR_MAPPING = {
    'M': 1, 'x': 2, 'j': 3, 'X': 4,
    'V': 5, 'y': 6, 'K': 7, 'v': 8,
    '8': 9, 'J': 10, 'N': 11, 'Q': 12
}

# 状态机常量
SCAN_MODE = 0
TARGET_MODE = 1

def setup():
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.skip_frames(time=2000)
    sensor.set_auto_gain(False)
    return UART(3, 9600), Pin('P7', Pin.OUT_PP)

def extract_key(url):
    parts = url.split('/')
    if len(parts) >= 2:
        key_part = parts[-2]
        return key_part[-1] if key_part else None
    return None

def main():
    uart, p_out = setup()
    LED("LED_BLUE").on()

    # 状态机变量
    current_mode = SCAN_MODE
    target_value = None
    target_counter = 0

    # 扫描模式变量
    last_sent = None
    continuous_counter = 0
    scan_threshold = 12

    # 目标模式参数
    target_threshold = 10

    while True:
        img = sensor.snapshot()
        codes = img.find_qrcodes()

        if codes:
            current = codes[0].payload()
            if (key := extract_key(current)) and (raw := QR_MAPPING.get(key)):
                num = raw * 10
                rect = codes[0].rect()

                if current_mode == SCAN_MODE:
                    # 更新连续计数器
                    if num == last_sent:
                        continuous_counter += 1
                    else:
                        continuous_counter = 1
                        last_sent = num
                        # 新数值立即发送一次
                        uart.write(bytes([num]))
                        p_out.high()
                        time.sleep_ms(8)
                        p_out.low()

                    # 检查模式切换条件
                    if continuous_counter >= scan_threshold:
                        current_mode = TARGET_MODE
                        target_value = num
                        target_counter = 0

                elif current_mode == TARGET_MODE:
                    if num == target_value:
                        target_counter += 1
                        if target_counter >= target_threshold:
                            # 目标确认成功，发送并重置
                            uart.write(bytes([target_value]))
                            p_out.high()
                            time.sleep_ms(8)
                            p_out.low()
                            current_mode = SCAN_MODE
                            last_sent = None
                            target_value = None
                            target_counter = 0
                    else:
                        # 目标不一致，返回扫描模式
                        current_mode = SCAN_MODE
                        last_sent = None
                        target_value = None
                        target_counter = 0

                # 绘制调试信息
                img.draw_rectangle(rect, color=(255,0,0))
                mode_str = "SCAN" if current_mode == SCAN_MODE else "TARGET"
                counter = continuous_counter if current_mode == SCAN_MODE else target_counter
                status = f"{mode_str} | {raw}->{num} | C:{counter}"
                img.draw_string(10, 10, status, color=(255,0,0))

        else:
            # 没有识别到二维码时处理目标模式超时
            if current_mode == TARGET_MODE:
                current_mode = SCAN_MODE
                target_value = None
                target_counter = 0

        time.sleep_ms(15)

if __name__ == "__main__":
    main()
