/**
 * Smart Energy Monitoring System - ESP32 Firmware
 * 
 * Hardware: ESP32 DevKit V1 + PZEM-004T v3.0 (AC Energy Meter) or SCT-013 CT Sensor
 * Protocol: WiFi 802.11 b/g/n + HTTP REST JSON Ingestion
 * 
 * Target Server Endpoint: POST http://<SERVER_IP>:8000/api/telemetry/ingest
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// WiFi Configuration
const char* ssid = "YOUR_FACTORY_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// Backend Server Configuration
const char* serverUrl = "http://192.168.1.100:8000/api/telemetry/ingest";
const char* deviceId = "ESP32-TX01";

// Pin Configuration (Hardware Serial 2 for PZEM-004T)
#define RXD2 16
#define TXD2 17

// Telemetry Sampling Interval
const unsigned long sampleIntervalMs = 2000;
unsigned long lastSampleTime = 0;

void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, RXD2, TXD2);

  Serial.println("\n[ESP32-EMS] Initializing Smart Energy Meter Firmware v2.5.0...");

  // Connect to WiFi
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("[ESP32-EMS] Connecting to WiFi");
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[ESP32-EMS] WiFi Connected!");
    Serial.print("[ESP32-EMS] IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[ESP32-EMS] Running in offline demo buffer mode...");
  }
}

void loop() {
  unsigned long currentMillis = millis();

  if (currentMillis - lastSampleTime >= sampleIntervalMs) {
    lastSampleTime = currentMillis;

    // Read Electrical Parameters from Sensor or Synthesized ADCs
    float voltage = readVoltage();
    float current = readCurrent();
    float powerFactor = readPowerFactor();
    float activePowerKw = (voltage * current * powerFactor) / 1000.0;
    float reactivePowerKvar = sqrt(max(0.0f, pow(voltage * current / 1000.0f, 2) - pow(activePowerKw, 2)));
    float frequency = 50.0;
    float temperature = readInternalTemperature();

    // Transmit to Backend
    if (WiFi.status() == WL_CONNECTED) {
      sendTelemetryPayload(voltage, current, activePowerKw, reactivePowerKvar, powerFactor, frequency, temperature);
    } else {
      Serial.printf("[LOCAL LOG] V: %.1fV, I: %.2fA, P: %.2fkW, PF: %.2f, Temp: %.1fC\n",
                    voltage, current, activePowerKw, powerFactor, temperature);
    }
  }
}

float readVoltage() {
  // Replace with PZEM.voltage() or ADC voltage divider
  return 230.0 + random(-30, 30) / 10.0;
}

float readCurrent() {
  // Replace with PZEM.current() or SCT-013 ADC analogRead
  return 42.5 + random(-40, 40) / 10.0;
}

float readPowerFactor() {
  return 0.94 + random(-3, 3) / 100.0;
}

float readInternalTemperature() {
  return 38.5 + random(-10, 15) / 10.0;
}

void sendTelemetryPayload(float v, float i, float kw, float kvar, float pf, float hz, float temp) {
  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "application/json");

  // Create JSON Document
  StaticJsonDocument<384> doc;
  doc["device_id"] = deviceId;
  doc["voltage_v"] = v;
  doc["voltage_l1"] = v;
  doc["voltage_l2"] = v;
  doc["voltage_l3"] = v;
  doc["current_a"] = i;
  doc["current_l1"] = i;
  doc["current_l2"] = i;
  doc["current_l3"] = i;
  doc["active_power_kw"] = kw;
  doc["reactive_power_kvar"] = kvar;
  doc["power_factor"] = pf;
  doc["frequency_hz"] = hz;
  doc["temperature_c"] = temp;

  String requestBody;
  serializeJson(doc, requestBody);

  int httpResponseCode = http.POST(requestBody);
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.printf("[HTTP %d] Telemetry pushed successfully. Response: %s\n", httpResponseCode, response.c_str());
  } else {
    Serial.printf("[HTTP ERROR] Failed to send telemetry, code: %d\n", httpResponseCode);
  }

  http.end();
}
