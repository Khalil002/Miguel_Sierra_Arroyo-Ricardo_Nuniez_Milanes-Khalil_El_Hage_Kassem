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

		

		with open(self.input_path, 'rb') as input_file, open(self.output_path, 'wb') as output_file:
			
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
		
		with open(self.output_path+output_file_extension, 'wb') as output_file:
			output_file.write(decompressed_binary)
	
	#def load_reverse_mapping(self):
	#	with open('reverse_mapping', 'rb') as reverse_mapping_file:
	#		self.reverse_mapping = pickle.load(reverse_mapping_file)
	
def main():
	input_path = "comprimido.elmejorprofesor"
	output_path = "descomprimido-elmejorprofesor"

	if(os.path.isfile(input_path) == False):
		print(input_path+" does not exist")
		exit(0)
	hd = HuffmanDecompressor(input_path, output_path)
	#hd.load_reverse_mapping()

	st = time.time()
	hd.decompress()
	et = time.time()
	ft = et-st
	print("Tiempo de descompresión: "+str(ft)+" segundos")


if __name__ == "__main__":
    main()