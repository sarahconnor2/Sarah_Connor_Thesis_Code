
import os
import socket
message = os.urandom(123)

UDP_IP = "10.1.1.154"
UDP_PORT = 5006

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP


while(1):
    sock.sendto(message, (UDP_IP, UDP_PORT))
    print("Message sent")


    