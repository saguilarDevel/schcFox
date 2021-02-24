import binascii
import socket

from network import Sigfox

sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ4)
print(binascii.hexlify(sigfox.id()))
print(binascii.hexlify(sigfox.pac()))
s = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)
s.setblocking(True)
s.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, True)

s.send(bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]))
print("Sent.")

ack = s.recv(64)
print(ack)
print(type(ack))
