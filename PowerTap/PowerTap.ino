#include "config.h"

#include <WiFiClientSecure.h>
#include <MQTTClient.h>  //MQTT Library Source: https://github.com/256dpi/arduino-mqtt

#include <ArduinoJson.h>  //ArduinoJson Library Source: https://github.com/bblanchon/ArduinoJson
#include "WiFi.h"

#include "time.h"
#include "sntp.h"

#include <Wire.h>
#include <Adafruit_ADS1X15.h>

Adafruit_ADS1115 ads;
WiFiClientSecure wifi_client = WiFiClientSecure();
MQTTClient mqtt_client = MQTTClient(256);  //256 indicates the maximum size for packets being published and received.
void connectAWS() {
  //Begin WiFi in station mode
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.println("Connecting to Wi-Fi");

  //Wait for WiFi connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();

  // Configure wifi_client with the correct certificates and keys
  wifi_client.setCACert(AWS_CERT_CA);
  wifi_client.setCertificate(AWS_CERT_CRT);
  wifi_client.setPrivateKey(AWS_CERT_PRIVATE);

  //Connect to AWS IOT Broker. 8883 is the port used for MQTT
  mqtt_client.begin(AWS_IOT_ENDPOINT, 8883, wifi_client);

  //Set action to be taken on incoming messages
  mqtt_client.onMessage(incomingMessageHandler);

  Serial.print("Connecting to AWS IOT");

  //Wait for connection to AWS IoT
  while (!mqtt_client.connect(THINGNAME)) {
    Serial.print(".");
    delay(100);
  }
  Serial.println();

  if (!mqtt_client.connected()) {
    Serial.println("AWS IoT Timeout!");
    return;
  }

  //Subscribe to a topic
  mqtt_client.subscribe(AWS_IOT_SUBSCRIBE_TOPIC);

  Serial.println("AWS IoT Connected!");
}

void publishMessage() {
  //Create a JSON document of size 200 bytes, and populate it
  //See https://arduinojson.org/
  StaticJsonDocument<200> doc;
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    Serial.println("No time available (yet)");
    return;
  }
  // Converting time to a desired time format
  String month = String(timeinfo.tm_mon + 1);
  if (month.length() == 1) {
    month = "0" + month;
  }
  String day = String(timeinfo.tm_mday);
  if (day.length() == 1) {
    day = "0" + day;
  }
  String year = String((timeinfo.tm_year + 1900) % 100);
  String hour = String(timeinfo.tm_hour);
  if (hour.length() == 1) {
    hour = "0" + hour;
  }
  String minute = String(timeinfo.tm_min);
  if (minute.length() == 1) {
    minute = "0" + minute;
  }
  String second = String(timeinfo.tm_sec);
  if (second.length() == 1) {
    second = "0" + second;
  }
  doc["Timestamp"] = month + "-" + day + "-" + year + " " + hour + ":" + minute + ":" + second;
  doc["Location"] = "Room 1";
  ADC = ads.readADC_SingleEnded(0); // Read the ADC Value
  if (ADC < 0) voltage = 0.0;
  else voltage = (ADC * 0.1875)/1000; // Convert ADC to voltage
  float conversion_factor = 20 * 120;
  float power = voltage * conversion_factor;
  doc["Power"] = power;
  char jsonBuffer[512];
  serializeJson(doc, jsonBuffer);  // print to mqtt_client
  //Publish to the topic + Sends jsonBuffer to dynamoDB based on Rule
  mqtt_client.publish(AWS_IOT_PUBLISH_TOPIC, jsonBuffer);
  Serial.println("Sent JSON: " + String(jsonBuffer));
}

// Can send messages from AWS to the IoT
void incomingMessageHandler(String &topic, String &payload) {
  Serial.println("Message received!");
  Serial.println("Topic: " + topic);
  Serial.println("Payload: " + payload);
}

// Callback function (get's called when time adjusts via NTP)
void timeavailable(struct timeval *t) {
  Serial.println("Got time adjustment from NTP!");
}

void setup() {
  ads.begin(); // Start the ADC
  Serial.begin(115200);
  // set notification call-back function
  sntp_set_time_sync_notification_cb(timeavailable); /**
   * NTP server address could be aquired via DHCP,
   *
   * NOTE: This call should be made BEFORE esp32 aquires IP address via DHCP,
   * otherwise SNTP option 42 would be rejected by default.
   * NOTE: configTime() function call if made AFTER DHCP-client run
   * will OVERRIDE aquired NTP server address
   */
  sntp_servermode_dhcp(1);                           // (optional)
  /**
   * This will set configured ntp servers and constant TimeZone/daylightOffset
   * should be OK if your time zone does not need to adjust daylightOffset twice a year,
   * in such a case time adjustment won't be handled automagicaly.
   */
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer1, ntpServer2);

  connectAWS();
}

void loop() {
  publishMessage();
  mqtt_client.loop();
  delay(1000);
}
