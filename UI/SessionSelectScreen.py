from Assets import *
from Util import *
from external import eztext


class SessionSelectScreen:

    def init(self, ui, windowSurface):
        self.ui = ui
        self.windowSurface = windowSurface
        #TODO: Move fonts to Assets
        self.tinyFont = pygame.font.SysFont(None, 18)
        self.smallFont = pygame.font.SysFont(None, 24)
        self.mediumFont = pygame.font.SysFont(None, 36)
        self.largeFont = pygame.font.SysFont(None, 48)

        #SESSIONS LIST
        #Contains 3 element arrays - [name:string, boardSize:int, playerCount:int]
        self._sessions = []

        #mock session
        self.addSession("Mock session", 8, 0)
        self.addSession("Mock session 2", 12, 4)


    def update(self, events):

        if escapePressed(events):
            self.ui.loadMainMenuScreen()

        #NEW SESSION
        newSessionText = self.mediumFont.render("Create new session", True, COLOR_WHITE, COLOR_BLACK)
        newSessionTextRect = newSessionText.get_rect()
        newSessionTextRect.left = 40
        newSessionTextRect.top = 40
        newSessionRect = self.windowSurface.blit(newSessionText, newSessionTextRect)
        if clickedOnRect(newSessionRect, events):
            print "Creating a new session"
            #TODO: Request new session
            self.ui.loadNewSessionScreen()

        #EXISTING SESSIONS
        sessionsText = self.mediumFont.render("Available sessions:", True, COLOR_BLACK)
        sessionsTextRect = sessionsText.get_rect()
        sessionsTextRect.left = 40
        sessionsTextRect.top = 90
        self.windowSurface.blit(sessionsText, sessionsTextRect)

        y = 150

        #TODO
        #To get sessions
        #self.ui.client.getRooms("")
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
                print "Clicked on " + name + " session"
                # TODO: Join session and switch screens
                #TODO: Determine if the user is reconnecting and has a previous state
                self.ui.client.joinRoom("RoomName","Username")
                #or is starting clean
                self.ui.loadSetupShipsScreen(boardSize)


    def addSession(self, name, boardSize, playerCount):
        self._sessions.append([name, boardSize, playerCount]);
