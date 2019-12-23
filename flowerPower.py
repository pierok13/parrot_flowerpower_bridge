import binascii
import struct
import time
import math
import os

from bluepy.btle import UUID, Peripheral, Scanner, DefaultDelegate, BTLEException

GAP_SERVICE_UUID                        = UUID(0x1800)
GAP_NAME_UUID                           = UUID(0x2A00)
GAP_APPEARANCE_UUID                     = UUID(0x2A01)

#Device Information Service
GAP_SYSTEM_ID_UUID                      = UUID(0x2A23)
GAP_SERIAL_NUMBER_UUID                  = UUID(0x2A25)
GAP_FIRMWARE_REVISION_UUID              = UUID(0x2A26)
GAP_HARDWARE_UUID                       = UUID(0x2A27)
GAP_MANUFACTURE_NAME_UUID               = UUID(0x2A29)

#Battery Service
GAP_BATTERY_LEVEL_SERVICE_UUID          = UUID(0x2A19)

LIVE_SERVICE_UUID                       = UUID('39e1fa0084a811e2afba0002a5d5c51b')
SUNLIGHT_UUID                           = UUID('39e1fa0184a811e2afba0002a5d5c51b')
SOIL_EC_UUID                            = UUID('39e1fa0284a811e2afba0002a5d5c51b')
SOIL_TEMPERATURE_UUID                   = UUID('39e1fa0384a811e2afba0002a5d5c51b')
AIR_TEMPERATURE_UUID                    = UUID('39e1fa0484a811e2afba0002a5d5c51b')
SOIL_MOISTURE_UUID                      = UUID('39e1fa0584a811e2afba0002a5d5c51b')
LIVE_MODE_PERIOD_UUID                   = UUID('39e1fa0684a811e2afba0002a5d5c51b')
LED_UUID                                = UUID('39e1fa0784a811e2afba0002a5d5c51b')
LAST_MOVE_DATE_UUID                     = UUID('39e1fa0884a811e2afba0002a5d5c51b')
CALIBRATED_SOIL_MOISTURE_UUID           = UUID('39e1fa0984a811e2afba0002a5d5c51b')
CALIBRATED_AIR_TEMPERATURE_UUID         = UUID('39e1fa0a84a811e2afba0002a5d5c51b')
CALIBRATED_DLI_UUID                     = UUID('39e1fa0b84a811e2afba0002a5d5c51b')
CALIBRATED_EA_UUID                      = UUID('39e1fa0c84a811e2afba0002a5d5c51b')
CALIBRATED_ECB_UUID                     = UUID('39e1fa0d84a811e2afba0002a5d5c51b')
CALIBRATED_EC_POROUS_UUID               = UUID('39e1fa0e84a811e2afba0002a5d5c51b')

UPLOAD_SERVICE_UUID                     = UUID('39e1fb0084a811e2afba0002a5d5c51b')
UPLOAD_TX_BUFFER_UUID                   = UUID('39e1fb0184a811e2afba0002a5d5c51b')
UPLOAD_TX_STATUS_UUID                   = UUID('39e1fb0284a811e2afba0002a5d5c51b')
UPLOAD_RX_STATUS_UUID                   = UUID('39e1fb0384a811e2afba0002a5d5c51b')

HISTORY_SERVICE_UUID                    = UUID('39e1fc0084a811e2afba0002a5d5c51b')
HISTORY_NB_ENTRIES_UUID                 = UUID('39e1fc0184a811e2afba0002a5d5c51b')
HISTORY_LASTENTRY_IDX_UUID              = UUID('39e1fc0284a811e2afba0002a5d5c51b')
HISTORY_TRANSFER_START_IDX_UUID         = UUID('39e1fc0384a811e2afba0002a5d5c51b')
HISTORY_CURRENT_SESSION_ID_UUID         = UUID('39e1fc0484a811e2afba0002a5d5c51b')
HISTORY_CURRENT_SESSION_START_IDX_UUID  = UUID('39e1fc0584a811e2afba0002a5d5c51b')
HISTORY_CURRENT_SESSION_PERIOD_UUID     = UUID('39e1fc0684a811e2afba0002a5d5c51b')

CLOCK_SERVICE_UUID                      = UUID('39e1fd0084a811e2afba0002a5d5c51b')
CLOCK_CURRENT_TIME_UUID                 = UUID('39e1fd0184a811e2afba0002a5d5c51b')
CLOCK_UTC_SINCE_EPOCH_UUID              = UUID('39e1fd0284a811e2afba0002a5d5c51b')

PLANT_DOCTOR_SERVICE_UUID               = UUID('39e1fd8084a811e2afba0002a5d5c51b')
PLANT_DOCTOR_CONFIG_ID_UUID             = UUID('39e1fd8184a811e2afba0002a5d5c51b')
PLANT_DOCTOR_DRY_N_UUID                 = UUID('39e1fd8284a811e2afba0002a5d5c51b')
PLANT_DOCTOR_DRY_WVC_UUID               = UUID('39e1fd8384a811e2afba0002a5d5c51b')
PLANT_DOCTOR_WET_N_UUID                 = UUID('39e1fd8484a811e2afba0002a5d5c51b')
PLANT_DOCTOR_WET_VWC_UUID               = UUID('39e1fd8584a811e2afba0002a5d5c51b')
PLANT_DOCTOR_STATUS_FLAGS_UUID          = UUID('39e1fd8684a811e2afba0002a5d5c51b')

CONFIGURATION_SERVICE_UUID              = UUID('39e1fe0084a811e2afba0002a5d5c51b')
CALIBRATION_DATA_UUID                   = UUID('39e1fe0184a811e2afba0002a5d5c51b')
FRIENDLY_NAME_UUID                      = UUID('39e1fe0384a811e2afba0002a5d5c51b')
COLOR_UUID                              = UUID('39e1fe0484a811e2afba0002a5d5c51b')

SCAN_UUIDS = [LIVE_SERVICE_UUID]

STRUCT_UInt8LE = 'B'
STRUCT_UInt16LE = 'H'
STRUCT_UInt32LE = 'I'
STRUCT_Float = 'f'
STRUCT_Bytes = 'B'
STRUCT_String = 's'



##################################################
class FlowerPower:

  class Flags:
    hasEntry = False
    hasMoved = False
    isStarting = False

  class RxStatusEnum:
    STANDBY   = 0
    RECEIVING = 1
    ACK       = 2
    NACK      = 3
    CANCEL    = 4
    ERROR     = 5

  class TxStatusEnum:
    IDLE        = 0
    TRANSFERING = 1
    WAITING_ACK = 2

  peripheral = None
  name = None
  flags = None
  uuid = None

  currentIdx = 0
  buffers = {}
  rxStatus = RxStatusEnum.STANDBY
  txStatus = TxStatusEnum.IDLE
  historyFile = None

  def __init__(self, deviceInformation):
    self._deviceInformation = deviceInformation
    self.uuid = deviceInformation.uuid
    self.name = deviceInformation.localName
    
    self.flags = FlowerPower.Flags()
    if (deviceInformation.flags & 1) == 1:
      self.flags.hasEntry = True

    if (deviceInformation.flags & 2) == 2:
      self.flags.hasMoved = True

    if (deviceInformation.flags & 4) == 4:
      self.flags.isStarting = True

  def connectAndSetup(self):
    print "Connecting to", self.uuid, self._deviceInformation.addr
    for i in range(0,10):
      try:
        ADDR_TYPE_PUBLIC = "public"
        self.peripheral = Peripheral(self._deviceInformation.addr, ADDR_TYPE_PUBLIC)
        return True
      except BTLEException, ex:
        if i == 10:
          print "BTLE Exception", ex
        continue

    return False

  def __str__(self):
    str = '{{addr: "{}", uuid: "{}", name: "{}"}}'.format(self._deviceInformation.addr, self.uuid, self.name)
    return str

################

  def readCharacteristic(self, serviceUuid, characteristicUuid):
    try:
      ch = self.peripheral.getCharacteristics(uuid=characteristicUuid)[0]
      if (ch.supportsRead()):
        val = ch.read()
        return val
    except BTLEException, ex:
      print "BTLE Exception", ex

    print "Error on readCharacteristic"
    return None

  def readDataCharacteristic(self, serviceUuid, characteristicUuid):
    try:
      ch = self.peripheral.getCharacteristics(uuid=characteristicUuid)[0]
      if (ch.supportsRead()):
        val = ch.read()
        val = binascii.b2a_hex(val)
        #print val
        val = binascii.unhexlify(val)
        #print val
        return val
    except BTLEException, ex:
      print "BTLE Exception", ex

    print "Error on readCharacteristic"
    return None

  def writeDataCharacteristic(self, serviceUuid, characteristicUuid, value):
    ch = self.peripheral.getCharacteristics(uuid=characteristicUuid)[0]
    #val = struct.pack(STRUCT_Bytes, value)
    ch.write(value)
    return None

  def readStringCharacteristic(self, serviceUuid, characteristicUuid):
    try:
      ch = self.peripheral.getCharacteristics(uuid=characteristicUuid)[0]
      if (ch.supportsRead()):
        val = ch.read()
        val = val[:val.index('\0')]
        #print "String", [hex(ord(c)) for c in val]
        return val
    except BTLEException, ex:
      print "BTLE Exception", ex

    print "Error on readCharacteristic"
    return None


  def readStringCharacteristic2(self, serviceUuid, characteristicUuid):
    val = self.readDataCharacteristic(serviceUuid, characteristicUuid)
    if val is None:
      print "Error on readCharacteristic", characteristicUuid
      return None

    val = struct.unpack(STRUCT_String, val)[0]
    print "readStringCharacteristic", characteristicUuid, val

    return val

  def writeStringCharacteristic(self, serviceUuid, characteristicUuid, value):
    #ch = _peripheral.getCharacteristics(uuid=uuid)[0]
    #val = struct.pack(STRUCT_Bytes, value)
    #ch.write(val)
    return None

  def readFloatLECharacteristic(self, serviceUuid, characteristicUuid):
    val = self.readDataCharacteristic(serviceUuid, characteristicUuid)
    if val is None:
      print "Error on readCharacteristic", characteristicUuid
      return None

    val = struct.unpack(STRUCT_Float, val)[0]
    print "readFloatLECharacteristic", characteristicUuid, val

    return val

################

  def readSystemId(self):
    systemId = self.readDataCharacteristic(None, GAP_SYSTEM_ID_UUID)
    if systemId is None:
      return "unknown"

    return systemId

  def readSerialNumber(self):
    serialNumber = self.readStringCharacteristic(None, GAP_SERIAL_NUMBER_UUID)
    if serialNumber is None:
      return "unknown"

    print serialNumber
    return serialNumber

  def readFirmwareRevision(self):
    firmwareRevision = self.readStringCharacteristic(None, GAP_FIRMWARE_REVISION_UUID)
    if firmwareRevision is None:
      return "unknown"

    return firmwareRevision

  def readHardwareRevision(self):
    hardware = self.readStringCharacteristic(None, GAP_HARDWARE_UUID)
    if hardware is None:
      return "unknown"

    return hardware

  def readManufacturerName(self):
    manufactureName = self.readStringCharacteristic(None, GAP_MANUFACTURE_NAME_UUID)
    if manufactureName is None:
      return "unknown"

    return manufactureName

  def readBatteryLevel(self):
    data = self.readCharacteristic(None, GAP_BATTERY_LEVEL_SERVICE_UUID)
    if data is None:
      return 0

    batteryLevel = ord(data)

    return batteryLevel

################

  def readFriendlyName(self):
    friendlyName = self.readStringCharacteristic(CONFIGURATION_SERVICE_UUID, FRIENDLY_NAME_UUID)
    if friendlyName is None:
      return 'Unknown'

    return friendlyName

  def writeFriendlyName(self, friendlyName):
    return None

  def readColor(self):
    data = self.readDataCharacteristic(CONFIGURATION_SERVICE_UUID, COLOR_UUID)
    if data is None:
      return 'unknown'

    colorCode = struct.unpack(STRUCT_UInt16LE, data)[0]
    COLOR_CODE_MAPPER = {
      4: 'brown',
      6: 'green',
      7: 'blue'
    }
    if COLOR_CODE_MAPPER.has_key(colorCode):
      color = COLOR_CODE_MAPPER[colorCode]
    else:
      color = 'unknown';

    return color

  def convertSunlightData(self, data):
    rawValue = struct.unpack(STRUCT_UInt16LE, data)[0] * 1.0;

    sunlight = 0.08640000000000001 * (192773.17000000001 * math.pow(rawValue, -1.0606619))

    return sunlight

  def readSunlight(self):
    data = self.readDataCharacteristic(LIVE_SERVICE_UUID, SUNLIGHT_UUID)
    if data is None:
      return 0.0

    sunlight = self.convertSunlightData(data)
    return sunlight

  def convertSoilElectricalConductivityData(self, data):
    rawValue = struct.unpack(STRUCT_UInt16LE, data)[0] * 1.0

    # TODO: convert raw (0 - 1771) to 0 to 10 (mS/cm)
    soilElectricalConductivity = rawValue

    return soilElectricalConductivity

  def readSoilElectricalConductivity(self):
    data = self.readDataCharacteristic(LIVE_SERVICE_UUID, SOIL_EC_UUID)
    if data is None:
      return 0.0

    soilEC = self.convertSoilElectricalConductivityData(data)
    return soilEC

  def convertTemperatureData(self, data):
    rawValue = struct.unpack(STRUCT_UInt16LE, data)[0] * 1.0

    temperature = 0.00000003044 * math.pow(rawValue, 3.0) - 0.00008038 * math.pow(rawValue, 2.0) + rawValue * 0.1149 - 30.449999999999999

    if temperature < -10.0:
      temperature = -10.0
    elif temperature > 55.0:
      temperature = 55.0

    return temperature

  def readSoilTemperature(self):
    data = self.readDataCharacteristic(LIVE_SERVICE_UUID, SOIL_TEMPERATURE_UUID)
    if data is None:
      return 0.0

    temperature = self.convertTemperatureData(data)
    return temperature

  def readAirTemperature(self):
    data = self.readDataCharacteristic(LIVE_SERVICE_UUID, AIR_TEMPERATURE_UUID)
    if data is None:
      return 0.0

    temperature = self.convertTemperatureData(data)
    return temperature

  def convertSoilMoistureData(self, data):
    rawValue = struct.unpack(STRUCT_UInt16LE, data)[0] * 1.0

    soilMoisture = 11.4293 + (0.0000000010698 * math.pow(rawValue, 4.0) - 0.00000152538 * math.pow(rawValue, 3.0) +  0.000866976 * math.pow(rawValue, 2.0) - 0.169422 * rawValue)
    soilMoisture = 100.0 * (0.0000045 * math.pow(soilMoisture, 3.0) - 0.00055 * math.pow(soilMoisture, 2.0) + 0.0292 * soilMoisture - 0.053);

    if soilMoisture < 0.0:
      soilMoisture = 0.0
    elif soilMoisture > 60.0:
      soilMoisture = 60.0

    return soilMoisture

  def readSoilMoisture(self):
    data = self.readDataCharacteristic(LIVE_SERVICE_UUID, SOIL_MOISTURE_UUID)
    if data is None:
      return 0.0

    soilMoisture = self.convertSoilMoistureData(data)
    return soilMoisture

  def readCalibratedSoilMoisture(self):
    calibratedSoilMoisture = self.readFloatLECharacteristic(LIVE_SERVICE_UUID, CALIBRATED_SOIL_MOISTURE_UUID)
    if calibratedSoilMoisture is None:
      return 0.0

    return calibratedSoilMoisture

  def readCalibratedAirTemperature(self):
    calibratedAirTemperature = self.readFloatLECharacteristic(LIVE_SERVICE_UUID, CALIBRATED_AIR_TEMPERATURE_UUID)
    if calibratedAirTemperature is None:
      return 0.0

    return calibratedAirTemperature

  def readCalibratedSunlight(self):
    calibratedSunlight = self.readFloatLECharacteristic(LIVE_SERVICE_UUID, CALIBRATED_DLI_UUID)
    if calibratedSunlight is None:
      return 0.0

    return calibratedSunlight

  def readCalibratedEa(self):
    calibratedEa = self.readFloatLECharacteristic(LIVE_SERVICE_UUID, CALIBRATED_EA_UUID)
    if calibratedEa is None:
      return 0.0

    return calibratedEa

  def readCalibratedEcb(self):
    calibratedEcb = self.readFloatLECharacteristic(LIVE_SERVICE_UUID, CALIBRATED_ECB_UUID)
    if calibratedEcb is None:
      return 0.0

    return calibratedEcb

  def readCalibratedEcPorous(self):
    calibratedEcPorous = self.readFloatLECharacteristic(LIVE_SERVICE_UUID, CALIBRATED_EC_POROUS_UUID)
    if calibratedEcPorous is None:
      return 0.0

    return calibratedEcPorous

  def getHistoryNbEntries(self):
    #self.readData(HISTORY_SERVICE_UUID, HISTORY_NB_ENTRIES_UUID, "readUInt16LE");
    data = self.readDataCharacteristic(HISTORY_SERVICE_UUID, HISTORY_NB_ENTRIES_UUID)
    if data is None:
      return 0.0

    return struct.unpack(STRUCT_UInt16LE, data)[0] 

  def getHistoryLastEntryIdx(self):
    # self.readData(HISTORY_SERVICE_UUID,HISTORY_LASTENTRY_IDX_UUID, "readUInt32LE");
    data = self.readDataCharacteristic(HISTORY_SERVICE_UUID, HISTORY_LASTENTRY_IDX_UUID)
    if data is None:
      return 0.0

    return struct.unpack(STRUCT_UInt32LE, data)[0] 

  def getHistoryCurrentSessionID(self):
    # self.readData(HISTORY_SERVICE_UUID, HISTORY_CURRENT_SESSION_ID_UUID, "readUInt16LE");
    data = self.readDataCharacteristic(HISTORY_SERVICE_UUID, HISTORY_CURRENT_SESSION_ID_UUID)
    if data is None:
      return 0.0

    return struct.unpack(STRUCT_UInt16LE, data)[0] 

  def getHistoryCurrentSessionStartIdx(self):
    # self.readData(HISTORY_SERVICE_UUID, HISTORY_CURRENT_SESSION_START_IDX_UUID, "readUInt32LE");
    data = self.readDataCharacteristic(HISTORY_SERVICE_UUID, HISTORY_CURRENT_SESSION_START_IDX_UUID)
    if data is None:
      return 0.0

    return struct.unpack(STRUCT_UInt32LE, data)[0] 

  def getHistoryCurrentSessionPeriod(self):
    # self.readData(HISTORY_SERVICE_UUID, HISTORY_CURRENT_SESSION_PERIOD_UUID, "readUInt16LE");
    data = self.readDataCharacteristic(HISTORY_SERVICE_UUID, HISTORY_CURRENT_SESSION_PERIOD_UUID)
    if data is None:
      return 0.0

    return struct.unpack(STRUCT_UInt16LE, data)[0] 

  def writeTxStartIdx(self, startIdx):
    startIdxBuff = struct.pack(STRUCT_UInt32LE, startIdx)

    self.writeDataCharacteristic(HISTORY_SERVICE_UUID, HISTORY_TRANSFER_START_IDX_UUID, startIdxBuff);

  def getStartupTime(self):
    #data = self.readData(CLOCK_SERVICE_UUID, CLOCK_CURRENT_TIME_UUID, "readUInt32LE")
    data = self.readDataCharacteristic(CLOCK_SERVICE_UUID, CLOCK_CURRENT_TIME_UUID)
    if data is None:
      return 0.0

    value = struct.unpack(STRUCT_UInt32LE, data)[0] 

    from datetime import datetime, timedelta
    startupTime = datetime.now()
    startupTime = startupTime -  timedelta(seconds=value)

    return startupTime

  class StatusFlags:
    soilDry = False
    soilWet = False

    def __init__(self, value):
      print "StatusFlags", value

      if (value & 1) == 1:
        self.soilDry = True
      if (value & 2) == 2:
        self.soilWet = True

  def getStatusFlags(self):
    data = self.readDataCharacteristic(PLANT_DOCTOR_SERVICE_UUID, PLANT_DOCTOR_STATUS_FLAGS_UUID)

    if data is None:
      return FlowerPower.StatusFlags(0)

    return FlowerPower.StatusFlags(struct.unpack(STRUCT_UInt8LE, data)[0])

  def getHistory(self, startIdx):
    self.writeTxStartIdx(startIdx)

    upload = FlowerPower.Upload(self)
    self.peripheral.withDelegate(upload)

    self.notifyTxStatus()
    self.notifyTxBuffer()
    self.writeRxStatus(FlowerPower.RxStatusEnum.RECEIVING)

    self.transmissionInProgress = True
    while self.transmissionInProgress:
      notified = self.peripheral.waitForNotifications(10)
      if notified:
        #print "Notification"
        pass

    self.peripheral.withDelegate(None)

    return self.historyFile.encode("base64")

  def ledPulse(self):
    self.writeDataCharacteristic(LIVE_SERVICE_UUID, LED_UUID, {0x01})

  def ledOff(self):
    self.writeDataCharacteristic(LIVE_SERVICE_UUID, LED_UUID, {0x00})

###################

  def notifyCharacteristic(self, serviceUuid, characteristicUuid, enable):
    char = self.peripheral.getCharacteristics(uuid=characteristicUuid)[0]
    #ccc_desc = char.getDescriptors(forUUID=0x2902)[0]
    char_descr = char.getDescriptors(forUUID=0x2902)[0]

    if enable:
      #ccc_desc.write(b"\x01")
      char_descr.write(struct.pack('<bb', 0x01, 0x00), True)
    else:
      #ccc_desc.write(b"\x00")
      char_descr.write(struct.pack('<bb', 0x00, 0x00), True)

    return char.getHandle() 

  def onWaitingAck(self):
    print "onWaitingAck"

    success = True
    #for idx in range(self.currentIdx, self.currentIdx+128):
    #  if idx >= self.nbTotalBuffers:
    #    break

    #  if idx > 0:
    #    #if (!this.buffers.hasOwnProperty(idx)){
    #    success = False;
    #    break;

    if success is True:
      self.currentIdx += 128;

      print "currentIdx", self.currentIdx
      print "nbTotalBuffers", self.nbTotalBuffers

      if self.currentIdx >= self.nbTotalBuffers:

        #print self.buffers
        self.historyFile = ''
        for buffer in self.buffers:
          if buffer is not None:
            self.historyFile = self.historyFile + buffer
        #print self.historyFile

        self.writeRxStatus(FlowerPower.RxStatusEnum.ACK)
        self.unnotifyTxStatus()
        self.unnotifyTxBuffer()
        self.writeRxStatus(FlowerPower.RxStatusEnum.STANDBY)

      else:
        self.writeRxStatus(FlowerPower.RxStatusEnum.ACK)

    else:
      self.writeRxStatus(FlowerPower.RxStatusEnum.NACK)

  def onTxStatusChange(self, data):
    print "onTxStatusChange", [hex(ord(c)) for c in data]
    self.txStatus = struct.unpack('<B', data)[0]
    print "txStatus", self.txStatus

    if self.txStatus == FlowerPower.TxStatusEnum.WAITING_ACK:
      self.onWaitingAck()

    if self.txStatus == FlowerPower.TxStatusEnum.IDLE:
      if self.historyFile != None: # and type(this.historyFile) != 'undefined':
        #this.finishCallback(None, self.historyFile.toString('base64'));
        #return
        print "Transfer finished"
      else:
        #this.finishCallback(Error("Transfer failed", None));
        print "Transfer failed"

      self.transmissionInProgress = False

  def setFileLength(self, fileLength):
    print "setFileLength", fileLength
    self.fileLength = fileLength
    self.nbTotalBuffers = int(math.ceil(self.fileLength / self.bufferLength) + 1)

    self.buffers = [None] * (self.nbTotalBuffers + 1)

    print "setFileLength", self.fileLength, self.nbTotalBuffers

  def readFirstBuffer(self, buffer):
    print "readFirstBuffer", [hex(ord(c)) for c in buffer]
    self.bufferLength = len(buffer)

    fileLength = struct.unpack('<I', buffer[0:4])[0]
    self.setFileLength(fileLength)


  def onTxBufferReceived(self, data):
    print "onTxBufferReceived", [hex(ord(c)) for c in data]
    buffer = FlowerPower.UploadBuffer(data)
    self.buffers[buffer.idx] = buffer.data
    if buffer.idx == 0:
      self.readFirstBuffer(buffer.data)

  def notifyTxStatus(self):
    print "notifyTxStatus"
    self.notifyCharacteristic(UPLOAD_SERVICE_UUID, UPLOAD_TX_STATUS_UUID, True)

  def notifyTxBuffer(self):
    print "notifyTxBuffer"
    self.notifyCharacteristic(UPLOAD_SERVICE_UUID, UPLOAD_TX_BUFFER_UUID, True)

  def unnotifyTxStatus(self):
    print "unnotifyTxStatus"
    self.notifyCharacteristic(UPLOAD_SERVICE_UUID, UPLOAD_TX_STATUS_UUID, False)

  def unnotifyTxBuffer(self):
    print "unnotifyTxBuffer"
    self.notifyCharacteristic(UPLOAD_SERVICE_UUID, UPLOAD_TX_BUFFER_UUID, False)

  def writeRxStatus(self, rxStatus):
    print "writeRxStatus", rxStatus
    rxStatusBuff = struct.pack(STRUCT_UInt8LE, rxStatus)

    self.writeDataCharacteristic(UPLOAD_SERVICE_UUID, UPLOAD_RX_STATUS_UUID, rxStatusBuff);

###################

  class UploadBuffer:
    def __init__(self, buffer):
      self.idx = struct.unpack('<H', buffer[0:2])[0]
      dataLength = len(buffer) - 2
      #self.data = struct.unpack('<' + str(dataLength) + 'B', buffer[2:])
      self.data =  buffer[2:]

  class Upload(DefaultDelegate):
    def __init__(self, fp):
      DefaultDelegate.__init__(self)
      self.fp = fp

    def handleNotification(self, cHandle, data):
      #print "handleNotification", cHandle, data
      if cHandle == 109:
        self.fp.onTxStatusChange(data)
      elif cHandle == 105:
        self.fp.onTxBufferReceived(data)
