# IoT and AI based Irrigation System

  

The system consists of many IoT nodes which sense various environmental variables (Currently random numbers) and turn on/off the irrigation system based on the response from the server. The nodes use MQTT protocol to publish their sensed data to a broker in a specific topic (Different for each node). A python server reads the published data and adds the data along with timestamp to a sqlite3 database for some future analysis (Not implemented). The server also makes an irrigation decision (wether to turn on or off) based on the current sensed data using the AI model (Currently uses random decision as data is synthetic) and publishes the decision for the specific node to read and perform action.

  

The project consists of 5 files

1. `main.py`: The code to be executed on the IoT device (Micropython)
2. `server.py`: The code for the server
3. `IOT_Project.ipynb`: The EDA and Construction of the AI model
4. `ml_model.py & random_forest_model.pkl`: Model integration file and the weights of the model

## Usage

Start the MQTT broker on the network.
Put the `main.py` file on the IoT device and change the wifi ssid and password to your credentials and change the IP and Port of the MQTT broker to whatever ip and port you used.
Start the server by `python server.py <broker url> <broker port>`
