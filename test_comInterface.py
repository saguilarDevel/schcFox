#Microphyton imports
import pycom
import sys
import time
import math
from network import Sigfox
import socket
import ubinascii
# from schc-sigfox import ComInterface as com

# Chronometers for testing
from machine import Timer
import time

class ComInterface(object):
    """ Static Class to manage the communication to the Radio """

    the_socket = None
    sg = None

    chrono = None

    @staticmethod
    def initialize(chrono):
        ComInterface.chrono = chrono
        # init Sigfox for RCZ1 (Europe)
        ComInterface.sg = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ1)
        # create a Sigfox socket
        ComInterface.the_socket = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)
        # make the socket blocking
        ComInterface.the_socket.setblocking(True)


    @staticmethod
    def send_sigfox(data,timeout, downlink_enable = False, downlink_mtu = 8):
	""" Function to send messages to the sigfox cloud  """
	# Set the timeout for RETRANSMISSION_TIMER_VALUE.
	pycom.rgbled(0x00ff00)
	sleep_after = 0
	ComInterface.the_socket.settimeout(timeout)
	print("Socket timeout: {}".format(timeout))
	if downlink_enable:
		ack = None
		# wait for a downlink after sending the uplink packet
		ComInterface.the_socket.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, True)
		try:
			# send uplink data
			pycom.rgbled(0x6600CC) # purple
			print("Sending and waiting response at: {}".format(ComInterface.chrono.read()))
			ComInterface.the_socket.send(data)
			ack = ComInterface.the_socket.recv(downlink_mtu)	
			print("Response received at: {}: ".format(ComInterface.chrono.read()))
			print('ack -> {}'.format(ack))
			print('message RSSI: {}'.format(sigfox.rssi()))
			ack = ''.join("{:08b}".format(int(byte)) for byte in ack)
			print('ack string -> {}'.format(ack))
			#time.sleep(wait_time)
		except OSError as e:
			# No message was received ack=None
			print("Error at: {}: ".format(ComInterface.chrono.read()))
			print('Error number {}, {}'.format(e.args[0],e))
			pycom.rgbled(0xff0000) # red
			if e.args[0] == 11:
				# Retry Logic
				print('Error {}, {}'.format(e.args[0],e))
		time.sleep(sleep_after)
		return ack

	else:
		# make the socket uplink only
		ComInterface.the_socket.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, True)

		try:
			# send uplink data
			pycom.rgbled(0x00ffff) # cyan
			print("Sending with no response at: {}".format(ComInterface.chrono.read()))
			ComInterface.the_socket.send(data)
			print("data sent at: {}: ".format(ComInterface.chrono.read()))
			print('message RSSI: {}'.format(sigfox.rssi()))
			#time.sleep(wait_time)
		except OSError as e:
			print("Error at: {}: ".format(ComInterface.chrono.read()))
			print('Error number {}, {}'.format(e.args[0],e))
			pycom.rgbled(0xff0000) # red
			if e.args[0] == 11:
				# Retry Logic
				print('Error {}, {}'.format(e.args[0],e))
		time.sleep(sleep_after)
		return None

# Init Chrono
chrono = Timer.Chrono()
# Start Time
chrono.start()
ComInterface.initialize(chrono)
ComInterface.send_sigfox(bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]), 30, False)




