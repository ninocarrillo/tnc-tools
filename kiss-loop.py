# kiss-loop
# Python3
# Send, receive, and validate KISS frames from one serial port to another
# Nino Carrillo
# 29 Oct 2023
# Exit codes
# 1 Wrong python version
# 2 Not enough command line arguments
# 3 Unable to open transmit serial port
# 4 Unable to open receive serial port
# 5 Invalid frame count
# 6 Invalid payload length
# 7 Invalid inverval time

import serial
import sys
from timeit import default_timer as timer
import random
import string
import crc

def GracefulExit2(porta, portb, code):
	try:
		porta.close()
	except:
		pass
	try:
		portb.close()
	except:
		pass	
	sys.exit(code)
	
def GenerateRandomCallsign():
	this = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
	this += '-'
	this += ''.join(random.choices(string.digits, k=1))
	return this
	
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
		print(f'{hex(working_character)} ', end='')
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
			print(f'{hex(working_character)} ', end='')
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
			if (working_character == 0xCC):
				print("ARPA Internet Protocol", end='')
			if (working_character == 0xCD):
				print("ARPA Address Resolution", end='')
			if (working_character == 0xCF):
				print("TheNET (NET/ROM)", end='')
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

if len(sys.argv) < 8:
	print('Not enough arguments. Usage prototype below.\r\npython3 kiss-loop.py <tx serial device> <tx baud rate> <rx serial device> <rx baud rate> <frame count> <payload length> <frame interval>')
	sys.exit(2)

try:
	tx_port = serial.Serial(sys.argv[1], baudrate=sys.argv[2], bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0, timeout=3)
except:
	print('Unable to open transmit serial port.')
	sys.exit(3)

try:
	rx_port = serial.Serial(sys.argv[3], baudrate=sys.argv[4], bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0, timeout=0.1)
except:
	print('Unable to open receive serial port.')
	sys.exit(4)

source_callsign = StringCallsignToArray(GenerateRandomCallsign(), 'Source Callsign or SSID is invalid.', 4)
dest_callsign = StringCallsignToArray(GenerateRandomCallsign(), 'Destination Callsign or SSID is invalid.', 5)

print(source_callsign)
print(dest_callsign)

try:
	transmit_frame_count_target = int(sys.argv[5])
except:
	print('Frame count argument is not an integer.')
	GracefulExit2(tx_port, rx_port, 5)
	
try:
	target_payload_length = int(sys.argv[6])
except:
	print('Payload length argument is not an integer.')
	GracefulExit2(tx_port, rx_port, 6)
	
try:
	frame_interval = float(sys.argv[7])
except:
	print('Frame interval is not a number.')
	GracefulExit2(tx_port, rx_port, 7)


RX_FESC = 0xDB
RX_FEND = 0xC0
RX_TFESC = 0xDD
RX_TFEND = 0xDC

FESC = int(0xDB).to_bytes(1,'big')
FEND = int(0xC0).to_bytes(1,'big')
TFESC = int(0xDD).to_bytes(1,'big')
TFEND = int(0xDC).to_bytes(1,'big')
KISS_PORT = 0
KISS_COMMAND = 0
KISS_TYPE_ID = (KISS_PORT * 16) + KISS_COMMAND
KISS_TYPE_ID = KISS_TYPE_ID.to_bytes(1,'big')

transmit_frame_counter = 0;
transmit_trigger = False
last_transmit_time = timer() - frame_interval

rx_kiss_state = "non-escaped"
receive_frame = []
receive_match_count = 0
receive_mismatch_count = 0
receive_miss_count = 0

receive_interlock = False

keep_going = True

#for transmit_frame_counter in range(0, transmit_frame_count_target):
while keep_going:
	if timer() - last_transmit_time > frame_interval:
		transmit_trigger = True
	keep_going = False
	if transmit_frame_count_target > transmit_frame_counter:
		keep_going = True
	else:
		transmit_trigger = False
	if timer() - last_transmit_time < frame_interval:
		keep_going = True
		

	
	if transmit_trigger == True:
		transmit_trigger = False
		if receive_interlock == True:
			receive_interlock = False
			receive_miss_count += 1
			print(f'Receive miss, count:{receive_miss_count}')
		receive_interlock = True
		transmit_frame_counter += 1
		# Assemble KISS frame:
		transmit_frame = bytearray()
		source_callsign = StringCallsignToArray(GenerateRandomCallsign(), 'Source Callsign or SSID is invalid.', 4)
		dest_callsign = StringCallsignToArray(GenerateRandomCallsign(), 'Destination Callsign or SSID is invalid.', 5)
		# Add destination callsign, shifted left one bit:
		for j in range(6):
			transmit_frame.extend((dest_callsign[j]<<1).to_bytes(1,'big'))
		# Add destination SSID with CRR bits set
		transmit_frame.extend((((dest_callsign[6] & 0xF)<<1) | 0xE0).to_bytes(1,'big'))
		# Add source callsign, shifted left one bit:
		for k in range(6):
			transmit_frame.extend((source_callsign[k]<<1).to_bytes(1,'big'))
		# Add source SSID with Address Extension Bit and RR bits:
		transmit_frame.extend((((source_callsign[6] & 0xF) << 1) | 0x61).to_bytes(1,'big'))

		# Add Control field for TEST:
		transmit_frame.extend((0xE3).to_bytes(1,'big'))
		# Add PID for No Layer 3:
		transmit_frame.extend((0xF0).to_bytes(1,'big'))

		# save the length of the kiss frame for payload length computations later
		payload_length = len(transmit_frame)


		#transmit_frame.extend(payload)
		#payload = bytearray(payload_text, 'UTF-8')
		#transmit_frame.extend(payload)
		
		if target_payload_length > 1:
			transmit_frame.extend(bytearray(str(transmit_frame_counter), 'UTF-8'))
			transmit_frame.extend(bytearray(" ", 'UTF-8'))

		payload_length = len(transmit_frame) - payload_length
		#print(payload_length)

		# Pad payload to specified length:
		if payload_length < target_payload_length:
			payload = bytearray()
			for j in range(0, target_payload_length - payload_length):
				rand = random.randint(32,126)
				payload.extend(bytearray(rand.to_bytes(1,'big')))
			transmit_frame.extend(payload)

		print(f'Sending Frame {transmit_frame_counter} CRC value: {crc.CalcCRC16(transmit_frame)}')
		character_counter = 0
		# for character in transmit_frame:
			# print(hex(character), end=' ')
			# character_counter += 1
			# if character_counter == 16:
				# character_counter = 0
				# print(f'\n', end='')
		#sys.stdout.flush()

		frame_index = 0
		transmit_kiss_frame = bytearray()
		while(frame_index < len(transmit_frame)):
			kiss_byte = transmit_frame[frame_index]
			if kiss_byte.to_bytes(1,'big') == FESC:
				transmit_kiss_frame.extend(FESC)
				transmit_kiss_frame.extend(TFESC)
			elif kiss_byte.to_bytes(1, 'big') == FEND:
				transmit_kiss_frame.extend(FESC)
				transmit_kiss_frame.extend(TFEND)
			else:
				transmit_kiss_frame.extend(kiss_byte.to_bytes(1, 'big'))
			frame_index += 1
		transmit_kiss_frame = bytearray(FEND) + bytearray(KISS_TYPE_ID) + transmit_kiss_frame + bytearray(FEND)
		tx_port.write(transmit_kiss_frame)
		last_transmit_time = timer()

	rx_serial_data = rx_port.read(1)
	if rx_serial_data:
		if rx_kiss_state == "non-escaped":
			if ord(rx_serial_data) == RX_FESC:
				rx_kiss_state = "escaped"
			elif ord(rx_serial_data) == RX_FEND:
				receive_time = timer()
				if len(receive_frame) > 0:
					receive_interlock = False
					# create an integer version of transmit_frame
					transmit_frame_int = [x for x in transmit_frame]
					# strip KISS command byte from receive frame
					receive_frame = receive_frame[1:]
					if transmit_frame_int == receive_frame:
						receive_match_count += 1
						print(f'Receive match, count:{receive_match_count}, transit time:{receive_time - last_transmit_time}')
					else:
						receive_mismatch_count += 1
						print(f'Receive MISMATCH, count:{receive_mismatch_count}')
						print(f'Sent frame:\n{transmit_frame_int}')
						print(f'Receive frame:\n{receive_frame}')
					#t = datetime.datetime.now()
					#kiss_frame_time = time.strftime("%H:%M:%S", t)
					#print_frame(kiss_frame, t, frame_count)
					#header_length = print_ax25_header(receive_frame)
					#receive_frame_string = ""
					#for receive_character in receive_frame[header_length:]:
						#kiss_frame_string += chr(character)
					#print(kiss_frame_string)
					#kiss_frame = []
					receive_frame = []
				else:
					receive_frame = []
			else:
				receive_frame.append(ord(rx_serial_data))
		elif rx_kiss_state == "escaped":
			print('e', end='')
			if ord(rx_serial_data) == RX_TFESC:
				receive_frame.append(RX_FESC)
				rx_kiss_state = "non-escaped"
			elif ord(rx_serial_data) == RX_TFEND:
				receive_frame.append(RX_FEND)
				rx_kiss_state = "non-escaped"
print('\nFinal status:')
print(f'Receive Match Count: {receive_match_count}')
print(f'Receive Mismatch Count: {receive_mismatch_count}')
print(f'Receive Miss Count: {receive_miss_count}')

print('\nDone.')
GracefulExit2(tx_port, rx_port, 0)
