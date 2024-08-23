from kafka import KafkaProducer
import json

KAFKA_BROKER_URL = 'localhost:9092'
KAFKA_TOPIC = 'logging'

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER_URL,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def send_log(log_data: dict):
    print("LOG DATA",log_data)
    producer.send(KAFKA_TOPIC, log_data)
    producer.flush()
