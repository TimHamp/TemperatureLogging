import sys
from datetime import datetime
import Adafruit_DHT
import requests
import json
import os

outpath = "/home/pi/conditions_log/"

def load_settings(filename="settings.json"):
    """Load settings from settings.json"""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Settings file '{filename}' not found.")
    with open(filename, "r") as f:
        settings = json.load(f)
    return settings

def get_cpu_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_str = f.readline().strip()
            # Value is in millidegrees Celsius, so divide by 1000
            temp_c = int(temp_str) / 1000.0
            return round(temp_c, 2)
    except FileNotFoundError:
        print("Temperature file not found. Are you running this on a Raspberry Pi?")
        return None
    except ValueError:
        print("Could not read temperature value.")
        return None

def get_room_temperature(sensor, pim):
	humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
	return round(temperature, 1), round(humidity, 1)

def get_weather(zip, country_code, api_key, units="metric"):
    """
    Get temperature, humidity, and cloud coverage for a city from OpenWeatherMap.
    
    Args:
        zip (str): Zipcode (e.g., "55555").
        country_code (str): Country code (e.g. "de")
        api_key (str): Your OpenWeatherMap API key.
        units (str): Units for temperature ("metric", "imperial", or "standard").
        
    Returns:
        dict: A dictionary with temperature (°C or °F), humidity (%), and clouds (%).
    """
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "zip": f"{zip},{country_code}",
        "appid": api_key,
        "units": units
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = response.json()
        
        weather_data = {
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "clouds": data["clouds"]["all"]
        }
        return weather_data
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data: {e}")
        return None


if __name__ == "__main__":
    try:
        if len(sys.argv) >= 2:
            settings_filename = sys.argv[1]
        else:
            settings_filename = "settings.json"

        settings = load_settings(settings_filename)
        sensor = settings['sensor']
        
        # Reading sensor data
        sensor_id = str(sensor['sensor_id'])
        pin = sensor['pin']
        sensor_args = { '11': Adafruit_DHT.DHT11,
                '22': Adafruit_DHT.DHT22,
                '2302': Adafruit_DHT.AM2302 }
        if (sensor_id not in sensor_args):
            print('Sensor ID is not valid. Allowed values are [11|22|2302]')
            sys.exit(1)
        
        temperature_in, humidity_in = get_room_temperature(sensor_args[sensor_id], pin)
        
        # Reading kernel temperature
        temperature_cpu = get_cpu_temperature()
        
        # Fetching weather data
        owm = settings["openweathermap"]
        weather_conditions = get_weather(owm["zip"], owm["country"], owm["api_key"])
        
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        current_date = now.strftime("%Y-%m-%d")

        # Saving data
        if humidity_in is not None and temperature_in is not None:
            f = open(outpath + current_date + ".csv", "a")
            f.write(current_time + ";" + str(temperature_in) + ";" + str(humidity_in) + ";" + str(temperature_cpu) + ";" + "0" + ";" + str(weather_conditions['temperature']) + ";" + str(weather_conditions['humidity']) + ";" + str(weather_conditions["clouds"]) + "\r\n")
            f.close()
        else:
            print('Failed to get reading. Try again!')
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
    






