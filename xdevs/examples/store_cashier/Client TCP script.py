import queue
import socket
import threading
import time
import datetime
import random

HOST = 'LocalHost'
PORT = 4321

c = socket.socket(socket.AF_INET,socket.SOCK_STREAM)

c.connect((HOST,PORT))
t_ini = time.time()

Q = queue.SimpleQueue()

"""for i in range(10):
    data = f'NewClient,{i}?{time.time()-t_ini}'
    if i%5:
        data = f'AvailableEmployee,{i}'
    c.sendall(data.encode())
    time.sleep(2)"""

def inyect_clients():
    for i in range(30):
        data = f'NewClient,TCP_{i}?{time.time()}'
        Q.put(data)
        print(data)
        valor = random.normalvariate(6, 0.5)
        time.sleep(valor)


t1 = threading.Thread(target=inyect_clients,daemon=True)

t1.start()

while True:
    data = Q.get()
    c.sendall(data.encode())