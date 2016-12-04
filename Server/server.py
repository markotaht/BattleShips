import pika
import threading
from collections import defaultdict
from session import *

class Server():
    def __init__(self,name):
        self.name = name
        self.rooms = defaultdict(BattleShipsSession)

        self.initListeners()

    def initListeners(self):
        self.joinsession = threading.Thread(target=self.joinSessionListner, args=(self,))
        self.createsession = threading.Thread(target=self.createSessionListner, args=(self,))

        self.createsession.start()
        self.joinsession.start()

    def createSessionListner(self,parent):
        self.createSessionConnection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.createSessionChannel = self.createSessionConnection.channel()
        self.createSessionChannel.queue_declare(queue=parent.name+"."+"rpc_createSession")

        self.createSessionChannel.basic_qos(prefetch_count=1)
        self.createSessionChannel.basic_consume(parent.createSession, parent.name+"."+"rpc_createSession")
        self.createSessionChannel.start_consuming()

    def joinSessionListner(self,parent):
        self.joinSessionConnection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.joinSessionChannel = self.joinSessionConnection.channel()
        self.joinSessionChannel.queue_declare(queue=parent.name+"."+"rpc_joinSession")

        self.joinSessionChannel.basic_qos(prefetch_count=1)
        self.joinSessionChannel.basic_consume(parent.joinSession, parent.name+"."+"rpc_joinSession")
        self.joinSessionChannel.start_consuming()

    def joinSession(self, ch, method, props, body):
        n = body

        print(" [.] joinsession(%s)" % n)

        #rooms[n]
        response = "JOINED"
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id= \
                                                             props.correlation_id),
                         body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def createSession(self, ch, method, props, body):
        n = body

        print(" [.] createsession(%s)" % n)
        #TODO room check for similar name
    #    room = BattleShipsSession(self.name,n)
    #    self.rooms[n] = room
        response = "CREATED:"+n
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id= \
                                                             props.correlation_id),
                         body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)

server = Server("North WU")