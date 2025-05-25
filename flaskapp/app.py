from flask import Flask, request, jsonify, render_template
import datetime
import os
import time # For sleeping in the background thread
import threading # For background tasks
from collections import deque
import logging

import google_drive_utils as drive_utils # Your Google Drive utility module

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Configuration ---
GOOGLE_DRIVE_CSV_FOLDER_ID = "1eT3I5RGrzFJRERu72Lw-N6YjeNgyzUD2"
LOCAL_DOWNLOAD_DIR = "downloaded_csvs"
MAX_MESSAGES = 3
received_alerts = deque(maxlen=MAX_MESSAGES)

# Configuration for background task
DRIVE_FETCH_INTERVAL_SECONDS = 20 # Fetch every 5 minutes (300 seconds)
background_thread_stop_event = threading.Event() # To signal the thread to stop

# --- Google Drive Fetching Logic (moved to a function) ---
def perform_drive_csv_fetch():
    """Fetches CSVs from Google Drive and saves them locally."""
    logger.info("Background task: Starting CSV fetch from Google Drive.")
    drive_service = drive_utils.get_drive_service() # This might trigger auth flow on first run if token.json is missing/invalid
    if not drive_service:
        logger.error("Background task: Failed to get Google Drive service. Cannot fetch files.")
        return {"status": "error", "message": "Failed to authenticate with Google Drive."}

    if not GOOGLE_DRIVE_CSV_FOLDER_ID or GOOGLE_DRIVE_CSV_FOLDER_ID == "YOUR_GOOGLE_DRIVE_FOLDER_ID_CONTAINING_CSVS":
        logger.error("Background task: GOOGLE_DRIVE_CSV_FOLDER_ID is not configured.")
        return {"status": "error", "message": "Google Drive folder ID not configured on server."}

    csv_files = drive_utils.list_csv_files_in_folder(drive_service, GOOGLE_DRIVE_CSV_FOLDER_ID)

    if not csv_files:
        logger.info("Background task: No new CSV files found in the Google Drive folder.")
        return {"status": "success", "message": "No new CSV files found.", "downloaded_files": 0, "files": []}

    downloaded_count = 0
    downloaded_file_names = []
    os.makedirs(LOCAL_DOWNLOAD_DIR, exist_ok=True)

    for item in csv_files:
        file_id = item['id']
        file_name = item['name']
        local_file_path = os.path.join(LOCAL_DOWNLOAD_DIR, file_name)

        if os.path.exists(local_file_path):
            logger.info(f"Background task: File '{file_name}' already exists locally. Skipping download.")
            continue

        logger.info(f"Background task: Attempting to download '{file_name}' (ID: {file_id})")
        if drive_utils.download_file(drive_service, file_id, file_name, local_file_path):
            downloaded_count += 1
            downloaded_file_names.append(file_name)
        else:
            logger.error(f"Background task: Failed to download '{file_name}'.")
    
    message = f"Successfully downloaded {downloaded_count} CSV file(s)." if downloaded_count > 0 else "No new files were downloaded."
    logger.info(f"Background task: {message}")
    return {
        "status": "success",
        "message": message,
        "downloaded_files_count": downloaded_count,
        "downloaded_file_names": downloaded_file_names
    }

# --- Background Task Runner ---
def background_drive_fetcher():
    """Periodically calls the drive fetching logic."""
    logger.info("Background Drive Fetcher thread started.")
    # Perform an initial fetch shortly after startup (optional, give server time to fully start)
    time.sleep(10) # Wait a few seconds before first fetch
    if not background_thread_stop_event.is_set():
        perform_drive_csv_fetch()

    while not background_thread_stop_event.is_set():
        logger.debug(f"Background Drive Fetcher sleeping for {DRIVE_FETCH_INTERVAL_SECONDS} seconds.")
        # Wait for the interval or until the stop event is set
        # Using wait() allows the thread to exit quickly if the event is set
        background_thread_stop_event.wait(DRIVE_FETCH_INTERVAL_SECONDS)
        if not background_thread_stop_event.is_set(): # Check again after waking up
            perform_drive_csv_fetch()
    logger.info("Background Drive Fetcher thread stopped.")


# --- Flask Routes (Alerts, Dashboard, etc. remain the same) ---
@app.route('/alert', methods=['POST'])
def receive_alert_post():
    # ... (same as before) ...
    global received_alerts
    if request.method == 'POST':
        try:
            data = request.get_json()
            if data:
                logger.info(f"New Alert Received via POST! Data: {data}")
                display_message = f"[{data.get('timestamp', 'No Timestamp')}] {data.get('message', 'No Message')}"
                received_alerts.appendleft(display_message)
                return jsonify({"status": "success", "message": "Alert received", "data": data}), 200
            else:
                logger.warning("Received POST to /alert with no JSON data.")
                return jsonify({"status": "error", "message": "No JSON data received"}), 400
        except Exception as e:
            logger.error(f"Error processing /alert POST request: {e}", exc_info=True)
            return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/', methods=['GET'])
def dashboard_page():
    logger.info("Dashboard page requested.")
    return render_template('dashboard.html')


@app.route('/get_alerts_data', methods=['GET'])
def get_alerts_data_json():
    alerts_list = list(received_alerts)
    return jsonify({"alerts": alerts_list})

# Optional: Manual trigger endpoint (can be removed if only background task is desired)
@app.route('/fetch_drive_csvs_manual', methods=['GET'])
def fetch_drive_csvs_route_manual():
    logger.info("Manual request received to fetch CSVs from Google Drive.")
    result = perform_drive_csv_fetch() # Call the refactored function
    return jsonify(result), 200 if result.get("status") == "success" else 500


# --- Main Execution ---
if __name__ == '__main__':
    logger.info("Flask Alert Server Starting with Google Drive integration...")
    os.makedirs(LOCAL_DOWNLOAD_DIR, exist_ok=True)
    logger.info(f"CSV files from Drive will be saved to: {os.path.abspath(LOCAL_DOWNLOAD_DIR)}")

    # Start the background thread for fetching Drive files
    # Make sure the initial Google Auth can happen if needed.
    # The first call to get_drive_service() might block for user input (OAuth).
    # If running headless, ensure token.json is pre-generated or run_console is used.
    logger.info("Attempting to initialize Google Drive service for background thread setup...")
    drive_service_init = drive_utils.get_drive_service()
    if drive_service_init:
        logger.info("Google Drive service initialized successfully. Starting background fetcher.")
        fetcher_thread = threading.Thread(target=background_drive_fetcher, daemon=True)
        fetcher_thread.start()
    else:
        logger.error("Failed to initialize Google Drive service. Background fetcher NOT started. Manual fetch might still work if auth succeeds later.")
        # You might want to decide if the app should exit or continue without the background task.

    try:
        # Note: When using Flask's development server with debug=True and auto-reloading,
        # the background thread might be started twice or behave unexpectedly on reloads.
        # For production, you'd use a proper WSGI server (Gunicorn, uWSGI) which handles
        # processes differently.
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False if drive_service_init else True)
        # use_reloader=False can help with threads in dev, but you lose auto-reload on code change.
        # If `drive_service_init` fails, reloader might be fine.
    except KeyboardInterrupt:
        logger.info("Flask server shutting down...")
    finally:
        logger.info("Signaling background thread to stop...")
        background_thread_stop_event.set()
        if 'fetcher_thread' in locals() and fetcher_thread.is_alive():
            fetcher_thread.join(timeout=5) # Wait for the thread to finish
        logger.info("Flask application terminated.")