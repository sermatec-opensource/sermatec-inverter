import logging
import asyncio

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

    def __init__(self, logger : logging.Logger, host : str, port : int = 8899):
        self.host = host
        self.port = port
        self.connected = False
        self.logger = logger

    def __del__(self):
        pass
    
    def __checkResponseIntegrity(self, response : bytes, expectedCommandByte : bytes) -> bool:
        # Length check.
        if len(response) < 8: return False

        # Signature check.
        if response[0x00:0x02] != self.REQ_SIGNATURE:
            logging.debug("Bad response signature.")
            return False
        # Sender + receiver check.
        if response[0x02:0x03] != self.REQ_INVERTER_ADDRESS:
            logging.debug("Bad response sender address.")
            return False
        if response[0x03:0x04] != self.REQ_APP_ADDRESS:
            logging.debug("Bad response recipient address.")
            return False
        # Response command check.
        if response[0x04:0x05] != expectedCommandByte:
            logging.debug("Bad response expected command.")
            return False
        # Zero.
        if response[0x05] != 0:
            logging.debug("No zero at response position 0x00.")
            return False
        # Checksum verification.
        if response[-0x02:-0x01] != self.__calculateChecksum(response[:len(response) - 2]):
            logging.debug(f"Bad response checksum: {response[-0x03:-0x02].hex()}")
            return False
        # Footer check.
        if response[-0x01] != int.from_bytes(self.REQ_FOOTER):
            logging.debug("Bad response footer.")
            return False

        return True

    def __calculateChecksum(self, data : bytes) -> bytes:
        checksum : int = 0x0f
        
        for byte in data:
            checksum = (checksum & 0xff) ^ byte
        
        self.logger.debug(f"Calculated checksum: {hex(checksum)}")

        return checksum.to_bytes(1)

    def __buildCommand(self, commandName : str) -> bytes:
        if not commandName in self.REQ_COMMANDS:
            raise KeyError(f"Specified command \"{commandName}\" does not exist.")
        
        command : bytearray = bytearray([*self.REQ_SIGNATURE, *self.REQ_APP_ADDRESS, *self.REQ_INVERTER_ADDRESS, *self.REQ_COMMANDS[commandName], 0x00, 0x00])
        command += self.__calculateChecksum(command)
        command += self.REQ_FOOTER

        self.logger.debug(f"Built command: {[hex(x) for x in command]}")

        return command
          
    async def __sendCommandAndReceiveData(self, commandName : str) -> bytes:
        if self.isConnected():
            dataToSend = self.__buildCommand(commandName)
            self.writer.write(dataToSend)
            await self.writer.drain()

            data = await self.reader.read(256)
            self.logger.debug(f"Received data: { data.hex(' ', 1) }")

            if len(data) == 0:
                self.logger.error(f"No data received when issued command {commandName}: connection closed by the inverter.")
                self.connected = False
                raise ConnectionAbortedError()
            
            if not self.__checkResponseIntegrity(data, self.REQ_COMMANDS[commandName]):
                self.logger.error(f"Command {commandName} response data malformed.")
                raise ValueError()

            return data

        else:
            self.logger.error("Can't send request: not connected.")
            raise RuntimeError("Can't send request: not connected.")
    
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

    async def connect(self) -> bool:
        if not self.isConnected():

            confut = asyncio.open_connection(host = self.host, port = self.port)
            try:
                self.reader, self.writer = await asyncio.wait_for(confut, timeout = 3)
            except:
                self.logger.error("Couldn't connect to the inverter.")
                self.connected = False
                return False
            else:
                self.connected = True
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

    async def getSerial(self) -> str:
        data = await self.__sendCommandAndReceiveData("systemInformation")
        data = data[0x0D:]
        data = data.split(b"\x00", 1)[0]
        serial = data.decode('ascii')
        return serial
    
    async def getBatteryInfo(self) -> dict:
        batInfo : dict = {}
        data = await self.__sendCommandAndReceiveData("batteryStatus")

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
        data = await self.__sendCommandAndReceiveData("gridPVStatus")
        
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
        data = await self.__sendCommandAndReceiveData("workingParameters")
        
        workingParams["upper_limit_ongrid_power"] = int.from_bytes(data[0x0F:0x11], byteorder = "big", signed = False)
        workingParams["working_mode"] = self.__parseWorkingMode(
            int.from_bytes(data[0x13:0x15], byteorder = "big", signed = False)
        )
        workingParams["lower_limit_ongrid_soc"] = int.from_bytes(data[0x1D:0x1F], byteorder = "big", signed = False)

        return workingParams

    async def getLoad(self) -> int:
        load : int = None
        data = await self.__sendCommandAndReceiveData("load")
        
        load = int.from_bytes(data[0x0B:0x0D], byteorder = "big", signed = False)
        return load
