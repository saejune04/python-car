import pygame
import math
from car import Car
from button import Button
from track import Track

# pygame setup
pygame.init()
WIDTH = 1920
HEIGHT = 1080
surface = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
running = True


defaultTrackCode = open('./defaultTrackCode.json', 'r').read()

track = Track()
track.load(defaultTrackCode)
car = Car(track)

# Load default track code


# up_button_img = pygame.image.load('./images/up_btn.png').convert_alpha()
# up_button = Button.Button(200, 100, up_button_img, 1)
# down_button_img = pygame.image.load('./images/down_btn.png').convert_alpha()
# down_button = Button.Button(300, 100, down_button_img, 1)

# 150 x 63 at 1 scale
undo_button_img = pygame.image.load('./images/undo_btn.png').convert_alpha()
undo_button = Button(100, 940, undo_button_img, 0.9)
clearall_button_img = pygame.image.load('./images/clear_all_btn.png').convert_alpha()
clearall_button = Button(100, 1010, clearall_button_img, 0.9)

edit_startline_button_img = pygame.image.load('./images/edit_startline_btn.png').convert_alpha()
edit_startline_button = Button(250, 940, edit_startline_button_img, 0.9)
clear_startline_button_img = pygame.image.load('./images/clear_startline_btn.png').convert_alpha()
clear_startline_button = Button(250, 1010, clear_startline_button_img, 0.9)

add_checkpoint_button_img = pygame.image.load('./images/add_checkpoint_btn.png').convert_alpha()
add_checkpoint_button = Button(400, 940, add_checkpoint_button_img, 0.9)
clear_checkpoints_button_img = pygame.image.load('./images/clear_checkpoints_btn.png').convert_alpha()
clear_checkpoints_button = Button(400, 1010, clear_checkpoints_button_img, 0.9)

add_boundary_button_img = pygame.image.load('./images/add_boundary_btn.png').convert_alpha()
add_boundary_button = Button(550, 940, add_boundary_button_img, 0.9)
clear_boundaries_button_img = pygame.image.load('./images/clear_boundaries_btn.png').convert_alpha()
clear_boundaries_button = Button(550, 1010, clear_boundaries_button_img, 0.9)
finalize_boundary_button_img = pygame.image.load('./images/finalize_boundary_btn.png').convert_alpha()
finalize_boundary_button = Button(550, 940, finalize_boundary_button_img, 0.9) 

save_button_img = pygame.image.load('./images/save_btn.png').convert_alpha()
save_button = Button(700, 940, save_button_img, 0.9)
load_button_img = pygame.image.load('./images/load_btn.png').convert_alpha()
load_button = Button(700, 1010, load_button_img, 0.9)

change_startpos_button_img = pygame.image.load('./images/change_startpos_btn.png').convert_alpha()
change_startpos_button = Button(850, 940, change_startpos_button_img, 0.9)
change_startdir_button_img = pygame.image.load('./images/change_startdir_btn.png').convert_alpha()
change_startdir_button = Button(850, 1010, change_startdir_button_img, 0.9)

while running:
    surface.fill("grey")
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Render
    track.render(surface)
    car.update(surface)


    # Button handler

    # if (up_button.draw(surface)):
    #     pass
    # if (down_button.draw(surface)):
    #     pass
    if undo_button.draw(surface):
        track.undo()
    if clearall_button.draw(surface):
        track.reset()
    if edit_startline_button.draw(surface):
        track.editStartLine()
    if clear_startline_button.draw(surface):
        track.clearStartLine()
    if add_checkpoint_button.draw(surface):
        track.addCheckpoint()
    if clear_checkpoints_button.draw(surface):
        track.clearCheckpoints()
    if not track.isEditingBoundary:
        if add_boundary_button.draw(surface):
            track.addBoundary()
    else:
        if finalize_boundary_button.draw(surface):
            track.finalizeBoundary()
    if clear_boundaries_button.draw(surface):
        track.clearBoundaries()
    if save_button.draw(surface):
        track.save()
    if load_button.draw(surface):
        code = input("Enter save data: ")
        track.load(code)
    if change_startpos_button.draw(surface):
        track.editStartPos()
    if change_startdir_button.draw(surface):
        print('TODO: implement')


    # Track editing handler
    # if track.isEditingStartLine:
    #     track.editStartLine()
    # if track.isEditingCheckpoint:
    #     track.addCheckpoint()
    # if track.isEditingBoundary:
    #     track.addBoundary()
    # if track.isEditingStartPos:
    #     track.editStartPos()

    # User controls
    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        car.accelerate(1.4)
    if keys[pygame.K_s]:
        car.accelerate(-0.8)
    if keys[pygame.K_a]:
        car.turn(-1.3 * 0.08726646)
    if keys[pygame.K_d]:
        car.turn(1.3 * 0.08726646)

    # flip() the display to put on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000

pygame.quit()