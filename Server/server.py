import pika
import threading
from collections import defaultdict
from session import BattleShipsSession
from commons import createRPCListener
from types import MethodType

class Server():
    def __init__(self,name):
        self.name = name
        self.prefix = name
        self.rooms = {}
        self.users = defaultdict(str)
        self.connections = []
        self.initListeners()

    def initListeners(self):
    #    self.joinsession = threading.Thread(target=self.joinSessionListner, args=(self,))
    #    self.createsession = threading.Thread(target=self.createSessionListner, args=(self,))
    #    self.getRoomsSession = threading.Thread(target=self.getRoomsListener,args=(self,))
        self.joinSessionListener = MethodType(createRPCListener(self,'rpc_joinSession',self.joinSessionCallback),self,Server)
        self.joinsession = threading.Thread(target=self.joinSessionListener)

        self.createSessionListener = MethodType(createRPCListener(self, 'rpc_createSession', self.createSessionCallback), self,
                                          Server)
        self.createsession = threading.Thread(target=self.createSessionListener)

        self.getRoomsListener = MethodType(createRPCListener(self,'rpc_getRooms',self.getRoomsCallback), self, Server)
        self.getRoomsSession = threading.Thread(target=self.getRoomsListener)

        self.createsession.start()
        self.joinsession.start()
        self.getRoomsSession.start()
    """
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

    def getRoomsListener(self,parent):
        self.getRoomsConnection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.getRoomsChannel = self.getRoomsConnection.channel()
        self.getRoomsChannel.queue_declare(queue=parent.name+"."+"rpc_getRooms")

        self.getRoomsChannel.basic_qos(prefetch_count=1)
        self.getRoomsChannel.basic_consume(parent.getRooms, parent.name+"."+"rpc_getRooms")
        self.getRoomsChannel.start_consuming()
    """
    def joinSessionCallback(self,request):
        n,user = request.split(":")
        print(" [.] joinsession(%s)" % n)
        self.rooms[n].addPlayer(user)

        return "JOINED:"+n, ""
    """
        def joinSession(self, ch, method, props, body):
            n,user = body.split(":")

            print(" [.] joinsession(%s)" % n)

            self.rooms[n].addPlayer(user)
            response = "JOINED:"+n
            ch.basic_publish(exchange='',
                             routing_key=props.reply_to,
                             properties=pika.BasicProperties(correlation_id= \
                                                                 props.correlation_id),
                             body=str(response))
            ch.basic_ack(delivery_tag=method.delivery_tag)
    """
    def createSessionCallback(self,request):
        n, whith, height, user = request.split(":")
        print(" [.] createsession(%s)" % n)
        room = BattleShipsSession(self.name, n, int(whith), int(height))
        self.rooms[n] = room
        room.start()
        room.addPlayer(user)
        response = "CREATED:" + n

        return response, ""
    """
        def createSession(self, ch, method, props, body):
            n,whith,height,user = body.split(":")

            print(" [.] createsession(%s)" % n)
            room = BattleShipsSession(self.name,n,int(whith),int(height))
            self.rooms[n] = room
            room.start()
            room.addPlayer(user)
            response = "CREATED:"+n
            ch.basic_publish(exchange='',
                             routing_key=props.reply_to,
                             properties=pika.BasicProperties(correlation_id= \
                                                                 props.correlation_id),
                             body=str(response))
            ch.basic_ack(delivery_tag=method.delivery_tag)
    """
    def getRoomsCallback(self,request):
        print(" [.] getRooms")
        response = ":".join(self.rooms.keys())
        return response, ""
    """
        def getRooms(self,ch, method,props, body):
            n = body

            print(" [.] getRooms" )
            response = ":".join(self.rooms.keys())
            ch.basic_publish(exchange='',
                             routing_key=props.reply_to,
                             properties=pika.BasicProperties(correlation_id= \
                                                                 props.correlation_id),
                             body=str(response))
            ch.basic_ack(delivery_tag=method.delivery_tag)
    """

server = Server("North WU")