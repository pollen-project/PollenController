import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib

# Define GPIO Pins
GPIO_pins = (14, 15, 18)  # Microstep Resolution MS1-MS3
direction = 27  # Direction control pin
step = 17  # Step control pin

# Initialize the motor
mymotor = RpiMotorLib.A4988Nema(direction, step, GPIO_pins, "A4988")

# Function to move motor
def move_motor(steps):
    if steps > 0:
        mymotor.motor_go(True, "Full", steps, 0.005, False, 0.01)  # Move forward
        print(f"Moved {steps} steps forward")
    elif steps < 0:
        mymotor.motor_go(False, "Full", abs(steps), 0.005, False, 0.01)  # Move backward
        print(f"Moved {abs(steps)} steps backward")
    else:
        print("Motor stopped.")

print("Enter a number between -100 and 100 to move. Enter '0' to stop. Enter 'q' to quit.")

while True:
    command = input("Command: ").strip().lower()

    if command == "q":
        print("Exiting...")
        GPIO.cleanup()  # Reset GPIO
        break

    try:
        steps = int(command)  # Convert input to integer
        if -100 <= steps <= 100:
            move_motor(steps)
        else:
            print("Invalid range. Please enter a number between -100 and 100.")
    except ValueError:
        print("Invalid input. Please enter a number between -100 and 100, or 'q' to quit.")
