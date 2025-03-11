from time import sleep
import threading
import numpy as np
import cv2
import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib
from picamera2 import Picamera2
import datetime


from stream_server import start_streaming_server, MAX_STEPS

GPIO_FOCUS_SENSOR = 18
GPIO_FOCUS_STEP = 4
GPIO_FOCUS_DIR = 17
GPIO_FOCUS_ENABLE = 23

MOTOR_SPEED = 0.001
STEP_SIZE = 20
FOCUS_END_POS = 2000


focus_motor = RpiMotorLib.A4988Nema(GPIO_FOCUS_DIR, GPIO_FOCUS_STEP, (0, 0, 0), "A4988")
focus_motor_pos = None

_picam2 = None  

def set_camera(cam):
    """Setter for the camera instance."""
    global _picam2
    _picam2 = cam

def get_camera():
    """Getter for the camera instance."""
    return _picam2

def setup_server():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_FOCUS_SENSOR, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
    GPIO.setup(GPIO_FOCUS_ENABLE, GPIO.OUT)

    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (1024, 768)}))
    picam2.set_controls({"Saturation": 0.0})

    # Ensure the camera is properly configured before starting
    if picam2.ready:
        print("Camera configured, starting server...")
        threading.Thread(target=start_streaming_server, args=(picam2,), daemon=True).start()
    else:
        print("Camera not properly configured.")



def picture():
    cam = get_camera()
    if cam is None:
        raise RuntimeError("Camera is not initialized!")
    
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  
    filename = f"image_{now}.jpg"
    cam.capture_file(filename)

def motor_enable(enable):
    GPIO.output(GPIO_FOCUS_ENABLE, enable)


def motor_go(steps):
    global focus_motor_pos

    if focus_motor_pos is None:
        print("Home position not known. Please home the motor first.")
        return

    if (steps < 0 and focus_motor_pos + steps < 0) or (steps > 0 and focus_motor_pos + steps > FOCUS_END_POS):
        print("End position reached.")
        return

    if steps > 0:
        focus_motor.motor_go(True, "Full", steps, MOTOR_SPEED, False, 0.0001)
        focus_motor_pos += steps
    elif steps < 0:
        focus_motor.motor_go(False, "Full", abs(steps), MOTOR_SPEED, False, 0.0001)
        focus_motor_pos -= abs(steps)


def calculate_sharpness():
    """Calculate sharpness using the Laplacian Variance method."""
    cam = get_camera()
    if cam is None:
        raise RuntimeError("Camera is not initialized!")
    image = cam.capture_array()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return np.var(laplacian)


def focus_home():
    global focus_motor_pos

    try:
        print('Focus to home...')
        motor_enable(True)
        while not GPIO.input(GPIO_FOCUS_SENSOR):
            focus_motor.motor_go(False, "Full", 10, MOTOR_SPEED, False, 0.0001)
        focus_motor_pos = 0
        print('Home done')
    except KeyboardInterrupt:
        print('Home cancelled')
    finally:
        motor_enable(False)


def focus():
    global focus_motor_pos

    try:
        motor_enable(True)

        sharpness = calculate_sharpness()
        while sharpness < 20 and focus_motor_pos < MAX_STEPS:
            motor_go(10)
            sharpness = calculate_sharpness()

        print('Focus done')
    except KeyboardInterrupt:
        print('Focus cancelled')
    finally:
        motor_enable(False)

    motor_enable(False)


def focus2():
    global focus_motor_pos
    best_sharp_pos = None

    # picam2.start()

    sharpness = calculate_sharpness()
    best_sharp_pos = (sharpness, focus_motor_pos)
    print(f'Sharpness: {sharpness}, Position: {focus_motor_pos}')

    last_sharpness = sharpness
    step_size = STEP_SIZE if sharpness < 20 else STEP_SIZE // 2
    direction = 1
    same_sharpness_count = 0

    try:
        print('Focus to max sharpness...')
        motor_enable(True)

        while True:
            if focus_motor_pos + step_size >= FOCUS_END_POS:
                direction = -1
            elif focus_motor_pos - step_size <= 0:
                direction = 1

            motor_go(step_size * direction)

            sharpness = calculate_sharpness()
            print(f'Sharpness: {sharpness}, Position: {focus_motor_pos}')

            diff = sharpness - last_sharpness
            if diff > 1:
                best_sharp_pos = (sharpness, focus_motor_pos)
                same_sharpness_count = 0
            elif diff < -1:
                direction = -direction
                # step_size = step_size // 2
                same_sharpness_count = 0
            elif sharpness > 20 and -1 < diff < 1:
                step_size = step_size // 2
                sleep(0.5)

            if -1 < diff < 1:
                same_sharpness_count += 1

            if same_sharpness_count > 5:
                # if sharpness > 20:
                break
                # else:
                #     direction = -direction
                #     same_sharpness_count = 0

            last_sharpness = sharpness

        print('Focus done')
    except KeyboardInterrupt:
        print('Focus cancelled')
    finally:
        motor_enable(False)

    # picam2.stop()
