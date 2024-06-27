import math
import pygame
import numpy as np
import torch
from Cars import car
from nn import NeuralNetwork
import random
from utils import (rotateClockwise2d, 
                   translate2d, 
                   doIntersect, 
                   findIntersectionPoint)

# Score parameters
CHECKPOINT_REWARD = 20
REWARD_DECAY = -0.1
PURGE_FRAME_THRESHOLD = 100 # number of frames a car has to get a reward before being killed off
FORWARD_REWARD = 0.2
TURN_REWARD = 0
BACKWARDS_REWARD = -0.3
CRASH_REWARD = -50 # Punishment given when car crashes

# Car controls
ACCELERATION = 1.3
BRAKE = 0.7
TURNING_POWER = 1.5 * 0.08726646

class AICar(car.Car):
    def __init__(self, track):
        """
        Args:
            track: The track that this AICar will drive and be evaluated on
        """
        super().__init__(track)
        
        # Setup
        self.alive = True
        self.immortal = False
        self.autoRespawn = False

        # Sensor parameters
        self.drawSensors = False
        self.simpleSensors = False # When true, only uses front facing sensors
        self.sensorRange = 800 # Max distance each sensor can detect something
        self.sensors = [] # Array of all sensors: a sensor is represented by 2 points making a line
                          # (p1, p2) where p1 is the position on the car and p2 is the end of the sensor

        # Hardcoded parameters so controller can make brain NN template
        self.numSensors = 7 if self.simpleSensors else 11 # Change this based on the number of sensors we have
                                                          # hardcoded for now, see self._updateSensors() to see all sensors
        self.numActions = 9 # Also hardcoded, see self.act() to see all possible actions

        # AI Stuff!            
        self.score = 0
        self.framesSinceLastReward = 0


    # Call this method to update the car every frame
    # Will reset the car if it detects its track is being edited

    # NEW TO AICar: Need to give the car an action, first call initializes a lotta stuff but doesnt move the car
    # if no action is given
    def update(self, surface, action=-1, epsilon=0):
        if not self.alive:
            return
    
        self.act(action=action, epsilon=epsilon)
        
        self.framesSinceLastReward += 1
        if self.framesSinceLastReward >= PURGE_FRAME_THRESHOLD:
            self.kill()
            return
 
        if self.track.editStatus != 0:
            self.reset()

        self._applyFriction()
        self._drive()
        self._updateHitboxPoints()

        # Just make the car not move after it's moving slowly enough
        if (self.getSpeed() < 0.1):
            self.vel = [0, 0]

        self.score += REWARD_DECAY # If car doesnt make progress it loses points

        if self._isCrashed():
            self.kill()
            return
        
        if self._passedCheckpoint():
            self.checkpointsPassed += 1
            self.score += CHECKPOINT_REWARD
            self.framesSinceLastReward = 0
        if self._finishedLap():
            self.lapsDone += 1
            self.checkpointsPassed = 0
            self.score += CHECKPOINT_REWARD       
            self.framesSinceLastReward = 0     

        self._updateSensors()
        if self.drawSensors:
            self._drawSensors(surface)

        self._drawCar(surface)


    #============================================================================
    # AI Stuff
    def getState(self):
        """Returns the current state of the car"""
        # Sensor distance + current speed
        sensor_data = self.getSensorData() 
        state = sensor_data + [self.getSpeed()]
        return state

    def act(self, action=-1, epsilon=0):
        """Car takes a given action with probability (1 - epsilon)

        Given action should range between 0 and self.numActions inclusive.
        Takes a random action with probability epsilon.
        
        Params:
            action: a number between 0 and self.numActions inclusive telling the car what action to take
            epsilon: probability of which to take a random action
        Returns:
            action: the action that was actually taken
        """

        if action == -1:
            return -1
        rand = random.random()

        if rand < epsilon:
            action = random.randint(0, 8)
        
        if action == 0: # W
            self.accelerate(ACCELERATION)
            self.score += FORWARD_REWARD
        elif action == 1: # A
            self.turn(-TURNING_POWER)
            self.score += TURN_REWARD
        elif action == 2: # S
            self.accelerate(-BRAKE)
            self.score += BACKWARDS_REWARD
        elif action == 3: # D
            self.turn(TURNING_POWER)
            self.score += TURN_REWARD
        elif action == 4: # W + A
            self.accelerate(ACCELERATION)
            self.turn(-TURNING_POWER)
            self.score += FORWARD_REWARD + TURN_REWARD
        elif action == 5: # W + D
            self.accelerate(ACCELERATION)
            self.turn(TURNING_POWER)
            self.score += FORWARD_REWARD + TURN_REWARD
        elif action == 6: # W + S
            self.accelerate(ACCELERATION - BRAKE)
            self.score += FORWARD_REWARD + BACKWARDS_REWARD
        elif action == 7: # W + S + A
            self.accelerate(ACCELERATION - BRAKE)
            self.turn(-TURNING_POWER)
            self.score += FORWARD_REWARD + BACKWARDS_REWARD + TURN_REWARD
        elif action == 8: # W + S + D
            self.accelerate(ACCELERATION - BRAKE)
            self.turn(TURNING_POWER)
            self.score += FORWARD_REWARD + BACKWARDS_REWARD + TURN_REWARD
        return action


    #============================================================================
    # Sensors
    def _updateSensors(self):
        # Define all sensors. A sensor is defined by a line segment (p1, p2) = ((p1x, p1y), (p2x, p2y))
        # where p1 is a point originating on the car

        # These sensors mimic the viewpoints of a human driver in the front-center of the car!
        A, B, C, D = self.hitboxPoints
        x, y = self.pos

        front_middle = ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2) # Midpoint of front bumper

        # Sensor data
        base_sensor = (self.sensorRange, 0)
        self.sensors = []

        # Init data in form (start of sensor, direction of sensor relative to car)
        sensor_init_data = [(front_middle, -math.pi/5), 
                            (front_middle, -math.pi/3),
                            (front_middle, -math.pi/2), 
                            (front_middle, 0),
                            (front_middle, math.pi/2),
                            (front_middle, -math.pi/3),
                            (front_middle, math.pi/5)]
        
        # Rearview and sideview mirrors that require a bit more computation
        if not self.simpleSensors:
            # Higher ratio r2 / r1 => rearview mirror and sideview mirrors closer to front
            r1 = 2
            r2 = 3
            rearview_mirror = ((r2 * front_middle[0] + r1 * x) / (r2 + r1),
                            (r2 * front_middle[1] + r1 * y) / (r2 + r1))
            right_sideview_mirror = ((r1 * C[0] + ((r2 + r1) * 2 - r1) * B[0]) / ((r2 + r1) * 2),
                                    (r1 * C[1] + ((r2 + r1) * 2 - r1) * B[1]) / ((r2 + r1) * 2))
            left_sideview_mirror = ((r1 * D[0] + ((r2 + r1) * 2 - r1) * A[0]) / ((r2 + r1) * 2),
                                (r1 * D[1] + ((r2 + r1) * 2 - r1) * A[1]) / ((r2 + r1) * 2))

            sensor_init_data += [(rearview_mirror, 13*math.pi/12),
                                 (rearview_mirror, 11*math.pi/12),
                                 (right_sideview_mirror, 5*math.pi/6),
                                 (left_sideview_mirror, 7*math.pi/6)]

        # Rotations are relative to the direction the car is facing
        for data in sensor_init_data:
            start_point, rot = data
            self.sensors.append((start_point, translate2d(start_point, rotateClockwise2d(base_sensor, self.direction + rot))))

    def getSensorData(self):
        distances = []
        for sensor in self.sensors:
            distance, _ = self._findMinDistanceSensorIntersection(sensor)
            distances.append(distance)
        return distances

    def _drawSensors(self, surface):
        """Draws the sensors and what they're reading
        
        NOTE: current implementation has redundant calculation call
        TODO: modularize the method call to calculate sensor readings
        """
        for sensor in self.sensors:
            _, intersection = self._findMinDistanceSensorIntersection(sensor)
            pygame.draw.line(surface, 'blue', sensor[0], intersection)
            pygame.draw.circle(surface, 'red', intersection, 5)
    
    def _findMinDistanceSensorIntersection(self, sensor):
        """Finds closest point on the car's track to the car along the given line

        Args:
            sensor: a tuple representing the line extending from the car. ((p1x, p1y), (p2x, p2y))
                (p1x, p1y) is the point originating at the car

        Returns:
            (distance, (ix, iy)) where distance is min(length of line, closest point on track to the car)
                and (ix, iy) is the point of intersection on the track of the closest point to the car
                or (p2x, p2y) if there is no such intersection
        """
        p1, p2 = sensor
        # By default, sensor 'detects' the furthest possible point from the car using given line segment
        min_distance = math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
        best_intersection = p2

        for boundary in self.track.trackpoints:
            for i in range(-1, len(boundary) - 1):
                if doIntersect(
                    p1,
                    p2,
                    boundary[i], 
                    boundary[i + 1]
                ):
                    intersection = findIntersectionPoint(p1, p2, boundary[i], boundary[i + 1])
                    distance = math.sqrt((p1[0] - intersection[0])**2 + (p1[1] - intersection[1])**2)
                    if distance < min_distance:
                        min_distance = distance
                        best_intersection = intersection

        return (min_distance, best_intersection)
    
    def kill(self):
        if not self.autoRespawn:
            self.alive = False
        self.score += CRASH_REWARD

    def reset(self):
        super().reset()
        self.framesSinceLastReward = 0
        self.score = 0

