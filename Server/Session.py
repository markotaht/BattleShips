import pika, threading, time, traceback, sys

from commons import createRPCListener
from types import MethodType
from Player import Player

#TODO: Make shared with Board.py
TILE_EMPTY = 0
TILE_SHIP = 1
TILE_MISS = 2
TILE_SHIP_HIT = 3

class Session(threading.Thread):
    def __init__(self, server, sessionName, hostName, boardWidth):
        threading.Thread.__init__(self)
        self.server = server
        self.name = sessionName
        self.hostName = hostName
        self.prefix = server +"." + sessionName
        self.lock = threading.Lock()
        self.updateChannel = None
        self.connections = []

        self.players = {}
        self.order = []
        self.boardWidth = boardWidth
        self.dead = []
        self.state = "INIT"
        self.playerturn = 0
        self.shots = 0

        self.initChannels()

    def addPlayer(self, name):
        with self.lock:
            #TODO: Comment back in once we have proper disconnect handling
            #if name in self.players:
            #    return False
            #else:
                board = [[0 for i in range(self.boardWidth)] for j in range(self.boardWidth)]
                isHost = name == self.hostName
                keepAliveTime = time.time()

                player = Player()
                player.init(name, isHost, False, keepAliveTime, board)

                self.players[name] = player
                self.order.append(name)

                #TODO: This should be sent as the argument in server.py
                self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                                 routing_key='',
                                                 body="NEWPLAYER:%s"%name)
                return True


    def run(self):
        while 1:
            #Check keepalive values for players and mark players as not ready if it is 20 seconds old
            for playerName in self.players:
                player = self.players[playerName]
                if player != 0:
                    if float(player.keepAliveTime) + 20 < float(time.time()):
                        if player.connected:
                            print "Old keepalive for player", player.keepAliveTime
                            print "Marking player as disconnected"
                            #TODO:
                            player.connected = False

                            self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                                             routing_key='',
                                                             body="DISCONNECTED:%s" % playerName)

            time.sleep(1) #check only every second

    def initChannels(self):
        with self.lock:
            self.updateConnection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            self.updateChannel = self.updateConnection.channel()
            self.updateChannel.exchange_declare(exchange=self.prefix + 'updates',type='fanout')
            self.connections.append(self.updateConnection)

            self.kickPlayerListener = MethodType(createRPCListener(self, 'rpc_kick_player', self.kickPlayerCallback), self, Session)
            self.kickPlayer = threading.Thread(target=self.kickPlayerListener)

            self.bombShipListener = MethodType(createRPCListener(self,'rpc_bomb',self.bombShipCallback), self, Session)
            self.bombship = threading.Thread(target=self.bombShipListener)

            self.gameStartListener = MethodType(createRPCListener(self,'rpc_start',self.gameStartCallback), self, Session)
            self.gamestart = threading.Thread(target=self.gameStartListener)

            self.finishedPlacingListener = MethodType(createRPCListener(self,'rpc_finished_placing',self.finishedPlacingCallback, True), self, Session)
            self.finishedPlacing = threading.Thread(target=self.finishedPlacingListener)

            self.keepAliveListener = MethodType(createRPCListener(self, 'rpc_update_keep_alive', self.updateKeepAlive), self, Session)
            self.keepAliveListener = threading.Thread(target = self.keepAliveListener)

            self.runThread = threading.Thread(target = self.run)

            self.kickPlayer.start()
            self.bombship.start()
            self.gamestart.start()
            self.finishedPlacing.start()
            self.keepAliveListener.start()
            self.runThread.start()

    def kickPlayerCallback(self, request):
        print(" [.] kickPlayer(%s)" % request)

        #TODO: Kick player
        return "", ""


    def finishedPlacingCallback(self,request):
        print( "[S] finishedPlacingCallback(%s)" % request)
        name, ships = request.split(':')

        success = self.placeShips(name, ships.split("|"))
        if success:
            self.players[name].isReady = True
            #TODO: Is this still needed?
            self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                             routing_key='',
                                             body="READY:%s" % name)
            print "Session - %s is ready"%name
            return "OK", "READY:" + name
        else:
            return "FAIL", ""

    def placeShips(self, name, ships):
        print(ships)
        try:
            board = self.players[name].board

            for ship in ships:
                ship = ship.split(";")
                tileX = int(ship[0])
                tileY = int(ship[1])
                vertical = bool(ship[2])
                shipSize = int(ship[3])

                if vertical == False:
                    if tileX > self.boardWidth - shipSize:
                        return False

                    # Check if the area around the ship is free
                    for x in range(tileX - 1, tileX + shipSize + 1):
                        for y in range(tileY - 1, tileY + 2):
                            if x < 0 or y < 0 or x >= self.boardWidth or y >= self.boardWidth:
                                # Out of range, can skip these tiles
                                continue
                            if board[x][y] != TILE_EMPTY:
                                return False

                    # If this is reached, can place the ship
                    for i in range(tileX, tileX + shipSize):
                        board[i][tileY] = TILE_SHIP
                else:
                    if tileY > self.boardWidth - shipSize:
                        # The ship would be out of bounds
                        return False

                    # Check if the area around the ship is free
                    for x in range(tileX - 1, tileX + 2):
                        for y in range(tileY - 1, tileY + + shipSize + 1):
                            if x < 0 or y < 0 or x >= self.boardWidth or y >= self.boardWidth:
                                # Out of range, can skip these tiles
                                continue
                            if board[x][y] != TILE_EMPTY:
                                return False

                    # If this is reached, can place the ship
                    for i in range(tileY, tileY + shipSize):
                        board[tileX][i] = TILE_SHIP


        except ValueError:
            traceback.print_exc(file=sys.stdout)
            return False
        except KeyError:
            traceback.print_exc(file=sys.stdout)
            return False

        return True


    def checkHit(self,x,y,player):
        if self.players[player].board[x][y] == 1:
            self.players[player].board[x][y] = 3
            return "HIT"
        return "MISS"

    def sunk(self,x,y,player):
        #TODO kui server hakkab ka misse hoidma siis peab seda t2iendama
        tmpBoard = self.players[player].board

        #check if ship on x+
        for i in range(x+1, self.boardWidth):
            if tmpBoard[i][y] == 1:
                return False #Return false if we find ship
            elif tmpBoard[i][y] == 0:
                break #dont continue if nothing there

        for i in range(x-1, 0, -1):
            if tmpBoard[i][y] == 1:
                return False
            elif tmpBoard[i][y] == 0:
                break


        for i in range(y+1, self.boardWidth):
            if tmpBoard[x][i] == 1:
                return False
            elif tmpBoard[x][i] == 0:
                break

        for i in range(y-1, 0, -1):
            if tmpBoard[x][i] == 1:
                return False
            elif tmpBoard[x][i] == 0:
                break

        return True

    def bombShipCallback(self,request):
        print request
        x, y, player, attacker = request.split(":")

        print(" [.] bomb(%s,%s, %s, %s)" %(x,y,player, attacker))
        response = self.checkHit(int(x),int(y),player)
        print response

        if response == "MISS":
            self.shots -= 1

        #TODO teha paremaks ja lisada juurde laeva edastamine koigile
        if response == "HIT" and self.sunk(int(x),int(y),player):
            message = ":".join(["SUNK",player, attacker,x,y])
            response = "SUNK"
        else:
            message = ":".join(["BOMB",player,attacker,x,y,response])

        #TODO this should be sent by the super global message thing
        self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                         routing_key='',
                                         body=message)

        print "SERVER - message:", message
        print "Shots remaining:", self.shots
        # TODO see kuidagi teisiti vb handlida
        if self.shots == 0:
            self.notifyNextPlayer()

        return response, message

    def notifyNextPlayer(self):
        message = ":".join(["NEXT",self.order[self.playerturn]])
        self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                         routing_key='',
                                         body=message)
        self.playerturn = (self.playerturn+1)%len(self.order)
        self.shots = len(self.order)-1
        print "%s's turn"%self.order[self.playerturn]

    def gameStartCallback(self,request):
        #TODO: Possibly validate if the request sender is the host
        print("Starting the game")
        if self.state == "INIT":
            self.state = "PLAY"
            #set number of shots
            self.shots = len(self.order)-1

            self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                             routing_key='',
                                             body="START")
            #Also notify that host is first
            #TODO actually not working and can be skipped as host is first?
            message = ":".join(["NEXT", self.order[0]])
            print ""
            self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                             routing_key='',
                                             body=message)
            print "%s's turn" % self.order[self.playerturn]

            return "OK",""
        else:
            return "FAIL",""

    def updateKeepAlive(self,request):
        name, keepalive = request.split(":")
        keepalive = float(keepalive)
        self.players[name].keepAliveTime = keepalive
        #print "New keepalive:", name
        #TODO check why it fails with OK
        #fails with ok as it does not contain :, dno why
        return "O:K", ""