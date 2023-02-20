import threading
import serial
import logging

logging.basicConfig(level=logging.INFO)

# define the serial ports to listen to
serial_ports = ['COM5', 'COM6']

# create a dictionary to store incoming data for each port
data = {port: [] for port in serial_ports}

# create a thread function to listen to a port
def listen(port):
    ser = serial.Serial(port, 115200)
    for i in range(10):
        while ser.in_waiting == 0:
            pass
        else:
            incoming_data = ser.readline().decode('utf-8').rstrip()
            # append the data to the list for this port
            data[port].append(incoming_data)
            logging.info(f'Got new data for {port}')

    print(data[port])

# create a thread for each port
threads = []
for port in serial_ports:
    t = threading.Thread(target=listen, args=(port,))
    threads.append(t)
    t.start()

# wait for all threads to finish
for t in threads:
    t.join()
    print("I'm here now")