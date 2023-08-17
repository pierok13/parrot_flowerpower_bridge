import sys
import json
from datetime import datetime
import time

from flowerPower import FlowerPower
from flowerPowerScanner import FlowerPowerScanner
import paho.mqtt.client as mqtt

def broadcastMqtt(client, server, port, user,passwd, prefix, postfix, data):
    # Publishing the results to MQTT
    mqttc = mqtt.Client(client)
    mqttc.username_pw_set(user,passwd)
    mqttc.connect(server, port)
    topic = prefix + "/" + postfix
    print ("MQTT Publish", topic, data)
    mqttc.publish(topic, data)
    mqttc.loop(2)


def getSamples(device, dataBLE):
    dataBLE['airtemp'] = device.readAirTemperature()
    dataBLE['sun'] = device.readSunlight()
    dataBLE['soiltemp'] = device.readSoilTemperature()
    dataBLE['batterylevel']= device.readBatteryLevel()
    dataBLE['calibratedSoilMoisture'] = device.readCalibratedSoilMoisture()
    dataBLE['soilDry'] = device.getStatusFlags().soilDry
    dataBLE['soilWet'] = device.getStatusFlags().soilWet
    return dataBLE

def main(argv):
    print("Starting")
    configuration = json.load(open('configuration.json'))
    if "mqtt-client" not in configuration :
      configuration["mqtt-client"] = "FlowerPowerCloud-Mqtt"

    if "mqtt-server" not in configuration :
      configuration["mqtt-server"] = "127.0.0.1"

    if "mqtt-port" not in configuration:
      configuration["mqtt-port"] = 1883

    if "mqtt-prefix" not in configuration :
      configuration["mqtt-prefix"] = "flower"

    print("Flower discover All")
    scanner = FlowerPowerScanner()
    devices = scanner.discoverAll()

    if devices is not None:
        for device in devices:
            if device.connectAndSetup() is True:
                dataBLE = {}
                dataBLE = getSamples(device,  dataBLE)
                for key,data in dataBLE.items() :
                    broadcastMqtt(
                        configuration["mqtt-client"],
                        configuration["mqtt-server"],
                        configuration["mqtt-port"],
                        configuration["mqtt-user"],
                        configuration["mqtt-passwd"],
                        configuration["mqtt-prefix"],
                        key,
                        data)
if __name__ == "__main__":
    main(sys.argv)
