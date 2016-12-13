from Assets import *
from Util import *
import pygame
from Board import *
from collections import defaultdict

class GameScreen:

    def init(self, client, windowSurface, board, isHost, isGameStarted, playerReady):
        self.client = client
        self.windowSurface = windowSurface
        self.boardWidth = board.boardWidth
        self.boards = defaultdict(Board)
        self.isGameStarted = isGameStarted;
        self.isHost = isHost
        self.boards[self.client.username] = board
        self.playerReady = playerReady
        board.parent = self
        #Active = Player whose board is being shown
        self.activePlayer = self.client.username
        self.activeBoard = self.boards[self.client.username]
        #Turn = Player whose turn it actually is
        self.turnPlayer = self.client.username if self.isHost else "not you"

        #Create boards for the existing players
        for player in playerReady.keys():
            if player != self.client.username:
                print "Adding a board for " + player
                playerBoard = Board()
                playerBoard.init(windowSurface, board.boardWidth, self)
                self.boards[player] = playerBoard

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
            if self.turnPlayer == self.client.username:
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
        everyoneReady = True
        for player in self.playerReady:
            ready = self.playerReady[player]

            x = 20

            if self.isHost:
                #Add kick option
                kickText = self.smallFont.render("KICK", True, COLOR_WHITE, COLOR_BLACK)
                kickTextRect = kickText.get_rect()
                kickTextRect.left = x
                kickTextRect.top = y
                x += 45
                kickRect = self.windowSurface.blit(kickText, kickTextRect)
                if clickedOnRect(kickRect, events):
                    #TODO
                    print "Should kick player"



            if ready:
                color = COLOR_GREEN
            else:
                color = COLOR_RED
                everyoneReady = False
            playerText = self.smallFont.render(player, True, color)

            playerTextRect = playerText.get_rect()
            playerTextRect.left = x
            playerTextRect.top = y
            y += 40
            self.windowSurface.blit(playerText, playerTextRect)

        if everyoneReady and self.isHost and len(self.boards) > 1:
            #
            if not self.isGameStarted:
                startGameText = self.mediumFont.render("Start game", True, COLOR_WHITE, COLOR_BLACK)
                startGameTextRect = startGameText.get_rect()
                startGameTextRect.left = 20
                startGameTextRect.bottom = 470
                startGameRect = self.windowSurface.blit(startGameText, startGameTextRect)
                if clickedOnRect(startGameRect, events):
                    print("Starting the game...")
                    response = self.client.startGame()
                    if response.startswith("OK"):
                        self.isGameStarted = True
                        self.nextBoard()


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

        if self.activePlayer == self.client.username:
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
        players = self.boards.items()

        for i in range(0, len(players)):
            if players[i][0] == self.activePlayer:
                if i > 0:
                    self.setActivePlayer(players[i - 1][0])
                else:
                    self.setActivePlayer(players[len(players) - 1][0])
                break

    def nextBoard(self):
        #Returns a list of tuples (playerName, board)
        players = self.boards.items()

        for i in range(0, len(players)):
            if players[i][0] == self.activePlayer:
                if i + 1 < len(players):
                    self.setActivePlayer(players[i + 1][0])
                else:
                    self.setActivePlayer(players[0][0])
                break

    #Called by the board whenever there's a click
    def onBoardClick(self, tileX, tileY):
        #TODO: identify board using self.activeBoard and do whatever
        #is needed depending on scenario

        # game logic
        # my turn
        if self.isGameStarted:
            if self.turnPlayer == self.client.username:
                if self.activePlayer != self.client.username:
                    request = ":".join([str(tileX),str(tileY), self.activePlayer, self.client.username])
                    response = self.client.bomb(request)
                    print "Bomb response", response
                    #TODO additional game logic needed here?
                    if response == "HIT":
                        self.activeBoard.setTileByIndex(tileX, tileY, 3)
                    elif response == "SUNK":
                        self.activeBoard.setTileByIndex(tileX, tileY, 3)
                        print "This is not handled yet"
                    else:
                        self.activeBoard.setTileByIndex(tileX, tileY, 2)
                else:
                    print "click on your board "+ str(tileX) + " " + str(tileY)

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

        if player not in self.boards:
            if player != self.client.username:
                print "Adding a board for " + player
                playerBoard = Board()
                playerBoard.init(self.windowSurface, self.boardWidth, self)
                self.boards[player] = playerBoard
