class Player:
    def init(self, name, isHost, isReady, keepAliveTime, board, shipCount):
        self.name = name
        self.isHost = isHost
        self.isReady = isReady
        self.keepAliveTime = keepAliveTime
        self.board = board
        self.connected = True
        #for checking win and loss condition
        self.isAlife = True
        self.shipsRemaining = shipCount

        #TODO: Manage this with done moves so rejoining players can be given their data
        self.otherBoards = {}

        #TODO: update this when restarting
        def setShipsRemaining(self, ships):
            self.shipsRemaining = ships