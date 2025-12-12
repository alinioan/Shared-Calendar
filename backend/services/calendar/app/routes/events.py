import requests
from datetime import datetime
from flask import Blueprint, current_app, jsonify, g, request
from ..utils.decorators import jwt_required, group_role_required
from ..models.group import Group
from ..models.group_user import GroupUser
from ..models.event import Event
from ..db import db

events_bp = Blueprint("events", __name__)

@events_bp.post("/group/<int:group_id>")
@jwt_required
@group_role_required("organizer")
def add_event(group_id):
    data = request.get_json()
    event = Event(
        group_id=group_id,
        title=data.get("title"),
        description=data.get("description", ""),
        start_time=data.get("start_time"),
        end_time=data.get("end_time"),
        created_by=g.user["keycloak_id"],
        creation_date=datetime.utcnow(),
        last_update=datetime.utcnow()
    )

    overlap_event = Event.query.filter(
        Event.start_time < event.end_time,
        Event.end_time > event.start_time
    ).first();

    if overlap_event:
        return jsonify({"error": "Event time overlaps with an existing event"}), 400

    db.session.add(event)
    db.session.commit()
    return jsonify(event.to_dict()), 201


@events_bp.get("/group/<int:group_id>")
@jwt_required
def get_group_events(group_id):
    events = Event.query.filter_by(group_id=group_id).all()
    events_list = [event.to_dict() for event in events]
    return jsonify({"group": group_id, "events": events_list}), 200

#TODO
@events_bp.post("/group/<int:group_id>/recommendations")
@jwt_required
@group_role_required("organizer")
def make_recommendation_request(group_id):
    pass

#TODO
@events_bp.get("/group/<int:group_id>/recommendations/<int:job_id>")
@jwt_required
@group_role_required("organizer")
def get_interval_recommendations(group_id, job_id):
    pass