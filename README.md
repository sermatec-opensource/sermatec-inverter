# sermatec-inverter
LAN communication docs and scripts for the Sermatec solar inverter.

## Protocol description
This protocol is used by the *Sermatec* application (available for Android and iOS) for a local connection to the inverter via built-in WiFi access point or via LAN connection.

Default AP's password is `gsstes123456`.

Distributor's (admin) passwords for setting parameters:
- This password is probably hardcoded in the apk, cannot be changed.
- Discovered passwords:
    - Sermatec2021
    - sermatec2021
    - Sermatec2015
    - Sermatec2019@Gsstes2019

Integers are presented in the big-endian format (MSB first).

Inverter's open ports:
- 23: telnet
- 80: UART-TCP module web config
    - username: admin
    - password: admin
- 8000: ?
- 8899: API port

## Request format
| Byte | Value |
| ---- | ----- |
| 0    | `0xFE`  |
| 1    | `0x55`  |
| 2    | source (`0x64`) |
| 3    | target (`0x14`) |
| 4-5  | command |
| 6    | message length |
| 7-n  | data |
| n+1  | checksum |
| n+2  | `0xAE` |

## Response format
It is the same but the source and target addresses are swapped.
Notes: 
- integers are represented in the big-endian format.
- fractional numbers (with exceptions) are represented in the fixed-point, scaling 1/10.
- all values are represented in the SI units (ampere, volt, watt, volt-ampere, volt-ampere reactive, hertz...).
- data type uint16_t at address 0x00 means hi-lo integer stored at bytes 0-1.

## Commands
| Command (in big-endian) | Function |
| ----------------------- | -------- |
| `0x9800`                | Get system information.
| `0x6800`                | Send current date and time. |
| `0x0a00` | Get battery information. |
| `0x0b00` | Get grid status. |
| `0x0c00` | ? |

### **`0x9800`: Get system information**
**Request:** `fe 55 64 14 98 00 00 4c ae`

**Response:**
| Address | Meaning | Data type |
| ----    | ------- | --------- |
| 0x07 | PCU version | uint16_t |
| 0x09 | ? | ? |
| 0x0B | ? | ? |
| 0x0D | Serial ID string. | string (null-terminated, max length 44 bytes) |

### **`0x6800`: Send current date and time**
YEAR[2];MONTH;DAY;HOUR;MINUTES;SECONDS

### **`0x0a00`: Battery information**
**Request:** `fe 55 64 14 0a 00 00 de ae`

**Response:**
| Address | Meaning | Data type |
| ---- | ------- | --------- |
| 0x07 | Battery voltage. | uint16_t fractional
| 0x09 | Battery current. | uint16_t fractional
| 0x0B | Battery temperature. | uint16_t fractional
| 0x0D | Battery state of charge. | uint16_t
| 0x0F | Battery state of health. | uint16_t
| 0x11 | Battery state (see note). | uint16_t
| 0x13 | Battery maximal charging current. | uint16_t fractional
| 0x15 | Battery maximal discharging current. | uint16_t fractional
| 0x17 | ? | ?
| 0x19 | ? | ?

Battery states:
- 0x0011: charging
- 0x0022: discharging
- 0x0033: stand-by

### **`0x0b00`: Grid and PV information**
**Request:** `fe 55 64 14 0b 00 00 df ae`

**Response:**
| Address | Meaning | Data type |
| ------- | ------- | --------- |
| 0x07 | PV1 voltage. | uint16_t fractional |
| 0x09 | PV1 current. | uint16_t fractional |
| 0x0B | PV1 power. | uint16_t fractional |
| 0x0D | PV2 voltage. | uint16_t fractional |
| 0x0F | PV2 current. | uint16_t fractional |
| 0x11 | PV2 power. | uint16_t fractional |
| 0x19 | AB line voltage | uint16_t fractional |
| 0x1B | A phase current. | uint16_t fractional |
| 0x21 | A phase voltage. | uint16_t fractional |
| 0x23 | BC line voltage. | uint16_t fractional |
| 0x25 | B phase current. | uint16_t fractional |
| 0x27 | B phase voltage. | uint16_t fractional |
| 0x2B | C phase voltage. | uint16_t fractional |
| 0x2D | CA line voltage. | uint16_t fractional |
| 0x2F | C phase current. | uint16_t fractional |
| 0x31 | Grid (mains) frequency. | uint16_t fractional (scaling 1/100) |
| 0x35 | Grid active power. | int16_t |
| 0x37 | Grid reactive power. | int16_t |
| 0x39 | Grid apparent power. | int16_t |

### **`0x0d00`: Error**
### **`0x1e00`: Error**

## Checksum
The checksum calculation function is unknown for now.