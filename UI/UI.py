import pygame, sys
from MainMenuScreen import *
from SessionSelectScreen import *
from SetupShipsScreen import *
from NewSessionScreen import *
from GameScreen import *
from Assets import *

class UI:
    def __init__(self):
        # set up pygame
        pygame.init()

        # set up the window
        self.windowSurface = pygame.display.set_mode((640, 480), 0, 32)
        self.windowSurface.fill(COLOR_WHITE)
        pygame.display.set_caption('Naval Warfare Simulator')

        self.name = "DefaultName"

        #TEST DIFFERENT SCREENS HERE
        self.loadMainMenuScreen()

        #When you want to start the application from the game screen
        #This will create an empty screen
        #board = Board()
        #board.init(self.windowSurface, 8, None)
        #self.loadGameScreen(board)

        self.run();

    def run(self):
        clock = pygame.time.Clock()

        while True:
            # Ensure max 30 fps
            clock.tick(30)

            events = pygame.event.get()
            for event in events:
                if event.type == QUIT:
                    sys.exit()

            # Clear the screen
            self.windowSurface.fill(COLOR_WHITE)

            self.screen.update(events)

            # refresh the screen
            pygame.display.flip()

    def loadMainMenuScreen(self):
        self.screen = MainMenuScreen()
        self.screen.init(self, self.windowSurface)
        self.screen.addServer("Mock server", 1234)

    def loadNewSessionScreen(self):
        self.screen = NewSessionScreen()
        self.screen.init(self, self.windowSurface)

    def loadSessionSelectScreen(self):
        self.screen = SessionSelectScreen()
        self.screen.init(self, self.windowSurface)

    def loadSetupShipsScreen(self, boardSize):
        self.screen = SetupShipsScreen()
        self.screen.init(self, self.windowSurface, boardSize)

    #Board should contain your placed ships
    def loadGameScreen(self, board):
        self.screen = GameScreen()
        self.screen.init(self, self.windowSurface, board)

if __name__ == "__main__":
    ui = UI()