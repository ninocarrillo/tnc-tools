# link-serial
# Python3
# Link two serial ports.
# Nino Carrillo
# 27 Jan 2023
# Exit codes
# 1 Wrong python version
# 2 Not enough command line arguments
# 3 Unable to open serial port

import serial
import sys
import time

if sys.version_info < (3, 0):
	print("Python version should be 3.x, exiting")
	sys.exit(1)

def GracefulExit(port1, port2, code):
	try:
		port1.close()
	except:
		pass
	try:
		port2.close()
	except:
		pass
	finally:
		sys.exit(code)

print('starting')

if len(sys.argv) < 5:
	print('Not enough arguments. Usage: python3 link-serial.py <serial device> <baud rate> <serial-device> <baud-rate>')
	sys.exit(2)

try:
	port1 = serial.Serial(sys.argv[1], baudrate=sys.argv[2], bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0, timeout=0)
except:
	print(f'Unable to open serial port {sys.argv[1]}')
	sys.exit(3)

print('Opened port', sys.argv[1])

try:
	port2 = serial.Serial(sys.argv[3], baudrate=sys.argv[4], bytesize=8, parity='N', stopbits=1, xonxoff=0, rtscts=0, timeout=0)
except:
	print(f'Unable to open serial port. {sys.argv[3]}')
	sys.exit(3)

print('Opened port', sys.argv[3])

# GracefulExit(port1,port2,0)
#
byte_count = 100
while 1:
	byte_count -= 1
	if port1.in_waiting > 0:
		input_data1 = port1.read(port1.in_waiting)
		if input_data1:
			port2.write(input_data1)
	if port2.in_waiting > 0:
		input_data2 = port2.read(port2.in_waiting)
		if input_data2:
			port1.write(input_data2)
	time.sleep(0.1)
#
#
GracefulExit(port1, port2, 0)
