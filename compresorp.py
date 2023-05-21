import os
import sys
import time
import heapq
import pickle
import math
from mpi4py import MPI

def dividrTexto(numProcesos, lenData):
	caracteres=[]
	result = float(lenData)/numProcesos
	decimalPart = result - math.floor(result)
	procesosMayorCaracteres = int(decimalPart*numProcesos)
	for i in range (procesosMayorCaracteres):
		caracteres.append(math.ceil(result))
	for j in range (i+1,numProcesos):	
		caracteres.append(math.floor(result))
	return caracteres

def combinar_freq_table(freq_tables):
    resultado = {}
    for freq_table in freq_tables:
        for clave, valor in freq_table.items():
            if clave in resultado:
                resultado[clave] += valor
            else:
                resultado[clave] = valor
    return resultado

class HuffmanCompressor:
	def __init__(self, input_path, output_path):
		self.input_path = input_path
		self.output_path = output_path
		self.heap = []
		self.codes = {}
		self.reverse_mapping = {}

	class HeapNode:
		def __init__(self, char, freq):
			self.char = char
			self.freq = freq
			self.left = None
			self.right = None

		def __lt__(self, other):
			if(other == None):
				return False
			return self.freq < other.freq

		def __eq__(self, other):
			if(other == None):
				return False
			return self.freq == other.freq

	#crea la tabla de frecuencia dada la lista de símbolos hexadeciamles 
	def create_freq_table(self, data):
		freq_table = {}
		for symbol in data:
			if not symbol in freq_table:
				freq_table[symbol] = 0
			freq_table[symbol] += 1
		return freq_table

	#toma la tabla de frecuencia y crea el montículo (símbolo con su frecuencia)	
	#los nodos se ordenan automáticamente en función de sus frecuencias
	def create_heap(self, freq_table):
		for key in freq_table:
			node = self.HeapNode(key, freq_table[key])
			heapq.heappush(self.heap, node)

	#fusiona repetidamente los nodos de menor frecuencia en el montículo hasta que solo quede un nodo
	def merge_nodes(self):
		while(len(self.heap)>1):
			node1 = heapq.heappop(self.heap)
			node2 = heapq.heappop(self.heap)

			merged = self.HeapNode(None, node1.freq + node2.freq)
			merged.left = node1
			merged.right = node2

			heapq.heappush(self.heap, merged)

	#realiza un recorrido DFS en el árbol para asignar códigos binarios a cada símbolo
	# los códigos se generan concatenando los movimientos, 0 hacia la izquierda y 1 hacia la derecha	
	def create_codes_helper(self, root, current_code):
		if(root == None):
			return

		if(root.char != None):
			self.codes[root.char] = current_code
			self.reverse_mapping[current_code] = root.char
			return

		self.create_codes_helper(root.left, current_code + "0")
		self.create_codes_helper(root.right, current_code + "1")

	#invoca create_codes_helper para generar los códigos para cada símbolo en el árbol
	def create_codes(self):
		root = heapq.heappop(self.heap)
		current_code = ""
		self.create_codes_helper(root, current_code)

	#recibe una lista de símbolos y devuelve el texto codificado obtenido al concatenar los códigos
	#correspondientes a cada símbolo.
	def get_encoded_text(self, text):
		encoded_text = ""
		for character in text:
			encoded_text += self.codes[character]
		return encoded_text

	#agrega un relleno al texto codificado para que su longitud sea múltiplo de 8 (un byte completo)
	def pad_encoded_text(self, encoded_text):
		extra_padding = 8 - len(encoded_text) % 8
		for i in range(extra_padding):
			encoded_text += "0"

		padded_info = "{0:08b}".format(extra_padding)
		encoded_text = padded_info + encoded_text
		return encoded_text

	#toma el texto codificado con el relleno y lo convierte en una secuencia de bytes
	def get_byte_array(self, padded_encoded_text):
		if(len(padded_encoded_text) % 8 != 0):
			print("Encoded text not padded properly")
			exit(0)

		b = bytearray()
		for i in range(0, len(padded_encoded_text), 8):
			byte = padded_encoded_text[i:i+8]
			b.append(int(byte, 2))
		return b

	def compress(self, input_file_extension):
		comm = MPI.COMM_WORLD
		size = comm.Get_size()
		rank = comm.Get_rank()

		if rank == 0:
			comm = MPI.COMM_WORLD
			rank = comm.Get_rank()
			size = comm.Get_size()
			with open(self.input_path, 'rb') as input_file, open(self.output_path, 'wb') as output_file:
				data_bytes = input_file.read()
				data_hex = data_bytes.hex()
				data = [data_hex[i:i+2] for i in range(0, len(data_hex), 2)]

				caracteres = dividrTexto(size-1,len(data))
				for i in range (1, size):
					comm.send(caracteres[i-1], dest=i)

				freq_table_array = []
				for i in range (1, size):
					dataReceived = comm.recv(source=MPI.ANY_SOURCE)
					freq_table_array.append(dataReceived)
				freq_table = combinar_freq_table(freq_table_array)
			
		else:
			dataReceived=comm.recv(source=0)
			freq_table = self.create_freq_table(dataReceived)
			comm.send(freq_table, dest=0)

		with open(self.input_path, 'rb') as input_file, open(self.output_path, 'wb') as output_file:
			data_bytes = input_file.read()
			data_hex = data_bytes.hex()
			
			data = [data_hex[i:i+2] for i in range(0, len(data_hex), 2)]
			
			freq_table = self.create_freq_table(data)
			self.create_heap(freq_table)
			self.merge_nodes()
			self.create_codes()

			encoded_text = self.get_encoded_text(data)
			padded_encoded_text = self.pad_encoded_text(encoded_text)

			b = self.get_byte_array(padded_encoded_text)
			b2 = pickle.dumps(self.reverse_mapping)
			b3 = len(b2)
			b4 = b3.to_bytes(4, sys.byteorder)
			b5 = str.encode(input_file_extension)
			b6 = len(b5)
			b7 = b6.to_bytes(4, sys.byteorder)
			
			#writes the file extension length
			output_file.write(b7)

			#writes the file extension
			output_file.write(b5)

			#writes the pickled reverse_mapping length
			output_file.write(b4)

			#writes the pickled reverse_mapping
			output_file.write(b2)

			#writes the compressed file
			output_file.write(bytes(b))
	
	#def save_reverse_mapping(self):
	#	with open('reverse_mapping', 'wb') as reverse_mapping_file:
	#		pickle.dump(self.reverse_mapping, reverse_mapping_file)

def main():
	input_path = sys.argv[1]
	input_filename, input_file_extension = os.path.splitext(input_path)
	output_path = "comprimido.elmejorprofesor"
	if(os.path.isfile(input_path) == False):
		print(input_path+" does not exist")
		exit(0)
	hc = HuffmanCompressor(input_path, output_path)

	st = time.time()
	hc.compress(input_file_extension)
	et = time.time()
	ft = et-st
	print("Tiempo de compresión: "+str(ft)+" segundos")

	#hc.save_reverse_mapping()

if __name__ == "__main__":
    main()