import os
import pika
import json
from datetime import timedelta, datetime

from models.group import Group
from models.group_user import GroupUser
from models.event import Event
from models.interval import Interval
from models.job import Job
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa

SQLALCHEMY_DATABASE_URI = os.getenv("CALENDAR_DATABASE_URL")
RABBITMQ_URL = os.getenv("RABBITMQ_URL")

base = declarative_base()
engine = sa.create_engine(SQLALCHEMY_DATABASE_URI)
base.metadata.bind = engine
session = orm.scoped_session(orm.sessionmaker(bind=engine))

def merge_intervals(intervals):
    if not intervals:
        return []

    intervals.sort(key=lambda x: x[0])

    merged = []
    current_start, current_end = intervals[0]

    for start, end in intervals[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            merged.append((current_start, current_end))
            current_start, current_end = start, end

    merged.append((current_start, current_end))
    return merged
        
def free_intervals(intervals, start_time, end_time):
    if not intervals:
        return [(start_time, end_time)]
    free = []

    if start_time < intervals[0][0]:
        free.append((start_time, intervals[0][0]))

    for i in range(len(intervals) - 1):
        free.append((intervals[i][1], intervals[i + 1][0]))

    if intervals[-1][1] < end_time:
        free.append((intervals[-1][1], end_time))

    return free

def process_intervals(ch, method, properties, body):
    job = json.loads(body)
    print("Processing job:", job)

    group_id = job["group_id"]
    duration = timedelta(
                    hours=job["duration"].get("hours", 0),
                    minutes=job["duration"].get("minutes", 0)
                )

    try:
        start_time = datetime.fromisoformat(job["start_time"])
        end_time = datetime.fromisoformat(job["end_time"])
    except:
        print("Invalid datetime")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
  
    intervals = []

    users = session.query(GroupUser).filter(GroupUser.group_id == group_id).all()
    for user in users:
        groups = session.query(GroupUser).filter(GroupUser.user_id == user.user_id).all()   
        for group in groups:
            events = session.query(Event).filter(Event.group_id == group.group_id).all()
            for event in events:
                event_start_time = event.start_time
                event_end_time = event.end_time
                if event_end_time <= start_time or event_start_time >= end_time:
                    continue
                intervals.append((max(event_start_time, start_time), min(event_end_time, end_time)))

    intervals = merge_intervals(intervals)
    free = free_intervals(intervals, start_time, end_time)

    for start, end in free:
        while start + duration <= end:
            job_result = Interval(
                job_id=job["job_id"],
                start_time=start,
                end_time=start + duration

            )
            session.add(job_result)
            
            start += duration

    job_record = session.get(Job, job["job_id"])
    if job_record is not None:
        job_record.status = "DONE"
        session.add(job_record)
    
    session.commit()

    print(f"Job {job_record.id} DONE, found intervals: {len(free)}")

    ch.basic_ack(delivery_tag=method.delivery_tag)

def _wait_for_rabbitmq(retries=10, delay=3):
    import time
    for attempt in range(retries):
        try:
            connection = pika.BlockingConnection(
                pika.URLParameters(RABBITMQ_URL)
            )
            print("RabbtiMQ connected.")
            return connection
        except pika.exceptions.AMQPConnectionError as e:
            print(f"RabbitMQ connection failed (attempt {attempt + 1}/{retries}): {e}")
            time.sleep(delay)


def main():
    print("Starting worker")
    connection = _wait_for_rabbitmq()
    channel = connection.channel()
    channel.queue_declare(queue="suggestions", durable=True)
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue="suggestions",
        on_message_callback=process_intervals
    )

    print("Worker started")
    channel.start_consuming()

if __name__ == "__main__":
    main()
