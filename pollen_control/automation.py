from time import sleep
from camera import take_picture, camera_settings
from motor import motors
from focus import focus
from concurrent.futures import ThreadPoolExecutor
from fan import fan_on, fan_off
from uploading import add_to_upload_queue
from DHT22 import read_dht22
from GPS import get_gps_data

# Pollen number calculation variables
IMAGE_SPACING_MM = 1
EXPOSURE_TIME_SEC = 1800
TEST_EXPOSURE_TIME_SEC = 300

# Physical dimensions
SAMPLE_AREA_MM = 30
INITIAL_STEPS = 1300
SAMPLE_AREA_STEPS = 800

auto_running = False
testing = False
focus_home_counter = 0

def auto_take_pictures_task(testing=False):
    global focus_home_counter

    sample_area_image_count = SAMPLE_AREA_MM / IMAGE_SPACING_MM
    tape_steps = SAMPLE_AREA_STEPS / sample_area_image_count

    # Calculate step progress globally or persistently if needed
    print("Taking picture with tape step:", tape_steps)

    if focus_home_counter >= 15:
        motors["focus"].home()
        focus_home_counter = 0

    motors["tape"].move(tape_steps * -1)
    fan_off()
    sleep(5.0)
    focus()
    image, image_jpeg, timestamp = take_picture()
    temperature, humidity = read_dht22()
    add_to_upload_queue({
        "timestamp": timestamp,
        "image_raw": image,
        "image": image_jpeg,
        "temperature": temperature,
        "humidity": humidity,
        "gps": get_gps_data(),
    })
    fan_on()

    focus_home_counter += 1


def start_auto_picture_loop(testing=False):
    global auto_running
    auto_running = True
    print("E: start_auto_picture_loop")
    exposure_time = TEST_EXPOSURE_TIME_SEC if testing else EXPOSURE_TIME_SEC
    sample_area_image_count = SAMPLE_AREA_MM / IMAGE_SPACING_MM
    image_freq_sec = exposure_time / sample_area_image_count

    fan_on()

    # Replace with your actual camera + motor logic
    camera_settings("color")
    camera_settings("denoise off")
    print("Returning Home")
    motors["focus"].home()

    with ThreadPoolExecutor(max_workers=1) as executor:
        print("E: thread opened")
        while auto_running:
            executor.submit(auto_take_pictures_task, testing)
            sleep(image_freq_sec)


def auto_stop():
    global auto_running
    auto_running = False
    fan_off()
