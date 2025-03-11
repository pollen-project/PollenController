from time import sleep
import RPi.GPIO as GPIO

sensor = 18

if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(sensor, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

    while True:
        print(f"Sensor: {GPIO.input(sensor)}")
        sleep(1)
