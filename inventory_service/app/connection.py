import pika
import time

# RabbitMQ connection parameters
rabbitmq_host = 'rabbitmq'
rabbitmq_port = 5672
rabbitmq_user = 'guest'
rabbitmq_password = 'guest'



def get_rabbitmq_connection(max_retries=5, delay=5):
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_password)
    connection_params = pika.ConnectionParameters(host=rabbitmq_host, port=rabbitmq_port, credentials=credentials)
    
    attempts = 0
    while attempts < max_retries:
        try:
            connection = pika.BlockingConnection(connection_params)
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            attempts += 1
            print(f"Connection attempt {attempts} failed: {e}")
            if attempts < max_retries:
                print(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("Max retries reached. Could not connect to RabbitMQ.")
                raise


def publish_message(message,method,queue):
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue=queue)
    properties = pika.BasicProperties(method)
    channel.basic_publish(exchange='', routing_key=queue, body=message,properties=properties)
    connection.close()
    
    
    
# Function to consume messages from RabbitMQ
def consume_messages(queue, callback):
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue=queue)
    
    def on_message_callback(ch, method, properties, body):
        try:
            message = body.decode()
            callback(message, properties)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception:
            print("message not consumed")
    
    channel.basic_consume(queue=queue, on_message_callback=on_message_callback)
    
    print("Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()
    
    channel.close()