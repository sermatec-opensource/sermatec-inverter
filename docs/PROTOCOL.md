# Protocol description
This protocol is used by the *Sermatec* application (available for Android and iOS) for a local connection to the inverter via built-in WiFi access point or via LAN connection.

Default AP's password is `gsstes123456`.

Distributor's (admin) passwords for setting parameters:
- This password is hardcoded in the apk, it cannot be changed.
- Discovered passwords:
    - Sermatec2021
    - sermatec2021 - confirmed working in the app version 1.7.5
    - Sermatec2015
    - Sermatec2019@Gsstes2019 - used as a RC4 key

Integers are presented in the big-endian format (MSB first).

Inverter's open ports:
- 23: telnet
- 80: UART-TCP module web config
    - username: admin
    - password: admin
- 8000: ?
- 8899: API port (this protocol)

## Request Datagram format
| Address | Length                 | Description       | Value                             |
|---------|------------------------|-------------------|-----------------------------------|
| 0-1     | 2 bytes                | Preamble          | `0xfe55`                          |
| 2       | 1 byte                 | Source Identifier | `0x64`                            |
| 3       | 1 byte                 | Target Identifier | `0x14`                            |
| 4-5     | 2 bytes                | Command           | [See Commands section](#commands) |
| 6       | 1 byte                 | Message Length    | **Varying**                       |
| 7-n     | *Message Length* bytes | Message           | **Varying**                       |
| n+1     | 1 byte                 | Checksum          | [See Checksum section](#checksum) |
| n+2     | 1 byte                 | Termination byte  | `0xae`                            |

## Response Datagram format

It is the same but the source and target addresses are swapped.

| Address | Length                 | Description                               | Value                             |
|---------|------------------------|-------------------------------------------|-----------------------------------|
| 0-1     | 2 bytes                | Preamble                                  | `0xfe55`                          |
| 2       | 1 byte                 | Target Identifier                         | `0x14`                            |
| 3       | 1 byte                 | Source Identifier                         | `0x64`                            |
| 4-5     | 2 bytes                | Command that the response is answering to | [See Commands section](#commands) |
| 6       | 1 byte                 | Message Length                            | **Varying**                       |
| 7-n     | *Message Length* bytes | Message                                   | **Varying**                       |
| n+1     | 1 byte                 | Checksum                                  | [See Checksum section](#checksum) |
| n+2     | 1 byte                 | Termination byte                          | `0xae`                            |

Notes: 
- integers are represented in the big-endian format.
- fractional numbers (with exceptions) are represented in the fixed-point, scaling 1/10.
- all values are represented in the SI units (ampere, volt, watt, volt-ampere, volt-ampere reactive, hertz...).
- data type uint16_t at address `0x00` means hi-lo integer stored at bytes 0-1.

## Commands
| Command (in big-endian) | Function                    |
|-------------------------|-----------------------------|
| `0x9800`                | Get system information.     |
| `0x6800`                | Send current date and time. |
| `0x0a00`                | Get battery information.    |
| `0x0b00`                | Get grid status.            |
| `0xbb00`                | ?                           |
| `0x0c00`                | ?                           |
| `0x0d00`                | Get load information.       |
| `0x9500`                | Get working parameters.     |
| `0x6600`                | Set working parameters.     |

### `0x9800`: Get system information
**Request example:** `fe 55 64 14 98 00 00 4c ae`

**Request message:** `0x00`

**Response message:**

| Address in message block | Length       | Meaning           | Data type                                     |
|--------------------------|--------------|-------------------|-----------------------------------------------|
| 0-1                      | 2 bytes      | PCU version       | unsigned int16                                |
| 2-5                      | 4 bytes      | ??                | ??                                            |
| 6-n (until `0x00`)       | varying size | Serial ID string. | string (null-terminated, max length 44 bytes) |

### `0x6800`: Send current date and time
**Request example:** `fe 55 64 14 68 00 ?? ?? ae`

**Request Message:** YEAR[2];MONTH;DAY;HOUR;MINUTES;SECONDS

**Response Message:** Still unknown

### `0x0a00`: Battery information
**Request example:** `fe 55 64 14 0a 00 00 de ae`

**Request message:** `0x00`

**Response message:**

| Address in message block | Length  | Meaning                              | Data type                                |
|--------------------------|---------|--------------------------------------|------------------------------------------|
| 0-1                      | 2 bytes | Battery voltage.                     | unsigned int16 fractional (scaling 1/10) |
| 2-3                      | 2 bytes | Battery current.                     | signed int16 fractional (scaling 1/10)   |
| 4-5                      | 2 bytes | Battery temperature.                 | unsigned int16 fractional (scaling 1/10) |
| 6-7                      | 2 bytes | Battery state of charge.             | unsigned int16                           |
| 8-9                      | 2 bytes | Battery state of health.             | unsigned int16                           |
| 10-11                    | 2 bytes | Battery state (see note).            | unsigned int16                           |
| 12-13                    | 2 bytes | Battery maximal charging current.    | unsigned int16 fractional (scaling 1/10) |
| 14-15                    | 2 bytes | Battery maximal discharging current. | unsigned int16 fractional (scaling 1/10) |

Battery states:
- `0x0011`: charging
- `0x0022`: discharging
- `0x0033`: stand-by

### `0x0b00`: Grid, PV and backup information
**Request example:** `fe 55 64 14 0b 00 00 df ae`

**Request message:** `0x00`

**Response message:**

| Address in message block | Length   | Meaning                   | Data type                                 |
|--------------------------|----------|---------------------------|-------------------------------------------|
| 0-1                      | 2 bytes  | PV1 voltage.              | unsigned int16 fractional (scaling 1/10)  |
| 2-3                      | 2 bytes  | PV1 current.              | unsigned int16 fractional (scaling 1/10)  |
| 4-5                      | 2 bytes  | PV1 power.                | unsigned int16                            |
| 6-7                      | 2 bytes  | PV2 voltage.              | unsigned int16 fractional (scaling 1/10)  |
| 8-9                      | 2 bytes  | PV2 current.              | unsigned int16 fractional (scaling 1/10)  |
| 10-11                    | 2 bytes  | PV2 power.                | unsigned int16                            |
| 12-13                    | 2 bytes  | Inverter Phase A voltage. | unsigned int16 fractional (scaling 1/10)  |
| 14-15                    | 2 bytes  | Inverter Phase A current. | signed int16 fractional (scaling 1/10)    |
| 16-17                    | 2 bytes  | Grid Phase A voltage.     | unsigned int16 fractional (scaling 1/10)  |
| 18-19                    | 2 bytes  | Grid Line AB voltage.     | unsigned int16 fractional (scaling 1/10)  |
| 20-21                    | 2 bytes  | Grid phase A current.     | signed int16 fractional (scaling 1/10)    |
| 22-23                    | 2 bytes  | Inverter Phase B voltage. | unsigned int16 fractional (scaling 1/10)  |
| 24-25                    | 2 bytes  | Inverter Phase B current. | signed int16 fractional (scaling 1/10)    |
| 26-27                    | 2 bytes  | Grid Phase B voltage.     | unsigned int16 fractional (scaling 1/10)  |
| 28-29                    | 2 bytes  | Grid line BC voltage.     | unsigned int16 fractional (scaling 1/10)  |
| 30-31                    | 2 bytes  | Grid Phase B current.     | signed int16 fractional (scaling 1/10)    |
| 32-23                    | 2 bytes  | Inverter Phase C voltage. | unsigned int16 fractional (scaling 1/10)  |
| 34-35                    | 2 bytes  | Inverter Phase C current. | signed int16 fractional (scaling 1/10)    |
| 36-37                    | 2 bytes  | Grid Phase C voltage.     | unsigned int16 fractional (scaling 1/10)  |
| 38-39                    | 2 bytes  | Grid line CA voltage.     | unsigned int16 fractional (scaling 1/10)  |
| 40-41                    | 2 bytes  | Grid Phase C current.     | signed int16 fractional (scaling 1/10)    |
| 42-43                    | 2 bytes  | Grid (mains) frequency.   | unsigned int16 fractional (scaling 1/100) |
| 44-45                    | 2 bytes  | Power Factor              | signed int16 fractional (scaling 1/1000)  |
| 46-47                    | 2 bytes  | Grid active power.        | signed int16                              |
| 48-49                    | 2 bytes  | Grid reactive power.      | signed int16                              |
| 50-51                    | 2 bytes  | Grid apparent power.      | signed int16                              |
| 52-69                    | 16 bytes | ??                        | ??                                        |
| 70-71                    | 2 bytes  | Device Type Code          | unsigned int16                            |
| 72-73                    | 2 bytes  | DSP Version High          | unsigned int16                            |
| 74-75                    | 2 bytes  | DSP Version Low           | unsigned int16                            |
| 90-91                    | 2 bytes  | Load Phase A voltage.     | unsigned int16 fractional (scaling 1/10)  |
| 92-93                    | 2 bytes  | Load Phase B voltage.     | unsigned int16 fractional (scaling 1/10)  |
| 94-95                    | 2 bytes  | Load Phase C voltage.     | unsigned int16 fractional (scaling 1/10)  |
| 96-97                    | 2 bytes  | Load frequency.           | unsigned int16 fractional (scaling 1/100) |
| 98-99                    | 2 bytes  | Load Phase A current.     | signed int16 fractional (scaling 1/10)    |
| 100-101                  | 2 bytes  | Load Phase B current.     | signed int16 fractional (scaling 1/10)    |
| 102-103                  | 2 bytes  | Load Phase C current.     | signed int16 fractional (scaling 1/10)    |
| 104-105                  | 2 bytes  | Load Power Factor         | signed int16 fractional (scaling 1/1000)  |
| 106-107                  | 2 bytes  | Load active power.        | signed int16                              |
| 108-109                  | 2 bytes  | Load reactive power.      | signed int16                              |
| 110-111                  | 2 bytes  | Load apparent power.      | signed int16                              |

### `0x0d00`: Get load information
**Request example:** `fe 55 64 14 0d 00 00 d9 ae`

**Request Message:** `0x00`

**Response Message:**

| Address in message block | Length  | Meaning                           | Data type    |
|--------------------------|---------|-----------------------------------|--------------|
| 3-4                      | 2 bytes | Current load (power consumption). | signed int16 |

### `0x9500`: Get working parameters
**Request Example:** `fe 55 64 14 95 00 00 41 ae`

**Request Message:** `0x00`

**Response Message:**

| Address in message block | Length  | Meaning                       | Data type               |
|--------------------------|---------|-------------------------------|-------------------------|
| 0-7                      | 6 bytes | ??                            | ??                      |
| 8-9                      | 2 bytes | Upper limit of on-grid power. | signed int16            |
| 10-11                    | 2 bytes | ??                            | ??                      |
| 12-13                    | 2 bytes | Working mode.                 | signed int16 (see note) |
| 14-21                    | 8 bytes | ??                            | ??                      |
| 22-23                    | 2 bytes | Lower limit of on-grid SOC.   | signed int16            |

Working modes:
- `0x0001`: General Mode
- `0x0002`: Energy Storage Mode
- code for another three modes is unknown (unable to test)

### `0x6600`: Set working parameters
**Request:**

| Address   | Meaning                             | Content               |
|-----------|-------------------------------------|-----------------------|
| 0x00      | Header.                             | `0xfe 0x55 0x64 0x14` |
| 0x04      | Command.                            | `0x66 0x00`           |
| 0x06      | Size.                               | `0x20`                |
| 0x07-0x0E | Zeroes.                             | `00...`               |
| 0x0F      | Upper limit of on-grid power.       | value as uint16_t     |
| 0x11-0x12 | Zeroes.                             | `00...`               |
| 0x13      | Working mode. See note at `0x9500`. | value as uint16_t     |
| 0x15-0x18 | Zeroes.                             | `00...`               |
| 0x19      | Unknown.                            | `0x00ee`              |
| 0x1B-0x1C | Zeroes.                             | `00...`               |
| 0x1D      | Lower limit of on-grid SOC.         | value as uint16_t     |
| 0x1F      | Unknown.                            | `0x0001`              |
| 0x21      | Unknown.                            | `0x0000`              |
| 0x23      | Unknown.                            | `0x059F`              |
| 0x25      | Unknown.                            | `0x0003`              |
| 0x27      | Checksum.                           | ?                     |
| 0x28      | Footer.                             | `0xAE`                |

**Response:** none

### `0x1e00`: Error
### `0xbb00`: Error

## Checksum
The checksum is calculated with a simple formula: xor all bytes until the checksum byte position, then xor with `0f`.

See following pseudocode:
```
let checksum = 0x0f
let data = a part of a request to or response from inverter
for every byte in data:
    checksum = checksum ⊻ byte
```

**Example:**

Let's calculate a checksum for the battery information request.
The header stays the same, the command is 0x0a followed by `0x00` and the message length is 0.
The message looks like this: `fe 55 64 14 0a 00 00`.
Checksum will be calculated using the formula above: `0f` ⊻ `fe` ⊻ `55` ⊻ `64` ⊻ `14` ⊻ `0a` ⊻ `00` ⊻ `00` = `de`.
We will attach the checksum and the header to the message, and we are finished: `fe 55 64 14 0a 00 00 de ae`.
