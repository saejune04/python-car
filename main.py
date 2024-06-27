import pygame
from Track.track import Track
from Controllers.GA_controller import GA_Controller
from Controllers.user_controller import User_Controller
from Controllers.DQL_controller import DQL_Controller
from time import perf_counter


WIDTH = 1920
HEIGHT = 1080

def main():
    pygame.init()

    surface = pygame.display.set_mode((WIDTH, HEIGHT))
    surface.set_alpha(None)

    from Buttons.button_handler import handleButtons
    clock = pygame.time.Clock()
    framerate_cap = 60
    running = True
    numframes = 0
    totaltime = 0
    fps = 0

    # Set up the track
    track = Track()
    defaultTrackCode = open('./Track/defaultTrackCode.json', 'r').read()
    track.load(defaultTrackCode)

    # Initialize controller
    # controller = GA_Controller(track, surface, brain_template=[32, 32], num_cars=40)
    # controller =  User_Controller(track, surface)
    controller = DQL_Controller(track, surface, brain_template=[128, 128])

    if type(controller) == GA_Controller:
        load = input("Load previous best model? (y/n): ")
        if load == "y":
            controller.load()
    if type(controller) == DQL_Controller:
        load = input("Load previous best model? (y/n): ")
        if load == "y":
            controller.load()

    while running:
        surface.fill("grey")
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if type(controller) == GA_Controller:
                    save = input("Save best model? (y/n): ")
                    if save == "y":
                        controller.save()
                if type(controller) == DQL_Controller:
                    save = input("Save best model? (y/n): ")
                    if save == "y":
                        controller.save()
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
        fps_surface = font.render("FPS: " + str(fps), False, (0, 0, 0))
        surface.blit(fps_surface, (20,20))

        # flip() the display to put on screen
        pygame.display.flip()

        actual_end = perf_counter()
        totaltime += actual_end - end
        
        # limits FPS to 60
        # dt is delta time in seconds since last frame, used for framerate-
        # independent physics.

        # Press 0 for hyperspeed, 9 to go back to 60 fps
        keys = pygame.key.get_pressed()
        if keys[pygame.K_0]:
            framerate_cap = 1000
        if keys[pygame.K_9]:
            framerate_cap = 60

        dt = clock.tick(framerate_cap) / 1000

    pygame.quit()

if __name__ == '__main__':
    main()