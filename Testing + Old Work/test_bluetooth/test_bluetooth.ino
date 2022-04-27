#include <ArduinoBLE.h>

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
//BLEByteCharacteristic max_x_Characteristic( BLE_UUID_MAX_X, BLERead | BLENotify | BLEBroadcast );
//BLEByteCharacteristic max_z_Characteristic( BLE_UUID_MAX_Z, BLERead | BLENotify | BLEBroadcast);

float x_buffer[256];
float z_buffer[256];

float max_x = 0.1;
float max_z = 0.2;


const char* ble_name = "Arduino Nano 33 BLE";

const int led_pin =  23;      // the number of the LED pin


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

void setup() {
  Serial.begin(9600);
  while (!Serial);
  
  Serial.println("Starting code");

  pinMode(led_pin, OUTPUT);

  
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

  // set the initial value for characeristics
//  max_x_Characteristic.writeValue( max_x );
//  max_z_Characteristic.writeValue( max_z );

  for (int i = 0; i < 256; i++)
  {
    x_buffer[i] = 0.1;
    z_buffer[i] = 0.2;
  }

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
  BLEDevice central = BLE.central();

  if (central) 
  {
    while (central.connected())
    {
      while (central.connected()) {

//        for (int i = 0; i < 256; i++) {
//          max_x_Characteristic.writeValue(x_buffer[i]); 
//          max_z_Characteristic.writeValue(z_buffer[i]);
//        }
        
        max_x_Characteristic.writeValue(max_x);
        max_z_Characteristic.writeValue(max_z);
//        max_x = max_x + 0.1;
//        max_z = max_z + 0.1;
      }
    }
  }
}
