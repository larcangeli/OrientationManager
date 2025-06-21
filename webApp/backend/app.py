from flask import Flask, request, jsonify, render_template, send_from_directory
import datetime
import os
from flask_cors import CORS
import google.generativeai as genai
import time 
import threading
from collections import deque
import logging
import json
import pandas as pd
from datetime import datetime, timedelta
import glob
import sys
import google_drive_utils as drive_utils

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# --- Configuration ---
GOOGLE_DRIVE_CSV_FOLDER_ID = "1eT3I5RGrzFJRERu72Lw-N6YjeNgyzUD2"
LOCAL_DOWNLOAD_DIR = "downloaded_csvs"
MAX_MESSAGES = 3
received_alerts = deque(maxlen=MAX_MESSAGES)
API_KEY_FILE_PATH = "../../config/google_API_key.txt"

# Load Google API key from file
GOOGLE_API_KEY = None
try:
    with open(API_KEY_FILE_PATH, 'r') as f:
        raw_key = f.read().strip()
        if raw_key:
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

# Topic-specific prompt templates
TOPIC_PROMPTS = {
    'analysis': """You are PosturAI, analyzing the user's posture data. Focus on:
    - Current posture patterns and trends
    - Specific problem areas identified from the data
    - Time periods when posture is worst/best
    - Measurable improvements or concerns
    Keep responses data-driven and specific.""",
    
    'tips': """You are PosturAI, providing practical posture improvement advice. Focus on:
    - Actionable, specific tips based on the user's data
    - Easy-to-implement daily habits
    - Prioritized recommendations (most important first)
    - Quick fixes for immediate improvement
    Keep advice practical and encouraging.""",
    
    'exercises': """You are PosturAI, recommending specific exercises. Focus on:
    - Targeted exercises for the user's specific posture issues
    - Simple desk exercises that can be done during work
    - Stretches and strengthening exercises
    - Frequency and duration recommendations
    Provide clear, step-by-step instructions.""",
    
    'workspace': """You are PosturAI, helping optimize workspace ergonomics. Focus on:
    - Desk height, monitor position, chair adjustment
    - Keyboard and mouse positioning
    - Lighting and screen setup
    - Equipment recommendations if needed
    Give specific measurements and setup instructions.""",
    
    'breaks': """You are PosturAI, advising on effective break strategies. Focus on:
    - Optimal break frequency based on user's patterns
    - Specific activities to do during breaks
    - Movement and stretching routines
    - How to make breaks more effective for posture
    Provide practical break schedules and activities.""",
    
    'progress': """You are PosturAI, helping track posture improvement. Focus on:
    - Comparing current data to previous periods
    - Identifying positive trends and areas of concern
    - Setting realistic improvement goals
    - Celebrating achievements and addressing setbacks
    Be encouraging while staying realistic about progress."""
}

def get_posture_summary_for_llm(user_id="default_user"):
    return """Posture Analysis Summary for Student (June 18, 2025):
    
    Current Session Data:
    - Total monitoring time today: 4.2 hours
    - Good posture maintained: 78% of time (3.3 hours)
    - Poor posture detected: 22% of time (52 minutes)
    - Total alerts generated: 12
    
    Primary Issues Detected:
    - Forward head posture: 60% of poor posture time (mainly 2-6 PM)
    - Left shoulder drop: 25% of poor posture time
    - Excessive forward lean: 15% of poor posture time
    
    Patterns Observed:
    - Posture deteriorates significantly after 2 hours of continuous work
    - Worst posture period: 3:00-4:00 PM (likely afternoon fatigue)
    - Best posture: Morning sessions (9-11 AM)
    
    Weekly Trends:
    - 15% improvement in good posture time vs last week
    - 30% reduction in severe forward head posture incidents
    - Consistent improvement in break-taking behavior
    
    Workspace Notes:
    - Frequent mouse-heavy tasks correlate with right shoulder tension
    - Extended reading periods show increased forward lean"""
 
def perform_drive_csv_fetch():
    
    """Fetches CSVs from Google Drive and saves them locally."""
    
    logger.info("Background task: Starting CSV fetch from Google Drive.")
    drive_service = drive_utils.get_drive_service()
    if not drive_service:
        logger.error("Background task: Failed to get Google Drive service. Cannot fetch files.")
        return {"status": "error", "message": "Failed to authenticate with Google Drive."}

    if not GOOGLE_DRIVE_CSV_FOLDER_ID:
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

def background_drive_fetcher():
    
    """Periodically calls the drive fetching logic."""
    
    logger.info("Background Drive Fetcher thread started.")
    time.sleep(10)
    if not background_thread_stop_event.is_set():
        perform_drive_csv_fetch()

    while not background_thread_stop_event.is_set():
        logger.debug(f"Background Drive Fetcher sleeping for {DRIVE_FETCH_INTERVAL_SECONDS} seconds.")
        background_thread_stop_event.wait(DRIVE_FETCH_INTERVAL_SECONDS)
        if not background_thread_stop_event.is_set():
            perform_drive_csv_fetch()
    logger.info("Background Drive Fetcher thread stopped.")

def generate_mock_posture_data(days):
    
    """Generate mock data for the demo. Needs replacement with real CSV analysis."""
    
    daily_data = []
    total_alerts = 0
    total_hours = 0
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=days-i-1)).strftime('%m/%d')
        good_posture = 60 + (i * 2) + (i % 3) * 10
        poor_posture = 100 - good_posture
        alert_count = 5 + (i % 4) * 3
        hours = 4 + (i % 3) * 1.5
        
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
        'forward_lean_percentage': 25,
        'side_tilt_percentage': 15,
        'total_alerts': total_alerts
    }
    
    return {
        'daily_data': daily_data,
        'summary': summary
    }




#______________________FLASK ROUTES_________________________________
@app.route('/alert', methods=['POST'])
def receive_alert_post():
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

@app.route('/get_alerts_data', methods=['GET'])
def get_alerts_data_json():
    alerts_list = list(received_alerts)
    return jsonify({"alerts": alerts_list})

@app.route('/fetch_drive_csvs_manual', methods=['GET'])
def fetch_drive_csvs_route_manual():
    logger.info("Manual request received to fetch CSVs from Google Drive.")
    result = perform_drive_csv_fetch()
    return jsonify(result), 200 if result.get("status") == "success" else 500

@app.route('/chat_ai', methods=['POST'])
def chat_ai_endpoint():
    data = request.get_json()
    user_question = data.get('question')
    topic_id = data.get('topic', 'general')
    topic_context = data.get('context', '')

    if not user_question:
        return jsonify({"error": "Question not provided"}), 400

    # Get posture data summary
    posture_context = get_posture_summary_for_llm()

    # Get topic-specific system prompt
    system_prompt = TOPIC_PROMPTS.get(topic_id, TOPIC_PROMPTS['tips'])

    # Enhanced prompt with topic context
    full_prompt = f"""  {system_prompt}

                        User's Current Posture Data:
                        {posture_context}

                        Topic Context: {topic_context}

                        User's Question: {user_question}

                        Provide a helpful, specific response as PosturAI focusing on this topic. Be encouraging but realistic, and base your advice on the provided posture data when possible."""

    try:
        if model_gemini:
            response = model_gemini.generate_content(full_prompt)
            ai_reply = response.text
        else:
            ai_reply = f"I'd love to help with {topic_id}, but I'm having trouble connecting to my AI services right now. Please try again later!"

    except Exception as e:
        logger.error(f"Error during LLM call: {e}")
        ai_reply = "I'm having some difficulty processing your request right now. Please try again in a moment."

    return jsonify({"reply": ai_reply})

@app.route('/api/posture-stats')
def get_posture_statistics():
    """API endpoint to get posture statistics for the frontend graphs"""
    try:
        days = int(request.args.get('days', 7))
        mock_data = generate_mock_posture_data(days)
        return jsonify(mock_data)
    except Exception as e:
        logger.error(f"Error getting posture statistics: {e}")
        return jsonify({"error": "Failed to fetch statistics"}), 500


if __name__ == '__main__':
    logger.info("Flask Alert Server Starting with Google Drive integration...")
    os.makedirs(LOCAL_DOWNLOAD_DIR, exist_ok=True)
    logger.info(f"CSV files from Drive will be saved to: {os.path.abspath(LOCAL_DOWNLOAD_DIR)}")

    logger.info("Attempting to initialize Google Drive service for background thread setup...")
    drive_service_init = drive_utils.get_drive_service()
    if drive_service_init:
        logger.info("Google Drive service initialized successfully. Starting background fetcher.")
        fetcher_thread = threading.Thread(target=background_drive_fetcher, daemon=True)
        fetcher_thread.start()
    else:
        logger.error("Failed to initialize Google Drive service. Background fetcher NOT started.")

    try:
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False if drive_service_init else True)
    except KeyboardInterrupt:
        logger.info("Flask server shutting down...")
    finally:
        logger.info("Signaling background thread to stop...")
        background_thread_stop_event.set()
        if 'fetcher_thread' in locals() and fetcher_thread.is_alive():
            fetcher_thread.join(timeout=5)
        logger.info("Flask application terminated.")