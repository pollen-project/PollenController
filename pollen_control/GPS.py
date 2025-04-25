import serial
import pynmea2
import threading


gps_data = {
    "timestamp": None,
    "latitude": None,
    "longitude": None,
    "altitude": None,
    "altitude_units": None,
    "num_sats": None,
}
serial_port = serial.Serial("/dev/ttyAMA3", 9600, timeout=0.5)


def gps_task():
    global gps_data

    _ = serial_port.readline()

    while True:
        line = serial_port.readline().decode("utf-8")
        if line.startswith("$GPGGA"):
            msg = pynmea2.parse(line)
            gps_data = {
                "latitude": msg.latitude,
                "longitude": msg.longitude,
                "altitude": msg.altitude,
                "altitude_units": msg.altitude_units,
                "num_sats": int(msg.num_sats),
            }


def gps_start():
    threading.Thread(target=gps_task, daemon=True).start()


def get_gps_data():
    global gps_data
    return gps_data


# Github for code
# https://github.com/FranzTscharf/Python-NEO-6M-GPS-Raspberry-Pi/blob/master/readme.md
