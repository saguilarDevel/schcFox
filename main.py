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
import json

from Entities.Fragmenter import Fragmenter
from Entities.Sigfox import Sigfox_Entity
from Messages.Fragment import Fragment

# Chronometers for testing
from machine import Timer
import time

def zfill(string, width):
	if len(string) < width:
		return ("0" * (width - len(string))) + string
	else:
		return string

def send_sigfox(the_socket, fragment, data, timeout, downlink_enable = False, downlink_mtu = 8):
	""" Function to send messages to the sigfox cloud  """
	# Set the timeout for RETRANSMISSION_TIMER_VALUE.
	sleep_after = 0
	the_socket.settimeout(timeout)
	print("Socket timeout: {}".format(timeout))
	# clear current_fragment before insertig new data
	current_fragment = {}
	current_fragment['RULE_ID'] = fragment.header.RULE_ID
	current_fragment['W'] = fragment.header.W
	current_fragment['FCN'] = fragment.header.FCN
	current_fragment['data'] = data
	if downlink_enable:
		ack = None
		# wait for a downlink after sending the uplink packet
		the_socket.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, True)
		try:
			# send uplink data
			current_fragment['download_enable'] = True
			current_fragment['ack_received'] = False
			pycom.rgbled(0x7700CC) # purple
			print("Sending and waiting response at: {}".format(chrono.read()))
			current_fragment['sending_start'] = chrono.read()
			the_socket.send(data)
			ack = the_socket.recv(downlink_mtu)
			current_fragment['sending_end'] = chrono.read()
			current_fragment['send_time'] = current_fragment['sending_end'] - current_fragment['sending_start']
			current_fragment['rssi'] = sigfox.rssi()
			print("Response received at: {}: ".format(chrono.read()))
			print('ack -> {}'.format(ack))
			print('message RSSI: {}'.format(sigfox.rssi()))
			# ack = ''.join(byte.bin for byte in ack)
			# ack =bytearray(b'\x07\xf7\xff\xff\xff\xff\xff\xff')
			ack = ''.join("{:08b}".format(int(byte)) for byte in ack)
			print('ack string -> {}'.format(ack))
			current_fragment['ack'] = ack if ack else ""
			current_fragment['ack_received'] = True
			#time.sleep(wait_time)
		except OSError as e:
			# No message was received ack=None
			current_fragment['sending_end'] = chrono.read()
			current_fragment['send_time'] = current_fragment['sending_end'] - current_fragment['sending_start']
			current_fragment['rssi'] = sigfox.rssi()
			current_fragment['ack'] = ""
			current_fragment['ack_received'] = False
			print("Error at: {}: ".format(chrono.read()))
			print('Error number {}, {}'.format(e.args[0],e))
			pycom.rgbled(0xff0000)
			if e.args[0] == 11:
				# Retry Logic
				print('Error {}, {}'.format(e.args[0],e))
		time.sleep(sleep_after)
		print("current_fragment:{}".format(current_fragment))
		fragments_info_array.append(current_fragment)
		return ack

	else:
		# make the socket uplink only
		the_socket.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, False)

		try:
			# send uplink data
			current_fragment['download_enable'] = False
			current_fragment['ack_received'] = False
			pycom.rgbled(0x00ffff) # cyan
			print("Sending with no response at: {}".format(chrono.read()))
			current_fragment['sending_start'] = chrono.read()
			the_socket.send(data)
			current_fragment['sending_end'] = chrono.read()
			current_fragment['send_time'] = current_fragment['sending_end'] - current_fragment['sending_start']
			current_fragment['rssi'] = sigfox.rssi()
			current_fragment['ack'] = ""
			print("data sent at: {}: ".format(chrono.read()))
			print('message RSSI: {}'.format(sigfox.rssi()))
			#time.sleep(wait_time)
		except OSError as e:
			current_fragment['sending_end'] = chrono.read()
			current_fragment['send_time'] = current_fragment['sending_end'] - current_fragment['sending_start']
			current_fragment['rssi'] = sigfox.rssi()
			current_fragment['ack'] = ""
			print("Error at: {}: ".format(chrono.read()))
			print('Error number {}, {}'.format(e.args[0],e))
			pycom.rgbled(0xff0000)
			if e.args[0] == 11:
				# Retry Logic
				print('Error {}, {}'.format(e.args[0],e))	
		time.sleep(sleep_after)
		print("current_fragment:{}".format(current_fragment))
		fragments_info_array.append(current_fragment)
		return None

# Declare states for state machine
STATE_INIT = "STATE_INIT"
STATE_SEND = "STATE_SEND"
STATE_WAIT4ACK = "STATE_WAIT4ACK"
STATE_END = "STATE_END"
STATE_ERROR = "STATE_ERROR"

STATE_RESEND = "STATE_RESEND"

#State management variables
CURRENT_STATE = ""
NEXT_STATE = ""


# STATE INIT 
# INIT variables 
# Read file to tx
# Fragmentation process
CURRENT_STATE = STATE_INIT


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
filename = 'example4.txt'
# address = (ip, port)


pycom.heartbeat(False)

pycom.rgbled(0x007f00) # green
# Read the file to be sent.
pycom.rgbled(0x7f7f00) # yellow
print("Reading file {}".format(filename))
with open(filename, "rb") as data:
	f = data.read()
	payload = bytearray(f)

pycom.rgbled(0x007f00) # green

# Init Chrono
chrono = Timer.Chrono()
laps = []
fragmentation_time = 0
start_sending_time = 0
end_sending_time = 0

# stats variables (for testing)
current_fragment = {}
fragments_info_array = []

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
# wait_time = 5

# the_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Start Time
chrono.start()




# Fragment the file.
fragmenter = Fragmenter(profile_uplink, payload)
fragment_list = fragmenter.fragment()

# read elapsed time without stopping
fragmentation_time = chrono.read()
print("fragmentation time -> {}".format(fragmentation_time))

# The fragment sender MUST initialize the Attempts counter to 0 for that Rule ID and DTag value pair
# (a whole SCHC packet)
attempts = 0
retransmitting = False
fragment = None

# if len(fragment_list) > (2 ** profile_uplink.M) * profile_uplink.WINDOW_SIZE:
# 	print(len(fragment_list))
# 	print((2 ** profile_uplink.M) * profile_uplink.WINDOW_SIZE)
# 	print("The SCHC packet cannot be fragmented in 2 ** M * WINDOW_SIZE fragments or less. A Rule ID cannot be selected.")
# 	# What does this mean?
# 	# Sending packet does not fit (should be tested in fragmentation)


start_sending_time = chrono.read()
# Start sending fragments.
CURRENT_STATE = STATE_SEND
while i < len(fragment_list):
	current_fragment = {}
	laps.append(chrono.read())
	print("laps - > {}".format(laps))
	if not retransmitting:
		pycom.rgbled(0x7f7f00) # yellow
		# A fragment has the format "fragment = [header, payload]".
		data = bytes(fragment_list[i][0] + fragment_list[i][1])


		# Convert to a Fragment class for easier manipulation.
		fragment = Fragment(profile_uplink, fragment_list[i])
		# current_fragment['RULE_ID'] = fragment.header.RULE_ID
		# current_fragment['W'] = fragment.header.W
		# current_fragment['FCN'] = fragment.header.FCN
		# current_fragment['data'] = data
		
		if verbose:
			print(str(i) + "th fragment:")
			
			print("RuleID:{}, WINDOW:{}, FCN:{}".format(fragment.header.RULE_ID,fragment.header.W,fragment.header.FCN))
			print("data -> {}".format(data))
			print("fragment list -> {}".format(fragment_list[i][1]))

		current_size += len(fragment_list[i][1])
		percent = round(float(current_size) / float(total_size) * 100, 2)
		wait_receive = False
		# Send the data.
		# If a fragment is an All-0 or an All-1:
		if fragment.is_all_0() or fragment.is_all_1():
			#clearing ack variable
			ack = None
			print('Preparing for sending All-0 or All-1')
			# current_fragment['sending_start'] = chrono.read()
			ack = send_sigfox(the_socket, fragment, data, profile_uplink.RETRANSMISSION_TIMER_VALUE, True, profile_downlink.MTU)
			# current_fragment['sending_end'] = chrono.read()
			# current_fragment['send_time'] = current_fragment['sending_end'] - current_fragment['sending_start']
			# current_fragment['rssi'] = sigfox.rssi()
		else:
			# current_fragment['sending_start'] = chrono.read()
			send_sigfox(the_socket, fragment, data, profile_uplink.RETRANSMISSION_TIMER_VALUE, False)
			# current_fragment['sending_end'] = chrono.read()
			# current_fragment['send_time'] = current_fragment['sending_end'] - current_fragment['sending_start']
			# current_fragment['rssi'] = sigfox.rssi()

		# print("current_fragment:{}".format(current_fragment))
		# fragments_info_array.append(current_fragment)
		# the_socket.sendto(data, address)
		pycom.rgbled(0x7f7f00) # yellow
		print(str(current_size) + " / " + str(total_size) + ", " + str(percent) + "%")

	# No ACK was received for the intermediate window
	if fragment.is_all_0() and ack is None:
		print('No ACK received, continue sending fragments')
		# TODO: add logic if fragment are lost.

	# No ACK was received for the last window
	# it should, so a SCHC ACK must be send.
	# Not sure if RETRANSMISSION_TIMER_VALUE was expired, but the 
	# reception window has expired, so there is no opportunity
	# from the receiver to send an ACK.
	# elif fragment.is_all_1() and ack is None:

	# If a fragment is an All-0 or an All-1:
	elif retransmitting or fragment.is_all_0() or fragment.is_all_1():

		# Juan Carlos dijo que al enviar un ACKREQ el contador se reinicia.
		attempts = 0

		# Set the timeout for RETRANSMISSION_TIMER_VALUE.
		the_socket.settimeout(profile_uplink.RETRANSMISSION_TIMER_VALUE)

		while attempts < profile_uplink.MAX_ACK_REQUESTS:
			print("attempts:{}".format(attempts))
			# Try receiving an ACK from the receiver.
			# Check if the ACK = None
			if ack is not None:

			# try:
						
				# ack, address = the_socket.recvfrom(profile_downlink.MTU)
				""" ACK Messages Format
				Uplink ACK-on-Error Mode: Single-byte SCHC Header
				Rule ID size:  3 bits
				Dtag: 0 bits
				Window index (W) size (M): 2 bits


				ACK Success: [ Rule ID | Dtag |   W  | C-1 | (P-0) ]
    			ACK Failure: [ Rule ID | Dtag |   W  | C-0 | Bitmap | (P-0) ]
    			Recv Abort : [ Rule ID | Dtag |  W-1 | C-1 | (P-1) ]

				Example ACK:
				0000000000001111111111111111111111111111111111111111111111111111
				RuleID: 000
				W: 00
				C: 0
				Bitmap: 0000001
				pading: 111111111111111111111111111111111111111111111111111
				ID|W|
				0000000000001111111111111111111111111111111111111111111111111111
				     ^_index
					 
				ID|W|c
				0000000000001111111111111111111111111111111111111111111111111111
				      ^_index
				  
				"""
				print("ACK received. {}".format(ack))
				# index = profile_uplink.RULE_ID_SIZE + profile_uplink.T + profile_uplink.M
				index = profile_uplink.RULE_ID_SIZE + profile_uplink.T + profile_uplink.M + 1
				print('index:{}'.format(index))
				bitmap = ack[index:index + profile_uplink.BITMAP_SIZE]
				ack_window = int(ack[profile_uplink.RULE_ID_SIZE + profile_uplink.T:index - 1], 2)
				print("ACK_WINDOW " + str(ack_window))
				print("ack -> {}".format(ack))
				print("bitmap -> {}".format(bitmap))

				# index_c = index + profile_uplink.BITMAP_SIZE
				index_c = index - 1

				c = ack[index_c]

				print("c -> {}".format(c))

				# If the C bit of the ACK is set to 1 and the fragment is an All-1 then we're done.
				if c == '1' and fragment.is_all_1():
					if ack_window == current_window:
						print("Last ACK received: Fragments reassembled successfully. End of transmission.")
						
						break
					else:
						print("Last ACK window {} does not correspond to last window {}".format(ack_window,current_window))
						break
						exit(1)

				# If the C bit is set to 1 and the fragment is an All-0 then something naughty happened.
				# you should received an ACK with C = 0 or no ACK at all
				elif c == '1' and fragment.is_all_0():
					print("You shouldn't be here. (All-0 with C = 1)")
					break
					exit(1)

				# If the C bit has not been set:
				elif c == '0':
					print('c bit = 0, resent = False')
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



								send_sigfox(the_socket, fragment_to_be_resent, data_to_be_resent, profile_uplink.timeout, False)
								# the_socket.send(data_to_be_resent)
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
								last_ack = None
								last_ack = send_sigfox(the_socket, fragment, data, profile_uplink.timeout, True)
								# the_socket.sendto(data, address)

					# After sending the lost fragments, send the last ACK-REQ again
					if resent:
						print("resend")

						last_ack = None
						last_ack = send_sigfox(the_socket, fragment, data, profile_uplink.timeout, True)
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
							# last_ack = the_socket.recv(profile_downlink.MTU)
							# last_ack, address = the_socket.recvfrom(profile_downlink.MTU)
							# c = last_ack.decode()[index_c]
							c = ack.decode()[index_c]

							# If the C bit is set to 1 then we're done.
							if c == '1':
								print(ack_window)
								print(current_window)
								if ack_window == (current_window % 2**profile_uplink.M):
									print("Last ACK received: Fragments reassembled successfully. End of transmission. (While retransmitting)")
									pycom.rgbled(0x007f00) # green
									break
								else:
									print("Last ACK window does not correspond to last window. (While retransmitting)")
									break
									exit(1)

						# If the last ACK was not received, raise an error.
						except socket.timeout:
							pycom.rgbled(0x7f0000) # red
							attempts += 1
							if attempts < profile_uplink.MAX_ACK_REQUESTS:

								# TODO: What happens when the ACK gets lost?
								# Send ACK-REQ or All-1
								time.sleep(profile_uplink.RETRANSMISSION_TIMER_VALUE)
								print("No ACK received (RETRANSMISSION_TIMER_VALUE). Waiting for it again...")

							else:
								print("MAX_ACK_REQUESTS reached. Goodbye.")
								print("A sender-abort MUST be sent...")
								break
								exit(1)

				# Proceed to next window.
				print("Proceeding to next window")
				resent = False
				retransmitting = False
				current_window += 1
				break

			# If no ACK was received
			else:
				print("NO ACK RECEIVED")
				
				# except socket.timeout:
				pycom.rgbled(0x7f0000) # red
				attempts += 1
				if attempts < profile_uplink.MAX_ACK_REQUESTS:
					print("Waiting for RETRANSMISSION_TIMER_VALUE time:{}".format(profile_uplink.RETRANSMISSION_TIMER_VALUE))
					# TODO: What happens when the ACK gets lost?
					# Should send an ACK REQ after Retransmission Timer expires?
					# The Number of ACK REQ that should be send depends in the MAX ACK REQ variable.?
					# time.sleep(profile_uplink.RETRANSMISSION_TIMER_VALUE)
					time.sleep(5)
					print("Attempt number: {}".format(attempts))
					print("No ACK received (RETRANSMISSION_TIMER_VALUE expired). Sending last SCHC fragment...")
					# current_fragment = {}
					# current_fragment['RULE_ID'] = fragment.header.RULE_ID
					# current_fragment['W'] = fragment.header.W
					# current_fragment['FCN'] = fragment.header.FCN
					# current_fragment['data'] = data
					ack = None
					# current_fragment['sending_start'] = chrono.read()
					ack = send_sigfox(the_socket, fragment, data, profile_uplink.RETRANSMISSION_TIMER_VALUE, True, profile_downlink.MTU)
					# current_fragment['sending_end'] = chrono.read()
					# current_fragment['send_time'] = current_fragment['sending_end'] - current_fragment['sending_start']
					# current_fragment['rssi'] = sigfox.rssi()
					# print(current_fragment)
					# fragments_info_array.append(current_fragment)

				else:
					print("MAX_ACK_REQUESTS reached. Goodbye.")
					print("A sender-abort MUST be sent...")
					break
					exit(1)
		else:
			print("MAX_ACK_REQUESTS reached. Goodbye.")
			print("A sender-abort MUST be sent...")
			break
			exit(1)

	# Continue to next fragment
	if not retransmitting:
		i += 1
end_sending_time = chrono.read()
# fragments_info_array = [{'sending_end': 9.444577, 'W': '00', 'RULE_ID': '00', 'send_time': 9.375487, 'data': b'\x0612345678910', 'sending_start': 0.06908989, 'FCN': '110'}, {'sending_end': 48.76381, 'W': '00', 'RULE_ID': '00', 'send_time': 39.27128, 'data': b'\x0711121314151', 'sending_start': 9.492536, 'FCN': '111'}]
print('Stats')
# print(fragments_info_array)

filename_stats = "stats_file.json"
print("Writing to file {}".format(filename_stats))
f = open(filename_stats, "w")
write_string = ''
results_json = {}
for index, fragment in enumerate(fragments_info_array):
	# print(fragment,index)
	print('{} - W:{}, FCN:{}, send Time:{}'.format(index, fragment['W'],fragment['FCN'],fragment['send_time']))
	write_string = write_string + '{} - W:{}, FCN:{}, send Time:{}'.format(index, fragment['W'],fragment['FCN'],fragment['send_time']) + "\n"
	results_json["{}".format(index)] = fragment

print("results_json:{}".format(results_json))

# f.write('{} - W:{}, FCN:{}, send Time:{}'.format(index, fragment['W'],fragment['FCN'],fragment['send_time']))
# print(write_string)
# with open(filename_stats,'w') as out:
#     out.writelines(fragments_info_array)
print("fragmentation time: {}".format(fragmentation_time))
print("total sending time: {}".format(end_sending_time-start_sending_time))
print("total number of fragments sent: {}".format(len(fragments_info_array)))
f.write(json.dumps(results_json))
f.close()
pycom.heartbeat(True)
# Close the socket and wait for the file to be reassembled
the_socket.close()
time.sleep(1)
f = open(filename_stats)
print(f.readlines())
f.close()
print("Reading file {}".format(filename_stats))
with open(filename_stats, "rb") as data:
	print(data.read())

# Compare if the reassembled file is the same as the original (only on offline testing)
# print(filecmp.cmp("received.txt", filename))