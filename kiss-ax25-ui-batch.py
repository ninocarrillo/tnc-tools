# kiss-ax25-ui-batch
# Python3
# Generate a timed, numbered batch of KISS-encapsulated AX.25 UI frames and send to the serial port.
# Nino Carrillo
# 24 Feb 2023
# Exit codes
# 1 Wrong python version
# 2 Not enough command line arguments
# 3 Unable to open serial port
# 4 Source callsign is invalid
# 5 Destination callsign is invalid
# 6 Frame count is invalid
# 7 Payload text is invalid
# 8 Payload length is invalid
# 9 Frame interval is invalid

import serial
import sys
import time
import random

def GracefulExit(port, code):
	try:
		port.close()
	except:
		pass
	finally:
		#print('Closed port ', port.port)
		sys.exit(code)

def StringCallsignToArray(input_string, error_string, error_code):
	output = [0x20, 0x20, 0x20, 0x20, 0x20, 0x20, 0]
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

if len(sys.argv) < 9:
	print('Not enough arguments. Usage prototype below.\r\npython3 kiss-ax25-ui-batch.py <serial device> <baud rate> <src call-ssid> <dest call-ssid> <frame count> <payload text> <payload length> <frame interval>')
	sys.exit(2)

try:
	port = serial.Serial(sys.argv[1], baudrate=sys.argv[2], bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0, timeout=3)
except:
	print('Unable to open serial port.')
	sys.exit(3)

source_callsign = StringCallsignToArray(sys.argv[3], 'Source Callsign or SSID is invalid.', 4)

dest_callsign = StringCallsignToArray(sys.argv[4], 'Destination Callsign or SSID is invalid.', 5)

#print(source_callsign)
#print(dest_callsign)

try:
	frame_count = int(sys.argv[5])
except:
	print('Frame count argument is not an integer.')
	GracefulExit(port, 6)
	
try:
	payload_text = sys.argv[6]
except:
	print('Payload text is invalid.')
	GracefulExit(port, 7)
	
try:
	target_payload_length = int(sys.argv[7])
except:
	print('Payload length argument is not an integer.')
	GracefulExit(port, 8)
	
try:
	frame_interval = float(sys.argv[8])
except:
	print('Frame interval is not a number.')
	GracefulExit(port, 9)

FESC = int(0xDB).to_bytes(1,'big')
FEND = int(0xC0).to_bytes(1,'big')
TFESC = int(0xDD).to_bytes(1,'big')
TFEND = int(0xDC).to_bytes(1,'big')
KISS_PORT = 0
KISS_COMMAND = 0
KISS_TYPE_ID = (KISS_PORT * 16) + KISS_COMMAND
KISS_TYPE_ID = KISS_TYPE_ID.to_bytes(1,'big')

for i in range(0, frame_count):

	# Assemble KISS frame:
	kiss_frame = bytearray()
	# Add destination callsign, shifted left one bit:
	for j in range(6):
		kiss_frame.extend((dest_callsign[j]<<1).to_bytes(1,'big'))
	# Add destination SSID with CRR bits set
	kiss_frame.extend((((dest_callsign[6] & 0xF)<<1) | 0xE0).to_bytes(1,'big'))
	# Add source callsign, shifted left one bit:
	for k in range(6):
		kiss_frame.extend((source_callsign[k]<<1).to_bytes(1,'big'))
	# Add source SSID with Address Extension Bit and RR bits:
	kiss_frame.extend((((source_callsign[6] & 0xF) << 1) | 0x61).to_bytes(1,'big'))

	# Add Control field for UI:
	kiss_frame.extend((0x03).to_bytes(1,'big'))
	# Add PID for No Layer 3:
	kiss_frame.extend((0xF0).to_bytes(1,'big'))

	# save the length of the kiss frame for payload length computations later
	payload_length = len(kiss_frame)
	

	#kiss_frame.extend(payload)
	payload = bytearray(payload_text, 'UTF-8')
	kiss_frame.extend(payload)
	kiss_frame.extend(bytearray(str(i + 1), 'UTF-8'))
	kiss_frame.extend(bytearray(" ", 'UTF-8'))
	
	payload_length = len(kiss_frame) - payload_length
	#print(payload_length)

	# Pad payload to specified length:
	if payload_length < target_payload_length:
		payload = bytearray()
		for j in range(0, target_payload_length - payload_length):
			rand = random.randint(32,126)
			payload.extend(bytearray(rand.to_bytes(1,'big')))
		kiss_frame.extend(payload)
	
	print(f'\nFrame {i} content bytes:')
	character_counter = 0
	for character in kiss_frame:
		print(hex(character), end=' ')
		character_counter += 1
		if character_counter == 16:
			character_counter = 0
			print(f'\n', end='')
	sys.stdout.flush()

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
	time.sleep(frame_interval)
print('\nDone.')
GracefulExit(port, 0)