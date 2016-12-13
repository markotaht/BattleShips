class Player:
    def init(self, name, isReady, board):
        self.name = name
        self.isReady = isReady
        self.board = board
        self.connected = True
        #For checking if this player has been shot by the local player during a particular turn
        self.hasBeenShot = False
        #for checking win and loss condition
        self.isAlife = True