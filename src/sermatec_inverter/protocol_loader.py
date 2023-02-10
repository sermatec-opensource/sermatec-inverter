import logging
import json
import re
import math

class SermatecProtocolParser:

    REPLY_OFFSET_DATA = 7

    def __init__(self, logger : logging.Logger, path : str):
        self.logger = logger

        with open(path, "r") as protocolFile:
            protocolData = json.load(protocolFile)
            try:
                self.osim = protocolData["osim"]
            except KeyError:
                raise KeyError("Protocol file malformed, 'osim' key not found.")
            
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

    def __parseReplyField(self, fieldData : bytes, fieldType : str, fieldMultiplier : float) -> int | str | float:

        if fieldType == "int":
            return round(int.from_bytes(fieldData, byteorder = "big", signed = True) * fieldMultiplier, self.__getMultiplierDecimalPlaces(fieldMultiplier))
        elif fieldType == "uInt":
            return round(int.from_bytes(fieldData, byteorder = "big", signed = False) * fieldMultiplier, self.__getMultiplierDecimalPlaces(fieldMultiplier))
        elif fieldType == "string":
            # The string is null-terminated, trimming everything after first occurence of '\0'.
            trimmedString = fieldData.split(b"\x00", 1)[0]
            return trimmedString.decode('ascii')
        else:
            raise TypeError(f"The provided field is of an unsuported type '{fieldType}'")

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

        for field in cmdFields:
            try:
                fieldName   = field["name"]
                fieldLength = int(field["byteLen"])
                fieldType   = field["type"]
            except KeyError:
                raise KeyError(f"Field in command 0x{command : hex} is malformed: {field}")

            if fieldLength < 1:
                raise ValueError("Field length is zero or negative.")

            if "unitValue" in field:
                try:
                    fieldMultiplier : float = float(field["unitValue"])
                except:
                    raise SyntaxError("Can't convert field's unitValue to float.")
            else:
                fieldMultiplier : float = 1
                self.logger.debug(f"Field {fieldName} has not 'unitValue' key, using 1 as a default multiplier.")

            fieldTag = re.sub(r"[^A-Za-z0-9]", "_", field["name"]).lower()
            self.logger.debug(f"Created tag from name: {fieldTag}")
            
            self.logger.debug(f"Parsing field data: {reply[ replyPosition : (replyPosition + fieldLength) ].hex(' ')}")
            parsedData[fieldTag] = self.__parseReplyField(reply[ replyPosition : (replyPosition + fieldLength) ], fieldType, fieldMultiplier)

            replyPosition += fieldLength
        
        return parsedData
    
    def __calculateChecksum(self, data : bytes) -> bytes:
        checksum : int = 0x0f
        
        for byte in data:
            checksum = (checksum & 0xff) ^ byte
        
        self.logger.debug(f"Calculated checksum: {hex(checksum)}")

        return checksum.to_bytes(1)

    def generateRequest(self, command : int, version : int, reply : bytes) ->bytes:  
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
    binfile0d = open("../../dumps/0d", "rb")
    c0d = binfile0d.read()

    print(smc.parseReply(0x98, 400, c98))