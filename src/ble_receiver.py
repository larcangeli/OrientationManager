import asyncio
import csv
from datetime import datetime
from bleak import BleakClient, BleakScanner
import requests

# Server configuration
FLASK_SERVER_URL = "http://127.0.0.1:5000/alert"

# Define UUIDs - must match those in your Arduino sketch
ORIENTATION_SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214"
CSV_DATA_CHARACTERISTIC_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"
ALERT_DATA_CHARACTERISTIC_UUID = "19B10002-E8F2-537E-4F6C-D104768A1214"

# CSV file setup
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_filename = f"nicla_orientation_{timestamp}.csv"
csv_file = None
csv_writer = None
header_written = False

def csv_callback(sender, data):
    """Handle incoming data notifications from the BLE device"""
    global csv_file, csv_writer, header_written
    
    # Convert bytes to string
    data_string = data.decode('utf-8')
    print(f"Received: {data_string}")
    
    # Split the CSV string
    values = data_string.strip().split(',')
    
    # Check if this is the header row
    if not header_written and 'timestamp' in data_string:
        # Write header to CSV
        csv_writer.writerow(values)
        header_written = True
    elif len(values) >= 4:  # Basic validation (we expect at least 4 values)
        # Write data row to CSV
        csv_writer.writerow(values)
        # Ensure data is written to disk
        csv_file.flush()
        
def alert_callback(sender, data):
    """Handle incoming alert messages"""
    # Decode the incoming data
    alert_str = data.decode('utf-8')
    
    # Only process non-empty and actual alerts
    if alert_str and "ALERT" in alert_str:
        # Print the alert with timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_alert = f"[{current_time}] {alert_str}"
        
        # Print with highlighting to make alerts stand out
        print("\033[91m" + formatted_alert + "\033[0m")  # Red text for alerts
        
    # Forward the alert to Flask server
        try:
            # Create JSON payload
            payload = {
                "timestamp": current_time,
                "message": alert_str
            }
            
            # Send POST request to Flask server
            response = requests.post(FLASK_SERVER_URL, json=payload)
            if response.status_code == 200:
                print(f"Alert successfully sent to server: {response.text}")
            else:
                print(f"Failed to send alert to server. Status code: {response.status_code}")
        
        except Exception as e:
            print(f"Error sending alert to server: {e}")

async def main():
    global csv_file, csv_writer
    
    print("Scanning for NiclaSenseCSV device...")
    
    # Scan for the device
    device = await BleakScanner.find_device_by_name("NiclaSenseCSV")
    
    if device is None:
        print("Could not find NiclaSenseCSV device.")
        return
    
    print(f"Found device: {device.name} [{device.address}]")
    
    # Open CSV file
    csv_file = open(csv_filename, 'w', newline='')
    csv_writer = csv.writer(csv_file)
    
    print(f"Starting to log data to {csv_filename}")
    print("Press Ctrl+C to stop recording")
    
    try:
        async with BleakClient(device) as client:
            print(f"Connected to {device.name}")
            
            # Subscribe to the characteristic CSV
            await client.start_notify(
                CSV_DATA_CHARACTERISTIC_UUID, 
                csv_callback
            )
            
            # Subscribe to the characteristic ALERT
            await client.start_notify(
                ALERT_DATA_CHARACTERISTIC_UUID, 
                alert_callback
            )
            
            print("Receiving data... (press Ctrl+C to stop)")
            
            # Keep the connection alive
            while True:
                await asyncio.sleep(1.0)
                
    except asyncio.CancelledError:
        # Handle clean exit
        print("Recording stopped")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if csv_file:
            csv_file.close()
            print(f"Data saved to {csv_filename}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nRecording stopped by user")