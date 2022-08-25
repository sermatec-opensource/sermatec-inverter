import socket
import logging

class Sermatec:

    REQ_SYSINFO = bytes([0xfe, 0x55, 0x64, 0x14, 0x98, 0x00, 0x00, 0x4c, 0xae])
    REQ_BATTERY = bytes([0xfe, 0x55, 0x64, 0x14, 0x0a, 0x00, 0x00, 0xde, 0xae])

    def __init__(self, host : str, port : int = 8899):
        self.host = host
        self.port = port
        self.connected = False
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except:
            raise RuntimeError("Couldn't create socket.")
        else:
            self.sock.settimeout(5)

    def __del__(self):
        pass

    def __headerCheck(self, data : bytes) -> bool:
        return data.startswith(b"\xFE\x55\x14\x64")

    def __sendReq(self, toSend : bytes) -> bytes:
        if self.connected:
            self.sock.sendall(toSend)
            data = self.sock.recv(256)

            if len(data) == 0:
                logging.error("No data received: connection closed.")
                self.connected = False
                return b""
            
            if not self.__headerCheck(data):
                logging.error("Bad header in data received.")
                return b""
            
            logging.debug(data.hex(" ", 1))

            return data
        else:
            logging.error("Can't send request: not connected.")
            return b""
    
    def __parseBatteryState(self, stateInt : int) -> str:
        if stateInt == 0x0011:
            return "charging"
        elif stateInt == 0x0022:
            return "discharging"
        elif stateInt == 0x0033:
            return "stand-by"
        else:
            return "unknown"

    def connect(self) -> bool:
        if not self.connected:
            try:
                self.sock.connect((self.host, self.port))
            except:
                logging.error("Couldn't connect to the inverter.")
                self.connected = False
                return False
            else:
                self.connected = True
                return True
        else:
            return True

    def disconnect(self) -> None:
        self.sock.close()
        self.connected = False

    def getSerial(self) -> str:
        data = self.__sendReq(self.REQ_SYSINFO)
        if len(data) < 0x0E or data[0x04:0x06] != self.REQ_SYSINFO[0x04:0x06]:
            logging.error("Bad message received.")
            return ""

        data = data[0x0D:]
        data = data.split(b"\x00", 1)[0]
        serial = data.decode('ascii')
        return serial
    
    def getBatteryInfo(self) -> dict:
        batInfo : dict = {}
        data = self.__sendReq(self.REQ_BATTERY)
        if len(data) < 0x1B or data[0x04:0x06] != self.REQ_BATTERY[0x04:0x06]:
            logging.error("Bad message received")
            return batInfo

        batInfo["voltage"] = int.from_bytes(data[0x07:0x09], byteorder = "big", signed = False) / 10.0
        batInfo["current"] = int.from_bytes(data[0x09:0x0B], byteorder = "big", signed = False) / 10.0
        batInfo["temperature"] = int.from_bytes(data[0x0B:0x0D], byteorder = "big", signed = False) / 10.0
        batInfo["SOC"] = int.from_bytes(data[0x0D:0x0F], byteorder = "big", signed = False)
        batInfo["SOH"] = int.from_bytes(data[0x0F:0x11], byteorder = "big", signed = False)
        batInfo["state"] = self.__parseBatteryState(
            int.from_bytes(data[0x11:0x13], byteorder = "big", signed = False)
        )
        batInfo["max_charging_current"] = int.from_bytes(data[0x13:0x15], byteorder = "big", signed = False) / 10
        batInfo["max_discharging_current"] = int.from_bytes(data[0x15:0x17], byteorder = "big", signed = False) / 10

        return batInfo
        
if __name__ == "__main__":
    logging.basicConfig(level = "DEBUG")
    smc = Sermatec("IP-HERE")
    smc.connect()
    print(smc.getSerial())
    print(smc.getBatteryInfo())
    smc.disconnect()