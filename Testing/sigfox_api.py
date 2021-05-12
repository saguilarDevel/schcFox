import requests
import json
import numpy as np

device = "4D5A87"
user = '5ef13a40e833d97984411c43'
passwd = '4181ccbc3f573d2f77eba1e3e6aad35c'

# get last 100 messages
response_json = requests.get(f"https://api.sigfox.com/v2/devices/{device}/messages", auth=(user, passwd)).json()
with open("response_json.json", 'w') as f:
    json.dump(response_json, f)

with open("response_json.json", 'r') as json_file:
    msg_array = json.load(json_file)['data']
    rssi_array = []
    snr_array = []
    lqi_array = []
    received = 0
    for message in msg_array:
        if message['data'].startswith('41'):
            received += 1
        rssi_array.append(float(message['rinfos'][0]['rssi']))
        snr_array.append(float(message['rinfos'][0]['snr']))
        lqi_array.append(int(message['lqi']))

    print(f"Received {received} messages out of 100.\n"
          f"====RSSI====\n"
          f"Mean: {np.mean(rssi_array)} dBm\n"
          f"SDev: {np.std(rssi_array)} dBm\n"
          f"====SNR====\n"
          f"Mean: {np.mean(snr_array)} dB\n"
          f"SDev: {np.std(snr_array)} dB\n"
          f"====LQI====\n"
          f"Median: {np.median(lqi_array)}\n"
          f"SDev: {np.std(lqi_array)}\n")
