from pika import BlockingConnection, ConnectionParameters, PlainCredentials, exceptions
import backoff

from helpers import RabbitMQSettings


@backoff.on_exception(
    backoff.expo,
    exception=(
        exceptions.AMQPConnectionError,
        exceptions.AMQPChannelError,
        ValueError,
    ),
    max_time=60,
)
def is_pinging(client: BlockingConnection):
    if not client.is_open:
        raise ValueError("Connection failed")

    try:
        channel = client.channel()
        channel.basic_qos(prefetch_count=1)
        channel.close()
    except (exceptions.AMQPConnectionError, exceptions.AMQPChannelError) as e:
        raise ValueError(f"Failed to communicate with RabbitMQ: {str(e)}")


if __name__ == "__main__":
    rabbitmq_client = None
    rabbitmq_settings = RabbitMQSettings()
    try:
        connection_params = ConnectionParameters(
            host=rabbitmq_settings.host,
            port=rabbitmq_settings.port,
            credentials=PlainCredentials(
                username=rabbitmq_settings.username,
                password=rabbitmq_settings.password
            )
        )
        rabbitmq_client = BlockingConnection(connection_params)
        is_pinging(rabbitmq_client)
        print("RabbitMQ is available and working correctly")
    except Exception as e:
        print(f"Failed to connect to RabbitMQ: {str(e)}")
    finally:
        if rabbitmq_client and rabbitmq_client.is_open:
            rabbitmq_client.close()
