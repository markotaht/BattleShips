import pygame
from Assets import *
from Util import *
import re

#TODO: Make shared with Session.py
TILE_EMPTY = 0
TILE_SHIP = 1
TILE_MISS = 2
TILE_SHIP_HIT = 3

class Board:
    def init(self, windowSurface, boardWidth, parent):
        self.windowSurface = windowSurface
        self.boardWidth = boardWidth
        self.parent = parent
        self.board = [[0 for x in range(boardWidth)] for y in range(boardWidth)]

        #Can be called for the n'th letter for n'th row. Starts from 0
        self._letters = []
        for x in range(self.boardWidth):
            self._letters.append(str(unichr(65 + x)))
            for y in range(self.boardWidth):
                self.board[x][y] = TILE_EMPTY

        #Some debug values
        self._gameAreaWidth = 350
        self._tileWidth = self._gameAreaWidth / boardWidth

        #TODO: Move fonts to Assets
        self.tinyFont = pygame.font.SysFont(None, 18)
        self.smallFont = pygame.font.SysFont(None, 24)
        self.mediumFont = pygame.font.SysFont(None, 36)
        self.largeFont = pygame.font.SysFont(None, 48)



    def update(self, events):
        startX = 270#(self.windowSurface.get_width() - self._gameAreaWidth) / 2
        startY = (self.windowSurface.get_height() - self._gameAreaWidth) / 2

        for x in range(self.boardWidth):
            posX = startX + x * self._tileWidth

            #Print letters
            letterText = self.smallFont.render(self._letters[x], True, COLOR_BLACK)
            letterTextRect = letterText.get_rect()
            letterTextRect.centerx = posX + self._tileWidth/2
            letterTextRect.bottom = startY - 4
            self.windowSurface.blit(letterText, letterTextRect)

            for y in range(self.boardWidth):
                posY = startY + y * self._tileWidth
                #Print unmbers
                if x == 0:
                    letterText = self.smallFont.render(str(y + 1), True, COLOR_BLACK)
                    letterTextRect = letterText.get_rect()
                    letterTextRect.right = startX - 4
                    letterTextRect.centery = posY + self._tileWidth / 2
                    self.windowSurface.blit(letterText, letterTextRect)

                #Drawing tiles
                tile = self.board[x][y]
                tileRect = (posX +1, posY+1, self._tileWidth-2, self._tileWidth-2)
                borderRect = (posX , posY , self._tileWidth , self._tileWidth )
                if tile == TILE_EMPTY:
                    pygame.draw.rect(self.windowSurface, COLOR_BLACK, borderRect, 2)
                    rect = pygame.draw.rect(self.windowSurface, COLOR_WHITE, tileRect, 0)
                if tile == TILE_SHIP:
                    rect = pygame.draw.rect(self.windowSurface, COLOR_DARK_GREY, tileRect, 0)
                    pygame.draw.rect(self.windowSurface, COLOR_DARK_GREY, borderRect, 2)
                elif tile == TILE_SHIP_HIT:
                    pygame.draw.rect(self.windowSurface, COLOR_DARK_GREY, borderRect, 2)
                    rect = pygame.draw.rect(self.windowSurface, COLOR_DARK_GREY, tileRect, 0)
                    pygame.draw.line(self.windowSurface, COLOR_RED, (posX, posY),
                                     (posX + self._tileWidth, posY + self._tileWidth), 3)
                    pygame.draw.line(self.windowSurface, COLOR_RED, (posX + self._tileWidth, posY),
                                     (posX, posY + self._tileWidth), 3)
                elif tile == TILE_MISS:
                    pygame.draw.rect(self.windowSurface, COLOR_BLACK, borderRect, 2)
                    rect = pygame.draw.rect(self.windowSurface, COLOR_WHITE, tileRect, 0)
                    pygame.draw.circle(self.windowSurface, COLOR_DARK_GREY,
                                       (posX + self._tileWidth/2, posY + self._tileWidth/2),
                                       self._tileWidth / 6)

                if clickedOnRect(rect, events):
                    self.parent.onBoardClick(x, y)


    def getTileByIndex(self, x, y):
        return self.board[x][y]

    def setTileByIndex(self, x, y, value):
        #TODO: What if it's not legitimate?
        if x >= 0 and y >= 0 and x < self.boardWidth and y < self.boardWidth:
            self.board[x][y] = value

    #Coordinates expected to be in form "A4", "C12" etc
    def setTileByGameCoordinates(self, coordinates, value):
        #fails when there are more than 1 letters ("AA3")
        x = int(coordinates[1:]) - 1
        y = ord(coordinates[0])
        self.setTileByIndex(x, y, value)
        return
