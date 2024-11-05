import cv2
import numpy as np
from ultralytics import YOLO

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
    jpg_path = '1.jpg'
    detect_pose_in_jpg(jpg_path)