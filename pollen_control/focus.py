from camera import picam2
import cv2
from motor import motor_enable, move_motor
import numpy as np



def calculate_sharpness():
    """Calculate sharpness using the Laplacian Variance method."""
    image = picam2.capture_array()
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return np.var(laplacian)


def focus():
    global focus_motor_pos

    try:
        sharpness = calculate_sharpness()
        while sharpness < 20:
            move_motor("focus",10)
            sharpness = calculate_sharpness()

        print('Focus done')
    except KeyboardInterrupt:
        print('Focus cancelled')
    


