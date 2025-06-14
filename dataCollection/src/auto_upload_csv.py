import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# --- CONFIGURATION ---
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file'] 
LOCAL_DIR_TO_WATCH = os.path.join(os.path.dirname(__file__), ".")  
DRIVE_FOLDER_ID = "1eT3I5RGrzFJRERu72Lw-N6YjeNgyzUD2" 
CREDENTIALS_FILE = '../../config/credentials.json'
TOKEN_FILE = '../../config/token.json'


# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# --- GOOGLE DRIVE AUTHENTICATION ---
def get_drive_service():
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0) # Will open a browser for auth
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)
        return service
    except HttpError as error:
        logging.error(f'An error occurred building the Drive service: {error}')
        return None

# --- GOOGLE DRIVE UPLOAD ---
def upload_file_to_drive(service, filepath, drive_folder_id):
    """Uploads a file to the specified Google Drive folder."""
    file_metadata = {
        'name': os.path.basename(filepath)
    }
    if drive_folder_id:
        file_metadata['parents'] = [drive_folder_id]

    media = MediaFileUpload(filepath, mimetype='text/csv', resumable=True)
    try:
        file = service.files().create(body=file_metadata,
                                      media_body=media,
                                      fields='id').execute()
        logging.info(f"File '{os.path.basename(filepath)}' uploaded successfully. File ID: {file.get('id')}")
        return file.get('id')
    except HttpError as error:
        logging.error(f"An error occurred uploading '{os.path.basename(filepath)}': {error}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred uploading '{os.path.basename(filepath)}': {e}")
        return None

# --- WATCHDOG EVENT HANDLER ---
class CSVHandler(FileSystemEventHandler):
    def __init__(self, drive_service, drive_folder_id):
        self.drive_service = drive_service
        self.drive_folder_id = drive_folder_id
        self.processed_files = {} # To avoid processing a file multiple times for rapid events

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".csv"):
            self._process_file(event.src_path, "created")

    def on_modified(self, event):
        if not event.is_directory and event.src_path.lower().endswith(".csv"):
            # Some editors trigger 'modified' multiple times quickly when saving.
            # We'll add a small delay and check if it's a genuine new save.
            self._process_file(event.src_path, "modified")

    def _process_file(self, filepath, event_type):
        # Debounce: Check if this file was processed recently for the same event type
        # This is a simple debounce. More sophisticated logic might be needed for complex save patterns.
        current_time = time.time()
        last_processed_time = self.processed_files.get(filepath, 0)

        # If file was created or modified very recently, give it a second to fully write
        # and avoid processing multiple "modified" events for a single save action.
        if current_time - last_processed_time < 2: # 2 second debounce window
            return

        logging.info(f"CSV file {event_type}: {filepath}")
        # Wait a tiny bit to ensure the file is fully written before uploading
        time.sleep(1)
        try:
            if os.path.exists(filepath) and os.path.getsize(filepath) > 0: # Check if file exists and is not empty
                upload_file_to_drive(self.drive_service, filepath, self.drive_folder_id)
                self.processed_files[filepath] = current_time
            else:
                logging.warning(f"File {filepath} is empty or no longer exists. Skipping upload.")
        except Exception as e:
            logging.error(f"Error processing file {filepath}: {e}")


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    if not os.path.exists(LOCAL_DIR_TO_WATCH):
        logging.error(f"Error: Local directory to watch does not exist: {LOCAL_DIR_TO_WATCH}")
        exit()

    if not DRIVE_FOLDER_ID:
        logging.warning("DRIVE_FOLDER_ID is not set. Files will be uploaded to the root of 'My Drive'.")


    logging.info("Attempting to authenticate with Google Drive...")
    drive_service = get_drive_service()

    if not drive_service:
        logging.error("Could not connect to Google Drive. Exiting.")
        exit()
    logging.info("Successfully authenticated with Google Drive.")

    logging.info(f"Monitoring directory: {LOCAL_DIR_TO_WATCH} for .csv files...")
    event_handler = CSVHandler(drive_service, DRIVE_FOLDER_ID)
    observer = Observer()
    observer.schedule(event_handler, LOCAL_DIR_TO_WATCH, recursive=False) # Set recursive=True if you want to watch subfolders
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user.")
    except Exception as e:
        logging.error(f"An unexpected error occurred in the main loop: {e}")
    finally:
        observer.stop()
        observer.join()
        logging.info("Observer shut down.")