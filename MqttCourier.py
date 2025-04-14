import os
import sys
import json
import time
import socket
import ipaddress
import numpy as np
import dns.resolver
from termcolor import colored # Color text at terminal
import paho.mqtt.client as mqtt
from typing import Dict, Any


class MqttCourier:
    def __init__(self, config_file: str, auto_connect:bool = True, logging_level:Any = mqtt.LogLevel.MQTT_LOG_ERR):
        """
        Initializes an MqttCourcier with the given configuration file
        
        :param config_file: Filename of the JSON configuration file.
        :param auto_connect: If the courier should connect on being initialized. 
        :param logging:level: Level of MQTT logging.
        """ 
        
        # Load the config and check if it is valid to connect
        self.config = self.load_configuration(config_file)
        self.check_ip(self.config.get("broker_ip"))
        self.check_port(self.config.get("broker_port"))
        
        # Set up a dictionary for received data
        self.received_data = {}
        
        # Set MQTT logging level used in on_log()
        self.logging_level = logging_level
        
        # Initialize the MQTT client
        self.client = mqtt.Client()
        
        # Set MQTT client callbacks defined below
        self.client.on_connect = self.__on_connect
        self.client.on_log = self.__on_log
        self.client.on_message = self.__on_message
        self.client.on_publish = self.__on_publish
        self.client.on_subscribe = self.__on_subscribe
        self.client.on_disconnect = self.__on_disconnect
        
        # Set up the MQTT client
        self.client.username_pw_set(self.config['broker_user'], self.config['broker_password'])
        
        if auto_connect:
            self.connect()
    
    # Configuration methods
    
    def load_configuration(self, file_name: str) -> Dict[str, Any]:
        # Check if the configuration file exists
        if not (os.path.isfile(file_name)):
            print(colored("FAIL", "red"))
            print("MQTT configuration file not found!")
            return None
            
        print(f"Configuration file \"{file_name}\" found, try to read it...")
        # Open the configuration file
        with open(file_name, "r") as json_file:
            try:
                # Load the file
                config = json.load(json_file)
                print(colored("OK", "green"))
                print("Config file successfully read!")
                return config
            except Exception as e:
                print(colored("FAIL", "red"))
                print(f"Error reading configuration file: {e}")
                return None
    
    def check_ip(self, ip_addr : str) -> None:
        
        # Check if the string is empty
        if not ip_addr:
            raise NameError("No ip address given in the config")
        
        try:
            # Try to check for a valid IP address...
            ipaddress.ip_address(ip_addr)
            #...IP address is valid!
            print("Broker ip is a valid ip address")
        except:
            #...IP address is not valid, maybe it is a string with a dnsname!?
            try:
                # Try to resolve dnsname...
                socket.gethostbyname(ip_addr)
                #...name was resolved
                print("Broker ip is a valid dns name")
            except:
                # If we get to here the IP address is not correct
                # neither the dns name is resolvable
                raise TypeError("Config ip is not usable to connect via MQTT")
            
    def check_port(self, port : str) -> None:
        
        # Check if the string is empty
        if not port:
            raise NameError("No port given in the config")
        
        try:
            int(port)
        except:
            raise TypeError("Config port cannot be converted to int and so is not usable to connect via MQTT")
            
        
    # MQTT callbacks (private, because do not have to be used outside the class itself)
    
    def __on_log(self, client: mqtt.Client, userdata: Any, level: int, buf: str) -> None:
        if level == self.logging_level:
            print(buf)
    
    def __on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        # Save the received data based on the topic
        self.received_data[msg.topic] = msg.payload.decode()
    
    def __on_publish(self, client: mqtt.Client, userdata: Any, mid: int) -> None:
        #print(f"Message published with ID: {mid}")
        pass
    
    def __on_subscribe(self, client: mqtt.Client, userdata: Any, mid: int, granted_qos: tuple[int, ...]) -> None:
        #print(f"Subscribed with ID: {mid}")
        pass
    
    def __on_connect(self, client: mqtt.Client, userdata: Any, flags: Dict[str, int], rc: int) -> None:
        
        # Connectiong to MQTT
        print(f"Connect reason code: {rc}")
        if rc != 0:
            print(f"Failed to connect, reason code {rc}")
            raise NotImplementedError

        print("Connected to MQTT Broker")
        
        # Subscribing to all need topics on connection
        self.__subscribe_to_all()
 
    def __on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int):
        
        print (f"Disconnected with result code: {rc}")
    
        if self.keep_running:
            print("Disconnect not on purpose. Try reconnect")
            self.attempt_reconnect()
        

    # Higher level courier functions used for the communication
    
    def connect(self) -> None:
        self.keep_running = True
        self.client.connect(self.config.get("broker_ip"), int(self.config.get("broker_port")), 60)
        self.client.loop_start()
        
    def disconnect(self) -> None:
        self.keep_running = False
        self.client.loop_stop()
        self.client.disconnect()
    
    def attempt_reconnect(self) -> None:
        # Reconnect parameters
        FIRST_RECONNECT_DELAY = 1
        RECONNECT_RATE = 2
        MAX_RECONNECT_COUNT = 12
        MAX_RECONNECT_DELAY = 60
        
        reconnect_count, reconnect_delay = 0, FIRST_RECONNECT_DELAY
        
        while reconnect_count < MAX_RECONNECT_COUNT:
            print (f"Reconnecting in {reconnect_delay} seconds...")
            time.sleep(reconnect_delay)

            try:
                self.client.reconnect()
                print ("Reconnected successfully!")
                return
            except Exception as err:
                print(f"{err}. Reconnect failed. Retrying...", err)

            reconnect_delay *= RECONNECT_RATE
            reconnect_delay = min(reconnect_delay, MAX_RECONNECT_DELAY)
            reconnect_count += 1
        print("Reconnect failed after %s attempts. Exiting...", reconnect_count)
        sys.exit()
    
    def __subscribe_to_all(self) -> None:
        subscribe_topics = self.config.get('subscribe_topics', {})
        
        # Subscribe to the topics
        print("Try to subscribe to configuration file topics...")
        for topic, topic_key in subscribe_topics.items():
            result = self.client.subscribe(self.config.get('instance') + "/" + topic)
            print("Subscribed to topic: " + topic_key + " : " + self.config.get('instance') + "/" + topic)
            status = result[0]
            if status != 0:
                print("Failed to subscribe to topic: " +  topic_key + " : " + self.config.get('instance') + "/" + topic + "\n")
                return False
        print("Successfully subscribed to all topics!")
        print("Ready to send data...","\n")
        return True    
    
    def get_data_by_topic(self, topic_key: str) -> str:
        subscribe_topics = self.config.get('subscribe_topics', {})
        
        if not topic_key in subscribe_topics.values():
            print(f"Topic key '{topic_key}' is not in 'subscribe_topics' list of the configuration file.")
            return 0
        
        # Find the topic associated with the given topic_key in subscribe_topics 
        topic = next(key for key, value in subscribe_topics.items() if value == topic_key)
        topic_up = self.config.get('instance') + "/" + topic    
        if topic_up in self.received_data:
            #print("Read data on Topic:    ", topic_up, ":", received_data[topic_up])
            return self.received_data[topic_up]
        else:
            print("No data on topic:", topic_key + " : " + topic_up)
            return "0"
        
    def send_data_by_topic(self, topic_key: str, data: str) -> None:
        publish_topics = self.config.get('publish_topics', {})
        config_data_types = self.config.get("config_data_types", {})
        
        # When German convention is used, replace with international one
        data = data.replace(",", ".")
        
        # Check if topic key even there and if so, determine topic name
        if not topic_key in publish_topics.values():
            raise KeyError(f"{topic_key} is not included in the config")
        topic = next(key for key, value in publish_topics.items() if value == topic_key)
        
        # Check the data types
        if not topic in config_data_types:
            raise KeyError(f"{topic} ({topic_key} in short) has no data type specified in the config")
        expected_type = config_data_types[topic]
        if expected_type == "bool":
            if data.lower() == "true" or data == "1":
                data = "1"
            elif data.lower() == "false" or data == "0":
                data = "0"
            else:
                print(colored('Data on Topic: ', 'red') + self.config.get('instance') + "/" + f"{topic} : {data} not published!")
                print(f"Error: Data type mismatch for topic: " + self.config.get('instance') + "/" + topic + f". Value '{data}' must be of type 'bool'!")
                return
        elif expected_type == "str":
            if len(data)<=4:
                data=data
            else:
                print(colored('Data on Topic: ', 'red') + self.config.get('instance') + "/" + f"{topic} : {data} not published!")
                print(f"Error: Data type mismatch for topic: " + self.config.get('instance') + "/" + topic + f". Value '{data}' must be of type 'bool'!")
                return
        # Handle 'float' data type		
        elif expected_type == "float":
            try:
                data = str(round(float(data),3))
            except ValueError:
                print(colored('Data on Topic: ', 'red') + self.config.get('instance') + "/" + f"{topic} : {data} not published!")
                print(f"Error: Data type mismatch for topic: " + self.config.get('instance') + "/" + topic + f". Value'{data}' must be of type 'float'!")
                return
        # Handle 'int' data type
        elif expected_type == "int":
            try:
                data = str(int(data))
            except ValueError:
                print(colored('Data on Topic: ', 'red') + self.config.get('instance') + "/" + f"{topic} : {data} not published!")
                print(f"Error: Data type mismatch for topic: " + self.config.get('instance') + "/" + topic + f". Value '{data}' must be of type 'int'!")
                return
        # Unsupported data type set
        else:
            print(colored('Data on Topic: ', 'red') + self.config.get('instance') + "/" + f"{topic} : {data} not published!")
            print(f"Error: Received data type mismatch for topic '{topic}'")
            return
        
        self.client.publish(self.config.get('instance') + "/" + topic, data)
        
        # Print published data
        print(colored('Publish data on Topic: ', 'green') , topic_key + " : " + self.config.get('instance') + "/" + topic + " : " + data)