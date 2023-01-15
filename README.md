![License badge](https://img.shields.io/github/license/andreondra/sermatec-inverter?style=for-the-badge)

# Sermatec Solar Inverter
This repository contains local API documentation for the Sermatec solar inverter and communication scripts.

Whole communication with the inverter runs through the UART-TCP converter USR-WIFI232-B2, which supports 802.11 b/g/n. It works either in a station mode (for connection to the home AP) or in a access point mode (local connection mode in the official ap). See docs below for more technical information.

## Index
### Generic contribution guide
If you want to contribute, please check the guidelines first: [`CONTRIBUTING.md`](docs/CONTRIBUTING.md).

### Reverse-engineering (development) guides
If you want to help with decoding the proprietary Sermatec protocol, choose if you want to use the physical Android device or a virtual one and continue with the appropriate guide.
- [`RE_AVD.md`](docs/RE_AVD.md): Android virtual device configuration.
- [`RE_PHYSICAL_DEVICE.md`](docs/RE_PHYSICAL_DEVICE.md): Physical device configuration.
- [`RE_DATA_INSPECTION.md`](docs/RE_DATA_INSPECTION.md): Data inspection guide.

### Inverter and protocol docs
- [`PROTOCOL.md`](docs/PROTOCOL.md): protocol documentation.

## Console interface usage

The script takes very few args to run:
1. the `--get` arg to know which kind of data you want to retrieve.
2. the ip of your inverter.

The script also takes few optional args:
1. the `-v` flag to have a verbose output.
2. the `--port` arg to use a different port than default 8899 for inverter connection.
3. the `-h` or `--help` flag to display the help about the command

#### Examples
Having battery info on an inverter with 10.0.0.254 ip:
```bash
python3 -m src.sermatec_inverter --get=battery 10.0.0.254
```
Having grid info using the verbose mode with a 192.168.0.254 inverter with port 8900:
```bash
python3 -m src.sermatec_inverter --get=grid -v --port=8900 192.168.0.254
```

### *Newest version:* Source
```
git clone https://github.com/andreondra/sermatec-inverter.git
cd sermatec-inverter
python3 -m src.sermatec_inverter --help
```

### *Docker / Docker-compose:*
This method require to have both `docker` and `docker compose` setup on your computer (`docker compose` is now embedded officially when you install docker).
Refer to this [official documentation](https://docs.docker.com/get-docker/) to have it installed.

Once done: you can use the docker-compose to run the app in a controlled environment:
```bash
git clone https://github.com/andreondra/sermatec-inverter.git
cd sermatec-inverter
docker compose run python-bash
```
Once the container started, you'll be in a bash environment with all your need for working and running the script:
```bash
python3 -m sermatec_inverter --help
```

### *Stable version:* PyPI package
```
pip install sermatec-inverter
python3 -m sermatec_inverter --help
```

## License
The project is licensed under the MIT License. (C) Ondrej Golasowski
