# Protocol description
The inverter's TCP protocol, nicknamed FE 55 (by its signature) and also known as Optical Storage Integrated Machine Protocol (osim) is used by the *Sermatec* application (available for Android and iOS) for a local connection to the inverter via built-in WiFi access point or via LAN connection.

Default AP's password is `gsstes123456`.

Distributor's (admin) passwords for setting parameters:
- This password is hardcoded in the apk, it cannot be changed.
- Discovered passwords:
    - Sermatec2021
    - sermatec2021 - confirmed working in the app version 1.7.5
    - Sermatec2015
    - Sermatec2019@Gsstes2019 - used as a RC4 key

Inverter's open ports:
- 23: telnet
- 80: UART-TCP module web config
    - username: admin
    - password: admin
- 8000: ?
- 8899: API port (this protocol)

## Protocol format
- All values are represented in the SI units (ampere, volt, watt, volt-ampere, volt-ampere reactive, hertz...).
- Some columns have different meaning for different inverter models, this document uses following abbreviations of these types:
    - 10K = 10 kW hybrid inverter,
    - 6K = 6 kW hybrid inverter,
    - 5K = 5 kW hybrid inverter.

### Data types
A majority of values are integers represented by big-endian (hi-lo, MSB first) bytes:
- u16: unsigned two-byte integer
- s16: signed two-byte integer
- u16/x: fixed-point fractional unsigned integer = multiply the value *converted to base 10* by 1/x to get the result, examples:
    - value 0x5432 of a type u16/10 is 21554 in base 10, mutiplied by 1/10 is 2155.4.
- enum: only listed values are valid

However, some responses (e.g. 0x0c) contains flags represented as bits - bit positions are indexed from lowest bit starting from 0:

```
76543210 (position)
||||||||
vvvvvvvv
00000000 (byte)
```

Some bits are unused - in that case the default value is marked as "default" and the other one as "-".



### Request format
- All *get* requests have the same structure - standard header, empty payload (no data) and then a checksum and a footer. Because of that, particular requests are not described again.
- *Set* requests have additionally some values in their payload. Thus, payload format is always described at every command byte by byte with a table or a description of allowed values.

| Byte | Value |
| ---- | ----- |
| 0    | `0xfe`  |
| 1    | `0x55`  |
| 2    | source (`0x64`) |
| 3    | target (`0x14`) |
| 4 | command |
| 5 | `0x00` |
| 6    | message length |
| 7-n  | data (payload) |
| n+1  | checksum |
| n+2  | `0xae` |

### Response format
- For now, bytes in responses are addressed from the start of the message (including the header, so 0x07 offset).

| Byte | Value |
| ---- | ----- |
| 0    | `0xfe`  |
| 1    | `0x55`  |
| 2    | source (`0x14`) |
| 3    | target (`0x64`) |
| 4 | command the inverter is responding to (= same as in preceeding request) |
| 5 | `0x00` |
| 6    | message length |
| 7-n  | data (payload) |
| n+1  | checksum |
| n+2  | `0xae` |

## Commands
| Command (in big-endian) | Function |
| ----------------------- | -------- |
| `0x0a` | *Get* battery information. |
| `0x0b` | *Get* PV, grid, backup and other status. |
| `0x0c` | *Get* inverter status. |
| `0x0d` | *Get* load value and BMS/meter connection status. |
| `0x66` | *Set* working parameters. |
| `0x68` | *Set* current date and time. |
| `0x95` | *Get* working parameters. |
| `0x98` | *Get* system information. |

### **`0x98`: Get system information**
**Response:**
| Address | Meaning | Data type |
| ----    | ------- | --------- |
| 0x07 | PCU version | u16 |
| 0x09 | ? | ? |
| 0x0B | ? | ? |
| 0x0D | Serial ID string. | string (null-terminated, max length 44 bytes) |

### **`0x68`: Send current date and time**
YEAR[2];MONTH;DAY;HOUR;MINUTES;SECONDS

### **`0x0a`: Battery information**
**Response:**
| Address | Meaning | Data type |
| ---- | ------- | --------- |
| 0x07 | Battery voltage. | u16/10 |
| 0x09 | Battery current. | s16/10 |
| 0x0B | Battery temperature. | u16/10 |
| 0x0D | Battery state of charge. | u16 |
| 0x0F | Battery state of health. | u16 |
| 0x11 | Battery state (see note). | u16 |
| 0x13 | Battery maximal charging current. | u16/10 |
| 0x15 | Battery maximal discharging current. | u16/10 |
| 0x17 | Charging cut-off voltage. | u16/10 |
| 0x19 | Discharging cut-off voltage. | u16/10 |
| 0x1B | Charging/discharging times. | u16 |
| 0x1D | Battery pressure. | u16 |
| 0x1F | Battery warning. | u16 |
| 0x21 | Battery error. | u16 |
| 0x23 | Battery communication status. | u16 |

Battery states:
- 0x0011: charging
- 0x0022: discharging
- 0x0033: stand-by

### **`0x0b`: Grid, PV and backup information**
**Response:**
| Address | Meaning | Data type |
| ------- | ------- | --------- |
| 0x07 | PV1 voltage. | u16/10 |
| 0x09 | PV1 current. | u16/10 |
| 0x0B | PV1 power. | u16 |
| 0x0D | PV2 voltage. | u16/10 |
| 0x0F | PV2 current. | u16/10 |
| 0x11 | PV2 power. | u16 |
| 0x13 | Inverter phase A voltage. | u16/10 |
| 0x15 | Inverter phase A current. | s16/10 |
| 0x17 | Grid phase A voltage. | u16/10 
| 0x19 | Grid AB line voltage | u16/10 |
| 0x1B | Grid phase A current. | s16/10 |
| 0x1D | Inverter phase B voltage. | u16/10 |
| 0x1F | Inverter phase B current. | s16/10 |
| 0x21 | Grid phase B voltage. | u16/10 |
| 0x23 | Grid BC line voltage. | u16/10 |
| 0x25 | Grid phase B current. | s16/10 |
| 0x27 | Inverter phase C voltage. | u16/10 |
| 0x29 | Inverter phase C current. | s16/10 |
| 0x2B | Grid phase C voltage. | u16/10 |
| 0x2D | Grid CA line voltage. | u16/10 |
| 0x2F | Grid phase C current. | s16/10 |
| 0x31 | Grid (mains) frequency. | u16/100 |
| 0x33 | Grid power factor. | s16/1000) |
| 0x35 | Grid active power. | s16 |
| 0x37 | Grid reactive power. | s16 |
| 0x39 | Grid apparent power. | s16 |
| 0x3B | Battery current. | s16/10 |
| 0x3D | Battery voltage. | s16/10 |
| 0x3F | DC positive bus voltage. | u16/10 |
| 0x41 | DC negative bus voltage. | u16/10 |
| 0x43 | DC bilateral bus voltage. | u16/10 |
| 0x45 | DC power. | s16 |
| 0x47 | Inverter internal temperature. | u16/10 |
| 0x49 | 10K: DC positive bus backup voltage. 5K/6K: Secondary bus 1. | u16/10 |
| 0x4B | 10K: DC negative bus backup voltage. 5K/6K: Secondary bus 2. | u16/10 |
| 0x4D | Device type encoding. | u16 |
| 0x4F | Inverter SW version - high digits. | u16 |
| 0x51 | Inverter SW version - low digits. | u16 |
| 0x53 | Parallel address. | u16 |
| 0x55 | Inverter efficiency. | u16 |
| 0x57 | Battery current 1. | s16/10 |
| 0x59 | Battery current 2. | s16/10 |
| 0x5B | Module A1 temperature. | s16/10 |
| 0x5D | Module B1 temperature. | s16/10 |
| 0x5F | Module C1 temperature. | s16/10 |
| 0x61 | Backup Phase A voltage. | u16/10 |
| 0x63 | Backup Phase B voltage. | u16/10 |
| 0x65 | Backup Phase C voltage. | u16/10 |
| 0x67 | Backup frequency. | u16/10 (scaling 1/100) |
| 0x69 | Backup Phase A current. | s16/10 |
| 0x6B | Backup Phase B current. | s16/10 |
| 0x6D | Backup Phase C current. | s16/10 |
| 0x6F | Backup power factor. | s16/1000) |
| 0x71 | Backup active power. | s16 |
| 0x73 | Backup reactive power. | s16 |
| 0x75 | Backup apparent power. | s16 |

### **`0x0c`: Get inverter status**
**Response:**
This reponse consists of flags (see Data types). Only bold values' meaning are verified.

| Address | Bit position | =1 | =0 | =other |
| ------- | ------------ | -- | -- | ---- |
| 0x07 | 0 | default | - | - |
| 0x07 | 1 | **Grid is unavailable.** | **Grid is available.** | - |
| 0x07 | 2 | Power derating on. | Power derating off. | - |
| 0x07 | 3 | **Parallel connection mode.** | **Single inverter mode.** | - |
| 0x07 | 4 | Inverter is a slave unit. | Inverter is a master unit. | - |
| 0x07 | 5 | Active mode. | Passive mode. | - |
| 0x07 | 6-7 | - | - | =01 - OK, other states unknown. |
| 0x08 | 0-2 | - | - | AC side running status. Meanings of the values unknown. |
| 0x08 | 3 | Relay self-test on. | Relay self-test off. |
| 0x08 | 4-6 | - | - | AC side operation mode. |
| 0x08 | 7 | - | - | Only described as a "switch", probably hw switch state? |

`0x09-0x0A` is a PV status word (some debugging info).

### **`0x0d`: Get load value and BMS/meter connection status**
**Response:**
| Address | Meaning | Data type |
| ------- | ------- | --------- |
| 0x07 | BMS connection status. | s16 |
| 0x09 | Meter connection status. | s16 |
| 0x0B | Current load (power consumption). | s16 |

### **`0x95`: Get working parameters**
**Response:**
| Address | Meaning | Data type |
| ------- | ------- | --------- |
| 0x0F | Upper limit of on-grid power. | u16 |
| 0x13 | Working mode. | u16 (see note) |
| 0x1D | Lower limit of on-grid SOC. | u16 |

Working modes:
- 0x0001: General Mode
- 0x0002: Energy Storage Mode
- code for another three modes is unknown (unable to test)

### **`0x64`: Set on/off mode**
**Request payload:**
- 0x00: Inverter running mode (on/off)
    - enum:

    | Value | Meaning |
    | ----- | ------- |
    | 0xaa  | Turn off the inverter |
    | 0x55  | Turn on the inverter |

**Response:** none

### **`0x66`: Set working parameters**
Until we know meanings of all values, it is a good idea to 

**Request payload:**
- 0x00: Electricity price (tip)
    - s16/10
- 0x02: Electricity price (peak)
    - s16/10
- 0x04: Electricity price (flat)
    - s16/10
- 0x06: Electricity price (valley)
    - s16/10
- 0x08: On-grid power limit
    - s16
- 0x0A: "Battery charge and discharge power" (???)
    - s16
- 0x0C: Working mode
    - enum

    | Value   | Meaning |
    | -----   | ------- |
    | 0x0001  | General Mode |
    | 0x0002  | Energy Storage Mode |
    | 0x0003  | TBA |
    | 0x0004  | TBA |
    | 0x0005  | TBA |

- 0x0E: "PV and off-grid" (???)
    - s16
- 0x0F: 3-phase unbalanced output
    - probably two-value enum, in app it's represented by a switch
- 0x11: "Battery charge and discharge power" again (???)
    - s16
- 0x13: on-grid battery SOC lower limit in %
    - s16 (0 - 100)
- 0x15: off-grid SOC lower limit in %
    - s16 (0 - 100)
- 0x17: Meter detection
    - probably two-value enum
- 0x19-0x32: Reserved, begins with `0x05 0x9f 0x00 0x03` and then contains zeroes.
- 0x33: Total number of records

**Response:** none

### **`0x1e`: BMS alarm information display**
TODO

### **`0x1f`: System failure status display**
TODO

## Checksum
The checksum is calculated with a simple formula: xor all bytes until the checksum byte position, then xor with `0f`.

See following pseudocode:
```
let checksum = 0x0f
let data = a part of a request to or response from inverter
for every byte in data:
    checksum = checksum ⊻ byte
```

Example: let's calculate a checksum for the battery information request. The header stays the same, the command is 0x0a followed by 0x00 and the message length is 0. The message looks like this: `fe 55 64 14 0a 00 00`. Checksum will be calculated using the formula above: 0f ⊻ fe ⊻ 55 ⊻ 64 ⊻ 14 ⊻ 0a ⊻ 00 ⊻ 00 = de. We will attach the checksum and the header to the message and we are finished: `fe 55 64 14 0a 00 00 de ae`.