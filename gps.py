from counterfit_connection import CounterFitConnection
CounterFitConnection.init('127.0.0.1', 5000)

import time
import counterfit_shims_serial
import pynmea2
import json

serial = counterfit_shims_serial.Serial('/dev/ttyAMA0')
from counterfit_shims_grove.grove_led import GroveLed

from azure.iot.device import IoTHubDeviceClient, Message, MethodResponse

connection_string = 'HostName=2022hub.azure-devices.net;DeviceId=2022device;SharedAccessKey=KD8Sas4U+tcg7GJXcdapk7mrV4ovp5LMc5PI1QNt890='

ledRight = GroveLed(6)
ledLeft = GroveLed(7)

device_client = IoTHubDeviceClient.create_from_connection_string(connection_string)

print('Connecting')
device_client.connect()
print('Connected')

def handle_method_request(request):
    print("Direct method received - ", request.name)
    
    if request.name == "green_right":
        ledRight.on()
        ledLeft.off()
    elif request.name == "green_left":
        ledRight.off()
        ledLeft.on()

    method_response = MethodResponse.create_from_method_request(request, 200)
    device_client.send_method_response(method_response)

device_client.on_method_request_received = handle_method_request

def send_gps_data(line):
    msg = pynmea2.parse(line)
    if msg.sentence_type == 'GGA':
        lat = pynmea2.dm_to_sd(msg.lat)
        lon = pynmea2.dm_to_sd(msg.lon)

        if msg.lat_dir == 'S':
            lat = lat * -1

        if msg.lon_dir == 'W':
            lon = lon * -1

        print(f'{lat},{lon} - from {msg.num_sats} satellites')

        # Create JSON message with latitude and longitude
        gps_data = {
            'latitude': lat,
            'longitude': lon,
            'num_sats': msg.num_sats
        }

        # Send the JSON message to IoT Hub
        message = Message(json.dumps(gps_data))
        device_client.send_message(message)


while True:
    line = serial.readline().decode('utf-8')

    while len(line) > 0:
        send_gps_data(line)
        line = serial.readline().decode('utf-8')

    time.sleep(5)