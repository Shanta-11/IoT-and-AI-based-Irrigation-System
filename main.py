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

rtc = machine.RTC()
SERVER = "0.0.0.0"
CLIENT_ID = ubinascii.hexlify(machine.unique_id())
PUBLISH_TOPIC = b"IOT/location0/data"
SUBSCRIBE_TOPIC = b"IOT/location0/server"

def getInternetTime():
    global rtc
    ntptime.timeout=30 # NTP server timeout
    ntptime.settime() # Get internet time
    print("Clock Synchronised")
    t = utime.localtime(utime.mktime(utime.localtime()) + 19800) # IST 
    # Set Real time clock to follow IST 
    rtc.datetime((t[0], t[1], t[2], 0, t[3], t[4], t[5], 0))

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

def subscribe_callback(topic, msg):
    M5.Speaker.tone(5000, 500)

async def getSensorData_task():
    global rtc
    while True:
        
#        M5.update()
        timestamp = rtc.datetime()
        air_temp = random.randint(250, 350)/10
        air_moist = random.randint(30, 40)
        water_depth = random.randint(1, 10)/10
        soil_moist = random.randint(1, 10)
        soil_ph = random.randint(6, 9)
        solar_rad = random.randint(3, 9)
        wind_speed = random.randint(1, 10)
        wind_dir = random.randint(0, 360)
    
#       data = f"{str(timestamp)},{str(air_temp)},{str(air_moist)},{str(water_depth)},{str(soil_moist)},{str(soil_ph)},{str(solar_rad)},{str(wind_speed)},{str(wind_dir)}"    
        data = {}
        data['timestamp'] = timestamp
        data['air_temp'] = str(air_temp)
        data['air_moist'] = str(air_moist)
        data['water_depth'] = str(water_depth)
        data['soil_moist'] = str(soil_moist)
        data['soil_ph'] = str(soil_ph)
        data['wind_speed'] = str(wind_speed)
        data['solar_rad'] = str(solar_rad)
        data['wind_dir'] = str(wind_dir)
        with open('sensor_data.json', 'r+') as f:
            j = json.loads(f.read())
            j.append(data)
            f.seek(0)
            json.dump(j, f)
        print("sensed")
        await asyncio.sleep_ms(5000)

        

async def publishData_task(c):
    try:
        while True:
            
            with open('sensor_data.json', 'r+') as f:
                j = json.loads(f.read())
                c.publish(PUBLISH_TOPIC, json.dumps(j), qos = 1)
                
            
            with open('sensor_data.json', 'w') as f:
                j = []
                json.dump(j,f)
            print("published")
            await asyncio.sleep_ms(10000)
            
            
            
    except Exception as e:
        print(e)

async def main(c):
    try:
        t1 = asyncio.create_task(getSensorData_task())
        t2 = asyncio.create_task(publishData_task(c))
        await asyncio.gather(t1, t2)
    except Exception as e:
        print(e)


try:
    wlan = connect_to_wifi('Shanta\'s Dell', 'Shanta1111')
    if SERVER == "0.0.0.0":
        SERVER = wlan.ifconfig()[2]
#        getInternetTime()        
    c = MQTTClient(CLIENT_ID, SERVER)
    c.connect()
    print("Connected to %s" % SERVER)
    c.set_callback(subscribe_callback)
    c.subscribe(SUBSCRIBE_TOPIC)
    asyncio.run(main(c))
except (Exception, KeyboardInterrupt) as e:
    try:
        from utility import print_error_msg
        print_error_msg(e)
    except ImportError:
        print("Unable to import utility module")
finally:
    c.disconnect()