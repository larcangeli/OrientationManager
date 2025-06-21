#include "Arduino_BHY2.h"
#include <math.h>
#include <ArduinoBLE.h>
#include "Nicla_System.h"

// Create sensor objects
SensorXYZ gyro(SENSOR_ID_GYRO);       // Raw gyroscope data
SensorQuaternion rotation(SENSOR_ID_RV); // Rotation vector (quaternion)

float pitch, roll, yaw;

BLEService orientationService("19B10000-E8F2-537E-4F6C-D104768A1214");
BLEStringCharacteristic csvDataCharacteristic("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify, 128);
BLEStringCharacteristic alertCharacteristic("19B10002-E8F2-537E-4F6C-D104768A1214", BLERead | BLENotify, 128);

char csvData[128];
char alertMessage[128];

const float ALERT_THRESHOLD = 5.0;

void quaternionToEuler(float w, float x, float y, float z, float& p, float& r, float& ya) {
  double sinr_cosp = 2.0 * (w * x + y * z);
  double cosr_cosp = 1.0 - 2.0 * (x * x + y * y);
  r = atan2(sinr_cosp, cosr_cosp);

  double sinp = 2.0 * (w * y - z * x);
  if (abs(sinp) >= 1)
    p = copysign(M_PI / 2.0, sinp); 
  else
    p = asin(sinp);

  double siny_cosp = 2.0 * (w * z + x * y);
  double cosy_cosp = 1.0 - 2.0 * (y * y + z * z);
  ya = atan2(siny_cosp, cosy_cosp);

  // Convert radians to degrees
  p = p * 180.0 / M_PI;
  r = r * 180.0 / M_PI;
  ya = ya * 180.0 / M_PI;
}

void setup() {
  Serial.begin(9600);
  
  nicla::begin();
  nicla::leds.begin();
  
  nicla::leds.setColor(green);
  
  if (!BLE.begin()) {
    Serial.println("Failed to initialize BLE!");
    nicla::leds.setColor(red);
    while (1);
  }

  BHY2.begin();
  gyro.begin();
  rotation.begin();

  BLE.setLocalName("NiclaSenseCSV");
  BLE.setAdvertisedService(orientationService);
  orientationService.addCharacteristic(csvDataCharacteristic);
  orientationService.addCharacteristic(alertCharacteristic);
  BLE.addService(orientationService);

  csvDataCharacteristic.writeValue("timestamp,pitch,roll,yaw,gyro_x,gyro_y,gyro_z");
  
  BLE.advertise();
  
  Serial.println("Nicla Sense ME orientation CSV over BLE started");
  Serial.println("Waiting for connections...");
  nicla::leds.setColor(blue);
}

void loop() {
  BLEDevice central = BLE.central();
  
  if (central) {
    Serial.print("Connected to central: ");
    Serial.println(central.address());
    nicla::leds.setColor(green);
    
    while (central.connected()) {
      static unsigned long lastUpdateTime = 0;
      static unsigned long lastAlertTime = 0;
      unsigned long currentTime = millis();
      
      BHY2.update();
      
      float q_w = rotation.w();
      float q_x = rotation.x();
      float q_y = rotation.y();
      float q_z = rotation.z();
      
      quaternionToEuler(q_w, q_x, q_y, q_z, pitch, roll, yaw);
      
      if (currentTime - lastUpdateTime >= 200) {
        lastUpdateTime = currentTime;
        
        snprintf(csvData, sizeof(csvData), 
                 "%lu,%.2f,%.2f,%.2f", 
                 currentTime, pitch, roll, yaw);
        csvDataCharacteristic.writeValue(csvData);
        
        Serial.println(csvData);
      }
      
      //for a vertical NICLA
      if (currentTime - lastAlertTime >= 1000){
        if (abs(pitch) > ALERT_THRESHOLD+1 || (abs(roll) > 100.0 || abs(roll) < 80.0)) {
          lastAlertTime = currentTime;

          if (abs(pitch) > ALERT_THRESHOLD+1 && (abs(roll) > 100.0 || abs(roll) < 80.0)) {
            snprintf(alertMessage, sizeof(alertMessage), "ALERT: Both side (%.1f°) and forward/backward (%.1f°) tilt exceed threshold", pitch, 90-roll);
          } else if (abs(pitch) > ALERT_THRESHOLD) {
            snprintf(alertMessage, sizeof(alertMessage), "ALERT: Side tilt (%.1f°) exceeds threshold", pitch);
          } else {
            snprintf(alertMessage, sizeof(alertMessage), "ALERT: Forward/backward tilt (%.1f°) exceeds threshold", 90-roll);  
          }
          alertCharacteristic.writeValue(alertMessage);
          Serial.println(alertMessage);
        }
      }

      /* for a horizontal NICLA
      if (currentTime - lastAlertTime >= 1000){
        if (abs(pitch) > ALERT_THRESHOLD || abs(roll) > ALERT_THRESHOLD) {
          lastAlertTime = currentTime;

          if (abs(pitch) > ALERT_THRESHOLD && (abs(roll) > 95.0 || abs(roll) < 85.0)) {
            snprintf(alertMessage, sizeof(alertMessage), "ALERT: Both pitch (%.1f°) and roll (%.1f°) exceed threshold", pitch, roll);
          } else if (abs(pitch) > ALERT_THRESHOLD) {
            snprintf(alertMessage, sizeof(alertMessage), "ALERT: Forward/backward tilt (%.1f°) exceeds threshold", pitch);
          } else {
            snprintf(alertMessage, sizeof(alertMessage), "ALERT: Side tilt (%.1f°) exceeds threshold", roll);  
          }
          alertCharacteristic.writeValue(alertMessage);
          Serial.println(alertMessage);
        }
      }
      */
      

    }
    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
    nicla::leds.setColor(blue);
  }
}