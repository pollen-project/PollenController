import cv2
import numpy as np
import time
from picamera2 import Picamera2
import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib

# Initialize camera
picam2 = Picamera2()
picam2.configure(picam2.create_still_configuration())
picam2.start()

# Initialize stepper motor
GPIO_pins = (14, 15, 18)  # Microstep Resolution MS1-MS3 -> GPIO Pin
direction = 27  # Direction -> GPIO Pin
step = 17  # Step -> GPIO Pin
STEP_SIZE = 5  # Adjust step size as needed
MAX_STEPS = 100  # Maximum steps to prevent endless loop
motor = RpiMotorLib.A4988Nema(direction, step, GPIO_pins, "A4988")

def motor_move(steps):
    motor.motor_go(False, "Full", steps, .01, False, .05)
    print(f"Motor moved by {steps} steps")

def capture_image():    
    """Capture an image from the camera."""
    return picam2.capture_array()

def calculate_sharpness(image):
    """Calculate sharpness using the Laplacian Variance method."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return np.var(laplacian)

def hill_climb_focus():
    """Perform hill climbing to find the optimal focus position."""
    best_position = 0
    best_sharpness = 0
    current_position = 0
    step_size = STEP_SIZE
    direction = 1  # 1 for forward, -1 for backward

    print("Starting autofocus...")

    for _ in range(MAX_STEPS):
        # Move stepper motor
        motor_move(step_size * direction)  # Move the motor by step_size * direction
        time.sleep(0.2)  # Wait for vibrations to settle

        # Capture and evaluate sharpness
        image = capture_image()
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

        # Stop if step size is too small
        if step_size == 1 and sharpness <= best_sharpness:
            break

    # Move to best focus position
    motor_move(best_position - current_position)
    print(f"Best Focus Position: {best_position}, Sharpness: {best_sharpness}")

if __name__ == "__main__":
    hill_climb_focus()
