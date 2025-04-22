from DHT22 import read_dht22
import datetime
import Adafruit_DHT


def get_all_sensor_values():
    now = datetime.datetime.now().isoformat()
    temperature, humidity = read_dht22()
    #gps = read_gps_data()

    data = {
        "timestamp": now,
        "humidity": humidity,
        "temperature": temperature
    }
    return data
