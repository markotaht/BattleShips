from Player import Player
from Board import *

class GameScreen:

    def init(self, client, windowSurface, board, isHost, isGameStarted, players):
        self.client = client
        self.windowSurface = windowSurface
        self.boardWidth = board.boardWidth
        self.isGameStarted = isGameStarted
        self.isGameOver = False
        self.isHost = isHost

        self.players = players
        for player in players.keys():
            #Update board parent fields
            players[player].board.parent = self

        #Active = Player whose board is being shown
        self.activePlayer = self.client.username
        self.activeBoard = self.players[self.client.username].board
        #Turn = Player whose turn it actually is
        self.turnPlayer = "Waiting from server"
        self.winnerStr = ""
        self.deadStr = ""

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

        if self.isGameOver == True:
            turnStr = "Good game!"
            # Show winner if there is one
            winnerText = self.smallFont.render(self.winnerStr, True, COLOR_BLACK)
            winnerTextRect = winnerText.get_rect()
            winnerTextRect.left = 20
            winnerTextRect.bottom = 430
            self.windowSurface.blit(winnerText, winnerTextRect)

        #Show this when you are dead
        deadText = self.smallFont.render(self.deadStr, True, COLOR_BLACK)
        deadTextRect = deadText.get_rect()
        deadTextRect.left = 20
        deadTextRect.bottom = 400
        self.windowSurface.blit(deadText, deadTextRect)

        turnText = self.mediumFont.render(turnStr, True, COLOR_BLACK)
        turnTextRect = turnText.get_rect()
        turnTextRect.left = 10
        turnTextRect.top = 10
        self.windowSurface.blit(turnText, turnTextRect)

        #leave button
        leaveText = self.smallFont.render("Leave session", True, COLOR_WHITE, COLOR_BLACK)
        leaveTextRect = leaveText.get_rect()
        leaveTextRect.left = 280
        leaveTextRect.top = 10
        leaveRect = self.windowSurface.blit(leaveText, leaveTextRect)
        if clickedOnRect(leaveRect, events):
            self.client.leave(self.client.username)

        #If player is not dead
        if self.deadStr == "":
            #disconnect button
            disconnectText = self.smallFont.render("Disconnect temporarily", True, COLOR_WHITE, COLOR_BLACK)
            disconnectTextRect = disconnectText.get_rect()
            disconnectTextRect.left = 400
            disconnectTextRect.top = 10
            disconnectRect = self.windowSurface.blit(disconnectText, disconnectTextRect)
            if clickedOnRect(disconnectRect, events):
                self.client.disconnect(self.client.username)

        y = 100
        #Player list
        everyoneReady = True
        for player in self.players:
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
                    print "Kicking " + player
                    self.client.kickPlayer(player)
                    #Temporarily skip a frame to prevent errors below
                    return

            if self.turnPlayer == self.client.username:
                if player != self.client.username and self.players[player].hasBeenShot:
                    shootText = self.smallFont.render("[SHOT]", True, COLOR_BLACK)
                    shootTextRect = shootText.get_rect()
                    shootTextRect.left = x
                    shootTextRect.top = y
                    x += 65
                    self.windowSurface.blit(shootText, shootTextRect)

            if not self.players[player].isAlive:
                deadText = self.smallFont.render("[DEAD]", True, COLOR_BLACK)
                deadTextRect = deadText.get_rect()
                deadTextRect.left = x
                deadTextRect.top = y
                x += 65
                self.windowSurface.blit(deadText, deadTextRect)

            if self.isGameStarted:
                if self.players[player].connected:
                    color = COLOR_GREEN
                else:
                    #Mark disconnected players grey
                    color = COLOR_DARK_GREY
            else:
                if self.players[player].connected:
                    if self.players[player].isReady:
                        color = COLOR_GREEN
                    else:
                        color = COLOR_RED
                        everyoneReady = False
                else:
                    color = COLOR_DARK_GREY
                    everyoneReady = False

            playerText = self.smallFont.render(player, True, color)
            playerTextRect = playerText.get_rect()
            playerTextRect.left = x
            playerTextRect.top = y
            self.windowSurface.blit(playerText, playerTextRect)
            y += 40

        if not self.isGameStarted and everyoneReady and self.isHost and len(self.players) > 1:
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

        if self.isHost and self.isGameOver:
            restartGameText = self.mediumFont.render("Restart game", True, COLOR_WHITE, COLOR_BLACK)
            restartGameTextRect = restartGameText.get_rect()
            restartGameTextRect.left = 20
            restartGameTextRect.bottom = 470
            restartGameRect = self.windowSurface.blit(restartGameText, restartGameTextRect)
            if clickedOnRect(restartGameRect, events):
                print("Restarting the game...")
                response = self.client.restartGame("")

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
        players = self.players.keys()

        for i in range(0, len(players)):
            if players[i] == self.activePlayer:
                if i > 0:
                    self.setActivePlayer(players[i - 1])
                else:
                    self.setActivePlayer(players[len(players) - 1])
                break

    def nextBoard(self):
        players = self.players.keys()

        for i in range(0, len(players)):
            if players[i] == self.activePlayer:
                if i + 1 < len(players):
                    self.setActivePlayer(players[i + 1])
                else:
                    self.setActivePlayer(players[0])
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
                    if not self.players[self.activePlayer].hasBeenShot and self.players[self.activePlayer].isAlive:
                        if self.activeBoard.getTileByIndex(tileX, tileY) == 0:
                            request = ":".join([str(tileX),str(tileY), self.activePlayer, self.client.username])
                            response = self.client.bomb(request)
                            print "Bomb response", response
                            #TODO additional game logic needed here?
                            if response == "HIT" or response == "SUNK":
                                self.activeBoard.setTileByIndex(tileX, tileY, 3)
                            if response == "MISS":
                                #Set this board to be finished with the current move
                                self.players[self.activePlayer].hasBeenShot = True
                                self.activeBoard.setTileByIndex(tileX, tileY, 2)
                        else:
                            print "Tried to click on a tile that has already been hit"
                    else:
                        print "Tried to shoot a player that the player has beenalready shot otr is dead"
                else:
                    print "click on your board "+ str(tileX) + " " + str(tileY)

    #draws the sunk ship and it's surroundings
    def markAsSunk(self,attackedPlayer, shiphit):
        shiphit = shiphit.split(",")
        #mark ship as sunk
        tmpBoard = self.players[attackedPlayer].board
        for i in shiphit:
            tmp = i.split(";")
            x = int(tmp[0])
            y = int(tmp[1])
            tmpBoard.setTileByIndex(x,y, 3)

        #add miss symbols to edges
        for j in shiphit:
            tmp = j.split(";")
            x = int(tmp[0])
            y = int(tmp[1])
            # check if ship on x+
            for i in range(x + 1, self.boardWidth):
                if tmpBoard.getTileByIndex(i,y) == 3:
                    #skip sunkship symbols
                    pass
                elif tmpBoard.getTileByIndex(i,y) == 0:
                    #if we find empty place place miss symbol there
                    tmpBoard.setTileByIndex(i, y, 2)
                    #and also to corners!
                    if y + 1 <= self.boardWidth:
                        tmpBoard.setTileByIndex(i, y + 1, 2)
                    if y != 0:
                        tmpBoard.setTileByIndex(i, y-1, 2)
                    break
                else:
                    #other options:
                    #miss - can skip
                    #if there is ship symbol then something is wrong
                    #if previous was hitsymbol and current is miss then add corners
                    if tmpBoard.getTileByIndex(i-1,y) == 3 and tmpBoard.getTileByIndex(i,y) == 2:
                        if y + 1 <= self.boardWidth:
                            tmpBoard.setTileByIndex(i, y + 1, 2)
                        if y != 0:
                            tmpBoard.setTileByIndex(i, y - 1, 2)
                    break
            if x == 1:
                if tmpBoard.getTileByIndex(0, y) == 0:
                    tmpBoard.setTileByIndex(0, y, 2)
            else:
                for i in range(x - 1, -1, -1):
                    if tmpBoard.getTileByIndex(i,y) == 3:
                        pass
                    elif tmpBoard.getTileByIndex(i,y) == 0:
                        tmpBoard.setTileByIndex(i, y, 2)
                        if y + 1 <= self.boardWidth:
                            tmpBoard.setTileByIndex(i, y + 1, 2)
                        if y != 0:
                            tmpBoard.setTileByIndex(i, y - 1, 2)
                        break
                    else:
                        if tmpBoard.getTileByIndex(i + 1, y) == 3 and tmpBoard.getTileByIndex(i, y) == 2:
                            if y + 1 <= self.boardWidth:
                                tmpBoard.setTileByIndex(i, y + 1, 2)
                            if y != 0:
                                tmpBoard.setTileByIndex(i, y - 1, 2)
                        break

            for i in range(y + 1, self.boardWidth):
                if tmpBoard.getTileByIndex(x,i) == 3:
                    pass
                elif tmpBoard.getTileByIndex(x,i) == 0:
                    tmpBoard.setTileByIndex(x, i, 2)
                    if x + 1 <= self.boardWidth:
                        tmpBoard.setTileByIndex(x+1, i, 2)
                    if y != 0:
                        tmpBoard.setTileByIndex(x-1, i, 2)
                    break
                else:
                    if tmpBoard.getTileByIndex(x, i-1) == 3 and tmpBoard.getTileByIndex(x, i) == 2:
                        if x + 1 <= self.boardWidth:
                            tmpBoard.setTileByIndex(x + 1, i, 2)
                        if y != 0:
                            tmpBoard.setTileByIndex(x - 1, i, 2)
                    break
            if y == 1:
                if tmpBoard.getTileByIndex(x, 0) == 0:
                    tmpBoard.setTileByIndex(x, 0, 2)
            else:
                for i in range(y - 1, -1, -1):
                    if tmpBoard.getTileByIndex(x,i) == 3:
                        pass
                    elif tmpBoard.getTileByIndex(x,i) == 0:
                        tmpBoard.setTileByIndex(x, i, 2)
                        if x + 1 <= self.boardWidth:
                            tmpBoard.setTileByIndex(x + 1, i, 2)
                        if y != 0:
                            tmpBoard.setTileByIndex(x - 1, i, 2)
                        break
                    else:
                        if tmpBoard.getTileByIndex(x, i + 1) == 3 and tmpBoard.getTileByIndex(x, i) == 2:
                            if x + 1 <= self.boardWidth:
                                tmpBoard.setTileByIndex(x + 1, i, 2)
                            if y != 0:
                                tmpBoard.setTileByIndex(x - 1, i, 2)
                        break

    def addPlayer(self, playerName):
        #Create a new player with a board
        board = Board()
        board.init(self.windowSurface, self.boardWidth, self)

        player = Player()
        player.init(playerName, False, board)

        self.players[playerName] = player

    def setPlayerReady(self, playerName, isReady):
        self.players[playerName].isReady = isReady

    # Player should be a string
    def setActivePlayer(self, player):
        self.activePlayer = player
        self.activeBoard = self.players[player].board

    # Player should be a string
    def setTurnPlayer(self, player):
        self.turnPlayer = player

        if self.turnPlayer == self.client.username:
            #Reset the hasBeenShot field
            for player in self.players.keys():
                self.players[player].hasBeenShot = False

    def killPlayer(self, player):
        self.players[player].isAlive = False

    def setWinnerStr(self, winner):
        if winner == self.client.username:
            self.winnerStr = "YOU WIN!"
        else:
            self.winnerStr = winner + " WON!"

    def removePlayer(self, playerName):
        self.players.pop(playerName, None)
        #Just to be safe
        self.setActivePlayer(self.client.username)