class Player:
    def init(self, name, isHost, isReady, keepAliveTime, board):
        self.name = name
        self.isHost = isHost
        self.isReady = isReady
        self.keepAliveTime = keepAliveTime
        self.board = board
        self.connected = True