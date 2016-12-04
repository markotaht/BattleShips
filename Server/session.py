import pika
import threading

class BattleShipsSession(threading.Thread):
    def __init__(self, server, name):
        threading.Thread.__init__(self)
        self.server = server
        self.name = name
        self.prefix = server +"." + name + "."
        self.lock = threading.Lock()
        self.updateChannel = None

        #somehow track who has ships
        self.players = []
        self.dead = []
        self.state = "INIT"
        self.playerturn = ""
        self.shots = 0

    def addPlayer(self, name):
        with self.lock:
            self.players.append(name)
            self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                             routing_key='',
                                             body="%s joined the game"%name)


    def run(self):
        self.initChannels()

    def initChannels(self):
        with self.lock:
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
        self.finishedPlacingChannel.basic_consume(finishedPlacing, queue= self.prefix + 'rpc_finished_placing')
        self.finishedPlacingChannel.start_consuming()


    def checkHit(self,x,y,player):
        return "MISS"

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

        message = ":".join(["BOMB",response,player,x,y])
        self.updateChannel.basic_publish(exchange=self.prefix+'updates',
                                         routing_key='',
                                         body=message)

        self.shots -= 1
        if self.shots == 0:
            self.notifyNextPlayer()

    def notifyNextPlayer(self):
        player = "Someone somewhere"
        message = ":".join(["NEXT",player])
        self.updateChannel.basic_publish(exchange=self.prefix + 'updates',
                                         routing_key='',
                                         body=message)

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
