import asyncio
from bleak import BleakScanner
from bleak import BleakClient
import logging
import struct

import pygame
from sys import exit
from random import randint, choice
from math import atan, radians, cos, sin

from collections import deque
import numpy as np
import argparse
import imutils
import cv2
import urllib 
# import speech_recognition as sr
import time

logger = logging.getLogger(__name__)



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
    
    
    
# obtain audio from the microphone


BLACK = (0, 0, 0)
BLUE = (0, 0, 255)

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        
        self.player_walk = pygame.image.load('graphics/player/player_walk_1.png').convert_alpha()
        self.image = self.player_walk
        self.player_jump = pygame.image.load('graphics/player/jump.png').convert_alpha()

        self.rect = self.image.get_rect(midbottom = (80,300))
        self.gravity = 0

        self.jump_sound = pygame.mixer.Sound('audio/jump.mp3')
        self.jump_sound.set_volume(0.5)

    def player_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] and self.rect.bottom >= 300:
            self.gravity = -20
            self.jump_sound.play()

    def apply_gravity(self):
        self.gravity += 1
        self.rect.y += self.gravity
        if self.rect.bottom >= 300:
            self.rect.bottom = 300

    def update(self):
        self.player_input()
        self.apply_gravity()
        
class Cup(pygame.sprite.Sprite):
    def __init__(self,x_pos):
        super().__init__()
        
        self.cup = pygame.image.load('graphics/Fly/Fly1.png').convert_alpha()
        self.image = self.cup

        self.rect = self.image.get_rect(midbottom = (x_pos,300))


class Ball(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        
        ball = pygame.image.load('graphics/snail/snail1.png').convert_alpha()
        self.image = ball
        self.rect = self.image.get_rect(midbottom = (100,300))

    def ball_path(self,power,time):
        angle = 0.785
        vel = power/1.25+20
        vel_x = vel * cos(angle)
        vel_y = vel * sin(angle)
        dist_x = vel_x * time
        dist_y = (vel_y * time) + ((-9.8 * (time)**2)/2)
        self.rect.midbottom = (round(dist_x + 100),round(-1*dist_y + 300))

    def destroy(self):
        if (self.rect.midbottom[0] > 900) or (self.rect.midbottom[0] < 0) or (self.rect.midbottom[1] > 300):
            self.kill()
            
    def update(self,power,time):
        self.ball_path(power,time)
        self.destroy()

class PowerBar:
    def __init__(self):
        self.power = 0
        self.direction = 1

    def draw(self, screen):
        pygame.draw.rect(screen, BLACK, (250, 100, 300, 50), 1)
        pygame.draw.rect(screen, BLUE, (250, 100, self.power*3, 50), 0)

    def move_bar(self):
        self.power += self.direction
        if self.power <= 0 or self.power >= 100:
            self.direction *= -1
    
    def ret_power(self):
        return self.power
    
    def reset(self):
        self.power = 0
        self.direction = 1

def display_score():
    current_time = int(pygame.time.get_ticks()) - start_time
    score_surf = test_font.render(f'Score: {current_time}',False,(64,64,64))
    score_rect = score_surf.get_rect(center = (400,50))
    screen.blit(score_surf,score_rect)
    return current_time

#def collision_sprite():
#    if pygame.sprite.spritecollide(.sprite,obstacle_group,False):
#        obstacle_group.empty()
#        return False
#    else: return True

# start of main code
pygame.init()
screen = pygame.display.set_mode((800,400))
pygame.display.set_caption('Bruin Pong')
clock = pygame.time.Clock()
test_font = pygame.font.Font('font/Pixeltype.ttf', 50)
game_active = False
start_time = 0
score = 0
#bg_music = pygame.mixer.Sound('audio/music.wav')
#bg_music.play(loops = -1)

#Groups
player = pygame.sprite.GroupSingle()
player.add(Player())

ball = pygame.sprite.GroupSingle()
cup_group = pygame.sprite.Group()

sky_surface = pygame.image.load('graphics/Sky.png').convert()
ground_surface = pygame.image.load('graphics/ground.png').convert()

# Intro screen
player_stand = pygame.image.load('graphics/player/player_stand.png').convert_alpha()
player_stand = pygame.transform.rotozoom(player_stand,0,2)
player_stand_rect = player_stand.get_rect(center = (400,200))

game_name = test_font.render('Bruin Pong',False,(111,196,169))
game_name_rect = game_name.get_rect(center = (400,80))

game_message = test_font.render('Press space to start',False,(111,196,169))
game_message_rect = game_message.get_rect(center = (400,330))

# Timer
ball_timer = pygame.USEREVENT + 1
pygame.time.set_timer(ball_timer,1500)

# global variables
is_throw = False
time = 0



class Connection:
    
    client: BleakClient = None
    
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        max_x_characteristic: str,
        max_z_characteristic: str
    ):
        self.loop = loop
        self.max_x_characteristic = max_x_characteristic
        self.max_z_characteristic = max_z_characteristic
        
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
            else:
                await self.select_device()
                await asyncio.sleep(15.0, loop=loop) 

    async def connect(self):
        if self.connected:
            return
        try:
            # print("here now")
            # print(self.client)
            await self.client.connect()
            print("client was connected")
            # self.connected = await self.client.is_connected()
            # if self.connected:
            if self.client.is_connected():
                print(f"Connected to {self.connected_device.name}")
                self.client.set_disconnected_callback(self.on_disconnect)

                await self.client.start_notify(
                    self.max_x_characteristic, self.max_x_characteristic_handler,
                )
                await self.client.start_notify(
                    self.max_z_characteristic, self.max_z_characteristic_handler,
                )
                while True:
                    if not self.connected:
                        break
                    for service in self.client.services:
                        for char in service.characteristics:
                            if "read" in char.properties:
                                value = bytes(await self.client.read_gatt_char(char.uuid))
                                print(f"\t[Characteristic] {char} ({','.join(char.properties)}), Value: {value}")
                    await asyncio.sleep(5.0, loop=loop)
                    
            else:
                print(f"Failed to connect to {self.connected_device.name}")
        except Exception as e:
            print(e)
    
    async def cleanup(self):
        if self.client:
            await self.client.stop_notify(max_x_characteristic)
            await self.client.stop_notify(max_z_characteristic)
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

    async def play_game(self):
        while True:
            for event in pygame.event.get():
                # terminate application
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

                # press return key to throw ball if on game page
                if game_active:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                        is_throw = True
                        time = 0
                        ball.add(Ball())
                
                # on home page, press space to enter game page
                else:
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        game_active = True
                        
                        # game page initiations
                        start_time = int(pygame.time.get_ticks())
                        power = PowerBar()
        #                cup_group.add(Cup(500))
        #                cup_group.add(Cup(600))
        #                cup_group.add(Cup(700))

        # update game page
        if game_active:
            # game page background
            screen.blit(sky_surface,(0,0))
            screen.blit(ground_surface,(0,300))
            score = display_score()
            
            # game page sprites
            player.draw(screen)
            player.update()
            cup_group.draw(screen)
            
            power.draw(screen)
            
            # if throwing
            if is_throw:
                ball.draw(screen)
                ball.update(power.ret_power(),time)
                time += 0.05
                # if the ball is deleted
                if not ball:
                    is_throw = False
                    power.reset()
            # if not throwing, keep adjusting powerbar
            else:
                power.move_bar()
    #        game_active = collision_sprite()
        
        # on the restart page
        else:
            screen.fill((94,129,162))
            screen.blit(player_stand,player_stand_rect)

            score_message = test_font.render(f'Your score: {score}',False,(111,196,169))
            score_message_rect = score_message.get_rect(center = (400,330))
            screen.blit(game_name,game_name_rect)

            if score == 0: screen.blit(game_message,game_message_rect)
            else: screen.blit(score_message,score_message_rect)

        # update the display and fps
        pygame.display.update()
        clock.tick(60)
        await asyncio.sleep(5)


#if command=='start': 
def choose_level():
    print('Game launching')
    # time.sleep(1)
    print('Choose Game Mode')
    # time.sleep(3)
    detected=False

    
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
                

                    elif key=="blue":
                            cv2.putText(frame, "Game mode: Earth", (100,100), cv2.FONT_HERSHEY_SIMPLEX, 0.6,colors[key],2)
                            mode = 2

                    elif key=="green":
                            cv2.putText(frame, "Game mode: Jupytor", (100,100), cv2.FONT_HERSHEY_SIMPLEX, 0.6,colors[key],2)
                            mode = 3

                    elif key=="purple":
                            cv2.putText(frame, "Game mode: Venus", (100,100), cv2.FONT_HERSHEY_SIMPLEX, 0.6,colors[key],2)
                            mode = 4


        cv2.imshow("Frame", frame)
        
       # if(detected):
       #     time.sleep(5)
       #     break

        key = cv2.waitKey(1) & 0xFF
        # press 'q' to stop the loop
        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    choose_level()
    loop = asyncio.get_event_loop()
    max_x_characteristic = "00001142-0000-1000-8000-00805f9b34fb"
    max_z_characteristic = "00001143-0000-1000-8000-00805f9b34fb"
    connection = Connection(
        loop, max_x_characteristic, max_z_characteristic,)
    try:
        asyncio.ensure_future(connection.play_game())
        asyncio.ensure_future(connection.manager())
        # asyncio.ensure_future(user_console_manager(connection))
        loop.run_forever()
    except KeyboardInterrupt:
        print()
        print("User stopped program.")
    finally:
        print("Disconnecting...")
        loop.run_until_complete(connection.cleanup())
