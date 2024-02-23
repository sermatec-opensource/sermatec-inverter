import sys
import argparse
import logging
import asyncio
from pathlib import Path
from . import Sermatec
from .protocol_parser import SermatecProtocolParser
from .exceptions import *

async def customQueryFunc(**kwargs):
    """Query the inverter with a custom command.

    Keyword Args:
        command (int): The command's single-byte code. 
        ip (str): Inverter's IP.
        port (str): Inverter's API port.
        protocolFilePath (str): Path to the protocol JSON.
        raw (bool): True = parse the response, otherwise return raw bytes.
    """

    # Parsing command - it can be hex, dec or whathever base integer.
    try:
        parsedCmd = int(kwargs["command"], 0)
        if parsedCmd not in range(0, 255):
            raise ValueError
    except:
        print("The command has to be an integer in range [0, 255] (single byte).")
        return

    smc = Sermatec(kwargs["ip"], kwargs["port"], kwargs["protocolFilePath"])
    print(f"Connecting to Sermatec at {kwargs['ip']}:{kwargs['port']}...", end = "")
    if await smc.connect():
        print("OK")
    else:
        print("Can't connect.")
        return

    print("Getting data...")
    data : str | dict = {}

    if kwargs["raw"]:
        data = (await smc.queryCustomRaw(parsedCmd)).hex(' ')
    else:
        try:
            data = await smc.queryCustom(parsedCmd)
        except CommandNotFoundInProtocol:
            print("The command was not found in protocol for inverter's version, unable to parse. Try --raw to get raw bytes.")
        except (ProtocolFileMalformed, ParsingNotImplemented):
            print("There was an error parsing the command. Refer to logs.")
        except (NoDataReceived):
            print("Inverter sent no data.")
        except (FailedResponseIntegrityCheck):
            print("The response was malformed.")

    if data: print(data)

    print("Disconnecting...", end = "")
    await smc.disconnect()
    print("OK")

async def queryFunc(**kwargs):
    
    smc = Sermatec(kwargs["ip"], kwargs["port"], kwargs["protocolFilePath"])
    print(f"Connecting to Sermatec at {kwargs['ip']}:{kwargs['port']}...", end = "")
    if await smc.connect():
        print("OK")
    else:
        print("Can't connect.")
        return

    print("Getting data...")
    pass

    data : dict = {}

    try:
        data = await smc.query(kwargs["command"])
    except CommandNotFoundInProtocol:
        print("The command was not found in protocol for inverter's version, unable to parse. Try --raw to get raw bytes.")
    except (ProtocolFileMalformed, ParsingNotImplemented):
        print("There was an error parsing the command. Refer to logs.")
    except (NoDataReceived):
        print("Inverter sent no data.")
    except (FailedResponseIntegrityCheck):
        print("The response was malformed.")
        
    if data: print(data)

    print("Disconnecting...", end = "")
    await smc.disconnect()
    print("OK")

async def setFunc(**kwargs):
    pass

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog = "sermatec_inverter",
        description = "Sermatec Inverter communication script.",
    )
    parser.add_argument(
        "ip",
        help = "IP address of the inverter."
    )
    
    subparsers = parser.add_subparsers(dest = "cmd")
    queryParser = subparsers.add_parser("query", help = "Query datasets from the inverter.")
    queryParser.set_defaults(cmdFunc = queryFunc)

    cmdShortNames = SermatecProtocolParser.COMMAND_SHORT_NAMES.keys()
    queryParser.add_argument(
        "command",
        help = "A dataset to query.",
        choices = cmdShortNames,
    )

    setParser = subparsers.add_parser("set", help = "Configure a value in the inverter.")
    setParser.set_defaults(cmdFunc = setFunc)

    customqueryParser = subparsers.add_parser("customquery", help = "Query the inverter using custom command.")
    customqueryParser.set_defaults(cmdFunc = customQueryFunc)
    customqueryParser.add_argument(
        "command",
        help = "A single-byte command to send.",
    )
    customqueryParser.add_argument(
        "--raw",
        help = "Do not parse the response.",
        action = "store_true"
    )
    
    parser.add_argument(
        "--port",
        help = "API port. Defaults to 8899.",
        default = 8899
    )
    parser.add_argument(
        "-v",
        help = "Print debug data.",
        action = "store_true"
    )
    parser.add_argument(
        "--protocolFilePath",
        help = "JSON with the OSIM protocol description.",
        default = (Path(__file__).parent / "protocol-en.json").resolve()
    )

    args = parser.parse_args()

    if args.v:
        logging.basicConfig(level = "DEBUG")

    if not args.cmd:
        print("Error: No command specified.")
        parser.print_help()
        sys.exit()
    else:
        asyncio.run(args.cmdFunc(**vars(args)))
