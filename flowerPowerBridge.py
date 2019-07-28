
import sys
import json
from datetime import datetime
import time

from flowerPower import FlowerPower
from flowerPowerScanner import FlowerPowerScanner

from flowerPowerCloud import FlowerPowerCloud

class DataBLE:
  startupTime = None
  serialNumber = None
  firmwareVersion = None
  hardwareVersion = None
  friendlyName = None
  historyNbEntries = None
  historyLastEntryIndex = None
  historyCurrentSessionId = None
  historyCurrentSessionPeriod = None
  historyCurrentSessionStartIdx = None
  historyBase64 = None

  calibratedSoilMoisture = None
  statusFlags = None

def getSamples(device, cloudUser, dataBLE):

  dataBLE.startupTime = device.getStartupTime()
  dataBLE.serialNumber = device.readSerialNumber()
  dataBLE.firmwareVersion = device.readFirmwareRevision()
  dataBLE.hardwareVersion = device.readHardwareRevision()

  dataBLE.friendlyName = device.readFriendlyName()

  dataBLE.historyNbEntries = device.getHistoryNbEntries()
  dataBLE.historyLastEntryIndex = device.getHistoryLastEntryIdx()

  dataBLE.historyCurrentSessionId = device.getHistoryCurrentSessionID()
  dataBLE.historyCurrentSessionPeriod = device.getHistoryCurrentSessionPeriod()
  dataBLE.historyCurrentSessionStartIdx = device.getHistoryCurrentSessionStartIdx()


  index = 0
  for location in cloudUser["locations"]:
    if location["sensor"]["sensor_identifier"] == dataBLE.friendlyName:
      index = location["sensor"]["current_history_index"]


  firstEntryIndex = dataBLE.historyLastEntryIndex - dataBLE.historyNbEntries + 1
  if index >= firstEntryIndex:
    startIndex = index
  else:
    startIndex = firstEntryIndex

  if '\u0000' in dataBLE.hardwareVersion:
    dataBLE.hardwareVersion = dataBLE.hardwareVersion[dataBLE.hardwareVersion.find('\u0000'):]

  if '\u0000' in dataBLE.firmwareVersion:
    dataBLE.firmwareVersion = dataBLE.firmwareVersion[firmwareVersion.find('\u0000'):]

  print "startupTime", dataBLE.startupTime
  print "serialNumber", dataBLE.serialNumber

  print "hardwareVersion", dataBLE.hardwareVersion
  print "firmwareVersion", dataBLE.firmwareVersion
  print "friendlyName", dataBLE.friendlyName

  print "historyNbEntries", dataBLE.historyNbEntries
  print "historyLastEntryIndex", dataBLE.historyLastEntryIndex

  print "historyCurrentSessionId", dataBLE.historyCurrentSessionId
  print "historyCurrentSessionPeriod", dataBLE.historyCurrentSessionPeriod
  print "historyCurrentSessionStartIdx", dataBLE.historyCurrentSessionStartIdx

  print "cloudIndex", index
  print "startIndex", startIndex

  if startIndex > dataBLE.historyLastEntryIndex:
    print('No update required')
    return

  dataBLE.historyBase64 = device.getHistory(startIndex)

  print "History", dataBLE.historyBase64

  return dataBLE

def getStatusWatering(device, cloudUser, dataBLE):

  dataBLE.calibratedSoilMoisture = device.readCalibratedSoilMoisture()
  dataBLE.statusFlags = device.getStatusFlags()

  print "calibratedSoilMoisture", dataBLE.calibratedSoilMoisture
  print "statusFlags.soilDry", dataBLE.statusFlags.soilDry
  print "statusFlags.soilWet", dataBLE.statusFlags.soilWet

  return dataBLE

def syncSamples(cloud, cloudUser, dataBLE, name):
  param = {}
  session = {}
  uploads = {}

  #sensorName = ""
  #for idx in range(0, len(cloudUser["locations"])):
  #  location = cloudUser["locations"][idx]

  #  print location["sensor"]["sensor_identifier"], name
  #  if location["sensor"]["sensor_identifier"] == name:
  #    sensorName = str(idx)
  #    break

  now = datetime.utcnow()

  print "Name", name, "FriendlyName", dataBLE.friendlyName

  session["sensor_serial"]                = dataBLE.friendlyName #dataBLE.serialNumber
  session["sensor_startup_timestamp_utc"] = dataBLE.startupTime.strftime("%Y-%m-%dT%H:%M:%SZ") #2017-10-22T15:50:50Z
  session["session_id"]                   = dataBLE.historyCurrentSessionId
  session["session_start_index"]          = dataBLE.historyCurrentSessionStartIdx
  session["sample_measure_period"]        = dataBLE.historyCurrentSessionPeriod
  param["session_histories"] = [session]

  uploads["sensor_serial"]                = dataBLE.friendlyName #dataBLE.serialNumber
  uploads["upload_timestamp_utc"]         = now.strftime("%Y-%m-%dT%H:%M:%SZ") #2017-11-13T17:44:11Z
  uploads["buffer_base64"]                = dataBLE.historyBase64
  uploads["app_version"]                  = "4.6.2_Android";
  uploads["sensor_fw_version"]            = dataBLE.firmwareVersion
  uploads["sensor_hw_identifier"]         = dataBLE.hardwareVersion
  param["uploads"] = [uploads]

  tmzOffset = 0 - int(time.timezone / 60.0)
  param["tmz_offset"] = tmzOffset
  param["client_datetime_utc"] = now.strftime("%Y-%m-%dT%H:%M:%SZ")
  param["user_config_version"] = cloudUser["user_config_version"]
  param["plant_science_database_identifier"] = "en_20170118_4.0.7";

#{
#  "session_histories": [{
#    "sensor_serial": "Flower power 934B",
#    "sensor_startup_timestamp_utc": "2017-10-22T15:50:50Z",
#    "session_id": 3,
#    "session_start_index": 23040,
#    "sample_measure_period": 900
#  }],
#  "uploads": [{
#    "sensor_serial": "Flower power 934B",
#    "latitude": 49.35037904,
#    "longitude": 11.15025194,
#    "upload_timestamp_utc": "2017-11-13T17:44:09Z",
#    "buffer_base64": "AwAAAgAdGZ0AAGJHAAMDhALf\/\/8BjwLLAncDXALx\/\/8BjwLMAngDXA==\n",
#    "app_version": "4.6.2_Android",
#    "sensor_fw_version": "2016-09-14_hawaii-2.0.3_hardware-config-MP",
#    "sensor_hw_identifier": "2013-07-26_hawaiiProduction-1.2_protoDV-bootloader"
#  }],
#  "tmz_offset": 60,
#  "client_datetime_utc": "2017-11-13T17:44:11Z",
#  "user_config_version": 53,
#  "plant_science_database_identifier": "en_20170118_4.0.7"
#}

  def getSendSamplesCallback(self, err, res):
    if err:
     print err
    else:
      print res

  cloud.sendSamples(param, getSendSamplesCallback)

def syncStatus(cloud, cloudUser, dataBLE, name):
  param = {}
  update_status = {}

  now = datetime.utcnow()

  print "Name", name, "FriendlyName", dataBLE.friendlyName

  sensorId = 0
  for idx in range(0, len(cloudUser["locations"])):
    location = cloudUser["locations"][idx]

    print location["sensor"]["sensor_identifier"], dataBLE.friendlyName
    if location["sensor"]["sensor_identifier"] == dataBLE.friendlyName:
      sensorId = idx
      break

  update_status['location_identifier'] = cloudUser["locations"][sensorId]["location_identifier"]
  update_status['status_creation_datetime_utc'] = now.strftime("%Y-%m-%dT%H:%M:%SZ") #2017-11-13T17:44:11Z

  watering = {
    'status_key': 'status_ok',
    'instruction_key': 'soil_moisture_good',
    'soil_moisture': {
      'status_key': 'status_ok',
      'instruction_key': 'soil_moisture_good',
      'current_vwc': 0
    },
    'automatic_watering': {
      'status_key': 'status_ok',
      'instruction_key': 'automatic_watering_off',
      'next_watering_datetime_utc': None,
      'full_autonomy_days': None,
      'predicted_action_datetime_utc': None,
      'current_water_level': 0
    }
  }

  watering['soil_moisture']['current_vwc'] = dataBLE.calibratedSoilMoisture

  if dataBLE.statusFlags.soilDry and not dataBLE.statusFlags.soilWet:
    watering['soil_moisture']['status_key'] = 'status_critical'
    watering['soil_moisture']['instruction_key'] = 'soil_moisture_too_low'

  if dataBLE.statusFlags.soilWet and not dataBLE.statusFlags.soilDry:
    watering['soil_moisture']['status_key'] = 'status_warning'
    watering['soil_moisture']['instruction_key'] = 'soil_moisture_too_high'

  update_status['watering'] = watering

  param['update_status'] = [update_status]

  param["client_datetime_utc"] = now.strftime("%Y-%m-%dT%H:%M:%SZ") #2017-11-13T17:44:11Z
  param["user_config_version"] = cloudUser["user_config_version"]

  def getSendGardenStatusCallback(self, err, res):
    if err:
     print err
    else:
      print res

  cloud.sendGardenStatus(param, getSendGardenStatusCallback)

def syncFlowerPower(cloud, cloudUser, dataBLE, name):
  syncStatus(cloud, cloudUser, dataBLE, name)
  syncSamples(cloud, cloudUser, dataBLE, name)

loggedIn = False
cloudUserConfig = None
cloudGarden = None


def main(argv):
  print "Starting"
  cloud = FlowerPowerCloud()

  credentials = json.load(open('credentials.json'))
  credentials['auto-refresh'] = False

  print "Configuration:"
  print "Cloud API Id:  ", credentials["client_id"]
  print "Cloud Username:", credentials["username"]

  import os
  os.environ['TZ'] = "Europe/Berlin"
  time.tzset()

  print("TZ", time.timezone / 3600.0)

  def loginCallback(self, err, res):
    if err:
     print err
    else:
      print "Head in the clouds :)", res
      global loggedIn
      loggedIn = True

  def getUserCallback(self, err, res):
    if err:
     print err
    else:
      global cloudUserConfig
      cloudUserConfig = res

      cloud.getGarden(None, getGardenCallback)

  def getGardenCallback(self, err, res):
    if err:
     print err
    else:
      global cloudGarden
      cloudGarden = res

      global cloudUser
      cloudUser = cloud.concatJson(cloudUserConfig, cloudGarden)

  print "Cloud Login"
  cloud.login(credentials, loginCallback)

  print "Flower discover All"
  scanner = FlowerPowerScanner()
  devices = scanner.discoverAll()

  print "Cloud get User Versions"
  cloud.getUserVersions(None, getUserCallback)

  if devices is not None:
    for device in devices:
      if device.connectAndSetup() is True:
        dataBLE = DataBLE()
        dataBLE = getStatusWatering(device, cloudUser, dataBLE)
        #exit(0)
        dataBLE = getSamples(device, cloudUser, dataBLE)

        syncFlowerPower(cloud, cloudUser, dataBLE, device.name)

        #exit(0)

if __name__ == "__main__":
  main(sys.argv)
