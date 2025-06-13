from flask import Flask, request, jsonify, render_template, send_from_directory
import datetime
import os
from flask_cors import CORS # For handling CORS if needed
import google.generativeai as genai
import time # For sleeping in the background thread
import threading # For background tasks
from collections import deque
import logging
import json
import pandas as pd
from datetime import datetime, timedelta
import glob

import google_drive_utils as drive_utils # Your Google Drive utility module

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes (optional, adjust as needed)

# --- Configuration ---
GOOGLE_DRIVE_CSV_FOLDER_ID = "1eT3I5RGrzFJRERu72Lw-N6YjeNgyzUD2"
LOCAL_DOWNLOAD_DIR = "downloaded_csvs"
MAX_MESSAGES = 3
received_alerts = deque(maxlen=MAX_MESSAGES)
API_KEY_FILE_PATH = "google_API_key.txt" # Path to your Google API key file
# Load Google API key from file
GOOGLE_API_KEY = None
try:
    with open(API_KEY_FILE_PATH, 'r') as f:
        # Leggi la chiave, rimuovendo eventuali spazi bianchi o a capo
        # Se hai più chiavi nel file, dovrai gestirlo diversamente
        raw_key = f.read().strip()
        if raw_key: #file not empty
            GOOGLE_API_KEY = raw_key
        else:
            print(f"ATTENZIONE: Il file della API key '{API_KEY_FILE_PATH}' è vuoto.")
except FileNotFoundError:
    print(f"ATTENZIONE: File della API key '{API_KEY_FILE_PATH}' non trovato.")
except Exception as e:
    print(f"ATTENZIONE: Errore durante la lettura del file API key '{API_KEY_FILE_PATH}': {e}")

# Initialize Google Generative AI client if API key is available
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    model_gemini = genai.GenerativeModel('gemini-2.0-flash') 
else:
    print("ATTENZIONE: La variabile d'ambiente GOOGLE_API_KEY non è impostata.")
    model_gemini = None 


# Configuration for background task
DRIVE_FETCH_INTERVAL_SECONDS = 20 
background_thread_stop_event = threading.Event() 

# Funzione placeholder, da sostituire con la tua vera analisi CSV
def get_posture_summary_for_llm(user_id="default_user"):
    # QUI VA LA LOGICA DI LETTURA E ANALISI CSV
    # Esempio:
    # posture_data_summary = posture_analyzer.summarize_csv_data_for_user(user_id, days_to_analyze=7)
    # return posture_data_summary
    return """Analisi posturale per l'utente StudenteX dal 20/05/2025 al 26/05/2025:
    - Tempo totale di monitoraggio: 25 ore.
    - Inclinazione eccessiva in avanti (pitch > 20°): rilevata per il 60% del tempo, principalmente nelle ore pomeridiane (14:00-18:00) durante le sessioni di studio.
    - Inclinazione laterale a sinistra (roll < -15°): rilevata per il 15% del tempo, spesso quando l'utente scrive o usa il mouse.
    - Rispetto alla settimana precedente, l'inclinazione in avanti è leggermente aumentata."""


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

def generate_mock_posture_data(days):
    """
    Generate mock data for testing. Replace this with real CSV analysis.
    """
    daily_data = []
    total_alerts = 0
    total_hours = 0
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=days-i-1)).strftime('%m/%d')
        good_posture = 60 + (i * 2) + (i % 3) * 10  # Varies between 60-90%
        poor_posture = 100 - good_posture
        alert_count = 5 + (i % 4) * 3  # Varies between 5-17 alerts
        hours = 4 + (i % 3) * 1.5  # Varies between 4-7 hours
        
        daily_data.append({
            'date': date,
            'good_posture_percentage': good_posture,
            'poor_posture_percentage': poor_posture,
            'alert_count': alert_count,
            'hours_monitored': hours
        })
        
        total_alerts += alert_count
        total_hours += hours
    
    summary = {
        'total_hours': round(total_hours, 1),
        'good_posture_percentage': round(sum(d['good_posture_percentage'] for d in daily_data) / len(daily_data), 1),
        'forward_lean_percentage': 25,  # Mock data
        'side_tilt_percentage': 15,     # Mock data
        'total_alerts': total_alerts
    }
    
    return {
        'daily_data': daily_data,
        'summary': summary
    }

def analyze_csv_data_for_stats(days=7):
    """
    Analyze actual CSV files from your posture data.
    This function should be implemented to read your CSV files and calculate real statistics.
    """
    # TODO: Implement real CSV analysis
    # 1. Read CSV files from LOCAL_DOWNLOAD_DIR
    # 2. Filter data for the last 'days' days
    # 3. Calculate posture statistics (pitch/roll thresholds)
    # 4. Count alerts and monitoring time
    # 5. Return structured data for frontend
    
    csv_files = glob.glob(os.path.join(LOCAL_DOWNLOAD_DIR, "*.csv"))
    
    # Example structure for real implementation:
    # for csv_file in csv_files:
    #     df = pd.read_csv(csv_file)
    #     # Analyze pitch, roll, yaw data
    #     # Calculate time periods with good vs poor posture
    #     # Count alerts based on your thresholds
    
    pass


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

'''
@app.route('/', methods=['GET'])
def dashboard_page():
    logger.info("Dashboard page requested.")
    return render_template('dashboard.html')

@app.route('/')
def index():
    return render_template('chat_interface.html')
'''

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

@app.route('/chat_ai', methods=['POST'])
def chat_ai_endpoint():
    data = request.get_json()
    user_question = data.get('question')

    if not user_question:
        return jsonify({"error": "Domanda non fornita"}), 400

    # 1. Ottieni il riassunto dei dati posturali
    posture_context = get_posture_summary_for_llm() # In futuro, passerai un user_id

    # 2. Costruisci il Prompt per l'LLM
    system_prompt = """Tu sei PosturAI, un consulente AI amichevole e esperto di ergonomia, specializzato nell'aiutare gli studenti a migliorare la loro postura.
    Il tuo obiettivo è analizzare i dati posturali forniti, rispondere alle domande degli studenti, offrire consigli pratici e incoraggianti.
    Non fornire diagnosi mediche. Concentrati su abitudini, esercizi semplici e setup della postazione di studio.
    Sii conciso ma informativo."""

    # Prompt per l'utente (combinando contesto e domanda)
    # Per Gemini (che preferisce un formato di prompt più diretto o una storia di chat)
    # Puoi anche usare una struttura di chat con turni 'user' e 'model' se l'API lo supporta meglio
    full_prompt = f"""Contesto dei dati posturali dello studente:
    {posture_context}

    Domanda dello studente:
    {user_question}

    Tua risposta come PosturAI:"""

    # 3. Chiama l'API dell'LLM
    try:
        # Esempio con Google Gemini
        response = model_gemini.generate_content(full_prompt)
        ai_reply = response.text

        # Esempio con OpenAI (se si usa client_openai)
        # chat_completion = client_openai.chat.completions.create(
        #     messages=[
        #         {"role": "system", "content": system_prompt},
        #         {"role": "user", "content": f"Contesto: {posture_context}\n\nDomanda: {user_question}"}
        #     ],
        #     model="gpt-3.5-turbo",
        # )
        # ai_reply = chat_completion.choices[0].message.content

    except Exception as e:
        print(f"Errore durante la chiamata all'LLM: {e}")
        ai_reply = "Scusa, sto avendo qualche difficoltà a elaborare la tua richiesta in questo momento. Riprova più tardi."

    return jsonify({"reply": ai_reply})


@app.route('/api/posture-stats')
def get_posture_statistics():
    """
    API endpoint to get posture statistics for the frontend graphs
    """
    try:
        days = int(request.args.get('days', 7))
        
        # This is where you'll implement your CSV analysis logic
        # For now, returning mock data structure
        mock_data = generate_mock_posture_data(days)
        
        return jsonify(mock_data)
    
    except Exception as e:
        print(f"Error getting posture statistics: {e}")
        return jsonify({"error": "Failed to fetch statistics"}), 500



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