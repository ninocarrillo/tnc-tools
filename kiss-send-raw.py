# kiss-send-raw
# Python3
# Generate a single KISS-encapsulated AX.25 UI frame and send to the serial port.
# Nino Carrillo
# 24 Feb 2023
# Exit codes
# 1 Wrong python version
# 2 Not enough command line arguments
# 3 Unable to open serial port

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

if sys.version_info < (3, 0):
	print("Python version should be 3.x, exiting")
	sys.exit(1)

if len(sys.argv) < 4:
	print('Not enough arguments. Usage prototype below. Enclose payload in "double quotes".\r\npython3 kiss-send-raw.py <serial device> <baud rate> <payload>')
	sys.exit(2)

try:
	port = serial.Serial(sys.argv[1], baudrate=sys.argv[2], bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0, timeout=3)
except:
	print('Unable to open serial port.')
	sys.exit(3)

print(sys.argv[3])
kiss_frame = bytes(sys.argv[3], 'ascii')
print(kiss_frame)

FESC = int(0xDB).to_bytes(1,'big')
FEND = int(0xC0).to_bytes(1,'big')
TFESC = int(0xDD).to_bytes(1,'big')
TFEND = int(0xDC).to_bytes(1,'big')

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
kiss_output_frame = bytearray(FEND) + kiss_output_frame + bytearray(FEND)
print(kiss_output_frame)
frame_time = len(kiss_output_frame) * 10 / int(sys.argv[2])
port.write(kiss_output_frame)
time.sleep(frame_time * 1.5)
GracefulExit(port, 0)
