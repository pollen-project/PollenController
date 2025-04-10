import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib

# Define GPIO Pins
sensor = 18
motor_en_focus = 23
motor_en_tape = 24

# Initialize the motor
motors = {
    'a': RpiMotorLib.BYJMotor("focus", "28BYJ"),
    'b': RpiMotorLib.BYJMotor("tape", "28BYJ")
}
gpios = {
    'a': [5, 6, 13, 19],
    'b': [16, 20, 21, 26]
}


def motor_en(motor, enable):
    if motor == "a":
        GPIO.output(motor_en_focus, enable)
    elif motor == "b":
        GPIO.output(motor_en_tape, enable)


# Function to move motor
def move_motor(motor, steps):
    motor_en(motor, True)

    motors[motor].motor_run(gpios[motor], 0.001, abs(steps), (steps < 0), False, "full", 0.01)
    print(f"Moved motor {motor} {steps} steps")

    motor_en(motor, False)


def home_motor_a():
    motor_en("a", True)
    while not GPIO.input(sensor):
        motors["a"].motor_run(gpios["a"], 0.001, 10, False, False, "full", 0.01)
    motor_en("a", False)


if __name__ == "__main__":
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(sensor, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
    GPIO.setup(motor_en_focus, GPIO.OUT)
    GPIO.setup(motor_en_tape, GPIO.OUT)

    GPIO.output(motor_en_focus, False)
    GPIO.output(motor_en_tape, False)

    print("Enter a motor command or 'q' to quit.")

    while True:
        command = input("Command: ").strip().lower()

        if command == "q":
            print("Exiting...")
            GPIO.cleanup()  # Reset GPIO
            break

        if command == "h":
            home_motor_a()
            continue

        try:
            motor = command[0:1]
            steps = int(command[1:])
            move_motor(motor, steps)
            print(f"Sensor: {GPIO.input(sensor)}")
        except ValueError:
            print("Invalid input")
