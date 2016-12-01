import pygame

#Rect - the bounding rectangle which to check
#Events - list of pygame events
#Return - True/False depending on if events include mouse left click on the rect
def clickedOnRect(rect, events):
    for event in events:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mousePos = pygame.mouse.get_pos()
            if rect.collidepoint(mousePos):
                return True
    return False