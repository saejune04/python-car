import pygame
import math
from car import Car
from aicar import AICar
from button import Button
from track import Track
from GA_controller import GA_Controller
from user_controller import User_Controller
from time import perf_counter


WIDTH = 1920
HEIGHT = 1080

def main():
    pygame.init()

    surface = pygame.display.set_mode((WIDTH, HEIGHT))
    surface.set_alpha(None)

    from button_handler import handleButtons
    clock = pygame.time.Clock()
    running = True
    numframes = 0
    totaltime = 0
    fps = 0

    # Set up the track
    track = Track()
    defaultTrackCode = open('./defaultTrackCode.json', 'r').read()
    track.load(defaultTrackCode)

    # Initialize controller
    controller = GA_Controller(track, surface, brain_template=[50, 32], num_cars=40)
    # controller =  User_Controller(track, surface)

    if type(controller) == GA_Controller:
        load = input("Load previous best model? (y/n): ")
        if load == "y":
            controller.loadBestModel()

    while running:
        surface.fill("grey")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if type(controller) == GA_Controller:
                    save = input("Save best model? (y/n): ")
                    if save == "y":
                        controller.saveBestModel()
                running = False

        # Render and update
        start = perf_counter()

        track.render(surface)
        controller.update()

        # Button handler
        handleButtons(surface, track)


        # Track editing handler
        # if track.isEditingStartLine:
        #     track.editStartLine()
        # if track.isEditingCheckpoint:
        #     track.addCheckpoint()
        # if track.isEditingBoundary:
        #     track.addBoundary()
        # if track.isEditingStartPos:
        #     track.editStartPos()
  


        # Display FPS
        end = perf_counter()
        totaltime += end - start
        numframes += 1   

        if totaltime >= 0.25: # Time to refresh fps
            fps = int(numframes / totaltime) if totaltime > 0 else 0
            numframes = 0
            totaltime = 0

        pygame.font.init()
        font = pygame.font.SysFont('Comic Sans MS', 10)
        fps_surface = font.render(str(fps), False, (0, 0, 0))
        surface.blit(fps_surface, (20,20))

        # flip() the display to put on screen
        pygame.display.flip()

        actual_end = perf_counter()
        totaltime += actual_end - end
        
        # limits FPS to 60
        # dt is delta time in seconds since last frame, used for framerate-
        # independent physics.
        dt = clock.tick(60) / 1000

    pygame.quit()

if __name__ == '__main__':
    main()