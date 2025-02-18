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
sensor = 22
STEP_SIZE = 100  # Adjust step size for the motor
MAX_STEPS = 10000  # Max number of steps to prevent an endless loop
motor = RpiMotorLib.A4988Nema(direction, step, GPIO_pins, "A4988")


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            # # Convert JPEG buffer to NumPy array
            # image_array = np.frombuffer(buf, dtype=np.uint8)

            # # Decode image from JPEG
            # image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            # # Convert to grayscale
            # gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # # Re-encode as JPEG
            # _, jpeg_buffer = cv2.imencode('.jpg', gray_image)

            # # Save the processed frame
            # self.frame = jpeg_buffer.tobytes()

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


def calculate_sharpness():
    """Calculate sharpness using the Laplacian Variance method."""
    image = picam2.capture_array()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return np.var(laplacian)


def startup():
    sharpness_list = []
    motor_position = 0

    while not GPIO.input(sensor):
        motor_move(-50)

    for i in range(MAX_STEPS // STEP_SIZE):
        motor_move(STEP_SIZE)
        motor_position += STEP_SIZE
        sharpness = calculate_sharpness()
        sharpness_list.append((motor_position, sharpness))

    for (motor_position, sharpness) in sharpness_list:
        print(f"Position: {motor_position}, Sharpness: {sharpness}")

    best_position = max(sharpness_list, key=lambda item: item[1])[0]
    print(f"Best position: {best_position}")
    if best_position < 0:
        motor_move((motor_position + abs(best_position)) * -1)
    else:
        motor_move((motor_position - best_position) * -1)


def hill_climb_focus():
    """Perform hill climbing to find the optimal focus position."""
    best_position = 0
    best_sharpness = 0
    current_position = 0
    step_size = STEP_SIZE
    direction = 1  # 1 for forward, -1 for backward

    print("Starting autofocus...")
    best_sharpness = calculate_sharpness()
    print(f"Initial sharpness: {best_sharpness}")

    for _ in range(MAX_STEPS):
        # Move the motor by step_size * direction
        motor_move(step_size * direction)
        current_position += step_size * direction  # Update position after moving

        time.sleep(0.2)  # Wait for vibrations to settle

        # Capture and evaluate sharpness
        sharpness = calculate_sharpness()
        print(f"Position: {current_position}, Sharpness: {sharpness}")

        sharpness_diff = sharpness - best_sharpness

        print(f"Position: {current_position}, Sharpness: {sharpness}, Diff: {sharpness_diff}")

        if sharpness_diff >= 1:
            best_sharpness = sharpness
            best_position = current_position  # Store best position
        elif sharpness_diff <= -1:
            # Reverse direction and reduce step size
            direction *= -1
            step_size = max(1, step_size // 2)

        # Stop if step size is too small and sharpness is not improving
        if step_size == 1 and abs(sharpness_diff) < 1:
            break

    # Move to the best focus position
    correction_steps = best_position - current_position
    print(f"Moving back to best focus position: {best_position} (Correction: {correction_steps} steps)")
    
    motor_move(correction_steps)  # Move back to best position
    print(f"Best Focus Position: {best_position}, Sharpness: {best_sharpness}")


def motor_move(steps):
    if steps > 0:
        motor.motor_go(True, "1/4", steps, 0.0005, False, 0.01)  # Move forward
    elif steps < 0:
        motor.motor_go(False, "1/4", abs(steps), 0.0005, False, 0.01)  # Move backward
    print(f"Motor moved by {steps} steps")


def listen_for_focus_command():
    """Listen for 'focus' command from terminal and trigger autofocus."""
    while True:
        command = input("Enter command: ").strip().lower()
        if command == "start":
            startup()
        elif command == "focus":
            hill_climb_focus()
        elif command == "exit":
            print("Exiting...")
            break
        else:
            print("Unknown command. Type 'focus' to trigger autofocus or 'exit' to quit.")


if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(sensor, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # Initialize Picamera2
    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (1024, 768)}))  # (640, 480)
    picam2.set_controls({"Saturation": 0.0})

    # Start the streaming server in a separate thread
    threading.Thread(target=start_streaming_server, args=(picam2,), daemon=True).start()

    # Start listening for focus command in the main thread
    listen_for_focus_command()
