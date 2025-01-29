import logging
import azure.functions as func
import json
import os
from azure.iot.hub import IoTHubRegistryManager
from azure.iot.hub.models import CloudToDeviceMethod

# Initialize the previous_longitude variable globally
previous_longitude = None

def main(event: func.EventHubEvent):
    global previous_longitude  # Declare the variable as global so it can be updated

    body = json.loads(event.get_body().decode('utf-8'))
    device_id = event.iothub_metadata['connection-device-id']

    logging.info(f'Received message: {body} from {device_id}')

    # Extract latitude and longitude from the received data
    latitude = body.get('latitude')
    longitude = body.get('longitude')

    if latitude is not None and longitude is not None:
        # If this is the first longitude reading, initialize the previous_longitude
        if previous_longitude is None:
            previous_longitude = longitude
            logging.info(f'First longitude reading: {longitude}')
            return  # Skip further logic for the first reading

        # Compare the current longitude with the previous one
        if longitude > previous_longitude:
            logging.info(f'Longitude increased: {longitude} (Previous: {previous_longitude})')
            direct_method = CloudToDeviceMethod(method_name='green_right', payload='{}')
        elif longitude < previous_longitude:
            logging.info(f'Longitude decreased: {longitude} (Previous: {previous_longitude})')
            direct_method = CloudToDeviceMethod(method_name='green_left', payload='{}')
        else:
            logging.info(f'Longitude is unchanged: {longitude} (Previous: {previous_longitude})')
            return  # No action needed if longitude hasn't changed

        # Send the direct method request to the device
        logging.info(f'Sending direct method request for {direct_method.method_name} for device {device_id}')
        
        registry_manager_connection_string = os.environ['REGISTRY_MANAGER_CONNECTION_STRING']
        registry_manager = IoTHubRegistryManager(registry_manager_connection_string)

        # Invoke the direct method on the device
        registry_manager.invoke_device_method(device_id, direct_method)

        # Update the previous longitude to the current one
        previous_longitude = longitude

        logging.info('Direct method request sent!')
    else:
        logging.error('No valid latitude or longitude in the received message.')
