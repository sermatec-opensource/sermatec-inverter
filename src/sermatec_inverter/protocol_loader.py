import logging
import json

class SermatecProtocolParser:
    def __init__(self, logger : logging.Logger, path : str):
        self.logger = logger

        with open(path, "r") as protocolFile:
            protocolData = json.load(protocolFile)
            try:
                self.osim = protocolData["osim"]
            except KeyError:
                raise KeyError("File malformed, 'osim' key not found.")
            
    # Get all available query commands in the specified version.
    def getQueryCommands(self, version : int) -> list:
        cmds = set()
        for ver in self.osim["versions"]:
            cmds |= {int(cmd, base=16) for cmd in ver["queryCommands"] if ver["version"] <= version}
        
        listCmds = list(cmds)
        listCmds.sort()
        print(type(listCmds[0]))
        return listCmds

    def getCommandByVersion(self, command : int, version : int) -> dict:
        # Get all commands supported by the specified versions.
        allSupportedVersions = [ver for ver in self.osim["versions"] if ver["version"] <= version]
        cmd = {}
        # Get a newest version of a specified command.
        for ver in allSupportedVersions:
            cmd = next((cmd for cmd in ver["commands"] if int(cmd["type"],base=16) == command), cmd)

        if not cmd:
            raise KeyError(f"Specified command '{command : hex}' not found.")

        return cmd        
        

    # Parse a command reply using a specified version definition.
    def parseReply(self, command : int, version : int, reply : bytes):
        cmd = self.getCommandByVersion(command, version)
        


if __name__ == "__main__":
    smc : SermatecProtocolParser = SermatecProtocolParser(logging, "protocol-en.json")
    #print(smc.getQueryCommands(0))
    smc.getCommandByVersion(0x98, 300)