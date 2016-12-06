import pika

#BLACK MAGIC to reduce code size
def createRPCListener(parent, queue,callback,globalmessage=False,host='localhost'):

    def receiver(ch, method, props, body):
        response,globmessage = callback(body)

        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id= \
                                                             props.correlation_id),
                         body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)

        if globalmessage:
            parent.updateChannel.basic_publish(exchange=parent.prefix + 'updates',
                                             routing_key='',
                                             body=globmessage)

    __receiver = receiver
    def listener(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        self.connections.append(connection)
        channel = connection.channel()
        channel.queue_declare(queue=parent.prefix+"."+queue)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(__receiver, parent.prefix+"."+queue)
        channel.start_consuming()

    return listener
