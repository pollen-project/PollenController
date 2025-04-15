import serial
import pynmea2
import threading


serialPort = serial.Serial("/dev/ttyAMA3", 9600, timeout=0.5)


def gps_task():
    while True:
        line = serialPort.readline().decode("utf-8")
        if line.startswith("$GPGGA"):
            msg = pynmea2.parse(line)
            print(f"Timestamp: {msg.timestamp} -- Lat: {msg.latitude} -- Lon: {msg.longitude} -- Altitude: {msg.altitude} {msg.altitude_units}")


def gps_start():
    threading.Thread(target=gps_task, daemon=True).start()


# Github for code
# https://github.com/FranzTscharf/Python-NEO-6M-GPS-Raspberry-Pi/blob/master/readme.md
