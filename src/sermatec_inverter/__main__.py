import sys
import argparse
import logging
import asyncio
from . import Sermatec

async def main(cmds : list, host : str, port : int = None):

    if port:
        smc = Sermatec(logging, host, port)
    else:
        smc = Sermatec(logging, host)

    await smc.connect()
    
    if "serial" in cmds:        print(await smc.getSerial())
    if "battery" in cmds:       print(await smc.getBatteryInfo())
    if "grid" in cmds:          print(await smc.getGridPVInfo())
    if "parameters" in cmds:    print(await smc.getWorkingParameters())
    if "load" in cmds:          print(await smc.getLoad())

    await smc.disconnect()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog = "sermatec_inverter",
        description = "Sermatec Inverter communication script.",
    )
    parser.add_argument(
        "ip",
        help = "IP address of the inverter."
    )
    parser.add_argument(
        "--port",
        help = "API port. Defaults to 8899."
    )
    parser.add_argument(
        "--get",
        "-g",
        help = "Get data from the inverter.",
        choices = ["serial", "battery", "grid", "parameters", "load"],
        action = "append"
    )
    parser.add_argument(
        "-v",
        help = "Print debug data.",
        action = "store_true"
    )
    args = parser.parse_args()
    
    if not args.get:
        print("No command specified.")
        sys.exit()
    
    if args.v:
        logging.basicConfig(level = "DEBUG")

    asyncio.run(main(args.get, args.ip, args.port))