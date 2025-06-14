# 🏃‍♂️ OrientationManager - Student Posture Monitoring System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.0%2B-blue)](https://reactjs.org/)
[![Arduino](https://img.shields.io/badge/Arduino-IDE-green)](https://www.arduino.cc/)

A comprehensive posture monitoring system designed for students using **NICLA Sense ME** hardware, real-time data analysis, and AI-powered insights to promote healthy study habits.

## 🎯 Overview

OrientationManager helps students maintain proper posture during study sessions by:
- **Real-time monitoring** of head and neck orientation using IMU sensors
- **Instant alerts** when poor posture is detected
- **AI-powered analysis** using Google Gemini for personalized recommendations
- **Data visualization** with comprehensive statistics and trends
- **Cloud storage** integration for long-term posture tracking

## 🏗️ System Architecture

```
┌─────────────────┐    BLE     ┌──────────────────┐    HTTP    ┌─────────────────┐
│   NICLA Sense   │◄──────────►│  Python BLE      │◄──────────►│   Flask Web     │
│      ME         │            │   Receiver       │            │   Application   │
│   (C++/Arduino) │            │                  │            │  (Python/React) │
└─────────────────┘            └──────────────────┘            └─────────────────┘
        │                               │                               │
        │ Collects IMU Data            │ Processes & Stores            │ AI Analysis
        │ Detects Poor Posture         │ Forwards Alerts               │ Web Dashboard
        │ Sends via Bluetooth          │ Uploads to Drive              │ Chat Interface
        └─────────────────────────────────────────────────────────────────────────┘
```


## 🏗️ Repository Structure

```
OrientationManager/
├── config/                # Python requirements and configuration files
│   └── requirements.txt
├── dataCollection/        # Python BLE data collection & logging
│   └── src/
├── hardware/              # Arduino/C++ firmware for NICLA Sense ME
│   ├── src/
│   ├── include/
│   └── platformio.ini
├── lib/                   # Additional libraries (see README inside)
├── test/                  # Test scripts and utilities (see README inside)
├── webApp/                # Web application (backend & frontend)
│   ├── backend/           # Python Flask backend API
│   └── frontend/          # React+Vite dashboard and chat interface
├── .gitignore
└── README.md
```

## 🧩 Components

### 1. Hardware (`hardware/`)
- **Language**: C++ (Arduino/PlatformIO)
- **Device**: NICLA Sense ME
- **Function**: Collects IMU (BHY2) sensor data, detects poor posture, sends alerts via BLE.

### 2. Data Collection (`dataCollection/`)
- **Language**: Python
- **Function**: Receives BLE data, logs to CSV, uploads to Google Drive, forwards alerts to backend.

### 3. Web Application (`webApp/`)
- **Backend**: Flask API (`webApp/backend/`)
  - Receives and manages alerts, connects with Google Gemini for AI analysis, handles REST API.
- **Frontend**: React+Vite (`webApp/frontend/`)
  - Posture dashboard, statistics, real-time alerts, AI chat (PosturAI).

### 4. Libraries & Tests
- **lib/**: Custom or external libraries for hardware/software.
- **test/**: Scripts for testing BLE, LLM integration, data pipeline, etc.


## 🚀 Quick Start

### Prerequisites
- NICLA Sense ME board
- Python 3.8+
- Node.js 16+
- Arduino IDE or PlatformIO
- Google Drive API credentials

### 1. Hardware Setup
```bash
# Open hardware/src/ in Arduino IDE or PlatformIO
# Select "Arduino Nicla Sense ME" board
# Upload the firmware
```

### 2. Python Environment
```bash
# Clone the repository
git clone https://github.com/larcangeli/OrientationManager.git
cd OrientationManager

# Install Python dependencies
pip install -r requirements.txt

# Set up Google Drive API
# 1. Download credentials.json from Google Cloud Console
# 2. Place in project root
# 3. Add your Google API key to google_API_key.txt
```

### 3. Start Data Collection
```bash
# Start BLE receiver (in dataCollection/)
python dataCollection/src/ble_receiver.py

# (Optional) Start automatic CSV upload
python dataCollection/src/auto_upload_csv.py
```


### 4. Start Web Application
```bash
# Backend (Flask)
cd webApp/backend
python app.py

# Frontend (React+Vite)
cd ../frontend
npm install
npm run dev

# Open http://localhost:5173 in your browser
```


## 📊 Usage

1. **Wear the Device**: Attach NICLA Sense ME to your head/neck area.
2. **Start Monitoring**: Run the Python BLE receiver.
3. **Access Dashboard**: Open the web dashboard.
4. **Chat with AI**: Ask PosturAI questions about your posture.
5. **View Statistics**: Monitor your posture trends over time.

---

## 🔧 Configuration

### Environment Variables
Set these as local environment variables or in a `.env` file:
```bash
GOOGLE_DRIVE_CSV_FOLDER_ID="your_folder_id_here"
FLASK_SERVER_URL="http://127.0.0.1:5000/alert"
```

### Posture Thresholds
Adjust in `hardware/src/main.cpp`:
```cpp
const float ALERT_THRESHOLD = 5.0; // degrees
```


## 📈 Features

- Real-time IMU monitoring (pitch, roll, yaw)
- Configurable posture thresholds and alerts
- BLE data collection and cloud upload
- AI-driven posture analysis (Google Gemini)
- Web dashboard (React+Vite) with statistics, notifications, and chat

---

## ⚙️ Development

- See `lib/README` and `test/README` for library and testing details
- Contribute via feature branches & pull requests


## 📋 Requirements

### Hardware
- NICLA Sense ME board
- USB-C cable
- Optional: 3D printed mount

### Software
- Python 3.8+
- Node.js 16+
- Arduino IDE 2.0+ or PlatformIO


## 🔒 Security & Privacy

- All data is stored locally and/or your Google Drive
- No third-party data sharing
- Secure BLE communication


## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/larcangeli/OrientationManager/issues)
- **Discussions**: [GitHub Discussions](https://github.com/larcangeli/OrientationManager/discussions)
- **Wiki**: [Wiki](https://github.com/larcangeli/OrientationManager/wiki)


## 🎓 Academic Use

If you use this in research, please cite:

```bibtex
@software{OrientationManager2025,
  author = {larcangeli},
  title = {OrientationManager: Student Posture Monitoring System},
  year = {2025},
  url = {https://github.com/larcangeli/OrientationManager}
}
```
