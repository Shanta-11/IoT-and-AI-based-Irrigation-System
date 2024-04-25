from paho.mqtt import client as mqtt
import sqlite3
import json
from datetime import datetime
import sys
import time
import numpy as np
from ml_model import predict_with_saved_model

# Define MQTT topics, Each topic corrosponds to a node in the IoT network
topic1 = "IOT/location0/data"
topic2 = "IOT/location1/data"
topic3 = "IOT/location2/data"

pub_topic1 = "IOT/location0/server"
pub_topic2 = "IOT/location1/server"
pub_topic3 = "IOT/location2/server"
client_id = f'python-mqtt-{10}'

sqliteConnection = None

def on_connect(client, userdata, flags, reason_code, properties):
    """
    Callback function that is called when the client successfully connects to the MQTT broker.

    Args:
        client (paho.mqtt.client.Client): The client instance for this callback.
        userdata (Any): The private user data as set in Client() or userdata_set().
        flags (dict): Response flags sent by the broker.
        reason_code (int): The connection result.
        properties (paho.mqtt.properties.Properties): The properties sent by the broker.

    Returns:
        None

    This function is called when the client successfully connects to the MQTT broker.
    It prints the connection result code and subscribes to the specified topics.
    """
    print(f"Connected with result code {reason_code}")
    
    # Subscribe to topics
    client.subscribe(topic1)
    client.subscribe(topic2)
    client.subscribe(topic3)

def on_message(client, userdata, msg):
    """
    Callback function that is called when a message is received from the MQTT broker.

    Args:
        client (paho.mqtt.client.Client): The client instance for this callback.
        userdata (Any): The private user data as set in Client() or userdata_set().
        msg (paho.mqtt.MQTTMessage): The message received from the broker.

    Returns:
        None

    This function processes the received message, converts timestamps, inserts sensor data into the database,
    makes an irrigation decision based on a random number/ML model, and publishes the decision to the MQTT broker and hence to the Node.
    """
    raw = json.loads(msg.payload)
    
    cursor = sqliteConnection.cursor()
    for data in raw:
        # convert data['timestamp'] list to datetime object and insert into database
        data['timestamp'] = datetime(*data['timestamp'][:6])
        cursor.execute("INSERT INTO sensor_data (timestamp, node, air_temp, air_moist, water_depth, soil_moist, soil_ph, wind_speed, solar_rad, wind_dir) VALUES (?,?,?,?, ?,?,?,?, ?,?)", (data['timestamp'], msg.topic ,data['air_temp'], data['air_moist'], data['water_depth'], data['soil_moist'], data['soil_ph'], data['wind_speed'], data['solar_rad'], data['wind_dir']))
    sqliteConnection.commit()
    cursor.close()
    print("Added data from " + msg.topic + " to database")

    # make an irrigation decision based on latest sensor data
    irrigation_state = data['irrigation_state']

    # Uncomment the following line to use the ML model, currently not in use
    
    irrigation_decision = np.random.randint(2)
    # irrigation_decision = predict_with_saved_model()

    if irrigation_decision ^ irrigation_state:
        client.publish(topic=pub_topic1, payload=1)
        print("Irrigation decision: " + str(irrigation_decision))
    
    


def run():
    global sqliteConnection
    if len(sys.argv) != 3:
        print('usage: python server.py <mqtt broker url> <port>')
        sys.exit(1)

    url = sys.argv[1]
    port = int(sys.argv[2])

    # Connect to the database
    sqliteConnection = sqlite3.connect('database.db')

    # Create the table if it doesn't exist
    cursor = sqliteConnection.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS sensor_data (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, node STRING, air_temp FLOAT, air_moist FLOAT, water_depth FLOAT, soil_moist FLOAT, soil_ph FLOAT, wind_speed FLOAT, solar_rad FLOAT, wind_dir FLOAT)")
    sqliteConnection.commit()
    cursor.close()

    # Start MQTT client and set it up
    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.connect(url, port)
    mqttc.loop_forever()




if __name__ == '__main__':
    run()