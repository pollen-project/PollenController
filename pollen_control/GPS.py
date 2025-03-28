import serial
import pynmea2
import threading

def parseGPS(str):
    if str.find('GGA') > 0:
        msg = pynmea2.parse(str)
        print (f"Timestamp: {msg.timestamp} -- Lat: {msg.lat} {msg.lat_dir} -- Lon: {msg.lon} {msg.lon_dir} -- Altitude: {msg.altitude} {msg.altitude_units}")

serialPort = serial.Serial("/dev/ttyAMA0", 9600, timeout=0.5)

def GPS_task():

    while True:
        str = serialPort.readline()
        parseGPS(str)


def GPS_start():
    threading.Thread(target=GPS_task, daemon=True).start()


# Github for code
# https://github.com/FranzTscharf/Python-NEO-6M-GPS-Raspberry-Pi/blob/master/readme.md