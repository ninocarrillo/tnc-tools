# kiss-ax25-ui
# Python3
# Generate a single KISS-encapsulated AX.25 UI frame and sen to the serial port.
# Nino Carrillo
# 23 Feb 2023
# Exit codes
# 1 Wrong python version
# 2 Not enough command line arguments
# 3 Unable to open serial port
# 4 Source callsign is invalid

import serial
import sys


def GracefulExit(port, code):
	try:
		port.close()
	except:
		pass
	finally:
		print('Closed port ', port.port)
		sys.exit(code)

def StringCallsignToArray(input_string, error_string, error_code):
	output = [20, 20, 20, 20, 20, 20, 0]

	callsign_length = 0
	ssid_digits = 0
	ssid = [0,0]
	currently_reading = 'callsign'
	input = bytes(input_string, 'UTF-8')
	for character in input:
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


if len(sys.argv) < 5:
	print('Not enough arguments. Usage: python3 kiss-ax25-ui.py <serial device> <baud rate> <src call-ssid> <dest call-ssid> <payload>')
	sys.exit(2)

try:
	port = serial.Serial(sys.argv[1], baudrate=sys.argv[2], bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0, timeout=3)
except:
	print('Unable to open serial port.')
	sys.exit(3)

print('Opened port', sys.argv[1])

source_callsign = StringCallsignToArray(sys.argv[3], 'Source Callsign or SSID is invalid.', 4)

dest_callsign = StringCallsignToArray(sys.argv[4], 'Destination Callsign or SSID is invalid.', 4)


print(source_callsign)
print(dest_callsign)

GracefulExit(port, 0)


try:
	frame_length = int(sys.argv[4])
except:
	print('Frame length argument is not an integer.')
	GracefulExit(port, 5)


print('Frame length = %d' % frame_length)

try:
	frame_interval = float(sys.argv[5])
except:
	print('Frame interval is not a number.')
	GracefulExit(port, 6)

print('Frame interval = %f' % frame_interval, ' seconds.')

FESC = int(0xDB).to_bytes(1,'big')
FEND = int(0xC0).to_bytes(1,'big')
TFESC = int(0xDD).to_bytes(1,'big')
TFEND = int(0xDC).to_bytes(1,'big')
KISS_PORT = 0
KISS_COMMAND = 0
KISS_TYPE_ID = (KISS_PORT * 16) + KISS_COMMAND
KISS_TYPE_ID = KISS_TYPE_ID.to_bytes(1,'big')

for i in range(0, frame_count):
	kiss_frame = bytearray()
	#kiss_frame = bytearray(FEND.to_bytes(1,'big'))
	frame_text = "KISS Frame "
	kiss_frame +=bytearray(frame_text.encode())
	frame_text = str(i + 1) + ' '
	kiss_frame.extend(bytearray(frame_text.encode()))
	extend_length = frame_length - len(kiss_frame)
	rand_bytes = bytearray()
	for j in range(0, extend_length):
		rand = random.randint(32,126)
		rand_bytes.extend(bytearray(rand.to_bytes(1,'big')))
	kiss_frame.extend(rand_bytes)
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
	print(kiss_output_frame)
	port.write(kiss_output_frame)
	time.sleep(frame_interval)

GracefulExit(port, 0)
