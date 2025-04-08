import threading
from time import sleep
from camera import take_picture, camera_settings
from motor import motors
from focus import focus
from uploading import upload_image
from concurrent.futures import ThreadPoolExecutor

# Pollen number calculation variables
IMAGE_SPACING_MM = 1
EXPOSURE_TIME_SEC = 1800
TEST_EXPOSURE_TIME_SEC = 60

# Physical dimensions
SAMPLE_AREA_MM = 30
INITIAL_STEPS = 1300
SAMPLE_AREA_STEPS = 400

auto_running = False
testing = False 

def auto_take_pictures_task(testing=False):
    sample_area_image_count = SAMPLE_AREA_MM / IMAGE_SPACING_MM
    tape_steps = SAMPLE_AREA_STEPS / sample_area_image_count

    # Calculate step progress globally or persistently if needed
    print("Taking picture with tape step:", tape_steps)

    motors["tape"].move(tape_steps * -1)
    focus()
    take_picture()
    


def start_auto_picture_loop(testing=False):
    global auto_running
    auto_running = True
    print("E: start_auto_picture_loop")
    exposure_time = TEST_EXPOSURE_TIME_SEC if testing else EXPOSURE_TIME_SEC
    sample_area_image_count = SAMPLE_AREA_MM / IMAGE_SPACING_MM
    image_freq_sec = exposure_time / sample_area_image_count

    # Replace with your actual camera + motor logic
    camera_settings("color")
    camera_settings("denoise off")
    motors["focus"].home()

    with ThreadPoolExecutor(max_workers=1) as executor:
        print("E: thread opened")
        while auto_running:
           
            executor.submit(auto_take_pictures_task, testing)
            sleep(image_freq_sec)


def auto_stop():
    global auto_running
    auto_running = False
