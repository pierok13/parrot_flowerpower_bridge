import sys
import json

from prometheus_client import CollectorRegistry, Gauge, Summary, Enum, push_to_gateway
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from influxdb import InfluxDBClient

from flowerPowerCloud import FlowerPowerCloud

def main(argv):

  print "Starting"
  cloud = FlowerPowerCloud()

  credentials = json.load(open('credentials.json'))
  credentials['auto-refresh'] = False

  configuration = json.load(open('configuration.json'))
  if configuration.has_key("prometheuspush-client") is False:
    configuration["prometheuspush-client"] = "Parrot-Prometheus"

  if configuration.has_key("prometheuspush-server") is False:
    configuration["prometheuspush-server"] = "127.0.0.1"

  if configuration.has_key("prometheuspush-port") is False:
    configuration["prometheuspush-port"] = 9091

  if configuration.has_key("prometheuspush-prefix") is False:
    configuration["prometheuspush-prefix"] = "flower"

  if configuration.has_key("influxdb-client") is False:
    configuration["influxdb-client"] = "Ruuvi-Influxdb"

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

  #if configuration.has_key("mqtt-p") is False:
  #  configuration["mqtt-prefix"] = "flower"

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

      influxDbClient = InfluxDBClient(configuration["influxdb-server"], configuration["influxdb-port"], 
        configuration["influxdb-username"], configuration["influxdb-password"], configuration["influxdb-database"])

      try:
        influxDbClient.create_database(configuration["influxdb-database"])
      except InfluxDBClientError, ex:
        print "InfluxDBClientError", ex

        # Drop and create
        #client.drop_database(DBNAME)
        #client.create_database(DBNAME)

      influxDbClient.create_retention_policy(configuration["influxdb-policy"], 'INF', 3, default=True)

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

        registry = CollectorRegistry()
        for key in flower.keys():
          print "Pushing", sensorId, ":", configuration["prometheuspush-prefix"] + '_' + key + '_total', "=", flower[key]

          if flower[key][1] is None:
            continue

          elif type(flower[key][1]) is str:
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

          #print "Pushing", sensorId, ":", configuration["prometheuspush-prefix"] + '_' + key + '_total', "=", flower[key]

        push_to_gateway(configuration["prometheuspush-server"] + ":" + configuration["prometheuspush-port"], 
          job=configuration["prometheuspush-client"] + "_" + sensorId, 
          registry=registry)

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
        influxDbClient.write_points(influxDbJson, retention_policy=configuration["influxdb-policy"])

  cloud.login(credentials, loginCallback)

if __name__ == "__main__":
  main(sys.argv)