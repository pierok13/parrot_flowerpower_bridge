import sys
import json
import time
from datetime import datetime

from prometheus_client import CollectorRegistry, Gauge, Summary, Enum, push_to_gateway
from influxdb import InfluxDBClient

from flowerPower import FlowerPower
from flowerPowerScanner import FlowerPowerScanner


def main(argv):
  deviceFilter = None

  print "Starting"

  configuration = json.load(open('configuration.json'))
  if configuration.has_key("prometheuspush-client") is False:
    configuration["prometheuspush-client"] = "Flowerpower-Prometheus"

  if configuration.has_key("prometheuspush-server") is False:
    configuration["prometheuspush-server"] = "127.0.0.1"

  if configuration.has_key("prometheuspush-port") is False:
    configuration["prometheuspush-port"] = 9091

  if configuration.has_key("prometheuspush-prefix") is False:
    configuration["prometheuspush-prefix"] = "flower"

  if configuration.has_key("influxdb-client") is False:
    configuration["influxdb-client"] = "Flowerpower-Influxdb"

  if configuration.has_key("influxdb-server") is False:
    configuration["influxdb-server"] = "127.0.0.1"

  if configuration.has_key("influxdb-username") is False:
    configuration["influxdb-username"] = "influxdb"

  if configuration.has_key("influxdb-password") is False:
    configuration["influxdb-password"] = "influxdb"

  if configuration.has_key("influxdb-port") is False:
    configuration["influxdb-port"] = 8086

  if configuration.has_key("influxdb-database") is False:
    configuration["influxdb-database"] = "measurements"

  if configuration.has_key("influxdb-policy") is False:
    configuration["influxdb-policy"] = "sensor"

  if configuration.has_key("influxdb-prefix") is False:
    configuration["influxdb-prefix"] = "flower"

  print "Configuration:"
  print "Prometheus Push Client:   ", configuration["prometheuspush-client"]
  print "Prometheus Push Server:   ", configuration["prometheuspush-server"]
  print "Prometheus Push Port:     ", configuration["prometheuspush-port"]
  print "Prometheus Push Prefix   :", configuration["prometheuspush-prefix"]

  print "Influxdb Push Client:     ", configuration["influxdb-client"]
  print "Influxdb Push Username:   ", configuration["influxdb-username"]
  print "Influxdb Push Password:   ", configuration["influxdb-password"]
  print "Influxdb Push Server:     ", configuration["influxdb-server"]
  print "Influxdb Push Port:       ", configuration["influxdb-port"]
  print "Influxdb Push Database    ", configuration["influxdb-database"]
  print "Influxdb Push Policy      ", configuration["influxdb-policy"]
  print "Influxdb Push Prefix      ", configuration["influxdb-prefix"]

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

  influxDbClient = InfluxDBClient(configuration["influxdb-server"], configuration["influxdb-port"], 
    configuration["influxdb-username"], configuration["influxdb-password"], configuration["influxdb-database"])

  try:
    influxDbClient.create_database(configuration["influxdb-database"])
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
            dataToPrometheus(sensorId, battery, temperature, conductivity, light, moisture, configuration, plant, influxDbClient)

          time.sleep(0.2)

def dataToPrometheus(sensorId, battery, temperature, conductivity, light, moisture, configuration, plant, influxDbClient):
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

  registry = CollectorRegistry()
  for key in flower.keys():

    if type(flower[key][1]) is str:
      if len(flower[key]) == 3:
        e = Enum(configuration["prometheuspush-prefix"]  + '_' + key + '_total', 
          flower[key][0], ['sensorid'],
          states=flower[key][2],
          registry=registry)

        e.labels(sensorid=sensorId).state(flower[key][1])
    else:
      g = Gauge(configuration["prometheuspush-prefix"]  + '_' + key + '_total', 
        flower[key][0], ['sensorid'],
        registry=registry)

      g.labels(sensorid=sensorId).set(flower[key][1])

    print "Pushing", sensorId, ":", configuration["prometheuspush-prefix"] + '_' + key + '_total', "=", flower[key]

  try:
    push_to_gateway(configuration["prometheuspush-server"] + ":" + configuration["prometheuspush-port"], 
      job=configuration["prometheuspush-client"] + "_" + sensorId, 
      registry=registry)
  except:
    print "Prometheus not available"

  influxDbJson = [
  {
    "measurement": configuration["influxdb-prefix"],
    "tags": {
        "sensor": sensorId,
    },
    "time": lastUtc[1],
    "fields": {
    }
  }]
  for key in flower.keys():
    influxDbJson[0]["fields"][key] = flower[key][1]

  print "Pushing", influxDbJson
  try:
    influxDbClient.write_points(influxDbJson, retention_policy=configuration["influxdb-policy"])
  except:
    print "Influxdb not available"

if __name__ == "__main__":
  main(sys.argv)