import pygame
import numpy as np
from random import randint, choice
from math import atan, radians, cos, sin
from scipy.integrate import ode

BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

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
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.image.load('graphics/ball/ball.png').convert_alpha()
        self.image = pygame.transform.scale(self.image, (16, 16))
        self.state = [0, 0, 0, 0]
        self.prev_state = [0, 0, 0, 0]
        self.mass = 1.0
        self.t = 0
        self.radius = 5
        self.friction = 0
        self.g = 9.8

        self.solver = ode(self.f)
        self.solver.set_integrator("dop853")
        self.solver.set_f_params(self.friction, self.g)
        self.solver.set_initial_value(self.state, self.t)

    def f(self, t, state, arg1, arg2):
        dx = state[2]
        dy = state[3]
        dvx = -state[2] * arg1
        dvy = -arg2 - state[3] * arg1
        dx += dvx
        dy += dvy
        return [dx, dy, dvx, dvy]

    def set_pos(self, pos):
        self.state[0:2] = pos
        self.solver.set_initial_value(self.state, self.t)
        return self

    def set_vel(self, vel):
        self.state[2:] = vel
        self.solver.set_initial_value(self.state, self.t)
        return self

    def update(self, dt):
        self.t += dt
        self.prev_state = self.state[:]
        self.state = self.solver.integrate(self.t)

    def move_by(self, delta):
        self.prev_state = self.state[:]
        self.state[0:2] = np.add(self.state[0:2], delta)
        return self

    def draw(self, surface):
        rect = self.image.get_rect()
        rect.center = (self.state[0], 400-self.state[1])  # Flipping y
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

def display_score():
    current_time = int(pygame.time.get_ticks()) - start_time
    score_surf = test_font.render(f'Score: {current_time}',False,(64,64,64))
    score_rect = score_surf.get_rect(center = (400,50))
    screen.blit(score_surf,score_rect)
    return current_time

class Rim(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)

        self.image = pygame.image.load('graphics/ball/disk-red.png')
        self.radius = 5
        self.image = pygame.transform.scale(self.image, (self.radius * 2, self.radius * 2))
        self.state = [0, 0, 0, 0]

    def set_pos(self, pos):
        self.state[0:2] = pos
        return self

    def draw(self, surface):
        rect = self.image.get_rect()
        rect.center = (self.state[0], 400-self.state[1])  # Flipping y
        surface.blit(self.image, rect)

class World:
    def __init__(self):
        self.ball = Ball().set_pos([100, 150])
        self.rim = []
        self.e = 1.0  # Coefficient of restitution
        self.shot = False
        self.scored = False
        self.shot_from = 30

    def add_rim(self):
        rim = Rim()
        self.rim.append(rim)
        return rim

    def draw(self, screen):
        self.ball.draw(screen)
        for rim in self.rim:
            rim.draw(screen)

    def update(self, dt, power):
        reset = False
        self.check_rim_collision()
        self.ball.update(dt)
        # ball is out of bounds -> reset
        if (
            self.ball.state[0] > 800 + self.ball.radius
            or self.ball.state[1] < 0  - self.ball.radius
        ):
            reset = True
        # ball is in the rim -> scored
        top_of_ball = self.ball.state[1] + self.ball.radius
        if (
            self.ball.state[0] > 460
            and self.ball.state[0] < 540
            and top_of_ball > 215
            and top_of_ball < 225
        ):
            self.scored = True
        return reset
        

    def normalize(self, v):
        return v / np.linalg.norm(v)

    def check_rim_collision(self):
        pos_i = self.ball.state[0:2]
        for j in range(0, len(self.rim)):

            pos_j = np.array(self.rim[j].state[0:2])
            dist_ij = np.sqrt(np.sum((pos_i - pos_j) ** 2))

            radius_j = self.rim[j].radius
            if dist_ij > self.ball.radius + radius_j:
                continue

            self.ball.state = self.ball.prev_state + 0.1

            vel_i = np.array(self.ball.state[2:])
            n_ij = self.normalize(pos_i - pos_j)

            mass_i = self.ball.mass

            J = -(1 + self.e) * np.dot(vel_i, n_ij) / ((1.0 / mass_i + 1.0))

            vel_i_aftercollision = vel_i + n_ij * J / mass_i

            self.ball.set_vel(vel_i_aftercollision)
            return


# initializing pygame
pygame.init()

# top left corner is (0,0)
win_width = 800
win_height = 400
screen = pygame.display.set_mode((win_width, win_height))
pygame.display.set_caption('Bruin Pong')
clock = pygame.time.Clock()
test_font = pygame.font.Font('font/Pixeltype.ttf', 50)

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

#Groups
player = pygame.sprite.GroupSingle()
player.add(Player())
cup_group = pygame.sprite.Group()
world = World()
power = PowerBar()

dt = 0.1
game_active = False
start_time = 0
score = 0

while True:
    for event in pygame.event.get():
        # terminate application
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        # press return key to throw ball if on game page
        if game_active:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                angle = 1.0472
                power_val = power.ret_power()
                vel = power_val/1.25+20
                vel_x = vel * cos(angle)
                vel_y = vel * sin(angle)
                is_throw = True
                world.ball.set_vel([vel_x,vel_y])
        
        # on home page, press space to enter game page
        else:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                game_active = True
                
                # game page initiations
                start_time = int(pygame.time.get_ticks())
                # draw rim line
                pygame.draw.line(screen, RED, [460, 300], [540, 300], 10)
                world.add_rim().set_pos([475, 175])
                world.add_rim().set_pos([525, 175])
                cup_group.add(Cup(500))
                #cup_group.add(Cup(600))
                #cup_group.add(Cup(700))

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
        world.draw(screen)
        
        # if throwing
        if is_throw:
            world.update(dt,power)
            if world.update(dt,power):
                is_throw = False
                power.reset()
                world.ball.set_pos([100, 150])
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
    clock.tick(60)


