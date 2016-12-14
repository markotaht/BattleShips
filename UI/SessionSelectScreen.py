from Assets import *
from Util import *
from external import eztext
from Board import Board
from Player import Player

class SessionSelectScreen:

    def init(self, client, windowSurface):
        self.client = client
        self.windowSurface = windowSurface

        self.tinyFont = tinyFont
        self.smallFont = smallFont
        self.mediumFont = mediumFont
        self.largeFont = largeFont

        #SESSIONS LIST
        #Contains 4 element arrays - [name:string, boardSize:int, playerCount:int, state:string]
        self._sessions = []
        self._refreshSessions()
        self.joinFailText = ""

        #mock session
        #self.addSession("Mock session", 8, 0)
        #self.addSession("Mock session 2", 12, 4)


    def update(self, events):

        if escapePressed(events):
            self.client.loadMainMenuScreen()

        #NEW SESSION
        newSessionText = self.mediumFont.render("Create new session", True, COLOR_WHITE, COLOR_BLACK)
        newSessionTextRect = newSessionText.get_rect()
        newSessionTextRect.left = 40
        newSessionTextRect.top = 40
        newSessionRect = self.windowSurface.blit(newSessionText, newSessionTextRect)
        if clickedOnRect(newSessionRect, events):
            print "Creating a new session"
            #TODO: Request new session
            self.client.loadNewSessionScreen()

        #EXISTING SESSIONS
        sessionsText = self.mediumFont.render("Available sessions:", True, COLOR_BLACK)
        sessionsTextRect = sessionsText.get_rect()
        sessionsTextRect.left = 40
        sessionsTextRect.top = 90
        self.windowSurface.blit(sessionsText, sessionsTextRect)

        #REFRESH BUTTON
        refreshText = self.mediumFont.render("REFRESH", True, COLOR_WHITE, COLOR_BLACK)
        refreshTextRect = refreshText.get_rect()
        refreshTextRect.right = 600
        refreshTextRect.bottom = 440
        refreshRect = self.windowSurface.blit(refreshText, refreshTextRect)
        if clickedOnRect(refreshRect, events):
            self._refreshSessions()


        y = 150
        if len(self._sessions) == 0:
            # no sessions
            sessions = [["No sessions found", 0, 0, ""]]
        else:
            sessions = self._sessions

        for session in sessions:
            name = session[0]
            boardSize = session[1]
            playerCount = session[2]
            state = session[3]

            nameText = self.smallFont.render(name, True, COLOR_BLACK)
            nameTextRect = nameText.get_rect()
            nameTextRect.left = 60
            nameTextRect.centery = y

            #Contains the other 3 fields
            otherText = self.smallFont.render(str(boardSize)
                        + "x" + str(boardSize) + "        " + str(playerCount) + "         " + state
                        + " players", True, COLOR_BLACK)
            otherTextRect = otherText.get_rect()
            otherTextRect.right = 460
            otherTextRect.centery = y

            y += 35

            sessionRect = self.windowSurface.blit(nameText, nameTextRect)
            otherRect = self.windowSurface.blit(otherText, otherTextRect)

            joinFailError = self.smallFont.render(self.joinFailText, True, COLOR_WHITE,
                                                   COLOR_BLACK)
            joinFailErrorRect = joinFailError.get_rect()
            joinFailErrorRect.left = 50
            joinFailErrorRect.top = 380
            self.windowSurface.blit(joinFailError, joinFailErrorRect)

            if clickedOnRect(sessionRect, events) or clickedOnRect(otherRect, events):
                if name != "No sessions found":
                    print "Clicked on " + name + " session"
                    #TODO: Determine if the user is reconnecting and has a previous state
                    self.client.sessionName = name
                    response = self.client.joinSession(name, self.client.username)

                    print "Server responded with %s" % response

                    if(response.startswith("FAIL") == False):
                        split = response.split(':')
                        if response.startswith("WELCOMEBACK"):
                            #Rejoining on game screen only (setup ships rejoin just overwrites the player)
                            #Definitely not a host anymore
                            isHost = False
                            isGameStarted = True

                            #third element should contain board width
                            boardWidth = int(split[2])
                            print "boardwidth is " + str(boardWidth)

                            #fourth element should contain the player's board
                            boardData = split[3]
                            print "local board data is " + boardData

                            board = Board()
                            board.init(self.windowSurface, boardWidth, self)

                            for i in range(0, len(boardData)):
                                x = i / boardWidth
                                y = i % boardWidth
                                #print "Setting " + str(x) + " " + str(y) + " to " + str(boardData[i])
                                board.setTileByIndex(x, y, int(boardData[i]))

                            players = { }
                            localPlayer = Player()
                            localPlayer.init(self.client.username, True, board)
                            players[self.client.username] = localPlayer

                            #Fifth element should contain whose turn it is
                            whoseTurn = split[4]

                            #Sixth element should contain the already connected users
                            playerData = split[5].split(";")
                            print(playerData)
                            for i in range(0, len(playerData), 3):
                                playerName = playerData[i]
                                playerConnected = playerData[i + 1] == 'True'
                                playerBoardData = playerData[i + 2]
                                print "other player board data is " + playerBoardData
                                otherBoard = Board()
                                otherBoard.init(self.windowSurface, boardWidth, self)
                                for i in range(0, len(playerBoardData)):
                                    x = i / boardWidth
                                    y = i % boardWidth
                                    otherBoard.setTileByIndex(x, y, int(playerBoardData[i]))

                                player = Player()
                                player.init(playerName, False, otherBoard)
                                players[playerName] = player

                                players[playerName].connected = playerConnected
                                players[playerName].isReady = True

                            self.client.loadGameScreen(board, isHost, isGameStarted, players)
                            self.client.screen.setTurnPlayer(whoseTurn)


                        elif response.startswith("WELCOME"):
                            #New player/Rejoining on ship placement

                            #Third element should be true if the client is host
                            isHost = split[2] == 'True'

                            #TODO: Determine to go ingame or start from setup ships screen
                            self.client.loadSetupShipsScreen(boardSize, isHost)

                            #Fourth element should contain the already connected users
                            playerData = split[3].split(";")
                            print(playerData)
                            for i in range(0, len(playerData), 2):
                                playerName = playerData[i]
                                playerReady = playerData[i + 1] == 'True'
                                self.client.screen.addPlayer(playerName)
                                self.client.screen.setPlayerReady(playerName, playerReady)


                    else:
                        print("Unable to join the session")
                        error = response.split(":")[2]
                        if error == "INVALIDSESSION":
                            self.joinFailText = "Tried to join invalid session."
                        elif error == "NAMEINUSE":
                            self.joinFailText = "Your name is already in use and active in that session."
                        elif error == "GAMESTARTED":
                            self.joinFailText = "Unable to join, game already started."
                        else:
                            self.joinFailText = "Unknown error occured when trying to join session."




    def _refreshSessions(self):
        data = self.client.getSessions("").split(":")
        if len(data) <= 1:
            return
        self._sessions = []
        for i in range(0, len(data), 4):
            name = data[i]
            boardWidth = int(data[i + 1])
            players = data[i + 2]
            state = data[i + 3]
            self._addSession(name, boardWidth, players, state)

    def _addSession(self, name, boardSize, playerCount, state):
        if state == "INIT":
            state = "Setup"
        elif state == "PLAY":
            state = "Playing"
        self._sessions.append([name, boardSize, playerCount, state]);
