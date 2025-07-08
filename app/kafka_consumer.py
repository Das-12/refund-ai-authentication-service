import asyncio
import json
from kafka import KafkaConsumer
from app.database import get_db
from app.subscriptions.models import Subscription, UserSubscriptionCount
from app.auth import get_user
from app.config import settings
from datetime import datetime, timedelta, timezone
import pytz

IST = pytz.timezone("Asia/Kolkata")

topic = settings.KAFKA_COUNT_TOPIC
broker_url = settings.KAFKA_BROKER_URL

async def update_subscription_count(consumer):
    print("Starting Kafka consumer...")
    await consumer.start()
    print("Kafka consumer started!")
    try:
        async for message in consumer:
            print(f"Received message: {message.value}")
            try:
                data = json.loads(message.value.decode("utf-8"))
                username = data.get("username")
                count = data.get("count", 1)
                print(f"Received message for {username} with count {count}")
                
                db = next(get_db())
                user = get_user(db, username=username)
                
                if not user:
                    print(f"User not found: {username}")
                    continue
                
                now_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
                now_ist = now_utc.astimezone(IST)
                current_month = now_ist.month
                current_year = now_ist.year
                
                user_count = db.query(UserSubscriptionCount).filter(
                    UserSubscriptionCount.user_id == user.id,
                    UserSubscriptionCount.month == current_month,
                    UserSubscriptionCount.year == current_year
                ).first()
                
                if user_count:
                    user_count.request_count += 1
                    print(f"Updated count for user {username} in {current_month}/{current_year} (IST). New count: {user_count.request_count}")
                else:
                    user_count = UserSubscriptionCount(
                        user_id=user.id,
                        company_id=user.company_id,
                        month=current_month,
                        year=current_year,
                        request_count=count
                    )
                    db.add(user_count)
                    print(f"Created new entry for user {username} in {current_month}/{current_year} (IST) with count {count}")
                
                # if user.roles != "company":
                #     print(f"Cannot update count for non-company user: {username}")
                #     continue
                
                subscription = db.query(Subscription).filter(Subscription.company_id == user.company_id).first()
                
                if subscription:
                    subscription.total_count += 1
                    db.commit()
                    db.refresh(subscription)
                    print(f"Updated count for company_id {user.company_id} (username: {username}). New count: {subscription.total_count}")
                else:
                    print(f"No subscription found for company_id {user.company_id}")
            except Exception as e:
                print(f"Error processing message: {e}")
                db.rollback()
            finally:
                db.close()
    except Exception as e:
        print(f"Error in consumer: {e}")
    
    finally:
        print("Consumer stopped")

# async def consume():
#     retries = 10
#     while retries > 0:
#         try:
#             consumer = KafkaConsumer(
#                 topic,
#                 bootstrap_servers=broker_url,
#                 auto_offset_reset='latest',
#                 group_id='logging-group',
#                 enable_auto_commit=True, 
#             )
#             print('consumer started')
#             break
#         except Exception as e:
#             print('failed starting consumer')
#             retries -= 1
#             await asyncio.sleep(10)  # Wait before retrying
            
#     task = asyncio.create_task(update_subscription_count(consumer))
            
#     try:
#         yield
#     finally:
#         task.cancel()
#         await asyncio.wait_for(task, timeout=5)