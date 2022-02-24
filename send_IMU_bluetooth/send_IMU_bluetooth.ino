#include <Arduino_LSM9DS1.h>
#include <ArduinoBLE.h>

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
const char* max_z_uuid = "00001143-0000-1000-8000-00805f9b34fb";


//----------------------------------------------------------------------------------------------------------------------
// BLE
//----------------------------------------------------------------------------------------------------------------------

BLEService testService( BLE_UUID_TEST_SERVICE );
BLEFloatCharacteristic max_x_Characteristic(max_x_uuid, BLERead | BLENotify | BLEBroadcast );
BLEFloatCharacteristic max_z_Characteristic(max_z_uuid, BLERead | BLENotify | BLEBroadcast);

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

void setup() {
  Serial.begin(9600);
  while (!Serial);

  Serial.println("Starting code");

  pinMode(led_pin, OUTPUT);
  pinMode(BUTTON_PIN, INPUT);
  pinMode(4, OUTPUT);

  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }

  // set advertised local name and service
  if (!BLE.begin()) {
    Serial.println("starting BLE failed!");
    while (1);
  }

  BLE.setDeviceName( "Arduino Nano 33 BLE" );
  BLE.setLocalName( ble_name );
  BLE.setAdvertisedService( testService );


  // BLE add characteristics
  testService.addCharacteristic( max_x_Characteristic );
  testService.addCharacteristic( max_z_Characteristic );

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
      else {
        if (prev_button_state == 0 && button_pressed == 0) {
          Serial.print("max x = ");
          Serial.println(max_x);
          Serial.print("max z = ");
          Serial.println(max_z);
          prev_button_state = 1;
          max_x_Characteristic.writeValue(max_x);
          max_z_Characteristic.writeValue(max_z);
          max_x = 0;
          max_z = 0;
        }
      }
    }
  }   
}
  
  
  
