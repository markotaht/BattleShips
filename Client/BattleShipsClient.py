import pika
import uuid
import threading

from types import MethodType

class BattleShipsClient(object):
    def __init__(self):
        self.serverList = ["North WU","Always offline"]
        self.server = self.serverList[0]
        self.room = ""
        self.roomprefix = ""

        self.username = "Testing"

        self.asyncConnection = pika.BlockingConnection(pika.ConnectionParameters(
                host='localhost'))

        self.syncConnection = pika.BlockingConnection(pika.ConnectionParameters(
                host='localhost'))

        self.state = "INIT"
        self.initServerListeners()
    ##    self.initlisteners()

    def initlisteners(self):
        self.roomprefix = self.server + "." + self.room
        self.asynclistener = threading.Thread(target=self.listenForUpdates, args=(self.asyncConnection,))
        self.asynclistener.start()
        self.finishedPlacing = MethodType(self.createFunction(self.roomprefix, 'rpc_finished_placing'), self,
                                   BattleShipsClient)

        self.placeShip = MethodType(self.createFunction(self.roomprefix, 'rpc_place_ship'), self,
                                          BattleShipsClient)

        self.bomb = MethodType(self.createFunction(self.roomprefix, 'rpc_bomb'), self,
                                          BattleShipsClient)

        self.startGame = MethodType(self.createFunction(self.roomprefix, 'rpc_start'), self,
                                          BattleShipsClient)

        """
        self.placeShipConnecion = pika.BlockingConnection(pika.ConnectionParameters(
                host='localhost'))

        self.placeShipChannel = self.placeShipConnecion.channel()

        result = self.placeShipChannel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.placeShipChannel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)
        self.bombShipConnection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))

        self.bombShipChannel = self.bombShipConnection.channel()

        result = self.bombShipChannel.queue_declare(exclusive=True)
        self.callback_queue2 = result.method.queue

        self.bombShipChannel.basic_consume(self.on_response, no_ack=True,
                                           queue=self.callback_queue2)

        self.startGameConnection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))

        self.startGameChannel = self.startGameConnection.channel()

        result = self.startGameChannel.queue_declare(exclusive=True)
        self.callback_queue5 = result.method.queue

        self.startGameChannel.basic_consume(self.on_response, no_ack=True,
                                           queue=self.callback_queue5)


        self.finishedPlacingConnection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))

        self.finishedPlacingChannel = self.finishedPlacingConnection.channel()

        result = self.finishedPlacingChannel.queue_declare(exclusive=True)
        self.callback_queue6 = result.method.queue

        self.finishedPlacingChannel.basic_consume(self.on_response, no_ack=True,
                                            queue=self.callback_queue6)
        """

    def initServerListeners(self):
        self.createRoom = MethodType(self.createFunction(self.server,'rpc_createSession',True),self,BattleShipsClient)
        self.joinRoom = MethodType(self.createFunction(self.server, 'rpc_joinSession', True), self,
                                     BattleShipsClient)
        self.getRooms = MethodType(self.createFunction(self.server, 'rpc_getRooms'), self,
                                     BattleShipsClient)
        """
        self.createRoomChannel = self.syncConnection.channel()

        result = self.createRoomChannel.queue_declare(exclusive=True)
        self.callback_queue3 = result.method.queue

        self.createRoomChannel.basic_consume(self.on_response, no_ack=True,
                                           queue=self.callback_queue3)

        self.joinRoomChannel = self.syncConnection.channel()

        result = self.joinRoomChannel.queue_declare(exclusive=True)
        self.callback_queue4 = result.method.queue

        self.joinRoomChannel.basic_consume(self.on_response, no_ack=True,
                                             queue=self.callback_queue4)
        """

    #Stuff for asynccalls
    def listenForUpdates(self,connection):
        channel = connection.channel()

        channel.exchange_declare(exchange=self.roomprefix + 'updates',
                                 type='fanout')

        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        channel.queue_bind(exchange=self.roomprefix+'updates',
                           queue=queue_name)

        print(' [*] Waiting for updates. To exit press CTRL+C')

        def callback(ch, method, properties, body):
            if body == "START":
                self.state = "PLAY"
                return
            parts = body.split(":")
            if parts[0] == "BOMB":
                if parts[1] != "SINK" and parts[2] != self.username:
                    return
                print body
            elif parts[0] == "NEXT":
                if parts[1] == self.username:
                    print "YAY minu kaik"
                else:
                    print "Peab veel ootama"

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
fibonacci_rpc = BattleShipsClient()

print(" [x] Requesting place")
#response = fibonacci_rpc.placeShip(0,0,4)
#print(" [.] Got %r" % response)
print(" [x] Requesting bomb")
#response = fibonacci_rpc.bomb(0,0,"Test")
#print(" [.] Got %r" % response)
print(" [x] Requesting room")
response = fibonacci_rpc.createRoom("Test","ME")
print(" [.] Got %r" % response)
print(" [x] Joining room")
response = fibonacci_rpc.joinRoom("Test","ME")
print(" [.] Got %r" % response)
print(" [x] startgaem room")
#response = fibonacci_rpc.startGame()
#print(" [.] Got %r" % response)
print(" [x] finish shipping room")
response = fibonacci_rpc.finishedPlacing()
print(" [.] Got %r" % response)
print(" [x] Get rooms")
response = fibonacci_rpc.getRooms("")
print(" [.] Got %r" % response)