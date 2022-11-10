# Sermatec Solar Inverter
This repository contains local API documentation for the Sermatec solar inverter and communication scripts.

Whole communication with the inverter runs through the UART-TCP converter USR-WIFI232-B2, which supports 802.11 b/g/n. It works either in a station mode (for connection to the home AP) or in a access point mode (local connection mode in the official ap). See docs below for more technical information.

## Index
- [`DEVELOPMENT.md`](docs/DEVELOPMENT.md): protocol reverse-engineering guide.
- [`PROTOCOL.md`](docs/PROTOCOL.md): protocol documentation.
- [`sermatec_inverter`](src/sermatec_inverter): communication module.

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