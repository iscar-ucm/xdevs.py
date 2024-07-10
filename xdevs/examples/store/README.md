# Instructions for running the store examples

## Virtual time (regular simulation)

To run the store examples with virtual time, you can use the following command:

```bash
$ cd xdevs/examples/store
$ python3 1_vt_simulation.py
```

## Real time with CSV output log

This example runs the store model in real time and uses an output handler to store output events.
The CSV file is saved in the `output` directory.
You can run the example with the following command:

```bash
$ cd xdevs/examples/store
$ python3 2_rt_simulation_csv_output_handler.py
```

## Real time with TCP input clients

This example runs the store model in real time and uses a TCP input handler to inject extra clients.
You can run the example with the following command:

```bash
$ cd xdevs/examples/store
$ python3 3_rt_simulation_tcp_input_handler.py
```

This executable will start a TCP server that listens for incoming connections on `localhost:4321`.
You can connect to the server using a TCP client, such as `netcat`:

```bash
$ nc localhost 4321
```

The client can send messages to the server in the following format:

```
<input_port>,<client_id>?<t_entered>
```

The model only has one input port, called `IP_NewClient`.

## MQTT Example

An MQTT example is provided, in which the connection between two `DEVS` models is created.
The execution of both models should be carried out in parallel.

_First model, MQTT subscriber_
```bash
$ cd xdevs/examples/store
$ python3 4_1_rt_simulation_mqtt_input_handler.py
```

_Second model, MQTT publisher_
```bash
$ cd xdevs/examples/store
$ python3 4_2_rt_simulation_mqtt_output_handler.py
```