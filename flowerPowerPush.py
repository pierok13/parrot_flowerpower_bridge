import sys
import json
import time
from datetime import datetime

import paho.mqtt.client as mqtt
from prometheus_client import CollectorRegistry, Gauge, Summary, Enum, push_to_gateway
from influxdb import InfluxDBClient

from flowerPower import FlowerPower
from flowerPowerScanner import FlowerPowerScanner

def broadcastMqtt(client, server, port, prefix, postfix, data):
  # Publishing the results to MQTT
  mqttc = mqtt.Client(client)
  mqttc.connect(server, port)

  topic = prefix + "/" + postfix

  #print "MQTT Publish", topic, data
  mqttc.publish(topic, data)

  mqttc.loop(2)

def main(argv):
  deviceFilter = None

  print "Starting"

  configuration = json.load(open('configuration.json'))

  if configuration.has_key("mqtt"):
    try:
      if configuration["mqtt"].has_key("client") is False:
        configuration["mqtt"]["client"] = "Flowerpower-Mqtt"

      if configuration["mqtt"].has_key("server") is False:
        configuration["mqtt"]["server"] = "127.0.0.1"

      if configuration["mqtt"].has_key("port") is False:
        configuration["mqtt"]["port"] = 1883

      if configuration["mqtt"].has_key("prefix") is False:
        configuration["mqtt"]["prefix"] = "flower"

      if configuration["mqtt"].has_key("enabled") is False:
        configuration["mqtt"]["enabled"] = True

      print "MQTT Configuration:"
      print "MQTT Client:   ", configuration["mqtt"]["client"]
      print "MQTT Server:   ", configuration["mqtt"]["server"]
      print "MQTT Port:     ", configuration["mqtt"]["port"]
      print "MQTT Prefix:   ", configuration["mqtt"]["prefix"]
      print "MQTT Enabled:  ", configuration["mqtt"]["enabled"]

    except Exception, ex:
      print "Error parsing mqtt configuration", ex
      configuration["mqtt"]["enabled"] = False
  else:
    configuration["mqtt"] = {}
    configuration["mqtt"]["enabled"] = False

  if configuration.has_key("prometheuspush"):
    try:
      if configuration["prometheuspush"].has_key("server") is False:
        configuration["prometheuspush"]["server"] = "127.0.0.1"

      if configuration["prometheuspush"].has_key("port") is False:
        configuration["prometheuspush"]["port"] = 9091

      if configuration["prometheuspush"].has_key("client") is False:
        configuration["prometheuspush"]["client"] = "Flowerpower-Prometheus"

      if configuration["prometheuspush"].has_key("prefix") is False:
        configuration["prometheuspush"]["prefix"] = "flower"

      if configuration["prometheuspush"].has_key("enabled") is False:
        configuration["prometheuspush"]["enabled"] = True

      print "Prometheus Push Configuration:"
      print "Prometheus Push Client:   ", configuration["prometheuspush"]["client"]
      print "Prometheus Push Server:   ", configuration["prometheuspush"]["server"]
      print "Prometheus Push Port:     ", configuration["prometheuspush"]["port"]
      print "Prometheus Push Prefix:   ", configuration["prometheuspush"]["prefix"]
      print "Prometheus Push Enabled:  ", configuration["prometheuspush"]["enabled"]

    except Exception, ex:
      print "Error parsing prometheuspush configuration", ex
      configuration["prometheuspush"]["enabled"] = False
  else:
    configuration["prometheuspush"] = {}
    configuration["prometheuspush"]["enabled"] = False

  if configuration.has_key("influxdb"):
    try:
      if configuration["influxdb"].has_key("client") is False:
        configuration["influxdb"]["client"] = "Flowerpower-Influxdb"

      if configuration["influxdb"].has_key("server") is False:
        configuration["influxdb"]["server"] = "127.0.0.1"

      if configuration["influxdb"].has_key("username") is False:
        configuration["influxdb"]["username"] = "influxdb"

      if configuration["influxdb"].has_key("password") is False:
        configuration["influxdb"]["password"] = "influxdb"

      if configuration["influxdb"].has_key("port") is False:
        configuration["influxdb"]["port"] = 8086

      if configuration["influxdb"].has_key("database") is False:
        configuration["influxdb"]["database"] = "measurements"

      if configuration["influxdb"].has_key("policy") is False:
        configuration["influxdb"]["policy"] = "flower"

      if configuration["influxdb"].has_key("prefix") is False:
        configuration["influxdb"]["prefix"] = "weather"

      if configuration["influxdb"].has_key("enabled") is False:
        configuration["influxdb"]["enabled"] = True

      print "Influxdb Configuration:"
      print "Influxdb Client:     ", configuration["influxdb"]["client"]
      print "Influxdb Username:   ", configuration["influxdb"]["username"]
      print "Influxdb Password:   ", configuration["influxdb"]["password"]
      print "Influxdb Server:     ", configuration["influxdb"]["server"]
      print "Influxdb Port:       ", configuration["influxdb"]["port"]
      print "Influxdb Database:   ", configuration["influxdb"]["database"]
      print "Influxdb Policy:     ", configuration["influxdb"]["policy"]
      print "Influxdb Prefix:     ", configuration["influxdb"]["prefix"]
      print "Influxdb Enabled:    ", configuration["influxdb"]["enabled"]

    except Exception, ex:
      print "Error parsing influxdb configuration", ex
      configuration["influxdb"]["enabled"] = False
  else:
    configuration["influxdb"] = {}
    configuration["influxdb"]["enabled"] = False

  plants = []
  if configuration.has_key("flowerpower"):
    flowerpower = configuration["flowerpower"]
    if flowerpower.has_key("plants"):
      plants = flowerpower["plants"]

    if flowerpower.has_key("sensors"):
      sensors = flowerpower["sensors"]

  print plants

  if configuration.has_key("miflora"):
    miflora = configuration["miflora"]
    if miflora.has_key("plants"):
      plants.extend(miflora["plants"])

  print plants
  print sensors

  scanner = FlowerPowerScanner()
  devices = scanner.discoverAll()

  if configuration["influxdb"]["enabled"]:
    influxDbClient = InfluxDBClient(configuration["influxdb"]["server"], configuration["influxdb"]["port"], 
      configuration["influxdb"]["username"], configuration["influxdb"]["password"], configuration["influxdb"]["database"])

    try:
      influxDbClient.create_database(configuration["influxdb"]["database"])
    except InfluxDBClientError, ex:
      print "InfluxDBClientError", ex

  if devices is not None:
    for device in devices:

      deviceSensor = None
      for sensor in sensors:
        if sensor.has_key("name") and sensor["name"] == device.name:
          deviceSensor = sensor

      print "deviceSensor", deviceSensor
      if deviceSensor is None:
        continue

      sensorId = str(deviceSensor["name"][-4:].lower())

      devicePlant = None
      if deviceSensor is not None and deviceSensor.has_key("plant-name"):
        for plant in plants:
          if plant.has_key("name") and plant["name"] == deviceSensor["plant-name"]:
            devicePlant = plant

            if deviceSensor.has_key("location"):
              devicePlant["location"] = deviceSensor["location"]

      print "devicePlant", devicePlant

      if devicePlant is not None:
        if device.connectAndSetup() is True:
          battery      = device.readBatteryLevel()

          try:
            moisture = device.readCalibratedSoilMoisture()
            if moisture == 0.0:
              moisture = device.readSoilMoisture()
          except:
            device.connectAndSetup()
            moisture = None

          try:
            temperature = device.readCalibratedAirTemperature()
            if temperature == 0.0:
              temperature = device.readAirTemperature()
          except:
            device.connectAndSetup()
            temperature = None

          try:
            #conductivity = device.readCalibratedEcPorous() #readCalibratedEcb
            #if conductivity == 0.0:
            conductivity = device.readSoilElectricalConductivity()
          except:
            device.connectAndSetup()
            conductivity = None

          try:
            light = device.readCalibratedSunlight()
            if light == 0.0:
              light = device.readSunlight()
          except:
            device.connectAndSetup()
            light = None

          if battery is not None and battery > 0 and moisture is not None and moisture > 0.0:
            pushData(sensorId, battery, temperature, conductivity, light, moisture, configuration, plant, influxDbClient)

          time.sleep(0.2)

def pushData(sensorId, battery, temperature, conductivity, light, moisture, configuration, plant, influxDbClient):
  flower = {}

  #flower["plant_name"] = ("Plant", devicePlant["name"])

  flower["plant"] = ("Plant", str(plant["name"]))
  flower["location"] = ("Location", str(plant["location"]))

  if battery is not None:
    flower["battery"] = ("Battery", int(battery))

  if temperature is not None:
    flower["air_temperature"] = ("Temperature", float(temperature))
    flower["air_temperature_status"] = ["Temperature Status", "good", ["good", "too_low", "too_high"]]

    if temperature < plant["temperature_C_threshold_lower"]:
      flower["air_temperature_status"][1] = "too_low"
    elif temperature > plant["temperature_C_threshold_upper"]:
      flower["air_temperature_status"][1] = "too_high"

  if conductivity is not None:
    flower["fertilizer"] = ("Fertilizer", float(conductivity))
    flower["fertilizer_status"] = ["Fertilizer Status", "good", ["good", "too_low", "too_high"]]

    if conductivity < plant["fertility_us_cm_threshold_lower"]:
      flower["fertilizer_status"][1] = "too_low"
    elif conductivity > plant["fertility_us_cm_threshold_upper"]:
      flower["fertilizer_status"][1] = "too_high"

  if light is not None:
    flower["light"] = ("Light", float(light))
    flower["light_status"] = ["Light Status", "good", ["good", "too_low", "too_high"]]

    if light < plant["light_lux_threshold_lower"]:
      flower["light_status"][1] = "too_low"
    elif light > plant["light_lux_threshold_upper"]:
      flower["light_status"][1] = "too_high"

  if moisture is not None:
    flower["watering"] = ("Moisture", float(moisture))
    flower["watering_status"] = ["Moisture Status", "good", ["good", "too_low", "too_high"]]

    if moisture < plant["moisture_threshold_lower"]:
      flower["watering_status"][1] = "too_low"
    elif moisture > plant["moisture_threshold_upper"]:
      flower["watering_status"][1] = "too_high"

  now = datetime.utcnow()
  lastUtc = ("Updated", now.strftime("%Y-%m-%dT%H:%M:%SZ")) #2017-11-13T17:44:11Z

  if configuration["mqtt"]["enabled"]:
    print "Pushing Mqtt", sensorId, ":", configuration["mqtt"]["prefix"], flower
    try:
      broadcastMqtt(
        configuration["mqtt"]["client"], 
        configuration["mqtt"]["server"], 
        configuration["mqtt"]["port"], 
        configuration["mqtt"]["prefix"], 
        sensorId + "/update",
        json.dumps(flower))
    except Exception, ex:
      print "Error on mqtt broadcast", ex

  if configuration["prometheuspush"]["enabled"]:
    registry = CollectorRegistry()
    for key in flower.keys():

      if type(flower[key][1]) is str:
        if len(flower[key]) == 3:
          e = Enum(configuration["prometheuspush"]["prefix"]  + '_' + key + '_total', 
            flower[key][0], ['sensorid'],
            states=flower[key][2],
            registry=registry)

          e.labels(sensorid=sensorId).state(flower[key][1])
      else:
        g = Gauge(configuration["prometheuspush"]["prefix"]  + '_' + key + '_total', 
          flower[key][0], ['sensorid'],
          registry=registry)

        g.labels(sensorid=sensorId).set(flower[key][1])

    print "Pushing Prometheus", sensorId, ":", configuration["prometheuspush"]["prefix"] + '_' + key + '_total', "=", flower[key]

    try:
      push_to_gateway(configuration["prometheuspush"]["server"] + ":" + configuration["prometheuspush"]["port"], 
        job=configuration["prometheuspush"]["client"] + "_" + sensorId, 
        registry=registry)
    except Exception, ex:
      print "Error on prometheus push", ex

  if configuration["influxdb"]["enabled"]:
    influxDbJson = [
    {
      "measurement": configuration["influxdb"]["prefix"],
      "tags": {
          "sensor": sensorId,
      },
      "time": lastUtc[1],
      "fields": {
      }
    }]
    for key in flower.keys():
      influxDbJson[0]["fields"][key] = flower[key][1]

    print "Pushing InfluxDb", influxDbJson
    try:
      influxDbClient.write_points(influxDbJson, retention_policy=configuration["influxdb"]["policy"])
    except Exception, ex:
      print "Error on influxdb write_points", ex

if __name__ == "__main__":
  main(sys.argv)