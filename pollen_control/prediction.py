from ultralytics import YOLO

yolo_model = YOLO('birch_1024_v14.pt')


def run_predict(image):
    detections = yolo_model.predict(image, conf=0.1)
    if len(detections) > 0:
        return detections[0].summary()
    else:
        return []
