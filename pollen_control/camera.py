# Initialize Picamera2
from picamera2 import Picamera2
import datetime
import cv2
import numpy as np
from io import BytesIO

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (1024, 768)}))  # (640, 480)
picam2.set_controls({"Saturation": 1.0})

denoise_toggle = False

def camera_settings(mode):
    global denoise_toggle
    if mode == "grey":
        picam2.set_controls({"Saturation": 0.0})   
    if mode == "color":
        picam2.set_controls({"Saturation": 1.0})
    if mode == "denoise":
        denoise_toggle = not denoise_toggle
    

def picture():
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Format timestamp
    filename = f"photos/image_{now}.jpg"  # Create filename
        
    img =denoise_image(picam2.capture_array())
    
    
    
    #cv2.imwrite(filename, processed)
    #picam2.capture_file(filename)  # Save the image

def denoise_image(buf):
    if not denoise_toggle:
        return buf
    
    image = cv2.cvtColor(buf, cv2.COLOR_BGR2GRAY)

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