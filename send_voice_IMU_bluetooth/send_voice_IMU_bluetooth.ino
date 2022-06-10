/*
 * Voice classifier for Arduino Nano 33 BLE Sense by Alan Wang
 */

#include <math.h>
#include <PDM.h>
#include <EloquentTinyML.h>      // https://github.com/eloquentarduino/EloquentTinyML
//#include <eloquent_tinyml/tensorflow.h>
#include "model.h"       // TF Lite model file

#include <Arduino_LSM9DS1.h>
#include <ArduinoBLE.h>

#define PDM_SOUND_GAIN     255   // sound gain of PDM mic
#define PDM_BUFFER_SIZE    256   // buffer size of PDM mic

#define SAMPLE_THRESHOLD   900   // RMS threshold to trigger sampling
#define FEATURE_SIZE       32    // sampling size of one voice instance
#define SAMPLE_DELAY       20    // delay time (ms) between sampling

#define NUMBER_OF_LABELS   5     // number of voice labels
const String words[NUMBER_OF_LABELS] = {"Start", "Rules", "Single", "Multi", "Planet"};  // words for each label


#define PREDIC_THRESHOLD   0.6   // prediction probability threshold for labels
#define RAW_OUTPUT         true  // output prediction probability of each label
#define NUMBER_OF_INPUTS   FEATURE_SIZE
#define NUMBER_OF_OUTPUTS  NUMBER_OF_LABELS
#define TENSOR_ARENA_SIZE  4 * 1024


Eloquent::TinyML::TfLite<NUMBER_OF_INPUTS, NUMBER_OF_OUTPUTS, TENSOR_ARENA_SIZE> tf_model;
float feature_data[FEATURE_SIZE];
volatile float rms;
bool voice_detected;


//----------------------------------------------------------------------------------------------------------------------
// Variable Initializations / Definitions
//----------------------------------------------------------------------------------------------------------------------

const int led_pin =  23;      // the number of the LED pin
const int BUTTON_PIN = 2; // the number of the pushbutton pin

int button_pressed;    // the current reading from the input pin
int prev_button_state = 1;

float max_x = 0;
float max_z;

//----------------------------------------------------------------------------------------------------------------------
// BLE UUIDs
//----------------------------------------------------------------------------------------------------------------------

#define BLE_UUID_TEST_SERVICE               "9A48ECBA-2E92-082F-C079-9E75AAE428B1"
#define BLE_UUID_MAX_X                      "C8F88594-2217-0CA6-8F06-A4270B675D69"
#define BLE_UUID_MAX_Z                      "E3ADBF53-950E-DC1D-9B44-076BE52760D6"


const char* max_x_uuid = "00001142-0000-1000-8000-00805f9b34fb";
//const char* max_z_uuid = "00001143-0000-1000-8000-00805f9b34fb";
const char* voice_uuid = "00001143-0000-1000-8000-00805f9b34fb";


//----------------------------------------------------------------------------------------------------------------------
// BLE
//----------------------------------------------------------------------------------------------------------------------

BLEService testService( BLE_UUID_TEST_SERVICE );
BLEFloatCharacteristic max_x_Characteristic(max_x_uuid, BLERead | BLENotify | BLEBroadcast );
BLEIntCharacteristic voice_Characteristic(voice_uuid, BLERead | BLENotify | BLEBroadcast );

//BLEFloatCharacteristic max_z_Characteristic(max_z_uuid, BLERead | BLENotify | BLEBroadcast);

const char* ble_name = "Arduino Nano 33 BLE";

void onBLEConnected(BLEDevice central) {
  Serial.print("Connected event, central: ");
  Serial.println(central.address());
  digitalWrite(led_pin, HIGH);
}

void onBLEDisconnected(BLEDevice central) {
  Serial.print("Disconnected event, central: ");
  Serial.println(central.address());
  digitalWrite(led_pin, LOW);
}

//----------------------------------------------------------------------------------------------------------------------


// callback function for PDM mic
void onPDMdata() {

  rms = -1;
  short sample_buffer[PDM_BUFFER_SIZE];
  int bytes_available = PDM.available();
  PDM.read(sample_buffer, bytes_available);

  // calculate RMS (root mean square) from sample_buffer
  unsigned int sum = 0;
  for (unsigned short i = 0; i < (bytes_available / 2); i++) sum += pow(sample_buffer[i], 2);
  rms = sqrt(float(sum) / (float(bytes_available) / 2.0));
}

void setup() {

  Serial.begin(115200);
//  while (!Serial);

  pinMode(BUTTON_PIN, INPUT);
  pinMode(4, OUTPUT);

  PDM.onReceive(onPDMdata);
  PDM.setBufferSize(PDM_BUFFER_SIZE);
  PDM.setGain(PDM_SOUND_GAIN);

  if (!PDM.begin(1, 16000)) {  // start PDM mic and sampling at 16 KHz
    Serial.println("Failed to start PDM!");
    while (1);
  }

  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }

  // set advertised local name and service
  if (!BLE.begin()) {
    Serial.println("starting BLE failed!");
    while (1);
  }

  pinMode(LED_BUILTIN, OUTPUT);

  BLE.setDeviceName( "Arduino Nano 33 BLE" );
  BLE.setLocalName( ble_name );
  BLE.setAdvertisedService( testService );


  // BLE add characteristics
  testService.addCharacteristic( max_x_Characteristic );
  testService.addCharacteristic (voice_Characteristic);
//  testService.addCharacteristic( max_z_Characteristic );

  // add service
  BLE.addService(testService);
  
  // Bluetooth LE connection handlers.
  BLE.setEventHandler(BLEConnected, onBLEConnected);
  BLE.setEventHandler(BLEDisconnected, onBLEDisconnected);

  BLE.advertise();
  // Print out full UUID and MAC address.
  Serial.println("Peripheral advertising info: ");
  Serial.print("Name: ");
  Serial.println(ble_name);
  Serial.print("MAC: ");
  Serial.println(BLE.address());
  Serial.println("Bluetooth device active, waiting for connections...");
  
    // start TF Lite model
  tf_model.begin((unsigned char*) model_data);
  
  Serial.println("=== Classifier start ===\n");
}

void loop() {

  float aX, aY, aZ, gX, gY, gZ;
  digitalWrite(4, HIGH);

  BLEDevice central = BLE.central();

  if (central) {
    while (central.connected()){
      button_pressed = digitalRead(BUTTON_PIN);

      if(button_pressed) {
        if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable()) {
          IMU.readAcceleration(aX, aY, aZ);
          IMU.readGyroscope(gX, gY, gZ);
          if (aX > max_x) {
            max_x = aX;
            max_z = aZ;
          }
          prev_button_state = 0;
        }
      }
      else if (prev_button_state == 0 && button_pressed == 0) {
        Serial.print("max x = ");
        Serial.println(max_x);
        Serial.print("max z = ");
        Serial.println(max_z);
        prev_button_state = 1;
        max_x_Characteristic.writeValue(max_x);
        max_x = 0;
        max_z = 0;
      }
      else {
        // waiting until sampling triggered
        if (rms > SAMPLE_THRESHOLD) {
          for (int i = 0; i < FEATURE_SIZE; i++) {  // sampling
            while (rms < 0);
            feature_data[i] = rms;
            delay(SAMPLE_DELAY);
          }
        
          // predict voice and put results (probability) for each label in the array
          float prediction[NUMBER_OF_LABELS];
          tf_model.predict(feature_data, prediction);
        
          // print out prediction results;
          // in theory, you need to find the highest probability in the array,
          // but only one of them would be high enough over 0.5~0.6
          Serial.println("Predicting the word:");
          if (RAW_OUTPUT) {
            for (int i = 0; i < NUMBER_OF_LABELS; i++) {
              Serial.print("Label ");
              Serial.print(i);
              Serial.print(" = ");
              Serial.println(prediction[i]);
            }
          }
          voice_detected = false;
          for (int i = 0; i < NUMBER_OF_LABELS; i++) {
            if (prediction[i] >= PREDIC_THRESHOLD) {
              Serial.print("Word detected: ");
              Serial.println(words[i]);
              Serial.println("");
              voice_detected = true;
              voice_Characteristic.writeValue(i);
            }
          }
          if (!voice_detected && !RAW_OUTPUT) Serial.println("Word not recognized\n");
        }
      }
    }
  }   
}
