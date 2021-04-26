import requests

id = "4d5a87"
user = '5ef13a40e833d97984411c43'
passwd = '4181ccbc3f573d2f77eba1e3e6aad35c'

# get last 100 messages
response_json = requests.get(f"https://api.sigfox.com/v2/devices/{id}/messages", auth=(user, passwd)).json()

print(len(response_json['data']))

