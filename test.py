from mpi4py import MPI
import time

def primeCheck(num):
    """
    Función que verifica si un número es primo
    """
    divisores = 0
    for i in range(2, num):
        if num % i == 0:
            divisores += 1
            break
    if divisores == 0:
        return True
    else:
        return False

# Inicialización de MPI
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

# Argumentos de entrada
k = int(input("Ingrese el número de dígitos k: "))
q = int(input("Ingrese el valor de q (0 o 1): "))
n_primos = int(input("Ingrese el número límite de primos a verificar: "))

# Proceso raíz
if rank == 0:
    start_time = time.time()
    paquetes = []
    primos = []
    paquetes_por_trabajar = n_primos // 10
    if n_primos % 10 != 0:
        paquetes_por_trabajar += 1
    for i in range(paquetes_por_trabajar):
        paquete = []
        for j in range(10):
            numero = i * 10 + j + 1
            if len(str(numero)) == k:
                paquete.append(numero)
                if len(paquete) == 10:
                    paquetes.append(paquete)
                    paquete = []
        if len(paquete) > 0:
            paquetes.append(paquete)
    trabajadores = size - 1
    paquetes_enviados = 0
    paquetes_recibidos = 0
    while paquetes_enviados < len(paquetes):
        # Envía un paquete a un proceso trabajador disponible
        status = MPI.Status()
        comm.recv(source=MPI.ANY_SOURCE, status=status)
        proceso = status.Get_source()
        comm.send(paquetes[paquetes_enviados], dest=proceso)
        paquetes_enviados += 1
    while paquetes_recibidos < paquetes_por_trabajar:
        # Recibe el resultado de un proceso trabajador y envía otro paquete
        status = MPI.Status()
        primo = comm.recv(source=MPI.ANY_SOURCE, status=status)
        proceso = status.Get_source()
        if primo:
            primos.append(primo)
        if paquetes_enviados < len(paquetes):
            comm.send(paquetes[paquetes_enviados], dest=proceso)
            paquetes_enviados += 1
        else:
            comm.send(None, dest=proceso)
        paquetes_recibidos += 1
    end_time = time.time()
    print("
