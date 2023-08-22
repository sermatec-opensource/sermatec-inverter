import logging
import asyncio
from . import protocol_parser
from .exceptions import *

_LOGGER = logging.getLogger(__name__)

class Sermatec:

    REQ_COMMANDS = {
        "systemInformation"   : bytes([0x98]),
        "batteryStatus"       : bytes([0x0a]),
        "gridPVStatus"        : bytes([0x0b]),
        "workingParameters"   : bytes([0x95]),
        "load"                : bytes([0x0d])
    }

    REQ_SIGNATURE           = bytes([0xfe, 0x55])
    REQ_APP_ADDRESS         = bytes([0x64])
    REQ_INVERTER_ADDRESS    = bytes([0x14])
    REQ_FOOTER              = bytes([0xae])

    def __init__(self, host : str, port : int, protocolFilePath : str):
        self.host = host
        self.port = port
        self.connected = False
        self.parser = protocol_parser.SermatecProtocolParser(protocolFilePath)
        self.pcuVersion = 0

    def __del__(self):
        pass
    
    async def __sendQuery(self, command : int) -> bytes:
        if self.isConnected():
            dataToSend = self.parser.generateRequest(command)
            self.writer.write(dataToSend)
            await self.writer.drain()

            data = await self.reader.read(256)
            _LOGGER.debug(f"Received data: { data.hex(' ', 1) }")

            if len(data) == 0:
                _LOGGER.error(f"No data received when issued command {command}: connection closed by the inverter.")
                self.connected = False
                raise NoDataReceived()
            
            if not self.parser.checkResponseIntegrity(data, command):
                _LOGGER.error(f"Command 0x{command:02x} response data malformed.")
                raise FailedResponseIntegrityCheck()

            return data
                    
        else:
            _LOGGER.error("Can't send request: not connected.")
            raise NotConnected()

    async def __sendQueryByName(self, commandName : str) -> bytes:
        command : int = self.parser.getCommandCodeFromName(commandName)
        return await self.__sendQuery(command)

    def __parseBatteryState(self, stateInt : int) -> str:
        if stateInt == 0x0011:
            return "charging"
        elif stateInt == 0x0022:
            return "discharging"
        elif stateInt == 0x0033:
            return "stand-by"
        else:
            return "unknown"

    def __parseWorkingMode(self, modeInt : int) -> str:
        if modeInt == 0x0001:
            return "General Mode"
        elif modeInt == 0x0002:
            return "Energy Storage Mode"
        else:
            return "unknown"

# ========================================================================
# Communications
# ========================================================================
    async def connect(self) -> bool:
        if not self.isConnected():

            confut = asyncio.open_connection(host = self.host, port = self.port)
            try:
                self.reader, self.writer = await asyncio.wait_for(confut, timeout = 3)
            except:
                _LOGGER.error("Couldn't connect to the inverter.")
                self.connected = False
                return False
            else:
                version : int = 0
                self.connected = True

                try:
                    version = await self.getPCUVersion()
                except PCUVersionMalformed:
                    _LOGGER.warning("Can't get PCU version! Using version 0, available parameters will be limited.")
                else:
                    self.pcuVersion = version
                    _LOGGER.info(f"Inverter's PCU version: {version}")
                
                return True
        else:
            return True
    
    def isConnected(self) -> bool:
        return self.connected

    async def disconnect(self) -> None:
        if self.connected:
            self.writer.close()
            await self.writer.wait_closed()
            self.connected = False

# ========================================================================
# Query methods
# ========================================================================
    async def getCustom(self, command : int) -> dict:
        data : bytes = await self.__sendQuery(command)
        parsedData : dict = self.parser.parseReply(command, self.pcuVersion, data)
        return parsedData
    
    async def getCustomRaw(self, command : int) -> bytes:
        return await self.__sendQuery(command)

    async def get(self, commandName : str) -> dict:
        data : bytes = await self.__sendQueryByName(commandName)
        parsedData : dict = self.parser.parseReply(self.parser.getCommandCodeFromName(commandName), self.pcuVersion, data)
        return parsedData
    
    async def getSerial(self) -> str:
        parsedData : dict = await self.get("systemInformation")
        serial : str = parsedData["product_sn"]["value"]
        return serial
    
    async def getBatteryInfo(self) -> dict:
        batInfo : dict = {}
        data = await self.__sendQueryByName("batteryStatus")

        batInfo["battery_voltage"]      = int.from_bytes(data[0x07:0x09], byteorder = "big", signed = False) / 10.0
        batInfo["battery_current"]      = int.from_bytes(data[0x09:0x0B], byteorder = "big", signed = True) / 10.0
        batInfo["battery_temperature"]  = int.from_bytes(data[0x0B:0x0D], byteorder = "big", signed = False) / 10.0
        batInfo["battery_SOC"]          = int.from_bytes(data[0x0D:0x0F], byteorder = "big", signed = False)
        batInfo["battery_SOH"]          = int.from_bytes(data[0x0F:0x11], byteorder = "big", signed = False)
        
        batInfo["battery_state"]        = self.__parseBatteryState(
            int.from_bytes(data[0x11:0x13], byteorder = "big", signed = False)
        )

        batInfo["battery_max_charging_current"]     = int.from_bytes(data[0x13:0x15], byteorder = "big", signed = False) / 10
        batInfo["battery_max_discharging_current"]  = int.from_bytes(data[0x15:0x17], byteorder = "big", signed = False) / 10

        return batInfo
    
    async def getGridPVInfo(self) -> dict:
        gridPVInfo : dict = {}
        data = await self.__sendQueryByName("gridPVStatus")
        
        gridPVInfo["pv1_voltage"]               = int.from_bytes(data[0x07:0x09], byteorder = "big", signed = False) / 10.0
        gridPVInfo["pv1_current"]               = int.from_bytes(data[0x09:0x0B], byteorder = "big", signed = False) / 10.0
        gridPVInfo["pv1_power"]                 = int.from_bytes(data[0x0B:0x0D], byteorder = "big", signed = False)
        gridPVInfo["pv2_voltage"]               = int.from_bytes(data[0x0D:0x0F], byteorder = "big", signed = False) / 10.0
        gridPVInfo["pv2_current"]               = int.from_bytes(data[0x0F:0x11], byteorder = "big", signed = False) / 10.0
        gridPVInfo["pv2_power"]                 = int.from_bytes(data[0x11:0x13], byteorder = "big", signed = False)
        gridPVInfo["ab_line_voltage"]           = int.from_bytes(data[0x19:0x1B], byteorder = "big", signed = False) / 10.0
        gridPVInfo["a_phase_current"]           = int.from_bytes(data[0x1B:0x1D], byteorder = "big", signed = False) / 10.0
        gridPVInfo["a_phase_voltage"]           = int.from_bytes(data[0x21:0x23], byteorder = "big", signed = False) / 10.0
        gridPVInfo["bc_line_voltage"]           = int.from_bytes(data[0x23:0x25], byteorder = "big", signed = False) / 10.0
        gridPVInfo["b_phase_current"]           = int.from_bytes(data[0x25:0x27], byteorder = "big", signed = False) / 10.0
        gridPVInfo["b_phase_voltage"]           = int.from_bytes(data[0x27:0x29], byteorder = "big", signed = False) / 10.0
        gridPVInfo["c_phase_voltage"]           = int.from_bytes(data[0x2B:0x2D], byteorder = "big", signed = False) / 10.0
        gridPVInfo["ca_line_voltage"]           = int.from_bytes(data[0x2D:0x2F], byteorder = "big", signed = False) / 10.0
        gridPVInfo["c_phase_current"]           = int.from_bytes(data[0x2F:0x31], byteorder = "big", signed = False) / 10.0
        gridPVInfo["grid_frequency"]            = int.from_bytes(data[0x31:0x33], byteorder = "big", signed = False) / 100.0
        gridPVInfo["grid_active_power"]         = int.from_bytes(data[0x35:0x37], byteorder = "big", signed = True)
        gridPVInfo["grid_reactive_power"]       = int.from_bytes(data[0x37:0x39], byteorder = "big", signed = True)
        gridPVInfo["grid_apparent_power"]       = int.from_bytes(data[0x39:0x3B], byteorder = "big", signed = True)
        gridPVInfo["backup_a_phase_voltage"]    = int.from_bytes(data[0x61:0x63], byteorder = "big", signed = False) / 10.0
        gridPVInfo["backup_b_phase_voltage"]    = int.from_bytes(data[0x63:0x65], byteorder = "big", signed = False) / 10.0
        gridPVInfo["backup_c_phase_voltage"]    = int.from_bytes(data[0x65:0x67], byteorder = "big", signed = False) / 10.0
        gridPVInfo["backup_frequency"]          = int.from_bytes(data[0x67:0x69], byteorder = "big", signed = False) / 100.0
        gridPVInfo["backup_a_phase_current"]    = int.from_bytes(data[0x69:0x6B], byteorder = "big", signed = False) / 10.0
        gridPVInfo["backup_b_phase_current"]    = int.from_bytes(data[0x6B:0x6D], byteorder = "big", signed = False) / 10.0
        gridPVInfo["backup_c_phase_current"]    = int.from_bytes(data[0x6D:0x6F], byteorder = "big", signed = False) / 10.0
        gridPVInfo["backup_active_power"]       = int.from_bytes(data[0x71:0x73], byteorder = "big", signed = True)
        gridPVInfo["backup_reactive_power"]     = int.from_bytes(data[0x73:0x75], byteorder = "big", signed = True)
        gridPVInfo["backup_apparent_power"]     = int.from_bytes(data[0x75:0x77], byteorder = "big", signed = True)
        return gridPVInfo
    
    async def getWorkingParameters(self) -> dict:
        workingParams : dict = {}
        data = await self.__sendQueryByName("workingParameters")
        
        workingParams["upper_limit_ongrid_power"] = int.from_bytes(data[0x0F:0x11], byteorder = "big", signed = False)
        workingParams["working_mode"] = self.__parseWorkingMode(
            int.from_bytes(data[0x13:0x15], byteorder = "big", signed = False)
        )
        workingParams["lower_limit_ongrid_soc"] = int.from_bytes(data[0x1D:0x1F], byteorder = "big", signed = False)

        return workingParams

    async def getLoad(self) -> int:
        load : int
        data = await self.__sendQueryByName("load")
        
        load = int.from_bytes(data[0x0B:0x0D], byteorder = "big", signed = False)
        return load

    async def getPCUVersion(self) -> int:
        parsedData : dict = await self.get("systemInformation")

        if not "protocol_version_number" in parsedData:
            _LOGGER.error("PCU version is missing!")
            raise PCUVersionMalformed()
        else:
            version : int = 0

            try:
                version = int(parsedData["protocol_version_number"]["value"])
            except ValueError:
                _LOGGER.error("Can't parse PCU version!")
                raise PCUVersionMalformed()
            
            return version