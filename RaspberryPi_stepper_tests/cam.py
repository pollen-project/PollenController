import numpy as np
import cv2
from picamera2 import Picamera2


def denoise_image(buf):
    #image_array = np.frombuffer(buf, dtype=np.uint8)
    #image = cv2.imdecode(image_array, cv2.IMREAD_GRAYSCALE)
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


if __name__ == "__main__":
    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (1024, 768)}))
    picam2.set_controls({"Saturation": 0.0})

    picam2.start()

    image_arr = picam2.capture_array()
    denoise_image(image_arr)

    picam2.stop()
