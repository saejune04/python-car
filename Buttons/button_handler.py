import pygame
from Buttons import button

# up_button_img = pygame.image.load(button_images_file_path + 'up_btn.png').convert_alpha()
# up_button = button.Button(200, 100, up_button_img, 1)
# down_button_img = pygame.image.load(button_images_file_path + 'down_btn.png').convert_alpha()
# down_button = button.Button(300, 100, down_button_img, 1)

button_images_file_path = "./Buttons/Button_images/"

# 150 x 63 at 1 scale
undo_button_img = pygame.image.load(button_images_file_path + 'undo_btn.png').convert_alpha()
undo_button = button.Button(100, 940, undo_button_img, 0.9)
clearall_button_img = pygame.image.load(button_images_file_path + 'clear_all_btn.png').convert_alpha()
clearall_button = button.Button(100, 1010, clearall_button_img, 0.9)

edit_startline_button_img = pygame.image.load(button_images_file_path + 'edit_startline_btn.png').convert_alpha()
edit_startline_button = button.Button(250, 940, edit_startline_button_img, 0.9)
clear_startline_button_img = pygame.image.load(button_images_file_path + 'clear_startline_btn.png').convert_alpha()
clear_startline_button = button.Button(250, 1010, clear_startline_button_img, 0.9)

add_checkpoint_button_img = pygame.image.load(button_images_file_path + 'add_checkpoint_btn.png').convert_alpha()
add_checkpoint_button = button.Button(400, 940, add_checkpoint_button_img, 0.9)
clear_checkpoints_button_img = pygame.image.load(button_images_file_path + 'clear_checkpoints_btn.png').convert_alpha()
clear_checkpoints_button = button.Button(400, 1010, clear_checkpoints_button_img, 0.9)

add_boundary_button_img = pygame.image.load(button_images_file_path + 'add_boundary_btn.png').convert_alpha()
add_boundary_button = button.Button(550, 940, add_boundary_button_img, 0.9)
clear_boundaries_button_img = pygame.image.load(button_images_file_path + 'clear_boundaries_btn.png').convert_alpha()
clear_boundaries_button = button.Button(550, 1010, clear_boundaries_button_img, 0.9)
finalize_boundary_button_img = pygame.image.load(button_images_file_path + 'finalize_boundary_btn.png').convert_alpha()
finalize_boundary_button = button.Button(550, 940, finalize_boundary_button_img, 0.9) 

save_button_img = pygame.image.load(button_images_file_path + 'save_btn.png').convert_alpha()
save_button = button.Button(700, 940, save_button_img, 0.9)
load_button_img = pygame.image.load(button_images_file_path + 'load_btn.png').convert_alpha()
load_button = button.Button(700, 1010, load_button_img, 0.9)

change_startpos_button_img = pygame.image.load(button_images_file_path + 'change_startpos_btn.png').convert_alpha()
change_startpos_button = button.Button(850, 940, change_startpos_button_img, 0.9)
change_startdir_button_img = pygame.image.load(button_images_file_path + 'change_startdir_btn.png').convert_alpha()
change_startdir_button = button.Button(850, 1010, change_startdir_button_img, 0.9)

def handleButtons(surface, track):
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