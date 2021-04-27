# This is the beacon module to be run for experiments...

from network import Sigfox
import socket
import time

from Entities.SCHCTimer import SCHCTimer


def zfill(string, width):
	if len(string) < width:
		return ("0" * (width - len(string))) + string
	else:
		return string


# init Sigfox for RCZ4 (Chile)
# sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ4)
# init Sigfox for RCZ1 (Europe)
sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ4)

s = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)
s.setblocking(True)

s.settimeout(10)

timer = SCHCTimer(0)

c = 10
n = 100
delay = 0

# Send n messages to the Sigfox network to test connectivity
# s.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, False)
# for i in range(n):
# 	string = "{}{}".format(zfill(str(c), 3), zfill(str(i), 3))
# 	payload = bytes(string.encode())
# 	print("Sending...")
# 	s.send(payload)
# 	print("Sent.")
# 	print(payload)
# 	timer.wait(delay)

s.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, True)
received = 0
for i in range(n//2):
	string = "A{}{}".format(zfill(str(c), 3), zfill(str(i), 3))
	payload = bytes(string.encode())
	try:
		print("Sending...")
		s.send(payload)
		print("Sent.")
		ack = s.recv(64)
		received += 1
		print(ack)
	except OSError as e:
		print("No DL received.")
	timer.wait(delay)

print("received: {}".format(received))
