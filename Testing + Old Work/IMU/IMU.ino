#include <Arduino_LSM9DS1.h>
#include <ArduinoBLE.h>

const float accelerationThreshold = 2.5; // threshold of significant in G's
const int BUTTON_PIN = 2; // the number of the pushbutton pin

int button_pressed;    // the current reading from the input pin
int prev_button_state = 1;

float max_x = 0;
float max_z;

void setup() {
    Serial.begin(9600);
    pinMode(BUTTON_PIN, INPUT);
    pinMode(4, OUTPUT);

    if (!IMU.begin()) {
      Serial.println("Failed to initialize IMU!");
      while (1);
    }
}

void loop() {
    digitalWrite(4, HIGH);
    float aX, aY, aZ, gX, gY, gZ;
    
    button_pressed = digitalRead(BUTTON_PIN);    
    if(button_pressed)
    {
      if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable()) {
        IMU.readAcceleration(aX, aY, aZ);
        IMU.readGyroscope(gX, gY, gZ);
        if (aX > max_x)
        {
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
        max_x = 0;
        max_z = 0;
      }
    }
    
}
        /*
        Serial.print(aX, 3);
        Serial.print(',');
        Serial.print(aY, 3);
        Serial.print(',');
        Serial.print(aZ, 3);
        Serial.print(',');
        Serial.print(gX, 3);
        Serial.print(',');
        Serial.print(gY, 3);
        Serial.print(',');
        Serial.print(gZ, 3);
        Serial.println();
        */
