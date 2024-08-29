from aiokafka import AIOKafkaProducer
import asyncio
import json

KAFKA_BROKER_URL = 'kafka:9093'
KAFKA_TOPIC = 'logging'
KAFKA_COUNT_TOPIC = 'count'

producer = None

async def init_kafka_producer():
    global producer
    retries = 5
    while retries > 0:
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=KAFKA_BROKER_URL,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await producer.start()
            break
        except Exception as e:
            retries -= 1
            await asyncio.sleep(10)  # Wait before retrying

async def send_log(log_data: dict):
    try:
        resp = await producer.send_and_wait(KAFKA_TOPIC, log_data)
    except Exception as e:
        print(f"Failed to send log: {str(e)}")

async def send_count(log_data: dict):
    try:
        resp = await producer.send_and_wait(KAFKA_COUNT_TOPIC, log_data)
    except Exception as e:
        print(f"Failed to send log: {str(e)}")

async def close_kafka_producer():
    global producer
    if producer:
        await producer.stop()
