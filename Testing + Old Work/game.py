'''
Inputs:
Player 1:
1. Velocity - IMU
2. Angle of release - IMU
3. Starting height voice - (y0 height)
4. Ready - voice - (1,0)
5. Left-Right distance - camera

Player 2:

Set:
table height / height of cups
distance from the cups
width of the cups
'''

'''
def main_game(
    p1_velocity,
    p1_angle,
    p1_height,
    p1_ready,
)
'''

'''
Game State
1. how many cups each player has
2. has game finished yet
3. 
'''

from math import sin, cos, radians
from matplotlib import pyplot as plt
import numpy as np

class Cannon:
    def __init__(self, x0, y0, v, angle):
        """
        x0 and y0 are initial coordinates of the cannon
        v is the initial velocity
        angle is the angle of shooting in degrees
        """
        # current x and y coordinates of the missile
        self.x    = x0
        self.y    = y0
        # current value of velocity components
        self.vx  = v*cos(radians(angle))
        self.vy  = v*sin(radians(angle))

        # acceleration by x and y axes
        self.ax   = 0
        self.ay   = -9.8
        # start time
        self.time = 0

        # these list will contain discrete set of missile coordinates
        self.xarr = [self.x]
        self.yarr = [self.y]

        self.x_intersection = 0
        self.y_intersection = 0

    def updateVx(self, dt):
            self.vx = self.vx + self.ax*dt
            return self.vx
    def updateVy(self, dt):
        self.vy = self.vy + self.ay*dt
        return self.vy

    def updateX(self, dt):
            self.x = self.x + 0.5*(self.vx + self.updateVx(dt))*dt
            return self.x
    def updateY(self, dt):
        self.y = self.y + 0.5*(self.vy + self.updateVy(dt))*dt
        if self.y <= 0.01 and self.y > -0.01:
            self.x_intersection = self.x
            self.y_intersection = self.y
        return self.y

    def step(self, dt):
        self.xarr.append(self.updateX(dt))
        self.yarr.append(self.updateY(dt))
        self.time = self.time + dt


def makeShoot(x0, y0, velocity, angle):
    """
    Returns a tuple with sequential pairs of x and y coordinates
    """
    cannon = Cannon(x0, y0, velocity, angle)
    dt = 0.001 # time step
    t = 0 # initial time
    cannon.step(dt)

    ###### THE  INTEGRATION ######
    while cannon.y >= 0:
        cannon.step(dt)
        t = t + dt
    ##############################

    return (cannon.xarr, cannon.yarr, cannon.x_intersection, cannon.y_intersection)

class Player:
    def __init__(self, velocity, angle, height, ready):
        self.velocity   = velocity
        self.angle      = angle
        self.height     = height
        self.ready      = ready

class Cup:
     def __init__(self, x_location, width):
        self.location   = x_location
        self.width      = width


def print_intersection(self):
    print('intersection point: (' + str(self.x_intersection) + ',' + str(self.y_intersection) + ')')


def start_game(player1, player2):
    p1_x, p1_y, p1_x_intersection, p1_y_intersection = makeShoot(0, player1.height, player1.velocity, player1.angle)
    p2_x, p2_y, p2_x_intersection, p2_y_intersection = makeShoot(25, player2.height, -player2.velocity, -player2.angle)
    cup_2 = Cup(10, 1)
    cup_1 = Cup(15, 1)
        
    
    plt.plot(p1_x, p1_y, 'bo-', p2_x, p2_y, 'go-',
        [0, 25], [0, 0], 'k-' # ground
        )

    plt.vlines(x=[  cup_1.location - cup_1.width/2, 
                    cup_1.location + cup_1.width/2, 
                    cup_2.location - cup_2.width/2,
                    cup_2.location + cup_2.width/2], 
                    ymin=[0,0,0,0],
                    ymax=[0.5, 0.5, 0.5, 0.5], colors='red', ls='--', lw=2, label='cups')
    plt.legend(['Player 1', 'Player 2', 'Table', 'Cups'])
    

    if p1_x_intersection > cup_1.location - cup_1.width/2 or p1_x_intersection < cup_1.location + cup_1.width/2:
        print('Player 1 landed their shot!')
    else:
        print('Player 1 missed their shot!')

    if p2_x_intersection > cup_2.location - cup_2.width/2 or p2_x_intersection < cup_2.location + cup_2.width/2:
        print('Player 2 landed their shot!')
    else:
        print('Player 2 missed their shot!')

    plt.show()

def main():
    
    player1 = Player(12, 30, 1.5, 1)
    player2 = Player(12, 30, 1.5, 1)
    

    '''
    p1_velocity = float(input("Enter Player 1 Velocity: "))
    p1_angle = float(input("Enter Player 1 Angle: "))
    p1_height = float(input("Enter Player 1 Height: "))
    player1 = Player(p1_velocity, p1_angle, p1_height, 1)

    p2_velocity = float(input("Enter Player 2 Velocity: "))
    p2_angle = float(input("Enter Player 2 Angle: "))
    p2_height = float(input("Enter Player 2 Height: "))
    player2 = Player(p2_velocity, p2_angle, p2_height, 1)
    '''

    if player1.ready and player2.ready:
        start_game(player1, player2)

if __name__ == '__main__':
    main()

    '''
    
    # main game loop
while not game_finished:
   
else:
    print("Game finished!")

p1_velocity = 
p1_angle =
p1_height = 
p1_ready = 
main_game()
'''