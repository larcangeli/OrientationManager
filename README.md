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

## 🔧 Components

### 1. Hardware (Arduino/C++)
- **File**: `src/main.cpp`
- **Hardware**: NICLA Sense ME with BHY2 sensors
- **Features**:
  - Quaternion to Euler angle conversion
  - Real-time posture threshold monitoring
  - Bluetooth Low Energy (BLE) data transmission
  - LED status indicators

### 2. Data Collection (Python)
- **Files**: `src/ble_receiver.py`, `src/auto_upload_csv.py`
- **Features**:
  - BLE connection and data reception
  - CSV data logging with timestamps
  - Automatic Google Drive upload
  - Real-time alert forwarding to Flask server

### 3. Web Application
- **Backend**: Flask (`flaskapp/app.py`)
  - Google Gemini AI integration
  - RESTful API endpoints
  - Real-time alert management
  - Google Drive data analysis
- **Frontend**: React (`flaskapp/frontend/`)
  - Interactive chat with PosturAI
  - Statistics dashboard with visualizations
  - Real-time alert notifications

## 🚀 Quick Start

### Prerequisites
- NICLA Sense ME board
- Python 3.8+
- Node.js 16+
- Arduino IDE
- Google Drive API credentials

### 1. Hardware Setup
```bash
# Flash the Arduino code to NICLA Sense ME
# Open src/main.cpp in Arduino IDE
# Select "Arduino Nicla Sense ME" board
# Upload the sketch
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
# Start BLE receiver
python src/ble_receiver.py

# In another terminal, start Flask app
cd flaskapp
python app.py
```

### 4. Frontend Setup
```bash
# Navigate to frontend directory
cd flaskapp/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 📊 Usage

1. **Wear the Device**: Attach NICLA Sense ME to your head/neck area
2. **Start Monitoring**: Run the Python BLE receiver
3. **Access Dashboard**: Open `http://localhost:5000` in your browser
4. **Chat with AI**: Ask PosturAI questions about your posture
5. **View Statistics**: Monitor your posture trends over time

## 🔑 Configuration

### Environment Variables
```bash
# Google Drive folder ID for CSV storage
GOOGLE_DRIVE_CSV_FOLDER_ID="your_folder_id_here"

# Flask server URL for alerts
FLASK_SERVER_URL="http://127.0.0.1:5000/alert"
```

### Posture Thresholds
Modify thresholds in `src/main.cpp`:
```cpp
const float ALERT_THRESHOLD = 5.0; // degrees
```

## 📈 Features

### Real-time Monitoring
- Continuous IMU data collection (pitch, roll, yaw)
- Configurable posture thresholds
- Instant visual and audio alerts

### AI-Powered Insights
- Personalized posture recommendations
- Conversational interface with PosturAI
- Pattern analysis and trend identification

### Data Management
- Automatic CSV generation with timestamps
- Google Drive cloud storage
- Long-term posture history tracking

### Web Dashboard
- Interactive statistics and graphs
- Real-time alert notifications
- Multi-user support ready

## 🛠️ Development

### Project Structure
```
OrientationManager/
├── src/                    # Arduino and Python source code
│   ├── main.cpp           # Arduino firmware
│   ├── ble_receiver.py    # BLE data collection
│   └── auto_upload_csv.py # Google Drive integration
├── flaskapp/              # Web application
│   ├── app.py            # Flask backend
│   ├── frontend/         # React frontend
│   └── templates/        # HTML templates
├── docs/                 # Documentation
├── examples/             # Usage examples
└── tests/               # Unit tests
```

### Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 Requirements

### Hardware
- NICLA Sense ME board
- USB-C cable for programming
- Optional: 3D printed mounting case

### Software
- Python 3.8+
- Node.js 16+
- Arduino IDE 2.0+

### Python Dependencies
```
flask
flask-cors
bleak
google-api-python-client
google-auth-oauthlib
google-generativeai
watchdog
requests
```

### Frontend Dependencies
```
react
vite
@vitejs/plugin-react
```

## 🔒 Security & Privacy

- All data is stored locally and in your personal Google Drive
- No third-party data sharing
- Google Gemini AI calls are made only when explicitly requested
- BLE communication is device-specific and secure

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

- **Issues**: Report bugs and request features via [GitHub Issues](https://github.com/larcangeli/OrientationManager/issues)
- **Discussions**: Join the conversation in [GitHub Discussions](https://github.com/larcangeli/OrientationManager/discussions)
- **Wiki**: Check the [Wiki](https://github.com/larcangeli/OrientationManager/wiki) for detailed documentation

## 🎓 Academic Use

This project was developed as part of a student health and wellness initiative. If you use this project in academic research, please cite:

```bibtex
@software{OrientationManager2025,
  author = {larcangeli},
  title = {OrientationManager: Student Posture Monitoring System},
  year = {2025},
  url = {https://github.com/larcangeli/OrientationManager}
}
```

---

**Made with ❤️ for student health and wellness**
