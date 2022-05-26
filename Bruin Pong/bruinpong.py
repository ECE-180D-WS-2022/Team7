import pygame
import numpy as np
from sys import exit
from random import randint, choice
from math import atan, radians, cos, sin
import cv2
import argparse
import imutils
import random

### MQTT 
import paho.mqtt.client as mqtt
global receieved_msg
receieved_msg = 0

global msg_receieved
msg_receieved = 0
global is_voice
is_voice = 0
skip_first = 0

def on_connect(client, userdata, flags, rc):
  print("Connection returned result: "+str(rc))

  # Subscribing in on_connect() means that if we lose the connection and
  # reconnect then subscriptions will be renewed.
  client.subscribe("ece180d/team7/pygame", qos=1) 

# The callback of the client when it disconnects. 
def on_disconnect(client, userdata, rc): 
  if rc != 0: 
    print('Unexpected Disconnect')
  else:
    print('Expected Disconnect')

def on_message(client, userdata, message): 
  print('Received message: "' + str(message.payload) + '" on topic "' + 
        message.topic + '" with QoS ' + str(message.qos))
  global msg_receieved, receieved_msg, is_voice
  msg_receieved = 1
  message.payload = message.payload.decode("utf-8")
  receieved_msg = message.payload
  if len(receieved_msg) == 1:
      is_voice = 1
  else:
      is_voice = 0

client = mqtt.Client()
# add additional client options (security, certifications, etc.)
# many default options should be good to start off.
# add callbacks to client. 
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

client.connect_async("test.mosquitto.org")
client.loop_start()

### Camera
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the (optional) video file")
ap.add_argument("-b", "--buffer", type=int, default=64, help="max buffer size")
args = vars(ap.parse_args())

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

def cameraOn(level,levelpast):
    if not args.get("video", False):
        camera = cv2.VideoCapture(0)

    else:
        camera = cv2.VideoCapture(args["video"])
        
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
                            mode = 2
                            level = 'Mars'
                            count = count + 1
                            color = (255, 165, 0)
                    elif key=="blue":
                            cv2.putText(frame, "Game mode: Earth", (100,100), cv2.FONT_HERSHEY_SIMPLEX, 0.6,colors[key],2)
                            mode = 5
                            level = 'Earth'
                            count = count + 1
                            color = (0, 255, 255)
                    elif key=="green":
                            cv2.putText(frame, "Game mode: Jupiter", (100,100), cv2.FONT_HERSHEY_SIMPLEX, 0.6,colors[key],2)
                            mode = 10
                            level = 'Jupiter'
                            count = count + 1
                            color = (0, 255, 0)
                    elif key=="purple":
                            cv2.putText(frame, "Game mode: Venus", (100,100), cv2.FONT_HERSHEY_SIMPLEX, 0.6,colors[key],2)
                            mode = 7
                            level = 'Venus'
                            count = count + 1
                            color = (230,230,250)
                    else:
                        mode = 0

        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF
        # press 'q' to stop the loop
        if key == ord("q"):
            break
        if count > 100:
            break

    camera.release()
    cv2.destroyAllWindows()
    if levelpast == level:
        #print("delete this")
        levelpast = "unchanged"
    else:
        #print("delelel")
        levelpast = level
        
    return mode, level, levelpast, color

BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
player_num = 1

# Player Sprite Object
class Player(pygame.sprite.Sprite):
    def __init__(self, player_num):
        super().__init__()
        
        if player_num == 1:
            self.sprites = []
            # animates when is_throw is true
            self.is_animating = False
            self.is_switching = False
            # four images to simulate animation
            self.sprites.append(pygame.image.load('graphics/player/ninja1.png'))
            self.sprites.append(pygame.image.load('graphics/player/ninja2.png'))
            self.sprites.append(pygame.image.load('graphics/player/ninja3.png'))
            self.sprites.append(pygame.image.load('graphics/player/ninja4.png'))
            self.current_sprite = 0
            self.image = self.sprites[self.current_sprite]
            self.image = pygame.transform.scale(self.image, (78, 186))
            self.rect = self.image.get_rect(midbottom = (160,630))
            
        if player_num == 2:
            self.sprites = []
            # animates when is_throw is true
            self.is_animating = False
            self.is_switching = False
            # four images to simulate animation
            self.sprites.append(pygame.image.load('graphics/player/player1.png'))
            self.sprites.append(pygame.image.load('graphics/player/player2.png'))
            self.sprites.append(pygame.image.load('graphics/player/player3.png'))
            self.sprites.append(pygame.image.load('graphics/player/player4.png'))
            self.current_sprite = 0
            self.image = self.sprites[self.current_sprite]
            self.image = pygame.transform.scale(self.image, (78, 186))
            self.rect = self.image.get_rect(midbottom = (100,630))

    def animate(self):
        global msg_receieved
        
        if msg_receieved and self.current_sprite == 0:
            self.is_animating = True
            msg_receieved = 0

    def update(self, switch_flag):
        if is_throw:
            self.animate()
        elif not is_throw and switch_flag:
            self.is_switching = True

        if self.is_switching == True:
            if self.rect.x > 90:
                self.rect.x = 50
            elif self.rect.x < 80:
                self.rect.x = 120
            self.is_switching = False

        # animation code
        if self.is_animating == True:
            self.current_sprite += 0.15
            if self.current_sprite >= len(self.sprites):
                self.current_sprite = 0
                self.is_animating = False
            self.image = self.sprites[int(self.current_sprite)]
            self.image = pygame.transform.scale(self.image, (78, 186))
 
# Cup Sprite Object
class Cup(pygame.sprite.Sprite):
    def __init__(self,x_pos):
        super().__init__()
        
        self.cup = pygame.image.load('graphics/cups/cup.png').convert_alpha()
        self.image = self.cup

        self.rect = self.image.get_rect(midbottom = (x_pos,600))

# Ball Sprite Object
class Ball(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        
        self.image = pygame.image.load('graphics/ball/ball.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (16, 16))
        # [x coord, y coord, x vel, y vel]
        self.prev_state = [0, 0, 0, 0]
        self.state = [0, 0, 0, 0]
        self.radius = 16
        
    def set_pos(self, pos):
        self.state[0:2] = pos
        
    def set_vel(self, vel):
        self.state[2:] = vel
            
    def update(self,power,gravity_value):
        self.prev_state = self.state
        self.state[0] = self.prev_state[0] + 0.05*self.prev_state[2]
        self.state[1] = self.prev_state[1] + 0.05*self.prev_state[3]
        self.state[3] = self.prev_state[3] + gravity_value*0.05

    def draw(self, surface):
        self.rect = self.image.get_rect()
        self.rect.center = (self.state[0], self.state[1])
        surface.blit(self.image, self.rect)

class PowerBar:
    def __init__(self):
        self.power = 0
        self.direction = 1

    def draw(self, screen):
        pygame.draw.rect(screen, BLACK, (750, 70, 300, 50), 1)
        pygame.draw.rect(screen, BLUE, (750, 70, self.power*3, 50), 0)

    def move_bar(self,value):
        if self.power >= value:
            return
        self.power += self.direction
    
    def ret_power(self):
        return self.power
    
    def reset(self):
        self.power = 0
        self.direction = 1

def collision_sprite():
    collision = pygame.sprite.spritecollide(world.ball,cup_group,False)
    
    if collision:
        if world.ball.rect.top < (collision[0].rect.top):
            collision[0].kill()
            is_throw = False
            power.reset()
            if world.ball.state[0]>770 and world.ball.state[0]<830:
                world.rim[0].set_pos([1300,300])
                world.rim[1].set_pos([1300,300])
            elif world.ball.state[0]>829 and world.ball.state[0]<889:
                world.rim[2].set_pos([1300,300])
                world.rim[3].set_pos([1300,300])
            elif world.ball.state[0]>889 and world.ball.state[0]<949:
                world.rim[4].set_pos([1300,300])
                world.rim[5].set_pos([1300,300])
            elif world.ball.state[0]>949 and world.ball.state[0]<1009:
                world.rim[6].set_pos([1300,300])
                world.rim[7].set_pos([1300,300])
            elif world.ball.state[0]>1009 and world.ball.state[0]<1069:
                world.rim[8].set_pos([1300,300])
                world.rim[9].set_pos([1300,300])
            world.ball.set_pos([130, 1000])
            return True
    else:
        return False

def display_score(score, num):
    #current_time = int(pygame.time.get_ticks()) - start_time
    score_surf = test_font.render(f'Score: {score}',False, BLACK)
    if num == 1:
        score_rect = score_surf.get_rect(center = (200,150))
    elif num == 2:
        score_rect = score_surf.get_rect(center = (200,250))
    screen.blit(score_surf,score_rect)
    return True

def display_throw(throw, num):
    throw_surf = test_font.render(f'Throws: {throw}',False,BLACK)
    if num == 1:
        throw_rect = throw_surf.get_rect(center = (400,150))
    elif num == 2:
        throw_rect = throw_surf.get_rect(center = (400,250))
    screen.blit(throw_surf,throw_rect)
    return True


def display_player(num):
    player_surf = player_font.render(f'Player: {num}',False,(64,64,64))
    if num == 1:
        player_rect = player_surf.get_rect(center = (200,100))
    elif num == 2:
        player_rect = player_surf.get_rect(center = (200,200))
    screen.blit(player_surf, player_rect)
    return player

def arrow(num):
    arrow_surf = player_font.render('>',False,WHITE)
    if num == 1:
        arrow_rect = arrow_surf.get_rect(center = (80,95))
    elif num == 2:
        arrow_rect = arrow_surf.get_rect(center = (80,195))
    screen.blit(arrow_surf, arrow_rect)
    return arrow


#what game mode are we in? default is Earth
#Random past level value that makes the game go go go
#default levelpast is unchanged
levelpast = 'unchanged'
level = 'unchanged'

def getRandom():
    if level == "Earth":
        list1 = [1 , 1 , 2 , 2 , 3,  4]
    if level == "Mars":
        list1 = [1, 2, 3, 4]
    if level == "Jupiter":
        list1 = [1, 2, 3, 4]
    if level == "Venus":
        list1 = [1, 2, 3, 4]
    rnd = random.choice(list1)
    return rnd


def getsky(level, levelpast, sky_surface, bg_music):
    rnd = getRandom()
    print("RANDOM SHIIIII" + str(rnd))
    if levelpast == level:
        levelpast = 'unchanged'
    if level == "Earth":
        sky_surface = pygame.image.load('graphics/Levels/Earth/Earth' + str(rnd) + '.png').convert()
        bg_music.stop()
        bg_music = pygame.mixer.Sound('audio/Levels/Earth/Earth' + str(rnd) + '.mp3')
        bg_music.play(loops = -1)
    if level == "Mars":
        sky_surface = pygame.image.load('graphics/Levels/Mars/Mars' + str(rnd) + '.png').convert()
        bg_music.stop()
        bg_music = pygame.mixer.Sound('audio/Levels/Mars/Mars' + str(rnd) + '.mp3')
        bg_music.play(loops = -1)
    if level == "Jupiter":
        sky_surface = pygame.image.load('graphics/Levels/Jupiter/Jupiter' + str(rnd) + '.png').convert()
        bg_music = pygame.mixer.Sound('audio/Levels/Jupiter/Jupiter' + str(rnd) + '.mp3')
        bg_music.play(loops = -1)
    if level == "Venus":
        sky_surface = pygame.image.load('graphics/Levels/Venus/Venus' + str(rnd) + '.png').convert()
        bg_music.stop()
        bg_music = pygame.mixer.Sound('audio/Levels/Venus/Venus' + str(rnd) + '.mp3')
        bg_music.play(loops = -1)
    return level, levelpast, sky_surface


class Rim(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.image.load('graphics/ball/disk-red.png')
        self.radius = 5
        self.image = pygame.transform.scale(self.image, (self.radius * 2, self.radius * 2))
        self.state = [0, 0]

    def set_pos(self, pos):
        self.state[0:2] = pos
        return self

    def draw(self, surface):
        rect = self.image.get_rect()
        rect.center = (self.state[0], self.state[1])
        surface.blit(self.image, rect)
        
#class SideRim(pygame.sprite.Sprite):
#    def __init__(self):
#        pygame.sprite.Sprite.__init__(self)
#
#        self.image = pygame.image.load('graphics/ball/disk-red.png')
#        self.radius = 5
#        self.image = pygame.transform.scale(self.image, (self.radius * 2, self.radius * 12))
#        self.state = [0, 0]
#
#    def set_pos(self, pos):
#        self.state[0:2] = pos
#        return self
#
#    def draw(self, surface):
#        rect = self.image.get_rect()
#        rect.center = (self.state[0], self.state[1])
#        surface.blit(self.image, rect)

class World:
    def __init__(self):
        self.rim = []
        self.collision_sound = pygame.mixer.Sound('audio/pingpong1.mp3')
        self.collision_sound.set_volume(1)

    def add_ball(self):
        ball = Ball()
        self.ball = ball
        return ball
        
    def add_rim(self):
        rim = Rim()
        self.rim.append(rim)
        return rim

#    def add_siderim(self):
#        siderim = SideRim()
#        self.siderim = siderim
#        return siderim
        
    def draw(self, screen):
        self.ball.draw(screen)
        for rim in self.rim:
            rim.draw(screen)
#        self.siderim.draw(screen)
            
    def update(self, power, gravity_value):
        reset = False
        self.check_rim_collision()
        self.ball.update(power,gravity_value)
        # ball is out of bounds -> reset
        if (self.ball.state[0] > 1250 or self.ball.state[1] > 600):
            reset = True
        return reset

    def check_rim_collision(self):
        pos_i = self.ball.state[0:2]
#        if (np.abs(self.ball.state[0]-780) < 5) and (np.abs(self.ball.state[1]-560) < 30) and (self.ball.state[2] > 0):
#            self.ball.state[2] *= -1
#            self.collision_sound.play()
        for j in range(0, len(self.rim)):
            pos_j = np.array(self.rim[j].state[0:2])
            dist_ij = np.sqrt(np.sum((pos_i - pos_j) ** 2))
            radius_j = self.rim[j].radius
            
            # there is a collision between ball and lip of cup
            if (dist_ij <= self.ball.radius + radius_j):
                # make rim centered at (0,0) and normalize ball coordinates
                new_ball_state = pos_i - pos_j
                if (new_ball_state[1] >= new_ball_state[0]) and (new_ball_state[1] < -1*new_ball_state[0]):
                    self.ball.state[2] *= -1
                    self.collision_sound.play()
        return

# start of main code
pygame.init()
screen = pygame.display.set_mode((1200,800))
pygame.display.set_caption('Bruin Pong')
clock = pygame.time.Clock()
test_font = pygame.font.Font('font/Pixeltype.ttf', 50)
player_font = pygame.font.Font('font/Pixeltype.ttf', 70)

def font_size(num):
    return pygame.font.Font('font/Pixeltype.ttf', num)

game_active = False
start_time = 0

playerNum = 0
pygame.mixer.init()
bg_music = pygame.mixer.Sound('audio/poolparty.mp3')
bg_music.play(loops = -1)

#Groups
player = pygame.sprite.GroupSingle()
player.add(Player(1))

player2 = pygame.sprite.GroupSingle()
player2.add(Player(2))

cup_group = pygame.sprite.Group()
world = World()

sky_surface = pygame.image.load('graphics/bruinpong.png').convert()
ground_surface = pygame.image.load('graphics/table.jpeg').convert()

#RULES IMPLEMENTATION
rule_1_stand = pygame.image.load('graphics/Rules/rule_1.png').convert_alpha()
rule_1_stand = pygame.transform.rotozoom(rule_1_stand,0,2)
rule_1_stand_rect = rule_1_stand.get_rect(center = (600,500))

rule_2_stand = pygame.image.load('graphics/Rules/rule_2.png').convert_alpha()
rule_2_stand = pygame.transform.rotozoom(rule_2_stand,0,2)
rule_2_stand_rect = rule_2_stand.get_rect(center = (600,500))

rule_3_stand = pygame.image.load('graphics/Rules/rule_3.png').convert_alpha()
rule_3_stand = pygame.transform.rotozoom(rule_3_stand,0,2)
rule_3_stand_rect = rule_3_stand.get_rect(center = (600,500))

rules = pygame.image.load('graphics/rules.png').convert_alpha()
rules_stand = pygame.transform.rotozoom(rules, 0, 1.5)
rules_stand_rect = rules_stand.get_rect(center = (100, 150))

# Intro screen
player_stand = pygame.image.load('graphics/main_copy.png').convert_alpha()
player_stand = pygame.transform.rotozoom(player_stand,0,2)
player_stand_rect = player_stand.get_rect(center = (600,500))

game_name = font_size(150).render('Bruin Pong',False, BLACK)
game_name_rect = game_name.get_rect(center = (600,200))

game_message = test_font.render('Say "Single" for Single Player',False,BLACK)
game_message_rect = game_message.get_rect(center = (500,330))

game_message2 = test_font.render('Say "Multi" for Multiplayer',False,BLACK)
game_message_rect2 = game_message.get_rect(center = (500,400))

game_message3 = test_font.render('Press "R" for Rules',False,BLACK)
game_message_rect3 = game_message.get_rect(center = (500,470))

# Timer
ball_timer = pygame.USEREVENT + 1
pygame.time.set_timer(ball_timer,1500)

# global variables
is_throw = False
power_value = 0

score = 0
score_num = 0
throw = 0
throw_num = 0
score2 = 0
score_num2 = 0
throw2 = 0
throw_num2 = 0
global arrowNum
arrowNum = 1
#single and multiplayer modes
single_mode_active = False
multiplayer_mode_active = False
rule_active = False

# ADD BELOW constant
rule_pageNum = 1

gravity_value = 4.9
color = (0, 153, 76)
text = 'Earth'
prev_power_value = 0


def start_single():
    # game page initiations
    start_time = int(pygame.time.get_ticks())
    power = PowerBar()
    
    world.add_ball().set_pos([130, 470])
    world.add_rim().set_pos([775, 525])
    world.add_rim().set_pos([825, 525])
    world.add_rim().set_pos([834, 525])
    world.add_rim().set_pos([884, 525])
    world.add_rim().set_pos([894, 525])
    world.add_rim().set_pos([944, 525])
    world.add_rim().set_pos([954, 525])
    world.add_rim().set_pos([1004, 525])
    world.add_rim().set_pos([1014, 525])
    world.add_rim().set_pos([1064, 525])
#                world.add_siderim().set_pos([780, 560])

    cup_group.add(Cup(800))
    cup_group.add(Cup(860))
    cup_group.add(Cup(920))
    cup_group.add(Cup(980))
    cup_group.add(Cup(1040))

def start_multi():
    start_time = int(pygame.time.get_ticks())
    
    world.add_ball().set_pos([130, 470])
    world.add_rim().set_pos([775, 525])
    world.add_rim().set_pos([825, 525])
    world.add_rim().set_pos([834, 525])
    world.add_rim().set_pos([884, 525])
    world.add_rim().set_pos([894, 525])
    world.add_rim().set_pos([944, 525])
    world.add_rim().set_pos([954, 525])
    world.add_rim().set_pos([1004, 525])
    world.add_rim().set_pos([1014, 525])
    world.add_rim().set_pos([1064, 525])
#                world.add_siderim().set_pos([780, 560])

    cup_group.add(Cup(800))
    cup_group.add(Cup(860))
    cup_group.add(Cup(920))
    cup_group.add(Cup(980))
    cup_group.add(Cup(1040))

# infinite loop for pygame, only terminates with exiting application
while True:
    for event in pygame.event.get():
        # terminate application
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        # press return key to throw ball if on game page
        
        if single_mode_active or multiplayer_mode_active:
            # display

            if event.type == pygame.KEYDOWN and event.key == pygame.K_c: 
                gravity_value, level, levelpast, color = cameraOn(level, levelpast)

            elif msg_receieved and is_voice:
                msg_receieved = 0
                voice_command_list = ['start', 'rules', 'single', 'multi', 'planet']
                voice_command = int(receieved_msg)
                if voice_command_list[voice_command ] == 'planet':
                    gravity_value, level, levelpast, color = cameraOn(level, levelpast)

            if msg_receieved and not is_voice:
                # msg_receieved = 0
                if prev_power_value == float(receieved_msg):
                    continue
                else:
                    power_value = float(receieved_msg)
                    prev_power_value = power_value
                angle = 0.9
                vel = (power_value * 25)/1.25+20
                vel_x = vel * cos(angle)
                vel_y = -vel * sin(angle)
                is_throw = True
                world.ball.set_vel([vel_x,vel_y])

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                power_value = power.ret_power()
                angle = 0.9
                vel = power_value/1.25+20
                vel_x = vel * cos(angle)
                vel_y = -vel * sin(angle)
                is_throw = True
                world.ball.set_vel([vel_x,vel_y])

        # on home page, press space to enter game page
        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r: 
                rule_active = True
                rule_pageNum = 1
            if rule_active and event.type == pygame.KEYDOWN and event.key == pygame.K_RIGHT: 
                rule_pageNum += 1
            if rule_active and event.type == pygame.KEYDOWN and event.key == pygame.K_LEFT: 
                rule_pageNum -= 1
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_b:
                score = 0
                rule_active = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_0: 
                score = 0
                score2 = 0
                score_num = 0
                score_num2 = 0 
                throw_num = 0
                throw_num2 = 0
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                single_mode_active = True
                start_single()
                power = PowerBar()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                multiplayer_mode_active = True
                start_multi()
                power = PowerBar()

            if msg_receieved and is_voice:
                rule_active = False
                msg_receieved = 0
                voice_command_list = ['start', 'rules', 'single', 'multi', 'planet']
                voice_command = int(receieved_msg)

                if voice_command_list[voice_command ] == 'single':
                    single_mode_active = True
                    start_single()

                    # game page initiations
                    start_time = int(pygame.time.get_ticks())
                    power = PowerBar()
                    
                    world.add_ball().set_pos([130, 470])
                    world.add_rim().set_pos([775, 525])
                    world.add_rim().set_pos([825, 525])
                    world.add_rim().set_pos([834, 525])
                    world.add_rim().set_pos([884, 525])
                    world.add_rim().set_pos([894, 525])
                    world.add_rim().set_pos([944, 525])
                    world.add_rim().set_pos([954, 525])
                    world.add_rim().set_pos([1004, 525])
                    world.add_rim().set_pos([1014, 525])
                    world.add_rim().set_pos([1064, 525])
    #                world.add_siderim().set_pos([780, 560])

                    cup_group.add(Cup(800))
                    cup_group.add(Cup(860))
                    cup_group.add(Cup(920))
                    cup_group.add(Cup(980))
                    cup_group.add(Cup(1040))

                elif voice_command_list[voice_command ] == 'multi':
                    msg_receieved = 0
                    multiplayer_mode_active = True
                    rule_active = False
                    start_time = int(pygame.time.get_ticks())
                    power = PowerBar()
                    
                    world.add_ball().set_pos([130, 470])
                    world.add_rim().set_pos([775, 525])
                    world.add_rim().set_pos([825, 525])
                    world.add_rim().set_pos([834, 525])
                    world.add_rim().set_pos([884, 525])
                    world.add_rim().set_pos([894, 525])
                    world.add_rim().set_pos([944, 525])
                    world.add_rim().set_pos([954, 525])
                    world.add_rim().set_pos([1004, 525])
                    world.add_rim().set_pos([1014, 525])
                    world.add_rim().set_pos([1064, 525])
    #                world.add_siderim().set_pos([780, 560])

                    cup_group.add(Cup(800))
                    cup_group.add(Cup(860))
                    cup_group.add(Cup(920))
                    cup_group.add(Cup(980))
                    cup_group.add(Cup(1040))
                    
                

    # update game page
    if single_mode_active:
        # game page background
        if levelpast == "unchanged":
            screen.blit(sky_surface,(0,0))
        else:
            #pause background music and get new sky and level data
            bg_music.stop()
            level, levelpast, sky_surface = getsky(level,levelpast, sky_surface, bg_music)

            screen.blit(sky_surface,(0,0))
        screen.blit(ground_surface,(0,600))
        
        # game page sprites
        player.draw(screen)
        player.update(False)
        
        arrow = arrow(1)
        
        power.draw(screen)
        world.draw(screen)
        cup_group.draw(screen)
        
        score = display_score(score_num, 1)
        playerNum = display_player(1)
        throw = display_throw(throw_num, 1)
        
        if gravity_value == 2:
            text = 'Mars'
            color = (255, 128, 0)
        elif gravity_value == 5:
            text = 'Earth'
            color = (0, 153, 76)
        elif gravity_value == 10:
            text = 'Jupytor'
            color = (0, 0, 255)
        elif gravity_value == 7:
            text = 'Venus'
            color = (127, 0, 255)
        
        gravity_surf = font_size(70).render(f'Planet Mode: {text}',False,color)
        gravity_rect = gravity_surf.get_rect(center = (900,150))
        relative_gravity = round(gravity_value/5,1)
        gravity_surf1 = font_size(70).render(f'Gravity Value: {relative_gravity}x Earth',False,color)
        gravity_rect1 = gravity_surf1.get_rect(center = (900,190))
        screen.blit(gravity_surf,gravity_rect)
        screen.blit(gravity_surf1,gravity_rect1)
            
        # if throwing
        if is_throw:
            world.update(power_value,gravity_value)
            power.move_bar((power_value * 25)/1.25+20)
#            if world.ball.state[1]=520 and world.ball.state[0]-800<=20
                
#            for cup in cup_group:
#                collide = world.ball.rect.colliderect(cup.rect)
#                if collide:
#                    cup.kill()
#                    is_throw = False
#                    power.reset()
#                    world.ball.set_pos([130, 470])
            # if the ball is deleted
            if collision_sprite():
                score_num += 1
                
                if len(cup_group) == 0:
                    single_mode_active = False
               
            if world.update(power_value,gravity_value):
                is_throw = False
                throw_num += 1
                power.reset()
                world.ball.set_pos([130, 470])
       
    elif multiplayer_mode_active:
        if levelpast == "unchanged":
            screen.blit(sky_surface,(0,0))
        else:
            #pause background music and get new sky and level data
            bg_music.stop()
            level, levelpast, sky_surface = getsky(level,levelpast, sky_surface, bg_music)
            # game page background
            screen.blit(sky_surface,(0,0))
        screen.blit(ground_surface,(0,600))
        
        # game page sprites
        player.draw(screen)
        if arrowNum == 1:
            player.update(False)
            

        if arrowNum == 2:
            player2.update(False)

        player2.draw(screen)
        power.draw(screen)
        world.draw(screen)
        cup_group.draw(screen)
        
        score = display_score(score_num, 1)
        score2 = display_score(score_num2, 2)
        
        playerNum = display_player(1)
        playerNum2 = display_player(2)
        
        arrow = arrow(arrowNum)
        
        throw = display_throw(throw_num, 1)
        throw2 = display_throw(throw_num2, 2)
        
        if gravity_value == 2:
            text = 'Mars'
            color = (255, 128, 0)
        elif gravity_value == 5:
            text = 'Earth'
            color = (0, 153, 76)
        elif gravity_value == 10:
            text = 'Jupytor'
            color = (0, 0, 255)
        elif gravity_value == 7:
            text = 'Venus'
            color = (127, 0, 255)
        
        gravity_surf = font_size(70).render(f'Planet Mode: {text}',False,color)
        gravity_rect = gravity_surf.get_rect(center = (900,150))
        relative_gravity = round(gravity_value/5,1)
        gravity_surf1 = font_size(70).render(f'Gravity Value: {relative_gravity}x Earth',False,color)
        gravity_rect1 = gravity_surf1.get_rect(center = (900,190))
        screen.blit(gravity_surf,gravity_rect)
        screen.blit(gravity_surf1,gravity_rect1)
        
        # if throwing
        if is_throw:
            power.move_bar((power_value * 25)/1.25+20)
            world.update(power_value,gravity_value)
            
            # if the ball is deleted
            if collision_sprite():
                if arrowNum == 1:
                    score_num += 1
                else:
                    score_num2 += 1
                
            if len(cup_group) == 0:
                multiplayer_mode_active = False

            if world.update(power_value,gravity_value):
                if arrowNum == 1:
                    throw_num += 1
                    arrowNum = 2
                else:
                    throw_num2 += 1
                    arrowNum = 1
                
                is_throw = False
                player2.update(True)
                player.update(True)
                
                power.reset()
                world.ball.set_pos([130, 470])
    elif rule_active is True: 
        if rule_pageNum == 1: 
            screen.blit(rule_1_stand,rule_1_stand_rect)
        if rule_pageNum == 2: 
            screen.blit(rule_2_stand,rule_2_stand_rect)
        if rule_pageNum == 3: 
            screen.blit(rule_3_stand,rule_3_stand_rect)
        
     
    # on the restart page
    elif single_mode_active is False  and multiplayer_mode_active is False:
     
        screen.fill((94,129,162))
        screen.blit(player_stand,player_stand_rect)
        
        if score != 0 and score2 == 0:
      
            score_message = test_font.render(f'Your score:     # of cups made: {score_num}     # of throws: {throw_num}',False,BLACK)
            score_message_rect = score_message.get_rect(center = (450,330))
            screen.blit(game_name,game_name_rect)
            final_message = test_font.render(f'Press 0 to go back to main menu',False,BLACK)
            final_message_rect = score_message.get_rect(center = (450,400))
            
            
            screen.blit(score_message, score_message_rect)
            screen.blit(final_message,final_message_rect)
            
        elif score != 0 and score2 != 0: 
            score_message1 = test_font.render(f'Player 1 score:     # of cups made: {score_num}     # of throws: {throw_num}',False,BLACK)
            score_message_rect1 = score_message1.get_rect(center = (450,330))
            score_message2 = test_font.render(f'Player 2 score:     # of cups made: {score_num2}     # of throws: {throw_num2}',False,BLACK)
            score_message_rect2 = score_message2.get_rect(center = (450,360))
            
            screen.blit(score_message1,score_message_rect1)
            screen.blit(score_message2,score_message_rect2)
            final_message = test_font.render(f'Press 0 to go back to main menu',False,BLACK)
            final_message_rect = score_message1.get_rect(center = (450,430))
            screen.blit(final_message,final_message_rect)
            
        elif score == 0: 
            screen.blit(game_name,game_name_rect)
            screen.blit(game_message,game_message_rect)
            screen.blit(game_message2,game_message_rect2)
            screen.blit(game_message3,game_message_rect3)

    # update the display and fps
    pygame.display.update()
    clock.tick(100)
