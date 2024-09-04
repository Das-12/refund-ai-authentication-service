from aiokafka import AIOKafkaProducer
import asyncio
import json
from .config import settings
producer = None

async def init_kafka_producer():
    global producer
    retries = 5
    while retries > 0:
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BROKER_URL,
                # security_protocol='SASL_PLAINTEXT',  
                # sasl_mechanism='PLAIN',              # Specify the SASL mechanism
                # sasl_plain_username=KAFKA_USERNAME,  # Username for SASL/PLAIN
                # sasl_plain_password=KAFKA_PASSWORD,  
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await producer.start()
            print("PRODUCER INITIALIZED")
            break
        except Exception as e:
            retries -= 1
            await asyncio.sleep(10)  # Wait before retrying

async def send_log(log_data: dict):
    try:
        resp = await producer.send_and_wait(settings.KAFKA_TOPIC, log_data)
        print("LOG SEND")
    except Exception as e:
        print(f"Failed to send log: {str(e)}")

async def send_count(log_data: dict):
    try:
        resp = await producer.send_and_wait(settings.KAFKA_COUNT_TOPIC, log_data)
        print("COUNT SEND")
    except Exception as e:
        print(f"Failed to send log: {str(e)}")

async def close_kafka_producer():
    global producer
    if producer:
        await producer.stop()
