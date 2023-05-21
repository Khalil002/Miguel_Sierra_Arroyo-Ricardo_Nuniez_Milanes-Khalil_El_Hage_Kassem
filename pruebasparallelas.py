import os
import sys
import time
import heapq
import pickle
import numpy as np
from mpi4py import MPI

#Get input & output paths
input_path = sys.argv[1]
input_filename, input_file_extension = os.path.splitext(input_path)
output_path = "comprimido.elmejorprofesor"
if(os.path.isfile(input_path) == False):
	print(input_path+" does not exist")
	exit(0)
	
#
amode = MPI.MODE_WRONLY|MPI.MODE_CREATE
comm = MPI.COMM_WORLD
rank = comm.Get_rank()

fh = MPI.File.Open(comm, input_path, amode)
if rank == 0:
    print("")
else:
	print("")

#Begin compression
st = time.time()
#Compressing
et = time.time()
ft = et-st
print("Tiempo de compresión: "+str(ft)+" segundos")