# This is the beacon module to be run for experiments...

from network import Sigfox
import socket
import sys
import math
import time
import pycom
import ubinascii
import json
# Chronometers for testing
from machine import Timer

def zfill(string, width):
	if len(string) < width:
		return ("0" * (width - len(string))) + string
	else:
		return string


# init Sigfox for RCZ4 (Chile)
# sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ4)
# init Sigfox for RCZ1 (Europe)
sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ1)

s = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)
s.setblocking(True)
# set False for only uplink, true for BIDIR
s.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, True)
timeout = 45
s.settimeout(timeout)

c = 10
submerged_time = 0
n = 20

# Wait for the beacon to be submerged
time.sleep(submerged_time)


chrono = Timer.Chrono()
# stats variables (for testing)
current_fragment = {}
fragments_info_array = []

# Start Time
chrono.start()

max_payload = 12 # 12 bytes
downlink_mtu = 8*8 # 8 bytes - 64 bits
sleep_after = 0
pycom.heartbeat(False)
# Send n messages to the Sigfox network to test connectivity
for i in range(n):
	print("sending frame number:{}".format(i))
	current_fragment = {}
	string = "{}".format(zfill(str(i), max_payload))
	print(string)
	print(len(string))
	payload = bytes(string.encode())
	print("Sending...")
	# s.send(payload)
	# print("Sent.")
	print(payload)
	current_fragment['data'] = payload
	current_fragment['timeout'] = timeout
	current_fragment['downlink_enable'] = True
	current_fragment['ack_received'] = False
	current_fragment['fragment_size'] = len(payload)
	current_fragment['sending_start'] = 0
	try:
		pycom.rgbled(0x7700CC) # purple
		print("Sending: {}".format(payload))
		current_fragment['sending_start'] = chrono.read()
		s.send(payload)
		response = s.recv(downlink_mtu)
		current_fragment['sending_end'] = chrono.read()
		current_fragment['send_time'] = current_fragment['sending_end'] - current_fragment['sending_start']
		current_fragment['rssi'] = sigfox.rssi()
		print("response -> {}".format(response))
		decode_response = ''.join("{:08b}".format(int(byte)) for byte in response)
		print('decode_response -> {}'.format(decode_response))
		current_fragment['ack'] = decode_response if decode_response else ""
		current_fragment['ack_received'] = True
	
	except OSError as e:
		current_fragment['sending_end'] = chrono.read()
		current_fragment['send_time'] = current_fragment['sending_end'] - current_fragment['sending_start']
		current_fragment['rssi'] = sigfox.rssi()
		current_fragment['ack'] = ""
		current_fragment['ack_received'] = False
		print('Error number {}, {}'.format(e.args[0],e))
		pycom.rgbled(0xff0000)
		if e.args[0] == 11:
			# Retry Logic
			print('Error {}, {}'.format(e.args[0],e))
	print("current_fragment:{}".format(current_fragment))
	fragments_info_array.append(current_fragment)
	time.sleep(sleep_after)

s.close()
print("Done")
filename_stats = "LoPy_stats_file_v5.7.json"
print("Writing to file {}".format(filename_stats))
f = open(filename_stats, "w")
write_string = ''
results_json = {}
for index, fragment in enumerate(fragments_info_array):
	# print(fragment,index)
	if fragment['downlink_enable']:
		print('{} - TT:{}s, DL(E):{}, ack(R):{}'.format(index,fragment['send_time'],fragment['downlink_enable'],fragment['ack_received']))
	else:
		print('{} - TT:{}s'.format(index, fragment['send_time']))

	# write_string = write_string + '{} - W:{}, FCN:{}, send Time:{}, downlink_enable:{}, ack_received:{}'.format(index,
	# 	fragment['W'],fragment['FCN'],fragment['send_time'],fragment['downlink_enable'],fragment['ack_received']) + "\n"
	results_json["{}".format(index)] = fragment
	# results_json[index] = fragment
print("TT: Transmission Time, DL (E): Downlink enable, ack (R): ack received")

f.write(json.dumps(results_json))
f.close()
pycom.heartbeat(True)
# Close the socket and wait for the file to be reassembled

# time.sleep(1)
# print("results_json:{}".format(results_json))

# f.write('{} - W:{}, FCN:{}, send Time:{}'.format(index, fragment['W'],fragment['FCN'],fragment['send_time']))
# print(write_string)
# with open(filename_stats,'w') as out:
#     out.writelines(fragments_info_array)
