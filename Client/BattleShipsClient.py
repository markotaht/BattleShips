import pika
import uuid
import threading

from commons import *

class BattleShipsClient(object):
    def __init__(self):
        self.asynclistener = threading.Thread(target=self.listenForUpdates)
        self.asynclistener.start()
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(
                host='localhost'))

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)

    #Stuff for asynccalls
    def listenForUpdates(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host='localhost'))
        channel = connection.channel()

        channel.exchange_declare(exchange='logs',
                                 type='fanout')

        result = channel.queue_declare(exclusive=True)
        queue_name = result.method.queue

        channel.queue_bind(exchange='updates',
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

    def bomb(self, x,y,player):
        n = str(x)+ ":" + str(y) + ":" + str(player)
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key='rpc_bomb',
                                   properties=pika.BasicProperties(
                                         reply_to = self.callback_queue,
                                         correlation_id = self.corr_id,
                                         ),
                                   body=str(n))
        while self.response is None:
            self.connection.process_data_events()
        return self.response

    def placeShip(self,x,y,orientation):
        n = str(x) + ":" + str(y) + ":" + str(orientation)
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key='rpc_place_ship',
                                   properties=pika.BasicProperties(
                                       reply_to=self.callback_queue,
                                       correlation_id=self.corr_id,
                                   ),
                                   body=str(n))
        while self.response is None:
            self.connection.process_data_events()
        return self.response
fibonacci_rpc = BattleShipsClient()

print(" [x] Requesting fib(30)")
response = fibonacci_rpc.placeShip(0,0,4)
print(" [.] Got %r" % response)
response = fibonacci_rpc.bomb(0,0,1)
print(" [.] Got %r" % response)