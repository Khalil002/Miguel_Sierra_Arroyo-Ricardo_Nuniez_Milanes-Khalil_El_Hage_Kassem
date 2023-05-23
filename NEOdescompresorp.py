import os
import sys
import time
import pickle
from mpi4py import MPI
from math import ceil

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

		

		with open(self.input_path, 'rb') as input_file:
			
			#Load the reverse_mapping
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

			encoded_text = self.remove_padding(bit_string)

			
			decompressed_text = self.decode_text(encoded_text)
			decompressed_binary = bytes.fromhex(decompressed_text)
		
		return decompressed_binary, output_file_extension
		with open(self.output_path+output_file_extension, 'wb') as output_file:
			output_file.write(decompressed_binary)
	
	#def load_reverse_mapping(self):
	#	with open('reverse_mapping', 'rb') as reverse_mapping_file:
	#		self.reverse_mapping = pickle.load(reverse_mapping_file)

def divide_data(data, size):
    parts = []
    chunckSize = ceil(len(data)/(size-1))
    for i in range(0, size):
        if(i == size-1):
            parts.append(data[chunckSize*(i-1):len(data)])
        else:
            parts.append(data[chunckSize*(i-1):chunckSize*i])
    return parts, chunckSize

def main():
	comm = MPI.COMM_WORLD
	size = comm.Get_size()
	rank = comm.Get_rank()
	amode = MPI.MODE_WRONLY|MPI.MODE_CREATE
	output_path = "descomprimidop-elmejorprofesor"
	if rank == 0:

		input_path = sys.argv[1]

		if(os.path.isfile(input_path) == False):
			print(input_path+" does not exist")
			exit(0)
		hd = HuffmanDecompressor(input_path, output_path)
		st = time.time()
		decoded_text, output_file_extension = hd.decompress()
		divided_decoded_text, chunckSize = divide_data(decoded_text, size)
	else:
		decoded_text = None
		output_file_extension = None
		chunckSize = None
		divided_decoded_text = None
	
	divided_decoded_text = comm.scatter(divided_decoded_text, root = 0)
	output_file_extension = comm.bcast(output_file_extension, root = 0)
	chunckSize = comm.bcast(chunckSize, root = 0)
	fh = MPI.File.Open(comm, output_path+output_file_extension, amode)
	offset = chunckSize*(rank-1)
	fh.Write_at_all(offset, divided_decoded_text)
	fh.Close()

	if rank == 0:
		et = time.time()
		ft = et-st
		print(ft)

if __name__ == "__main__":
    main()