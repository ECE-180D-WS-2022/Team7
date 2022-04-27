'''
calculate_coordinates.py: 
1. Read serial data from Arduino to collect IMU data
2. Process IMU data to be used for physics trajectory calculation
3. Calculate trajectory of dart path for placement on board (x,y) grid

Libraries necessary:
pyserial
'''

import serial

# declare serial port variable
arduino_serial = serial.Serial("COM5", 9600)

# loop through and read data from IMU
while 1:
  incoming = arduino_serial.readline().decode("utf-8")

  # TODO: convert into a list
  print(str(incoming))

''' TODO: 
parse through and process the data
figure out which values are necessary for the physics trajectory calculation

HAVE: 
  - Acceleration in horizontal axis  
  - Gyroscopic measurements
WANT:
  - Angle of throw/release
  - Calculation for trajectory
