from detector import Detector
from media.sensor import CAM_CHN_ID_2  # 导入缺失的常量

def main():
    det = Detector()
    try:
        det.run()  # 使用Detector封装好的运行逻辑
    except KeyboardInterrupt:
        print("Interrupted by user, exiting.")
    finally:
        det.cleanup()

if __name__ == "__main__":
    main()
