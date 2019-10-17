import timeit
import Adafruit_ADXL345
import os
import socket

def gatherData():
    
    accel = Adafruit_ADXL345.ADXL345()
    data = bytearray()

    while (len(data)<123):
        # Read the X, Y, Z axis acceleration values and print them.
        x, y, z = accel.read()
        newData = "X=" + str(x) + ",Y=" + str(y) + ",Z=" + str(z) + "; "
        new_data_bytes = bytearray(newData)
        index = 0

        while((len(data)<123)and(index < len(new_data_bytes))): #To collect exactly 123 bytes of data. 
            data.append(new_data_bytes[index])
            index = index + 1
    
    data = bytes(data)
    return data


sock = socket.socket(socket.AF_INET, 
                     socket.SOCK_DGRAM) 

times = ""

UDP_IP = "10.1.1.154"
UDP_PORT = 5005

mysetup = '''
import socket
import os
import Adafruit_ADXL345
from __main__ import gatherData, sock, UDP_IP, UDP_PORT
from __main__ import sock
'''

times = timeit.repeat(setup = mysetup, 
                stmt =  'plaintext = gatherData();' + 
                        'sock.sendto(plaintext, (UDP_IP, UDP_PORT))', 
                repeat = 100,
                number = 1) 

print(times)

sock.sendto(', '.join(map(str,times)), (UDP_IP, UDP_PORT))
