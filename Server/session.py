import pika
import threading

class BattleShipsSession():
    def __init__(self, server, name):
        self.server = server
        self.name = name
        self.prefix = server +"." + name + "."

        self.initChannels()

    def initChannels(self):
        self.updateConnection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.updateChannel = self.updateConnection.channel()
        self.updateChannel.exchange_declare(exchange=self.prefix + 'updates',type='fanout')

        self.placeship = threading.Thread(target=self.placeShipListener,args=(self.placeShip,))
        self.bombship = threading.Thread(target=self.bombShipListener, args=(self.bombShip,))
        self.gamestart = threading.Thread(target=self.gameStartListener, args=(self.gameStart,))
        self.finishedplacing = threading.Thread(target=self.finishedPlacingListener, args=(self.finishedPlacing,))

        self.placeship.start()
        self.bombship.start()
        self.gamestart.start()
        self.finishedplacing.start()

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
        self.finishedPlacingChannel.basic_consume(finishedPlacing, queue= self.prefix + 'rpc_start')
        self.finishedPlacingChannel.start_consuming()

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

    def gameStart(self, ch, method, props, body):
        n = body

        print("Staring game")
        response = "OK"
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id= \
                                                             props.correlation_id),
                         body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)

        self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                         routing_key='',
                                         body="WOLOLOLO")


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


client = BattleShipsSession("North WU", "Game1")