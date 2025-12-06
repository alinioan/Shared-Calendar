import requests
from datetime import datetime
from flask import Blueprint, current_app, jsonify, g, request
from ..utils.decorators import jwt_required, group_role_required
from ..models import Group, GroupUser
from ..db import db

groups_bp = Blueprint("groups", __name__)

@groups_bp.post("/")
@jwt_required()
def add_group():
    data = request.get_json()
    name = data.get("name")
    description = data.get("description", "")

    keycloak_user = g.user
    group = Group(
        name=name,
        description=description,
        owner_id=keycloak_user["keycloak_id"],
        creation_date=datetime.utcnow(),
        last_update=datetime.utcnow()
    )
    db.session.add(group)
    db.session.commit()

    group_user = GroupUser(
        group_id=group.id,
        user_keycloak_id=keycloak_user["keycloak_id"],
        role="organizer",
        joined_date=datetime.utcnow()
    )

    db.session.add(group_user)
    db.session.commit()

    return jsonify({"message": "Group created successfully",
                    "group": {
                        "id": group.id,
                        "name": group.name,
                        "description": group.description,
                        "creation_date": group.creation_date,
                        "last_update": group.last_update
                    }}), 201

@groups_bp.get("/<int:group_id>")
@jwt_required()
def get_group(group_id):
    group = Group.query.get(group_id)
    
    if not group:
        return jsonify({"error": "Group not found"}), 404
    
    return jsonify(group.to_dict()), 200
    

@groups_bp.delete("/<int:group_id>")
@group_role_required("organizer")
@jwt_required()
def delete_group(group_id):
    group = Group.query.get(group_id)
    
    if not group:
        return jsonify({"error": "Group not found"}), 404

    db.session.delete(group)
    db.session.commit()
    
    return jsonify({"message": "Group deleted successfully"}), 200

@groups_bp.post("/<int:group_id>/users")
@group_role_required("organizer")
@jwt_required()
def add_group_member(group_id):
    data = request.get_json()
    target_user_id = data.get("user_id")

    if not target_user_id:
        return jsonify({"error": "user_id is required"}), 400

    profile_url = f"{current_app.config['PROFILE_SERVICE_URL']}/profile/{target_user_id}"
    resp = requests.get(profile_url)

    if resp.status_code != 200:
        return jsonify({"error": "User not found in Profile Service"}), 404

    existing = GroupUser.query.filter_by(
        group_id=group_id,
        user_id=target_user_id
    ).first()

    if existing:
        return jsonify({"error": "User already in group"}), 409

    new_member = GroupUser(
        group_id=group_id,
        user_id=target_user_id,
        role_in_group="member"
    )

    db.session.add(new_member)
    db.session.commit()

    return jsonify({
        "message": "User added to group",
        "group_id": group_id,
        "user_id": target_user_id,
        "role": "member"
    }), 201


@groups_bp.get("/<int:group_id>/users")
@jwt_required()
def get_group_members(group_id):
    members = GroupUser.query.filter_by(group_id=group_id).all()
    members_list = [member.to_dict() for member in members]
    return jsonify({"group_id": group_id, "members": members_list}), 200

@groups_bp.delete("/<int:group_id>/users")
@group_role_required("organizer")
@jwt_required()
def remove_group_member(group_id, user_id):
    data = request.get_json()
    target_user_id = data.get("user_id")

    if not target_user_id:
        return jsonify({"error": "user_id is required"}), 400

    profile_url = f"{current_app.config['PROFILE_SERVICE_URL']}/profile/{target_user_id}"
    resp = requests.get(profile_url)

    if resp.status_code != 200:
        return jsonify({"error": "User not found in Profile Service"}), 404

    user = GroupUser.query.filter_by(
        group_id=group_id,
        user_id=target_user_id
    ).first()

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "User removed from group"}), 200