from Cars.car import Car
from Controllers.controller import Controller
import pygame

# Car controls
ACCELERATION = 1.3
BRAKE = 0.7
TURNING_POWER = 1.5 * 0.08726646

class User_Controller(Controller):
    def __init__(self, track, surface):
        self.track = track
        self.surface = surface
        self.car = Car(track)

    def update(self):
        """Handles user input and updates the user-controllable car"""

        # Get user controls
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            self.car.accelerate(ACCELERATION)
        if keys[pygame.K_s]:
            self.car.accelerate(-BRAKE)
        if keys[pygame.K_a]:
            self.car.turn(-TURNING_POWER)
        if keys[pygame.K_d]:
            self.car.turn(TURNING_POWER)

        self.car.update(self.surface)