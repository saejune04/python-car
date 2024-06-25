import json
import math
import pygame

class Track:

    # TEMPORARY LOWER LIMIT OF WHERE TRACK CAN BE DRAWN
    # This is so clicking buttons does not trigger a draw event as buttons atm are at the bottom of the screen
    LOWER_LIMIT = 940

    DEFAULT_CAR_START_POS = [20, 20]
    DEFAULT_CAR_START_DIR = math.pi

    def __init__(self):
        # Track Data
        self.trackpoints = [] # array of arrays of points, each array represents a border (so most likely 2 arrays for 2 borders, inner an outer)
        self.startLine = [(0, 0), (0, 0)] # array of 2 points
        self.checkpoints = [] # array of arrays of 2 points
        self.startPos = Track.DEFAULT_CAR_START_POS # 1 point
        self.startDir = Track.DEFAULT_CAR_START_DIR # starting orientation of car in radians

        # Edit track variables
        self.editStatus = 0 # 0 means not editing a point (ready to edit), 1 means editing first point, 2 means editing 2nd point, and so on
                            # Makes sure that each edit function can only be activated once the previous one is completed
        self.clicked = True
        self.clickReady = True
        self.isEditingCheckpoint = False
        self.isEditingStartLine = False
        self.isEditingBoundary = False
        self.isEditingStartPos = False
        self.isEditingStartDir = False

        # Show track details
        self.showCheckpoints = True

        # Keeps track of most recently added track feature for UNDO
        # 0 is start line, 1 is checkpoint, 2 + i is boundary array with index i (e.g. 3 on stack means the boundary with index 1)
        self.editStack = []

    #============================================================================
    # Track save and load
        
    # Requires a properly formatted JSON file (i.e. one created by the save function)
    def load(self, saveJSON):
        self.reset()
        save = json.loads(saveJSON)
        self.startPos = save["startPos"]
        self.startDir = save["startDir"]
        self.trackpoints = save["trackpoints"]
        self.checkpoints = save["checkpoints"]
        self.startLine = save["startLine"]

        # Tuple-fy the data 'points' (supposed to make it slightly more efficient)
        for track in self.trackpoints:
            for i in range(len(track)):
                track[i] = tuple(track[i])

        for checkpoint in self.checkpoints:
            for i in range(len(checkpoint)):
                checkpoint[i] = tuple(checkpoint[i])

        # self.startPos = tuple(self.startPos)

        for i in range(len(self.startLine)):
            self.startLine[i] = tuple(self.startLine[i])


    # Saves the track as JSON in the following format:
    # "startPos": (x, y) // 1 point
    # "startDir": number
    # "trackpoints": [[(x, y), (x, y)...], [(x, y), (x, y)...]] // Array of arrays of points
    # "checkpoints": [[(x, y), (x, y)], [(x, y), (x, y)]...] // Array of arrays of 2 points
    # "startLine": [(x, y), (x, y)] // Array of 2 points
    def save(self):
        if not self.editStatus == 0:
            print("Finish editing before saving")
            return

        saveFile = json.dumps({
            "startPos": self.startPos,
            "startDir": self.startDir,
            "trackpoints": self.trackpoints,
            "checkpoints": self.checkpoints,
            "startLine": self.startLine
        })

        print(saveFile)

    #============================================================================
    # Display and updates
    def render(self, surface):
        self._updateClickStatus()
        self._handleEdits()
        self._displayStartLine(surface)
        if self.showCheckpoints:
            self._displayCheckpoints(surface)
        self._displayTrack(surface)

    def _displayStartLine(self, surface):
        pygame.draw.line(surface, 'green', self.startLine[0], self.startLine[1])

    def _displayCheckpoints(self, surface):
        for checkpoint in self.checkpoints:
            pygame.draw.line(surface, 'white', checkpoint[0], checkpoint[1])

    def _displayTrack(self, surface):
        for boundary in self.trackpoints: # boundary is an array of points
            if len(boundary) == 2:
                pygame.draw.line(surface, 'black', boundary[0], boundary[1])
            elif len(boundary) > 2:
                pygame.draw.lines(surface, 'black', True, boundary)
            else:
                for point in boundary:
                    pygame.draw.circle(surface, 'black', point, 1)

    # Will set self.clicked to True the frame it detects a new click, will set it to false the frame after         
    def _updateClickStatus(self):
        if self.clicked:
            self.clicked = False
        if pygame.mouse.get_pressed()[0] and self.clickReady and pygame.mouse.get_pos()[1] < Track.LOWER_LIMIT:
            self.clicked = True
            self.clickReady = False
        elif not pygame.mouse.get_pressed()[0]:
            self.clickReady = True

    #============================================================================
    # Edit track
    
    # Handles all editing logic, call in render loop
    def _handleEdits(self):
        if self.isEditingStartLine:
            self.editStartLine()
        if self.isEditingCheckpoint:
            self.addCheckpoint()
        if self.isEditingBoundary:
            self.addBoundary()
        if self.isEditingStartPos:
            self.editStartPos()
    
    # Call once to init startline editing, continue to call so long as isEditingStartLine is true
    def editStartLine(self):
        # If not already editing start line, signify that we are now editing it
        if not(self.isEditingStartLine) and self.editStatus == 0:
            self.editStatus = 1
            self.isEditingStartLine = True
        elif self.isEditingStartLine:
            # Temporary sets start line position to the mouse cursor
            if self.editStatus == 1:
                self.startLine[0] = [i for i in pygame.mouse.get_pos()]
            self.startLine[1] = [i for i in pygame.mouse.get_pos()]

            # Handles adding 1st point then 2nd point
            if self.clicked and self.editStatus == 1:
                self.startLine[0] = [i for i in pygame.mouse.get_pos()]
                self.editStatus = 2
            elif self.clicked and self.editStatus == 2:
                self.startLine[1] = [i for i in pygame.mouse.get_pos()]
                self.editStatus = 0
                self.isEditingStartLine = False
                self.editStack.append(0)

    def clearStartLine(self):
        if self.isEditingStartLine:
            self.editStatus = 0
            self.isEditingStartLine = False
        self.startLine = [[0, 0], [0, 0]]

    # Call once to init checkpoint addition, continue to call so long as isEditingCheckpoint is true
    def addCheckpoint(self):
        # If not already adding a checkpoint, signify that we are now editing it
        if not(self.isEditingCheckpoint) and self.editStatus == 0:
            self.editStatus = 1
            self.isEditingCheckpoint = True

            # Adds new checkpoint at mouse position temporarily
            self.checkpoints.append([[i for i in pygame.mouse.get_pos()],[i for i in pygame.mouse.get_pos()]])
        elif self.isEditingCheckpoint:
            # Temporary sets the position of the new checkpoint to mouse position
            if self.editStatus == 1:
                self.checkpoints[-1][0] = [i for i in pygame.mouse.get_pos()]
            self.checkpoints[-1][1] = [i for i in pygame.mouse.get_pos()]

            # Handles setting the new checkpoint's 1st point then 2nd point
            if self.clicked and self.editStatus == 1:
                self.checkpoints[-1][0] = [i for i in pygame.mouse.get_pos()]
                self.editStatus = 2
            elif self.clicked and self.editStatus == 2:
                self.checkpoints[-1][1] = [i for i in pygame.mouse.get_pos()]
                self.editStatus = 0
                self.isEditingCheckpoint = False
                self.editStack.append(1)

    def clearCheckpoints(self):
        if self.isEditingCheckpoint:
            self.editStatus = 0
            self.isEditingCheckpoint = False
        self.checkpoints = []

    # Call once to init the creation of a new boundary, continue to call so long as isEditingBoundary is true
    def addBoundary(self):
        if not(self.isEditingBoundary) and self.editStatus == 0:
            self.editStatus = 1
            self.isEditingBoundary = True

            # Add a new empty boundary
            self.trackpoints.append([[i for i in pygame.mouse.get_pos()]])

        elif self.isEditingBoundary:
            # Sets next point on the boundary to current mouse position
            self.trackpoints[-1][-1] = [i for i in pygame.mouse.get_pos()]

            # On click, adds a new point to the boundary and preps the next point
            if self.clicked:
                self.trackpoints[-1][-1] = [i for i in pygame.mouse.get_pos()]
                self.trackpoints[-1].append([i for i in pygame.mouse.get_pos()])
                self.editStack.append(1 + len(self.trackpoints))

    # Call once currently drawing boundary is done
    def finalizeBoundary(self):
        # Remove the most recent 'prepped point' from the boundary
        self.trackpoints[-1].pop()

        # Remove the newly drawn 'boundary' if it's empty
        if len(self.trackpoints[-1]) == 0:
            self.trackpoints.pop()
        self.isEditingBoundary = False
        self.editStatus = 0

    def clearBoundaries(self):
        if self.isEditingBoundary:
            self.finalizeBoundary()
        self.trackpoints = []

    def editStartPos(self):
        if not(self.isEditingStartPos) and self.editStatus == 0:
            self.editStatus = 1
            self.isEditingStartPos = True
        
        elif self.isEditingStartPos:
            self.startPos = [i for i in pygame.mouse.get_pos()]
            if self.clicked:
                self.isEditingStartPos = False
                self.editStatus = 0
    
    # Primitive UNDO function that simply removes the last thing added. Does not account for
    # other clear functions nor does it replace the old features
    
    # It also does not undo a point already placed!! (e.g. if placed point 1 of a new checkpoint, deletes wrong one)
    def undo(self):
        if (len(self.editStack) > 0):
            toRemove = self.editStack.pop()
            if toRemove == 0: # start line
                self.clearStartLine()
            elif toRemove == 1: # checkpoint
                self.checkpoints.pop()
            else:
                removeIndex = toRemove - 2
                self.trackpoints[removeIndex].pop()
            
    # Resets the track to default
    def reset(self):
        self.clearBoundaries()
        self.clearStartLine()
        self.clearCheckpoints()
        self.startPos = Track.DEFAULT_CAR_START_POS
        self.startDir = Track.DEFAULT_CAR_START_DIR
        self.editStack = []

        self.editStatus = 0
        self.isEditingCheckpoint = False
        self.isEditingStartLine = False
        self.isEditingBoundary = False
        self.isEditingStartPos = False
        self.isEditingStartDir = False