import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib

# Define GPIO Pins
GPIO_pins = (14, 15, 18)  # Microstep Resolution MS1-MS3
step_a = 4  # Step control pin
direction_a = 17  # Direction control pin
step_b = 27  # Step control pin
direction_b = 22  # Direction control pin

# Initialize the motor
motors = {
    'a': RpiMotorLib.A4988Nema(direction_a, step_a, GPIO_pins, "A4988"),
    'b': RpiMotorLib.A4988Nema(direction_b, step_b, GPIO_pins, "A4988")
}

# Function to move motor
def move_motor(motor, steps):
    if steps > 0:
        motors[motor].motor_go(True, "Full", steps, 0.0005, False, 0.01)  # Move forward
        print(f"Moved motor {motor} {steps} steps forward")
    elif steps < 0:
        motors[motor].motor_go(False, "Full", abs(steps), 0.0005, False, 0.01)  # Move backward
        print(f"Moved motor {motor} {abs(steps)} steps backward")
    else:
        print("Motor stopped.")

print("Enter a number between -1000 and 1000 to move. Enter '0' to stop. Enter 'q' to quit.")

while True:
    command = input("Command: ").strip().lower()

    if command == "q":
        print("Exiting...")
        GPIO.cleanup()  # Reset GPIO
        break

    try:
        motor = command[0:1]
        steps = int(command[1:])  # Convert input to integer
        if -1000 <= steps <= 1000:
            move_motor(motor, steps)
        else:
            print("Invalid range. Please enter a number between -100 and 100.")
    except ValueError:
        print("Invalid input. Please enter a number between -100 and 100, or 'q' to quit.")
