import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib

GPIO_pins = (14, 15, 18) # Microstep Resolution MS1-MS3 -> GPIO Pin
direction = 27       # Direction -> GPIO Pin
step = 17      # Step -> GPIO Pin

mymotortest = RpiMotorLib.A4988Nema(direction, step, GPIO_pins, "A4988")

mymotortest.motor_go(False, "Full", 100, .01, False, .05)
