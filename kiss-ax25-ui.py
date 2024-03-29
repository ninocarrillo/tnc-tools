# kiss-ax25-ui
# Python3
# Generate a single KISS-encapsulated AX.25 UI frame and send to the serial port.
# Nino Carrillo
# 24 Feb 2023
# Exit codes
# 1 Wrong python version
# 2 Not enough command line arguments
# 3 Unable to open serial port
# 4 Source callsign is invalid
# 5 Destination callsign is invalid

import serial
import sys
import time

def GracefulExit(port, code):
	try:
		port.close()
	except:
		pass
	finally:
		#print('Closed port ', port.port)
		sys.exit(code)

def StringCallsignToArray(input_string, error_string, error_code):
	output = [32, 32, 32, 32, 32, 32, 0]
	callsign_length = 0
	ssid_digits = 0
	ssid = [0,0]
	currently_reading = 'callsign'
	input_string = input_string.upper()
	input_string = bytes(input_string, 'UTF-8')
	for character in input_string:
		if currently_reading == 'callsign':
			if character == bytes('-', 'UTF-8')[0]:
				currently_reading = 'ssid'
			else:
				output[callsign_length] = int(character)
				callsign_length += 1
				if callsign_length == 6:
					currently_reading = 'hyphen'
				# print(output)
		elif currently_reading == 'hyphen':
			if character != bytes('-', 'UTF-8')[0]:
				print(error_string)
				sys.exit(error_code)
			currently_reading = 'ssid'
		elif currently_reading == 'ssid':
			ssid[ssid_digits] = character - bytes('0', 'UTF-8')[0]
			ssid_digits += 1
			# print(ssid)
	if ssid_digits == 1:
		ssid = ssid[0]
	elif ssid_digits == 2:
		ssid = ssid[0] * 10 + ssid[1]
	else:
		ssid = 0
	if ssid > 16:
		ssid = 16
	if ssid < 0:
		ssid = 0
	output[6] = ssid
	return output

if sys.version_info < (3, 0):
	print("Python version should be 3.x, exiting")
	sys.exit(1)

if len(sys.argv) < 4:
	print('Not enough arguments. Usage prototype below. Enclose payload in "double quotes" if it contains whitespace.\r\npython3 kiss-ax25-ui.py <serial device> <baud rate> <src call-ssid> <optional dest call-ssid> <optional payload>')
	sys.exit(2)

try:
	port = serial.Serial(sys.argv[1], baudrate=sys.argv[2], bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0, timeout=3)
except:
	print('Unable to open serial port.')
	sys.exit(3)

source_callsign = StringCallsignToArray(sys.argv[3], 'Source Callsign or SSID is invalid.', 4)

if len(sys.argv) > 4:
	dest_callsign = sys.argv[4]
else:
	dest_callsign = 'IDENT-0'
dest_callsign = StringCallsignToArray(dest_callsign, 'Destination Callsign or SSID is invalid.', 5)
#print(source_callsign)
#print(dest_callsign)

FESC = int(0xDB).to_bytes(1,'big')
FEND = int(0xC0).to_bytes(1,'big')
TFESC = int(0xDD).to_bytes(1,'big')
TFEND = int(0xDC).to_bytes(1,'big')
KISS_PORT = 0
KISS_COMMAND = 0
KISS_TYPE_ID = (KISS_PORT * 16) + KISS_COMMAND
KISS_TYPE_ID = KISS_TYPE_ID.to_bytes(1,'big')

# Assemble KISS frame:
kiss_frame = bytearray()
# Add destination callsign, shifted left one bit:
for i in range(6):
	kiss_frame.extend((dest_callsign[i]<<1).to_bytes(1,'big'))
# Add destination SSID:
kiss_frame.extend(((dest_callsign[6] & 0xF)<<1).to_bytes(1,'big'))
# Add source callsign, shifted left one bit:
for i in range(6):
	kiss_frame.extend((source_callsign[i]<<1).to_bytes(1,'big'))
# Add source SSID with Address Extension Bit:
kiss_frame.extend((((source_callsign[6] & 0xF) << 1) | 1).to_bytes(1,'big'))

# Add Control field for UI:
kiss_frame.extend((0x03).to_bytes(1,'big'))
# Add PID for No Layer 3:
kiss_frame.extend((0xF0).to_bytes(1,'big'))
# Add payload:
try:
	payload = bytes(sys.argv[5], 'UTF-8')
except:
	payload = bytearray()
kiss_frame.extend(payload)
#print(kiss_frame)

frame_index = 0
kiss_output_frame = bytearray()
while(frame_index < len(kiss_frame)):
	kiss_byte = kiss_frame[frame_index]
	if kiss_byte.to_bytes(1,'big') == FESC:
		kiss_output_frame.extend(FESC)
		kiss_output_frame.extend(TFESC)
	elif kiss_byte.to_bytes(1, 'big') == FEND:
		kiss_output_frame.extend(FESC)
		kiss_output_frame.extend(TFEND)
	else:
		kiss_output_frame.extend(kiss_byte.to_bytes(1, 'big'))
	frame_index += 1
kiss_output_frame = bytearray(FEND) + bytearray(KISS_TYPE_ID) + kiss_output_frame + bytearray(FEND)
# print(kiss_output_frame)
frame_time = len(kiss_output_frame) * 10 / int(sys.argv[2])
port.write(kiss_output_frame)
time.sleep(frame_time * 1.5)
GracefulExit(port, 0)
