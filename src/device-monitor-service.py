#!/usr/bin/env python
 
import logging
import logging.handlers
import argparse
import sys
import time  # this is only being used as part of the example
import deviceMonitor

import paho.mqtt.client as mqtt
import time
import json

 
# Deafults
LOG_FILENAME = "/tmp/device-monitor-service.log"
LOG_LEVEL = logging.INFO  # Could be e.g. "DEBUG" or "WARNING"
 
# Define and parse command line arguments
parser = argparse.ArgumentParser(description="My simple Python service")
parser.add_argument("-l", "--log", help="file to write log to (default '" + LOG_FILENAME + "')")
 
# If the log file is specified on the command line then override the default
args = parser.parse_args()
if args.log:
	LOG_FILENAME = args.log
 
# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)
 
# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
	def __init__(self, logger, level):
		"""Needs a logger and a logger level."""
		self.logger = logger
		self.level = level
 
	def write(self, message):
		# Only log if there is a message (not just a new line)
		if message.rstrip() != "":
			self.logger.log(self.level, message.rstrip())
 
# Replace stdout with logging to file at INFO level
sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
sys.stderr = MyLogger(logger, logging.ERROR)
 

# device registration info from IBM Internet of Things Foundation
org="okx4rp"
mqttHost= org + ".messaging.internetofthings.ibmcloud.com"
mqttPort=1883
deviceType="RaspberryPiMQTT"
deviceId="RaspberryPI-0013efb035a7"
clientId="d:" + org + ":" + deviceType + ":" + deviceId
authMethod="token"
authToken="@MTD+L(n-xeOcqpe?O"
topic="iot-2/evt/sump_monitor_update/fmt/json"

def on_connect(mqttClient, obj, rc):
# log connection and response codes
        logger.info("MQTT Connected Code = %d"%(rc))

def on_disconnect(pahoClient, obj, rc):
# log disconnects
        logger.info("MQTT Disconnected Code = %d"%(rc))

# Create a client instance
client=mqtt.Client(client_id=clientId)

# Register callbacks
client.on_connect = on_connect
client.on_disconnnect = on_disconnect

#Set userid and password
client.username_pw_set("use-token-auth", authToken)

#connect and start background loop
logger.info("connecting MQTT client")
x = client.connect(mqttHost, mqttPort, 60)
client.loop_start()

sumpMonitor.setup_gpio()

while True:
    cmDistance = round(sumpMonitor.measureSumpWaterLevel(),1)

    mins_since_last_pump=round((time.time()-sumpMonitor.sump_last_turned_on_time)/60,1)

    payload={}
    #payload["d"]={} # IoT foundation payload starts with "d" for device
    #payload["myName"]=clientId
    payload["sumpTurnOnCount"]=sumpMonitor.sump_turn_on_counter
    payload["sumpMinSinceLastTurnOn"]=mins_since_last_pump
    payload["sumpWaterLevel"]=cmDistance

    logger.info("publishing device data" + json.dumps(payload))
    client.publish(topic, json.dumps(payload), 0)
    #dweepy.dweet_for(dweet_thing_name,{'sump_counter':sump_turn_on_counter, 'minutes_since':mins_since_last_pump, 'water_level':cmDistance})
    time.sleep(10)


client.loop_stop();
client.disconnet();
sumpMonitor.cleanup_gpio();
