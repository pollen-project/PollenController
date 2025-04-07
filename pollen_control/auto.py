from time import sleep
from stream_server import start_stream
from automation import auto_take_pictures_task
from uploading import upload_image

if __name__ == "__main__":
    start_stream()
    auto_take_pictures_task()
    upload_image()
    while True:
        sleep(1)
