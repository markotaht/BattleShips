import pika
import threading
import time

from commons import createRPCListener
from types import MethodType

class Session(threading.Thread):
    def __init__(self, server, name, boardWidth):
        threading.Thread.__init__(self)
        self.server = server
        self.name = name
        self.prefix = server +"." + name + "."
        self.lock = threading.Lock()
        self.updateChannel = None
        self.connections = []

        self.players = {}
        self.order = []
        self.boardWidth = boardWidth
        self.boards = {}
        self.dead = []
        self.state = "INIT"
        self.playerturn = 0
        self.shots = 0

        self.initChannels()

    def addPlayer(self, name):
        with self.lock:
            self.players[name] = time.time()
            self.boards[name] = [[0 for i in range(self.boardWidth)] for j in range(self.boardWidth)]
            self.order.append(name)
            self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                             routing_key='',
                                             body="%s joined the game"%name)

    def initChannels(self):
        with self.lock:
            self.updateConnection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            self.updateChannel = self.updateConnection.channel()
            self.updateChannel.exchange_declare(exchange=self.prefix + 'updates',type='fanout')
            self.connections.append(self.updateConnection)
            """
            self.placeship = threading.Thread(target=self.placeShipListener,args=(self.placeShip,))
            self.bombship = threading.Thread(target=self.bombShipListener, args=(self.bombShip,))
            self.gamestart = threading.Thread(target=self.gameStartListener, args=(self.gameStart,))
            self.finishedplacing = threading.Thread(target=self.finishedPlacingListener, args=(self.finishedPlacing,))
            """

            self.placeShipListener = MethodType(createRPCListener(self,'rpc_place_ship',self.placeShipCallback), self, Session)
            self.placeship = threading.Thread(target=self.placeShipListener)

            self.bombShipListener = MethodType(createRPCListener(self,'rpc_bomb',self.bombShipCallback), self, Session)
            self.bombship = threading.Thread(target=self.bombShipListener)

            self.gameStartListener = MethodType(createRPCListener(self,'rpc_start',self.gameStartCallback), self, Session)
            self.gamestart = threading.Thread(target=self.gameStartListener)

            self.finishedPlaceingListener = MethodType(createRPCListener(self,'rpc_finished_placing',self.finishedPlacingCallback), self, Session)
            self.finishedPlacing = threading.Thread(target=self.finishedPlaceingListener)

            self.placeship.start()
            self.bombship.start()
            self.gamestart.start()
            self.finishedPlacing.start()

    """
        def placeShipListener(self, placeShip):
            self.placeShipConnection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            self.placeShipChannel = self.placeShipConnection.channel()
            self.placeShipChannel.queue_declare(queue=self.prefix + 'rpc_place_ship')

            self.placeShipChannel.basic_qos(prefetch_count=1)
            self.placeShipChannel.basic_consume(placeShip, queue=self.prefix + 'rpc_place_ship')
            self.placeShipChannel.start_consuming()

        def bombShipListener(self, bombShip):
            self.bombShipConnection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            self.bombShipChannel = self.bombShipConnection.channel()
            self.bombShipChannel.queue_declare(queue=self.prefix + 'rpc_bomb')

            self.bombShipChannel.basic_qos(prefetch_count=1)
            self.bombShipChannel.basic_consume(bombShip, queue= self.prefix + 'rpc_bomb')
            self.bombShipChannel.start_consuming()

        def gameStartListener(self, gameStart):
            self.gameStartConnection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            self.gameStartChannel = self.gameStartConnection.channel()
            self.gameStartChannel.queue_declare(queue=self.prefix + 'rpc_start')

            self.gameStartChannel.basic_qos(prefetch_count=1)
            self.gameStartChannel.basic_consume(gameStart, queue= self.prefix + 'rpc_start')
            self.gameStartChannel.start_consuming()

        def finishedPlacingListener(self, finishedPlacing):
            self.finishedPlacingConnection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            self.finishedPlacingChannel = self.finishedPlacingConnection.channel()
            self.finishedPlacingChannel.queue_declare(queue=self.prefix + 'rpc_finished_placing')

            self.finishedPlacingChannel.basic_qos(prefetch_count=1)
            self.finishedPlacingChannel.basic_consume(finishedPlacing, queue= self.prefix + 'rpc_finished_placing')
            self.finishedPlacingChannel.start_consuming()
    """
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
    """
        def bombShip(self, ch, method, props, body):
            x,y,player,attacker = body.slit(":")

            print(" [.] bomb(%s,%s, %s)" %x,y,player)
            response = self.checkHit(int(x),int(y),player,attacker)
            ch.basic_publish(exchange='',
                             routing_key=props.reply_to,
                             properties=pika.BasicProperties(correlation_id= \
                                                                 props.correlation_id),
                             body=str(response))
            ch.basic_ack(delivery_tag=method.delivery_tag)

            #TODO teha paremaks ja lisada juurde laeva edastamine koigile
            if self.sunk(int(x),int(y),player):
                message = ":".join(["SUNK",x,y,player])
            else:
                message = ":".join(["BOMB",response,player,x,y])
            self.updateChannel.basic_publish(exchange=self.prefix+'updates',
                                             routing_key='',
                                             body=message)

            self.shots -= 1
            if self.shots == 0:
                self.notifyNextPlayer()
    """
    def notifyNextPlayer(self):
        message = ":".join(["NEXT",self.order[self.playerturn]])
        self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                         routing_key='',
                                         body=message)
        self.playerturn = (self.playerturn+1)%len(self.order)
        self.shots = len(self.order)-1

    def __placeShipOnField(self,x,y,dir,name):
        self.fields[name][y][x] = 1
        #SOemthing something direction

    def placeShipCallback(self, request):
        x, y, dir, name = request.split(":")
        print(" [.] place(%s)" % name)
        self.__placeShipOnField(int(x),int(y),dir,name)
        response = "OK"

        return response, ""

    """
    def placeShip(self, ch, method, props, body):
        x,y,dir,name = body.split(":")

        print(" [.] place(%s)" % name)
        self.__placeShipOnField(int(x),int(y),dir,name)
        response = "OK"
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id= \
                                                             props.correlation_id),
                         body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)
    """

    def gameStartCallback(self,request):
        print("Staring game")
        self.state = "PLAY"
        return "OK","START"

    """
    def gameStart(self, ch, method, props, body):
        n = body

        print("Staring game")
        response = "OK"
        self.state = "PLAY"
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id= \
                                                             props.correlation_id),
                         body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)

        self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                         routing_key='',
                                         body="START")

        self.notifyNextPlayer()
    """

    def finishedPlacingCallback(self,request):
        print("Finished placing ships")
        return "READY", ""

    """
    def finishedPlacing(self, ch, method, props, body):
        n = body

        print("Finished placing ships")
        response = "Ready"
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id= \
                                                             props.correlation_id),
                         body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)

        self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                         routing_key='',
                                         body="WOLOLOLO")
    """
