import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib

# Define GPIO Pins
sensor = 18

# Initialize the motor
motors = {
    'focus': RpiMotorLib.BYJMotor("focus", "28BYJ"),
    'tape': RpiMotorLib.BYJMotor("tape", "28BYJ")
}
motor_gpios = {
    'focus': [5, 6, 13, 19],
    'tape': [16, 20, 21, 26]
}


# Function to move motor
def move_motor(motor, steps):
    motors[motor].motor_run(motor_gpios[motor], 0.025, abs(steps), (steps < 0), False, "full", 0.01)


def home_motor_a():
    while not GPIO.input(sensor):
        move_motor("focus", -10)

def setup_motor():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(sensor, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
