import pika
import uuid


class RpcClient(object):
  """RabbitMq based RPC Client"""

  def __init__(self, amqp_url, serverQueueName, expectReply=True):
    self.serverQueueName = serverQueueName
    self.expectReply = expectReply

    # blocking connection allows us to avoid using callbacks in every step
    self.connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=amqp_url,
        heartbeat_interval=(60 * 10)))

    self.channel = self.connection.channel()

    if self.expectReply:
      self.callback_queue = self.channel.queue_declare(
          exclusive=True).method.queue
      self.channel.basic_consume(self.on_response, queue=self.callback_queue)

  def call(self, headers, message):
    if self.expectReply:
      return self.call_expectReply(headers, message)
    else:
      return self.call_noExpectReply(headers, message)

  def on_response(self, ch, method, props, body):
    if self.corr_id == props.correlation_id:
      self.response = body
      # ack the delivery of message
      ch.basic_ack(delivery_tag=method.delivery_tag)

  def call_expectReply(self, headers, message):
    self.response = None
    self.corr_id = str(uuid.uuid4())
    properties = pika.BasicProperties(
        reply_to=self.callback_queue,
        correlation_id=self.corr_id,
        headers=headers,
        delivery_mode=1)
    self.channel.basic_publish(
        exchange='',
        routing_key=self.serverQueueName,
        properties=properties,
        body=message)
    # block until response
    while self.response is None:
      self.connection.process_data_events()
    return self.response

  def call_noExpectReply(self, headers, message):
    properties = pika.BasicProperties(headers=headers, delivery_mode=1)
    self.channel.basic_publish(
        exchange='',
        routing_key=self.serverQueueName,
        properties=properties,
        body=message)
    return None

  def close(self):
    self.connection.close()
