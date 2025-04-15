import board
import adafruit_dht

# Initialize the sensor
dhtDevice = adafruit_dht.DHT22(board.D25)

def read_dht22():
    try:
        temperature_c = dhtDevice.temperature
        humidity = dhtDevice.humidity
        return temperature_c, humidity
    except RuntimeError as error:
        print(f"DHT22 Read Error: {error}")
        return None, None

def main():
    print(read_dht22())

if __name__ == "__main__":
    main()

# github link
# https://github.com/FranzTscharf/Python-DHT22-Temperature-Humidity-Sensor-Raspberry-Pi/blob/master/README.md

