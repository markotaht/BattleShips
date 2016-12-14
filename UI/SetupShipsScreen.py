from Player import Player
from Board import *

class SetupShipsScreen:

    def init(self, client, windowSurface, boardWidth, isHost):
        self.client = client
        self.windowSurface = windowSurface
        self.boardWidth = boardWidth
        self.isHost = isHost
        self.tinyFont = tinyFont
        self.smallFont = smallFont
        self.mediumFont = mediumFont
        self.largeFont = largeFont

        self.players = {}
        self.playerReady = {}

        self.clear()

        #Also create a player for the local client since SetupShipsScreen doesn't do it
        localPlayer = Player()
        localPlayer.init(self.client.username, True, self.board)
        self.players[self.client.username] = localPlayer

    def clear(self):
        self.board = Board()
        self.board.init(self.windowSurface, self.boardWidth, self)

        #Contains arrays in the form[shipSize, amount]
        self._availableShips = []
        #Contains arrays in the form[shipStartX:int, shipStartY:int, vertical:boolean, shipLength:int]
        self._placedShips = []
        self._verticalPlacement = True

        #when changing this also update session.getShipCount
        if self.boardWidth == 4:
            self._selectedSize = 2
            self._availableShips.append([2, 2]);
            self._availableShips.append([1, 2]);
        elif self.boardWidth == 6:
            self._selectedSize = 3
            self._availableShips.append([3, 1]);
            self._availableShips.append([2, 1]);
            self._availableShips.append([1, 2]);
        elif self.boardWidth == 8:
            self._selectedSize = 4
            self._availableShips.append([4, 1]);
            self._availableShips.append([3, 1]);
            self._availableShips.append([2, 2]);
            self._availableShips.append([1, 3]);
        elif self.boardWidth == 10:
            self._selectedSize = 5
            self._availableShips.append([5, 1]);
            self._availableShips.append([4, 1]);
            self._availableShips.append([3, 2]);
            self._availableShips.append([2, 3]);
            self._availableShips.append([1, 4]);
        elif self.boardWidth == 12:
            self._selectedSize = 6
            self._availableShips.append([6, 1]);
            self._availableShips.append([5, 1]);
            self._availableShips.append([4, 2]);
            self._availableShips.append([3, 3]);
            self._availableShips.append([2, 4]);
            self._availableShips.append([1, 5]);
        else:
            print "Warning! Unsupported board size."

        if self.client.username in self.players:
            self.players[self.client.username].board = self.board

    def update(self, events):

        #if escapePressed(events):
            #TODO: Handle

        #disconnect button
        disconnectText = self.mediumFont.render("Disconnect", True, COLOR_WHITE, COLOR_BLACK)
        disconnectTextRect = disconnectText.get_rect()
        disconnectTextRect.left = 300
        disconnectTextRect.top = 10
        self.windowSurface.blit(disconnectText, disconnectTextRect)
        if clickedOnRect(disconnectTextRect, events):
            print("Disconnect placeholder...")

        #SETUP SHIPS TEXT
        setupShipsText = self.mediumFont.render("Setup your ships:", True, COLOR_BLACK)
        setupShipsTextRect = setupShipsText.get_rect()
        setupShipsTextRect.left = 10
        setupShipsTextRect.top = 10
        self.windowSurface.blit(setupShipsText, setupShipsTextRect)

        y = 90
        for ship in self._availableShips:
            shipSize = ship[0]
            shipAmount = ship[1]

            if shipSize == self._selectedSize:
                color = COLOR_GREEN
            else:
                color = COLOR_WHITE

            shipText = self.largeFont.render(u'\ua258'*shipSize + " x" + str(shipAmount), True, COLOR_BLACK, color)
            shipTextRect = shipText.get_rect()
            shipTextRect.right = 190
            shipTextRect.centery = y
            y += 40

            shipRect = self.windowSurface.blit(shipText, shipTextRect)

            if clickedOnRect(shipRect, events):
                self._selectedSize = shipSize

        #SHIP ROTATION TEXT
        if self._verticalPlacement:
            text = "Placing vertically"
        else:
            text = "Placing horizontally"

        rotationText = self.mediumFont.render(text, True, COLOR_WHITE, COLOR_BLACK)
        rotationTextRect = rotationText.get_rect()
        rotationTextRect.left = 10
        rotationTextRect.top = 350
        rotationRect = self.windowSurface.blit(rotationText, rotationTextRect)

        if clickedOnRect(rotationRect, events):
            self._verticalPlacement = not self._verticalPlacement

        #CLEAR BOARD TEXT
        clearText = self.mediumFont.render("Clear board", True, COLOR_WHITE, COLOR_BLACK)
        clearTextRect = clearText.get_rect()
        clearTextRect.left = 10
        clearTextRect.top = 400
        clearRect = self.windowSurface.blit(clearText, clearTextRect)

        if clickedOnRect(clearRect, events):
            self.clear()

        #ALL SHIPS PLACED
        if len(self._availableShips) == 0:
            continueText = self.mediumFont.render("Continue", True, COLOR_WHITE, COLOR_BLACK)
            continueTextRect = continueText.get_rect()
            continueTextRect.left = 50
            continueTextRect.top = 220
            continueRect = self.windowSurface.blit(continueText, continueTextRect)

            if clickedOnRect(continueRect, events):
                print "Ships placed"
                #TODO: pass self._placedShips
                #TODO correction: After every ship is placed info needs to be given to server

                placedShips = ""
                for ship in self._placedShips:
                    placedShips += str(ship[0]) + ";" + str(ship[1]) + ";" + str(ship[2]) + ";" + str(ship[3]) + "|"

                #Remove extra | from end
                placedShips = placedShips[:-1]

                response = self.client.finishedPlacing(self.client.username, placedShips)
                print "Response: %s" % response

                if(response.startswith("FAIL") == False):
                    self.client.loadGameScreen(self.board, self.isHost, False, self.players)
                else:
                    print "Server rejected ship placement."


        self.board.update(events)

    #Called by the board whenever there's a click
    def onBoardClick(self, tileX, tileY):
        #print str(tileX) + " " + str(tileY)
        success = self.tryPlaceShip(tileX, tileY)

        if success:
            placedSize = self._selectedSize
            # Reduce the selected ship amount
            for ship in self._availableShips:
                shipSize = ship[0]
                shipAmount = ship[1]

                if shipSize == self._selectedSize:
                    if shipAmount == 1:
                        #Remove this size ships altogether
                        self._availableShips.remove(ship)
                        self._selectedSize = 0
                    else:
                        ship[1] = shipAmount - 1
                    #automatically take next shipsize if no ships left
                    if self._selectedSize == 0:
                        if len(self._availableShips) > 0:
                            self._selectedSize = self._availableShips[0][0]

            self._placedShips.append([tileX, tileY, self._verticalPlacement, placedSize])
            #Siin vist lisada
            #self.client.placeShip(x,y,dir,"ME")


    def tryPlaceShip(self, tileX, tileY):
        #TODO: Also check surroundings for conflicting ships
        shipSize = self._selectedSize
        if self._verticalPlacement == False:
            if tileX > self.boardWidth - shipSize:
                #The ship would be out of bounds
                return False

            #Check if the area around the ship is free
            for x in range(tileX - 1, tileX + shipSize + 1):
                for y in range(tileY - 1, tileY + 2):
                    if x < 0 or y < 0 or x >= self.boardWidth or y >= self.boardWidth:
                        #Out of range, can skip these tiles
                        continue
                    if self.board.getTileByIndex(x, y) != TILE_EMPTY:
                        return False

            #If this is reached, can place the ship
            for i in range(tileX, tileX + shipSize):
                self.board.setTileByIndex(i, tileY, TILE_SHIP)
        else:
            if tileY > self.boardWidth - shipSize:
                #The ship would be out of bounds
                return False

            #Check if the area around the ship is free
            for x in range(tileX - 1, tileX + 2):
                for y in range(tileY - 1, tileY + + shipSize + 1):
                    if x < 0 or y < 0 or x >= self.boardWidth or y >= self.boardWidth:
                        #Out of range, can skip these tiles
                        continue
                    if self.board.getTileByIndex(x, y) != TILE_EMPTY:
                        return False

            #If this is reached, can place the ship
            for i in range(tileY, tileY + shipSize):
                self.board.setTileByIndex(tileX, i, TILE_SHIP)
        return True


    def addPlayer(self, playerName):
        #Create a new player with a board
        board = Board()
        board.init(self.windowSurface, self.boardWidth, self)

        player = Player()
        player.init(playerName, False, board)

        self.players[playerName] = player

    def setPlayerReady(self, playerName, isReady):
        self.players[playerName].isReady = isReady