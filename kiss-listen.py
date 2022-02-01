# kiss-listen
# Python3
# Monitors KISS frames from specified serial port.
# Nino Carrillo 
# 30 Jan 2022
# Exit codes
# 1 Wrong python version
# 2 Not enough command line arguments
# 3 Unable to open serial port

import serial
import sys
import time

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
		sys.exit(code)

if len(sys.argv) < 3:
	print('Not enough arguments. Usage: python3 kiss-listen.py <serial device> <baud rate>')
	sys.exit(2)

try:
	port = serial.Serial(sys.argv[1], baudrate=sys.argv[2], bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0, timeout=3)
except:
	print('Unable to open serial port.')
	sys.exit(3)

print('Opened port', sys.argv[1])

kiss_state = "non-escaped"
kiss_frame = []
FESC = 0xDB
FEND = 0xC0
TFESC = 0xDD
TFEND = 0xDC

frame_count = 0

while 1:
	input_data = port.read(1)
	if input_data:
		# print(input_data)
		if kiss_state == "non-escaped":
			if ord(input_data) == FESC:
				kiss_state = "escaped"
			elif ord(input_data) == FEND:
				if len(kiss_frame) > 0:
					frame_count += 1
					t = time.localtime()
					kiss_frame_time = time.strftime("%H:%M:%S", t)
					print_frame(kiss_frame, kiss_frame_time, frame_count)
					kiss_frame = []
				else:
					kiss_frame = []
			else:
				kiss_frame.append(ord(input_data))
		elif kiss_state == "escaped":
			if ord(input_data) == TFESC:
				kiss_frame.append(FESC)
				kiss_state = "non-escaped"
			elif ord(input_data) == TFEND:
				kiss_frame.append(FEND)
				kiss_state = "non-escaped"

GracefulExit(port, 0)
