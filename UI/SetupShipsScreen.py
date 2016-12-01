from Assets import *
from Util import *
import pygame
from Board import *

class SetupShipsScreen:

    def init(self, windowSurface, boardWidth):
        self.windowSurface = windowSurface
        self.boardWidth = boardWidth
        self.board = Board()
        self.board.init(windowSurface, boardWidth)

        #TODO: Move fonts to Assets
        self.tinyFont = pygame.font.SysFont(None, 18)
        self.smallFont = pygame.font.SysFont(None, 24)
        self.mediumFont = pygame.font.SysFont(None, 36)
        self.largeFont = pygame.font.SysFont(None, 48)


    def update(self, events):
        self.board.update(events)

