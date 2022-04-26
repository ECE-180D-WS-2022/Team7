import asyncio

from bleak import BleakScanner
from bleak import BleakClient
import logging
import struct

from collections import deque
import numpy as np
import argparse
import imutils
import cv2
import urllib 
import time
import speech_recognition as sr

import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print("Connection returned result: "+str(rc))
    if rc != 0:
        print("connection failed")
        quit()

def on_disconnect(client, userdata, rc): 
    if rc != 0:     
        print('Unexpected Disconnect')
    else:
        print('Expected Disconnect')

def on_message(client, userdata, message): 
  print('Received message: "' + str(message.payload) + '" on topic "' + 
        message.topic + '" with QoS ' + str(message.qos))

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client.on_message = on_message
mqtt_client.connect_async("test.mosquitto.org")
mqtt_client.loop_start()


# Setup Color Detection 
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the (optional) video file")
ap.add_argument("-b", "--buffer", type=int, default=64, help="max buffer size")
args = vars(ap.parse_args())
 

# Ranges for the balls 
lower = {'orange':(5, 50, 50), 'green':(66, 122, 129), 'blue':(97, 100, 117), 'purple':(129, 50, 70)} 
upper = {'orange':(15,255,255), 'green':(86,255,255), 'blue':(117,255,255), 'purple':(158,255,255)}
 
# Color of texts displayed 
colors = {'orange':(0,140,255), 'green':(0,255,0), 'blue':(255,0,0), 'purple':(230,100,230)}
modes = {'Mars':1, 'Earth':2, 'Jupytor':3, 'Venus':4}
 

if not args.get("video", False):
    camera = cv2.VideoCapture(0)

else:
    camera = cv2.VideoCapture(args["video"])
    
    
'''
# obtain audio from the microphone

r = sr.Recognizer()
with sr.Microphone() as source:
    print("Say 'start' to launch the game, 'help' to see commands")
    audio = r.listen(source)

try:
    print("Command detected " + r.recognize_sphinx(audio))
except sr.UnknownValueError:
    print("Sphinx could not understand audio")
except sr.RequestError as e:
    print("Sphinx error; {0}".format(e))


command = r.recognize_sphinx(audio)
'''
class Connection:
    
    client: BleakClient = None
    
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        max_x_characteristic: str,
        max_z_characteristic: str,
        mqtt_client
    ):
        self.loop = loop
        self.max_x_characteristic = max_x_characteristic
        self.max_z_characteristic = max_z_characteristic
        self.mqtt_client = mqtt_client
        self.velocity = 0
        self.voice_command = 0
        
        # Device state
        self.connected = False
        self.connected_device = None

        self.max_x_data = []
        self.max_z_data = []

    def on_disconnect(self, client: BleakClient):
        self.connected = False
        # Put code here to handle what happens on disconnet.
        print(f"Disconnected from {self.connected_device.name}!")

    def max_x_characteristic_handler(self, sender: str, data: bytearray):
        print("X value:")
        clean_data = struct.unpack('f', data)
        print(clean_data)

    def max_z_characteristic_handler(self, sender: str, data: bytearray):
        print("Z value:")
        clean_data = struct.unpack('f', data)
        print(clean_data)

    async def manager(self):
        print("Starting connection manager.")
        while True:
            if self.client:
                await self.connect()
                await asyncio.sleep(5.0, loop=loop)
            else:
                await self.select_device()
                await asyncio.sleep(15.0, loop=loop) 

    async def connect(self):
        if self.connected:
            return
        try:
            await self.client.connect()
            print("client was connected")
            if self.client.is_connected():
                print(f"Connected to {self.connected_device.name}")
                self.client.set_disconnected_callback(self.on_disconnect)

                while True:
                    for service in self.client.services:
                        for char in service.characteristics:
                            # print ('characteristic =', str(char))
                            # print ('characteristic type =', str(type(char)))
                            if "read" in char.properties:
                                # TODO: need to differentiate between the properties
                                # maybe can use the char uuid
                                value = bytes(await self.client.read_gatt_char(char.uuid))
                                # velocity
                                if str(char.uuid) == '00001142-0000-1000-8000-00805f9b34fb':
                                    max_x = struct.unpack('f', value)
                                    if max_x != self.velocity:
                                        self.velocity = max_x
                                        print('velocity = ', self.velocity)
                                        publish_result = self.mqtt_client.publish('ece180d/team7/pygame', float(self.velocity[0]), qos=1)
                                        print(publish_result)
                                elif str(char.uuid) == '00001143-0000-1000-8000-00805f9b34fb':
                                    self.voice_command = struct.unpack('i', value)
                                    publish_result = self.mqtt_client.publish('ece180d/team7/pygame', int(self.voice_command), qos=1)
                                    print(publish_result)
 
            else:
                print(f"Failed to connect to {self.connected_device.name}")
        except Exception as e:
            print(e)
    
    async def cleanup(self):
        if self.client:
            # await self.client.stop_notify(max_x_characteristic)
            await self.client.disconnect()

    async def select_device(self):
        print("Bluetooh LE hardware warming up...")
        await asyncio.sleep(2.0, loop=loop) # Wait for BLE to initialize.
        devices = await BleakScanner.discover()

        print("Please select device: ")
        for i, device in enumerate(devices):
            print(f"{i}: {device.name}")

        response = -1
        while True:
            response = input("Select device: ")
            try:
                response = int(response.strip())
            except:
                print("Please make valid selection.")
            
            if response > -1 and response < len(devices):
                break
            else:
                print("Please make valid selection.")
        
        print(f"Connecting to {devices[response].name}")
        self.connected_device = devices[response]
        self.client = BleakClient(devices[response].address)
        print("here")


def choose_level():
    mode = 0
    print('Game launching')
    # time.sleep(1)
    print('Choose Game Mode')
    # time.sleep(3)
    detected=False
    count = 0
    
    while True:
        
        (grabbed, frame) = camera.read()
        if args.get("video") and not grabbed:
            break


        frame = imutils.resize(frame, width=900)

        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        
        cv2.putText(frame, "Bring the ball closer to camera", (20,30), cv2.FONT_HERSHEY_SIMPLEX, 1.5 ,[255, 255, 255],2)
        for key, value in upper.items():

            kernel = np.ones((9,9),np.uint8)
            mask = cv2.inRange(hsv, lower[key], upper[key])
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)


            cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE)[-2]
            center = None
            


            if len(cnts) > 0:

                c = max(cnts, key=cv2.contourArea)
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))


                if radius > 0.5:

                    cv2.circle(frame, (int(x), int(y)), int(radius), colors[key], 5)
                    cv2.putText(frame,key + "color", (int(x-radius),int(y-radius)), cv2.FONT_HERSHEY_SIMPLEX, 0.6,colors[key],2)

                if radius > 250:
                    detected=True
                    if key == "orange":
                            cv2.putText(frame, "Game mode: Mars", (100,100), cv2.FONT_HERSHEY_SIMPLEX, 0.6,colors[key],2)
                            mode = 1
                            count = count + 1

                    elif key=="blue":
                            cv2.putText(frame, "Game mode: Earth", (100,100), cv2.FONT_HERSHEY_SIMPLEX, 0.6,colors[key],2)
                            mode = 2
                            count = count + 1

                    elif key=="green":
                            cv2.putText(frame, "Game mode: Jupytor", (100,100), cv2.FONT_HERSHEY_SIMPLEX, 0.6,colors[key],2)
                            mode = 3
                            count = count + 1

                    elif key=="purple":
                            cv2.putText(frame, "Game mode: Venus", (100,100), cv2.FONT_HERSHEY_SIMPLEX, 0.6,colors[key],2)
                            mode = 4
                            count = count + 1
                    else:
                        mode = 0


        cv2.imshow("Frame", frame)
        
      
        key = cv2.waitKey(1) & 0xFF
        # press 'q' to stop the loop
        if key == ord("q"):
            break
        if count > 150: 
            break

    camera.release()
    cv2.destroyAllWindows()
    
    # game mode 1: Mars (Orange)
    # game mode 2: Earth (Blue)
    # game mode 3: Jupytor (green)
    # game mode 4: Venus (purple)
    return mode

'''
while True:
    if command=='start': 
        break
    else:
        continue
'''

game_mode = choose_level()
print(game_mode)


loop = asyncio.get_event_loop()
max_x_characteristic = "00001142-0000-1000-8000-00805f9b34fb"
max_z_characteristic = ""
voice_characteristic = "00001143-0000-1000-8000-00805f9b34fb"

connection = Connection(
    loop, max_x_characteristic, max_z_characteristic, mqtt_client)
try:
    
    asyncio.ensure_future(connection.manager())
    loop.run_forever()
except KeyboardInterrupt:
    print()
    print("User stopped program.")
finally:
    print("Disconnecting...")
    loop.run_until_complete(connection.cleanup())
