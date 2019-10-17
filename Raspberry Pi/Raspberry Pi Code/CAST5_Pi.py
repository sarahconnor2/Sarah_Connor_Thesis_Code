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

        while((len(data)<123)and(index < len(new_data_bytes))):  #To collect exactly 123 bytes of data. 
            data.append(new_data_bytes[index])
            index = index + 1

    return bytes(data)


UDP_IP = "10.1.1.154"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

PlainTextList = []
times = ""

mysetup = '''
import socket
import os
import Adafruit_ADXL345
from Encrypt_Decrypt_Functions import CAST5Encrypt, CAST5Decrypt, pad
from __main__ import gatherData
from __main__ import sock
from __main__ import PlainTextList
from Key128 import key

UDP_IP = "10.1.1.154"
UDP_PORT = 5005

'''

times = timeit.repeat(setup = mysetup, 
                stmt = 'plaintext = gatherData();' + 
                        'PlainTextList.append(plaintext);' + 
                        'iv = os.urandom(8);' + 
                        'ciphertext = CAST5Encrypt(plaintext, key, iv);' + 
                        'message = iv + ciphertext;' + 
                        'sock.sendto(message, (UDP_IP, UDP_PORT))', 
                repeat = 100,
                number = 1) 

print(times)

for y in range(0, 100):
    sock.sendto(PlainTextList[y], (UDP_IP, UDP_PORT))

sock.sendto(', '.join(map(str,times)), (UDP_IP, UDP_PORT))

#Check successful message and encryption at the other side. 