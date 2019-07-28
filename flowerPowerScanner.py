
from bluepy.btle import UUID, Scanner, BTLEException

from flowerPower import FlowerPower
from flowerPower import SCAN_UUIDS


class DeviceInformation:
  localName = ""
  flags = 0
  manufacturer = ""
  addr = ""
  rssi = 0.0
  uuid = None


class FlowerPowerScanner:

  def __init__(self):
    self.scanner = Scanner()

  def _discover(self, duration=1):
    print "Scanner: discover"
    devices = self.scanner.scan(duration)
    if devices is None:
      print "Scanner: No devices found"
      return None

    flowerPowerDevices = []
    for device in devices:
      #print device.getScanData()

      deviceInformation = DeviceInformation()
      deviceInformation.localName    = device.getValueText(9) #Complete Local Name

      flags        = device.getValueText(1) #Flags
      if flags is not None:
        deviceInformation.flags        = int(flags, 16)

      deviceInformation.manufacturer = device.getValueText(255) #Manufacture

      deviceInformation.addr         = device.addr
      deviceInformation.rssi         = device.rssi

      uuid = device.getValueText(6) #Incomplete 128b Services
      if uuid is not None:
        #uuid = "".join(reversed([uuid[i:i+2] for i in range(0, len(uuid), 2)]))
        deviceInformation.uuid       = UUID(uuid)

        if deviceInformation.localName is None:
          deviceInformation.localName = 'Flower power {}'.format(uuid[0:4])

      if deviceInformation.uuid is not None:

        print "Found", deviceInformation.localName, deviceInformation.uuid
        print SCAN_UUIDS[0]

        if deviceInformation.uuid in SCAN_UUIDS:
          alreadyAdded = False
          #for flower in flowerPowerDevices:
          #  if deviceInformation.localName == flower.name:
          #    alreadyAdded = True
          #    break

          if alreadyAdded is False:
            flower = FlowerPower(deviceInformation)

            print "Scanner: Found Flower:", flower
            flowerPowerDevices.append(flower)

    if len(flowerPowerDevices) == 0:
      flowerPowerDevices = None

    return flowerPowerDevices

  def discover(self):
    devices = self._discover(1)
    if devices is None:
      return None

    return devices[0]

  def discoverAll(self):
    devices = self._discover(20)
    if devices is None:
      return None

    return devices
