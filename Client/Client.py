import pygame, sys, pika, uuid, threading
from UI.MainMenuScreen import *
from UI.SessionSelectScreen import *
from UI.SetupShipsScreen import *
from UI.NewSessionScreen import *
from UI.GameScreen import *
from UI.Assets import *


from types import MethodType
from time import time
from pika.exceptions import ConnectionClosed
from pika.exceptions import ChannelClosed

class Client(object):
    def __init__(self):
        # set up pygame
        pygame.init()
        # set up the pygame window
        self.windowSurface = pygame.display.set_mode((640, 480), 0, 32)
        self.windowSurface.fill(COLOR_WHITE)
        pygame.display.set_caption('Naval Warfare Simulator')

        #Username field
        self.username = "DefaultName"

        self.loadMainMenuScreen()

        self.state = "INIT"
        self.lastkeepAlive  = 0

        #Start the main loop
        self.run();

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
                    sys.exit()
            # Clear the screen
            self.windowSurface.fill(COLOR_WHITE)
            #Update whatever screen we are on
            self.screen.update(events)
            # refresh the screen
            pygame.display.flip()
            #send keepalive every 10 seconds
            if time() > self.lastkeepAlive + 10:
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
        #TODO: remove later
        #This is hardcoded and has also to be the same in Server.py for it to work
        self.screen.addServer('Hardcoded localhost server', 'localhost')

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
    def loadGameScreen(self, board, isHost):
        # NOTE: This expects the current screen to be setupships screen when called
        playerReady = self.screen.playerReady
        self.screen = GameScreen()
        #TODO: Implement correct arguments depending on scenario
        isGameStarted = False

        self.screen.init(self, self.windowSurface, board, isHost, isGameStarted, playerReady)


    def connect(self, serverName, mqAddress):
        print "Connecting to " + serverName + " " + mqAddress
        self.serverName = serverName
        self.mqAddress = mqAddress
        self.asyncConnection = pika.BlockingConnection(pika.ConnectionParameters(
            host=mqAddress))

        self.syncConnection = pika.BlockingConnection(pika.ConnectionParameters(
            host=mqAddress))

        self.initServerListeners()

        #TODO: Also apss self.username somehow and wait for verified response

        #TODO: Check if connection was successful and return false if not
        return True

    def initlisteners(self):
        self.sessionIdentifier = self.serverName + "." + self.sessionName
        self.asynclistener = threading.Thread(target=self.listenForUpdates, name= "asynclistenerThread", args=(self.asyncConnection,))
        self.asynclistener.start()

        self.kickPlayer = MethodType(self.createFunction(self.sessionIdentifier, 'rpc_kick_player'), self, Client)
        self.finishedPlacing = MethodType(self.createFunction(self.sessionIdentifier, 'rpc_finished_placing'), self, Client)
        self.placeShip = MethodType(self.createFunction(self.sessionIdentifier, 'rpc_place_ship'), self, Client)
        self.bomb = MethodType(self.createFunction(self.sessionIdentifier, 'rpc_bomb'), self, Client)
        self.startGame = MethodType(self.createFunction(self.sessionIdentifier, 'rpc_start'), self, Client)
        self.updateKeepAlive = MethodType(self.createFunction(self.sessionIdentifier, 'rpc_update_keep_alive'), self, Client)


    def initServerListeners(self):
        self.createSession = MethodType(self.createFunction(self.serverName, 'rpc_createSession',True),self, Client)
        self.joinSession = MethodType(self.createFunction(self.serverName, 'rpc_joinSession', True), self, Client)
        self.getSessions = MethodType(self.createFunction(self.serverName, 'rpc_getSessions'), self, Client)


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
                print "bomba",parts
                if parts[1] == self.username:
                    if parts[5] == "HIT":
                        #we were hit and we should see our ship attacked
                        #show that we were hit
                        self.screen.boards[self.username].setTileByIndex(int(parts[3]), int(parts[4]), 3)
                        #show the attacker (strange, as we know who's turn it was)
                    else:
                        self.screen.boards[self.username].setTileByIndex(int(parts[3]), int(parts[4]), 2)
                if parts[1] != "SUNK" and parts[2] != self.username:
                    return
                print body
            elif parts[0] == "SUNK":
                print "SUNK", parts
            elif parts[0] == "NEXT":
                print parts[1], self.username
                self.screen.setTurnPlayer(parts[1])
                if parts[1] == self.username:
                    print "My turn"
                else:
                    print "Not my turn yet"
            elif parts[0] == "READY":
                print "Client - Player %s is ready" % parts[1]
                try:
                    self.screen.addReadyPlayer(parts[1], True)
                except AttributeError:
                    print "Attribute error on %s" % parts[1]
                    # IF we are the player
                    pass
            elif parts[0] == "NEWPLAYER":
                print "%s joined the game" % parts[1]
                self.screen.addReadyPlayer(parts[1], False)

            else:
                print "not known message %s", body

        channel.basic_consume(callback,
                              queue=queue_name,
                              no_ack=True)

        channel.start_consuming()


    #Stuff for RPC/MQ
    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    #Magic function to remove repeating code
    def createFunction(self, prefix, queue, server=False):
        channel = self.syncConnection.channel()
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
                self.syncConnection.process_data_events()

            if server:
                self.room = self.response.split(":")[1]
                self.initlisteners()
            return self.response
        return communicate
"""
    def bomb(self, x,y,player):
        n = str(x)+ ":" + str(y) + ":" + player + ":" + self.username
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.bombShipChannel.basic_publish(exchange='',
                                   routing_key=self.roomprefix+'rpc_bomb',
                                   properties=pika.BasicProperties(
                                         reply_to = self.callback_queue2,
                                         correlation_id = self.corr_id,
                                         ),
                                   body=str(n))
        while self.response is None:
            self.syncConnection.process_data_events()
        return self.response

    def placeShip(self,x,y,orientation):
        n = str(x) + ":" + str(y) + ":" + self.username
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.placeShipChannel.basic_publish(exchange='',
                                   routing_key=self.roomprefix+'rpc_place_ship',
                                   properties=pika.BasicProperties(
                                       reply_to=self.callback_queue,
                                       correlation_id=self.corr_id,
                                   ),
                                   body=str(n))
        while self.response is None:
            self.placeShipConnecion.process_data_events()
        return self.response

    def startGame(self):
        n = "start"
        self.response5 = None
        self.corr_id5 = str(uuid.uuid4())
        self.startGameChannel.basic_publish(exchange='',
                                   routing_key=self.roomprefix+'rpc_start',
                                   properties=pika.BasicProperties(
                                       reply_to=self.callback_queue5,
                                       correlation_id=self.corr_id5,
                                   ),
                                   body=str(n))
        while self.response5 is None:
            self.startGameConnection.process_data_events()
        return self.response5

    def finishedPlacing(self):
        n = "You finished placing your ships."
        self.response6 = None
        self.corr_id6 = str(uuid.uuid4())
        self.finishedPlacingChannel.basic_publish(exchange='',
                                   routing_key=self.roomprefix+'rpc_finished_placing',
                                   properties=pika.BasicProperties(
                                       reply_to=self.callback_queue6,
                                       correlation_id=self.corr_id6,
                                   ),
                                   body=str(n))
        while self.response6 is None:
            self.finishedPlacingConnection.process_data_events()
        return self.response6


        def createRoom(self,name):
            n = name+ ":"+ self.username
            self.response = None
            self.corr_id = str(uuid.uuid4())
            self.createRoomChannel.basic_publish(exchange='',
                                       routing_key=self.server+"."+'rpc_createSession',
                                       properties=pika.BasicProperties(
                                           reply_to=self.callback_queue3,
                                           correlation_id=self.corr_id,
                                       ),
                                       body=str(n))
            while self.response is None:
                self.syncConnection.process_data_events()

            self.room = self.response.split(":")[1]
            self.initlisteners()
            return self.response

    def joinRoom(self,name):
        n = name+":"+self.username
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.joinRoomChannel.basic_publish(exchange='',
                                   routing_key=self.server+"."+'rpc_joinSession',
                                   properties=pika.BasicProperties(
                                       reply_to=self.callback_queue4,
                                       correlation_id=self.corr_id,
                                   ),
                                   body=str(n))
        while self.response is None:
            self.syncConnection.process_data_events()

        self.room = self.response.split(":")[1]
        self.initlisteners()
        return self.response
"""

#Run the client when class is entry point
if __name__ == "__main__":
    client = Client()

    #TODO: Old tests that don't currently run anymore, fix them

    #print(" [x] Requesting place")
    #response = client.placeShip(0, 0, orient, "ME")
    #print(" [.] Got %r" % response)
    #
    # print(" [x] Requesting bomb")
    # response = client.bomb(0, 0, "target", "ME")
    #
    # print(" [.] Got %r" % response)
    # print(" [x] Requesting session")
    # response = client.createSession("Test", "ME")
    #
    # print(" [.] Got %r" % response)
    # print(" [x] Joining room")
    # response = client.joinSession("Test", "ME")
    #
    # print(" [.] Got %r" % response)
    # print(" [x] startgame session")
    # response = client.startGame()
    #
    # print(" [.] Got %r" % response)
    # print(" [x] finish shipping room")
    # response = client.finishedPlacing("ME")
    # print(" [.] Got %r" % response)
    #
    # print(" [x] Get sessions")
    # response = client.getSessions("")
    # print(" [.] Got %r" % response)