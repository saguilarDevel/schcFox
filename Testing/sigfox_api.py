import requests
import json
import numpy as np

device = "xxxx"
user = 'xxxxxxxxxxxx'
passwd = 'xxxxxxxxxx'

# get last 100 messages
# response_json = requests.get(f"https://api.sigfox.com/v2/devices/{device}/messages?limit=50", auth=(user, passwd)).json()
# with open("response_json_ack.json", 'w') as f:
#     json.dump(response_json, f)

with open("response_json.json", 'r') as json_file:
# with open("response_json_ack.json", 'r') as json_file:
    msg_array = json.load(json_file)['data']
    rssi_array = []
    snr_array = []
    lqi_array = []
    received = 0
    for message in msg_array:
        if message['data'].startswith('303'):
        # if message['data'].startswith('41'):
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
