# tnc-tools
Utilities for interfacing with N9600A NinoTNC and other generic KISS TNCs connected over serial port.
# Requirements
- Python3
- Pyserial
# Command Descriptions
## n9600a-cmd.py
Usage: `python3 n9600a-cmd.py <serial device> <command> <optional value>`

Send command frames to an N9600A NinoTNC attached to the specified serial port. Invoke without arguments for a list of available commands. The serial number of the TNC must be clear before it can be set. Use CLRSERNO to clear it. 

Example without argument:
````
C:\github\tnc-tools>py -3 n9600a-cmd.py com18
Not enough arguments. Usage prototype below.
python3 n9600a-cmd.py <serial device> <command> <optional value>
Available commands:
CLRSERNO               : Erases the stored TNC serial number. Perform before SETSERNO.
SETSERNO xxxxxxxx      : Sets the TNC serial number, value is 8 ASCII characters.
GETSERNO               : Queries and displays the TNC serial number.
SETBCNINT nnn          : Sets the beacon interval, value is minutes 0 to 255. 0 disables.
GETVER                 : Queries and displays the TNC firmware version.
STOPTX                 : Stop the current transmission and flush queues.
GETALL                 : Dump diagnostic data.
SETPERSIST nnn         : Set CSMA persistance value, 0 to 255.
SETSLOT nnn            : Set CSMA slot time in 10mS units, 0 to 255.

````
Example GETVER:
````
C:\github\tnc-tools>py -3 n9600a-cmd.py com18 getver
4.21
````
Example SETSERNO and GETSERNO:
````
C:\github\tnc-tools>py -3 n9600a-cmd.py com18 setserno ABc12D9x

C:\github\tnc-tools>py -3 n9600a-cmd.py com18 getserno
ABc12D9x
````

## kiss-listen.py
Usage: `python3 kiss-listen.py <serial device> <baud rate>`

Listen for kiss frames on the specified serial port and display them on the console. Each frame is displayed as printable characters, raw byte values, and an AX.25 decode. Frames are given a date/time stamp, as well as a count index. Number of bytes in the frame is displayed as well. Press CTRL-C to exit. 

Example:

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
## kiss-ax25-ui.py
Usage: `python3 kiss-ax25-ui.py <serial device> <baud rate> <src call-ssid> <optional dest call-ssid> <optional payload>`

Generate a single AX.25 un-numbered information packet, like an APRS packet, and send it to the specified serial port with KISS encapsulation. Only the serial device, baud rate, and source callsign arguments are requred. Destination callsign will default to "IDENT-0" if omitted. Payload argument should be enclosed in double quotes if it contains whitespace. 

Minimum argument example:
````
C:\github\tnc-tools>py -3 kiss-ax25-ui.py com18 57600 kk4hej-4
````
At the receiver, this generates a packet that looks like:
````
-- 2023-03-15 14:13:13.365019 frame number: 27 byte count:  17
......@`..h..... |  0 92 88 8A 9C A8 40 60 96 96 68 90 8A 94 E9  3
.                | F0
- AX.25 Decode:
To:IDENT-0, From:KK4HEJ-4, Control: UI, PID: No Layer 3
````
Example with a payload:
````
C:\github\tnc-tools>py -3 kiss-ax25-ui.py com18 57600 kk4hej-4 aprs ":payload can be an APRS information field"
````
Received packet:
````
-- 2023-03-15 14:16:40.761511 frame number: 30 byte count:  58
.....@@`..h..... |  0 82 A0 A4 A6 40 40 60 96 96 68 90 8A 94 E9  3
.:payload can be | F0 3A 70 61 79 6C 6F 61 64 20 63 61 6E 20 62 65
 an APRS informa | 20 61 6E 20 41 50 52 53 20 69 6E 66 6F 72 6D 61
tion field       | 74 69 6F 6E 20 66 69 65 6C 64
- AX.25 Decode:
To:APRS-0, From:KK4HEJ-4, Control: UI, PID: No Layer 3
:payload can be an APRS information field
````
## kiss-ax25-ui-batch.py
Usage: `python3 kiss-ax25-ui-batch.py <serial device> <baud rate> <src call-ssid> <dest call-ssid> <frame count> <payload text> <payload length> <frame interval>`
Generate a sequence of un-numbered information frames and send them to the serial port at the specified interval. Useful for testing links and bench testing TNCs and radios. Program accepts a payload text argument, as well as a payload length argument. If the payload length requested is longer than the supplied payload text (plus an added frame index) then the program extends each payload with random printable characters to meet the requested payload length.

Example:
````
C:\github\tnc-tools>py -3 kiss-ax25-ui-batch.py com18 57600 kk4hej-4 test 3 "-115dBm GFSK 9600 IL2P " 53 1
````
On the receive side:
````
C:\github\tnc-tools>py -3 kiss-listen.py com6 57600
Opened port com6

-- 2023-03-15 14:26:21.038707 frame number: 1 byte count:  70
.....@@`..h..... |  0 A8 8A A6 A8 40 40 60 96 96 68 90 8A 94 E9  3
.-115dBm GFSK 96 | F0 2D 31 31 35 64 42 6D 20 47 46 53 4B 20 39 36
00 IL2P 1 S@l/aG | 30 30 20 49 4C 32 50 20 31 20 53 40 6C 2F 61 47
vuH<s,2Td/$UYg/  | 76 75 48 3C 73 2C 32 54 64 2F 24 55 59 67 2F 20
f5hER*           | 66 35 68 45 52 2A
- AX.25 Decode:
To:TEST-0, From:KK4HEJ-4, Control: UI, PID: No Layer 3
-115dBm GFSK 9600 IL2P 1 S@l/aGvuH<s,2Td/$UYg/ f5hER*

-- 2023-03-15 14:26:22.065947 frame number: 2 byte count:  70
.....@@`..h..... |  0 A8 8A A6 A8 40 40 60 96 96 68 90 8A 94 E9  3
.-115dBm GFSK 96 | F0 2D 31 31 35 64 42 6D 20 47 46 53 4B 20 39 36
00 IL2P 2 J`yPUP | 30 30 20 49 4C 32 50 20 32 20 4A 60 79 50 55 50
KBe!QP,&DRFX$s(_ | 4B 42 65 21 51 50 2C 26 44 52 46 58 24 73 28 5F
5I:3cq           | 35 49 3A 33 63 71
- AX.25 Decode:
To:TEST-0, From:KK4HEJ-4, Control: UI, PID: No Layer 3
-115dBm GFSK 9600 IL2P 2 J`yPUPKBe!QP,&DRFX$s(_5I:3cq

-- 2023-03-15 14:26:23.078650 frame number: 3 byte count:  70
.....@@`..h..... |  0 A8 8A A6 A8 40 40 60 96 96 68 90 8A 94 E9  3
.-115dBm GFSK 96 | F0 2D 31 31 35 64 42 6D 20 47 46 53 4B 20 39 36
00 IL2P 3 ohhGn) | 30 30 20 49 4C 32 50 20 33 20 6F 68 68 47 6E 29
8[*r:zqfyG!R9zko | 38 5B 2A 72 3A 7A 71 66 79 47 21 52 39 7A 6B 6F
=W%.mJ           | 3D 57 25 2E 6D 4A
- AX.25 Decode:
To:TEST-0, From:KK4HEJ-4, Control: UI, PID: No Layer 3
-115dBm GFSK 9600 IL2P 3 ohhGn)8[*r:zqfyG!R9zko=W%.mJ
````
