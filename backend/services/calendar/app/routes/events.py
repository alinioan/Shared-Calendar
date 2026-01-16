import requests
from datetime import datetime
from flask import Blueprint, current_app, jsonify, g, request
from ..utils.decorators import jwt_required, group_role_required
from ..models.group import Group
from ..models.group_user import GroupUser
from ..models.event import Event
from ..models.job import Job
from ..models.interval import Interval
from ..db import db

import pika
import json
import uuid
import time

events_bp = Blueprint("events", __name__)

def acquire_lock(redis_client, lock_key, timeout=5000):
    """Acquire a Redis lock, returns lock_id if successful, None otherwise"""
    lock_id = str(uuid.uuid4())
    acquired = redis_client.set(lock_key, lock_id, nx=True, px=timeout)
    return lock_id if acquired else None

def release_lock(redis_client, lock_key, lock_id):
    """Release a Redis lock"""
    lua_script = """
    if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
    else
        return 0
    end
    """
    redis_client.eval(lua_script, 1, lock_key, lock_id)

@events_bp.post("/group/<int:group_id>")
@jwt_required
@group_role_required("organizer")
def add_event(group_id):
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    if not data.get("start_time") or not data.get("end_time"):
        return jsonify({"error": "start_time and end_time are required"}), 400

    if data["start_time"] >= data["end_time"]:
        return jsonify({"error": "start_time must be before end_time"}), 400

    event = Event(
        group_id=group_id,
        title=data.get("title"),
        description=data.get("description", ""),
        start_time=data.get("start_time"),
        end_time=data.get("end_time"),
        creation_date=datetime.utcnow(),
        last_update=datetime.utcnow()
    )

    lock_key = f"group:{group_id}:event_lock"
    lock_id = acquire_lock(current_app.redis_client, lock_key, timeout=5000)
    
    if not lock_id:
        return jsonify({"error": "Calendar is busy, try again"}), 409
    
    try:
        overlap_event = Event.query.filter(
            Event.group_id == group_id,
            Event.start_time < event.end_time,
            Event.end_time > event.start_time
        ).first()
        
        if overlap_event:
            return jsonify({"error": "Event time overlaps with an existing event"}), 400
        
        db.session.add(event)
        db.session.commit()
    finally:
        release_lock(current_app.redis_client, lock_key, lock_id)


    return jsonify(event.to_dict()), 201


@events_bp.get("/group/<int:group_id>")
@jwt_required
def get_group_events(group_id):
    events = Event.query.filter_by(group_id=group_id).all()
    events_list = [event.to_dict() for event in events]
    return jsonify({"group": group_id, "events": events_list}), 200

@events_bp.delete("group/<int:group_id>")
@jwt_required
@group_role_required("organizer")
def remove_event(group_id):
    data = request.get_json()
    event = Event.query.filter_by(
        group_id=group_id,
        id=data.get("event_id")
    ).first()

    if not event:
        return jsonify({"error": "Event not found"}), 404

    db.session.delete(event)
    db.session.commit()
    return jsonify({"message": "Event deleted successfully"}), 200

@events_bp.post("/recommendations/group/<int:group_id>")
@jwt_required
@group_role_required("organizer")
def make_recommendation_request(group_id):
    data = request.get_json()

    job = Job(status="PENDING")
    db.session.add(job)
    db.session.commit()

    try:
        start_time = validate_iso_datetime(data["start_time"])
        end_time = validate_iso_datetime(data["end_time"])
    except (KeyError, ValueError) as e:
        return jsonify({"error": str(e)}), 400

    job = {
        "job_id": job.id,
        "group_id": group_id,
        "duration": data["duration"],
        "start_time": start_time,
        "end_time": end_time
    }

    lock_key = f"group:{group_id}:recommendation_lock"
    lock_id = acquire_lock(current_app.redis_client, lock_key, timeout=5000)
    
    if not lock_id:
        max_wait = 10.0  # seconds
        wait = 0.1
        elapsed = 0.0

        while elapsed < max_wait:
            time.sleep(wait)
            elapsed += wait
            lock_id = acquire_lock(current_app.redis_client, lock_key, timeout=5000)
            if lock_id:
                break
            wait = min(wait * 2, 2.0)

        if not lock_id:
            return jsonify({"error": "Calendar is busy, try again"}), 409
    
    try:
        publish_suggestion_job(job)
    finally:
        release_lock(current_app.redis_client, lock_key, lock_id)

    return jsonify({
            "job_id": job["job_id"],
            "status": "submitted"
        }), 202

@events_bp.get("/recommendations/group/<int:group_id>/job/<int:job_id>")
@jwt_required
@group_role_required("organizer")
def get_interval_recommendations(group_id, job_id):
    job = Job.query.filter_by(
        id = job_id
    ).first()

    if not job:
        return jsonify({"error": "No job with this id exists"}), 404
    
    if job.status == "PENDING":
        return jsonify({"error": "Job pending"}), 202
    
    intervals = Interval.query.filter_by(job_id = job.id).all()

    if not intervals:
        return jsonify({"error": "No intervals found"}), 404
    
    return jsonify({
        "intervals": [interval.to_dict() for interval in intervals],
        "status": job.status
    }), 200

def publish_suggestion_job(payload):
    connection = pika.BlockingConnection(
        pika.URLParameters(current_app.config["RABBITMQ_URL"])
    )
    channel = connection.channel()

    channel.queue_declare(queue="suggestions", durable=True)

    channel.basic_publish(
        exchange="",
        routing_key="suggestions",
        body=json.dumps(payload),
        properties=pika.BasicProperties(delivery_mode=2)
    )

    connection.close()

def validate_iso_datetime(value):
    try:
        datetime.fromisoformat(value)
    except ValueError:
        raise ValueError(
            "Invalid datetime format. Expected ISO-8601, e.g. 2026-01-31T08:00:00"
        )

    return value
