import numpy as np

def CalcCRC16(packet):
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
	return(hex(fcs_val))
