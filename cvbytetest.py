import time

import cv2
import numpy as np
from ultralytics import YOLO

from hk_connector import HkConnector


def detect_pose_in_jpg(jpg_path):
    model = YOLO('yolov8n-pose.pt')
    with open(jpg_path, 'rb') as f:
        binary_data = f.read()
    img = cv2.imdecode(np.frombuffer(binary_data, np.uint8), cv2.IMREAD_COLOR)
    results = model(img)
    annotated_img = results[0].plot()
    cv2.imshow('Pose Detection', annotated_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == '__main__':
    #jpg_path = '1.jpg'
    #detect_pose_in_jpg(jpg_path)

    model = YOLO('yolov8n-pose.pt')

    dev = HkConnector()
    dev.init_dll()  # 设置SDK初始化依赖库路径
    dev.hikSDK.NET_DVR_Init()  # 初始化sdk
    dev.hk_log_setting()  # 通用设置，日志，回调函数等
    dev.login_dev(ip=b'169.254.43.56', username=b"admin", pwd=b"tongda2024")  # 登录设备
    dev.start_play()
    time.sleep(5)
    while True:
        frame = dev.get_frame()
        img = cv2.imdecode(np.frombuffer(frame, np.uint8), cv2.IMREAD_COLOR)
        results = model(img)
        annotated_img = results[0].plot()
        cv2.imshow('Pose Detection', annotated_img)
        cv2.waitKey(1)
    cv2.destroyAllWindows()