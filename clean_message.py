import ubinascii
import socket

from network import Sigfox

sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ4)
s = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)
s.setblocking(True)
s.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, False)

string = ubinascii.unhexlify("{}a434c45414e".format(1))

s.send(string)
print("Sent.")
