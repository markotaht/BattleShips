import pygame, sys
from MainMenuScreen import *
from SetupShipsScreen import *
from pygame.locals import *
from Assets import *

# set up pygame
pygame.init()

# set up the window
windowSurface = pygame.display.set_mode((640, 480), 0, 32)
windowSurface.fill(COLOR_WHITE)
pygame.display.set_caption('Naval Warfare Simulator')

screen = SetupShipsScreen()
screen.init(windowSurface, 12)

#screen = MainMenuScreen()
#screen.init(windowSurface)
#screen.addServer("127.0.0.1", 7777)
#screen.addServer("Mock server", 1234)

clock = pygame.time.Clock()

# # draw the white background onto the surface
# windowSurface.fill(WHITE)
#
# # draw a green polygon onto the surface
# pygame.draw.polygon(windowSurface, GREEN, ((146, 0), (291, 106), (236, 277), (56, 277), (0, 106)))
#
# # draw some blue lines onto the surface
# pygame.draw.line(windowSurface, BLUE, (60, 60), (120, 60), 4)
# pygame.draw.line(windowSurface, BLUE, (120, 60), (60, 120))
# pygame.draw.line(windowSurface, BLUE, (60, 120), (120, 120), 4)
#
# # draw a blue circle onto the surface
# pygame.draw.circle(windowSurface, BLUE, (300, 50), 20, 0)
#
# # draw a red ellipse onto the surface
# pygame.draw.ellipse(windowSurface, RED, (300, 250, 40, 80), 1)
#
# # draw the text's background rectangle onto the surface
# pygame.draw.rect(windowSurface, RED, (textRect.left - 20, textRect.top - 20, textRect.width + 40, textRect.height + 40))
#
# # get a pixel array of the surface
# pixArray = pygame.PixelArray(windowSurface)
# pixArray[480][380] = BLACK
# del pixArray

while True:
    #Ensure max 30 fps
    clock.tick(30)

    events = pygame.event.get()
    for event in events:
        if event.type == QUIT:
            sys.exit()

    #Clear the screen
    windowSurface.fill(COLOR_WHITE)

    screen.update(events)

    # refresh the screen
    pygame.display.flip()
#
