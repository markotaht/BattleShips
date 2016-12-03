import pika
import threading

class BattleShipsSession():
    def __init__(self, server, name):
        self.initChannels()
        self.server = server
        self.name = name
        self.prefix = server +"." + name + "."

    def initChannels(self):
        self.updateConnection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.updateChannel = self.updateConnection.channel()
        self.updateChannel.exchange_declare(exchange=self.prefix + 'updates',type='fanout')

        self.placeship = threading.Thread(target=self.placeShipListener,args=(self.placeShip,))
        self.bombship = threading.Thread(target=self.bombShipListener, args=(self.bombShip,))

        self.placeship.start()
        self.bombship.start()

    def placeShipListener(self, placeShip):
        self.placeShipConnection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.placeShipChannel = self.placeShipConnection.channel()
        self.placeShipChannel.queue_declare(queue='rpc_place_ship')

        self.placeShipChannel.basic_qos(prefetch_count=1)
        self.placeShipChannel.basic_consume(placeShip, queue='rpc_place_ship')
        self.placeShipChannel.start_consuming()

    def bombShipListener(self, bombShip):
        self.bombShipConnection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.bombShipChannel = self.bombShipConnection.channel()
        self.bombShipChannel.queue_declare(queue='rpc_bomb')

        self.bombShipChannel.basic_qos(prefetch_count=1)
        self.bombShipChannel.basic_consume(bombShip, queue='rpc_bomb')
        self.bombShipChannel.start_consuming()

    def bombShip(self, ch, method, props, body):
        n = body

        print(" [.] bomb(%s)" % n)
        response = "MISS"
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id= \
                                                             props.correlation_id),
                         body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)

        self.updateChannel.basic_publish(exchange=self.prefix+'updates',
                                         routing_key='',
                                         body="KABOOM")

    def placeShip(self, ch, method, props, body):
        n = body

        print(" [.] place(%s)" % n)
        response = "HIT"
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id= \
                                                             props.correlation_id),
                         body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)

        self.updateChannel.basic_publish(exchange=self.prefix+'updates',
                                         routing_key='',
                                         body="WOLOLOLO")

client = BattleShipsSession("North WU", "Game1")