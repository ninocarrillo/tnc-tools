# kiss-testframe
# Python3
# Generate KISS frames and send them to the serial port.
# Nino Carrillo 
# 30 Jan 2022
# Exit codes
# 1 Wrong python version
# 2 Not enough command line arguments
# 3 Unable to open serial port
# 4 Invalid frame count argument
# 5 Invalid frame length argument
# 6 Invalid frame interval argument

import serial
import sys
import time
import random

def print_frame(frame, time, count):
	print(time, end=' ')
	frame_len = len(frame)
	print("%8d" % count, end='  ')
	print("KISS frame contains", frame_len, end=' bytes:\r\n')
	frame_lines = (frame_len // 16)
	if (frame_len % 16) > 0:
		frame_lines += 1
	last_line_len = frame_len - (frame_lines * 16)
	frame_index = 0
	for line in range(0, frame_lines):
		for i in range(0, 16):
			if frame_index < frame_len:
				if frame[frame_index] < 0x20:
					print('.', end='')
				elif frame[frame_index] > 0x7E:
					print('.', end='')
				else:
					print(chr(frame[frame_index]), end='')
				frame_index += 1
			else:
				print(' ', end='')
		print(' | ', end='')
		frame_index = line * 16
		for i in range(0, 16):
			if frame_index < frame_len:
				print("%2X" % frame[frame_index], end=' ')
				frame_index += 1
		print('\r\n', end='')

	

if sys.version_info < (3, 0): 
	print("Python version should be 3.x, exiting")
	sys.exit(1)

def GracefulExit(port, code):
	try:
		port.close()
	except:
		pass
	finally:
		print('Closed port ', port.port)
		sys.exit(code)

if len(sys.argv) < 5:
	print('Not enough arguments. Usage: python3 kiss-testframe.py <serial device> <baud rate> <frame count> <frame length> <interval>')
	sys.exit(2)

try:
	port = serial.Serial(sys.argv[1], baudrate=sys.argv[2], bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0, timeout=3)
except:
	print('Unable to open serial port.')
	sys.exit(3)

print('Opened port', sys.argv[1])

try:
	frame_count = int(sys.argv[3])
except:
	print('Frame count argument is not an integer.')
	GracefulExit(port, 4)

print('Frame count = %d' % frame_count)

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
