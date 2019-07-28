import sys
import json
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

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

  print "Configuration:"
  print "Prometheus Push Client:   ", configuration["prometheuspush-client"]
  print "Prometheus Push Server:   ", configuration["prometheuspush-server"]
  print "Prometheus Push Port:     ", configuration["prometheuspush-port"]
  print "Prometheus Push Prefix   :", configuration["prometheuspush-prefix"]

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
      for location in res["locations"]:
        #print json.dumps(location, indent=2, sort_keys=True)
        sensorId = location["sensor"]["sensor_identifier"][-4:].lower()

        flower = {}
        #flower["sensor_name"] = location["sensor"]["sensor_identifier"]

        flower["battery"] = ("Battery", location["battery"]["gauge_values"]["current_value"])

        flower["air_temperature"] = ("Temperature", location["air_temperature"]["gauge_values"]["current_value"])
        #flower["air_temperature_status"] = ("Temperature Status", location["air_temperature"]["instruction_key"])

        flower["fertilizer"] = ("Fertilizer", location["fertilizer"]["gauge_values"]["current_value"])
        #flower["fertilizer_status"] = ("Fertilizer Status", location["fertilizer"]["instruction_key"])

        flower["light"] = ("Light", location["light"]["gauge_values"]["current_value"])
        #flower["light_status"] = ("Light Status", location["light"]["instruction_key"])

        flower["watering"] = ("Moisture", location["watering"]["soil_moisture"]["gauge_values"]["current_value"])
        #flower["watering_status"] = ("Moisture Status", location["watering"]["soil_moisture"]["instruction_key"])

        #flower["last_utc"] = location["last_sample_utc"]

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

  cloud.login(credentials, loginCallback)

if __name__ == "__main__":
  main(sys.argv)