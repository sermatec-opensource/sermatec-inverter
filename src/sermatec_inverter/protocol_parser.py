import logging
import json
import re
import math

# Local module logger.
logger = logging.getLogger(__name__)

class SermatecProtocolParser:

    REPLY_OFFSET_DATA = 7
    
    REQ_SIGNATURE           = bytes([0xfe, 0x55])
    REQ_APP_ADDRESS         = bytes([0x64])
    REQ_INVERTER_ADDRESS    = bytes([0x14])
    REQ_FOOTER              = bytes([0xae])

    COMMAND_SHORT_NAMES : dict = {
        "systemInformation"   : 0x98,
        "batteryStatus"       : 0x0a,
        "gridPVStatus"        : 0x0b,
        "runningStatus"       : 0x0c,
        "workingParameters"   : 0x95,
        "load"                : 0x0d, # Same as bmsStatus, keeping for backwards compatibility.
        "bmsStatus"           : 0x0d
    }


    def __init__(self, logger : logging.Logger, path : str):
        self.logger = logger

        with open(path, "r") as protocolFile:
            protocolData = json.load(protocolFile)
            try:
                self.osim = protocolData["osim"]
            except KeyError:
                raise KeyError("Protocol file malformed, 'osim' key not found.")
            
    def getCommandCodeFromName(self, commandName : str) -> int:
        if commandName in self.COMMAND_SHORT_NAMES:
            return self.COMMAND_SHORT_NAMES[commandName]
        else:
            raise KeyError(f"Specified command '{commandName}' not found.")

    # Get all available query commands in the specified version.
    def getQueryCommands(self, version : int) -> list:
        cmds = set()
        for ver in self.osim["versions"]:
            cmds |= {int(cmd, base=16) for cmd in ver["queryCommands"] if ver["version"] <= version}
        
        listCmds = list(cmds)
        listCmds.sort()
        print(type(listCmds[0]))
        return listCmds

    def __getCommandByVersion(self, command : int, version : int) -> dict:
        # Get all commands supported by the specified versions.
        allSupportedVersions = [ver for ver in self.osim["versions"] if ver["version"] <= version]
        cmd = {}
        # Get a newest version of a specified command.
        for ver in allSupportedVersions:
            cmd = next((cmd for cmd in ver["commands"] if int(cmd["type"],base=16) == command), cmd)

        if not cmd:
            raise KeyError(f"Specified command '{command : hex}' not found.")

        return cmd
    
    def __getMultiplierDecimalPlaces(self, multiplier : float) -> int:
        if "." in str(multiplier):
            return len(str(multiplier).split(".")[1])
        else:
            return 0

    # Parse a command reply using a specified version definition.
    # Command can be probably extracted from the reply, but here we check the integrity.
    def parseReply(self, command : int, version : int, reply : bytes) -> dict:
        cmd : dict = self.__getCommandByVersion(command, version)
        self.logger.debug(f"Reply to parse: {reply[self.REPLY_OFFSET_DATA:].hex(' ')}")

        try:
            cmdType     : dict = cmd["type"]
            cmdName     : dict = cmd["comment"]
            cmdFields   : dict = cmd["fields"]
        except KeyError:
            raise KeyError(f"Protocol file malformed, can't process command 0x{command : hex}")
        self.logger.debug(f"It is command 0x{cmdType}: {cmdName} with {len(cmdFields)} fields")

        parsedData : dict = {}
        replyPosition = self.REPLY_OFFSET_DATA

        for idx, field in enumerate(cmdFields):

            self.logger.debug(f"== Field #{idx} (reply byte #{replyPosition})")

            if not (("name" or "byteLen" or "type") in field):
                raise KeyError(f"Field has a 'name', 'byteLen' or 'type' missing: {field}.")

            fieldLength = int(field["byteLen"])
            if fieldLength < 1:
                raise ValueError("Field length is zero or negative.")

            if ("same" in field and field["same"]) or idx == 0:
                self.logger.debug(f"Staying at the same byte.")
            else:
                replyPosition += fieldLength

            fieldType = field["type"]
            if fieldType == "bit":
                if "bitPosition" in field:
                    fieldBitPosition = field["bitPosition"]
                else:
                    raise KeyError("Field is of a type 'bit', but is missing key 'bitPosition'.")

            if fieldType == "bitRange":
                if "fromBit" and "endBit":
                    fieldFromBit = field["fromBit"]
                    fieldEndBit = field["endBit"]
                else:
                    raise KeyError("Field is of a type 'bitRange' but is missing key 'fromBit' or 'endBit'.")


            fieldName = field["name"]
            fieldTag = re.sub(r"[^A-Za-z0-9]", "_", field["name"]).lower()
            self.logger.debug(f"Created tag from name: {fieldTag}")


            if "unitValue" in field:
                try:
                    fieldMultiplier : float = float(field["unitValue"])
                except:
                    raise SyntaxError("Can't convert field's unitValue to float.")
            else:
                fieldMultiplier : float = 1
                self.logger.debug(f"Field {fieldName} has not 'unitValue' key, using 1 as a default multiplier.")          
            
            currentFieldData = reply[ replyPosition : (replyPosition + fieldLength) ]
            self.logger.debug(f"Parsing field data: {currentFieldData.hex(' ')}")

            if fieldType == "int":
                parsedData[fieldTag] = round(int.from_bytes(currentFieldData, byteorder = "big", signed = True) * fieldMultiplier, self.__getMultiplierDecimalPlaces(fieldMultiplier))
            elif fieldType == "uInt":
                parsedData[fieldTag] = round(int.from_bytes(currentFieldData, byteorder = "big", signed = False) * fieldMultiplier, self.__getMultiplierDecimalPlaces(fieldMultiplier))
            elif fieldType == "string":
                # The string is null-terminated, trimming everything after first occurence of '\0'.
                trimmedString = currentFieldData.split(b"\x00", 1)[0]
                parsedData[fieldTag] = trimmedString.decode('ascii')
            elif fieldType == "bit":
                binString : str = bin(int.from_bytes(currentFieldData, byteorder = "little", signed = False)).removeprefix("0b")
                parsedData[fieldTag] = int(binString[fieldBitPosition])
            elif fieldType == "bitRange":
                binString : str = bin(int.from_bytes(currentFieldData, byteorder = "little", signed = False)).removeprefix("0b")
                parsedData[fieldTag] = binString[fieldFromBit:fieldEndBit]
            else:
                raise TypeError(f"The provided field is of an unsuported type '{fieldType}'")

            self.logger.debug(f"Parsed: {parsedData[fieldTag]}")
        
        return parsedData
    
    def __calculateChecksum(self, data : bytes) -> bytes:
        checksum : int = 0x0f
        
        for byte in data:
            checksum = (checksum & 0xff) ^ byte
        
        self.logger.debug(f"Calculated checksum: {hex(checksum)}")

        return checksum.to_bytes(1)

    def checkResponseIntegrity(self, response : bytes, expectedCommandByte : int) -> bool:
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

    def generateRequest(self, command : int) ->bytes:  
        request : bytearray = bytearray([*self.REQ_SIGNATURE, *self.REQ_APP_ADDRESS, *self.REQ_INVERTER_ADDRESS, command, 0x00, 0x00])
        request += self.__calculateChecksum(request)
        request += self.REQ_FOOTER

        self.logger.debug(f"Built command: {[hex(x) for x in request]}")

        return request
            

if __name__ == "__main__":
    logging.basicConfig(level = "DEBUG")
    smc : SermatecProtocolParser = SermatecProtocolParser(logging, "protocol-en.json")
    #print(smc.getQueryCommands(0))
    binfile98 = open("../../dumps/98", "rb")
    c98 = binfile98.read()
    binfile0a = open("../../dumps/0a", "rb")
    c0a = binfile0a.read()
    binfile0b = open("../../dumps/0b", "rb")
    c0b = binfile0b.read()
    binfile0c = open("../../dumps/0c_ongrid", "rb")
    c0c = binfile0c.read()
    binfile0d = open("../../dumps/0d", "rb")
    c0d = binfile0d.read()

    print(smc.parseReply(0x0d, 400, c0d))
    # print(smc.parseReply(0x0c, 400, c0c))