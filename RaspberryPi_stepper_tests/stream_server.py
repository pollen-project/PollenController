import io
import logging
import socketserver
from http import server
from threading import Condition
import time
import numpy as np
import cv2
import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
from libcamera import controls
import threading

PAGE = """\
<html>
<head>
<title>picamera2 MJPEG streaming demo</title>
</head>
<body>
<h1>Picamera2 MJPEG Streaming Demo</h1>
<img src="stream.mjpg" width="640" height="480" />
</body>
</html>
"""
GPIO_pins = (14, 15, 18)  # Microstep Resolution MS1-MS3 -> GPIO Pin
direction = 27  # Direction -> GPIO Pin
step = 17  # Step -> GPIO Pin
STEP_SIZE = 150  # Adjust step size for the motor
MAX_STEPS = 1500  # Max number of steps to prevent an endless loop
motor = RpiMotorLib.A4988Nema(direction, step, GPIO_pins, "A4988")

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                logging.warning(
                    'Removed streaming client %s: %s',
                    self.client_address, str(e))
        else:
            self.send_error(404)
            self.end_headers()


class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def start_streaming_server(picam2):
    """Run the stream server while using the given Picamera2 instance."""
    picam2.set_controls(
        {
            "AfMode": controls.AfModeEnum.Manual, "LensPosition": 10.0,
        }
    )
    global output
    output = StreamingOutput()  # Initialize output here
    picam2.start_recording(JpegEncoder(), FileOutput(output))
    try:
        address = ('', 8080)
        server = StreamingServer(address, StreamingHandler)
        server.serve_forever()
    finally:
        picam2.stop_recording()


# def perform_autofocus(picam2):                        //this was used for testing/prototyping and can be deleted
#     """Trigger autofocus using the camera."""
#     print("Triggering autofocus...")
#     # Capture an image
#     image = picam2.capture_array()

#     # Calculate sharpness and adjust lens position
#     sharpness = calculate_sharpness(image)
#     print(f"Sharpness: {sharpness}")
#     adjust_focus(sharpness, picam2)


def calculate_sharpness(image):
    """Calculate sharpness using the Laplacian Variance method."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return np.var(laplacian)


def hill_climb_focus(picam2):
    """Perform hill climbing to find the optimal focus position."""
    best_position = 0
    best_sharpness = 0
    current_position = 0
    step_size = STEP_SIZE
    direction = 1  # 1 for forward, -1 for backward

    print("Starting autofocus...")

    for _ in range(MAX_STEPS):
        # Move stepper motor (this can be connected to motor controls)
        motor_move(step_size * direction)  # Move the motor by step_size * direction
        time.sleep(0.8)  # Wait for vibrations to settle

        # Capture and evaluate sharpness
        image = picam2.capture_array()
        sharpness = calculate_sharpness(image)
        print(f"Position: {current_position}, Sharpness: {sharpness}")

        if sharpness > best_sharpness:
            best_sharpness = sharpness
            best_position = current_position
        else:
            # Reverse direction and decrease step size
            direction *= -1
            step_size = max(1, step_size // 2)

        current_position += step_size * direction

        # Stop if step size is too small and sharpness is not improving
        if step_size == 1 and sharpness <= best_sharpness:
            break

    # Move to the best focus position
    motor_move(best_position - current_position)
    print(f"Best Focus Position: {best_position}, Sharpness: {best_sharpness}")


def motor_move(steps):
    motor.motor_go(False, "Full", steps, .01, False, .05)
    print(f"Motor moved by {steps} steps")


def listen_for_focus_command(picam2):
    """Listen for 'focus' command from terminal and trigger autofocus."""
    while True:
        command = input("Enter command: ").strip().lower()
        if command == "focus":
            hill_climb_focus(picam2)
        elif command == "exit":
            print("Exiting...")
            break
        else:
            print("Unknown command. Type 'focus' to trigger autofocus or 'exit' to quit.")


if __name__ == "__main__":
    # Initialize Picamera2
    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))

    # Start the streaming server in a separate thread
    threading.Thread(target=start_streaming_server, args=(picam2,), daemon=True).start()

    # Start listening for focus command in the main thread
    listen_for_focus_command(picam2)
