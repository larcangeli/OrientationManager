# google_drive_utils.py
import os
import io
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

# --- CONFIGURATION ---
# If modifying these scopes, delete the file token.json.
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly' # Read-only access is enough to list and download
    # If you also need to delete files from Drive after download, add:
    # 'https://www.googleapis.com/auth/drive.file'
]
CREDENTIALS_FILE = '../../config/credentials.json'
TOKEN_FILE = '../../config/token.json'

# Setup basic logging for this module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def get_drive_service():
    """Authenticates and returns the Google Drive API service client."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired Google Drive token.")
            creds.refresh(Request())
        else:
            logger.info("Google Drive token not found or invalid. Initiating new auth flow.")
            if not os.path.exists(CREDENTIALS_FILE):
                logger.error(f"{CREDENTIALS_FILE} not found. Cannot authenticate.")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            # For a server-side app that might not have a browser readily available
            # during initial setup, run_console() is often preferred over run_local_server().
            # You'll copy a URL to a browser, authorize, and paste back a code.
            # If run_local_server is problematic on your server:
            # creds = flow.run_console()
            try:
                creds = flow.run_local_server(port=0) # Will open a browser for auth on first run
            except Exception as e:
                logger.error(f"Failed to run local server for OAuth: {e}. Try run_console() instead in get_drive_service().")
                logger.info("Attempting run_console() as a fallback...")
                try:
                    creds = flow.run_console()
                except Exception as e_console:
                    logger.error(f"run_console() also failed: {e_console}")
                    return None

        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
            logger.info(f"Google Drive token saved to {TOKEN_FILE}")

    try:
        service = build('drive', 'v3', credentials=creds)
        logger.info("Google Drive service created successfully.")
        return service
    except HttpError as error:
        logger.error(f'An error occurred building the Drive service: {error}')
        return None
    except Exception as e:
        logger.error(f'An unexpected error occurred: {e}')
        return None


def list_csv_files_in_folder(service, folder_id):
    """Lists CSV files in a specific Google Drive folder."""
    if not service:
        logger.error("Drive service is not available.")
        return []
    try:
        query = f"'{folder_id}' in parents and mimeType='text/csv' and trashed=false"
        results = service.files().list(
            q=query,
            pageSize=100, # Adjust as needed
            fields="nextPageToken, files(id, name)"
        ).execute()
        items = results.get('files', [])
        logger.info(f"Found {len(items)} CSV files in folder '{folder_id}'.")
        return items
    except HttpError as error:
        logger.error(f'An error occurred listing files: {error}')
        return []

def download_file(service, file_id, file_name, local_download_path):
    """Downloads a file from Google Drive to a local path."""
    if not service:
        logger.error("Drive service is not available.")
        return False
    try:
        request = service.files().get_media(fileId=file_id)
        os.makedirs(os.path.dirname(local_download_path), exist_ok=True) # Ensure directory exists
        fh = io.FileIO(local_download_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        logger.info(f"Starting download of '{file_name}' (ID: {file_id}) to '{local_download_path}'")
        while done is False:
            status, done = downloader.next_chunk()
            if status:
                logger.info(f"Download {int(status.progress() * 100)}%.")
        logger.info(f"Successfully downloaded '{file_name}' to '{local_download_path}'.")
        return True
    except HttpError as error:
        logger.error(f'An error occurred downloading file ID {file_id}: {error}')
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during download of {file_id}: {e}")
        return False

# Optional: function to delete a file from Drive (if you use drive.file scope)
# def delete_drive_file(service, file_id):
#     if not service:
#         logger.error("Drive service is not available for deletion.")
#         return False
#     try:
#         service.files().delete(fileId=file_id).execute()
#         logger.info(f"File with ID: {file_id} deleted successfully from Google Drive.")
#         return True
#     except HttpError as error:
#         logger.error(f"An error occurred deleting file {file_id} from Google Drive: {error}")
#         return False