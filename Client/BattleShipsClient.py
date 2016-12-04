import pika
import uuid
import threading

from commons import *

class BattleShipsClient(object):
    def __init__(self):
        self.server = "North WU"
        self.room = "Game1"
        self.roomprefix = self.server + "." + self.room + "."

        self.initServerListeners()
        self.initlisteners()

    def initlisteners(self):
        self.asynclistener = threading.Thread(target=self.listenForUpdates)
        self.asynclistener.start()
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

        self.bombShipChannel.basic_consume(self.on_response2, no_ack=True,
                                   queue=self.callback_queue2)

    def initServerListeners(self):
        self.createRoomConnection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))

        self.createRoomChannel = self.createRoomConnection.channel()

        result = self.createRoomChannel.queue_declare(exclusive=True)
        self.callback_queue3 = result.method.queue

        self.createRoomChannel.basic_consume(self.on_response3, no_ack=True,
                                           queue=self.callback_queue3)

        self.joinRoomConnection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))

        self.joinRoomChannel = self.joinRoomConnection.channel()

        result = self.joinRoomChannel.queue_declare(exclusive=True)
        self.callback_queue4 = result.method.queue

        self.joinRoomChannel.basic_consume(self.on_response4, no_ack=True,
                                             queue=self.callback_queue4)

    #Stuff for asynccalls
    def listenForUpdates(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))
        channel = connection.channel()

        channel.exchange_declare(exchange=self.roomprefix + 'updates',
                                 type='fanout')

        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        channel.queue_bind(exchange=self.roomprefix+'updates',
                           queue=queue_name)

        print(' [*] Waiting for updates. To exit press CTRL+C')

        def callback(ch, method, properties, body):
            print(" [x] %r" % body)

        channel.basic_consume(callback,
                              queue=queue_name,
                              no_ack=True)

        channel.start_consuming()

    #Stuff for RPC/MQ
    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def on_response2(self, ch, method, props, body):
        if self.corr_id2 == props.correlation_id:
            self.response2 = body

    def on_response3(self, ch, method, props, body):
        if self.corr_id3 == props.correlation_id:
            self.response3 = body

    def on_response4(self, ch, method, props, body):
        if self.corr_id4 == props.correlation_id:
            self.response4 = body

    def bomb(self, x,y,player):
        n = str(x)+ ":" + str(y) + ":" + str(player)
        self.response2 = None
        self.corr_id2 = str(uuid.uuid4())
        self.bombShipChannel.basic_publish(exchange='',
                                   routing_key=self.roomprefix+'rpc_bomb',
                                   properties=pika.BasicProperties(
                                         reply_to = self.callback_queue2,
                                         correlation_id = self.corr_id2,
                                         ),
                                   body=str(n))
        while self.response2 is None:
            self.bombShipConnection.process_data_events()
        return self.response2

    def placeShip(self,x,y,orientation):
        n = str(x) + ":" + str(y) + ":" + str(orientation)
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

    def createRoom(self,name):
        n = name
        self.response3 = None
        self.corr_id3 = str(uuid.uuid4())
        self.createRoomChannel.basic_publish(exchange='',
                                   routing_key=self.server+"."+'rpc_createSession',
                                   properties=pika.BasicProperties(
                                       reply_to=self.callback_queue3,
                                       correlation_id=self.corr_id3,
                                   ),
                                   body=str(n))
        while self.response3 is None:
            self.createRoomConnection.process_data_events()

        self.room = self.response3.split(":")[1]
        return self.response3

    def joinRoom(self,name):
        n = name
        self.response4 = None
        self.corr_id4 = str(uuid.uuid4())
        self.joinRoomChannel.basic_publish(exchange='',
                                   routing_key=self.server+"."+'rpc_joinSession',
                                   properties=pika.BasicProperties(
                                       reply_to=self.callback_queue4,
                                       correlation_id=self.corr_id4,
                                   ),
                                   body=str(n))
        while self.response4 is None:
            self.joinRoomConnection.process_data_events()

  #      self.room = self.response4.split(":")[1]
        return self.response4

fibonacci_rpc = BattleShipsClient()

print(" [x] Requesting place")
#response = fibonacci_rpc.placeShip(0,0,4)
#print(" [.] Got %r" % response)
print(" [x] Requesting bomb")
#response = fibonacci_rpc.bomb(0,0,1)
#print(" [.] Got %r" % response)
print(" [x] Requesting room")
response = fibonacci_rpc.createRoom("Test")
print(" [.] Got %r" % response)
print(" [x] Joining room")
response = fibonacci_rpc.joinRoom("Test")
print(" [.] Got %r" % response)