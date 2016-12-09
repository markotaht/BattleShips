from Assets import *
from Util import *
from external import eztext


class SessionSelectScreen:

    def init(self, client, windowSurface):
        self.client = client
        self.windowSurface = windowSurface

        self.tinyFont = tinyFont
        self.smallFont = smallFont
        self.mediumFont = mediumFont
        self.largeFont = largeFont

        #SESSIONS LIST
        #Contains 3 element arrays - [name:string, boardSize:int, playerCount:int]
        self._sessions = []
        self._refreshSessions()

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
            sessions = [["No sessions found", 0, 0]]
        else:
            sessions = self._sessions

        for session in sessions:
            name = session[0]
            boardSize = session[1]
            playerCount = session[2]

            nameText = self.smallFont.render(name, True, COLOR_BLACK)
            nameTextRect = nameText.get_rect()
            nameTextRect.left = 60
            nameTextRect.centery = y

            #Contains the other 3 fields
            otherText = self.smallFont.render(str(boardSize)
                        + "x" + str(boardSize) + "        " + str(playerCount)
                        + " players", True, COLOR_BLACK)
            otherTextRect = otherText.get_rect()
            otherTextRect.right = 460
            otherTextRect.centery = y

            y += 35

            sessionRect = self.windowSurface.blit(nameText, nameTextRect)
            otherRect = self.windowSurface.blit(otherText, otherTextRect)

            if clickedOnRect(sessionRect, events) or clickedOnRect(otherRect, events):
                if name != "No sessions found":
                    print "Clicked on " + name + " session"
                    #TODO: Determine if the user is reconnecting and has a previous state
                    self.client.sessionName = name
                    self.client.joinSession(name, self.client.username)

                    self.client.loadSetupShipsScreen(boardSize)


    def _refreshSessions(self):
        data = self.client.getSessions("").split(":")
        self._sessions = []
        for i in range(0, len(data), 3):
            name = data[i]
            boardWidth = int(data[i + 1])
            players = data[i + 2]
            self._addSession(name, boardWidth, players)

    def _addSession(self, name, boardSize, playerCount):
        self._sessions.append([name, boardSize, playerCount]);
