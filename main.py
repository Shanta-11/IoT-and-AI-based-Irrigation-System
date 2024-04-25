# IMPORTANT : Set WiFi credentials (line 142) and MQTT port (line 149) before running

import network
import time
import ntptime
import utime
from umqtt.simple import MQTTClient
import ubinascii
import random
import machine
import M5
import uasyncio as asyncio
import json
from M5 import Widgets

# Initializing global variables
rtc = machine.RTC() # Machine Real Time Clock
SERVER = "0.0.0.0" # Server ID
CLIENT_ID = ubinascii.hexlify(machine.unique_id()) # Client ID
PUBLISH_TOPIC = b"IOT/location0/data" # Publish Topic at Server
SUBSCRIBE_TOPIC = b"IOT/location0/server" # Subscribe Topic from Server
IRRIGATION_STATE = 0 # Variable to monitor whether irrigation is active or not
Widgets.fillScreen(0x222222) # Widgets to display information
counterLabel = Widgets.Label("Irrigation Status: Off", 10, 30, 
                            1.0, 0xffffff, 0x222222, 
                            Widgets.FONTS.DejaVu12)

title0 = Widgets.Title("Irrigation System", 25, 
                        0xffffff, 0x0000FF, 
                        Widgets.FONTS.DejaVu24) 

# Function which uses the NTP server to synchronize machine RTC
def getInternetTime():
    global rtc
    ntptime.timeout=30 # NTP server timeout
    ntptime.settime() # Get internet time
    print("Clock Synchronised")
    t = utime.localtime(utime.mktime(utime.localtime()) + 19800) # IST 
    # Set Real time clock to follow IST 
    rtc.datetime((t[0], t[1], t[2], 0, t[3], t[4], t[5], 0))

# Function which connects the device to WiFi
def connect_to_wifi(ssid, password):
    # Configure WiFi using Station Interface
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Connecting to network...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            pass
    print('Network config:', wlan.ifconfig())
    return (wlan)

# Callback set to update irrigation state and generate a beep sound whenever server transmits information to device
def subscribe_callback(topic, msg):
    global IRRIGATION_STATE, counterLabel
    M5.update()
    M5.Speaker.tone(5000, 500)
    IRRIGATION_STATE = 1-IRRIGATION_STATE
    if IRRIGATION_STATE == 0:
        counterLabel.setText("Irrigation Status: Off")
    else:
        counterLabel.setText("Irrigation Status: On")

# Asynchronous function for data collection
async def getSensorData_task():
    global rtc
    while True:

        # Generating synthetic data due to absence of appropriate sensors
        timestamp = rtc.datetime()
        air_temp = random.randint(250, 350)/10
        air_moist = random.randint(30, 40)
        water_depth = random.randint(1, 10)/10
        soil_moist = random.randint(1, 10)
        soil_ph = random.randint(6, 9)
        solar_rad = random.randint(3, 9)
        wind_speed = random.randint(1, 10)
        wind_dir = random.randint(0, 360)

        # Write data as a dictionary, to be converted into JSON
        data = {}
        data['timestamp'] = timestamp
        data['air_temp'] = air_temp
        data['air_moist'] = air_moist
        data['water_depth'] = water_depth
        data['soil_moist'] = soil_moist
        data['soil_ph'] = soil_ph
        data['wind_speed'] = wind_speed
        data['solar_rad'] = solar_rad
        data['wind_dir'] = wind_dir
        data['irrigation_state'] = IRRIGATION_STATE

        # Append sensed data to the file 'sensor_data.json'
        # Used for safeguarding against power failures
        with open('sensor_data.json', 'r+') as f:
            j = json.loads(f.read())
            j.append(data)
            f.seek(0)
            json.dump(j, f)
        print("sensed")

        # Repeat task after 5s
        await asyncio.sleep_ms(5000)
      
# Asynchronous function for data transmission
async def publishData_task(c):
    try:
        while True:

            # Check for any pending transmissions and transmit all
            with open('sensor_data.json', 'r+') as f:
                j = json.loads(f.read())
                if len(j)>0:
                    c.publish(PUBLISH_TOPIC, json.dumps(j), qos = 1) # QoS = 1 ensures reliability in transmission
                
            # Clear file contents after transmission
            with open('sensor_data.json', 'w') as f:
                j = []
                json.dump(j,f)
            print("published")

            # Repeat task after 10s
            await asyncio.sleep_ms(10000)
            
    except Exception as e:
        print(e)

# Function to create data collection and data transmission tasks
async def main(c):
    try:
        t1 = asyncio.create_task(getSensorData_task())
        t2 = asyncio.create_task(publishData_task(c))
        await asyncio.gather(t1, t2)
    except Exception as e:
        print(e)

# Compiling the above functions to complete device functionality
try:
    # IMPORTANT : Replace your own WiFi credentials before running
    wlan = connect_to_wifi('Shanta\'s Dell', 'Shanta1111')
    if SERVER == "0.0.0.0":
        SERVER = wlan.ifconfig()[2]
        getInternetTime()

    # Connecting to MQTT service
    # IMPORTANT : Ensure that the MQTT service is running on port 1884, else change port argument in all files
    c = MQTTClient(CLIENT_ID, SERVER, port = 1884)
    c.connect()
    print("Connected to %s" % SERVER)
    c.set_callback(subscribe_callback)
    c.subscribe(SUBSCRIBE_TOPIC)
    asyncio.run(main(c))

# Printing error messages
except (Exception, KeyboardInterrupt) as e:
    try:
        from utility import print_error_msg
        print_error_msg(e)
    except ImportError:
        print("Unable to import utility module")
finally:
    c.disconnect()
