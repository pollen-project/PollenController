import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib

# Define GPIO Pins
GPIO_pins = (0, 0, 0)  # Microstep Resolution MS1-MS3
step_a = 4  # Step control pin
direction_a = 17  # Direction control pin
step_b = 27  # Step control pin
direction_b = 22  # Direction control pin
sensor = 18
motor_en_focus = 23
motor_en_tape = 24

# Initialize the motor
motors = {
    'a': RpiMotorLib.A4988Nema(direction_a, step_a, GPIO_pins, "A4988"),
    'b': RpiMotorLib.A4988Nema(direction_b, step_b, GPIO_pins, "A4988")
}


def motor_en(motor, enable):
    if motor == "a":
        GPIO.output(motor_en_focus, enable)
    elif motor == "b":
        GPIO.output(motor_en_tape, enable)


# Function to move motor
def move_motor(motor, steps):
    motor_en(motor, True)

    if steps > 0:
        motors[motor].motor_go(True, "Full", steps, 0.001, False, 0.01)  # Move forward
        print(f"Moved motor {motor} {steps} steps forward")
    elif steps < 0:
        motors[motor].motor_go(False, "Full", abs(steps), 0.001, False, 0.01)  # Move backward
        print(f"Moved motor {motor} {abs(steps)} steps backward")
    else:
        print("Motor stopped.")

    motor_en(motor, False)


def home_motor_a():
    motor_en("a", True)
    while not GPIO.input(sensor):
        motors["a"].motor_go(False, "Full", 10, 0.001, False, 0.01)
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
