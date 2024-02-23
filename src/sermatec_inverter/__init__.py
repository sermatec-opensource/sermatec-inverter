import logging
import asyncio
from . import protocol_parser
from .exceptions import *

_LOGGER = logging.getLogger(__name__)

class Sermatec:

    QUERY_WRITE_TIMEOUT     = 10
    QUERY_READ_TIMEOUT      = 20
    QUERY_ATTEMPTS          = 3

    def __init__(self, host : str, port : int, protocolFilePath : str):
        self.host = host
        self.port = port
        self.connected = False
        self.parser = protocol_parser.SermatecProtocolParser(protocolFilePath)
        self.pcuVersion = 0
    
    async def __sendQuery(self, command : int) -> bytes:
        if self.isConnected():
            dataToSend = self.parser.generateRequest(command)
            self.writer.write(dataToSend)

            for attempt in range(self.QUERY_ATTEMPTS):
                _LOGGER.debug(f"Sending query, attempt {attempt + 1}/{self.QUERY_ATTEMPTS}")
                try:
                    await asyncio.wait_for(self.writer.drain(), timeout=self.QUERY_WRITE_TIMEOUT)
                except asyncio.TimeoutError:
                    _LOGGER.error(f"[{attempt + 1}/{self.QUERY_ATTEMPTS}] Timeout when sending request to inverter.")
                    if attempt + 1 == self.QUERY_ATTEMPTS:
                        raise NoDataReceived()
                    continue                    
                
                try:
                    data = await asyncio.wait_for(self.reader.read(256), timeout=self.QUERY_READ_TIMEOUT)
                except asyncio.TimeoutError:
                    _LOGGER.error(f"[{attempt + 1}/{self.QUERY_ATTEMPTS}] Timeout when waiting for response from the inverter.")
                    if attempt + 1 == self.QUERY_ATTEMPTS:
                        raise NoDataReceived()
                    continue                  

                _LOGGER.debug(f"Received data: { data.hex(' ', 1) }")

                if len(data) == 0:
                    _LOGGER.error(f"No data received when issued command {command}: connection closed by the inverter.")
                    self.connected = False
                    raise NoDataReceived()
                
                if not self.parser.checkResponseIntegrity(data, command):
                    _LOGGER.error(f"[{attempt + 1}/{self.QUERY_ATTEMPTS}] Command 0x{command:02x} response data malformed.")
                    if attempt + 1 == self.QUERY_ATTEMPTS:
                        raise FailedResponseIntegrityCheck()
                else:
                    break

            return data
                    
        else:
            _LOGGER.error("Can't send request: not connected.")
            raise NotConnected()

    async def __sendQueryByName(self, commandName : str) -> bytes:
        command : int = self.parser.getCommandCodeFromName(commandName)
        return await self.__sendQuery(command)

# ========================================================================
# Communications
# ========================================================================
    async def connect(self) -> bool:
        if not self.isConnected():

            confut = asyncio.open_connection(host = self.host, port = self.port)
            try:
                self.reader, self.writer = await asyncio.wait_for(confut, timeout = 3)
            except asyncio.TimeoutError:
                _LOGGER.error("Couldn't connect to the inverter.")
                self.connected = False
                return False
            else:
                version : int = 0
                self.connected = True

                try:
                    version = await self.getPCUVersion()
                except (NoDataReceived, FailedResponseIntegrityCheck, PCUVersionMalformed):
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
    async def queryCustom(self, command : int) -> dict:
        data : bytes = await self.__sendQuery(command)
        parsedData : dict = self.parser.parseReply(command, self.pcuVersion, data)
        return parsedData
    
    async def queryCustomRaw(self, command : int) -> bytes:
        return await self.__sendQuery(command)

    async def query(self, commandName : str) -> dict:
        data : bytes = await self.__sendQueryByName(commandName)
        parsedData : dict = self.parser.parseReply(self.parser.getCommandCodeFromName(commandName), self.pcuVersion, data)
        return parsedData

    async def getPCUVersion(self) -> int:
        parsedData : dict = await self.query("systemInformation")

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