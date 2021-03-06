import pygame
import numpy as np
from sys import exit
from random import randint, choice
from math import atan, radians, cos, sin
import cv2
import argparse


ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to the (optional) video file")
ap.add_argument("-b", "--buffer", type=int, default=64, help="max buffer size")
args = vars(ap.parse_args())


def cameraOn():
    if not args.get("video", False):
        camera = cv2.VideoCapture(0)

    else:
        camera = cv2.VideoCapture(args["video"])
        
        
    while True:
        
        (grabbed, frame) = camera.read()
        if args.get("video") and not grabbed:
            break
        cv2.imshow("Frame", frame)
        
      
        key = cv2.waitKey(1) & 0xFF
        # press 'q' to stop the loop
        if key == ord("q"):
            break

    camera.release()
    cv2.destroyAllWindows()

BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
player_num = 2

# Ball size is 16x16

class Player(pygame.sprite.Sprite):
    def __init__(self, player_num):
        super().__init__()
        
        
        if player_num == 1:
            self.player_walk = pygame.image.load('graphics/player/player_walk_1.png').convert_alpha()
            self.image = self.player_walk
            self.rect = self.image.get_rect(midbottom = (80,300))
            self.ID = 1
        if player_num == 2:
            self.player_walk = pygame.image.load('graphics/player/player2.png').convert_alpha()
            self.image = self.player_walk
            self.rect = self.image.get_rect(midbottom = (20,300))
            self.ID = 2
        
        
        self.player_jump = pygame.image.load('graphics/player/jump.png').convert_alpha()

        
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
        self.switch()
        
    def switch(self):
        if self.rect.x > 20:
            self.rect.x = 1
        elif self.rect.x < 5:
            self.rect.x = 60
        
class Cup(pygame.sprite.Sprite):
    def __init__(self,x_pos):
        super().__init__()
        
        self.cup = pygame.image.load('graphics/cups/cup.png').convert_alpha()
        self.image = self.cup

        self.rect = self.image.get_rect(midbottom = (x_pos,300))


class Ball(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        
        self.image = pygame.image.load('graphics/ball/ball.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (16, 16))
        self.prev_state = [0, 0, 0, 0]
        self.state = [0, 0, 0, 0]
        self.radius = 16
        
    def set_pos(self, pos):
        self.state[0:2] = pos
        
    def set_vel(self, vel):
        self.state[2:] = vel
            
    def update(self,power):
        self.prev_state = self.state
        self.state[0] = self.prev_state[0] + 0.05*self.prev_state[2]
        self.state[1] = self.prev_state[1] + 0.05*self.prev_state[3]
        self.state[3] = self.prev_state[3] + 9.8*0.05

    def draw(self, surface):
        rect = self.image.get_rect()
        rect.center = (self.state[0], self.state[1])
        surface.blit(self.image, rect)

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

def display_score(score, num):
    #current_time = int(pygame.time.get_ticks()) - start_time
    score_surf = test_font.render(f'Score: {score}',False,(64,64,64))
    if num == 1:
        score_rect = score_surf.get_rect(center = (200,80))
    elif num == 2:
        score_rect = score_surf.get_rect(center = (200,200))
    screen.blit(score_surf,score_rect)
    return True

def display_throw(throw, num):
    throw_surf = test_font.render(f'throws: {throw}',False,(64,64,64))
    if num == 1: 
        throw_rect = throw_surf.get_rect(center = (400,80))
    elif num == 2: 
        throw_rect = throw_surf.get_rect(center = (400,200))
    screen.blit(throw_surf,throw_rect)
    return True


def display_player(num):
    player_surf = test_font.render(f'Player: {num}',False,(64,64,64))
    if num == 1: 
        player_rect = player_surf.get_rect(center = (100,50))
    elif num == 2: 
        player_rect = player_surf.get_rect(center = (100,150))
    screen.blit(player_surf, player_rect)
    return player


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

class World:
    def __init__(self):
        self.rim = []

    def add_ball(self):
        ball = Ball()
        self.ball = ball
        return ball
        
    def add_rim(self):
        rim = Rim()
        self.rim.append(rim)
        return rim

    def draw(self, screen):
        self.ball.draw(screen)
        for rim in self.rim:
            rim.draw(screen)
            
    def update(self, power):
        reset = False
        self.check_rim_collision()
        self.ball.update(power)
        # ball is out of bounds -> reset
        if (self.ball.state[0] > 850 or self.ball.state[1] > 400):
            reset = True
        return reset

    def check_rim_collision(self):
        pos_i = self.ball.state[0:2]
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
#                if (new_ball_state[1] >= new_ball_state[0]) and (new_ball_state[1] >= -1*new_ball_state[0]):
#                    self.ball.state[3] *= -1
#                if (new_ball_state[1] < new_ball_state[0]) and (new_ball_state[1] >= -1*new_ball_state[0]):
#                    self.ball.state[2] *= -1
#                if (new_ball_state[1] < new_ball_state[0]) and (new_ball_state[1] >= -1*new_ball_state[0]):
#                    self.ball.state[3] *= -1
        return

# start of main code
pygame.init()
screen = pygame.display.set_mode((800,400))
pygame.display.set_caption('Bruin Pong')
clock = pygame.time.Clock()
test_font = pygame.font.Font('font/Pixeltype.ttf', 50)
#game_active = False
single_mode_active = False
multiplayer_mode_active = False
start_time = 0
score = 0
score_num = 0
throw = 0
throw_num = 0
score2 = 0
score_num2 = 0
throw2 = 0
throw_num2 = 0

playerNum = 0


#bg_music = pygame.mixer.Sound('audio/music.wav')
#bg_music.play(loops = -1)

#Groups
player = pygame.sprite.GroupSingle()
player.add(Player(1))

player2 = pygame.sprite.GroupSingle()
player2.add(Player(2))

#player2 = pygame.sprite.GroupSingle()
#player2.add(Player(2))


cup_group = pygame.sprite.Group()
world = World()

sky_surface = pygame.image.load('graphics/Sky.png').convert()
ground_surface = pygame.image.load('graphics/ground.png').convert()

# Intro screen
player_stand = pygame.image.load('graphics/player/player_stand.png').convert_alpha()
player_stand = pygame.transform.rotozoom(player_stand,0,2)
player_stand_rect = player_stand.get_rect(center = (400,200))

game_name = test_font.render('Bruin Pong',False,(111,196,169))
game_name_rect = game_name.get_rect(center = (400,80))

game_message = test_font.render('space: single player, M: multiplayer',False,(111,196,169))
game_message_rect = game_message.get_rect(center = (400,330))

# Timer
ball_timer = pygame.USEREVENT + 1
pygame.time.set_timer(ball_timer,1500)

# global variables
is_throw = False
power_value = 0

# infinite loop for pygame, only terminates with exiting application
while True:
    for event in pygame.event.get():
        # terminate application
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        # press return key to throw ball if on game page
        if single_mode_active or multiplayer_mode_active:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                power_value = power.ret_power()
                angle = 0.785
                vel = power_value/1.25+20
                vel_x = vel * cos(angle)
                vel_y = -vel * sin(angle)
                is_throw = True
                world.ball.set_vel([vel_x,vel_y])
                
            if event.type == pygame.KEYDOWN and event.key == pygame.K_c: 
                print('camera')
                cameraOn()
        
        # on home page, press space to enter game page
        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                single_mode_active = True
                 # game page initiations
                start_time = int(pygame.time.get_ticks())
                power = PowerBar()

                world.add_ball().set_pos([100, 280])
                world.add_rim().set_pos([475, 225])
                world.add_rim().set_pos([525, 225])

                cup_group.add(Cup(500))
                #cup_group.add(Cup(600))
                #cup_group.add(Cup(700))
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                multiplayer_mode_active = True
                
                # game page initiations
                start_time = int(pygame.time.get_ticks())
                power = PowerBar()

                world.add_ball().set_pos([100, 280])
                world.add_rim().set_pos([475, 225])
                world.add_rim().set_pos([525, 225])

                cup_group.add(Cup(500))
                #cup_group.add(Cup(600))
                #cup_group.add(Cup(700))
    # update game page
    # single game mode 
    if single_mode_active:
        # game page background
        screen.blit(sky_surface,(0,0))
        screen.blit(ground_surface,(0,300))
        score = display_score(score_num, 1)
        playerNum = display_player(1)
        throw = display_throw(throw_num, 1)
        
        # game page sprites
        player.draw(screen)
        player.update()
        
        
        cup_group.draw(screen)
        power.draw(screen)
        world.draw(screen)
        
        # if throwing
        if is_throw:
            
            world.update(power_value)
            # if the ball is deleted
            if world.update(power_value):
                throw_num += 1
                is_throw = False
                power.reset()
                world.ball.set_pos([100, 250])
        # if not throwing, keep adjusting powerbar
        else:
            power.move_bar()
    
    elif multiplayer_mode_active: 
        screen.blit(sky_surface,(0,0))
        screen.blit(ground_surface,(0,300))
        playerNum = display_player(1)
        playerNum2 = display_player(2)
        score = display_score(score_num, 1)
        throw = display_throw(throw_num, 1)
        
        score2 = display_score(score_num2, 2)
        throw2 = display_throw(throw_num2, 2)
        
        # game page sprites
        player.draw(screen)
        #player.update()
     
        player2.draw(screen)
        #player2.update()
        
        
        cup_group.draw(screen)
        power.draw(screen)
        world.draw(screen)
        
        # if throwing
        if is_throw:
            world.update(power_value)
            # if the ball is deleted
            if world.update(power_value):
                throw_num += 1
                is_throw = False
                power.reset()
                world.ball.set_pos([100, 250])
                player.update()
                player2.update()
        # if not throwing, keep adjusting powerbar
        else:
            power.move_bar()
            
            
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
    clock.tick(100)