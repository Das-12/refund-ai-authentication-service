from aiokafka import AIOKafkaProducer
import asyncio
import json

KAFKA_BROKER_URL = 'kafka:9093'
KAFKA_TOPIC = 'logging'

producer = None

async def init_kafka_producer():
    global producer
    producer = AIOKafkaProducer(
        bootstrap_servers=KAFKA_BROKER_URL,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    # Get the producer ready
    await producer.start()

async def send_log(log_data: dict):
    try:
        resp = await producer.send_and_wait(KAFKA_TOPIC, log_data)
    except Exception as e:
        print(f"Failed to send log: {str(e)}")

async def close_kafka_producer():
    global producer
    if producer:
        await producer.stop()
