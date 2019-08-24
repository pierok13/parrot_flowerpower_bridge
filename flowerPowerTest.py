
import sys

from flowerPower import FlowerPower
from flowerPowerScanner import FlowerPowerScanner


def main(argv):
  deviceFilter = None

  print "Starting"
  print "-"*60

  if len(argv) > 1:
    deviceFilter = argv[1].upper()

  print "Filter", deviceFilter

  scanner = FlowerPowerScanner()
  devices = None
  if deviceFilter is not None:
    devices = scanner.discover(deviceFilter)
  else:
    devices = scanner.discoverAll()

  if devices is not None:
    for device in devices:
      if device.connectAndSetup() is True:
        #print "SystemId                 ", device.readSystemId()
        #print "SerialNumber             ", device.readSerialNumber()
        #print "FirmwareRevision         ", device.readFirmwareRevision()
        #print "HardwareRevision         ", device.readHardwareRevision()
        #print "ManufactureName          ", device.readManufacturerName()
        print "BatteryLevel             ", device.readBatteryLevel(), "%"
        print "FriendlyName             ", device.readFriendlyName()
        print "Color                    ", device.readColor()
        print "Sunlight                 ", device.readSunlight(), "mol/m^2/d"
        print "SoilElectricalConductivity", device.readSoilElectricalConductivity()
        print "SoilTemperature           ", device.readSoilTemperature(), "C"
        print "AirTemperature            ", device.readAirTemperature(), "C"
        print "SoilMoisture              ", device.readSoilMoisture(), "%"
        print "CalibratedSoilMoisture    ", device.readCalibratedSoilMoisture(), "%"
        print "CalibratedAirTemperature  ", device.readCalibratedAirTemperature(), "C"
        print "CalibratedSunlight        ", device.readCalibratedSunlight(), "mol/m^2/d"
        print "CalibratedEa              ", device.readCalibratedEa()
        print "CalibratedEcb             ", device.readCalibratedEcb(), "dS/m"
        print "CalibratedEcPorous        ", device.readCalibratedEcPorous(), "dS/m"

        print "HistoryNbEntries          ", device.getHistoryNbEntries()
        print "HistoryLastEntryIdx       ", device.getHistoryLastEntryIdx()
        print "HistoryCurrentSessionID   ", device.getHistoryCurrentSessionID()
        print "HistoryCurrentSessionStartIdx ", device.getHistoryCurrentSessionStartIdx()
        print "HistoryCurrentSessionPeriod   ", device.getHistoryCurrentSessionPeriod()

        print "StartupTime        ", device.getStartupTime()

        #device.ledPulse()
        #device.ledOff()
    exit(1)
  exit(0)

if __name__ == "__main__":
  main(sys.argv)