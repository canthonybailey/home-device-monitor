# module of garageDoorMonitor functions

import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import time
import numpy
import json
import logging
import sys


garage_door_status = "open"
garage_door_cycle_count = 0
garage_door_cycle_time = time.time()

logger = logging.getLogger('device-monitor')
logger.info("I cant find this log %s",  __name__)
print("where is this logging", __name__)

def on_connect(self, mqttClient, obj, rc):
  # log connection and response codes
  logger.info("MQTT Connected Code = %d", rc)

def on_disconnect(self, pahoClient, obj, rc):
  # log disconnects
  logger.info("MQTT Disconnected Code = %d", rc)

def setup_mq():
  # device registration info from IBM Internet of Things Foundation
  org="okx4rp"
  mqttHost= org + ".messaging.internetofthings.ibmcloud.com"
  mqttPort=1883
  deviceType="RPiSwitchMonitor"
  deviceId="garageDoor-70f11c0b6756"
  clientId="d:" + org + ":" + deviceType + ":" + deviceId
  authMethod="token"
  authToken="b)SM)*0MU-PaEmx?tb"

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

  return(client)


def cycle_detected(channel):
  global garage_door_cycle_count
  global garage_door_cycle_time

  garage_door_cycle_count += 1
  garage_door_cycle_time=time.time()
  time.sleep(1)
  getSwitchStatus()
  #print('garage door cycled: cycle count: ', garage_door_cycle_count)
  sendStatusUpdate()

  return

def setup_gpio():
  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BCM)
  # GPIO14 is NC , GPIO 15 is NO, both need pull up resistors
  GPIO.setup(14, GPIO.IN, pull_up_down = GPIO.PUD_UP) # door closed limit switch
  GPIO.add_event_detect(14, GPIO.BOTH, callback=cycle_detected, bouncetime=300)
  return

def getSwitchStatus():
  global garage_door_status

  if GPIO.input(14)==1:
     garage_door_status = "closed"
  else:
     garage_door_status = "open"

  logger.info("Garage door status: %s", garage_door_status)
  return(garage_door_status)

def cleanup_gpio():
  GPIO.cleanup()


def sendStatusUpdate(client):
    topic="iot-2/evt/switch_status_update/fmt/json"

    payload={}
    payload["garageDoorCycleCount"]=garage_door_cycle_count
    payload["garageDoorCycleTime"]=garage_door_cycle_time
    payload["garageDoorStatus"]=garage_door_status

    logger.info("publishing device data" + json.dumps(payload))
    client.publish(topic, json.dumps(payload), 0)


def start(sleepTime):
  logger.info("starting garage door monitor main loop")
  setup_gpio()
  client=setup_mq()
  client.loop_start();

  while True:
    getSwitchStatus()
    sendStatusUpdate(client)
    time.sleep(sleepTime)

  cleanup_gpio()
  client.loop_stop();
  client.disconnect();

if __name__ == "__main__":
  logging.basicConfig(filename='./monitor.log',level=logging.DEBUG)
  logger.info("testing module")
  sleepTime = 2
  start(sleepTime)
