import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib


class Motor:
    def __init__(self, gpios, home_sensor = None, max_steps = None):
        self.__name = "".join(str(x) for x in gpios)
        self.__motor = RpiMotorLib.BYJMotor(self.__name, "28BYJ")
        self.__gpios = gpios
        self.__home_sensor = home_sensor
        self.__end_position = max_steps
        self.position = 0

        if self.__home_sensor:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.__home_sensor, GPIO.IN, pull_up_down=GPIO.PUD_OFF)

    def __motor_run(self, steps):
        self.__motor.motor_run(self.__gpios, 0.025, abs(steps), (steps < 0), False, "full", 0.01)

    def move(self, steps):
        if steps > 0:
            if self.__end_position and self.position >= self.__end_position:
                return False

            if self.__end_position and self.position + steps > self.__end_position:
                steps = (self.position + steps) - self.__end_position

            self.__motor_run(steps)
            self.position += steps
        elif self.__home_sensor:
            remaining_steps = abs(steps)

            while remaining_steps > 0:
                if GPIO.input(self.__home_sensor):
                    self.position = 0
                    return False

                motor_steps = remaining_steps if remaining_steps < 10 else 10
                remaining_steps -= motor_steps

                self.__motor_run(-1 * motor_steps)
                self.position -= motor_steps
        else:
            self.__motor_run(steps)
            self.position += steps

        return True

    def home(self):
        while not GPIO.input(self.__home_sensor):
            self.__motor_run(-10)
        self.position = 0


# Initialize motors
motors = {
    'focus': Motor([5, 6, 13, 19], 18, 250),
    'tape': Motor([16, 20, 21, 26])
}
