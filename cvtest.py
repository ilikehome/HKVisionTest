import cv2
from ultralytics import YOLO

def detect_pose_in_jpg(jpg_path):
    model = YOLO('yolov8n-pose.pt')
    img = cv2.imread(jpg_path)
    results = model(img)
    annotated_img = results[0].plot()
    cv2.imshow('Pose Detection', annotated_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

if __name__ == '__main__':
    jpg_path = '1.jpg'
    detect_pose_in_jpg(jpg_path)