from paho.mqtt import client as mqtt
import sqlite3
import json
from datetime import datetime
import sys
import time
import numpy as np
from ml_model import predict_with_saved_model

topic1 = "IOT/location0/data"
topic2 = "IOT/location1/data"
topic3 = "IOT/location2/data"
pub_topic1 = "IOT/location0/server"
client_id = f'python-mqtt-{10}'

sqliteConnection = None

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(topic1)
    client.subscribe(topic2)
    client.subscribe(topic3)

def on_message(client, userdata, msg):
    raw = json.loads(msg.payload)
    
    cursor = sqliteConnection.cursor()
    for data in raw:
        # convert data['timestamp'] list to datetime object
        data['timestamp'] = datetime(*data['timestamp'][:6])
        # print(data['timestamp'])
        cursor.execute("INSERT INTO sensor_data (timestamp, node, air_temp, air_moist, water_depth, soil_moist, soil_ph, wind_speed, solar_rad, wind_dir) VALUES (?,?,?,?, ?,?,?,?, ?,?)", (data['timestamp'], msg.topic ,data['air_temp'], data['air_moist'], data['water_depth'], data['soil_moist'], data['soil_ph'], data['wind_speed'], data['solar_rad'], data['wind_dir']))
    sqliteConnection.commit()
    cursor.close()
    print("Added data from " + msg.topic + " to database")
    irrigation_state = data['irrigation_state']
    # sample from bernoulli distribution
    irrigation_decision = np.random.randint(2)
    # irrigation_decision = predict_with_saved_model()
    if irrigation_decision ^ irrigation_state:
        client.publish(topic=pub_topic1, payload=1)
        print("Irrigation decision: " + str(irrigation_decision))
    
    


def run():
    global sqliteConnection
    if len(sys.argv) != 3:
        print('usage: python server.py <url> <port>')
        sys.exit(1)

    url = sys.argv[1]
    port = int(sys.argv[2])

    sqliteConnection = sqlite3.connect('database.db')
    cursor = sqliteConnection.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS sensor_data (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, node STRING, air_temp FLOAT, air_moist FLOAT, water_depth FLOAT, soil_moist FLOAT, soil_ph FLOAT, wind_speed FLOAT, solar_rad FLOAT, wind_dir FLOAT)")
    sqliteConnection.commit()
    cursor.close()

    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.connect(url, port)
    mqttc.loop_forever()




if __name__ == '__main__':
    run()