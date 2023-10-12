import numpy as np

def CalcCRC16(packet):
	#packet_val = packet[byte_count - 1] * 256
	#packet_val += packet[byte_count - 2]
	# print(hex(packet_val))
	#packet = packet[0:byte_count - 2] # slicing exludes the end index
	fcsval = np.uint16(0xFFFF)
	CRC_poly = np.uint16(0x8408)
	one = np.uint16(1)
	for byte in packet:
		for i in range(8):
			fcsbit = np.bitwise_and(fcsval, one)
			fcsval = np.right_shift(fcsval, 1)
			if np.bitwise_xor(fcsbit, np.bitwise_and(byte,one)) != 0:
				fcsval = np.bitwise_xor(fcsval, CRC_poly)
			byte = np.right_shift(byte, 1)
	fcs_val = np.bitwise_and(np.bitwise_not(fcsval), 0xFFFF)
	if packet_val == fcs_val:
		return [fcs_val, 1]
	else:
		return [fcs_val, 0]
