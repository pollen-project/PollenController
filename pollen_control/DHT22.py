import Adafruit_DHT


sensor = Adafruit_DHT.DHT22
pin = 25


def read_dht22():

    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)

    if humidity is not None and temperature is not None:
        print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(temperature, humidity))

        return temperature, humidity
    else:
        print('Failed to get reading from DHT22!')


# github link
# https://github.com/FranzTscharf/Python-DHT22-Temperature-Humidity-Sensor-Raspberry-Pi/blob/master/README.md

