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
        #TODO: Not really used?
        self.connections = []

        self.players = {}
        self.order = []
        self.boardWidth = boardWidth
        self.shipCount = self.getShipCount(boardWidth)
        self.dead = []
        self.state = "INIT"
        self.playerturn = 1
        self.shots = 0

        self.initChannels()


    def kill(self):
        for i in self.connections:
            i.close()


    def tryAddPlayer(self, name):
        with self.lock:
            if name in self.players and self.players[name].connected == True:
                return False
            else:
                self.updateChannel.basic_publish(exchange=self.prefix + 'updates', routing_key='',
                                                     body="NEWPLAYER:%s" % name)

                board = [[0 for i in range(self.boardWidth)] for j in range(self.boardWidth)]
                isHost = name == self.hostName
                keepAliveTime = time.time()


                player = Player()
                player.init(name, isHost, False, keepAliveTime, board, self.shipCount)
                self.players[name] = player
                self.order.append(name)

                #Create bombing boards
                for otherPlayer in self.players.keys():
                    if otherPlayer != name:
                        #Create a bombing board for other players to attack the joined player
                        self.players[otherPlayer].otherBoards[name] = [[0 for i in range(self.boardWidth)] for j in range(self.boardWidth)]
                        #Create a bombing board for the joined player to attack other players
                        self.players[name].otherBoards[otherPlayer] = [[0 for i in range(self.boardWidth)] for j in range(self.boardWidth)]

                return True


    def run(self):
        while 1:
            #Check keepalive values for players and mark players as not ready if it is 20 seconds old
            for playerName in self.players:
                player = self.players[playerName]
                if player != 0:
                    if float(player.keepAliveTime) + 6 < float(time.time()):
                        if player.connected:
                            print "Old keepalive for player", player.keepAliveTime
                            print "Marking player as disconnected"
                            #TODO: Pick a new host
                            player.connected = False

                            #TODO: send the player "TIMEDOUT" so if the player receives it, he can be put to main menu and stop listening

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
            self.kickPlayer.start()

            self.bombShipListener = MethodType(createRPCListener(self,'rpc_bomb',self.bombShipCallback), self, Session)
            self.bombship = threading.Thread(target=self.bombShipListener)
            self.bombship.start()

            self.gameStartListener = MethodType(createRPCListener(self,'rpc_start',self.gameStartCallback), self, Session)
            self.gamestart = threading.Thread(target=self.gameStartListener)
            self.gamestart.start()

            self.gameRestartListener = MethodType(createRPCListener(self, 'rpc_restart', self.gameRestartCallback), self, Session)
            self.gameRestart = threading.Thread(target=self.gameRestartListener)
            self.gameRestart.start()

            self.finishedPlacingListener = MethodType(createRPCListener(self,'rpc_finished_placing',self.finishedPlacingCallback, True), self, Session)
            self.finishedPlacing = threading.Thread(target=self.finishedPlacingListener)
            self.finishedPlacing.start()

            self.keepAliveListener = MethodType(createRPCListener(self, 'rpc_update_keep_alive', self.updateKeepAlive), self, Session)
            self.keepAliveListener = threading.Thread(target = self.keepAliveListener)
            self.keepAliveListener.start()

            self.leaveListener = MethodType(createRPCListener(self,'rpc_leave',self.leaveCallback,True),self,Session)
            self.leave = threading.Thread(target=self.leaveListener)
            self.leave.start()

            self.runThread = threading.Thread(target = self.run)
            self.runThread.start()


    def gameRestartCallback(self, request):
        print "Restarting the session"

        oldPlayers = self.players

        self.state = "INIT"
        self.players = { }
        self.order = []
        self.dead = []
        self.playerturn = 1
        self.shots = 0

        for oldPlayer in oldPlayers:
            self.tryAddPlayer(oldPlayer)

        #The global argument doesnt seem to be working, so...
        self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                         routing_key='',
                                         body="RESTARTING")
        return "OK", ""

    def leaveCallback(self,request):
        print("[.] player %s left" % request)
        self.order.remove(request)
        self.players.pop(request,None)

        #The global argument doesnt seem to be working, so...
        self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                         routing_key='',
                                         body="LEFT:"+request)

        return "OK",""

        return
    def kickPlayerCallback(self, request):
        print(" [.] kickPlayer(%s)" % request)
        if request in self.order:
            self.order.remove(request)
        if request in self.players:
            self.players.pop(request,None)

        #The global argument doesnt seem to be working, so...
        self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                         routing_key='',
                                         body="LEFT:"+request)

        return "OK", ""


    def finishedPlacingCallback(self,request):
        print( "[S] finishedPlacingCallback(%s)" % request)
        name, ships = request.split(':')

        success = self.placeShips(name, ships.split("|"))
        if success:
            self.players[name].isReady = True
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
                vertical = False if ship[2] == "False" else True
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


    def checkHit(self, x, y, victim, attacker):
        if self.players[victim].board[x][y] == TILE_SHIP:
            self.players[victim].board[x][y] = TILE_SHIP_HIT
            self.players[attacker].otherBoards[victim][x][y] = TILE_SHIP_HIT
            return "HIT"
        else:
            self.players[victim].board[x][y] = TILE_MISS
            self.players[attacker].otherBoards[victim][x][y] = TILE_MISS
            return "MISS"

    def checkSunk(self, x, y, victim):
        #TODO kui server hakkab ka misse hoidma siis peab seda t2iendama
        victimBoard = self.players[victim].board

        #check if ship on x+
        for i in range(x+1, self.boardWidth):
            if victimBoard[i][y] == TILE_SHIP:
                return False #Return false if we find ship
            elif victimBoard[i][y] == TILE_EMPTY:
                break #dont continue if nothing there

        for i in range(x-1, -1, -1):
            if victimBoard[i][y] == TILE_SHIP:
                return False
            elif victimBoard[i][y] == TILE_EMPTY:
                break


        for i in range(y+1, self.boardWidth):
            if victimBoard[x][i] == TILE_SHIP:
                return False
            elif victimBoard[x][i] == TILE_EMPTY:
                break

        for i in range(y-1, -1, -1):
            if victimBoard[x][i] == TILE_SHIP:
                return False
            elif victimBoard[x][i] == TILE_EMPTY:
                break

        return True

    def getSunkDetails(self,x,y,player):
        tmpBoard = self.players[player].board
        shiphit = []#tuples of coords (x,y),board = 3

        #can add x,y as they sunk the ship
        shiphit.append((x,y))

        #check all hits and create shiphit
        for i in range(x + 1, self.boardWidth):
            if tmpBoard[i][y] == 3:
                shiphit.append((i,y))
            else:
                break

        for i in range(x - 1, 0, -1):
            if tmpBoard[i][y] == 3:
                shiphit.append((i,y))
            else:
                break

        for i in range(y + 1, self.boardWidth):
            if tmpBoard[x][i] == 3:
                shiphit.append((x,i))
            else:
                break

        for i in range(y - 1, 0, -1):
            if tmpBoard[x][i] == 3:
                shiphit.append((x,i))
            else:
                break

        return shiphit


    def bombShipCallback(self,request):
        print request
        x, y, victim, attacker = request.split(":")

        print(" [.] bomb(%s,%s, %s, %s)" %(x,y,victim, attacker))
        response = self.checkHit(int(x),int(y),victim, attacker)
        print response

        if response == "MISS":
            self.shots -= 1

        if response == "HIT" and self.checkSunk(int(x),int(y),victim):
            hitcoords = self.getSunkDetails(int(x),int(y),victim)
            #pack for sending into x1;y1, x2;y2...
            hitcoords = ",".join([str(a[0])+";"+str(a[1]) for a in hitcoords])
            message = ":".join(["SUNK",victim, attacker,x,y, str(hitcoords)])
            #update player's ship count
            if self.players[victim].shipsRemaining != 1:
                self.players[victim].shipsRemaining -= 1
            else:
                self.players[victim].shipsRemaining = 0
                self.killPlayer(victim, attacker)
                self.shots -= 1

                print "%s is dead"%victim
                #TODO update also player that he is dead
            response = "SUNK"
        else:
            message = ":".join(["BOMB",victim,attacker,x,y,response])

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
        if len(self.order) == 0:
            return
        #TODO: Host gets 2 turns at start
        elif len(self.order) == 1 and self.playerturn == 1:
            self.playerturn = 0

        self.playerturn = (self.playerturn+1)%len(self.order)

        message = ":".join(["NEXT",self.order[self.playerturn]])
        self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                         routing_key='',
                                         body=message)
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
        if name in self.players:
            self.players[name].keepAliveTime = keepalive
        #print "New keepalive:", name
        #TODO check why it fails with OK
        #fails with ok as it does not contain :, dno why
        return "O:K", ""

    def getShipCount(self, boardWidth):
        if boardWidth == 4 or boardWidth == 6:
            return 4
        elif boardWidth == 8:
            return 7
        elif boardWidth == 10:
            return 11
        elif boardWidth == 12:
            return 16
        else:
            print "Warning! Unsupported board size."

    def checkWin(self):
        if len(self.order) == 1:
            print "%s WON!"%self.order[0]
            self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                             routing_key='',
                                             body="OVER:"+self.order[0])
            self.state = "OVER"

    def killPlayer(self, player, killer):
        self.players[player].shipsRemaining = 0
        self.players[player].isAlive = False
        self.order.remove(player)
        self.dead.append(player)
        print "%s is dead"%player
        self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                         routing_key='',
                                         body="DEAD:" + player + ":" + killer)
        self.checkWin()