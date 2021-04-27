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
from machine import RTC
import network
import utime

def zfill(string, width):
	if len(string) < width:
		return ("0" * (width - len(string))) + string
	else:
		return string
rtc = RTC()

def setRTCLocalTime():
    
    rtc.ntp_sync("pool.ntp.org")
    utime.sleep_ms(750)
    print('\nRTC Set from NTP to UTC:', rtc.now())
    utime.timezone(60*60)
    print('Adjusted from UTC to +1 timezone', utime.localtime(), '\n')


# setup as a station
ssid = 'PlatisWifi'
password = 'platis2001'
ssid = 'Orange-B6EA'
password = 'e2PNwgLz'
wlan = network.WLAN(mode=network.WLAN.STA)
wlan.connect(ssid, auth=(network.WLAN.WPA2, password))
while not wlan.isconnected():
    time.sleep_ms(50)
print(wlan.ifconfig())

setRTCLocalTime()

# rtc = RTC()
# rtc.ntp_sync("pool.ntp.org")
# time.sleep(5)
# print("time: {}".format(rtc.now()))
print(rtc.now())


# init Sigfox for RCZ4 (Chile)
# sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ4)
# init Sigfox for RCZ1 (Europe)
sigfox = Sigfox(mode=Sigfox.SIGFOX, rcz=Sigfox.RCZ1)

s = socket.socket(socket.AF_SIGFOX, socket.SOCK_RAW)
s.setblocking(True)
# set False for only uplink, true for BIDIR
s.setsockopt(socket.SOL_SIGFOX, socket.SO_RX, True)
s.setsockopt(socket.SOL_SIGFOX, socket.SO_TX_REPEAT, 0)
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
	current_fragment['start_sending_timestamp'] = utime.localtime()
	try:
		pycom.rgbled(0x7700CC) # purple
		print("Sending: {}".format(payload))
		current_fragment['sending_start'] = chrono.read()
		s.send(payload)
		response = s.recv(downlink_mtu)
		current_fragment['sending_end'] = chrono.read()
		current_fragment['end_sending_timestamp'] = utime.localtime()
		current_fragment['send_time'] = current_fragment['sending_end'] - current_fragment['sending_start']
		current_fragment['rssi'] = sigfox.rssi()
		print("response -> {}".format(response))
		decode_response = ''.join("{:08b}".format(int(byte)) for byte in response)
		print('decode_response -> {}'.format(decode_response))
		current_fragment['ack'] = decode_response if decode_response else ""
		current_fragment['ack_received'] = True
	
	except OSError as e:
		current_fragment['end_sending_timestamp'] = utime.localtime()
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
filename_stats = "LoPy_stats_file_v5.13.json"
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
