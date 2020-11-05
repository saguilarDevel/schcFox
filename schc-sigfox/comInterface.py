from network import Sigfox
import socket
# Chronometers for testing
from machine import Timer
import time

class ComInterface(object):
    """ Static Class to manage the communication to the Radio """

    the_socket = None
    sg = None
    @staticmethod
    def initialize():
        # init Sigfox for RCZ1 (Europe)
        cls.sg = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ1)
        # create a Sigfox socket
        cls.the_socket = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)
        # make the socket blocking
        cls.the_socket.setblocking(True)


    @staticmethod
    def send_sigfox(cls, data,timeout, downlink_enable = False, downlink_mtu = 8):
	""" Function to send messages to the sigfox cloud  """
	# Set the timeout for RETRANSMISSION_TIMER_VALUE.
	sleep_after = 0
	cls.the_socket.settimeout(timeout)
	print("Socket timeout: {}".format(timeout))
	if downlink_enable:
		ack = None
		# wait for a downlink after sending the uplink packet
		cls.the_socket.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, True)
		try:
			# send uplink data
			pycom.rgbled(0x6600CC) # purple
			print("Sending and waiting response at: {}".format(chrono.read()))
			cls.the_socket.send(data)
			ack = cls.the_socket.recv(downlink_mtu)	
			print("Response received at: {}: ".format(chrono.read()))
			print('ack -> {}'.format(ack))
			print('message RSSI: {}'.format(sigfox.rssi()))
			# ack = ''.join(byte.bin for byte in ack)
			# ack =bytearray(b'\x07\xf7\xff\xff\xff\xff\xff\xff')
			ack = ''.join("{:08b}".format(int(byte)) for byte in ack)
			print('ack string -> {}'.format(ack))
			#time.sleep(wait_time)
		except OSError as e:
			# No message was received ack=None
			print("Error at: {}: ".format(chrono.read()))
			print('Error number {}, {}'.format(e.args[0],e))
			if e.args[0] == 11:
				# Retry Logic
				print('Error {}, {}'.format(e.args[0],e))
		time.sleep(sleep_after)
		return ack

	else:
		# make the socket uplink only
		cls.the_socket.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, False)

		try:
			# send uplink data
			pycom.rgbled(0x7f0000) # red
			print("Sending with no response at: {}".format(chrono.read()))
			cls.the_socket.send(data)
			print("data sent at: {}: ".format(chrono.read()))
			print('message RSSI: {}'.format(sigfox.rssi()))
			#time.sleep(wait_time)
		except OSError as e:
			print("Error at: {}: ".format(chrono.read()))
			print('Error number {}, {}'.format(e.args[0],e))
			if e.args[0] == 11:
				# Retry Logic
				print('Error {}, {}'.format(e.args[0],e))	
		time.sleep(sleep_after)
		return None

