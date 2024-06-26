# GPT examples

This folder stores several examples in order to illustrate some of the possibilities offered by the repository.


## `xDEVS.py` Virtual Simulation

A virtual simulation is carried out only taking into account the virtual environment. 

### Example:


```bash
$ cd xdevs/examples/gpt
$ python3 gpt_v_sim.py
```

## `xDEVS` Real-Time Simulation

This section aims to show a collection of examples based on the methodology followed in this repository for achieving the wall-clock behaviour.

### Examples:

1. #### No handlers real-time simulation

```bash
$ cd xdevs/examples/gpt
$ python3 gpt_rt_sim.py
```
2. #### Input handler real-time simulation

```bash
$ cd xdevs/examples/gpt
$ python3 gpt_rt_ih_sim.py
```
However, in order to be able to completely understand the system you must execute a TCP client to send the input events to the model. 
The following code, show a basic example of a TCP client that sends an input event to the model. 
It is important to keep in mind that the expect message of the TCP Input handler is `Port_name,message` as it is specified in `xdevs.plugins.input_handlers.tcp`
```bash
import socket

HOST = 'LocalHost' 
PORT = 4321

c = socket.socket(socket.AF_INET,socket.SOCK_STREAM) # AF_INET: IPv4, SOCK_STREAM: TCP

c.connect((HOST,PORT))

c.sendall('ih_in,TCP'.encode()) # The data is 'port_name,msg'
```

3. #### Output handler real-time simulation

```bash
$ cd xdevs/examples/gpt
$ python3 gpt_rt_oh_sim.py
```
In order to capture the outgoing events of the model, you must execute a TCP server to receive the output events.
A basic TCP server is shown below:
```bash
import socket

HOST = 'LocalHost' 
PORT = 4321

s = socket.socket(socket.AF_INET,socket.SOCK_STREAM) # AF_INET: IPv4, SOCK_STREAM: TCP

s.bind((HOST,PORT))
s.listen()

s_con, add = s.accept()
print(f'Connected to: {add}')
while True:
    try:
        data = s_con.recv(1024) # 1024 is the buffer size
        data = data.decode()
        if not data:
            print(f'Client disconnected: {add}')
            break
        print(f'data received is: {data}')
    except ConnectionResetError:
        print(f'Client closed unexpectedly: {add}')
        break
````

4. #### Input and Output handlers real-time simulation

````bash
$ cd xdevs/examples/gpt
$ python3 gpt_rt_ih_oh_sim.py
````
If you want to test the system properly, you will have to execute the server TCP first, then run the example and later 
execute the client TCP to send the input events to the model.