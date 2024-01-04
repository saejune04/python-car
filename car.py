import math
import pygame
import utils

class Car:
    def __init__(self, track):
        # Setup
        self.alive = True
        self.immortal = False
        self.autoRespawn = True

        # Positioning
        self.pos = track.startPos[:] # Stores the car's current position
        self.direction = track.startDir # in radians, note that the pygame surface is rotated 90 deg clockwise from a normal cartesian plane
        
        # Dimensions
        self.width = 15
        self.height = self.width * 2

        # Movement
        self.vel = [0, 0]
        self.friction = 1.1
        self.driftFactor = 0.02

        # Trackers
        self.lapsDone = 0
        self.checkpointsPassed = 0

        # Track that this car is bound to
        self.track = track
    
    # Call this method to update the car every frame
    # Will reset the car if it detects its track is being edited
    def update(self, surface):
        if self.track.editStatus != 0:
            self.reset()
        self._applyFriction()
        self._drive()

        # Just make the car not move after it's moving slowly enough
        if (self.getTotalVel() < 0.1):
            self.vel = [0, 0]
        
        self._checkCrashed()
        self._checkCheckpoint()
        self._checkNextLap()
        self._drawCar(surface)

    #================================================================
    # Movement
    def _drive(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

    # When turning, the car's velocity is going in one direction, but is accelerating
    # in a different direction (the direction the tires face). 
    def turn(self, rad):
        self.direction += math.log(self.getTotalVel() + 1) / 3 * rad

    def accelerate(self, boost):
        self.vel[0] += boost * math.cos(self.direction + math.pi / 2)
        self.vel[1] += boost * math.sin(self.direction + math.pi / 2)

    def _applyFriction(self):
        self.vel[0] /= self.friction
        self.vel[1] /= self.friction

    # TODO - FIX AND RUN IN CAR UPDATE
    # just add some horizontal movement
    def _applyDrift(self, goingRight):
        # Reduce the speed in the direction car is currently moving and then
        # accelerate perpendicular to the car
        if goingRight:
            self.vel[0] = (self.vel[0] * self.driftFactor) + (1 - self.driftFactor) * math.cos(self.direction) * self.getTotalVel()
            self.vel[1] = (self.vel[1] * self.driftFactor) + (1 - self.driftFactor) * math.sin(self.direction) * self.getTotalVel()
        else:
            self.vel[0] = (self.vel[0] * self.driftFactor) - (1 - self.driftFactor) * math.cos(self.direction) * self.getTotalVel()
            self.vel[1] = (self.vel[1] * self.driftFactor) - (1 - self.driftFactor) * math.sin(self.direction) * self.getTotalVel()
        
    # Fully resets the car to it's starting values
    def reset(self):
        self.alive = True
        self.pos = self.track.startPos[:]
        self.direction = self.track.startDir
        self.vel = [0, 0]
        self.checkpointsPassed = 0

    #================================================================
    # Display
    def _drawCar(self, surface):
        cos = math.cos(self.direction)
        sin = math.sin(self.direction)
        
        # Main car frame
        pygame.draw.polygon(surface, 'black', [
            (self.width / 2 * cos - self.height / 2 * sin + self.pos[0], self.width / 2 * sin + self.height / 2 * cos + self.pos[1]),
            (self.width / 2 * cos + self.height / 2 * sin + self.pos[0], self.width / 2 * sin - self.height / 2 * cos + self.pos[1]),
            (-1 * self.width / 2 * cos + self.height / 2 * sin + self.pos[0], -1 * self.width / 2 * sin - self.height / 2 * cos + self.pos[1]),
            (-1 * self.width / 2 * cos - self.height / 2 * sin + self.pos[0], -1 * self.width / 2 * sin + self.height / 2 * cos + self.pos[1])
        ])

        # Headlights
        # pygame.draw.ellipse(surface, 'white', pygame.Rect(
        #     self.pos[0] + self.width / 2 * cos - self.height / 2 * sin,
        #     self.pos[1] + self.width / 2 * sin  self.height / 2 * cos,
        #     4,
        #     4
        # ))

    #================================================================
    # Collision Detection
    
    def _checkCrashed(self):
        cos = math.cos(self.direction)
        sin = math.sin(self.direction)
        
        for boundary in self.track.trackpoints:
            for i in range(-1, len(boundary) - 1):
                if utils.doIntersect(
                    (self.width / 2 * cos - self.height / 2 * sin + self.pos[0], self.width / 2 * sin + self.height / 2 * cos + self.pos[1]),
                    (self.width / 2 * cos + self.height / 2 * sin + self.pos[0], self.width / 2 * sin - self.height / 2 * cos + self.pos[1]),
                    boundary[i], 
                    boundary[i + 1]
                ) or utils.doIntersect(
                    (self.width / 2 * cos + self.height / 2 * sin + self.pos[0], self.width / 2 * sin - self.height / 2 * cos + self.pos[1]),
                    (-1 * self.width / 2 * cos + self.height / 2 * sin + self.pos[0], -1 * self.width / 2 * sin - self.height / 2 * cos + self.pos[1]),
                    boundary[i], 
                    boundary[i + 1]
                ) or utils.doIntersect(
                    (-1 * self.width / 2 * cos + self.height / 2 * sin + self.pos[0], -1 * self.width / 2 * sin - self.height / 2 * cos + self.pos[1]), 
                    (-1 * self.width / 2 * cos - self.height / 2 * sin + self.pos[0], -1 * self.width / 2 * sin + self.height / 2 * cos + self.pos[1]),
                    boundary[i], 
                    boundary[i + 1]
                ) or utils.doIntersect(
                    (-1 * self.width / 2 * cos - self.height / 2 * sin + self.pos[0], -1 * self.width / 2 * sin + self.height / 2 * cos + self.pos[1]),
                    (self.width / 2 * cos - self.height / 2 * sin + self.pos[0], self.width / 2 * sin + self.height / 2 * cos + self.pos[1]),
                    boundary[i], 
                    boundary[i + 1]
                ):
                    self.kill()

    def _checkCheckpoint(self):
        # No need to check for next checkpoint if the player is already passed it
        if len(self.track.checkpoints) == self.checkpointsPassed:
            return
        
        cos = math.cos(self.direction)
        sin = math.sin(self.direction)

        if utils.doIntersect(
            (self.width / 2 * cos - self.height / 2 * sin + self.pos[0], self.width / 2 * sin + self.height / 2 * cos + self.pos[1]),
            (self.width / 2 * cos + self.height / 2 * sin + self.pos[0], self.width / 2 * sin - self.height / 2 * cos + self.pos[1]),
            self.track.checkpoints[self.checkpointsPassed][0], 
            self.track.checkpoints[self.checkpointsPassed][1]
        ) or utils.doIntersect(
            (self.width / 2 * cos + self.height / 2 * sin + self.pos[0], self.width / 2 * sin - self.height / 2 * cos + self.pos[1]),
            (-1 * self.width / 2 * cos + self.height / 2 * sin + self.pos[0], -1 * self.width / 2 * sin - self.height / 2 * cos + self.pos[1]),
            self.track.checkpoints[self.checkpointsPassed][0], 
            self.track.checkpoints[self.checkpointsPassed][1]
        ) or utils.doIntersect(
            (-1 * self.width / 2 * cos + self.height / 2 * sin + self.pos[0], -1 * self.width / 2 * sin - self.height / 2 * cos + self.pos[1]), 
            (-1 * self.width / 2 * cos - self.height / 2 * sin + self.pos[0], -1 * self.width / 2 * sin + self.height / 2 * cos + self.pos[1]),
            self.track.checkpoints[self.checkpointsPassed][0], 
            self.track.checkpoints[self.checkpointsPassed][1]
        ) or utils.doIntersect(
            (-1 * self.width / 2 * cos - self.height / 2 * sin + self.pos[0], -1 * self.width / 2 * sin + self.height / 2 * cos + self.pos[1]),
            (self.width / 2 * cos - self.height / 2 * sin + self.pos[0], self.width / 2 * sin + self.height / 2 * cos + self.pos[1]),
            self.track.checkpoints[self.checkpointsPassed][0], 
            self.track.checkpoints[self.checkpointsPassed][1]
        ):
            self.checkpointsPassed += 1

    def _checkNextLap(self):
        # No need to check if the next lap is complete if the player hasnt gone through all the checkpoints!
        if self.checkpointsPassed != len(self.track.checkpoints):
            return
        cos = math.cos(self.direction)
        sin = math.sin(self.direction)
        if utils.doIntersect(
            (self.width / 2 * cos - self.height / 2 * sin + self.pos[0], self.width / 2 * sin + self.height / 2 * cos + self.pos[1]),
            (self.width / 2 * cos + self.height / 2 * sin + self.pos[0], self.width / 2 * sin - self.height / 2 * cos + self.pos[1]),
            self.track.startLine[0], 
            self.track.startLine[1]
        ) or utils.doIntersect(
            (self.width / 2 * cos + self.height / 2 * sin + self.pos[0], self.width / 2 * sin - self.height / 2 * cos + self.pos[1]),
            (-1 * self.width / 2 * cos + self.height / 2 * sin + self.pos[0], -1 * self.width / 2 * sin - self.height / 2 * cos + self.pos[1]),
            self.track.startLine[0], 
            self.track.startLine[1]
        ) or utils.doIntersect(
            (-1 * self.width / 2 * cos + self.height / 2 * sin + self.pos[0], -1 * self.width / 2 * sin - self.height / 2 * cos + self.pos[1]), 
            (-1 * self.width / 2 * cos - self.height / 2 * sin + self.pos[0], -1 * self.width / 2 * sin + self.height / 2 * cos + self.pos[1]),
            self.track.startLine[0], 
            self.track.startLine[1]
        ) or utils.doIntersect(
            (-1 * self.width / 2 * cos - self.height / 2 * sin + self.pos[0], -1 * self.width / 2 * sin + self.height / 2 * cos + self.pos[1]),
            (self.width / 2 * cos - self.height / 2 * sin + self.pos[0], self.width / 2 * sin + self.height / 2 * cos + self.pos[1]),
            self.track.startLine[0], 
            self.track.startLine[1]
        ):
            self.lapsDone += 1
            self.checkpointsPassed = 0
            print('laps done: ', self.lapsDone)

    def kill(self):
        if not self.immortal:
            self.reset()
        if not self.autoRespawn:
            self.alive = False

    #================================================================
    # Calculations
    def getTotalVel(self):
        return math.sqrt(self.vel[0]**2 + self.vel[1]**2)
