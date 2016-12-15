import pygame, sys, pika, uuid, threading
from UI.MainMenuScreen import *
from UI.SessionSelectScreen import *
from UI.SetupShipsScreen import *
from UI.NewSessionScreen import *
from UI.GameScreen import *
from UI.Assets import *


from types import MethodType
from time import time

class Client(object):
    def __init__(self):
        # set up pygame
        pygame.init()
        # set up the pygame window
        self.windowSurface = pygame.display.set_mode((640, 480), 0, 32)
        self.windowSurface.fill(COLOR_WHITE)
        pygame.display.set_caption('Naval Warfare Simulator')

        #Username value
        self.username = "DefaultName"

        self.loadMainMenuScreen()

        self.state = "INIT"
        self.lastkeepAlive  = time() - 10

        self.connected = False;
        self.syncServerConnection = None
        self.syncSessionConnection = None
        self.asyncConnection = None
        self.asyncServerListConnection = None

        self.serverlist("localhost")
        #Start the main loop
        self.run();


    def close(self):
        if self.syncServerConnection:
            try:
                self.syncServerConnection.close()
            except:
                pass
        if self.syncSessionConnection:
            try:
                self.syncSessionConnection.close()
            except:
                pass
        if self.asyncServerListConnection:
            try:
                self.asyncServerListConnection.close()
            except:
                pass
        if self.asyncConnection:
            try:
                self.asyncConnection.close()
            except:
                pass
        self.connected = False
        print "Closed"

    def serverlist(self, mqAddress):
        self.asyncServerListConnection =  pika.BlockingConnection(pika.ConnectionParameters(
            host=mqAddress))

        self.asyncServerListlistener = threading.Thread(target=self.listenforserverlist, name= "asyncServerListlistenerThread", args=(self.asyncServerListConnection,))
        self.asyncServerListlistener.start()

    def listenforserverlist(self, connection):
        self.serverListChannel = connection.channel()

        self.serverListChannel.exchange_declare('serverlist',
                                 type='fanout')

        result = self.serverListChannel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        self.serverListChannel.queue_bind(exchange='serverlist',
                           queue=queue_name)

        print(' [*] Waiting for ServerList. To exit press CTRL+C')

        def callback(ch, method, properties, body):
            if isinstance(self.screen, MainMenuScreen):
                self.screen.addServer(body,'localhost')

        self.serverListChannel.basic_consume(callback,
                              queue=queue_name,
                              no_ack=True)

        try:
            self.serverListChannel.start_consuming()
        except:
            print "Consuming failed"


    def run(self):
        clock = pygame.time.Clock()
        #Game loop
        while True:
            # Ensure max 30 fps
            clock.tick(30)
            #Process quitting
            events = pygame.event.get()
            for event in events:
                if event.type == QUIT:
                    #TODO Kill everything
                    self.close()
                    pygame.display.quit()
                    pygame.quit()
                    sys.exit()
            # Clear the screen
            self.windowSurface.fill(COLOR_WHITE)
            #Update whatever screen we are on
            self.screen.update(events)
            # refresh the screen
            pygame.display.flip()
            #send keepalive every 3 seconds
            if time() > self.lastkeepAlive + 3 and self.connected:
                try:
                    self.lastkeepAlive = time()
                    response = self.updateKeepAlive(self.username + ":" + str(self.lastkeepAlive))
                    if response != "O:K":
                        print "Updating keepalive, response", response
                except AttributeError:
                    # ignore if player has not joined a session
                    print "Trying to send keepalive but player has not joined a session"

    def loadMainMenuScreen(self):
        self.screen = MainMenuScreen()
        self.screen.init(self, self.windowSurface)

    def loadNewSessionScreen(self):
        self.screen = NewSessionScreen()
        self.screen.init(self, self.windowSurface)

    def loadSessionSelectScreen(self):
        self.screen = SessionSelectScreen()
        self.screen.init(self, self.windowSurface)

    def loadSetupShipsScreen(self, boardSize, isHost):
        self.screen = SetupShipsScreen()
        self.screen.init(self, self.windowSurface, boardSize, isHost)

    #Board should contain your placed ships
    def loadGameScreen(self, board, isHost, isGameStarted, players):
        self.screen = GameScreen()

        self.screen.init(self, self.windowSurface, board, isHost, isGameStarted, players)


    def connect(self, serverName, mqAddress):
        print "Connecting to " + serverName + " " + mqAddress
        self.serverName = serverName
        self.mqAddress = mqAddress

        self.connected = True

        self.syncServerConnection = pika.BlockingConnection(pika.ConnectionParameters(
            host=mqAddress))

        self.initServerListeners()

        #TODO: Also apss self.username somehow and wait for verified response

        #TODO: Check if connection was successful and return false if not
        return True

    def initlisteners(self):
        self.asyncConnection = pika.BlockingConnection(pika.ConnectionParameters(
            host=self.mqAddress))

        self.sessionIdentifier = self.serverName + "." + self.sessionName
        self.asynclistener = threading.Thread(target=self.listenForUpdates, name= "asynclistenerThread", args=(self.asyncConnection,))
        self.asynclistener.start()

        self.syncSessionConnection = pika.BlockingConnection(pika.ConnectionParameters(
            host=self.mqAddress))

        self.kickPlayer = MethodType(self.createFunction(self.sessionIdentifier, 'rpc_kick_player',self.syncSessionConnection), self, Client)
        self.finishedPlacing = MethodType(self.createFunction(self.sessionIdentifier, 'rpc_finished_placing',self.syncSessionConnection), self, Client)
        self.placeShip = MethodType(self.createFunction(self.sessionIdentifier, 'rpc_place_ship',self.syncSessionConnection), self, Client)
        self.bomb = MethodType(self.createFunction(self.sessionIdentifier, 'rpc_bomb',self.syncSessionConnection), self, Client)
        self.startGame = MethodType(self.createFunction(self.sessionIdentifier, 'rpc_start',self.syncSessionConnection), self, Client)
        self.restartGame = MethodType(self.createFunction(self.sessionIdentifier, 'rpc_restart', self.syncSessionConnection), self, Client)

        self.updateKeepAlive = MethodType(self.createFunction(self.sessionIdentifier, 'rpc_update_keep_alive',self.syncSessionConnection), self, Client)

        self.leave = MethodType(self.createFunction(self.sessionIdentifier,'rpc_leave',self.syncSessionConnection),self,Client)
        self.disconnect = MethodType(self.createFunction(self.sessionIdentifier,'rpc_disconnect',self.syncSessionConnection),self,Client)

    def initServerListeners(self):
        self.createSession = MethodType(self.createFunction(self.serverName, 'rpc_createSession',self.syncServerConnection,True),self, Client)
        self.joinSession = MethodType(self.createFunction(self.serverName, 'rpc_joinSession',self.syncServerConnection, True), self, Client)
        self.getSessions = MethodType(self.createFunction(self.serverName, 'rpc_getSessions',self.syncServerConnection), self, Client)


    #Stuff for asynccalls
    def listenForUpdates(self, connection):
        channel = connection.channel()

        channel.exchange_declare(exchange=self.sessionIdentifier + 'updates',
                                 type='fanout')

        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        channel.queue_bind(exchange=self.sessionIdentifier + 'updates',
                           queue=queue_name)

        print(' [*] Waiting for updates. To exit press CTRL+C')

        def callback(ch, method, properties, body):
            print "CLIENT - ", body
            if body == "START":
                print "Game has been started by the host!"
                self.screen.isGameStarted = True

                return
            elif body == "IGNORE":
                print "Ignore global message!"
                return
            parts = body.split(":")
            if parts[0] == "BOMB":
                if parts[1] == self.username:
                    if parts[5] == "HIT":
                        #we were hit and we should see our ship attacked
                        #show that we were hit
                        self.screen.players[self.username].board.setTileByIndex(int(parts[3]), int(parts[4]), 3)
                        #show the attacker (strange, as we know who's turn it was)
                    else:
                        self.screen.players[self.username].board.setTileByIndex(int(parts[3]), int(parts[4]), 2)
                if parts[1] != "SUNK" and parts[2] != self.username:
                    return
            elif parts[0] == "SUNK":
                # if any ships were sinked it should be visible for everyone at moment of sinking
                self.screen.markAsSunk(parts[1], parts[5], parts[6])
                print "SUNK", parts
            elif parts[0] == "NEXT":
                self.screen.setTurnPlayer(parts[1])
                if parts[1] == self.username:
                    print "My turn"
                else:
                    print "Not my turn yet"
            elif parts[0] == "READY":
                print "Client - Player %s is ready" % parts[1]
                try:
                    self.screen.setPlayerReady(parts[1], True)
                except AttributeError:
                    print "Attribute error on %s" % parts[1]
                    # IF we are the player
                    pass
            elif parts[0] == "NEWPLAYER":
                print "%s joined the game" % parts[1]
                self.screen.addPlayer(parts[1])
            elif parts[0] == "REJOININGPLAYER":
                print "%s rejoined the game" % parts[1]
                self.screen.players[parts[1]].connected = True
            elif parts[0] == "NEWHOST":
                print "Host changed to %s" % parts[1]
                if self.username == parts[1]:
                    self.screen.isHost = True
            elif parts[0] == "RESTARTING":
                print "Restarting the session..."

                oldPlayers = self.screen.players

                self.loadSetupShipsScreen(self.screen.boardWidth, self.screen.isHost)

                for player in oldPlayers:
                    if player != self.username:
                        self.screen.addPlayer(player)

            elif parts[0] == "DISCONNECTED":
                print "Marking %s as disconnected" % parts[1]

                if parts[1] != self.username:
                    self.screen.players[parts[1]].connected = False
                else:
                    #Player itself has been marked as disconnected
                    self.loadSessionSelectScreen()
                    self.stoplisteningToSession()

            elif parts[0] == "OVER":
                print "Game over, %s won"%parts[1]
                self.screen.isGameOver = True
                self.screen.setWinnerStr(parts[1])
            elif parts[0] == "DEAD":
                self.screen.killPlayer(parts[1])
                if parts[1] == self.username:
                    self.screen.deadStr = "Killed by %s"%parts[2]
            #Player left because he/she wanted to
            elif parts[0] == "LEFT":
                print "Player left " + parts[1]

                #TODO Review player leaving on his own will/kicked
                if parts[1] != self.username:
                    self.screen.removePlayer(parts[1])
                else:
                    # Player himself has been marked as disconnected
                    self.loadSessionSelectScreen()
                    self.screen.joinFailText = "You left/You were kicked from the session."
                    self.stoplisteningToSession()

            #send full board to spectators
            elif parts[0] == "SPECTATOR":
                if self.screen.deadStr != "":
                    print "%s attacked"%parts[1]
                    self.screen.spectatorUpdate(parts[1], parts[2])
            else:
                print "not known message "+body

        channel.basic_consume(callback,
                              queue=queue_name,
                              no_ack=True)

        try:
            channel.start_consuming()
        except:
            print "Something went wrong consuming"


    def stoplisteningToSession(self):
        print "Stopping listening to session."
        if self.asyncConnection:
            self.asyncConnection.close()
        if self.syncSessionConnection:
            self.syncSessionConnection.close()
        self.connected = False

    #Stuff for RPC/MQ
    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    #Magic function to remove repeating code
    def createFunction(self, prefix, queue, connection,server=False):
        channel = connection.channel()
        result = channel.queue_declare(exclusive=True)
        callback_queue = result.method.queue
        channel.basic_consume(self.on_response, no_ack=True,
                                queue=callback_queue)
        def communicate(self, *args):
            n = ":".join(map(str,args))
            self.response = None
            self.corr_id = str(uuid.uuid4())
            channel.basic_publish(exchange='',
                                               routing_key=prefix +"."+ queue,
                                               properties=pika.BasicProperties(
                                                   reply_to=callback_queue,
                                                   correlation_id=self.corr_id,
                                               ),
                                               body=str(n))
            while self.response is None:
                connection.process_data_events()

            if server:
                self.room = self.response.split(":")[1]
                self.initlisteners()
            return self.response
        return communicate

#Run the client when class is entry point
if __name__ == "__main__":
    client = Client()
