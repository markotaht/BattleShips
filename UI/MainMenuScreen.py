from Assets import *
from Util import *
from external import eztext
import random


class MainMenuScreen:

    def init(self, client, windowSurface):
        self.client = client
        self.windowSurface = windowSurface

        self.tinyFont = tinyFont
        self.smallFont = smallFont
        self.mediumFont = mediumFont
        self.largeFont = largeFont
        self.updateCounter = 0

        y = 0

        #TITLE
        self._titleText = self.largeFont.render('Naval Warfare Simulator', True, COLOR_WHITE, COLOR_BLACK)
        self._titleTextRect = self._titleText.get_rect()
        self._titleTextRect.centerx = self.windowSurface.get_rect().centerx
        self._titleTextRect.centery = self._titleTextRect.height
        y += self._titleTextRect.height

        #NAME INPUT
        self._nameTextBox = eztext.Input(maxlength=20, color=COLOR_BLACK,
                                         x = 200, y = y + 50, prompt='Your name: ',
                                         font = self.mediumFont)
        self._nameTextBox.focus = True
        y += 50

        #SERVER LIST
        #Contains 2 element arrays - [name:string, MQaddress:string]
        self._servers = []

        self._serversTitleText = self.mediumFont.render('Available servers (Click to join):', True, COLOR_BLACK)
        self._serversTitleTextRect = self._serversTitleText.get_rect()
        self._serversTitleTextRect.left = 40
        self._serversTitleTextRect.centery = 150

    def update(self, events):
        self.updateCounter += 1

        # TITLE
        self.windowSurface.blit(self._titleText, self._titleTextRect)

        #NAME INPUT
        self._updateNameInput(events)

        #SERVER LIST
        self._updateServerList(events)

    def _updateNameInput(self, events):
        value = self._nameTextBox.update(events)

        #If it doesn't return None, finished editing
        if value:
            print(value)
            self._nameTextBox.focus = False
            self._nameTextBox.color = COLOR_BLACK
            self.client.username = value;

        # Blink every 500ms at 30FPS
        if self._nameTextBox.focus and self.updateCounter % 15 == 0:
            if self._nameTextBox.color == COLOR_BLACK:
                self._nameTextBox.color = COLOR_DARK_GREY
            else:
                self._nameTextBox.color = COLOR_BLACK

        self._nameTextBox.draw(self.windowSurface)

        if clickedOnRect(self._nameTextBox.rect, events):
            self._nameTextBox.focus = True
        else:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    #User did click somewhere but it's not on the name box - remove focus from it
                    if hasattr(self, 'name') == False:
                        if(len(self._nameTextBox.value) > 0):
                            self.client.username = self._nameTextBox.value
                        else:
                            self.client.username = "Player " + str(random.randrange(0, 10000))
                    self._nameTextBox.focus = False
                    self._nameTextBox.color = COLOR_BLACK
                    break


    def _updateServerList(self, events):
        #Available servers text
        self.windowSurface.blit(self._serversTitleText, self._serversTitleTextRect)

        #The servers themselves
        y = 190

        if len(self._servers) == 0:
            #no servers
            servers = [["No servers found.", 0]]
        else:
            servers = self._servers

        self._serverTexts = []
        for server in servers:
            serverName = server[0]
            serverAddress = server[1]
            serverText = self.smallFont.render(serverName + " (" + serverAddress + ")", True, COLOR_BLACK)
            serverTextRect = serverText.get_rect()
            serverTextRect.left = 70
            serverTextRect.centery = y
            y += 35

            serverButtonRect = self.windowSurface.blit(serverText, serverTextRect)

            if clickedOnRect(serverButtonRect, events):
                if self.client.username == "__me__":
                    #Not allowed name
                    self.client.username = "DefaultName"

                #TODO: Connect and switch screens
                success = self.client.connect(serverName, serverAddress)
                if success:
                    self.client.loadSessionSelectScreen()
                else:
                    print("Failed to connect to the server. Should display an error message.")


    def clearServers(self):
        self._servers = []

    #name and mqAddress both expected to be strings
    def addServer(self, name, mqAddress):
        self._servers.append([name, mqAddress]);
