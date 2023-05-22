import os
import sys
import time
import pickle
from mpi4py import MPI

class HuffmanDecompressor:

	def __init__(self, input_path, output_path):
		self.input_path = input_path
		self.output_path = output_path
		self.reverse_mapping = {}

	def remove_padding(self, padded_encoded_text):
		padded_info = padded_encoded_text[:8]
		extra_padding = int(padded_info, 2)

		padded_encoded_text = padded_encoded_text[8:] 
		encoded_text = padded_encoded_text[:-1*extra_padding]

		return encoded_text

	def decode_text(self, encoded_text):
		current_code = ""
		decoded_bytes = ""

		for bit in encoded_text:
			current_code += bit
			if(current_code in self.reverse_mapping):
				character = self.reverse_mapping[current_code]
				decoded_bytes += character
				current_code = ""

		return decoded_bytes

	def decompress(self):

		output_file_extension = ""
		decompressed_binary = ""
		comm = MPI.COMM_WORLD
		size = comm.Get_size()
		rank = comm.Get_rank()
		
		if rank == 0:
			with open(self.input_path, 'rb') as input_file:
				#Load the extension
				n = int.from_bytes(input_file.read(4), byteorder=sys.byteorder)
				output_file_extension_as_bytes = input_file.read(n)
				output_file_extension = output_file_extension_as_bytes.decode()

				#Load the reverse_mapping
				n = int.from_bytes(input_file.read(4), byteorder=sys.byteorder)
				reverse_mapping_bytes = input_file.read(n)
				self.reverse_mapping = pickle.loads(reverse_mapping_bytes)

				bit_string = ""
				#Load the compressed file
				byte = input_file.read(1)
				while(len(byte) > 0):
					byte = ord(byte)
					bits = bin(byte)[2:].rjust(8, '0')
					bit_string += bits
					byte = input_file.read(1)

				print(bit_string)
				encoded_text = self.remove_padding(bit_string)
				print(encoded_text)
				
				decompressed_text = self.decode_text(encoded_text)
				decompressed_binary = bytes.fromhex(decompressed_text)
				
				length = len(decompressed_binary)
				parts = round(length / size)
				j = 0
				for i in range(0, length, parts):
					if j == size-1:
						comm.send(decompressed_binary[i:], dest=j+1)
						break
					else:
						comm.send(decompressed_binary[i:i+parts], dest=j+1)
						j += 1

				for i in range (1, size):
					comm.send(decompressed_binary, dest=i)

			with open(self.output_path+output_file_extension, 'wb') as output_file:
				for i in range(1, size):
					dataReceived=comm.recv(source=i)
					output_file.write(dataReceived)
			
		else:
			dataReceived=comm.recv(source=0)
			comm.send(dataReceived, dest=0)
	
def main():
	input_path = sys.argv[1]
	output_path = "descomprimidop-elmejorprofesor"

	if(os.path.isfile(input_path) == False):
		print(input_path+" does not exist")
		exit(0)
	hd = HuffmanDecompressor(input_path, output_path)
	#hd.load_reverse_mapping()
	st = time.time()
	hd.decompress()
	et = time.time()
	ft = et-st
	print(ft)


if __name__ == "__main__":
    main()