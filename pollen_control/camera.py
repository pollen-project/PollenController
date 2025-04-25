from datetime import datetime, timezone
import cv2
import numpy as np
from picamera2 import Picamera2

denoise_toggle = False
color_flag = True

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"format": "BGR888", "size": (1024, 768)}))  # (640, 480)
picam2.set_controls({"Saturation": 1.0})


def camera_settings(mode):
    global denoise_toggle
    global color_flag
    if mode == "grey":
        picam2.set_controls({"Saturation": 0.0})  
        color_flag = False 
    if mode == "color":
        picam2.set_controls({"Saturation": 1.0})
        color_flag = True
    if mode == "denoise":
        denoise_toggle = not denoise_toggle
    if mode == "denoise on":
        denoise_toggle = True
    if mode == "denoise off":
        denoise_toggle = False


def take_picture_all():
    global color_flag, denoise_toggle

    initial_color_flag = color_flag
    initial_denoise_flag = denoise_toggle

    # Color ON, denoise OFF
    color_flag = True
    denoise_toggle = False
    take_picture()

    # Color ON, denoise ON
    denoise_toggle = True
    take_picture()

    # Color OFF, denoise ON
    color_flag = False
    take_picture()

    color_flag = initial_color_flag
    denoise_toggle = initial_denoise_flag


def take_picture():
    picam2.start()
    now = datetime.now(timezone.utc)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Format timestamp
    
    noise_status = "" if not denoise_toggle else "dn"
    color_status = "G" if not color_flag else "C"

    settings = color_status+noise_status
    filename = f"photos/image_{timestamp}{settings}.jpg"  # Create filename

    camera_buf = picam2.capture_array()
    #image = denoise_image(camera_buf, input_array=True)
    image = camera_buf
    image_jpeg = encode_jpeg(image)

    with open(filename, 'wb') as f:
        f.write(image_jpeg)

    return image, image_jpeg, now


def calculate_sharpness():
    """Calculate sharpness using the Laplacian Variance method."""
    image = picam2.capture_array()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    return np.var(laplacian)


def encode_jpeg(buf):
    _, jpeg_buffer = cv2.imencode('.jpg', buf)
    return jpeg_buffer.tobytes()


def denoise_image(buf, input_array = False, encode_jpeg = False):
    if not denoise_toggle:
        return buf

    is_color = color_flag

    if input_array:
        image = cv2.cvtColor(buf, cv2.COLOR_BGR2GRAY)
        color_image = cv2.cvtColor(buf, cv2.COLOR_BGR2RGB)

    else:
        image_array = np.frombuffer(buf, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)
        color_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

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
    base_image = color_image if is_color else image
    denoised_image = cv2.bitwise_and(base_image, base_image, mask=mask)

    # Optional: Apply additional denoising methods like Gaussian or median blur
    # denoised_image = cv2.GaussianBlur(denoised_image, (5, 5), 0)

    if encode_jpeg:
        _, jpeg_buffer = cv2.imencode('.jpg', denoised_image)
        return jpeg_buffer.tobytes()

    return denoised_image
