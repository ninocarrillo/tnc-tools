# tnc-tools
Utilities for interfacing with N9600A NinoTNC and other generic KISS TNCs connected over serial port.
# Requirements
- Python3
- Pyserial


`python3 n9600a-cmd.py <serial device> <command> <optional value>`

`python3 kiss-ax25-ui.py <serial device> <baud rate> <src call-ssid> <optional dest call-ssid> <optional payload>`

`python3 kiss-ax25-ui.py <serial device> <baud rate> <src call-ssid> <dest call-ssid> <frame count> <payload text> <payload length> <frame interval>`
# Command Descriptions
## kiss-listen.py
Usage: `python3 kiss-listen.py <serial device> <baud rate>`

This program listens for kiss frames on the specified serial port and displays them on the console. Each frame will be displayed as printable characters, raw byte values, and an AX.25 decode. The frames are given a date/time stamp, as well as a count index. The number of bytes in the frame is displayed as well. Press CTRL-C to exit. Example:

````
C:\github\tnc-tools>py -3 kiss-listen.py com6 57600
Opened port com6

-- 2023-03-15 14:00:19.604402 frame number: 1 byte count:  70
...d...j..h..... |  0 96 82 64 88 8A AE 6A 96 96 68 90 8A 94 E9  3
.GFSK 9600 IL2P  | F0 47 46 53 4B 20 39 36 30 30 20 49 4C 32 50 20
-120dBm 1 ~EBB&P | 2D 31 32 30 64 42 6D 20 31 20 7E 45 42 42 26 50
4"PPhaB'|%<kSHcp | 34 22 50 50 68 61 42 27 7C 25 3C 6B 53 48 63 70
FI^i;}           | 46 49 5E 69 3B 7D
- AX.25 Decode:
To:KA2DEW-5, From:KK4HEJ-4, Control: UI, PID: No Layer 3
GFSK 9600 IL2P -120dBm 1 ~EBB&P4"PPhaB'|%<kSHcpFI^i;}
````
