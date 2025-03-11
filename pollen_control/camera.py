# Initialize Picamera2
from picamera2 import Picamera2

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (1024, 768)}))  # (640, 480)
picam2.set_controls({"Saturation": 0.0})