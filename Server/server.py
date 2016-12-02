import pika

class BattleShipsServer():
    def __init__(self):
        self.initChannels()

    def initChannels(self):
        self.updateConnection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.updateChannel = self.updateConnection.channel()
        self.updateChannel.exchange_declare(exchange='updates',type='fanout')

        self.placeShipConnection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.placeShipChannel = self.placeShipConnection.channel()
        self.placeShipChannel.queue_declare(queue='rpc_place_ship')

        self.placeShipChannel.basic_qos(prefetch_count=1)
        self.placeShipChannel.basic_consume(self.placeShip, queue='rpc_place_ship')
        self.placeShipChannel.start_consuming()

        self.bombShipConnection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.bombShipChannel = self.placeShipConnection.channel()
        self.bombShipChannel.queue_declare(queue='rpc_bomb')

        self.bombShipChannel.basic_qos(prefetch_count=1)
        self.bombShipChannel.basic_consume(self.bombShip, queue='rpc_bomb')
        self.bombShipChannel.start_consuming()

    def bombShip(self, ch, method, props, body):
        n = body

        print(" [.] fib(%s)" % n)
        response = "MISS"
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id= \
                                                             props.correlation_id),
                         body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)

        self.updateChannel.basic_publish(exchange='updates',
                                         routing_key='',
                                         body="KABOOM")

    def placeShip(self, ch, method, props, body):
        n = body

        print(" [.] fib(%s)" % n)
        response = "HIT"
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id= \
                                                             props.correlation_id),
                         body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)

        self.updateChannel.basic_publish(exchange='updates',
                                         routing_key='',
                                         body="WOLOLOLO")

client = BattleShipsServer()