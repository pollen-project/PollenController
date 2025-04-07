import threading
from time import sleep
from camera import take_picture, camera_settings
from motor import motors
from focus import focus
from uploading import upload_image


# Pollen number calculation variables
IMAGE_SPACING_MM = 1
EXPOSURE_TIME_SEC = 1800
TEST_EXPOSURE_TIME_SEC = 60

# Physical dimensions
SAMPLE_AREA_MM = 30
INITIAL_STEPS = 1300
SAMPLE_AREA_STEPS = 400

auto_running = False

def auto_take_pictures_task(testing=False):
    global auto_running

    exposure_time = TEST_EXPOSURE_TIME_SEC if testing else EXPOSURE_TIME_SEC
    first_sample_steps = INITIAL_STEPS + SAMPLE_AREA_STEPS
    sample_area_image_count = SAMPLE_AREA_MM / IMAGE_SPACING_MM
    tape_steps = SAMPLE_AREA_STEPS / sample_area_image_count
    image_freq_sec = exposure_time / sample_area_image_count

    camera_settings("color")
    camera_settings("denoise off")
    motors["focus"].home()
    startup_steps = 0
    auto_running = True

    while auto_running:
        motors["tape"].move(tape_steps * -1)

        if startup_steps >= first_sample_steps:
            focus()
            take_picture()
            #upload_image()
        else:
            startup_steps += tape_steps

        sleep(image_freq_sec)

def auto_take_pictures(testing=False):
    global auto_running

    threading.Thread(target=auto_take_pictures_task, args=(testing,), daemon=True).start()

def auto_stop():
    global auto_running

    auto_running = False
