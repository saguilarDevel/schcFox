import network
# from network import WLAN
# import machine

# wlan = WLAN(mode=WLAN.STA)

# ssid = 'Orange-B6EA'
# password = 'e2PNwgLz'

# wlan.connect(ssid=ssid, auth=(WLAN,network.WLAN.WPA2, password))
# while not wlan.isconnected():
#     machine.idle()
# print("WiFi connected succesfully")
# print(wlan.ifconfig())
# https://docs.pycom.io/gettingstarted/programming/ftp/

import network
import time
# setup as a station
ssid = '------'
password = '--------'
wlan = network.WLAN(mode=network.WLAN.STA)
wlan.connect(ssid, auth=(network.WLAN.WPA2, password))
while not wlan.isconnected():
    time.sleep_ms(50)
print(wlan.ifconfig())