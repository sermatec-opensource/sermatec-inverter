# Sermatec Solar Inverter
This repository contains local API documentation for the Sermatec solar inverter and communication scripts.

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