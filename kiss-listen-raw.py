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
import datetime

def print_ax25_header(frame):
	count = len(frame)
	index = 0
	if (count > 15):
		valid_header = 1
		address_extension_bit = 0
		index = 1
		subfield_character_index = 0
		subfield_index = 0
		print("- AX.25 Decode:")
		# Print address information
		while address_extension_bit == 0:
			working_character = int(frame[index])
			if (working_character & 0b1) == 1:
				address_extension_bit = 1
			working_character = working_character >> 1
			subfield_character_index = subfield_character_index + 1
			if (subfield_character_index == 1):
				if (subfield_index == 0):
					print("To:", end='')
				elif (subfield_index == 1):
					print(", From:", end='')
				else:
					print(", Via:", end='')
			if subfield_character_index < 7:
				# This is a callsign character
				if (working_character != 0) and (working_character != 0x20):
					print(chr(working_character), end='')
			elif subfield_character_index == 7:
				# This is the SSID characters
				# Get bits
				print('-', end='')
				print(working_character & 0b1111, end='')
				if (working_character & 0b10000000):
					# C or H bit is set
					print('*', end=' ')
				# This field is complete
				subfield_character_index = 0
				subfield_index = subfield_index + 1
			index = index + 1
			if index > count:
				address_extension_bit = 1
		# Control and PID fields
		working_character = frame[index]
		print(", Control: ", end='')
		poll_final_bit = (working_character & 0x10) >> 4
		# determine what type of frame this is
		if (working_character & 1) == 1:
			# either a Supervisory or Unnumbered frame
			frame_type = working_character & 3
		else:
			# Information frame
			frame_type = 0
			ax25_ns = (working_character >> 1) & 7
			ax25_nr = (working_character >> 5) & 7

		if frame_type == 1:
			# Supervisory frame
			ax25_nr = (working_character >> 5) & 7

		if frame_type == 3:
			# Unnumbered frame, determine what type
			ax25_u_control_field_type = working_character & 0xEF
		else:
			ax25_u_control_field_type = 0

		if (ax25_u_control_field_type == 0x6F):
			print("SABME", end='')
		elif (ax25_u_control_field_type == 0x2F):
			print("SABM", end='')
		elif (ax25_u_control_field_type == 0x43):
			print("DISC", end='')
		elif (ax25_u_control_field_type == 0x0F):
			print("DM", end='')
		elif (ax25_u_control_field_type == 0x63):
			print("UA", end='')
		elif (ax25_u_control_field_type == 0x87):
			print("FRMR", end='')
		elif (ax25_u_control_field_type == 0x03):
			print("UI", end='')
		elif (ax25_u_control_field_type == 0xAF):
			print("XID", end='')
		elif (ax25_u_control_field_type == 0xE3):
			print("TEST", end='')

		if (frame_type == 0) or (ax25_u_control_field_type == 3):
			# This is an Information frame, or an Unnumbered Information frame, so
			# there is a PID byte.
			index = index + 1
			working_character = frame[index]
			print(", PID: ", end='')
			if (working_character == 1):
				print("ISO 8208", end='')
			if (working_character == 6):
				print("Compressed TCP/IP", end='')
			if (working_character == 7):
				print("Uncompressed TCP/IP", end='')
			if (working_character == 8):
				print("Segmentation Fragment", end='')
			if (working_character == 0xC3):
				print("TEXNET", end='')
			if (working_character == 0xC4):
				print("Link Quality Protocol", end='')
			if (working_character == 0xCA):
				print("Appletalk", end='')
			if (working_character == 0xCB):
				print("ARPA Internet Protocol", end='')
			if (working_character == 0xCC):
				print("ARPA Address Resolution", end='')
			if (working_character == 0xCD):
				print("TheNET", end='')
			if (working_character == 0xF0):
				print("No Layer 3", end='')
			if (working_character == 0xFF):
				print("Escape", end='')

		index = index + 1

		# return the index of the start of payload data
		print(" ")
	return index

def print_frame(frame, time, count):
	print("\r\n-- ", end='')
	print(time, end=' ')
	frame_len = len(frame)
	print("frame number: %d" % count, end=' ')
	print("byte count: ", frame_len, end='\r\n')
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
		print('\r\n', end='', flush=True)

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
#		print(input_data)
		if kiss_state == "non-escaped":
			if ord(input_data) == FESC:
				kiss_state = "escaped"
			elif ord(input_data) == FEND:
				if len(kiss_frame) > 0:
					frame_count += 1
					t = datetime.datetime.now()
					#kiss_frame_time = time.strftime("%H:%M:%S", t)
					print_frame(kiss_frame, t, frame_count)
					#header_length = print_ax25_header(kiss_frame)
					#kiss_frame_string = ""
					#for character in kiss_frame[header_length:]:
					#	kiss_frame_string += chr(character)
					#print(kiss_frame_string)
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
