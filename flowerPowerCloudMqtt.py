import sys
import json
import paho.mqtt.client as mqtt

from flowerPowerCloud import FlowerPowerCloud

def broadcastMqtt(client, server, port, prefix, postfix, data):
  # Publishing the results to MQTT
  mqttc = mqtt.Client(client)
  mqttc.connect(server, port)

  topic = prefix + "/" + postfix

  print "MQTT Publish", topic, data
  mqttc.publish(topic, data)

  mqttc.loop(2)

def main(argv):

  print "Starting"
  cloud = FlowerPowerCloud()

  credentials = json.load(open('credentials.json'))
  credentials['auto-refresh'] = False

  configuration = json.load(open('configuration.json'))
  if configuration.has_key("mqtt-client") is False:
    configuration["mqtt-client"] = "FlowerPowerCloud-Mqtt"

  if configuration.has_key("mqtt-server") is False:
    configuration["mqtt-server"] = "127.0.0.1"

  if configuration.has_key("mqtt-port") is False:
    configuration["mqtt-port"] = 1883

  if configuration.has_key("mqtt-prefix") is False:
    configuration["mqtt-prefix"] = "flower"

  print "Configuration:"
  print "Cloud API Id:  ", credentials["client_id"]
  print "Cloud Username:", credentials["username"]

  print "MQTT Client:   ", configuration["mqtt-client"]
  print "MQTT Server:   ", configuration["mqtt-server"]
  print "MQTT Port:     ", configuration["mqtt-port"]
  print "MQTT Prefix   :", configuration["mqtt-prefix"]

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

        broadcastMqtt(
          configuration["mqtt-client"], 
          configuration["mqtt-server"], 
          configuration["mqtt-port"], 
          configuration["mqtt-prefix"], 
          sensorId + "/name",
          json.dumps(flower))

      cloud.getGarden(None, getGardenCallback)

  def getGardenCallback(self, err, res):
    if err:
     print err
    else:
      for location in res["locations"]:
        #print json.dumps(location, indent=2, sort_keys=True)

#{
#  "air_temperature": {
#    "gauge_values": {
#      "current_value": 23.4954096595684,
#      "max_threshold": 40.0,
#      "min_threshold": 10.0
#    },
#    "instruction_key": "air_temperature_good",
#    "next_analysis_datetime_utc": null,
#    "status_key": "status_ok"
#  },
#  "battery": {
#    "gauge_values": {
#      "current_value": 60,
#      "max_threshold": 100,
#      "min_threshold": 0
#    }
#  },
#  "fertilizer": {
#    "gauge_values": {
#      "current_value": 0.25157780702289,
#      "max_threshold": 5.0,
#      "min_threshold": 0.5
#    },
#    "instruction_key": "fertilizer_too_low",
#    "next_analysis_datetime_utc": null,
#    "status_key": "status_ok"
#  },
#  "first_sample_utc": "2017-10-22T16:24:08Z",
#  "global_validity_datetime_utc": "2017-11-20T11:53:04Z",
#  "growth_day": false,
#  "last_sample_upload": "2017-11-18T12:04:46Z",
#  "last_sample_utc": "2017-11-18T11:53:04Z",
#  "light": {
#    "gauge_values": {
#      "current_value": 0.263714194989064,
#      "max_threshold": 20.0,
#      "min_threshold": 5.0
#    },
#    "instruction_key": "light_too_low",
#    "next_analysis_datetime_utc": null,
#    "status_key": "status_ok"
#  },
#  "location_identifier": "Aqca3ixdRD1508688251211",
#  "processing_uploads": false,
#  "sensor": {
#    "current_history_index": 25612,
#    "firmware_update": {
#      "firmware_upgrade_available": false
#    },
#    "firmware_version": "2016-09-14_hawaii-2.0.3_hardware-config-MP",
#    "sensor_identifier": "Flower power 8493",
#    "sensor_type": "flower-power"
#  },
#  "status_creation_datetime_utc": "2017-11-18T12:04:45Z",
#  "total_sample_count": 2575,
#  "user_sharing": {
#    "first_all_green": {
#      "sharing_status": "never_remind"
#    }
#  },
#  "watering": {
#    "automatic_watering": {
#      "done_action_datetime_utc": null,
#      "full_autonomy_days": null,
#      "gauge_values": {
#        "current_value": 0,
#        "max_threshold": 100,
#        "min_threshold": 0
#      },
#      "instruction_key": "automatic_watering_off",
#      "last_watering_datetime_utc": null,
#      "next_watering_datetime_utc": null,
#      "predicted_action_datetime_utc": null,
#      "status_key": "status_ok"
#    },
#    "instruction_key": "soil_moisture_good",
#    "soil_moisture": {
#      "gauge_values": {
#        "current_value": 25.9364528656006,
#        "max_threshold": null,
#        "min_threshold": 35.0
#      },
#      "instruction_key": "soil_moisture_too_low",
#      "predicted_action_datetime_utc": null,
#      "predicted_action_vwc_value": null,
#      "status_key": "status_critical"
#    },
#    "status_key": "status_ok"
#  }
#},


        flower = {}
        flower["sensor_name"] = location["sensor"]["sensor_identifier"]
        sensorId = flower["sensor_name"][-4:].lower()

        flower["battery"] = location["battery"]["gauge_values"]["current_value"]

        flower["air_temperature"] = location["air_temperature"]["gauge_values"]["current_value"]
        flower["air_temperature_status"] = location["air_temperature"]["instruction_key"]

        flower["fertilizer"] = location["fertilizer"]["gauge_values"]["current_value"]
        flower["fertilizer_status"] = location["fertilizer"]["instruction_key"]

        flower["light"] = location["light"]["gauge_values"]["current_value"]
        flower["light_status"] = location["light"]["instruction_key"]

        flower["watering"] = location["watering"]["soil_moisture"]["gauge_values"]["current_value"]
        flower["watering_status"] = location["watering"]["soil_moisture"]["instruction_key"]

        flower["last_utc"] = location["last_sample_utc"]

        broadcastMqtt(
          configuration["mqtt-client"], 
          configuration["mqtt-server"], 
          configuration["mqtt-port"], 
          configuration["mqtt-prefix"], 
          sensorId + "/update",
          json.dumps(flower))

  cloud.login(credentials, loginCallback)

if __name__ == "__main__":
  main(sys.argv)