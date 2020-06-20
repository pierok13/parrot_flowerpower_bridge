import sys
import json

import paho.mqtt.client as mqtt
from prometheus_client import CollectorRegistry, Gauge, Summary, Enum, push_to_gateway
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from influxdb import InfluxDBClient

from flowerPowerCloud import FlowerPowerCloud

def broadcastMqtt(client, server, port, prefix, postfix, data):
  # Publishing the results to MQTT
  mqttc = mqtt.Client(client)
  mqttc.connect(server, port)

  topic = prefix + "/" + postfix

  #print "MQTT Publish", topic, data
  mqttc.publish(topic, data)

  mqttc.loop(2)

def main(argv):

  print "Starting"
  cloud = FlowerPowerCloud()

  credentials = json.load(open('credentials.json'))
  credentials['auto-refresh'] = False

  configuration = json.load(open('configuration.json'))

  if configuration.has_key("mqtt"):
    try:
      if configuration["mqtt"].has_key("client") is False:
        configuration["mqtt"]["client"] = "Ruuvi-Mqtt"

      if configuration["mqtt"].has_key("server") is False:
        configuration["mqtt"]["server"] = "127.0.0.1"

      if configuration["mqtt"].has_key("port") is False:
        configuration["mqtt"]["port"] = 1883

      if configuration["mqtt"].has_key("prefix") is False:
        configuration["mqtt"]["prefix"] = "weather"

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
        configuration["prometheuspush"]["client"] = "Ruuvi-Prometheus"

      if configuration["prometheuspush"].has_key("prefix") is False:
        configuration["prometheuspush"]["prefix"] = "weather"

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
        configuration["influxdb"]["client"] = "Ruuvi-Influxdb"

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
        configuration["influxdb"]["policy"] = "sensor"

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

  loggedIn = False

  def loginCallback(self, err, res):
    if err:
     print err
    else:
      print "Head in the clouds :)", res
      loggedIn = True

      cloud.getConfiguration(None, getConfigurationCallback)

  def getConfigurationCallback(self, err, res):
    if err:
     print err
    else:
      for location in res["locations"]:
        #print json.dumps(location, indent=2, sort_keys=True)

        flower = {}
        flower["plant_name"] = location["plant_nickname"]
        flower["sensor_name"] = location["sensor"]["sensor_identifier"]
        sensorId = flower["sensor_name"][-4:].lower()

      cloud.getGarden(None, getGardenCallback)

  def getGardenCallback(self, err, res):
    if err:
     print err
    else:

      if configuration["influxdb"]["enabled"]:
        influxDbClient = InfluxDBClient(configuration["influxdb"]["server"], configuration["influxdb"]["port"], 
          configuration["influxdb-username"], configuration["influxdb"]["password"], configuration["influxdb"]["database"])

        try:
          influxDbClient.create_database(configuration["influxdb"]["database"])
        except InfluxDBClientError, ex:
          print "InfluxDBClientError", ex

        influxDbClient.create_retention_policy(configuration["influxdb"]["policy"], 'INF', 3, default=True)

      for location in res["locations"]:
        #print json.dumps(location, indent=2, sort_keys=True)
        sensorId = location["sensor"]["sensor_identifier"][-4:].lower()

        flower = {}
        #flower["sensor_name"] = location["sensor"]["sensor_identifier"]

        if location["battery"]["gauge_values"]["current_value"] is not None:
          flower["battery"] = ("Battery", int(location["battery"]["gauge_values"]["current_value"]))

        if location["air_temperature"]["gauge_values"]["current_value"] is not None:
          flower["air_temperature"] = ("Temperature", float(location["air_temperature"]["gauge_values"]["current_value"]))
          flower["air_temperature_status"] = ["Temperature Status", str(location["air_temperature"]["instruction_key"]).replace("air_temperature_", ""), ["good", "too_low", "too_high"]]

        if location["fertilizer"]["gauge_values"]["current_value"] is not None:
          flower["fertilizer"] = ("Fertilizer",  float(location["fertilizer"]["gauge_values"]["current_value"]))
          flower["fertilizer_status"] = ["Fertilizer Status", str(location["fertilizer"]["instruction_key"]).replace("fertilizer_", ""), ["good", "too_low", "too_high"]]

        if location["light"]["gauge_values"]["current_value"] is not None:
          flower["light"] = ("Light",  float(location["light"]["gauge_values"]["current_value"]))
          flower["light_status"] = ["Light Status", str(location["light"]["instruction_key"]).replace("light_", ""), ["good", "too_low", "too_high"]]

        if location["watering"]["soil_moisture"]["gauge_values"]["current_value"] is not None:
          flower["watering"] = ("Moisture",  float(location["watering"]["soil_moisture"]["gauge_values"]["current_value"]))
          flower["watering_status"] = ["Moisture Status", str(location["watering"]["soil_moisture"]["instruction_key"]).replace("soil_moisture_", ""), ["good", "too_low", "too_high"]]

        lastUtc = ("Updated", str(location["last_sample_utc"]))

        if configuration["mqtt"]["enabled"]:
          print "Pushing Mqtt", sensorId, ":", configuration["mqtt"]["prefix"], flower
          try:
            broadcastMqtt(
              configuration["mqtt"]["client"], 
              configuration["mqtt"]["server"], 
              configuration["mqtt"]["port"], 
              configuration["mqtt"]["prefix"], 
              sensorId + "/update",
              json.dumps(taflowerg))
          except Exception, ex:
            print "Error on mqtt broadcast", ex

        if configuration["prometheuspush"]["enabled"]:
          registry = CollectorRegistry()
          for key in flower.keys():
            print "Pushing", sensorId, ":", configuration["prometheuspush"]["prefix"] + '_' + key + '_total', "=", flower[key]

            if flower[key][1] is None:
              continue

            elif type(flower[key][1]) is str:
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

          print "Pushing", sensorId, ":", configuration["prometheuspush"]["prefix"] + '_' + key + '_total', "=", flower[key]

          try:
            push_to_gateway(configuration["prometheuspush"]["server"] + ":" + configuration["prometheuspush"]["port"], 
              job=configuration["prometheuspush"]["client"] + "_" + sensorId, 
              registry=registry)
          except:
            print "Prometheus not available"

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

          print "Pushing", influxDbJson
          try:
            influxDbClient.write_points(influxDbJson, retention_policy=configuration["influxdb"]["policy"])
          except:
            print "Influxdb not available"

  cloud.login(credentials, loginCallback)

if __name__ == "__main__":
  main(sys.argv)