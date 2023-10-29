import socket
import time
s = socket.socket()
s.connect(('192.168.56.1', 9009))
client = input('client : ')

while True:
    s.send('client {}'.format(client).encode('utf-8'))
    time.sleep(2)
