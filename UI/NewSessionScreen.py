from Assets import *
from Util import *
import random
from external import eztext

class NewSessionScreen:

    def init(self, client, windowSurface):
        self.client = client
        self.windowSurface = windowSurface

        self.tinyFont = tinyFont
        self.smallFont = smallFont
        self.mediumFont = mediumFont
        self.largeFont = largeFont

        self._availableSizes = [8, 10, 12]


    def update(self, events):

        if escapePressed(events):
            self.client.loadSessionSelectScreen()

        #NEW SESSION
        newSessionText = self.largeFont.render("Creating a new session", True, COLOR_BLACK)
        newSessionTextRect = newSessionText.get_rect()
        newSessionTextRect.left = 40
        newSessionTextRect.top = 40
        newSessionRect = self.windowSurface.blit(newSessionText, newSessionTextRect)

        #EXISTING SESSIONS
        sizeText = self.mediumFont.render("Choose board size:", True, COLOR_BLACK)
        sizeTextRect = sizeText.get_rect()
        sizeTextRect.left = 40
        sizeTextRect.top = 150
        self.windowSurface.blit(sizeText, sizeTextRect)

        x = 100
        for size in self._availableSizes:
            sizeText = self.mediumFont.render(str(size) + "x" + str(size), True, COLOR_WHITE, COLOR_BLACK)
            sizeTextRect = sizeText.get_rect()
            sizeTextRect.centerx = x
            sizeTextRect.centery = 200
            x += 100

            sizeRect = self.windowSurface.blit(sizeText, sizeTextRect)

            if clickedOnRect(sizeRect, events):
                print "Clicked on " + str(size) + " size"
                sessionName = "Session " + str(random.randrange(0, 100000000))
                self.client.sessionName = sessionName
                success = self.client.createSession(sessionName, size, self.client.username)
                if(success):
                    self.client.loadSetupShipsScreen(size)
                else:
                    print "Something went wrong creating a session."
