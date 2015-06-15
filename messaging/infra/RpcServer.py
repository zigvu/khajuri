import pika

class RpcServer( object ):
  def __init__( self, amqp_url, serverQueueName, rpcHandlerObj ):
    # handler object that will reply to rpc requests
    # needs to have a '__call__' method that responds to messages
    self.rpcHandlerObj = rpcHandlerObj

    # blocking connection allows us to avoid using callbacks in every step
    self.connection = pika.BlockingConnection( pika.ConnectionParameters( 
      host = amqp_url, heartbeat_interval = ( 60 * 10 ) ) )

    channel = self.connection.channel()
    channel.queue_declare( queue = serverQueueName )
    channel.basic_qos( prefetch_count = 1 )
    channel.basic_consume( self.on_request, queue = serverQueueName )
    channel.start_consuming()


  def on_request( self, ch, method, props, body ):
    responseHeaders, responseMessage = self.rpcHandlerObj( props.headers, body )

    # if client is expecting a reply, it will have supplied a reply_to queue
    if props.reply_to != None:
      properties = pika.BasicProperties(
        correlation_id = props.correlation_id, 
        headers = responseHeaders,
        delivery_mode=1
      )

      ch.basic_publish(
        exchange = '',
        routing_key = props.reply_to,
        properties = properties,
        body = responseMessage
      )

    # ack the delivery of message
    ch.basic_ack(delivery_tag = method.delivery_tag)


  def close(self):
    self.connection.close()
