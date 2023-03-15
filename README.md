# tnc-tools
Utilities for interfacing with N9600A NinoTNC and other generic KISS TNCs connected over serial port.
# Requirements
- Python3
- Pyserial
# Usages
`python3 kiss-listen.py <serial device> <baud rate>`

`python3 n9600a-cmd.py <serial device> <command> <optional value>`

`python3 kiss-ax25-ui.py <serial device> <baud rate> <src call-ssid> <optional dest call-ssid> <optional payload>`

`python3 kiss-ax25-ui.py <serial device> <baud rate> <src call-ssid> <dest call-ssid> <frame count> <payload text> <payload length> <frame interval>`
