import RPi.GPIO as GPIO

RELAY_PIN = 22

GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)

# Turn fan ON initially (relay not triggered)
GPIO.output(RELAY_PIN, GPIO.LOW)

def fan_on():
    GPIO.output(RELAY_PIN, GPIO.HIGH)  # Trigger relay = FAN OFF

def fan_off():
    GPIO.output(RELAY_PIN, GPIO.LOW)  # Relay idle = FAN ON

def cleanup():
    GPIO.cleanup()