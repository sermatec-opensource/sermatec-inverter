# Sermatec Solar Inverter
This repository contains local API documentation for the Sermatec solar inverter and communication scripts.

Whole communication with the inverter runs through the UART-TCP converter USR-WIFI232-B2, which supports 802.11 b/g/n. It works either in a station mode (for connection to the home AP) or in a access point mode (local connection mode in the official ap). See docs below for more technical information.

## Index
- [`DEVELOPMENT.md`](docs/DEVELOPMENT.md): protocol reverse-engineering guide.
- [`PROTOCOL.md`](docs/PROTOCOL.md): protocol documentation.
- [`sermatec.py`](src/sermatec_inverter/sermatec.py): communication script.

## License
The project is licensed under the MIT License. (C) Ondrej Golasowski