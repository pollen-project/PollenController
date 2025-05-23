import io
import logging
import socketserver
from http import server
from threading import Condition
import time
import datetime
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
<title>Pollen stream</title>
</head>
<body>
<img src="stream.mjpg" width="640" height="480" />
</body>
</html>
"""
GPIO_pins = (0, 0, 0)  # Microstep Resolution MS1-MS3 -> GPIO Pin
direction_focus = 17  # Direction -> GPIO Pin
step_focus = 4  # Step -> GPIO Pin
direction_tape = 22
step_tape = 27
sensor = 18
motor_en_focus = 23
motor_en_tape = 24
STEP_SIZE = 10  # Adjust step size for the motor
MAX_STEPS = 4000  # Max number of steps to prevent an endless loop
motor = RpiMotorLib.A4988Nema(direction_focus, step_focus, GPIO_pins, "A4988")
motor_tape = RpiMotorLib.A4988Nema(direction_tape, step_tape, GPIO_pins, "A4988")


def denoise_image(buf):
    image_array = np.frombuffer(buf, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)

    # Apply binary thresholding
    _, thresh = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Set a minimum contour area (this will remove particles smaller than this size)
    min_contour_area = 200  # Adjust this value based on your requirements

    # Create a mask for large contours
    mask = np.zeros_like(image)

    for contour in contours:
        if cv2.contourArea(contour) >= min_contour_area:
            cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)

    # Apply the mask to the original image
    denoised_image = cv2.bitwise_and(image, image, mask=mask)

    # Optional: Apply additional denoising methods like Gaussian or median blur
    # denoised_image = cv2.GaussianBlur(denoised_image, (5, 5), 0)

    _, jpeg_buffer = cv2.imencode('.jpg', denoised_image)

    return jpeg_buffer.tobytes()


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

            ###########

            # self.frame = denoise_image(buf)

            #########

            self.frame = buf   # regular stream
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


# def perform_autofocus(picam2):                     
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
    """Robust hill climbing autofocus with initial coarse search."""
    def measure_sharpness():
        # Take several images, average sharpness for robustness
        return sum(calculate_sharpness() for _ in range(3)) / 3

    def initial_coarse_search():
        """Scan a wide range to find rough focus area if initial sharpness is very low."""
        print("Starting initial coarse search...")
        best_sharpness = 0
        best_position = 0
        scan_range = 50  # Arbitrary large initial range

        for offset in range(-scan_range, scan_range + 1, 5):
            motor_move_to(start_position + offset)
            time.sleep(0.1)
            sharpness = measure_sharpness()
            print(f"Coarse scan position {offset}: sharpness {sharpness}")

            if sharpness > best_sharpness:
                best_sharpness = sharpness
                best_position = offset

        motor_move_to(start_position + best_position)
        print(f"Coarse search completed. Best position: {best_position}, Sharpness: {best_sharpness}")
        return best_position, best_sharpness

    print("Starting autofocus...")
    
    start_position = 0
    while not GPIO.input(sensor):
        motor_move(STEP_SIZE * -1)

    initial_sharpness = measure_sharpness()
    print(f"Initial sharpness: {initial_sharpness}")

    if initial_sharpness < 10:  # Threshold for "very blurry"
        offset, sharpness = initial_coarse_search()
        motor_move_to(start_position + offset)
    else:
        sharpness = initial_sharpness

    best_position = motor_get_position()
    best_sharpness = sharpness

    step_size = STEP_SIZE
    direction = 1  # 1 = forward, -1 = backward

    for _ in range(MAX_STEPS):
        # Move and wait for vibration to settle
        motor_move(step_size * direction)
        time.sleep(0.2)

        sharpness = measure_sharpness()
        position = motor_get_position()

        sharpness_diff = sharpness - best_sharpness
        print(f"Position: {position}, Sharpness: {sharpness}, Diff: {sharpness_diff}")

        if sharpness > best_sharpness:
            best_sharpness = sharpness
            best_position = position
        elif sharpness_diff < -1:
            # Overshot: reverse and reduce step size
            direction *= -1
            step_size = max(1, step_size // 2)

        if step_size == 1 and abs(sharpness_diff) < 0.5:
            break  # Converged

    # Return to best focus point
    correction_steps = best_position - motor_get_position()
    print(f"Returning to best focus position: {best_position} (Correction: {correction_steps} steps)")
    motor_move(correction_steps)

    print(f"Best Focus Position: {best_position}, Final Sharpness: {best_sharpness}")


def motor_move(steps):
    GPIO.output(motor_en_focus, True)

    if steps > 0:
        motor.motor_go(True, "Full", steps, 0.0005, False, 0.01)  # Move forward
    elif steps < 0:
        motor.motor_go(False, "Full", abs(steps), 0.0005, False, 0.01)  # Move backward

    GPIO.output(motor_en_focus, False)

    print(f"Motor moved by {steps} steps")

def picture():
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Format timestamp
    filename = f"image_{now}.jpg"  # Create filename
    picam2.capture_file(filename)  # Save the image

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
        elif command == "1":
            for i in range (0,10):
                picture()
                time.sleep(0.2)
        else:
            print("Unknown command. Type 'focus' to trigger autofocus or 'exit' to quit.")


if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(sensor, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
    GPIO.setup(motor_en_focus, GPIO.OUT)
    GPIO.setup(motor_en_tape, GPIO.OUT)

    GPIO.output(motor_en_focus, False)
    GPIO.output(motor_en_tape, False)

    # Initialize Picamera2
    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (1024, 768)}))  # (640, 480)
    picam2.set_controls({"Saturation": 0.0})

    # Start the streaming server in a separate thread
    threading.Thread(target=start_streaming_server, args=(picam2,), daemon=True).start()

    # Start listening for focus command in the main thread
    listen_for_focus_command()
