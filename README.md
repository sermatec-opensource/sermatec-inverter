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
### *Newest version:* Source
```
git clone https://github.com/andreondra/sermatec-inverter.git
cd sermatec-inverter
python3 -m src.sermatec_inverter
```

### *Stable version:* PyPI package
```
pip install sermatec-inverter
python3 -m sermatec_inverter
```

## License
The project is licensed under the MIT License. (C) Ondrej Golasowski