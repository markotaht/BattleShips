from Assets import *
from Util import *
import pygame
from Board import *
from collections import defaultdict

class GameScreen:

    def init(self, client, windowSurface, board, isHost, isGameStarted):
        self.client = client
        self.windowSurface = windowSurface
        self.boardWidth = board.boardWidth
        self.boards = defaultdict(Board)
        self.isGameStarted = isGameStarted;
        self.isHost = isHost
        self.boards["__me__"] = board
        self.playerReady = {}
        board.parent = self
        #Active = Player whose board is being shown
        self.activePlayer = "__me__"
        self.activeBoard = self.boards["__me__"]
        #Turn = Player whose turn it actually is
        self.turnPlayer = "__me__"



        self.tinyFont = tinyFont
        self.smallFont = smallFont
        self.mediumFont = mediumFont
        self.largeFont = largeFont

    def update(self, events):
        #if escapePressed(events):
            #TODO: Handle

        if self.isGameStarted == False:
            turnStr = "Waiting for players..."
        else:
            if self.turnPlayer == "__me__":
                turnStr = "Your turn"
            else:
                turnStr = self.turnPlayer + "'s turn"

        turnText = self.mediumFont.render(turnStr, True, COLOR_BLACK)
        turnTextRect = turnText.get_rect()
        turnTextRect.left = 10
        turnTextRect.top = 10
        self.windowSurface.blit(turnText, turnTextRect)

        y = 100
        #Player list - WIP
        for player in self.playerReady:
            ready = self.playerReady[player]

            if ready:
                color = COLOR_GREEN
            else:
                color = COLOR_RED
            playerText = self.mediumFont.render(player, True, color)

            playerTextRect = playerText.get_rect()
            playerTextRect.left = 20
            playerTextRect.top = y
            y += 50
            self.windowSurface.blit(playerText, playerTextRect)



        #Navigating between boards
        previousText = self.largeFont.render(" < ", True, COLOR_WHITE, COLOR_BLACK)
        previousTextRect = previousText.get_rect()
        previousTextRect.right = 300
        previousTextRect.top = 420
        previousRect = self.windowSurface.blit(previousText, previousTextRect)
        if clickedOnRect(previousRect, events):
            self.previousBoard()

        nextText = self.largeFont.render(" > ", True, COLOR_WHITE, COLOR_BLACK)
        nextTextRect = nextText.get_rect()
        nextTextRect.left = 580
        nextTextRect.top = 420
        nextRect = self.windowSurface.blit(nextText, nextTextRect)
        if clickedOnRect(nextRect, events):
            self.nextBoard()

        if self.activePlayer == "__me__":
            currentBoardStr = "Your board"
        else:
            currentBoardStr = self.activePlayer + "'s board"

        currentBoardText = self.mediumFont.render(currentBoardStr, True, COLOR_BLACK)
        currentBoardTextRect = currentBoardText.get_rect()
        currentBoardTextRect.centerx = 440
        currentBoardTextRect.top = 425
        self.windowSurface.blit(currentBoardText, currentBoardTextRect)

        self.activeBoard.update(events)


    def previousBoard(self):
        #Returns a list of tuples (playerName, board)
        otherPlayers = self.boards.items()

        for i in range(0, len(otherPlayers)):
            if otherPlayers[i][0] == self.activePlayer:
                if i > 0:
                    self.setActivePlayer(otherPlayers[i - 1][0])
                else:
                    self.setActivePlayer(otherPlayers[len(otherPlayers) - 1][0])
                break

    def nextBoard(self):
        #Returns a list of tuples (playerName, board)
        otherPlayers = self.boards.items()

        for i in range(0, len(otherPlayers)):
            if otherPlayers[i][0] == self.activePlayer:
                if i + 1 < len(otherPlayers):
                    self.setActivePlayer(otherPlayers[i + 1][0])
                else:
                    self.setActivePlayer(otherPlayers[0][0])
                break

    #Called by the board whenever there's a click
    def onBoardClick(self, tileX, tileY):
        #TODO: identify board using self.activeBoard and do whatever
        #is needed depending on scenario
        print str(tileX) + " " + str(tileY)

    def addPlayer(self, name, board):
        self.boards[name] = board
        #TODO: Update this value properly
        self.playerReady[name] = False

    # Player should be a string, "__me__" for local player
    def setActivePlayer(self, player):
        self.activePlayer = player
        self.activeBoard = self.boards[player]

    # Player should be a string, "__me__" if local player's turn
    def setTurnPlayer(self, player):
        self.turnPlayer = player

    #Marks player as ready
    #TODO this is also used when player joins game, better use addPlayer?
    def addReadyPlayer(self, player, ready):
        self.playerReady[player] = ready