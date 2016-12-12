import pika, threading, time, traceback, sys

from commons import createRPCListener
from types import MethodType

#TODO: Make shared with Board.py
TILE_EMPTY = 0
TILE_SHIP = 1
TILE_MISS = 2
TILE_SHIP_HIT = 3

class Session(threading.Thread):
    def __init__(self, server, name, boardWidth):
        threading.Thread.__init__(self)
        self.server = server
        self.name = name
        self.prefix = server +"." + name
        self.lock = threading.Lock()
        self.updateChannel = None
        self.connections = []

        self.players = {}
        self.order = []
        self.boardWidth = boardWidth
        self.boards = {}
        self.playerReady = {}
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
                self.players[name] = time.time()
                self.playerReady[name] = False
                self.boards[name] = [[0 for i in range(self.boardWidth)] for j in range(self.boardWidth)]
                self.order.append(name)
                #TODO: This should be sent as the argument in server.py
                self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                                 routing_key='',
                                                 body="NEWPLAYER:%s"%name)
                return True

    def initChannels(self):
        with self.lock:
            self.updateConnection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            self.updateChannel = self.updateConnection.channel()
            self.updateChannel.exchange_declare(exchange=self.prefix + 'updates',type='fanout')
            self.connections.append(self.updateConnection)

            self.kickPlayerListener = MethodType(createRPCListener(self, 'rpc_kick_player', self.placeShipCallback), self, Session)
            self.kickPlayer = threading.Thread(target=self.kickPlayerListener)

            self.placeShipListener = MethodType(createRPCListener(self,'rpc_place_ship',self.kickPlayerCallback), self, Session)
            self.placeship = threading.Thread(target=self.placeShipListener)

            self.bombShipListener = MethodType(createRPCListener(self,'rpc_bomb',self.bombShipCallback), self, Session)
            self.bombship = threading.Thread(target=self.bombShipListener)

            self.gameStartListener = MethodType(createRPCListener(self,'rpc_start',self.gameStartCallback), self, Session)
            self.gamestart = threading.Thread(target=self.gameStartListener)

            self.finishedPlacingListener = MethodType(createRPCListener(self,'rpc_finished_placing',self.finishedPlacingCallback), self, Session)
            self.finishedPlacing = threading.Thread(target=self.finishedPlacingListener)

            self.kickPlayer.start()
            self.placeship.start()
            self.bombship.start()
            self.gamestart.start()
            self.finishedPlacing.start()

    def kickPlayerCallback(self, request):
        print(" [.] kickPlayer(%s)" % request)

        #TODO: Kick player
        return "", ""


    def finishedPlacingCallback(self,request):
        print( "[S] finishedPlacingCallback(%s)" % request)
        name, ships = request.split(':')

        success = self.placeShips(name, ships.split("|"))
        if success:
            self.playerReady[name] = True
            self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                             routing_key='',
                                             body="READY:%s" % name)
            return "OK", "READY2:" + name
        else:
            return "FAIL", ""

    def placeShips(self, name, ships):
        print(ships)
        try:
            board = self.boards[name]

            for ship in ships:
                print(ship)
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
        if self.fields[player][y][x] == 1:
            return "HIT"
        return "MISS"

    def sunk(self,x,y,player):
        #TODO lisada juurde et kas on laev loppenud voi mitte
        for i in range(x-1,0,-1):
            if self.fields[player][y][x] == 1:
                return False

        for i in range(x+1,self.fieldSize[0]):
            if self.fields[player][y][x] == 1:
                return False

        for i in range(y-1,0,-1):
            if self.fields[player][y][x] == 1:
                return False

        for i in range(y+1):
            if self.fields[player][y][x] == 1:
                return False
        return True

    def bombShipCallback(self,request):
        x, y, player, attacker = request.slit(":")

        print(" [.] bomb(%s,%s, %s)" %x,y,player)
        response = self.checkHit(int(x),int(y),player,attacker)

        #TODO teha paremaks ja lisada juurde laeva edastamine koigile
        if self.sunk(int(x),int(y),player):
            message = ":".join(["SUNK",x,y,player])
        else:
            message = ":".join(["BOMB",response,player,x,y])

        #TODO see kuidagi teisiti vb handlida
        self.shots -= 1
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

    def __placeShipOnField(self,x,y,dir,name):
        self.fields[name][y][x] = 1
        #Something something direction

    def placeShipCallback(self, request):
        x, y, dir, name = request.split(":")
        print(" [.] place(%s)" % name)
        self.__placeShipOnField(int(x),int(y),dir,name)
        response = "OK"

        return response, ""

    def gameStartCallback(self,request):
        #TODO: Possibly validate if the request sender is the host
        print("Starting the game")
        if self.state == "INIT":
            self.state = "PLAY"

            self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                             routing_key='',
                                             body="START")

            return "OK",""
        else:
            return "FAIL",""