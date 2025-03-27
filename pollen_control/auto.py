from time import sleep
from stream_server import start_stream
from automation import auto_take_pictures_task

if __name__ == "__main__":
    start_stream()
    auto_take_pictures_task()

    while True:
        sleep(1)
