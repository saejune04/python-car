import math
import pygame
from utils import rotateClockwise2d, translate2d, doIntersect

# Few things to note due to pygame coordinate plane having positive y going downwards:
# - All rotations within this method are CLCKWISE w.r.t theta (rad)
# - Thus the unit circle is also reflected over the 'x-axis'
#   - Rotating by theta CLOCKWISE in this new unit circle is the equivalent of moving theta COUNTERCLOCKWISE in the normal unit circle

class Car:
    def __init__(self, track): # Note: a car is assigned to a track at instantiation
        # Setup
        self.alive = True
        self.immortal = False
        self.autoRespawn = True

        # Positioning
        self.pos = track.startPos[:] # Stores the car's current position
        self.direction = track.startDir # Represents the direction the car faces.
                                        # is the number of radians turned CLOCKWISE from theta=0
        self.hitboxPoints = ((0, 0),(0, 0),(0, 0),(0, 0)) # Represents rectangle ABCD where A is the front left point of the car, points move CLOCKWISE

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
        self._updateHitboxPoints()

        # Just make the car not move after it's moving slowly enough
        if (self.getTotalVel() < 0.1):
            self.vel = [0, 0]
        
        if self._isCrashed():
            self.kill()
        if self._passedCheckpoint():
            self.checkpointsPassed += 1
        if self._finishedLap():
            self.lapsDone += 1
            self.checkpointsPassed = 0
            print('laps done: ', self.lapsDone)

        self._drawCar(surface)

    #================================================================
    # Movement
    def _drive(self):
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

    # When turning, the car's velocity is going in one direction, but is accelerating
    # in a different direction (the direction the tires face). 
    def turn(self, rad):
        # positive rad turns the car left, negative rad turns the car right
        self.direction += math.log(self.getTotalVel() + 1) / 3 * rad

    def accelerate(self, boost):
        self.vel[0] += boost * math.cos(self.direction)
        self.vel[1] += boost * math.sin(self.direction)

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
        self._updateHitboxPoints()
        self.checkpointsPassed = 0

    #================================================================
    # Display
    def _drawCar(self, surface):
        A, B, C, D = self.hitboxPoints

        # Main car frame
        pygame.draw.polygon(surface, 'black', [A, B, C, D])

        # Headlights
        # pygame.draw.ellipse(surface, 'white', pygame.Rect(
        #     self.pos[0] + self.width / 2 * cos - self.height / 2 * sin,
        #     self.pos[1] + self.width / 2 * sin  self.height / 2 * cos,
        #     4,
        #     4
        # ))

    # ALWAYS call right after updating car position, speed, direction, etc for precise collision detection detection
    def _updateHitboxPoints(self):
        # Note: when direction = 0 radians, the car faces "right" (along the positive x direction)
        self.hitboxPoints = (translate2d(self.pos, rotateClockwise2d((self.height / 2, -self.width / 2), self.direction)),
                             translate2d(self.pos, rotateClockwise2d((self.height / 2, self.width / 2), self.direction)),
                             translate2d(self.pos, rotateClockwise2d((-self.height / 2, self.width / 2), self.direction)),
                             translate2d(self.pos, rotateClockwise2d((-self.height / 2, -self.width / 2), self.direction)))

    #================================================================
    # Collision Detection
    def _isCrashed(self):
        A, B, C, D = self.hitboxPoints
        
        for boundary in self.track.trackpoints:
            for i in range(-1, len(boundary) - 1):
                if doIntersect(
                    A, B, boundary[i], boundary[i + 1]
                ) or doIntersect(
                    B, C, boundary[i], boundary[i + 1]
                ) or doIntersect(
                    C, D, boundary[i], boundary[i + 1]
                ) or doIntersect(
                    D, A, boundary[i], boundary[i + 1]
                ):
                    return True       
        return False

    def _passedCheckpoint(self):
        # No need to check for next checkpoint if the player is already passed it (i.e. they only need to cross startline)
        if len(self.track.checkpoints) == self.checkpointsPassed or len(self.track.checkpoints) == 0:
            return False
        
        A, B, C, D = self.hitboxPoints
        if doIntersect(
            A,
            B,
            self.track.checkpoints[self.checkpointsPassed][0], 
            self.track.checkpoints[self.checkpointsPassed][1]
        ) or doIntersect(
            B,
            C,
            self.track.checkpoints[self.checkpointsPassed][0], 
            self.track.checkpoints[self.checkpointsPassed][1]
        ) or doIntersect(
            C,
            D,
            self.track.checkpoints[self.checkpointsPassed][0], 
            self.track.checkpoints[self.checkpointsPassed][1]
        ) or doIntersect(
            D,
            A,
            self.track.checkpoints[self.checkpointsPassed][0], 
            self.track.checkpoints[self.checkpointsPassed][1]
        ):
            return True
        return False

    def _finishedLap(self):
        # No need to check if the next lap is complete if the player hasnt gone through all the checkpoints!
        if self.checkpointsPassed != len(self.track.checkpoints):
            return False
        
        A, B, C, D = self.hitboxPoints
        if doIntersect(
            A, B, self.track.startLine[0], self.track.startLine[1]
        ) or doIntersect(
            B, C, self.track.startLine[0], self.track.startLine[1]
        ) or doIntersect(
            C, D, self.track.startLine[0], self.track.startLine[1]
        ) or doIntersect(
            D, A, self.track.startLine[0], self.track.startLine[1]
        ):
            return True
        return False

    def kill(self):
        if not self.immortal:
            self.reset()
        if not self.autoRespawn:
            self.alive = False

    #================================================================
    # Calculations
    def getTotalVel(self):
        return math.sqrt(self.vel[0]**2 + self.vel[1]**2)
