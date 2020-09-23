# -*- coding: utf-8 -*-
# import getopt
# import socket
# import sys
# import time
# import filecmp

#Microphyton imports
import pycom
import sys
import time
import math
from network import Sigfox
import socket
import ubinascii

from Entities.Fragmenter import Fragmenter
from Entities.Sigfox import Sigfox_Entity
from Messages.Fragment import Fragment



def zfill(string, width):
	if len(string) < width:
		return ("0" * (width - len(string))) + string
	else:
		return string

pycom.heartbeat(True)
print("This is the SENDER script for a Sigfox Uplink transmission example")

# if len(sys.argv) < 4:
# 	print("python sender.py [IP] [PORT] [FILENAME] [-hv]")
# 	sys.exit()

verbose = True

# try:
# 	opts, args = getopt.getopt(sys.argv[4:], "hv")
# 	for opt, arg in opts:
# 		if opt == '-h':
# 			print("python sender.py [IP] [PORT] [FILENAME] [-hv]")
# 			sys.exit()
# 		elif opt == '-v':
# 			verbose = True
# 		else:
# 			print("Unhandled")
# except getopt.GetoptError as err:
# 	print(str(err))

# ip = sys.argv[1]
# port = int(sys.argv[2])
# filename = sys.argv[3]
filename = 'example.txt'
# address = (ip, port)


pycom.heartbeat(False)

pycom.rgbled(0x007f00) # green
# Read the file to be sent.
pycom.rgbled(0x7f7f00) # yellow
with open(filename, "rb") as data:
	f = data.read()
	payload = bytearray(f)

pycom.rgbled(0x007f00) # green
# Initialize variables.
total_size = len(payload)
current_size = 0
percent = 0
ack = None
last_ack = None
i = 0
current_window = 0
profile_uplink = Sigfox_Entity("UPLINK", "ACK ON ERROR")
profile_downlink = Sigfox_Entity("DOWNLINK", "NO ACK")
# init Sigfox for RCZ1 (Europe)
sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ1)

# create a Sigfox socket
the_socket = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)

# make the socket blocking
the_socket.setblocking(True)
# wait time required if blocking set to False
wait_time = 5

# the_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Fragment the file.
fragmenter = Fragmenter(profile_uplink, payload)
fragment_list = fragmenter.fragment()

# The fragment sender MUST initialize the Attempts counter to 0 for that Rule ID and DTag value pair
# (a whole SCHC packet)
attempts = 0
retransmitting = False
fragment = None

if len(fragment_list) > (2 ** profile_uplink.M) * profile_uplink.WINDOW_SIZE:
	print(len(fragment_list))
	print((2 ** profile_uplink.M) * profile_uplink.WINDOW_SIZE)
	print("The SCHC packet cannot be fragmented in 2 ** M * WINDOW_SIZE fragments or less. A Rule ID cannot be selected.")
	# What does this mean?

# Start sending fragments.
while i < len(fragment_list):

	if not retransmitting:
		pycom.rgbled(0x7f7f00) # yellow
		# A fragment has the format "fragment = [header, payload]".
		data = bytes(fragment_list[i][0] + fragment_list[i][1])

		if verbose:
			print(str(i) + "th fragment:")
			print("data -> {}".format(data))
			print("fragment list -> {}".format(fragment_list[i][1]))

		# Convert to a Fragment class for easier manipulation.
		fragment = Fragment(profile_uplink, fragment_list[i])

		current_size += len(fragment_list[i][1])
		percent = round(float(current_size) / float(total_size) * 100, 2)
		wait_receive = False
		# Send the data.
		# If a fragment is an All-0 or an All-1:
		if retransmitting or fragment.is_all_0() or fragment.is_all_1():
			print('Preparing for sending All-0 or All-1')
			# wait for a downlink after sending the uplink packet
			the_socket.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, True)
			
			# Set the timeout for RETRANSMISSION_TIMER_VALUE.
			the_socket.settimeout(profile_uplink.RETRANSMISSION_TIMER_VALUE)
			try:
				# send uplink data
				pycom.rgbled(0x6600CC) # purple
				print("Sending... blocking")
				the_socket.send(data)
				print("Send... unblocking")
				print("waiting for response... blocking")
				ack = the_socket.recv(profile_downlink.MTU)	
				print('ack -> {}'.format(ack))
				# ack = ''.join(byte.bin for byte in ack)
				# ack =bytearray(b'\x07\xf7\xff\xff\xff\xff\xff\xff')
				ack = ''.join("{:08b}".format(int(byte)) for byte in ack)
				print('ack -> {}'.format(ack))
				#time.sleep(wait_time)
			except OSError as e:
				print('Error number {}, {}'.format(e.args[0],e))
				if e.args[0] == 11:
					# Retry Logic
					print('Error {}, {}'.format(e.args[0],e))
		else:
			# make the socket uplink only
			the_socket.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, False)

			try:
				# send uplink data
				pycom.rgbled(0x7f0000) # red
				print("Sending... blocking")
				the_socket.send(data)
				print("Send... unblocking")
				#time.sleep(wait_time)
			except OSError as e:
				print('Error number {}, {}'.format(e.args[0],e))
				if e.args[0] == 11:
					# Retry Logic
					print('Error {}, {}'.format(e.args[0],e))
		# the_socket.sendto(data, address)
		pycom.rgbled(0x7f7f00) # yellow
		print(str(current_size) + " / " + str(total_size) + ", " + str(percent) + "%")


	# If a fragment is an All-0 or an All-1:
	if retransmitting or fragment.is_all_0() or fragment.is_all_1():

		# Juan Carlos dijo que al enviar un ACKREQ el contador se reinicia.
		attempts = 0

		# Set the timeout for RETRANSMISSION_TIMER_VALUE.
		the_socket.settimeout(profile_uplink.RETRANSMISSION_TIMER_VALUE)

		while attempts < profile_uplink.MAX_ACK_REQUESTS:

			# Try receiving an ACK from the receiver.
			try:
						
				# ack, address = the_socket.recvfrom(profile_downlink.MTU)
				print("ACK received. {}".format(ack))
				index = profile_uplink.RULE_ID_SIZE + profile_uplink.T + profile_uplink.M
				bitmap = ack[index:index + profile_uplink.BITMAP_SIZE]
				ack_window = int(ack[profile_uplink.RULE_ID_SIZE + profile_uplink.T:index], 2)
				print("ACK_WINDOW " + str(ack_window))
				print(ack)
				print(bitmap)

				index_c = index + profile_uplink.BITMAP_SIZE
				c = ack[index_c]

				print(c)

				# If the C bit of the ACK is set to 1 and the fragment is an All-1 then we're done.
				if c == '1' and fragment.is_all_1():
					if ack_window == current_window:
						print("Last ACK received: Fragments reassembled successfully. End of transmission.")
						break
					else:
						print("Last ACK window does not correspond to last window")
						exit(1)

				# If the C bit is set to 1 and the fragment is an All-0 then something naughty happened.
				elif c == '1' and fragment.is_all_0():
					print("You shouldn't be here. (All-0 with C = 1)")
					exit(1)

				# If the C bit has not been set:
				elif c == '0':

					resent = False
					# Check the bitmap.
					for j in range(len(bitmap)):
						# If the j-th bit of the bitmap is 0, then the j-th fragment was lost.
						if bitmap[j] == '0':

							print("The " + str(j) + "th (" + str(
								(2 ** profile_uplink.N - 1) * ack_window + j) + " / " + str(
								len(fragment_list)) + ") fragment was lost! Sending again...")

							# Try sending again the lost fragment.
							try:
								fragment_to_be_resent = fragment_list[(2 ** profile_uplink.N - 1) * ack_window + j]
								data_to_be_resent = bytes(fragment_to_be_resent[0] + fragment_to_be_resent[1])
								print(data_to_be_resent)
								the_socket.send(data_to_be_resent)
								# the_socket.sendto(data_to_be_resent, address)
								resent = True

							# If the fragment wasn't found, it means we're at the last window with no fragment
							# to be resent. The last fragment received is an All-1.
							except IndexError:
								print("No fragment found.")
								pycom.rgbled(0x7f0000) # red
								resent = False
								retransmitting = False

								# Request last ACK sending the All-1 again.
								the_socket.send(data)
								# the_socket.sendto(data, address)

					# After sending the lost fragments, send the last ACK-REQ again
					if resent:
						the_socket.send(data)
						# the_socket.sendto(data, address)
						retransmitting = True
						break

					# After sending the lost fragments, if the last received fragment was an All-1 we need to receive
					# the last ACK.
					if fragment.is_all_1():

						# Set the timeout for RETRANSMISSION_TIMER_VALUE
						the_socket.settimeout(profile_uplink.RETRANSMISSION_TIMER_VALUE)

						# Try receiving the last ACK.
						try:
							last_ack = the_socket.recv(profile_downlink.MTU)
							# last_ack, address = the_socket.recvfrom(profile_downlink.MTU)
							c = last_ack.decode()[index_c]

							# If the C bit is set to 1 then we're done.
							if c == '1':
								print(ack_window)
								print(current_window)
								if ack_window == (current_window % 2**profile_uplink.M):
									print("Last ACK received: Fragments reassembled successfully. End of transmission. (While retransmitting)")
									break
								else:
									print("Last ACK window does not correspond to last window. (While retransmitting)")
									exit(1)

						# If the last ACK was not received, raise an error.
						except socket.timeout:
							pycom.rgbled(0x7f0000) # red
							attempts += 1
							if attempts < profile_uplink.MAX_ACK_REQUESTS:

								# TODO: What happens when the ACK gets lost?

								print("No ACK received (RETRANSMISSION_TIMER_VALUE). Waiting for it again...")
							else:
								print("MAX_ACK_REQUESTS reached. Goodbye.")
								print("A sender-abort MUST be sent...")
								exit(1)

				# Proceed to next window.
				print("Proceeding to next window")
				resent = False
				retransmitting = False
				current_window += 1
				break

			# If no ACK was received
			except socket.timeout:
				pycom.rgbled(0x7f0000) # red
				attempts += 1
				if attempts < profile_uplink.MAX_ACK_REQUESTS:

					# TODO: What happens when the ACK gets lost?

					print("No ACK received (RETRANSMISSION_TIMER_VALUE). Waiting for it again...")
				else:
					print("MAX_ACK_REQUESTS reached. Goodbye.")
					print("A sender-abort MUST be sent...")
					exit(1)
		else:
			print("MAX_ACK_REQUESTS reached. Goodbye.")
			print("A sender-abort MUST be sent...")
			exit(1)

	# Continue to next fragment
	if not retransmitting:
		i += 1

# Close the socket and wait for the file to be reassembled
the_socket.close()
time.sleep(1)

# Compare if the reassembled file is the same as the original (only on offline testing)
print(filecmp.cmp("received.txt", filename))