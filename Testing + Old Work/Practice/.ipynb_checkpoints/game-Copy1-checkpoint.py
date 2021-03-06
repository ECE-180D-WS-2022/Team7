# have player on bottom left of screen, player has stand and throw motion
# have have snails as cups on the bottom right and stationary
# implement a ball to be thrown from midright of person rect
# implement collision between ball and cup/ground


import pygame
from sys import exit
from random import randint, choice
from math import atan, radians, cos, sin

import paho.mqtt.client as mqtt
global receieved_msg
receieved_msg = 0

global msg_receieved
msg_receieved = 0

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
    global msg_receieved, receieved_msg
    msg_receieved = 1
    message.payload = message.payload.decode("utf-8")
    receieved_msg = message.payload

client = mqtt.Client()
# add additional client options (security, certifications, etc.)
# many default options should be good to start off.
# add callbacks to client. 
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

client.connect_async("test.mosquitto.org")
client.loop_start()


BLACK = (0, 0, 0)
BLUE = (0, 0, 255)


# Ball size is 16x16

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
        
        self.cup = pygame.image.load('graphics/cups/cup.png').convert_alpha()
        self.image = self.cup

        self.rect = self.image.get_rect(midbottom = (x_pos,300))


class Ball(pygame.sprite.Sprite):
    def __init__(self, velocity, mode):
        super().__init__()
        
        ball = pygame.image.load('graphics/ball/ball.png').convert_alpha()
        self.image = ball
        self.rect = self.image.get_rect(midbottom = (100,250))
        self.mode = mode
        self.x_velocity = velocity

    def ball_path(self,power,time):
        angle = 0.785
        vel = (self.x_velocity * 25 )/1.25+20
        vel_x = vel * cos(angle)
        vel_y = vel * sin(angle)
        dist_x = vel_x * time
        
        if self.mode == 1: 
            gravity = -4
        elif self.mode == 2:
            gravity = -9.8
        elif self.mode == 3: 
            gravity = -20
        elif self.mode == 4:
            gravity = -8
        
        dist_y = (vel_y * time) + ((gravity * (time)**2)/2)
        
        
        self.rect.midbottom = (round(dist_x + 100),round(-1*dist_y + 250))

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

def display_score(score):
    #current_time = int(pygame.time.get_ticks()) - start_time
    score_surf = test_font.render(f'Score: {score}',False,(64,64,64))
    score_rect = score_surf.get_rect(center = (200,80))
    screen.blit(score_surf,score_rect)
    return True

def display_throw(throw):
    throw_surf = test_font.render(f'throws: {throw}',False,(64,64,64))
    throw_rect = throw_surf.get_rect(center = (400,80))
    screen.blit(throw_surf,throw_rect)
    return True

def collision_sprite():
    collision = pygame.sprite.spritecollide(ball.sprite,cup_group,False)
    
    if collision:
        if ball.sprite.rect.top < (collision[0].rect.top)+5:
            print(ball.sprite.rect.bottom)
            print(collision[0].rect.top)
            collision[0].kill()
            ball.sprite.kill() 
            return True
    else:
        return False
    


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
score_num = 0
score = 0
throw = 0
throw_num = 0
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


# infinite loop for pygame, only terminates with exiting application
while True:
    for event in pygame.event.get():
        # terminate application
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        # press return key to throw ball if on game page
        if game_active:
            # if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            if msg_receieved:
                is_throw = True
                time = 0
                ball.add(Ball(float(receieved_msg), 2))
                msg_receieved = 0
                throw_num +=1
        
        # on home page, press space to enter game page
        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                game_active = True
                
                # game page initiations
                start_time = int(pygame.time.get_ticks())
                power = PowerBar()
                
                cup_group.add(Cup(440))
                cup_group.add(Cup(500))
                cup_group.add(Cup(560))
                cup_group.add(Cup(620))
                cup_group.add(Cup(680))

    # update game page
    if game_active:
        # game page background
        screen.blit(sky_surface,(0,0))
        screen.blit(ground_surface,(0,300))
        score = display_score(score_num)
        throw = display_throw(throw_num)
        
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
            
            if not ball:
                is_throw = False
                power.reset()
          
            if ball and collision_sprite(): 
                score_num += 1
                #throw_num += 1
        
            # if the ball is deleted
           
        # if not throwing, keep adjusting powerbar
        else:
            power.move_bar()
        if not cup_group.sprites():
            screen.fill((94,129,162))
            screen.blit(player_stand,player_stand_rect)

            score_message = test_font.render(f'Your score: {score_num} / {throw_num}',False,(111,196,169))
            score_message_rect = score_message.get_rect(center = (400,330))
            finish_name = test_font.render('Game Over',False,(111,196,169))
            screen.blit(finish_name,game_name_rect)

            if score == 0: screen.blit(game_message,game_message_rect)
            else: screen.blit(score_message,score_message_rect)
            
#        game_active = collision_sprite()
     
    # on the restart page
    else:
        screen.fill((94,129,162))
        screen.blit(player_stand,player_stand_rect)

        score_message = test_font.render(f'Your score: {score_num}',False,(111,196,169))
        score_message_rect = score_message.get_rect(center = (400,330))
        screen.blit(game_name,game_name_rect)

        if score == 0: screen.blit(game_message,game_message_rect)
        else: screen.blit(score_message,score_message_rect)

    # update the display and fps
    pygame.display.update()
    clock.tick(60)
