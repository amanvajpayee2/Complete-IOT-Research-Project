#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

const char* ssid = "put your own wifi ssid";
const char* password = "put your own wifi password";
const char* mqtt_server = "test.mosquitto.org";
const int mqtt_port = 1883;
const char* mqtt_topic = "face_control/esp32/rotate";
const char* SECRET_TOKEN = "aman_face_access";

const int SERVO_PIN = 13;
const int LED_PIN = 2;

WiFiClient espClient;
PubSubClient client(espClient);
Servo myservo;

void doLed(int times=3, int ms_delay=200) {
  for (int i=0;i<times;i++){
    digitalWrite(LED_PIN,HIGH);
    delay(ms_delay);
    digitalWrite(LED_PIN,LOW);
    delay(ms_delay);
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (unsigned int i=0;i<length;i++) msg += (char)payload[i];
  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, msg);
  if (err) {
    Serial.print("[MQTT] JSON parse error: ");
    Serial.println(err.c_str());
    return;
  }
  const char* token = doc["token"];
  if (!token || String(token) != SECRET_TOKEN) {
    Serial.println("[MQTT] Token mismatch - ignoring.");
    return;
  }
  if (doc.containsKey("led")) {
    bool ledcmd = doc["led"];
    int times = doc["times"] | 3;
    int ms = doc["ms"] | 200;
    Serial.println("[MQTT] LED command - blinking");
    doLed(times, ms);
  }
  if (doc.containsKey("angle")) {
    int angle = doc["angle"] | 180;
    if (angle < 0) angle = 0;
    if (angle > 180) angle = 180;
    Serial.print("[MQTT] Servo command - rotating to ");
    Serial.println(angle);
    myservo.write(angle);
    delay(800);
    myservo.write(0);
    Serial.println("[MQTT] Servo returned to 0");
  }
  if (doc.containsKey("spin") && doc["spin"] == true) {
    Serial.println("[MQTT] Spin command received (approx 360 using two 180 moves).");
    myservo.write(180);
    delay(800);
    myservo.write(0);
    delay(400);
    myservo.write(180);
    delay(800);
    myservo.write(0);
    Serial.println("[MQTT] Approx spin complete.");
  }
}

void reconnect() {
  while (!client.connected()) {
    Serial.print("[MQTT] Attempting MQTT connection...");
    if (client.connect("esp32_unified")) {
      Serial.println("connected");
      client.subscribe(mqtt_topic);
      Serial.print("[MQTT] Subscribed to ");
      Serial.println(mqtt_topic);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5s");
      delay(5000);
    }
  }
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  myservo.attach(SERVO_PIN);
  myservo.write(0);
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  Serial.print("[WiFi] Connecting");
  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    if (millis() - start > 20000) {
      Serial.println();
      Serial.println("[WiFi] Connect timeout - restarting");
      ESP.restart();
    }
  }
  Serial.println();
  Serial.print("[WiFi] Connected! IP: ");
  Serial.println(WiFi.localIP());
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();
}
